#!/usr/bin/env python3
"""Export frozen v1 rasters and GeoJSON for a Unity WebGL viewer. Does not modify productos/."""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np
from PIL import Image
import rasterio

ROOT = Path("/workspace/analogs")
PROD = ROOT / "web/public/productos"
ELEV = ROOT / "data/processed/earth/ecuador_elevation_1km.tif"
OUT = ROOT / "web/public/unity"
STAMP = ROOT / "docs/version_congelada_v1.md"
CAT = PROD / "catalogo.json"
CSV = PROD / "tabla_validacion.csv"

# Official frozen SHA-256 (must remain the hashes in version_congelada_v1.md)
FROZEN_SHA256 = {
    "catalogo.json": "369dd38593f76d46266d1cd86077ce4729fb7b1e3811adc66b74fe0be51c87dd",
    "tabla_validacion.csv": "7ff7856cc3581e31b1a55f32b5a5cc48191a5160bf677dd3437a0968e4a95218",
    "delta_marte.png": "0152dfb637616e246d3c946f702ed251266c1a0db2c7d8bc6bfaf5fec30b0d4b",
    "delta_marte.tif": "dba0f23685d35f5e6399be7ebfbc816e552e0e969a88a8e35821b39b2b1ed406",
    "delta_luna.png": "5eb786ef217863e0f022127c5d3e1ee1c07099ccc1646b26d750cda00e684dc6",
    "delta_luna.tif": "daf00ed5e74e6308f2a9f46a4077075e335726c278e901c1a18bef24a67372c7",
    "clases.png": "c9fedb0c7931fda40311ccf1556266cb1165ceea9de12abfb0c519363e6997af",
    "clases.tif": "a92f6781cc589d0de787e5ac74eae0042e56c6d89a16bd3abfa23968b0d9b886",
}

# Dashboard colormap (sRGB) for optional preview; data files are encoded grayscale/palette.
CMAP_DELTA_MARS = [(13, 9, 8), (196, 92, 62), (244, 214, 170)]
CMAP_DELTA_LUNA = [(12, 12, 14), (180, 184, 196), (237, 236, 232)]
CLASS_COLORS = {
    0: (106, 110, 118, 255),  # ninguno
    1: (196, 92, 62, 255),    # marte
    2: (221, 214, 200, 255),  # luna
    3: (212, 160, 84, 255),   # ambos
    255: (0, 0, 0, 0),        # nodata
}
CLASS_NAMES = {0: "ninguno", 1: "marte", 2: "luna", 3: "ambos", 255: "nodata"}

GYQ = timezone(timedelta(hours=-5))


def load_grid(path: Path):
    with rasterio.open(path) as ds:
        arr = ds.read(1)
        b = ds.bounds
        meta = {
            "crs": "EPSG:4326",
            "width": int(ds.width),
            "height": int(ds.height),
            "bounds": {
                "oeste": float(b.left),
                "sur": float(b.bottom),
                "este": float(b.right),
                "norte": float(b.top),
            },
            "cell_deg": float(abs(ds.res[0])),
            "transform_affine": [float(x) for x in ds.transform[:6]],
            "pixel_origin": "upper_left",
            "axis_order": "row0_is_north",
        }
        nodata = ds.nodata
    return arr, nodata, meta


def ramp(stops, t):
    t = float(np.clip(t, 0, 1))
    if t <= 0:
        return stops[0]
    if t >= 1:
        return stops[-1]
    x = t * (len(stops) - 1)
    i = int(math.floor(x))
    f = x - i
    a, b = stops[i], stops[min(i + 1, len(stops) - 1)]
    return tuple(int(round(a[k] + (b[k] - a[k]) * f)) for k in range(3))


def write_delta_png(src: Path, dest: Path, preview: Path, cmap):
    arr, nodata, meta = load_grid(src)
    valid = np.isfinite(arr) & (arr != nodata)
    h, w = arr.shape
    # RGBA: R=G=B = round(δ*255), A=255 valid / 0 nodata
    enc = np.zeros((h, w), dtype=np.uint8)
    enc[valid] = np.clip(np.rint(arr[valid] * 255.0), 0, 255).astype(np.uint8)
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[..., 0] = enc
    rgba[..., 1] = enc
    rgba[..., 2] = enc
    rgba[..., 3] = np.where(valid, 255, 0).astype(np.uint8)
    Image.fromarray(rgba, mode="RGBA").save(dest, format="PNG", optimize=True)

    prev = np.zeros((h, w, 4), dtype=np.uint8)
    lut = np.array([ramp(cmap, i / 255.0) for i in range(256)], dtype=np.uint8)
    prev[..., 0] = lut[enc, 0]
    prev[..., 1] = lut[enc, 1]
    prev[..., 2] = lut[enc, 2]
    prev[..., 3] = rgba[..., 3]
    # don't iterate pixels — already vectorized; remove the dummy loop above in mind
    Image.fromarray(prev, mode="RGBA").save(preview, format="PNG", optimize=True)

    meta_out = {
        **meta,
        "archivo": dest.name,
        "vista_previa": preview.name,
        "codificacion": {
            "tipo": "PNG RGBA 8 bits",
            "canal": "R=G=B",
            "valor": "byte = round(delta * 255); delta en [0, 1]",
            "nodata": "alpha = 0 (el valor RGB no es significativo)",
            "valido": "alpha = 255",
        },
        "rango_fisico": {"min": 0.0, "max": 1.0, "unidad": "delta (adimensional)"},
        "nodata_fuente": nodata,
        "n_celdas_validas": int(valid.sum()),
        "colormap_vista_previa": "rampa RGB documentada en README_UNITY.md",
        "version": "ANALOG/delta v1 congelada 2026-11-14",
        "sha256_producto_fuente_tif": None,
    }
    return meta_out, valid


def write_class_png(src: Path, dest: Path):
    arr, nodata, meta = load_grid(src)
    h, w = arr.shape
    # source: -1 nodata, 0 ninguno, 1 marte, 2 luna, 3 ambos
    out = np.full((h, w), 255, dtype=np.uint8)
    valid = np.isfinite(arr) & (arr != nodata)
    out[valid] = np.clip(arr[valid], 0, 3).astype(np.uint8)
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    for code, color in CLASS_COLORS.items():
        m = out == code
        rgba[m] = color
    Image.fromarray(rgba, mode="RGBA").save(dest, format="PNG", optimize=True)
    meta_out = {
        **meta,
        "archivo": dest.name,
        "codificacion": {
            "tipo": "PNG 8 bits (índice / RGBA)",
            "valores": {
                "0": "ninguno",
                "1": "marte",
                "2": "luna",
                "3": "ambos",
                "255": "nodata (mar o celda no válida)",
            },
            "colormap": {
                "0": {"nombre": "ninguno", "rgba": [106, 110, 118, 255]},
                "1": {"nombre": "marte", "rgba": [196, 92, 62, 255]},
                "2": {"nombre": "luna", "rgba": [221, 214, 200, 255]},
                "3": {"nombre": "ambos", "rgba": [212, 160, 84, 255]},
                "255": {"nombre": "nodata", "rgba": [0, 0, 0, 0]},
            },
        },
        "aviso": (
            "Mapa de clases secundario. El umbral de Marte de la v1 tiene especificidad 0; "
            "no usar esta capa como inventario de análogos ni para calcular porcentajes de cobertura."
        ),
        "n_celdas_por_clase": {CLASS_NAMES[k]: int((out == k).sum()) for k in (0, 1, 2, 3, 255)},
        "version": "ANALOG/delta v1 congelada 2026-11-14",
    }
    return meta_out


def hillshade(z, dx, dy, azimuth_deg=315.0, altitude_deg=45.0, nodata_mask=None):
    z = z.astype(np.float64)
    # Horn 3x3
    pad = np.pad(z, 1, mode="edge")
    dzdx = ((pad[0:-2, 2:] + 2 * pad[1:-1, 2:] + pad[2:, 2:]) - (pad[0:-2, 0:-2] + 2 * pad[1:-1, 0:-2] + pad[2:, 0:-2])) / (8.0 * dx)
    dzdy = ((pad[2:, 0:-2] + 2 * pad[2:, 1:-1] + pad[2:, 2:]) - (pad[0:-2, 0:-2] + 2 * pad[0:-2, 1:-1] + pad[0:-2, 2:])) / (8.0 * dy)
    slope = np.arctan(np.sqrt(dzdx * dzdx + dzdy * dzdy))
    aspect = np.arctan2(dzdy, -dzdx)
    # aspect is a math angle (CCW from east, rows = south); azimuth is geographic
    # (clockwise from north). Convert so 315° really means light from the NW.
    az = np.radians((450.0 - azimuth_deg) % 360.0)
    alt = np.radians(altitude_deg)
    hs = np.sin(alt) * np.cos(slope) + np.cos(alt) * np.sin(slope) * np.cos(az - aspect)
    hs = np.clip(hs, 0, 1)
    out = np.clip(np.rint(hs * 255.0), 0, 255).astype(np.uint8)
    return out


def write_hillshade(src: Path, dest: Path):
    arr, nodata, meta = load_grid(src)
    valid = np.isfinite(arr) & (arr != nodata)
    # cell size in meters at mid-latitude of the grid (approx); hillshade is visual only
    mid_lat = (meta["bounds"]["norte"] + meta["bounds"]["sur"]) / 2.0
    m_per_deg = 111319.49 * math.cos(math.radians(mid_lat))
    dx = meta["cell_deg"] * m_per_deg
    dy = meta["cell_deg"] * 111319.49
    work = arr.copy()
    fill = float(np.median(arr[valid])) if valid.any() else 0.0
    work[~valid] = fill
    hs = hillshade(work, dx, dy)
    h, w = hs.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[..., 0] = hs
    rgba[..., 1] = hs
    rgba[..., 2] = hs
    rgba[..., 3] = np.where(valid, 255, 0).astype(np.uint8)
    Image.fromarray(rgba, mode="RGBA").save(dest, format="PNG", optimize=True)
    meta_out = {
        **meta,
        "archivo": dest.name,
        "codificacion": {
            "tipo": "PNG RGBA 8 bits",
            "canal": "R=G=B sombreado",
            "valor": "byte 0–255 (0 = sombra, 255 = luz)",
            "nodata": "alpha = 0",
            "algoritmo": "Horn 3×3, acimut 315°, elevación solar 45°. Solo visual.",
        },
        "fuente": "Copernicus DEM GLO-90 remuestreado a ~1 km (ecuador_elevation_1km.tif), no altera los productos congelados de δ.",
        "version": "ANALOG/delta v1 congelada 2026-11-14",
    }
    return meta_out


def write_json(path: Path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sites_geojson(cat):
    feats = []
    for s in cat["sitios_validacion"]:
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [s["lon"], s["lat"]]},
            "properties": {
                "id": s.get("id"),
                "nombre": s["nombre"],
                "buffer_km": s["buffer_km"],
                "etiqueta": s.get("etiqueta"),
                "clase_conocida": s.get("clase_conocida"),
                "clase_predicha": s.get("clase_predicha"),
                "delta_marte": s.get("delta_marte"),
                "delta_luna": s.get("delta_luna"),
                "acierto": s.get("acierto"),
                "entra_al_auc": s.get("entra_al_auc"),
                "excluido_auc": s.get("excluido_auc"),
                "banda_latitud": s.get("banda_latitud"),
                "cita": s.get("cita") or s.get("fuente"),
            },
        })
    return {
        "type": "FeatureCollection",
        "name": "sitios_validacion_v1_congelada",
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": feats,
    }


def zones_geojson(cat):
    feats = []
    for z in cat["zonas_prioritarias"]:
        feats.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [z["lon"], z["lat"]]},
            "properties": {
                "id": z.get("id"),
                "nombre": z["nombre"],
                "clase": z.get("clase"),
                "delta_marte": z.get("delta_marte"),
                "delta_luna": z.get("delta_luna"),
                "elevacion_m": z.get("elevacion_m"),
                "pendiente_deg": z.get("pendiente_deg"),
                "rugosidad_tri": z.get("rugosidad_tri"),
                "banda_latitud": z.get("banda_latitud"),
            },
        })
    return {
        "type": "FeatureCollection",
        "name": "zonas_prioritarias_ecuador_v1_congelada",
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": feats,
    }


def sha256(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # Verify frozen hashes have not drifted before exporting
    for name, expected in FROZEN_SHA256.items():
        got = sha256(PROD / name)
        if got != expected:
            raise SystemExit(f"HASH MISMATCH {name}: no exportar")

    cat = json.loads(CAT.read_text(encoding="utf-8"))

    m_meta, _ = write_delta_png(PROD / "delta_marte.tif", OUT / "delta_marte.png", OUT / "delta_marte_preview.png", CMAP_DELTA_MARS)
    m_meta["sha256_producto_fuente_tif"] = FROZEN_SHA256["delta_marte.tif"]
    write_json(OUT / "delta_marte.json", m_meta)

    l_meta, _ = write_delta_png(PROD / "delta_luna.tif", OUT / "delta_luna.png", OUT / "delta_luna_preview.png", CMAP_DELTA_LUNA)
    l_meta["sha256_producto_fuente_tif"] = FROZEN_SHA256["delta_luna.tif"]
    write_json(OUT / "delta_luna.json", l_meta)

    c_meta = write_class_png(PROD / "clases.tif", OUT / "clases.png")
    c_meta["sha256_producto_fuente_tif"] = FROZEN_SHA256["clases.tif"]
    write_json(OUT / "clases.json", c_meta)

    h_meta = write_hillshade(ELEV, OUT / "hillshade.png")
    write_json(OUT / "hillshade.json", h_meta)

    write_json(OUT / "sitios_validacion.geojson", sites_geojson(cat))
    write_json(OUT / "zonas_prioritarias.geojson", zones_geojson(cat))

    files = []
    for p in sorted(OUT.iterdir()):
        if p.name in {"manifest.json", "README_UNITY.md"}:
            continue
        if p.is_file():
            files.append({
                "archivo": p.name,
                "bytes": p.stat().st_size,
                "sha256": sha256(p),
            })

    manifest = {
        "nombre": "ANALOG/delta v1 congelada — exportación Unity WebGL",
        "version": "ANALOG/delta v1 real 2026-11-14",
        "congelado_en": cat.get("congelado_en"),
        "acta": "docs/version_congelada_v1.md",
        "huella_catalogo_congelado_sha256": FROZEN_SHA256["catalogo.json"],
        "huellas_productos_congelados_sha256": FROZEN_SHA256,
        "crs": "EPSG:4326",
        "extension": cat["grilla"]["extension"],
        "grilla": {"ancho": 1890, "alto": 756, "cell_deg": 0.009},
        "ruta_publica": "/unity/",
        "archivos": files,
        "nota": (
            "Estos archivos son una exportación de lectura de los productos v1 ya congelados. "
            "No recalculan el índice. El mapa de clases es secundario (especificidad de Marte = 0)."
        ),
    }
    write_json(OUT / "manifest.json", manifest)
    print("exported", {p.name: p.stat().st_size for p in sorted(OUT.iterdir())})


if __name__ == "__main__":
    main()
