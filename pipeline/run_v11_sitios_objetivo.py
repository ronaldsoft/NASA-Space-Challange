#!/usr/bin/env python3
"""
Corrida única de la revisión §9 / v1.1 (firmas por sitios objetivo).

Lee la lista, las ventanas y las variables desde el archivo de configuración
congelado ANTES de esta corrida. No elige sitios, radios ni variables
mirando la validación ni Ecuador. Si el AUC vuelve a fallar, no itera.
La versión por bandas (v1) no se sobrescribe: los productos de esta
variante van a web/public/productos/sitios_objetivo/ y el catálogo las
expone en paralelo, con «bandas» como firma por defecto del tablero.
"""
from __future__ import annotations

import csv
import json
import math
import shutil
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import from_bounds, Window

from pipeline.generate_mock import colorize_class, colorize_delta, save_png
from pipeline.index import CLASS_NAMES, choose_threshold, classify, delta_index
from pipeline.metrics import bootstrap_auc_ci, delong_paired, null_abs_lat_auc
from pipeline.signatures import Signature, build_signatures
from pipeline.standardize import fit_std_params
from pipeline.run_real import (
    AGREGACION_DOC,
    NODATA,
    OUT_WEB,
    PAL_MARS,
    PAL_MOON,
    PRIORITY_SEEDS,
    PROC,
    ROOT,
    haversine_km as haversine_earth_km,
    jsonable,
    label_to_class,
    load_ecuador,
    load_npz,
    now_iso,
    valid_mask,
    write_cog,
    y_pos,
    zone_from_cell,
    nearest_valid,
)

CONFIG_PATH = ROOT / "config" / "v1_1_sitios_objetivo.json"
OUT = OUT_WEB / "sitios_objetivo"
VARIABLES = ("elevation", "slope", "roughness")  # elevation = relieve relativo (congelado)


def wrap_lon(lon: float) -> float:
    return ((float(lon) + 180.0) % 360.0) - 180.0


def haversine_body_km(lat1, lon1, lat2, lon2, radius_km: float):
    p1, l1, p2, l2 = map(np.radians, (lat1, lon1, lat2, lon2))
    dphi = p2 - p1
    dl = l2 - l1
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * radius_km * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def pixel_centers(transform, shape):
    rows, cols = np.indices(shape)
    lon = transform.c + (cols + 0.5) * transform.a + (rows + 0.5) * transform.b
    lat = transform.f + (cols + 0.5) * transform.d + (rows + 0.5) * transform.e
    return lon, lat


def _read_window(path: Path, window: Window) -> tuple[np.ndarray, object]:
    with rasterio.open(path) as ds:
        w = window.round_offsets().round_lengths()
        # clip to dataset
        w = w.intersection(Window(0, 0, ds.width, ds.height))
        if w.width <= 0 or w.height <= 0:
            return np.empty((0, 0), np.float32), ds.transform
        arr = ds.read(1, window=w).astype(np.float32)
        if ds.nodata is not None:
            arr = np.where(arr == ds.nodata, np.nan, arr)
        return arr, ds.window_transform(w)


def extract_target_cells(body: str, site: dict, radius_body_km: float) -> dict:
    """Celdas válidas dentro del radio congelado (haversina del cuerpo)."""
    lat0 = float(site["lat"])
    lon0 = wrap_lon(site["lon"])
    radio = float(site["radio_km"])
    lat_pad = (radio / radius_body_km) * (180.0 / math.pi) * 1.8
    coslat = max(math.cos(math.radians(lat0)), 0.015)
    lon_pad = min(179.5, (radio / radius_body_km) * (180.0 / math.pi) / coslat * 1.8)

    paths = {
        "elevation": PROC / body / f"{body}_relative_relief_1km.tif",
        "slope": PROC / body / f"{body}_slope_1km.tif",
        "roughness": PROC / body / f"{body}_roughness_tri_1km.tif",
    }

    def bounds_ok(west, south, east, north):
        west = max(-180.0, west)
        east = min(180.0, east)
        south = max(-90.0, south)
        north = min(90.0, north)
        return west, south, east, north

    west0, south, east0, north = lon0 - lon_pad, lat0 - lat_pad, lon0 + lon_pad, lat0 + lat_pad
    # Si cruza el antimeridiano, se leen dos ventanas.
    segments = []
    if west0 < -180.0:
        segments.append(bounds_ok(west0 + 360.0, south, 180.0, north))
        segments.append(bounds_ok(-180.0, south, east0, north))
    elif east0 > 180.0:
        segments.append(bounds_ok(west0, south, 180.0, north))
        segments.append(bounds_ok(-180.0, south, east0 - 360.0, north))
    else:
        segments.append(bounds_ok(west0, south, east0, north))

    chunks = {k: [] for k in ("elevation", "slope", "roughness", "lat", "lon")}
    with rasterio.open(paths["elevation"]) as ref:
        transform0 = ref.transform
    for west, south_b, east, north_b in segments:
        if east <= west or north_b <= south_b:
            continue
        window = from_bounds(west, south_b, east, north_b, transform0)
        layers = {}
        wt = None
        for key, path in paths.items():
            arr, wt = _read_window(path, window)
            layers[key] = arr
        if layers["elevation"].size == 0:
            continue
        lon, lat = pixel_centers(wt, layers["elevation"].shape)
        chunks["elevation"].append(layers["elevation"].ravel())
        chunks["slope"].append(layers["slope"].ravel())
        chunks["roughness"].append(layers["roughness"].ravel())
        chunks["lat"].append(lat.ravel())
        chunks["lon"].append(lon.ravel())

    if not chunks["elevation"]:
        empty = np.array([], dtype=float)
        return {
            "n_celdas": 0,
            "n_en_radio": 0,
            "elevation": empty,
            "slope": empty,
            "roughness": empty,
            "latitude": empty,
            "longitude": empty,
        }

    elev = np.concatenate(chunks["elevation"])
    slope = np.concatenate(chunks["slope"])
    rough = np.concatenate(chunks["roughness"])
    lat = np.concatenate(chunks["lat"])
    lon = np.concatenate(chunks["lon"])
    dist = haversine_body_km(lat0, lon0, lat, lon, radius_body_km)
    ok = (
        np.isfinite(elev)
        & np.isfinite(slope)
        & np.isfinite(rough)
        & (elev != NODATA)
        & (slope != NODATA)
        & (rough != NODATA)
        & (dist <= radio)
    )
    return {
        "n_celdas": int(ok.sum()),
        "n_en_radio": int((dist <= radio).sum()),
        "elevation": elev[ok].astype(float),
        "slope": slope[ok].astype(float),
        "roughness": rough[ok].astype(float),
        "latitude": lat[ok].astype(float),
        "longitude": lon[ok].astype(float),
    }


def params_as_list(params):
    return [
        {
            "body_ref": p.body_ref,
            "variable": p.variable,
            "center": p.center,
            "scale": p.scale,
            "method": p.method,
            "frozen_at": p.frozen_at,
        }
        for p in params
    ]


def main() -> None:
    if not CONFIG_PATH.is_file():
        raise SystemExit(f"Falta el archivo congelado {CONFIG_PATH}. No se corre sin él.")
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    estado = str(cfg.get("estado") or "")
    if estado != "congelado":
        raise SystemExit(
            f"La v1.1 no está congelada (estado={estado!r}). "
            "No se corre la validación oficial hasta el OK del cliente y la congelación del config. "
            "Ver docs/cambio_metodo_sitios_objetivo.md."
        )

    # Copia inmutable junto a los productos (el original no se modifica).
    OUT.mkdir(parents=True, exist_ok=True)
    shutil.copy2(CONFIG_PATH, OUT / "v1_1_sitios_objetivo.congelado.json")

    frozen_at = now_iso()
    min_n = int(cfg["minimo_celdas_validas"])
    r_moon = float(cfg["radio_lunar_km"])
    r_mars = float(cfg["radio_marte_km"])
    radii = {"moon": r_moon, "mars": r_mars}

    print(f"§9 / v1.1 congelado en {cfg['fecha_congelacion']}. Corrida {frozen_at}.")
    print("Variables:", VARIABLES, "| elevacion_modo:", cfg["variables_indice"]["elevacion_modo"])
    print("Latitud en el vector: no. Una sola corrida.")

    # 1) Extraer ventanas y construir firmas (antes de mirar la validación terrestre).
    cells = {}
    n_por_sitio = []
    sigs = {"mars": [], "moon": []}
    for body in ("mars", "moon"):
        samples_by_site = {}
        for site in cfg["sitios_objetivo"][body]:
            print(f"  Ventana {body}/{site['id']} r={site['radio_km']} km …", flush=True)
            got = extract_target_cells(body, site, radii[body])
            n = got["n_celdas"]
            aviso_n = n < min_n
            rec = {
                "id": site["id"],
                "nombre": site["nombre"],
                "cuerpo": body,
                "lat": site["lat"],
                "lon": site["lon"],
                "lon_raster": wrap_lon(site["lon"]),
                "radio_km": site["radio_km"],
                "n_celdas": n,
                "cumple_minimo": (not aviso_n) and n > 0,
                "coordenada_provisional": bool(site.get("coordenada_provisional")),
                "ventana": site.get("ventana"),
                "cita_espacial": site.get("cita_espacial"),
            }
            n_por_sitio.append(rec)
            print(f"    n={n}  mínimo {min_n}: {'OK' if rec['cumple_minimo'] else 'POR DEBAJO O VACÍA'}")
            sample = {
                "elevation": got["elevation"],
                "slope": got["slope"],
                "roughness": got["roughness"],
                "_n": np.array([n]),
                "_short": np.array([aviso_n or n == 0]),
            }
            samples_by_site[site["id"]] = sample
            cells[(body, site["id"])] = got
        sigs[body] = build_signatures(body, samples_by_site, VARIABLES)

    # 2) std_params congelados sobre las muestras estratificadas del cuerpo de referencia
    #    (mismo npz de 56 000 celdas), no reajustados a las ventanas objetivo.
    params = {}
    for body in ("mars", "moon"):
        raw = load_npz(body)
        vals = {
            "elevation": raw["relative_relief_m"],
            "slope": raw["slope_deg"],
            "roughness": raw["roughness_tri_m"],
        }
        params[body] = fit_std_params(vals, body_ref=body, method="zscore", frozen_at=frozen_at)

    # 3) Validación terrestre: mismas medianas de buffer ya extraídas en la v1.
    catalog_v1 = json.loads((OUT_WEB / "catalogo.json").read_text(encoding="utf-8"))
    sites_v1 = catalog_v1["sitios_validacion"]

    def feat_val(s, key):
        det = (s.get("agregacion") or {}).get("detalle") or {}
        pack = det.get(key) or {}
        v = pack.get("mediana_buffer")
        return float(v) if v is not None else float("nan")

    vals = {
        "elevation": np.array([feat_val(s, "relative_relief") for s in sites_v1], float),
        "slope": np.array([feat_val(s, "slope") for s in sites_v1], float),
        "roughness": np.array([feat_val(s, "roughness") for s in sites_v1], float),
    }
    # lat_band dummy: modo todas_min compara contra todos los «sitios» (clave lat_band = id).
    dummy_bands = np.array([""] * len(sites_v1))
    in_auc = np.array([bool(s.get("entra_al_auc")) for s in sites_v1], bool)
    etiquetas = [s["etiqueta"] for s in sites_v1]
    y_mars = np.array([y_pos(e, "mars") for e in etiquetas], int)
    y_moon = np.array([y_pos(e, "moon") for e in etiquetas], int)
    lats = np.array([s["lat"] for s in sites_v1], float)

    dist, delta, win = {}, {}, {}
    for body in ("mars", "moon"):
        d, _, w = delta_index(
            vals, sigs[body], params[body], dummy_bands, body,
            variables=VARIABLES, d_max=1.0, modo_bandas="todas_min", use_abs_lat=False,
        )
        dist[body], win[body] = d, w
    d_max = {}
    for body in ("mars", "moon"):
        y = y_mars if body == "mars" else y_moon
        dpos = dist[body][in_auc & (y == 1) & np.isfinite(dist[body])]
        d_max[body] = float(np.nanmax(dpos) * 1.15) if dpos.size else 1.0
        if not np.isfinite(d_max[body]) or d_max[body] <= 0:
            d_max[body] = 1.0
        d, dl, w = delta_index(
            vals, sigs[body], params[body], dummy_bands, body,
            variables=VARIABLES, d_max=d_max[body], modo_bandas="todas_min", use_abs_lat=False,
        )
        dist[body], delta[body], win[body] = d, dl, w

    # Congelar umbrales en validación ANTES de Ecuador.
    thr = {
        "mars": choose_threshold(delta["mars"][in_auc], y_mars[in_auc], metric="youden", d_max=d_max["mars"]),
        "moon": choose_threshold(delta["moon"][in_auc], y_moon[in_auc], metric="youden", d_max=d_max["moon"]),
    }
    clas_sites = classify(delta["mars"], delta["moon"], thr["mars"].threshold, thr["moon"].threshold)
    print(
        f"Umbrales congelados v1.1: Marte={thr['mars'].threshold:.3f} AUC={thr['mars'].auc:.3f}; "
        f"Luna={thr['moon'].threshold:.3f} AUC={thr['moon'].auc:.3f}"
    )

    def pack_metrics(body_key, body, y, scores, thr_res):
        ci = bootstrap_auc_ci(y[in_auc], scores[in_auc], n_boot=2000, seed=2026)
        d = thr_res.as_dict()
        d["ic95_inferior"] = ci["ic95_inferior"]
        d["ic95_superior"] = ci["ic95_superior"]
        d["n_bootstrap"] = ci["n_bootstrap"]
        d["especificidad"] = d.get("specificity")
        return d

    metricas = {
        "etiqueta": "v1.1 sitios objetivo, sin latitud, relieve relativo, escala de esta corrida ~1 km",
        "d_max": d_max,
        "marte": pack_metrics("marte", "mars", y_mars, delta["mars"], thr["mars"]),
        "luna": pack_metrics("luna", "moon", y_moon, delta["moon"], thr["moon"]),
    }

    # Comparación (no se elige la «mejor»): DeLong v1 bandas (defecto) vs v1.1, y nulo |lat|.
    dm_v1 = np.array([s.get("delta_marte") if s.get("delta_marte") is not None else np.nan for s in sites_v1], float)
    dl_v1 = np.array([s.get("delta_luna") if s.get("delta_luna") is not None else np.nan for s in sites_v1], float)
    delong = {
        "marte_v1_bandas_vs_v11_sitios": delong_paired(y_mars[in_auc], dm_v1[in_auc], delta["mars"][in_auc]),
        "luna_v1_bandas_vs_v11_sitios": delong_paired(y_moon[in_auc], dl_v1[in_auc], delta["moon"][in_auc]),
    }
    nulo = {
        "marte": null_abs_lat_auc(y_mars[in_auc], lats[in_auc]),
        "luna": null_abs_lat_auc(y_moon[in_auc], lats[in_auc]),
        "nota": catalog_v1.get("modelo_nulo_solo_abs_lat", {}).get(
            "nota",
            "Modelo nulo: el puntaje es solo |lat|.",
        ),
    }

    sitios_out = []
    known_ok = known_auc = 0
    nombre_por_id = {}
    for body in ("mars", "moon"):
        for s in cfg["sitios_objetivo"][body]:
            nombre_por_id[s["id"]] = s["nombre"]

    for i, s in enumerate(sites_v1):
        known = label_to_class(s["etiqueta"])
        entra = bool(s.get("entra_al_auc"))
        if s.get("agregacion", {}).get("detalle") is None or clas_sites[i] < 0:
            pred = "" if s.get("agregacion", {}).get("detalle") is None else "ninguno"
            dm = dl = dist_m = dist_l = float("nan")
            acierto = False
            win_m = win_l = ""
        else:
            pred = CLASS_NAMES[int(clas_sites[i])]
            dm = float(delta["mars"][i])
            dl = float(delta["moon"][i])
            dist_m = float(dist["mars"][i])
            dist_l = float(dist["moon"][i])
            acierto = pred == known
            win_m = str(win["mars"][i])
            win_l = str(win["moon"][i])
        if entra:
            known_auc += 1
            known_ok += int(acierto)
        sitios_out.append({
            "id": s["id"],
            "nombre": s["nombre"],
            "lat": s["lat"],
            "lon": s["lon"],
            "buffer_km": s["buffer_km"],
            "etiqueta": s["etiqueta"],
            "fuente": s.get("fuente") or s.get("cita"),
            "cita": s.get("cita") or s.get("fuente"),
            "elevacion_m": s.get("elevacion_m"),
            "pendiente_deg": s.get("pendiente_deg"),
            "rugosidad_tri": s.get("rugosidad_tri"),
            "relieve_relativo_m": s.get("relieve_relativo_m"),
            "es_provisional": s.get("es_provisional", False),
            "banda_latitud": s.get("banda_latitud"),
            "sitio_ganador_marte": win_m,
            "sitio_ganador_luna": win_l,
            "sitio_ganador_marte_nombre": nombre_por_id.get(win_m, win_m),
            "sitio_ganador_luna_nombre": nombre_por_id.get(win_l, win_l),
            "delta_marte": None if not np.isfinite(dm) else round(dm, 4),
            "delta_luna": None if not np.isfinite(dl) else round(dl, 4),
            "distancia_marte": None if not np.isfinite(dist_m) else round(dist_m, 4),
            "distancia_luna": None if not np.isfinite(dist_l) else round(dist_l, 4),
            "clase_predicha": pred,
            "clase_conocida": known,
            "acierto": acierto if pred != "" else False,
            "excluido_auc": s.get("excluido_auc"),
            "coordenada_no_verificada": s.get("coordenada_no_verificada"),
            "entra_al_auc": entra,
            "firma": "sitios_objetivo",
        })

    # 4) Ecuador, umbrales ya congelados.
    print("Aplicando umbral congelado de v1.1 a Ecuador…", flush=True)
    layers, lon2d, lat2d, mask, profile, transform, bounds = load_ecuador()
    vals_ec = {
        "elevation": layers["relative_relief"][mask],
        "slope": layers["slope"][mask],
        "roughness": layers["roughness"][mask],
    }
    bands_ec = np.array([""] * int(mask.sum()))
    out_delta, out_win = {}, {}
    for body in ("mars", "moon"):
        d, dl, w = delta_index(
            vals_ec, sigs[body], params[body], bands_ec, body,
            variables=VARIABLES, d_max=d_max[body], modo_bandas="todas_min", use_abs_lat=False,
        )
        DL = np.full(mask.shape, np.nan)
        W = np.full(mask.shape, "", dtype=object)
        DL[mask] = dl
        W[mask] = w
        out_delta[body], out_win[body] = DL, W
    clas = classify(
        out_delta["mars"], out_delta["moon"],
        thr["mars"].threshold, thr["moon"].threshold,
        valid_mask=mask,
    )
    counts = {CLASS_NAMES[k]: int((clas == k).sum()) for k in (0, 1, 2, 3, -1)}
    print("Clases Ecuador v1.1 (no son el resultado principal):", counts)

    save_png(OUT / "delta_marte.png", colorize_delta(out_delta["mars"], mask, PAL_MARS))
    save_png(OUT / "delta_luna.png", colorize_delta(out_delta["moon"], mask, PAL_MOON))
    save_png(OUT / "clases.png", colorize_class(clas, mask))
    write_cog(OUT / "delta_marte.tif", out_delta["mars"], profile)
    write_cog(OUT / "delta_luna.tif", out_delta["moon"], profile)
    write_cog(OUT / "clases.tif", clas.astype(np.float32), profile, nodata=-1)

    west, south, east, north = bounds
    zones = []
    # Reutilizar los hitos geográficos de la v1; se recalcula δ con esta firma.
    for seed in PRIORITY_SEEDS:
        i, j = nearest_valid(seed["lat"], seed["lon"], lat2d, lon2d, mask)
        z = zone_from_cell(
            i, j, lat2d, lon2d, layers, mask,
            out_delta["mars"], out_delta["moon"], clas,
            out_win["mars"], out_win["moon"],
            np.full(mask.shape, "", dtype=object), seed,
        )
        if z:
            z["lat"] = seed["lat"]
            z["lon"] = seed["lon"]
            z["sitio_ganador_marte"] = z.pop("banda_ganadora_marte", "")
            z["sitio_ganador_luna"] = z.pop("banda_ganadora_luna", "")
            z["sitio_ganador_marte_nombre"] = nombre_por_id.get(z["sitio_ganador_marte"], z["sitio_ganador_marte"])
            z["sitio_ganador_luna_nombre"] = nombre_por_id.get(z["sitio_ganador_luna"], z["sitio_ganador_luna"])
            # Campos que el tablero aún espera
            z["banda_ganadora_marte"] = z["sitio_ganador_marte_nombre"]
            z["banda_ganadora_luna"] = z["sitio_ganador_luna_nombre"]
            zones.append(z)

    def add_extreme(kind, arr):
        scored = np.where(mask, arr, np.nan)
        if not np.isfinite(scored).any():
            return
        i, j = np.unravel_index(int(np.nanargmax(scored)), scored.shape)
        already = any(
            haversine_earth_km(z["lat"], z["lon"], float(lat2d[i, j]), float(lon2d[i, j])) < 15
            for z in zones
        )
        if already:
            return
        z = zone_from_cell(
            i, j, lat2d, lon2d, layers, mask,
            out_delta["mars"], out_delta["moon"], clas,
            out_win["mars"], out_win["moon"],
            np.full(mask.shape, "", dtype=object), None,
        )
        if z:
            z["id"] = f"max_{kind}"
            z["nombre"] = (
                f"Máxima similitud a {'Marte' if kind == 'marte' else 'la Luna'} "
                f"({z['lat']}°, {z['lon']}°) · firma sitios objetivo"
            )
            z["sitio_ganador_marte"] = z.pop("banda_ganadora_marte", "")
            z["sitio_ganador_luna"] = z.pop("banda_ganadora_luna", "")
            z["sitio_ganador_marte_nombre"] = nombre_por_id.get(z["sitio_ganador_marte"], z["sitio_ganador_marte"])
            z["sitio_ganador_luna_nombre"] = nombre_por_id.get(z["sitio_ganador_luna"], z["sitio_ganador_luna"])
            z["banda_ganadora_marte"] = z["sitio_ganador_marte_nombre"]
            z["banda_ganadora_luna"] = z["sitio_ganador_luna_nombre"]
            zones.append(z)

    add_extreme("marte", out_delta["mars"])
    add_extreme("luna", out_delta["moon"])
    order = {"marte": 0, "luna": 1, "ambos": 2, "ninguno": 3}
    zones.sort(key=lambda z: (order.get(z["clase"], 9), -max(z["delta_marte"], z["delta_luna"])))

    firmas_out = {
        body: [s.as_dict() for s in sigs[body]]
        for body in ("mars", "moon")
    }

    variante = {
        "revision": "v1.1",
        "seccion_metodologica": "§9",
        "fecha_congelacion": cfg["fecha_congelacion"],
        "corrida_en": frozen_at,
        "motivo": cfg["motivo"],
        "estado": cfg["estado"],
        "config_congelada": "/productos/sitios_objetivo/v1_1_sitios_objetivo.congelado.json",
        "firma_por_defecto_del_tablero": "bandas",
        "variables_indice": list(VARIABLES),
        "elevacion_modo": "relieve_relativo",
        "incluye_latitud": False,
        "pesos": {v: 1.0 / len(VARIABLES) for v in VARIABLES},
        "escala": cfg["escala"],
        "nomenclatura": cfg["nomenclatura"],
        "nota_de_validez_del_auc": cfg["nota_de_validez_del_auc"],
        "minimo_celdas_validas": min_n,
        "n_celdas_por_sitio": n_por_sitio,
        "sitios_objetivo": cfg["sitios_objetivo"],
        "std_params": {b: params_as_list(params[b]) for b in ("mars", "moon")},
        "signatures": firmas_out,
        "d_max": d_max,
        "umbrales": {"mars": thr["mars"].as_dict(), "moon": thr["moon"].as_dict()},
        "metricas_validacion": {
            **metricas,
            "aciertos_auc": known_ok,
            "n_sitios_auc": known_auc,
            "n_sitios": len(sitios_out),
            "aciertos": known_ok,
        },
        "delong_pareado_vs_v1_bandas": delong,
        "modelo_nulo_solo_abs_lat": nulo,
        "sitios_validacion": sitios_out,
        "zonas_prioritarias": zones,
        "clases_ecuador": counts,
        "capas": {
            "similitud-marte": {"archivo": "/productos/sitios_objetivo/delta_marte.png", "tipo": "png", "cuerpo": "mars"},
            "similitud-luna": {"archivo": "/productos/sitios_objetivo/delta_luna.png", "tipo": "png", "cuerpo": "moon"},
            "clases": {"archivo": "/productos/sitios_objetivo/clases.png", "tipo": "png", "etiqueta": "clases (no es el resultado principal)"},
        },
        "presentacion": (
            "Se reportan la v1 (firmas por bandas) y la v1.1 (firmas por sitios objetivo) "
            "en paralelo, sin elegir la mejor. El mapa que debe mostrarse es el continuo de δ, "
            "con la nota de incertidumbre; el mapa de clases no es el titular si la especificidad es baja. "
            "La mayoría de los positivos terrestres son análogos de Marte (o de la Luna) en general, "
            "no de Jezero, Arcadia u otro sitio objetivo en particular, así que el AUC sigue siendo "
            "una prueba imperfecta."
        ),
    }

    (OUT / "catalogo_variante.json").write_text(
        json.dumps(jsonable(variante), ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Parchear el catálogo v1: no se toca el defecto (bandas).
    catalog_v1["firma_por_defecto"] = "bandas"
    catalog_v1["firmas_disponibles"] = [
        {"id": "bandas", "etiqueta": "bandas", "revision": "v1"},
        {"id": "sitios_objetivo", "etiqueta": "sitios objetivo", "revision": "v1.1"},
    ]
    catalog_v1["variante_sitios_objetivo"] = jsonable(variante)
    catalog_v1["revision_s9"] = {
        "fecha": cfg["fecha_congelacion"],
        "motivo": cfg["motivo"],
        "nomenclatura_luna": cfg["nomenclatura"]["luna_regiones"],
        "nota": "Revisión post hoc declarada. Ver docs/cambio_metodo_sitios_objetivo.md.",
    }
    (OUT_WEB / "catalogo.json").write_text(
        json.dumps(jsonable(catalog_v1), ensure_ascii=False, indent=2), encoding="utf-8"
    )

    csv_path = OUT / "tabla_validacion.csv"
    also = Path("/workspace/tabla_validacion_sitios_objetivo.csv")
    fields = [
        "id", "nombre", "lat", "lon", "buffer_km", "etiqueta",
        "sitio_ganador_marte", "sitio_ganador_luna",
        "delta_marte", "delta_luna", "distancia_marte", "distancia_luna",
        "clase_conocida", "clase_predicha", "acierto", "entra_al_auc",
        "excluido_auc", "cita",
    ]
    for path in (csv_path, also):
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            for s in sitios_out:
                row = dict(s)
                row["acierto"] = "" if s["clase_predicha"] == "" else ("sí" if s["acierto"] else "no")
                row["entra_al_auc"] = "sí" if s["entra_al_auc"] else "no"
                row["excluido_auc"] = "sí" if s["excluido_auc"] else "no"
                w.writerow(row)

    # Resumen (ambas versiones, sin declarar ganadora).
    m1 = catalog_v1["metricas_validacion"]
    print("\n=== COMPARACIÓN (sin elegir la mejor) ===")
    print(
        f"v1 bandas (defecto): Marte AUC={m1['marte']['auc']:.3f} "
        f"thr={m1['marte']['threshold']:.3f} sens={m1['marte']['sensitivity']:.3f} prec={m1['marte']['precision']:.3f} | "
        f"Luna AUC={m1['luna']['auc']:.3f} thr={m1['luna']['threshold']:.3f} "
        f"sens={m1['luna']['sensitivity']:.3f} prec={m1['luna']['precision']:.3f} | "
        f"aciertos {m1.get('aciertos_auc')}/{m1.get('n_sitios_auc')}"
    )
    print(
        f"v1.1 sitios objetivo: Marte AUC={metricas['marte']['auc']:.3f} "
        f"[{metricas['marte'].get('ic95_inferior')}, {metricas['marte'].get('ic95_superior')}] "
        f"thr={metricas['marte']['threshold']:.3f} sens={metricas['marte']['sensitivity']:.3f} "
        f"prec={metricas['marte']['precision']:.3f} spec={metricas['marte'].get('specificity')} | "
        f"Luna AUC={metricas['luna']['auc']:.3f} "
        f"[{metricas['luna'].get('ic95_inferior')}, {metricas['luna'].get('ic95_superior')}] "
        f"thr={metricas['luna']['threshold']:.3f} sens={metricas['luna']['sensitivity']:.3f} "
        f"prec={metricas['luna']['precision']:.3f} spec={metricas['luna'].get('specificity')} | "
        f"aciertos {known_ok}/{known_auc}"
    )
    print("n por sitio objetivo:", json.dumps(n_por_sitio, ensure_ascii=False, indent=2))
    print("DeLong v1 vs v1.1:", json.dumps(jsonable(delong), ensure_ascii=False, indent=2))
    print("Clases Ecuador v1.1:", counts)
    print("Escrito en", OUT)


if __name__ == "__main__":
    main()
