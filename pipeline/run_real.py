#!/usr/bin/env python3
"""
Índice ANALOG/delta sobre datos reales (MOLA, LOLA, Copernicus GLO-90).

Ajusta parámetros y firmas solo sobre Marte y la Luna, fija el umbral en
la validación terrestre y, ya congelado, lo aplica a Ecuador.
No se reajusta nada con el mapa de Ecuador.
"""

from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import rasterio
from rasterio.enums import Resampling
from PIL import Image

from pipeline.generate_mock import colorize_class, colorize_delta, save_png
from pipeline.index import (
    CLASS_NAMES,
    MODO_BANDA_PROPIA,
    MODO_TODAS_MIN,
    choose_threshold,
    classify,
    delta_index,
    per_class_metrics,
)
from pipeline.metrics import bootstrap_auc_ci, delong_paired, null_abs_lat_auc
from pipeline.signatures import LatBand, assign_lat_band, build_signatures
from pipeline.standardize import fit_std_params

ROOT = Path("/workspace/analogs")
PROC = ROOT / "data" / "processed"
SITES_CSV = Path("/workspace/validacion_sitios.csv")
OUT_WEB = ROOT / "web" / "public" / "productos"
OUT_DOCS = ROOT / "docs"
TZ = ZoneInfo("America/Guayaquil")

BANDS = [
    LatBand("A", 0.0, 15.0),
    LatBand("B", 15.0, 30.0),
    LatBand("C", 30.0, 45.0),
    LatBand("D", 45.0, 60.0),
    LatBand("E", 60.0, 72.0),
    LatBand("F", 72.0, 80.0),
    LatBand("G", 80.0, 90.0),
]

INDEX_VARS = ("latitude", "elevation", "slope", "roughness")
NODATA = -9999.0
R_EARTH_KM = 6378.137

SITE_META = {
    "yungay": dict(
        nombre="Yungay, núcleo hiperárido del Atacama (Chile)",
        cita="Navarro-González et al. (2003), 10.1126/science.1089143; Ewing et al. (2006), 10.1016/j.gca.2006.08.020",
        excluido_auc=False, coordenada_no_verificada=False, folder="yungay",
    ),
    "haughton": dict(
        nombre="Estructura de impacto de Haughton, isla Devon (Nunavut, Canadá)",
        cita="Osinski et al. (2005), 10.1111/j.1945-5100.2005.tb00145.x",
        excluido_auc=False, coordenada_no_verificada=False, folder="haughton",
    ),
    "university_valley": dict(
        nombre="University Valley, Valles Secos de McMurdo (Antártida)",
        cita="Heldmann et al. (2013), 10.1016/j.pss.2013.05.019; Lapalme et al. (2017a), 10.1017/s0954102016000572",
        excluido_auc=False, coordenada_no_verificada=False, folder="university_valley",
    ),
    "askja": dict(
        nombre="Askja / colada basáltica Vikrahraun 1961 (Islandia)",
        cita="Blasizzo et al. (2022), 10.1186/s40623-022-01711-5, additional file 1, hoja '(1.1) Samples': punto medio de la colada Vikrahraun entre bocas (65.0647, -16.7247) y frente (65.0590, -16.5454). Se descarta el valor anterior 65.03, -16.78.",
        excluido_auc=False, coordenada_no_verificada=False, folder="askja",
    ),
    "mauna_kea": dict(
        nombre="Conos de ceniza de la cumbre de Mauna Kea (Hawái, EE. UU.)",
        cita="Guinness et al. (2007), 10.1029/2006je002822; ten Kate et al. (2013), 10.1061/(asce)as.1943-5525.0000200; Graham et al. (2015), 10.1016/j.asr.2015.01.024",
        excluido_auc=False, coordenada_no_verificada=False, folder="mauna_kea",
    ),
    "sverrefjell": dict(
        nombre="Sverrefjell, complejo volcánico de Bockfjorden (Svalbard, Noruega)",
        cita="Treiman et al. (2002), 10.1016/s0012-821x(02)00998-6",
        excluido_auc=False, coordenada_no_verificada=False, folder="sverrefjell",
    ),
    "timanfaya": dict(
        nombre="Parque Nacional de Timanfaya, Lanzarote (España)",
        cita="Martínez-Frías et al. (2017), 10.18814/epiiugs/2017/v40i4/017035; Alberquilla et al. (2022), 10.1038/s41598-022-20960-8",
        excluido_auc=False, coordenada_no_verificada=False, folder="timanfaya",
    ),
    "meteor_crater": dict(
        nombre="Meteor Crater (Barringer), Arizona (EE. UU.)",
        cita="Impact Earth (Western University), ficha Barringer; contexto en Osinski et al. (2023), 10.3389/fspas.2023.1186173",
        excluido_auc=False, coordenada_no_verificada=False, folder="meteor_crater",
    ),
    "sp_mountain": dict(
        nombre="S P Mountain (S P Crater), campo volcánico de San Francisco, Arizona (EE. UU.)",
        cita="Gullikson y Rumpf (2021), USGS OFR 2021-1072, https://pubs.usgs.gov/of/2021/1072/ofr20211072.pdf",
        excluido_auc=False, coordenada_no_verificada=False, folder="sp_mountain",
    ),
    "inferno_chasm": dict(
        nombre="Inferno Chasm, llanura de Snake River / entorno de Craters of the Moon, Idaho (EE. UU.)",
        cita="Garry et al. (2015), resumen LPSC 46, 1009 (coordenada de resumen, no de revista); Greeley (1971), 10.1126/science.172.3984.722",
        excluido_auc=False, coordenada_no_verificada=False, folder="inferno_chasm",
    ),
    "tapajos": dict(
        nombre="FLONA Tapajós, torre LBA km 67 (BR-Sa1), Amazonía (Brasil)",
        cita="AmeriFlux BR-Sa1, https://ameriflux.lbl.gov/sites/siteinfo/BR-Sa1 ; IGBP EBF",
        excluido_auc=False, coordenada_no_verificada=False, folder="tapajos",
    ),
    "bondville": dict(
        nombre="Bondville, Illinois (US-Bo1), llanura agrícola (EE. UU.)",
        cita="AmeriFlux US-Bo1, 10.17190/AMF/1246036 ; IGBP CRO",
        excluido_auc=False, coordenada_no_verificada=False, folder="bondville",
    ),
    "harvard_forest": dict(
        nombre="Harvard Forest EMS (US-Ha1), Massachusetts (EE. UU.)",
        cita="AmeriFlux US-Ha1, 10.17190/AMF/1246059 ; IGBP DBF",
        excluido_auc=False, coordenada_no_verificada=False, folder="harvard_forest",
    ),
    "tumbarumba": dict(
        nombre="Tumbarumba (AU-Tum), Nueva Gales del Sur (Australia)",
        cita="FLUXNET AU-Tum, 10.18140/FLX/1440126 ; IGBP EBF",
        excluido_auc=False, coordenada_no_verificada=False, folder="tumbarumba",
    ),
    "hainich": dict(
        nombre="Hainich (DE-Hai), Turingia (Alemania)",
        cita="FLUXNET DE-Hai, 10.18140/FLX/1440148 ; IGBP DBF",
        excluido_auc=False, coordenada_no_verificada=False, folder="hainich",
    ),
    "hyytiala": dict(
        nombre="Hyytiälä / SMEAR II (FI-Hyy), Finlandia",
        cita="FLUXNET FI-Hyy, 10.18140/FLX/1440158 ; IGBP ENF",
        excluido_auc=False, coordenada_no_verificada=False, folder="hyytiala",
    ),
}

# Sitios oficiales fuera del AUC de superficie: no hay ventanas GLO-90 procesadas.
EXCLUDED_SITES = [
    dict(
        id="rio_tinto",
        nombre="Peña de Hierro / cabecera del Río Tinto (Huelva, España)",
        lat=37.7267, lon=-6.5532, buffer_km=5, etiqueta="marciano",
        excluido_auc=True, coordenada_no_verificada=False,
        cita="Amils et al. (2014), 10.3390/life4030511; Fernández-Remolar et al. (2005), 10.1016/j.epsl.2005.09.043. Análogo solo geoquímico/mineralógico; excluido del AUC de superficie. Sin ventana GLO-90 en esta entrega.",
    ),
    dict(
        id="ries",
        nombre="Ries (Nördlinger Ries), Alemania",
        lat=48.8842, lon=10.5569, buffer_km=13, etiqueta="lunar",
        excluido_auc=True, coordenada_no_verificada=False,
        cita="Stöffler et al. (2013), 10.1111/maps.12086; IUGS Geoheritage. Cubeta con ciudad y agricultura; no usar como positivo de superficie. Sin ventana GLO-90 en esta entrega.",
    ),
    dict(
        id="sudbury",
        nombre="Cuenca de Sudbury, Ontario (Canadá)",
        lat=46.600, lon=-81.183, buffer_km=5, etiqueta="lunar",
        excluido_auc=True, coordenada_no_verificada=True,
        cita="Lowman (1992), 10.1029/92rg00755. Análogo geológico de cuenca tipo mare; cubierta de bosque, lagos y área urbana. Coordenada de catálogo no verificada en ficha PASSC. Excluido del AUC de superficie. Sin ventana GLO-90 en esta entrega.",
    ),
]

PRIORITY_SEEDS = [
    {"id": "chimborazo", "nombre": "Chimborazo (arenal y páramo)", "lat": -1.47, "lon": -78.82},
    {"id": "cotopaxi", "nombre": "Cotopaxi (páramo)", "lat": -0.68, "lon": -78.44},
    {"id": "antisana", "nombre": "Antisana", "lat": -0.48, "lon": -78.14},
    {"id": "el_altar", "nombre": "El Altar", "lat": -1.67, "lon": -78.41},
    {"id": "quilotoa", "nombre": "Quilotoa", "lat": -0.85, "lon": -78.90},
    {"id": "fernandina", "nombre": "Fernandina (Galápagos)", "lat": -0.37, "lon": -91.55},
    {"id": "cayambe", "nombre": "Cayambe", "lat": 0.03, "lon": -77.99},
    {"id": "sincholagua", "nombre": "Sincholagua", "lat": -0.54, "lon": -78.37},
]

PAL_MARS = [(20, 10, 8), (80, 30, 22), (150, 55, 35), (210, 100, 50), (240, 180, 90)]
PAL_MOON = [(12, 12, 14), (50, 52, 58), (110, 110, 118), (180, 178, 172), (236, 232, 222)]

AGREGACION_DOC = (
    "Mediana de las celdas válidas cuyo centro cae dentro del buffer (distancia "
    "haversina, radio oficial, R=6378.137 km). Una celda es válida si elevación, "
    "pendiente y TRI son finitos y distintos de nodata (−9999). También se guarda "
    "la celda central (vecina más cercana al punto oficial) como referencia, pero "
    "el índice y el umbral usan la mediana del buffer. No se elige la «mejor» "
    "celda del buffer, para no inflar el AUC."
)


def now_iso() -> str:
    local = datetime.now(TZ)
    return local.strftime("%Y-%m-%dT%H:%M:%S-05:00")


def jsonable(obj):
    if isinstance(obj, dict):
        return {k: jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(v) for v in obj]
    if isinstance(obj, np.generic):
        v = obj.item()
        if isinstance(v, float) and not math.isfinite(v):
            return None
        return v
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    return obj


def haversine_km(lat1, lon1, lat2, lon2):
    p1, l1, p2, l2 = map(np.radians, (lat1, lon1, lat2, lon2))
    dphi = p2 - p1
    dl = l2 - l1
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * R_EARTH_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def load_npz(body: str) -> dict[str, np.ndarray]:
    path = PROC / body / f"{body}_latband_samples.npz"
    z = np.load(path, allow_pickle=True)
    cols = [str(c) for c in z["columns"]]
    data = z["data"]
    out = {c: data[:, i].astype(float) for i, c in enumerate(cols)}
    return out


def samples_by_band(values: dict[str, np.ndarray], variables: tuple[str, ...]) -> dict:
    lat = values["latitude"]
    names = assign_lat_band(lat, BANDS)
    out = {}
    for b in BANDS:
        m = names == b.name
        sample = {v: values[v][m] for v in variables}
        sample["latitude"] = np.abs(values["latitude"][m]) if "latitude" in variables else np.abs(lat[m])
        sample["_n"] = np.array([int(m.sum())])
        sample["_short"] = np.array([m.sum() < 50])
        out[b.name] = sample
    return out


def valid_mask(arr: np.ndarray, nodata: float | None = NODATA) -> np.ndarray:
    m = np.isfinite(arr)
    if nodata is not None:
        m &= arr != nodata
    return m


def read_band(path: Path) -> tuple[np.ndarray, object, float | None]:
    with rasterio.open(path) as ds:
        a = ds.read(1).astype(np.float32)
        if ds.nodata is not None:
            a = np.where(a == ds.nodata, np.nan, a)
        return a, ds.transform, ds.profile, ds.nodata


def pixel_centers(transform, shape):
    rows, cols = np.indices(shape)
    # affine: x = a*col + c, y = e*row + f  (north-up)
    lon = transform.c + (cols + 0.5) * transform.a + (rows + 0.5) * transform.b
    lat = transform.f + (cols + 0.5) * transform.d + (rows + 0.5) * transform.e
    return lon, lat


def extract_site(site_id: str, lat0: float, lon0: float, buffer_km: float) -> dict:
    root = PROC / "earth" / "validation" / site_id
    layers = {}
    transform = None
    for key, fname in {
        "elevation": f"{site_id}_elevation_1km.tif",
        "slope": f"{site_id}_slope_1km.tif",
        "roughness": f"{site_id}_roughness_1km.tif",
        "relative_relief": f"{site_id}_relative_relief_1km.tif",
        "latitude": f"{site_id}_latitude_1km.tif",
    }.items():
        arr, transform, _, _ = read_band(root / fname)
        layers[key] = arr
    lon, lat = pixel_centers(transform, layers["elevation"].shape)
    dist = haversine_km(lat0, lon0, lat, lon)
    ok = (
        valid_mask(layers["elevation"])
        & valid_mask(layers["slope"])
        & valid_mask(layers["roughness"])
        & (dist <= buffer_km)
    )
    # celda central: más cercana al punto, con datos si es posible
    order = np.argsort(dist.ravel())
    center = None
    for idx in order[:50]:
        i, j = np.unravel_index(idx, dist.shape)
        if valid_mask(layers["elevation"])[i, j] and valid_mask(layers["slope"])[i, j] and valid_mask(layers["roughness"])[i, j]:
            center = (i, j)
            break
    if center is None:
        i, j = np.unravel_index(order[0], dist.shape)
        center = (i, j)

    def pack(arr):
        vals = arr[ok]
        ci, cj = center
        return {
            "mediana_buffer": float(np.median(vals)) if vals.size else float("nan"),
            "q1_buffer": float(np.percentile(vals, 25)) if vals.size else float("nan"),
            "q3_buffer": float(np.percentile(vals, 75)) if vals.size else float("nan"),
            "celda_central": float(arr[ci, cj]) if np.isfinite(arr[ci, cj]) else float("nan"),
            "n_celdas": int(vals.size),
        }

    out = {
        "n_celdas_buffer": int(ok.sum()),
        "distancia_celda_central_km": float(dist[center]),
        "elevation": pack(layers["elevation"]),
        "slope": pack(layers["slope"]),
        "roughness": pack(layers["roughness"]),
        "relative_relief": pack(layers["relative_relief"]),
        "latitude_celda_central": float(lat[center]),
        "longitude_celda_central": float(lon[center]),
    }
    return out


def label_to_class(etiqueta: str) -> str:
    return {"marciano": "marte", "lunar": "luna", "ambos": "ambos", "no_analogo": "ninguno"}.get(etiqueta, "ninguno")


def y_pos(etiqueta: str, body: str) -> int:
    if etiqueta == "ambos":
        return 1
    if body == "mars":
        return 1 if etiqueta == "marciano" else 0
    return 1 if etiqueta == "lunar" else 0


def build_reference(elevacion_modo: str):
    """std_params y firmas congelados sobre las muestras de Marte y de la Luna."""
    refs = {}
    params = {}
    sigs = {}
    frozen = now_iso()
    for body in ("mars", "moon"):
        raw = load_npz(body)
        vals = {
            "latitude": np.abs(raw["latitude"]),
            "elevation": raw["relative_relief_m"] if elevacion_modo == "relieve_relativo" else raw["elevation_m"],
            "slope": raw["slope_deg"],
            "roughness": raw["roughness_tri_m"],
        }
        params[body] = fit_std_params(vals, body_ref=body, method="zscore", frozen_at=frozen)
        by_band = samples_by_band({**vals, "latitude": np.abs(raw["latitude"])}, INDEX_VARS)
        sigs[body] = build_signatures(body, by_band, INDEX_VARS)
        refs[body] = vals
    return params, sigs, refs, frozen


def evaluar(sites, params, sigs, modo, variables, elevacion_modo):
    def feat_val(s, key):
        if not s.get("feat"):
            return float("nan")
        return float(s["feat"][key]["mediana_buffer"])

    elev_key = "relative_relief" if elevacion_modo == "relieve_relativo" else "elevation"
    vals = {
        "latitude": np.array([s["lat"] for s in sites], float),
        "elevation": np.array([feat_val(s, elev_key) for s in sites], float),
        "slope": np.array([feat_val(s, "slope") for s in sites], float),
        "roughness": np.array([feat_val(s, "roughness") for s in sites], float),
    }
    site_bands = assign_lat_band(vals["latitude"], BANDS)
    in_auc = np.array([not s["excluido_auc"] and s.get("feat") is not None for s in sites], bool)

    dist, delta, win = {}, {}, {}
    # primera pasada con d_max=1 para estimar d_max en positivos del AUC
    for body in ("mars", "moon"):
        d, _, w = delta_index(
            vals, sigs[body], params[body], site_bands, body,
            variables=variables, d_max=1.0, modo_bandas=modo, use_abs_lat=True,
        )
        dist[body], win[body] = d, w
    d_max = {}
    for body in ("mars", "moon"):
        y = np.array([y_pos(s["etiqueta"], body) for s in sites], int)
        dpos = dist[body][in_auc & (y == 1) & np.isfinite(dist[body])]
        d_max[body] = float(np.nanmax(dpos) * 1.15) if dpos.size else 1.0
        if not np.isfinite(d_max[body]) or d_max[body] <= 0:
            d_max[body] = 1.0
        d, dl, w = delta_index(
            vals, sigs[body], params[body], site_bands, body,
            variables=variables, d_max=d_max[body], modo_bandas=modo, use_abs_lat=True,
        )
        dist[body], delta[body], win[body] = d, dl, w

    y_m = np.array([y_pos(s["etiqueta"], "mars") for s in sites], int)
    y_l = np.array([y_pos(s["etiqueta"], "moon") for s in sites], int)
    thr = {
        "mars": choose_threshold(delta["mars"][in_auc], y_m[in_auc], metric="youden", d_max=d_max["mars"]),
        "moon": choose_threshold(delta["moon"][in_auc], y_l[in_auc], metric="youden", d_max=d_max["moon"]),
    }
    clas = classify(delta["mars"], delta["moon"], thr["mars"].threshold, thr["moon"].threshold)
    return {
        "vals": vals, "bands": site_bands, "in_auc": in_auc,
        "dist": dist, "delta": delta, "win": win, "d_max": d_max, "thr": thr, "clas": clas,
        "y_mars": y_m, "y_moon": y_l,
    }


def metricas_de(ev, etiqueta: str) -> dict:
    ia = ev["in_auc"]
    out = {"etiqueta": etiqueta, "d_max": ev["d_max"]}
    for body, key in (("mars", "marte"), ("moon", "luna")):
        y = ev[f"y_{body}"][ia]
        s = ev["delta"][body][ia]
        ci = bootstrap_auc_ci(y, s, n_boot=2000, seed=2026)
        d = ev["thr"][body].as_dict()
        d["ic95_inferior"] = ci["ic95_inferior"]
        d["ic95_superior"] = ci["ic95_superior"]
        d["n_bootstrap"] = ci["n_bootstrap"]
        out[key] = d
    return out


def load_ecuador():
    layers = {}
    profile = None
    transform = None
    for key, name in {
        "elevation": "ecuador_elevation_1km.tif",
        "slope": "ecuador_slope_1km.tif",
        "roughness": "ecuador_roughness_1km.tif",
        "relative_relief": "ecuador_relative_relief_1km.tif",
        "latitude": "ecuador_latitude_1km.tif",
    }.items():
        arr, transform, profile, _ = read_band(PROC / "earth" / name)
        layers[key] = arr
    lon, lat = pixel_centers(transform, layers["elevation"].shape)
    # si el ráster de latitud está bien, úsalo; si no, las coordenadas del affine
    lat_r = layers["latitude"]
    use_lat = np.where(valid_mask(lat_r), lat_r, lat)
    mask = valid_mask(layers["elevation"]) & valid_mask(layers["slope"]) & valid_mask(layers["roughness"])
    bounds = rasterio.transform.array_bounds(layers["elevation"].shape[0], layers["elevation"].shape[1], transform)
    # array_bounds returns (west, south, east, north)
    return layers, lon, use_lat, mask, profile, transform, bounds


def write_cog(path: Path, arr: np.ndarray, profile: dict, nodata: float = NODATA):
    data = np.where(np.isfinite(arr), arr, nodata).astype(np.float32)
    prof = dict(profile)
    prof.update(
        driver="GTiff",
        dtype="float32",
        count=1,
        nodata=nodata,
        compress="deflate",
        tiled=True,
        blockxsize=256,
        blockysize=256,
        predictor=3,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", **prof) as dst:
        dst.write(data, 1)
        dst.build_overviews([2, 4, 8], Resampling.average)
        dst.update_tags(ns="rio_overview", resampling="average")


def zone_from_cell(i, j, lat, lon, layers, mask, delta_m, delta_l, clas, win_m, win_l, bands, seed=None):
    if not mask[i, j]:
        return None
    cl = CLASS_NAMES[int(clas[i, j])]
    return {
        "id": seed["id"] if seed else f"celda_{i}_{j}",
        "nombre": seed["nombre"] if seed else f"Celda {lat[i, j]:.3f}°, {lon[i, j]:.3f}°",
        "lat": round(float(lat[i, j] if seed is None else seed["lat"]), 4),
        "lon": round(float(lon[i, j] if seed is None else seed["lon"]), 4),
        "banda_latitud": str(bands[i, j]),
        "banda_ganadora_marte": str(win_m[i, j]),
        "banda_ganadora_luna": str(win_l[i, j]),
        "elevacion_m": round(float(layers["elevation"][i, j]), 1),
        "pendiente_deg": round(float(layers["slope"][i, j]), 2),
        "rugosidad_tri": round(float(layers["roughness"][i, j]), 2),
        "relieve_relativo_m": round(float(layers["relative_relief"][i, j]), 2) if np.isfinite(layers["relative_relief"][i, j]) else None,
        "delta_marte": round(float(delta_m[i, j]), 4),
        "delta_luna": round(float(delta_l[i, j]), 4),
        "clase": cl,
        "firma_superficie": {
            "latitud": round(float(lat[i, j] if seed is None else seed["lat"]), 4),
            "elevacion_m": round(float(layers["elevation"][i, j]), 1),
            "pendiente_deg": round(float(layers["slope"][i, j]), 2),
            "rugosidad_tri": round(float(layers["roughness"][i, j]), 2),
        },
        "clima": {
            "disponible": False,
            "advertencia": "Capa de interpretación no publicada en esta entrega. No hay un producto climático homologable incluido; no se muestra un ejemplo sintético para no confundirlo con un dato real. El clima no entra al índice.",
            "nota": "El índice ANALOG/delta es solo de superficie (latitud, elevación, pendiente y rugosidad).",
        },
    }


def nearest_valid(lat0, lon0, lat, lon, mask):
    d = haversine_km(lat0, lon0, lat, lon)
    d = np.where(mask, d, np.inf)
    idx = int(np.argmin(d))
    return np.unravel_index(idx, mask.shape)


def main() -> None:
    OUT_WEB.mkdir(parents=True, exist_ok=True)
    OUT_DOCS.mkdir(parents=True, exist_ok=True)
    frozen_at = now_iso()
    print("Cargando sitios y ventanas…")

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

    print("Ajustando std_params y firmas (absoluta y relieve_relativo)…")
    params_abs, sigs_abs, _, frozen_abs = build_reference("absoluta")
    params_rel, sigs_rel, _, frozen_rel = build_reference("relieve_relativo")

    variants_cfg = [
        ("todas_min_con_latitud", MODO_TODAS_MIN, INDEX_VARS, "absoluta", params_abs, sigs_abs, "todas_min, vector con |lat|, elevación absoluta (defecto)"),
        ("banda_propia_con_latitud", MODO_BANDA_PROPIA, INDEX_VARS, "absoluta", params_abs, sigs_abs, "banda_propia, vector con |lat|, elevación absoluta"),
        ("todas_min_sin_latitud", MODO_TODAS_MIN, ("elevation", "slope", "roughness"), "absoluta", params_abs, sigs_abs, "todas_min, sin latitud en el vector, elevación absoluta"),
        ("banda_propia_sin_latitud", MODO_BANDA_PROPIA, ("elevation", "slope", "roughness"), "absoluta", params_abs, sigs_abs, "banda_propia, sin latitud en el vector, elevación absoluta"),
        ("todas_min_con_latitud_relieve_relativo", MODO_TODAS_MIN, INDEX_VARS, "relieve_relativo", params_rel, sigs_rel, "todas_min, vector con |lat|, relieve relativo"),
        ("banda_propia_con_latitud_relieve_relativo", MODO_BANDA_PROPIA, INDEX_VARS, "relieve_relativo", params_rel, sigs_rel, "banda_propia, vector con |lat|, relieve relativo"),
        ("todas_min_sin_latitud_relieve_relativo", MODO_TODAS_MIN, ("elevation", "slope", "roughness"), "relieve_relativo", params_rel, sigs_rel, "todas_min, sin latitud, relieve relativo"),
        ("banda_propia_sin_latitud_relieve_relativo", MODO_BANDA_PROPIA, ("elevation", "slope", "roughness"), "relieve_relativo", params_rel, sigs_rel, "banda_propia, sin latitud, relieve relativo"),
    ]

    evals = {}
    for key, modo, variables, emodo, params, sigs, label in variants_cfg:
        print(f"  Validación {key}…")
        ev = evaluar(sites, params, sigs, modo, variables, emodo)
        ev["label"] = label
        ev["modo"] = modo
        ev["variables"] = variables
        ev["elevacion_modo"] = emodo
        ev["params"] = params
        ev["sigs"] = sigs
        evals[key] = ev

    DEFAULT = "todas_min_con_latitud"
    ev0 = evals[DEFAULT]
    # Congelar umbral y d_max del modo por defecto ANTES de Ecuador
    d_max_frozen = ev0["d_max"]
    thr_frozen = ev0["thr"]
    print(
        f"Umbrales congelados: Marte={thr_frozen['mars'].threshold:.3f} "
        f"AUC={thr_frozen['mars'].auc:.3f}; Luna={thr_frozen['moon'].threshold:.3f} "
        f"AUC={thr_frozen['moon'].auc:.3f}"
    )

    metricas_por_variante = {k: metricas_de(v, v["label"]) for k, v in evals.items()}
    ia = ev0["in_auc"]
    delong = {
        "marte_con_vs_sin_latitud": delong_paired(
            ev0["y_mars"][ia], ev0["delta"]["mars"][ia], evals["todas_min_sin_latitud"]["delta"]["mars"][ia]
        ),
        "luna_con_vs_sin_latitud": delong_paired(
            ev0["y_moon"][ia], ev0["delta"]["moon"][ia], evals["todas_min_sin_latitud"]["delta"]["moon"][ia]
        ),
        "marte_absoluta_vs_relieve_relativo": delong_paired(
            ev0["y_mars"][ia], ev0["delta"]["mars"][ia],
            evals["todas_min_con_latitud_relieve_relativo"]["delta"]["mars"][ia],
        ),
        "luna_absoluta_vs_relieve_relativo": delong_paired(
            ev0["y_moon"][ia], ev0["delta"]["moon"][ia],
            evals["todas_min_con_latitud_relieve_relativo"]["delta"]["moon"][ia],
        ),
    }
    nulo = {
        "marte": null_abs_lat_auc(ev0["y_mars"][ia], ev0["vals"]["latitude"][ia]),
        "luna": null_abs_lat_auc(ev0["y_moon"][ia], ev0["vals"]["latitude"][ia]),
        "nota": "Modelo nulo: el puntaje es solo |lat|. Los positivos de este conjunto tienden a latitudes altas y podrían inflar el AUC del índice si la latitud domina.",
    }

    # --- Ecuador (umbrales ya congelados; no se reajustan) ---------------
    print("Aplicando umbral congelado a Ecuador…")
    layers, lon2d, lat2d, mask, profile, transform, bounds = load_ecuador()
    west, south, east, north = bounds
    flat_idx = np.flatnonzero(mask)
    # valores solo en tierra para el índice; luego reinyectar
    def pack_vals(elevacion_modo):
        elev = layers["relative_relief"] if elevacion_modo == "relieve_relativo" else layers["elevation"]
        return {
            "latitude": lat2d[mask],
            "elevation": elev[mask],
            "slope": layers["slope"][mask],
            "roughness": layers["roughness"][mask],
        }

    grid_bands_full = np.full(mask.shape, "", dtype=object)
    grid_bands_full[mask] = assign_lat_band(lat2d[mask], BANDS)

    def ecuador_for(ev):
        vals = pack_vals(ev["elevacion_modo"])
        bands = grid_bands_full[mask]
        out_d, out_delta, out_win = {}, {}, {}
        for body in ("mars", "moon"):
            d, dl, w = delta_index(
                vals, ev["sigs"][body], ev["params"][body], bands, body,
                variables=ev["variables"], d_max=ev["d_max"][body],
                modo_bandas=ev["modo"], use_abs_lat=True,
            )
            D = np.full(mask.shape, np.nan); D[mask] = d
            DL = np.full(mask.shape, np.nan); DL[mask] = dl
            W = np.full(mask.shape, "", dtype=object); W[mask] = w
            out_d[body], out_delta[body], out_win[body] = D, DL, W
        clas = classify(
            out_delta["mars"], out_delta["moon"],
            ev["thr"]["mars"].threshold, ev["thr"]["moon"].threshold,
            valid_mask=mask,
        )
        counts = {CLASS_NAMES[k]: int((clas == k).sum()) for k in (0, 1, 2, 3, -1)}
        return out_delta, out_win, clas, counts

    delta_grid, win_grid, clas, counts_default = ecuador_for(ev0)
    print("Clases Ecuador (defecto):", counts_default)

    # conteos de las demás variantes (diagnóstico; no se usan para reajustar)
    clases_por_variante = {DEFAULT: counts_default}
    for key, ev in evals.items():
        if key == DEFAULT:
            continue
        print(f"  Ecuador diagnóstico {key}…")
        _, _, _, counts = ecuador_for(ev)
        clases_por_variante[key] = counts
        print("   ", counts)

    # PNG + COG del modo por defecto
    save_png(OUT_WEB / "delta_marte.png", colorize_delta(delta_grid["mars"], mask, PAL_MARS))
    save_png(OUT_WEB / "delta_luna.png", colorize_delta(delta_grid["moon"], mask, PAL_MOON))
    save_png(OUT_WEB / "clases.png", colorize_class(clas, mask))
    write_cog(OUT_WEB / "delta_marte.tif", delta_grid["mars"], profile)
    write_cog(OUT_WEB / "delta_luna.tif", delta_grid["moon"], profile)
    write_cog(OUT_WEB / "clases.tif", clas.astype(np.float32), profile, nodata=-1)

    # variante banda_propia (absoluta, con lat) para poder cambiar rápido
    ev_own = evals["banda_propia_con_latitud"]
    d_own, _, c_own, counts_own = ecuador_for(ev_own)
    own_dir = OUT_WEB / "banda_propia"
    own_dir.mkdir(exist_ok=True)
    save_png(own_dir / "delta_marte.png", colorize_delta(d_own["mars"], mask, PAL_MARS))
    save_png(own_dir / "delta_luna.png", colorize_delta(d_own["moon"], mask, PAL_MOON))
    save_png(own_dir / "clases.png", colorize_class(c_own, mask))

    # zonas prioritarias
    zones = []
    for seed in PRIORITY_SEEDS:
        i, j = nearest_valid(seed["lat"], seed["lon"], lat2d, lon2d, mask)
        z = zone_from_cell(i, j, lat2d, lon2d, layers, mask, delta_grid["mars"], delta_grid["moon"], clas, win_grid["mars"], win_grid["moon"], grid_bands_full, seed)
        if z:
            # usar las coordenadas oficiales del hito, no las de la celda
            z["lat"] = seed["lat"]
            z["lon"] = seed["lon"]
            zones.append(z)

    def add_extreme(kind, arr):
        scored = np.where(mask, arr, np.nan)
        if not np.isfinite(scored).any():
            return
        i, j = np.unravel_index(int(np.nanargmax(scored)), scored.shape)
        already = any(haversine_km(z["lat"], z["lon"], float(lat2d[i, j]), float(lon2d[i, j])) < 15 for z in zones)
        if already:
            return
        z = zone_from_cell(i, j, lat2d, lon2d, layers, mask, delta_grid["mars"], delta_grid["moon"], clas, win_grid["mars"], win_grid["moon"], grid_bands_full, None)
        if z:
            z["id"] = f"max_{kind}"
            z["nombre"] = f"Máxima similitud a {'Marte' if kind=='marte' else 'la Luna'} ({z['lat']}°, {z['lon']}°)"
            zones.append(z)

    add_extreme("marte", delta_grid["mars"])
    add_extreme("luna", delta_grid["moon"])
    # ordenar: análogos primero, luego por max delta
    order = {"marte": 0, "luna": 1, "ambos": 2, "ninguno": 3}
    zones.sort(key=lambda z: (order.get(z["clase"], 9), -max(z["delta_marte"], z["delta_luna"])))

    # sitios de validación para el catálogo (modo por defecto)
    sitios_out = []
    known_ok = 0
    known_auc = 0
    for i, s in enumerate(sites):
        known = label_to_class(s["etiqueta"])
        if ev0["clas"][i] < 0 or s["feat"] is None:
            pred = "ninguno"
            dm = dl = dist_m = dist_l = float("nan")
            acierto = False
            band = str(assign_lat_band(s["lat"], BANDS))
            win_m = win_l = ""
        else:
            pred = CLASS_NAMES[int(ev0["clas"][i])]
            dm = float(ev0["delta"]["mars"][i])
            dl = float(ev0["delta"]["moon"][i])
            dist_m = float(ev0["dist"]["mars"][i])
            dist_l = float(ev0["dist"]["moon"][i])
            acierto = pred == known
            band = str(ev0["bands"][i])
            win_m = str(ev0["win"]["mars"][i])
            win_l = str(ev0["win"]["moon"][i])
        entra = (not s["excluido_auc"]) and s["feat"] is not None
        if entra:
            known_auc += 1
            known_ok += int(acierto)
        feat = s["feat"] or {}
        sitios_out.append({
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
            "modo_bandas": MODO_TODAS_MIN,
        })

    n_land = int(mask.sum())
    rows, cols = mask.shape
    res_deg = float(abs(transform.a))

    aviso = (
        "Datos reales de superficie: MOLA MEGDR 64 ppd (Marte), LOLA LDEM_64 v3.1 (Luna) y "
        "Copernicus DEM GLO-90 (Tierra: Ecuador, Galápagos y ventanas de validación), remuestreados a ~1 km. "
        "Pendiente y TRI recalculados sobre el DEM remuestreado. Askja entra al AUC con 65.060, −16.640 "
        "(buffer 6 km; Blasizzo et al., 2022). El clima no entra al índice y no se muestra un ráster climático en esta entrega."
    )
    limitaciones = [
        "La analogía es solo de superficie y únicamente con las variables comparables. No se puede llamar «clima análogo» al índice.",
        "La resolución única de ~1 km suaviza el relieve local (Andes, Meteor Crater ~1.2 km de diámetro, University Valley con buffer de 3 km).",
        "Marte se remuestrea de ~926 m (64 ppd) a ~1 km; no se usó el MEGDR de 128 ppd.",
        "Luna: de ~474 m (LDEM_64) a ~1 km; no se descargó el LDEM de 128 ppd.",
        "Cobertura MOLA: interpolación entre huellas y datos más pobres por encima de ~87° de latitud.",
        "LDEM 64: posibles artefactos en los bordes de las bandas de 45°. Datum vertical = esfera, no geoide lunar.",
        "Los datums verticales no son homologables al metro (areoide MOLA, esfera lunar de 1737.4 km, geoide EGM2008). La variante relieve_relativo está calculada pero no es el modo por defecto (pendiente de decisión del equipo, §3).",
        "En Tierra, el 0 m exacto de GLO-90 se enmascaró; costa y agua interior pueden perder celdas.",
        "Inferno Chasm usa una coordenada de resumen LPSC, no de revista.",
        "Albedo e inercia térmica no entran al índice v1 (veredicto de Expertos) y no se descargaron.",
        "Pendiente y TRI en proyección equirrectangular cerca de los polos son más inciertos (banda G).",
        "No hay un ráster global terrestre: solo Ecuador/Galápagos y las ventanas de validación.",
        "Modo de bandas por defecto: todas_min (pendiente de confirmación de Ronald sobre el §5). Los umbrales se fijaron con la misma regla y se congelaron antes de Ecuador.",
        "Río Tinto, Ries y Sudbury se listan pero no entran al AUC (análogos no de superficie o cobertura actual no comparable); no hay ventanas GLO-90 suyas en esta entrega.",
    ]

    # métricas de validación del modo por defecto
    pred_auc = [s for s in sitios_out if s["entra_al_auc"]]
    precision_por_clase = per_class_metrics(
        [s["clase_conocida"] for s in pred_auc],
        [s["clase_predicha"] for s in pred_auc],
    )
    catalog = {
        "mock": False,
        "aviso": aviso,
        "metric_version": "ANALOG/delta v1 real 2026-11-14",
        "congelado_en": frozen_at,
        "agregacion_validacion": AGREGACION_DOC,
        "grilla": {
            "resolucion_objetivo_m": 1000,
            "resolucion_deg": res_deg,
            "resolucion_mock_deg": res_deg,  # compat. con la UI anterior
            "nota": "Grilla geográfica de Ecuador+Galápagos a 0.01° (~1 km). Copernicus GLO-90 remuestreado; pendiente y TRI recalculados.",
            "sistema": "EPSG:4326 (WGS84)",
            "filas": rows,
            "columnas": cols,
            "n_celdas_tierra": n_land,
            "extension": {"oeste": west, "norte": north, "este": east, "sur": south},
        },
        "variables_indice": list(INDEX_VARS),
        "pesos_por_defecto": {v: 0.25 for v in INDEX_VARS},
        "variables": [
            {"nombre": "latitude", "unidad": "°", "in_index": True, "nota": "Entra como |lat|."},
            {"nombre": "elevation", "unidad": "m", "in_index": True, "nota": "Datum: areoide MOLA / esfera lunar 1737.4 km / geoide EGM2008. Modo por defecto: absoluta."},
            {"nombre": "slope", "unidad": "°", "in_index": True, "nota": "Horn 3×3 sobre el DEM remuestreado."},
            {"nombre": "roughness", "unidad": "m", "in_index": True, "nota": "TRI de Wilson 3×3 sobre el DEM remuestreado."},
        ],
        "bandas_latitud": [{"nombre": b.name, "abs_lat_min": b.abs_lat_min, "abs_lat_max": b.abs_lat_max} for b in BANDS],
        "std_params": {
            body: [p.as_dict() for p in params_abs[body]] for body in ("mars", "moon")
        },
        "signatures": {
            body: [s.as_dict() for s in sigs_abs[body]] for body in ("mars", "moon")
        },
        "d_max": d_max_frozen,
        "umbrales": {"mars": thr_frozen["mars"].as_dict(), "moon": thr_frozen["moon"].as_dict()},
        "metricas_validacion": {
            "marte": {k: getattr(thr_frozen["mars"], k) if hasattr(thr_frozen["mars"], k) else thr_frozen["mars"].as_dict().get(k) for k in ("threshold", "sensitivity", "precision", "auc", "agreement")},
            "luna": {k: getattr(thr_frozen["moon"], k) if hasattr(thr_frozen["moon"], k) else thr_frozen["moon"].as_dict().get(k) for k in ("threshold", "sensitivity", "precision", "auc", "agreement")},
            "precision_por_clase": precision_por_clase,
            "aciertos": known_ok,
            "aciertos_auc": known_ok,
            "n_sitios_auc": known_auc,
            "n_sitios": len(sitios_out),
        },
        "metricas_por_variante": metricas_por_variante,
        "metricas_sensibilidad": metricas_por_variante,
        "delong_pareado": delong,
        "modelo_nulo_solo_abs_lat": nulo,
        "incluir_askja": True,
        "elevacion_modo": "absoluta",
        "elevacion_modos_disponibles": ["absoluta", "relieve_relativo"],
        "modo_bandas": MODO_TODAS_MIN,
        "nota_modo_bandas": "todas_min es el defecto, pendiente de confirmación de Ronald sobre el §5. Solo es válida con distancia euclídea; si se usara Mahalanobis por banda, la latitud saldría del vector automáticamente.",
        "clases_ecuador": counts_default,
        "clases_ecuador_por_variante": clases_por_variante,
        "sitios_validacion": sitios_out,
        "zonas_prioritarias": zones,
        "capas": {
            "similitud-marte": {"archivo": "/productos/delta_marte.png", "tipo": "png", "cuerpo": "mars"},
            "similitud-luna": {"archivo": "/productos/delta_luna.png", "tipo": "png", "cuerpo": "moon"},
            "clases": {"archivo": "/productos/clases.png", "tipo": "png"},
        },
        "capa_clima": {
            "disponible": False,
            "etiqueta": "interpretación, no entra al índice",
            "nota": "No se publica un ráster climático en esta entrega para no presentar un ejemplo sintético como si fuera real.",
        },
        "limitaciones": limitaciones,
        "nota_de_incertidumbre": (
            "Índice v1 solo de superficie (latitud, elevación, pendiente, rugosidad). "
            "Datums verticales no homologables al metro; la variante de relieve relativo está calculada y no es el defecto. "
            "Resolución ~1 km suaviza Meteor Crater, conos y el relieve andino. "
            "Askja entra al AUC (65.060, −16.640, buffer 6 km). "
            "Banda A sin positivos terrestres (Ecuador se evalúa, no se calibra ahí). Banda D débil; banda G sin estaciones, añadida por el polo sur lunar. "
            "Umbrales fijados con la regla del mínimo entre bandas en validación y congelados antes de Ecuador. "
            "Ver docs/nota_incertidumbre.md."
        ),
        "fuentes": {
            "mars": "MGS MOLA MEGDR 64 ppd, areoide GMM3/mgm1025",
            "moon": "LRO LOLA LDEM_64 v3.1, esfera 1737.4 km",
            "earth": "Copernicus DEM GLO-90 (EGM2008)",
        },
    }

    # arreglo precision_por_clase si no es JSON-friendly
    (OUT_WEB / "catalogo.json").write_text(
        json.dumps(jsonable(catalog), ensure_ascii=False, indent=2), encoding="utf-8"
    )

    fieldnames = [
        "sitio", "latitud", "longitud", "buffer_km", "banda_latitud",
        "banda_ganadora_marte", "banda_ganadora_luna", "elevacion_m",
        "pendiente_deg", "rugosidad_tri", "relieve_relativo_m", "n_celdas_buffer",
        "agregacion", "etiqueta_conocida", "clase_conocida", "delta_marte",
        "delta_luna", "clase_predicha", "acierto", "entra_al_auc", "excluido_auc",
        "coordenada_no_verificada", "cita", "es_mock_superficies", "modo_bandas",
    ]
    csv_paths = [
        OUT_WEB / "tabla_validacion.csv",
        ROOT / "tabla_validacion.csv",
        Path("/workspace/tabla_validacion.csv"),
    ]
    for path in csv_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for s in sitios_out:
                nbuf = None
                if s["agregacion"] and s["agregacion"].get("detalle"):
                    nbuf = s["agregacion"]["detalle"].get("n_celdas_buffer")
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
                    "n_celdas_buffer": nbuf if nbuf is not None else "",
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
                    "es_mock_superficies": "no",
                    "modo_bandas": s["modo_bandas"],
                })

    # resumen en stdout
    print("\n=== MÉTRICAS REALES ===")
    for k, m in metricas_por_variante.items():
        print(
            f"{k}: Marte AUC={m['marte']['auc']:.3f} [{m['marte'].get('ic95_inferior')}, {m['marte'].get('ic95_superior')}] "
            f"thr={m['marte']['threshold']:.3f} sens={m['marte']['sensitivity']:.3f} prec={m['marte']['precision']:.3f} | "
            f"Luna AUC={m['luna']['auc']:.3f} [{m['luna'].get('ic95_inferior')}, {m['luna'].get('ic95_superior')}] "
            f"thr={m['luna']['threshold']:.3f} sens={m['luna']['sensitivity']:.3f} prec={m['luna']['precision']:.3f}"
        )
    print("DeLong:", json.dumps(jsonable(delong), ensure_ascii=False, indent=2))
    print("Nulo |lat|:", json.dumps(jsonable(nulo), ensure_ascii=False, indent=2))
    print("Aciertos AUC:", known_ok, "/", known_auc)
    print("Clases Ecuador defecto:", counts_default)
    print("Clases por variante:", json.dumps(jsonable(clases_por_variante), ensure_ascii=False))
    print("Zonas:", [(z["nombre"], z["clase"], z["delta_marte"], z["delta_luna"]) for z in zones])
    print("Escrito en", OUT_WEB)


if __name__ == "__main__":
    main()
