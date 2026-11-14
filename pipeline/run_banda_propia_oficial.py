#!/usr/bin/env python3
"""Corrida oficial v1 con modo_bandas=banda_propia.

Reutiliza std_params y firmas congelados de la corrida 13:40 (catalogo histórico).
No reajusta firmas ni pesos. Sí reajusta d_max y el umbral de Youden sobre
los mismos 16 sitios, con el mismo procedimiento que run_real.evaluar.
Aplica esos umbrales, ya fijos, a Ecuador (continente y Galápagos).
No pisa la copia en corrida_previa_todas_min/.
"""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from rasterio.windows import Window
from rasterio.windows import from_bounds as window_from_bounds

ROOT = Path("/workspace/analogs")
sys.path.insert(0, str(ROOT))

from pipeline.generate_mock import colorize_class, colorize_delta, save_png
from pipeline.index import CLASS_NAMES, MODO_BANDA_PROPIA, MODO_TODAS_MIN, classify
from pipeline.metrics import delong_paired, null_abs_lat_auc
from pipeline.run_real import (
    AGREGACION_DOC,
    BANDS,
    EXCLUDED_SITES,
    INDEX_VARS,
    OUT_WEB,
    PAL_MARS,
    PAL_MOON,
    PRIORITY_SEEDS,
    SITE_META,
    SITES_CSV,
    evaluar,
    extract_site,
    label_to_class,
    load_ecuador,
    metricas_de,
    nearest_valid,
    now_iso,
    write_cog,
    zone_from_cell,
)
from pipeline.signatures import Signature, assign_lat_band
from pipeline.standardize import StdParam

ARCH_CAT = ROOT / "data/processed/corrida_previa_todas_min/catalogo.json"
ARCH_WEB = ROOT / "web/public/productos/corrida_previa_todas_min"
PNG_1340 = ROOT / "web/public/productos/corrida_previa_todas_min/banda_propia_png_13-40"
OUT_STATS = ROOT / "data/processed/corrida_banda_propia"
POLY_YASUNI = Path("/tmp/yasuni/yasuni_pn_wdpa.json")


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_frozen_params(cat: dict):
    params, sigs = {}, {}
    for body in ("mars", "moon"):
        params[body] = [StdParam(**row) for row in cat["std_params"][body]]
        sigs[body] = [Signature(**row) for row in cat["signatures"][body]]
    return params, sigs


def load_sites():
    sites = []
    with SITES_CSV.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sid = row["id"]
            meta = SITE_META[sid]
            feat = extract_site(sid, float(row["lat"]), float(row["lon"]), float(row["buffer_km"]))
            sites.append({
                "id": sid,
                "nombre": meta["nombre"],
                "lat": float(row["lat"]),
                "lon": float(row["lon"]),
                "buffer_km": float(row["buffer_km"]),
                "etiqueta": row["etiqueta"],
                "excluido_auc": meta["excluido_auc"],
                "coordenada_no_verificada": meta["coordenada_no_verificada"],
                "cita": meta["cita"],
                "feat": feat,
                "csv_center": {
                    "elevation": float(row["elevation_m"]),
                    "slope": float(row["slope_deg"]),
                    "roughness": float(row["roughness_tri_m"]),
                    "relative_relief": float(row["relative_relief_m"]),
                },
            })
    for ex in EXCLUDED_SITES:
        sites.append({**ex, "feat": None, "csv_center": None})
    return sites


def sitios_from_ev(sites, ev, modo):
    out = []
    known_ok = known_auc = 0
    for i, s in enumerate(sites):
        known = label_to_class(s["etiqueta"])
        if ev["clas"][i] < 0 or s["feat"] is None:
            pred = "ninguno"
            dm = dl = dist_m = dist_l = float("nan")
            acierto = False
            band = str(assign_lat_band(s["lat"], BANDS))
            win_m = win_l = ""
        else:
            pred = CLASS_NAMES[int(ev["clas"][i])]
            dm = float(ev["delta"]["mars"][i])
            dl = float(ev["delta"]["moon"][i])
            dist_m = float(ev["dist"]["mars"][i])
            dist_l = float(ev["dist"]["moon"][i])
            acierto = pred == known
            band = str(ev["bands"][i])
            win_m = str(ev["win"]["mars"][i])
            win_l = str(ev["win"]["moon"][i])
        entra = (not s["excluido_auc"]) and s["feat"] is not None
        if entra:
            known_auc += 1
            known_ok += int(acierto)
        feat = s["feat"] or {}
        out.append({
            "id": s["id"],
            "nombre": s["nombre"],
            "lat": s["lat"],
            "lon": s["lon"],
            "buffer_km": s["buffer_km"],
            "etiqueta": s["etiqueta"],
            "fuente": s["cita"],
            "cita": s["cita"],
            "elevacion_m": feat.get("elevation", {}).get("mediana_buffer") if feat else None,
            "pendiente_deg": feat.get("slope", {}).get("mediana_buffer") if feat else None,
            "rugosidad_tri": feat.get("roughness", {}).get("mediana_buffer") if feat else None,
            "relieve_relativo_m": feat.get("relative_relief", {}).get("mediana_buffer") if feat else None,
            "agregacion": {
                "metodo": "mediana_buffer",
                "descripcion": AGREGACION_DOC,
                "detalle": feat if feat else None,
                "valores_celda_central_csv": s.get("csv_center"),
            } if feat else {"metodo": None, "descripcion": "Sin ventana GLO-90; excluido del AUC.", "detalle": None},
            "es_provisional": False,
            "banda_latitud": band,
            "banda_ganadora_marte": win_m,
            "banda_ganadora_luna": win_l,
            "delta_marte": None if not np.isfinite(dm) else round(dm, 4),
            "delta_luna": None if not np.isfinite(dl) else round(dl, 4),
            "distancia_marte": None if not np.isfinite(dist_m) else round(dist_m, 4),
            "distancia_luna": None if not np.isfinite(dist_l) else round(dist_l, 4),
            "clase_predicha": pred if s["feat"] is not None else "",
            "clase_conocida": known,
            "acierto": acierto if s["feat"] is not None else False,
            "excluido_auc": s["excluido_auc"],
            "coordenada_no_verificada": s["coordenada_no_verificada"],
            "entra_al_auc": entra,
            "es_mock_superficies": False,
            "modo_bandas": modo,
        })
    return out, known_ok, known_auc


def write_tabla(path: Path, sitios):
    fields = [
        "sitio", "latitud", "longitud", "buffer_km", "banda_latitud",
        "banda_ganadora_marte", "banda_ganadora_luna", "elevacion_m",
        "pendiente_deg", "rugosidad_tri", "relieve_relativo_m", "n_celdas_buffer",
        "agregacion", "etiqueta_conocida", "clase_conocida", "delta_marte",
        "delta_luna", "clase_predicha", "acierto", "entra_al_auc", "excluido_auc",
        "coordenada_no_verificada", "cita", "es_mock_superficies", "modo_bandas",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for s in sitios:
            nbuf = ""
            if s["agregacion"] and s["agregacion"].get("detalle"):
                nbuf = s["agregacion"]["detalle"].get("n_celdas_buffer") or ""
            w.writerow({
                "sitio": s["nombre"],
                "latitud": s["lat"],
                "longitud": s["lon"],
                "buffer_km": s["buffer_km"],
                "banda_latitud": s["banda_latitud"],
                "banda_ganadora_marte": s["banda_ganadora_marte"],
                "banda_ganadora_luna": s["banda_ganadora_luna"],
                "elevacion_m": "" if s["elevacion_m"] is None else round(s["elevacion_m"], 2),
                "pendiente_deg": "" if s["pendiente_deg"] is None else round(s["pendiente_deg"], 3),
                "rugosidad_tri": "" if s["rugosidad_tri"] is None else round(s["rugosidad_tri"], 3),
                "relieve_relativo_m": "" if s["relieve_relativo_m"] is None else round(s["relieve_relativo_m"], 3),
                "n_celdas_buffer": nbuf,
                "agregacion": "mediana_buffer" if s["entra_al_auc"] or (s["elevacion_m"] is not None) else "sin_ventana",
                "etiqueta_conocida": s["etiqueta"],
                "clase_conocida": s["clase_conocida"],
                "delta_marte": s["delta_marte"] if s["delta_marte"] is not None else "",
                "delta_luna": s["delta_luna"] if s["delta_luna"] is not None else "",
                "clase_predicha": s["clase_predicha"],
                "acierto": "" if s["clase_predicha"] == "" else ("sí" if s["acierto"] else "no"),
                "entra_al_auc": "sí" if s["entra_al_auc"] else "no",
                "excluido_auc": "sí" if s["excluido_auc"] else "no",
                "coordenada_no_verificada": "sí" if s["coordenada_no_verificada"] else "no",
                "cita": s["cita"],
                "es_mock_superficies": "sí" if s["es_mock_superficies"] else "no",
                "modo_bandas": s["modo_bandas"],
            })


def pack_vals(layers, lat2d, mask, elevacion_modo):
    elev = layers["relative_relief"] if elevacion_modo == "relieve_relativo" else layers["elevation"]
    return {
        "latitude": lat2d[mask],
        "elevation": elev[mask],
        "slope": layers["slope"][mask],
        "roughness": layers["roughness"][mask],
    }


def ecuador_for(ev, layers, lat2d, mask):
    vals = pack_vals(layers, lat2d, mask, ev["elevacion_modo"])
    bands = assign_lat_band(lat2d[mask], BANDS)
    out_delta, out_win = {}, {}
    from pipeline.index import delta_index
    for body in ("mars", "moon"):
        d, dl, w = delta_index(
            vals, ev["sigs"][body], ev["params"][body], bands, body,
            variables=ev["variables"], d_max=ev["d_max"][body],
            modo_bandas=ev["modo"], use_abs_lat=True,
        )
        DL = np.full(mask.shape, np.nan); DL[mask] = dl
        W = np.full(mask.shape, "", dtype=object); W[mask] = w
        out_delta[body], out_win[body] = DL, W
    clas = classify(
        out_delta["mars"], out_delta["moon"],
        ev["thr"]["mars"].threshold, ev["thr"]["moon"].threshold,
        valid_mask=mask,
    )
    counts = {CLASS_NAMES[k]: int((clas == k).sum()) for k in (0, 1, 2, 3, -1)}
    return out_delta, out_win, clas, counts


def aligned_window(src, west, south, east, north):
    t = src.transform
    # pixel indices of bounds (left-top / right-bottom)
    c0, r0 = ~t * (west, north)
    c1, r1 = ~t * (east, south)
    c0i, r0i = int(np.floor(c0 + 1e-9)), int(np.floor(r0 + 1e-9))
    c1i, r1i = int(np.ceil(c1 - 1e-9)), int(np.ceil(r1 - 1e-9))
    c0i = max(0, c0i); r0i = max(0, r0i)
    c1i = min(src.width, c1i); r1i = min(src.height, r1i)
    return Window(c0i, r0i, c1i - c0i, r1i - r0i)


def crop_png(src_png: Path, dest: Path, win: Window):
    im = Image.open(src_png)
    box = (int(win.col_off), int(win.row_off), int(win.col_off + win.width), int(win.row_off + win.height))
    im.crop(box).save(dest, format="PNG", optimize=True)


def crop_tif(src_tif: Path, dest: Path, win: Window, nodata=None):
    with rasterio.open(src_tif) as s:
        arr = s.read(1, window=win)
        prof = s.profile
        tr = s.window_transform(win)
        nd = s.nodata if nodata is None else nodata
    prof.update(height=int(win.height), width=int(win.width), transform=tr, driver="GTiff")
    write_cog(dest, arr, prof, nodata=nd if nd is not None else -9999)


def area_stats(delta, clas, mask, layers, lat2d, lon2d):
    valid = mask & np.isfinite(delta["mars"])
    n = int(valid.sum())
    n_total = int(mask.size)
    # nodata among cells in this crop: of all cells, those not valid land
    def summ(a):
        v = a[valid]
        q1, med, q3 = np.percentile(v, [25, 50, 75])
        return {"n": n, "median": float(med), "q1": float(q1), "q3": float(q3), "iqr": float(q3 - q1),
                "min": float(v.min()), "max": float(v.max())}
    counts = {CLASS_NAMES[k]: int(((clas == k) & valid).sum()) for k in (0, 1, 2, 3)}
    return {
        "n_celdas_tierra": n,
        "n_celdas_recote": int(delta["mars"].size),
        "pct_nodata": round(100.0 * (1 - n / delta["mars"].size), 4),
        "delta_marte": summ(delta["mars"]),
        "delta_luna": summ(delta["moon"]),
        "elevacion_m": summ(layers["elevation"]),
        "pendiente_deg": summ(layers["slope"]),
        "tri_m": summ(layers["roughness"]),
        "clases": counts,
        "extension": {
            "oeste": float(lon2d[0, 0]) if lon2d.size else None,  # filled later
        },
    }


def yasuni_stats(tif_marte, tif_luna, elev, slope, tri, poly_path):
    from rasterio.features import geometry_mask
    fc = json.loads(Path(poly_path).read_text())
    geom = fc["features"][0]["geometry"]
    props = fc["features"][0]["properties"]
    out = {"poligono": {
        "fuente": "UNEP-WCMC and IUCN (2026), Protected Planet: WDPCA, servicio de octubre 2026.",
        "url_servicio": "https://data-gis.unep-wcmc.org/server/rest/services/ProtectedPlanet/WDPCA/MapServer/1",
        "site_id": props.get("site_id"),
        "nombre": "Parque Nacional Yasuní",
        "desig": props.get("desig"),
        "iso3": props.get("iso3"),
        "verif": props.get("verif"),
        "status_yr": props.get("status_yr"),
        "iucn_cat": props.get("iucn_cat"),
        "regla": "celdas de 1 km cuyo centro cae dentro del polígono oficial (all_touched=False)",
    }}
    paths = {"delta_marte": tif_marte, "delta_luna": tif_luna, "elevacion_m": elev,
             "pendiente_deg": slope, "tri_m": tri}
    with rasterio.open(tif_marte) as s:
        inside = ~geometry_mask([geom], out_shape=s.shape, transform=s.transform, invert=False, all_touched=False)
    out["n_celdas_poligono"] = int(inside.sum())
    for k, p in paths.items():
        with rasterio.open(p) as s:
            a = s.read(1); nd = s.nodata
        sel = a[inside]
        valid = sel[np.isfinite(sel)]
        if nd is not None:
            valid = valid[valid != nd]
        n_nd = int(sel.size - valid.size)
        q1, med, q3 = np.percentile(valid, [25, 50, 75])
        rec = {
            "n": int(valid.size), "n_nodata": n_nd,
            "pct_nodata": round(100.0 * n_nd / sel.size, 4) if sel.size else None,
            "median": float(med), "q1": float(q1), "q3": float(q3), "iqr": float(q3 - q1),
            "min": float(valid.min()), "max": float(valid.max()),
        }
        if "delta" in k:
            rec["pct_bajo_0_05"] = float(100.0 * (valid < 0.05).mean())
        out[k] = rec
    return out


def main():
    OUT_STATS.mkdir(parents=True, exist_ok=True)
    cat_old = json.loads(ARCH_CAT.read_text())
    params, sigs = load_frozen_params(cat_old)
    print("Cargando sitios…")
    sites = load_sites()
    print("Evaluando todas_min (verificación) y banda_propia…")
    ev_tm = evaluar(sites, params, sigs, MODO_TODAS_MIN, INDEX_VARS, "absoluta")
    ev_bp = evaluar(sites, params, sigs, MODO_BANDA_PROPIA, INDEX_VARS, "absoluta")
    ev_tm["label"] = "todas_min, vector con |lat|, elevación absoluta (corrida previa)"
    ev_bp["label"] = "banda_propia, vector con |lat|, elevación absoluta (oficial)"
    ev_tm["modo"] = MODO_TODAS_MIN
    ev_bp["modo"] = MODO_BANDA_PROPIA
    ev_tm["variables"] = ev_bp["variables"] = INDEX_VARS
    ev_tm["elevacion_modo"] = ev_bp["elevacion_modo"] = "absoluta"
    ev_tm["params"] = ev_bp["params"] = params
    ev_tm["sigs"] = ev_bp["sigs"] = sigs

    met_tm = metricas_de(ev_tm, ev_tm["label"])
    met_bp = metricas_de(ev_bp, ev_bp["label"])
    # compare to catalog 13:40
    old_bp = cat_old["metricas_por_variante"]["banda_propia_con_latitud"]
    old_tm = cat_old["metricas_por_variante"]["todas_min_con_latitud"]
    def chk(tag, a, b, keys=("auc", "threshold")):
        for k in keys:
            print(f"  {tag}.{k}: nuevo={a[k]} archivo={b[k]} eq={np.isclose(a[k], b[k], rtol=0, atol=1e-12)}")
    print("Verificación vs catálogo 13:40:")
    chk("bp.marte", met_bp["marte"], old_bp["marte"])
    chk("bp.luna", met_bp["luna"], old_bp["luna"])
    chk("tm.marte", met_tm["marte"], old_tm["marte"])
    print("d_max bp", ev_bp["d_max"], "archivo", old_bp["d_max"])

    ia = ev_bp["in_auc"]
    delong_modos = {
        "marte_todas_min_vs_banda_propia": delong_paired(
            ev_bp["y_mars"][ia], ev_tm["delta"]["mars"][ia], ev_bp["delta"]["mars"][ia]
        ),
        "luna_todas_min_vs_banda_propia": delong_paired(
            ev_bp["y_moon"][ia], ev_tm["delta"]["moon"][ia], ev_bp["delta"]["moon"][ia]
        ),
    }
    nulo = {
        "marte": null_abs_lat_auc(ev_bp["y_mars"][ia], ev_bp["vals"]["latitude"][ia]),
        "luna": null_abs_lat_auc(ev_bp["y_moon"][ia], ev_bp["vals"]["latitude"][ia]),
        "nota": "Modelo nulo: el puntaje es solo |lat|. No depende del modo de bandas.",
    }

    sitios_bp, hits_bp, n_auc = sitios_from_ev(sites, ev_bp, MODO_BANDA_PROPIA)
    sitios_tm, hits_tm, n_auc_tm = sitios_from_ev(sites, ev_tm, MODO_TODAS_MIN)
    print(f"Aciertos banda_propia {hits_bp}/{n_auc}; todas_min {hits_tm}/{n_auc_tm}")

    print("Aplicando umbral congelado de banda_propia a Ecuador (no se reajusta)…")
    layers, lon2d, lat2d, mask, profile, transform, bounds = load_ecuador()
    delta, win, clas, counts = ecuador_for(ev_bp, layers, lat2d, mask)
    print("Clases Ecuador+Galápagos (banda_propia):", counts)
    west, south, east, north = bounds

    # write official rasters/pngs
    save_png(OUT_WEB / "delta_marte.png", colorize_delta(delta["mars"], mask, PAL_MARS))
    save_png(OUT_WEB / "delta_luna.png", colorize_delta(delta["moon"], mask, PAL_MOON))
    save_png(OUT_WEB / "clases.png", colorize_class(clas, mask))
    write_cog(OUT_WEB / "delta_marte.tif", delta["mars"], profile)
    write_cog(OUT_WEB / "delta_luna.tif", delta["moon"], profile)
    write_cog(OUT_WEB / "clases.tif", clas.astype(np.float32), profile, nodata=-1)

    # verify 13:40 PNGs
    verif = {}
    for name in ("delta_marte.png", "delta_luna.png", "clases.png"):
        a = np.array(Image.open(OUT_WEB / name))
        b = np.array(Image.open(PNG_1340 / name))
        same = a.shape == b.shape and np.array_equal(a, b)
        frac = None if a.shape != b.shape else float((a != b).any(axis=2).mean() if a.ndim == 3 else (a != b).mean())
        verif[name] = {"identico": same, "fraccion_pixeles_distintos": frac,
                       "sha_nuevo": sha256(OUT_WEB / name), "sha_13_40": sha256(PNG_1340 / name)}
        print("PNG vs 13:40", name, verif[name])

    # area crops
    areas = {
        "galapagos": {"oeste": -91.80, "sur": -1.54, "este": -89.12, "norte": 0.78,
                      "etiqueta": "Galápagos"},
        "ecuador_continental": {"oeste": -81.25, "sur": -5.103, "este": -74.997, "norte": 1.701,
                                "etiqueta": "Ecuador continental"},
    }
    with rasterio.open(OUT_WEB / "delta_marte.tif") as src:
        area_meta = {}
        for key, ext in areas.items():
            dest_dir = OUT_WEB / key
            dest_dir.mkdir(exist_ok=True)
            winw = aligned_window(src, ext["oeste"], ext["sur"], ext["este"], ext["norte"])
            tr = src.window_transform(winw)
            # exact bounds of cropped grid
            bnds = rasterio.transform.array_bounds(int(winw.height), int(winw.width), tr)
            w, s, e, n = bnds
            for fname, nd in (("delta_marte.tif", -9999.0), ("delta_luna.tif", -9999.0), ("clases.tif", -1.0)):
                crop_tif(OUT_WEB / fname, dest_dir / fname, winw, nodata=nd)
            for fname in ("delta_marte.png", "delta_luna.png", "clases.png"):
                crop_png(OUT_WEB / fname, dest_dir / fname, winw)
            # stats on crop arrays
            sl = (slice(int(winw.row_off), int(winw.row_off + winw.height)),
                  slice(int(winw.col_off), int(winw.col_off + winw.width)))
            d_c = {"mars": delta["mars"][sl], "moon": delta["moon"][sl]}
            m_c = mask[sl]
            st = {
                "n_celdas_tierra": int(m_c.sum()),
                "n_celdas_recorte": int(m_c.size),
                "pct_nodata": round(100.0 * (1 - m_c.sum() / m_c.size), 4),
                "extension": {"oeste": w, "sur": s, "este": e, "norte": n},
                "ventana_pixeles": {"col": int(winw.col_off), "row": int(winw.row_off),
                                    "ancho": int(winw.width), "alto": int(winw.height)},
            }
            def summ(a):
                v = a[m_c]
                v = v[np.isfinite(v)]
                q1, med, q3 = np.percentile(v, [25, 50, 75])
                return {"n": int(v.size), "median": float(med), "q1": float(q1), "q3": float(q3),
                        "iqr": float(q3 - q1), "min": float(v.min()), "max": float(v.max())}
            st["delta_marte"] = summ(d_c["mars"])
            st["delta_luna"] = summ(d_c["moon"])
            st["elevacion_m"] = summ(layers["elevation"][sl])
            st["pendiente_deg"] = summ(layers["slope"][sl])
            st["tri_m"] = summ(layers["roughness"][sl])
            csl = clas[sl]
            st["clases"] = {CLASS_NAMES[k]: int(((csl == k) & m_c).sum()) for k in (0, 1, 2, 3)}
            area_meta[key] = {**ext, **st, "capas": {
                "similitud-marte": {"archivo": f"/productos/{key}/delta_marte.png", "tipo": "png"},
                "similitud-luna": {"archivo": f"/productos/{key}/delta_luna.png", "tipo": "png"},
                "clases": {"archivo": f"/productos/{key}/clases.png", "tipo": "png"},
            }}
            print(key, "n", st["n_celdas_tierra"], "dM", st["delta_marte"]["median"], "dL", st["delta_luna"]["median"])

    # zones from official (banda_propia) grid
    grid_bands = np.full(mask.shape, "", dtype=object)
    grid_bands[mask] = assign_lat_band(lat2d[mask], BANDS)
    zones = []
    for seed in PRIORITY_SEEDS:
        i, j = nearest_valid(seed["lat"], seed["lon"], lat2d, lon2d, mask)
        z = zone_from_cell(i, j, lat2d, lon2d, layers, mask, delta["mars"], delta["moon"], clas,
                           win["mars"], win["moon"], grid_bands, seed)
        if z:
            z["lat"] = seed["lat"]
            z["lon"] = seed["lon"]
            z["area"] = "galapagos" if seed["lon"] < -85 else "ecuador_continental"
            zones.append(z)

    def add_extreme(kind, arr, area_mask, area_name):
        scored = np.where(mask & area_mask, arr, np.nan)
        if not np.isfinite(scored).any():
            return
        i, j = np.unravel_index(int(np.nanargmax(scored)), scored.shape)
        nombre = "Máxima similitud a Marte" if kind == "mars" else "Máxima similitud a la Luna"
        if area_name == "galapagos":
            nombre += " (Galápagos)"
        z = zone_from_cell(i, j, lat2d, lon2d, layers, mask, delta["mars"], delta["moon"], clas,
                           win["mars"], win["moon"], grid_bands,
                           {"id": f"max_{kind}_{area_name}", "nombre": nombre,
                            "lat": float(lat2d[i, j]), "lon": float(lon2d[i, j])})
        if z:
            z["area"] = area_name
            zones.append(z)

    gal_m = lon2d < -85
    cont_m = lon2d >= -85
    add_extreme("mars", delta["mars"], cont_m, "ecuador_continental")
    add_extreme("moon", delta["moon"], cont_m, "ecuador_continental")
    add_extreme("mars", delta["mars"], gal_m, "galapagos")
    add_extreme("moon", delta["moon"], gal_m, "galapagos")

    # Yasuní both runs
    yas = {}
    # todas_min from archive tifs
    if POLY_YASUNI.exists():
        yas["banda_propia"] = yasuni_stats(
            OUT_WEB / "delta_marte.tif", OUT_WEB / "delta_luna.tif",
            ROOT / "data/processed/earth/ecuador_elevation_1km.tif",
            ROOT / "data/processed/earth/ecuador_slope_1km.tif",
            ROOT / "data/processed/earth/ecuador_roughness_1km.tif",
            POLY_YASUNI,
        )
        yas["todas_min"] = yasuni_stats(
            ARCH_WEB / "delta_marte.tif", ARCH_WEB / "delta_luna.tif",
            ROOT / "data/processed/earth/ecuador_elevation_1km.tif",
            ROOT / "data/processed/earth/ecuador_slope_1km.tif",
            ROOT / "data/processed/earth/ecuador_roughness_1km.tif",
            POLY_YASUNI,
        )
        print("Yasuní todas_min dM", yas["todas_min"]["delta_marte"]["median"],
              "banda_propia dM", yas["banda_propia"]["delta_marte"]["median"],
              "n", yas["banda_propia"]["n_celdas_poligono"])

    frozen_at = now_iso()
    # write catalog based on historical, with official fields swapped
    cat = json.loads(ARCH_CAT.read_text())
    cat["modo_bandas"] = MODO_BANDA_PROPIA
    cat["nota_modo_bandas"] = (
        "Oficial: banda_propia, como el §5 del método (cada celda se compara solo con la firma "
        "de su propia banda de |lat|). La corrida con banda_propia se hizo después de ver el AUC de todas_min. "
        "todas_min queda como corrida previa, no se borra."
    )
    cat["congelado_en"] = frozen_at
    cat["elevacion_modo"] = "absoluta"
    cat["d_max"] = ev_bp["d_max"]
    cat["umbrales"] = {
        "mars": ev_bp["thr"]["mars"].as_dict(),
        "moon": ev_bp["thr"]["moon"].as_dict(),
    }
    cat["metricas_validacion"] = {
        "marte": {k: met_bp["marte"][k] for k in ("threshold", "sensitivity", "precision", "auc", "agreement") if k in met_bp["marte"]},
        "luna": {k: met_bp["luna"][k] for k in ("threshold", "sensitivity", "precision", "auc", "agreement") if k in met_bp["luna"]},
        "aciertos": hits_bp,
        "aciertos_auc": hits_bp,
        "n_sitios_auc": n_auc,
        "n_sitios": len(sitios_bp),
    }
    # keep historical variant metrics, overwrite with recomputed official pair
    cat["metricas_por_variante"]["todas_min_con_latitud"] = met_tm
    cat["metricas_por_variante"]["banda_propia_con_latitud"] = met_bp
    cat["comparacion_modos"] = {
        "nota": "La corrida con banda_propia se hizo después de ver el AUC de todas_min.",
        "todas_min": {
            "auc_marte": met_tm["marte"]["auc"],
            "ic95_marte": [met_tm["marte"]["ic95_inferior"], met_tm["marte"]["ic95_superior"]],
            "auc_luna": met_tm["luna"]["auc"],
            "ic95_luna": [met_tm["luna"]["ic95_inferior"], met_tm["luna"]["ic95_superior"]],
            "aciertos": hits_tm,
            "n": n_auc_tm,
            "threshold_marte": met_tm["marte"]["threshold"],
            "threshold_luna": met_tm["luna"]["threshold"],
            "congelado_en": "2026-11-14T13:40:40-05:00",
        },
        "banda_propia": {
            "auc_marte": met_bp["marte"]["auc"],
            "ic95_marte": [met_bp["marte"]["ic95_inferior"], met_bp["marte"]["ic95_superior"]],
            "auc_luna": met_bp["luna"]["auc"],
            "ic95_luna": [met_bp["luna"]["ic95_inferior"], met_bp["luna"]["ic95_superior"]],
            "aciertos": hits_bp,
            "n": n_auc,
            "threshold_marte": met_bp["marte"]["threshold"],
            "threshold_luna": met_bp["luna"]["threshold"],
            "congelado_en": frozen_at,
        },
        "delong_pareado": delong_modos,
    }
    cat["delong_pareado_modos"] = delong_modos
    cat["modelo_nulo_solo_abs_lat"] = nulo
    cat["clases_ecuador"] = counts
    cat["sitios_validacion"] = sitios_bp
    cat["zonas_prioritarias"] = zones
    cat["areas"] = area_meta
    cat["corrida_previa"] = {
        "modo_bandas": "todas_min",
        "ruta": "web/public/productos/corrida_previa_todas_min/",
        "acta": "docs/version_congelada_v1.md",
        "congelado_en": "2026-11-14T13:40:40-05:00",
    }
    # keep capas pointing at official root (full mosaic); areas have their own
    write_tabla(OUT_WEB / "tabla_validacion.csv", sitios_bp)

    # hashes after write
    official = [
        "catalogo.json", "tabla_validacion.csv",
        "delta_marte.png", "delta_marte.tif", "delta_luna.png", "delta_luna.tif",
        "clases.png", "clases.tif",
    ]
    # catalog written below after we know hashes of rasters first
    raster_files = official[2:]
    hashes = {f: sha256(OUT_WEB / f) for f in raster_files}
    hashes["tabla_validacion.csv"] = sha256(OUT_WEB / "tabla_validacion.csv")
    area_hashes = {}
    for key in areas:
        area_hashes[key] = {}
        for f in ("delta_marte.png", "delta_marte.tif", "delta_luna.png", "delta_luna.tif", "clases.png", "clases.tif"):
            area_hashes[key][f] = sha256(OUT_WEB / key / f)
    cat["huellas_sha256"] = hashes
    cat["huellas_areas_sha256"] = area_hashes
    (OUT_WEB / "catalogo.json").write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    hashes["catalogo.json"] = sha256(OUT_WEB / "catalogo.json")

    report = {
        "congelado_en": frozen_at,
        "modo_oficial": "banda_propia",
        "elevacion_modo": "absoluta",
        "verificacion_png_13_40": verif,
        "metricas_banda_propia": met_bp,
        "metricas_todas_min": met_tm,
        "aciertos": {"banda_propia": hits_bp, "todas_min": hits_tm, "n": n_auc},
        "umbrales_banda_propia": {
            "mars": ev_bp["thr"]["mars"].as_dict(),
            "moon": ev_bp["thr"]["moon"].as_dict(),
        },
        "d_max": ev_bp["d_max"],
        "delong_modos": delong_modos,
        "nulo": nulo,
        "clases_ecuador": counts,
        "areas": {k: {kk: vv for kk, vv in v.items() if kk != "capas"} for k, v in area_meta.items()},
        "yasuni": yas,
        "sha256": hashes,
        "sha256_areas": area_hashes,
        "nota": "La corrida con banda_propia se hizo después de ver el AUC de todas_min.",
    }
    (OUT_STATS / "resumen.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("congelado_en", frozen_at)
    print("hashes", json.dumps(hashes, indent=2))
    print("LISTO")


if __name__ == "__main__":
    main()
