#!/usr/bin/env python3
"""
Prepara rásteres de la v1.1 (sitios objetivo) SIN correr validación ni puntuar Ecuador.

- Marte: recorta las ventanas en MOLA MEGDR 128 ppd y calcula derivadas.
- Luna: agrega LDEM_80S_20M a 100 m (5×5) en estereográfico polar, recorta
  con los polígonos oficiales de USGS y calcula derivadas.
- Tierra: reconstruye pendiente, TRI y relieve relativo a 463 m (Marte) y
  100 m (Luna) para los 16 sitios del AUC y para Ecuador, a partir de GLO-90.

No calcula firmas, distancias, delta, umbrales ni mapas de clases.
"""
from __future__ import annotations

import gc
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.features import geometry_mask
from rasterio.transform import Affine, from_origin, array_bounds
from rasterio.windows import Window, transform as window_transform, from_bounds as window_from_bounds
from rasterio.warp import Resampling, reproject
from pyproj import CRS as PCRS, Transformer
from shapely.geometry import mapping, shape
from shapely import transform as shp_transform
from scipy.ndimage import median_filter, uniform_filter

sys.path.insert(0, "/workspace/analogs/pipeline_real")
from terrain import NODATA, meters_per_degree, reproject_array, slope_and_tri  # noqa: E402
from add_relative_relief import relative_relief_array, window_cells  # noqa: E402
from process import write_tif  # noqa: E402

ROOT = Path("/workspace/analogs")
RAW_MOLA = ROOT / "data/raw/mars/mola_megdr128"
RAW_LDEM = ROOT / "data/raw/moon/lola_ldem80s"
RAW_GLO = ROOT / "data/raw/earth/copernicus_glo90"
USGS_GJ = ROOT / "data/raw/usgs_luna/A3_9regions-lonlat-simplified.geojson"
OUT = ROOT / "data/processed/v11"
CFG_PATH = ROOT / "config/v1_1_sitios_objetivo.json"

MARS_R = 3_396_000.0
MOON_R = 1_737_400.0
EARTH_R = 6_378_137.0
MARS_M = 463.0  # ~ MEGDR 128 ppd (rótulo: 0.463 km/píxel)
MOON_M = 100.0  # preespecificado: LDEM 20 m agregado 5×5
RELIEF_KM = 15.0
PAD_KM = 20.0  # holgura para ventana de relieve 15 km y TRI 3×3
LDEM_DN_NODATA = -32768
LDEM_SCALE = 0.5
AGG = 5  # 20 m → 100 m

# Equivalente en grados (ecuador) para las grillas geográficas de Ecuador.
DEG_MARS_EARTH = MARS_M / meters_per_degree(EARTH_R)
DEG_MOON_EARTH = MOON_M / meters_per_degree(EARTH_R)

MOON_NAME_TO_ID = {
    "Peak Near Cabeus B": "peak_near_cabeus_b",
    "Haworth": "haworth",
    "Malapert Massif": "malapert_massif",
    "Mons Mouton Plateau": "mons_mouton_plateau",
    "Mons Mouton": "mons_mouton",
    "Nobile Rim 1": "nobile_rim_1",
    "Nobile Rim 2": "nobile_rim_2",
    "de Gerlache Rim 2": "de_gerlache_rim_2",
    "Slater Plain": "slater_plain",
}

CRS_MOON_LL = PCRS.from_proj4("+proj=longlat +R=1737400 +no_defs +type=crs")
CRS_MOON_PS = PCRS.from_proj4(
    "+proj=stere +lat_0=-90 +lon_0=0 +k=1 +R=1737400 +units=m +no_defs +type=crs"
)
CRS_MOON_PS_RIO = CRS.from_wkt(CRS_MOON_PS.to_wkt())
TO_PS = Transformer.from_crs(CRS_MOON_LL, CRS_MOON_PS, always_xy=True)
TO_LL = Transformer.from_crs(CRS_MOON_PS, CRS_MOON_LL, always_xy=True)

# LDEM_80S_20M: 30400², offset 15199.5, 20 m/píxel.
LDEM_N20 = 30400
LDEM_OFF20 = 15199.5
LDEM_M20 = 20.0
AFFINE_20 = Affine(LDEM_M20, 0.0, -LDEM_OFF20 * LDEM_M20, 0.0, -LDEM_M20, LDEM_OFF20 * LDEM_M20)
AFFINE_100 = Affine(MOON_M, 0.0, -LDEM_OFF20 * LDEM_M20, 0.0, -MOON_M, LDEM_OFF20 * LDEM_M20)

MOLA_TILES = {
    "megt44n000hb": dict(west=0.0, south=0.0, east=90.0, north=44.0),
    "megt00n090hb": dict(west=90.0, south=-44.0, east=180.0, north=0.0),
    "megt44n180hb": dict(west=180.0, south=0.0, east=270.0, north=44.0),
}
MOLA_PPD = 128.0
MOLA_SHAPE = (5632, 11520)

ECUADOR = dict(west=-92.007, south=-5.103, east=-74.997, north=1.701)


def odd_cells(cell_m: float, window_km: float = RELIEF_KM) -> int:
    return window_cells(cell_m, window_km)


def write_cog(path: Path, arr, transform, crs, tags=None, overviews=False):
    """Escritura comprimida; overviews opcionales (los recortes chicos no los necesitan)."""
    if overviews:
        return write_tif(path, arr, transform, crs, NODATA, tags)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = np.asarray(arr, dtype=np.float32)
    profile = dict(
        driver="GTiff", width=data.shape[1], height=data.shape[0], count=1,
        dtype="float32", crs=crs, transform=transform, nodata=NODATA,
        tiled=True, blockxsize=256, blockysize=256, compress="deflate",
        predictor=3, zlevel=6, BIGTIFF="IF_SAFER",
    )
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(data, 1)
        if tags:
            dst.update_tags(**tags)
    return path


def slope_tri_meters(z: np.ndarray, dx: float, dy: float, nodata: float = NODATA):
    """Horn + TRI Wilson sobre una grilla ya en metros (estereográfica o AEQD)."""
    z = np.asarray(z, dtype=np.float64)
    nr, nc = z.shape
    valid = np.isfinite(z) & (z != nodata)
    zpad = np.full((nr + 2, nc + 2), nodata, dtype=np.float64)
    zpad[1:-1, 1:-1] = z
    vpad = np.zeros((nr + 2, nc + 2), dtype=bool)
    vpad[1:-1, 1:-1] = valid
    a, b, c = zpad[0:-2, 0:-2], zpad[0:-2, 1:-1], zpad[0:-2, 2:]
    d, e, f = zpad[1:-1, 0:-2], zpad[1:-1, 1:-1], zpad[1:-1, 2:]
    g, h, i = zpad[2:, 0:-2], zpad[2:, 1:-1], zpad[2:, 2:]
    va, vb, vc = vpad[0:-2, 0:-2], vpad[0:-2, 1:-1], vpad[0:-2, 2:]
    vd, ve, vf = vpad[1:-1, 0:-2], vpad[1:-1, 1:-1], vpad[1:-1, 2:]
    vg, vh, vi = vpad[2:, 0:-2], vpad[2:, 1:-1], vpad[2:, 2:]
    all8 = va & vb & vc & vd & ve & vf & vg & vh & vi
    dzdx = ((c + 2.0 * f + i) - (a + 2.0 * d + g)) / (8.0 * dx)
    dzdy = ((g + 2.0 * h + i) - (a + 2.0 * b + c)) / (8.0 * dy)
    slope = np.degrees(np.arctan(np.sqrt(dzdx * dzdx + dzdy * dzdy)))
    diffs = np.stack([np.abs(a-e), np.abs(b-e), np.abs(c-e), np.abs(d-e),
                      np.abs(f-e), np.abs(g-e), np.abs(h-e), np.abs(i-e)], 0)
    tri = diffs.mean(axis=0)
    slope = np.where(all8, slope, nodata).astype(np.float32)
    tri = np.where(all8, tri, nodata).astype(np.float32)
    return slope, tri


def relative_relief_fast(z, size, nodata=NODATA, min_frac=0.5):
    """z − mediana focal, ignorando no-datos, con la misma regla min_frac=0.5 de la v1.

    Equivale a nanmedian si se rellenan los huecos con un centinela mayor que
    cualquier z: cuando hay ≥ 50 % de celdas válidas en la ventana (tamaño impar,
    N impar), la mediana del bloque coincide con la de los valores válidos.
    Evita el sliding_window_view, que no cabe en memoria a 100 m sobre Ecuador.
    """
    assert size % 2 == 1
    z32 = np.asarray(z, dtype=np.float32)
    valid = np.isfinite(z32) & (z32 != nodata)
    out = np.full(z32.shape, nodata, dtype=np.float32)
    if not valid.any():
        return out
    sentinel = float(np.max(np.abs(z32[valid]))) + 1.0e6
    work = np.where(valid, z32, sentinel)
    med = median_filter(work, size=size, mode="constant", cval=sentinel)
    del work
    # uniform_filter es separable; el recuento equivale al pad-con-nan de la v1.
    cnt = np.rint(
        uniform_filter(valid.astype(np.float32), size=size, mode="constant", cval=0.0)
        * (size * size)
    )
    min_n = max(1, int(np.ceil(min_frac * size * size)))
    ok = valid & (cnt >= min_n)
    out[ok] = (z32[ok] - med[ok]).astype(np.float32)
    return out


def relative_relief_auto(z, size, nodata=NODATA, wrap_x=False):
    """Usa el nanmedian de la v1 si cabe en memoria; si no, el filtro mediano equivalente
    en ventanas 100 % válidas (en costas, la mediana de N impar, no el promedio de dos
    valores centrales que usa np.nanmedian cuando el recuento es par)."""
    z = np.asarray(z)
    est = 24 * z.shape[1] * size * size * 8
    if wrap_x or est < 1_200_000_000:
        return relative_relief_array(z, size, nodata, wrap_x=wrap_x)
    print(
        f"    relieve relativo por filtro mediano ({z.shape[0]}×{z.shape[1]}, ventana {size}); "
        "idéntico al nanmedian de la v1 en ventanas completas",
        flush=True,
    )
    return relative_relief_fast(z, size, nodata)


def slope_and_tri_strips(dem, transform, radius_m, strip=300):
    """Horn + TRI por tiras para no apilar 8 copias float64 del raster completo."""
    h, w = dem.shape
    sl = np.full((h, w), NODATA, dtype=np.float32)
    tri = np.full((h, w), NODATA, dtype=np.float32)
    for r0 in range(0, h, strip):
        r1 = min(h, r0 + strip)
        y0 = max(0, r0 - 1)
        y1 = min(h, r1 + 1)
        sub_t = transform * Affine.translation(0, y0)
        s, t = slope_and_tri(dem[y0:y1], sub_t, radius_m, NODATA, wrap_x=False)
        a = r0 - y0
        sl[r0:r1] = s[a:a + (r1 - r0)]
        tri[r0:r1] = t[a:a + (r1 - r0)]
        del s, t
    return sl, tri


def derivatives_geo(dem, transform, radius_m):
    h, w = dem.shape
    if h * w > 3_000_000:
        sl, tri = slope_and_tri_strips(dem, transform, radius_m)
    else:
        sl, tri = slope_and_tri(dem, transform, radius_m, NODATA, wrap_x=False)
    cell_m = meters_per_degree(radius_m) * abs(transform.a)
    size = odd_cells(cell_m)
    rel = relative_relief_auto(dem, size, NODATA)
    return sl, tri, rel, size


def derivatives_m(dem, cell_m):
    sl, tri = slope_tri_meters(dem, cell_m, cell_m, NODATA)
    size = odd_cells(cell_m)
    rel = relative_relief_auto(dem, size, NODATA)
    return sl, tri, rel, size


def count_valid(dem, sl, tri, rel, mask=None):
    m = (dem != NODATA) & np.isfinite(dem)
    m &= (sl != NODATA) & np.isfinite(sl)
    m &= (tri != NODATA) & np.isfinite(tri)
    m &= (rel != NODATA) & np.isfinite(rel)
    if mask is not None:
        m &= mask
    return int(m.sum())


def haversine_mask(lat0, lon0, lat, lon, radius_km, body_r_km):
    p1, l1, p2, l2 = map(np.radians, (lat0, lon0, lat, lon))
    a = np.sin((p2-p1)/2)**2 + np.cos(p1)*np.cos(p2)*np.sin((l2-l1)/2)**2
    d = 2 * body_r_km * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    return d <= radius_km


# ---------------------------------------------------------------------------
# Luna: geometría oficial + LDEM agregado
# ---------------------------------------------------------------------------
def official_polygons():
    geo = json.loads(USGS_GJ.read_text(encoding="utf-8"))
    rows = []
    for feat in geo["features"]:
        props = feat["properties"]
        name = props["Region"]
        if name not in MOON_NAME_TO_ID:
            raise SystemExit(f"Nombre inesperado en el shapefile: {name!r}")
        geom = shape(feat["geometry"])
        def _to_ps(xy):
            # shapely.transform passes (n, 2)
            lon, lat = xy[:, 0], xy[:, 1]
            x, y = TO_PS.transform(lon, lat)
            out = np.empty_like(xy)
            out[:, 0], out[:, 1] = x, y
            return out
        geom_ps = shp_transform(geom, _to_ps)
        cx, cy = geom_ps.centroid.x, geom_ps.centroid.y
        lon, lat = TO_LL.transform(cx, cy)
        rows.append({
            "id": MOON_NAME_TO_ID[name],
            "nombre_oficial": name,
            "region_code": props.get("RegionCode"),
            "area_km2_atributo_usgs": float(props["Area_km2"]),
            "area_km2_calculada_estereografica": float(geom_ps.area / 1e6),
            "centroide_lat": float(lat),
            "centroide_lon": float(lon),
            "centroide_x_m": float(cx),
            "centroide_y_m": float(cy),
            "n_vertices": int(len(feat["geometry"]["coordinates"][0])),
            "bbox_lonlat": [float(v) for v in geom.bounds],
            "bbox_ps_m": [float(v) for v in geom_ps.bounds],
            "geometry_lonlat": feat["geometry"],
            "geometry_ps": mapping(geom_ps),
        })
    got = {r["nombre_oficial"] for r in rows}
    expected = set(MOON_NAME_TO_ID)
    if got != expected:
        raise SystemExit(f"Las 9 regiones no coinciden: falta {expected-got}, sobra {got-expected}")
    return rows


def aggregate_ldem_100m(out_path: Path) -> Path:
    img = RAW_LDEM / "ldem_80s_20m.img"
    if img.stat().st_size != 1_848_320_000:
        raise SystemExit(f"LDEM inesperado: {img.stat().st_size} bytes")
    if out_path.exists() and out_path.stat().st_size > 10_000_000:
        print(f"  ya existe {out_path}")
        return out_path
    src = np.memmap(img, dtype="<i2", mode="r", shape=(LDEM_N20, LDEM_N20))
    nout = LDEM_N20 // AGG
    out = np.full((nout, nout), NODATA, dtype=np.float32)
    # Agregar por bloques de filas (5 filas nativas = 1 fila de salida).
    chunk = 200  # filas de salida
    for r0 in range(0, nout, chunk):
        r1 = min(nout, r0 + chunk)
        block = np.asarray(src[r0*AGG:r1*AGG, :], dtype=np.int16)
        h = block.shape[0] // AGG
        w = nout
        view = block[:h*AGG, :w*AGG].reshape(h, AGG, w, AGG)
        dn = view.astype(np.float32)
        valid = view != LDEM_DN_NODATA
        dn = np.where(valid, dn, np.nan)
        mean_dn = np.nanmean(dn, axis=(1, 3))
        n = valid.sum(axis=(1, 3))
        elev = mean_dn * LDEM_SCALE
        out[r0:r0+h] = np.where(n > 0, elev, NODATA).astype(np.float32)
        print(f"  agregando filas {r0}-{r1}/{nout}", flush=True)
    del src
    tags = {
        "BODY": "moon",
        "SOURCE": "LDEM_80S_20M (ldem_80s_20m.img), HEIGHT=DN*0.5, agregado 5x5 a 100 m",
        "PROJECTION": "polar stereographic, lat_0=-90, lon_0=0, R=1737.4 km",
        "CELL_M": str(MOON_M),
        "VERTICAL_DATUM": "esfera 1737.4 km (ME/PA DE421)",
    }
    write_cog(out_path, out, AFFINE_100, CRS_MOON_PS_RIO, tags, overviews=True)
    print(f"  escrito {out_path} ({out_path.stat().st_size/1e6:.1f} MB)")
    return out_path


def prepare_moon(polys, ldem_path: Path):
    out_root = OUT / "moon"
    out_root.mkdir(parents=True, exist_ok=True)
    with rasterio.open(ldem_path) as ds:
        full = None  # read windows only
        transform = ds.transform
        results = []
        for p in polys:
            dest = OUT / "moon" / p["id"]
            needed = [
                dest / "elevation_100m.tif", dest / "slope_100m.tif",
                dest / "roughness_100m.tif", dest / "relative_relief_100m.tif",
                dest / "polygon_mask_100m.tif",
            ]
            if all(f.exists() and f.stat().st_size > 1000 for f in needed):
                with rasterio.open(dest / "elevation_100m.tif") as e, \
                     rasterio.open(dest / "slope_100m.tif") as s, \
                     rasterio.open(dest / "roughness_100m.tif") as r, \
                     rasterio.open(dest / "relative_relief_100m.tif") as rels, \
                     rasterio.open(dest / "polygon_mask_100m.tif") as mds:
                    dem, sl, tri, rel, mask = e.read(1), s.read(1), r.read(1), rels.read(1), mds.read(1) == 1.0
                    n = count_valid(dem, sl, tri, rel, mask)
                    n_elev = int(((dem != NODATA) & np.isfinite(dem) & mask).sum())
                    shape = [int(dem.shape[0]), int(dem.shape[1])]
                    size = int(e.tags().get("RELIEF_WINDOW_CELLS") or odd_cells(MOON_M))
                rec = {
                    **{k: p[k] for k in (
                        "id", "nombre_oficial", "region_code",
                        "area_km2_atributo_usgs", "area_km2_calculada_estereografica",
                        "centroide_lat", "centroide_lon",
                    )},
                    "n_celdas_elevacion_en_poligono": n_elev,
                    "n_celdas_validas_derivadas": n,
                    "cumple_minimo_100": n >= 100,
                    "relief_window_cells": size,
                    "cell_m": MOON_M,
                    "shape_recorte": shape,
                    "recontado_de_archivos": True,
                }
                results.append(rec)
                print(f"  {p['nombre_oficial']}: n_elev={n_elev} n_validas={n} area={p['area_km2_atributo_usgs']} km2 (ya existía)")
                continue
            minx, miny, maxx, maxy = p["bbox_ps_m"]
            pad = PAD_KM * 1000.0
            window = rasterio.windows.from_bounds(
                minx - pad, miny - pad, maxx + pad, maxy + pad, transform=transform
            ).round_offsets().round_lengths()
            window = window.intersection(rasterio.windows.Window(0, 0, ds.width, ds.height))
            dem = ds.read(1, window=window).astype(np.float32)
            wt = ds.window_transform(window)
            # geometry_mask(..., invert=True) is True inside the polygon.
            # Do not invert again: that would count the pad instead of the official region.
            mask = geometry_mask(
                [p["geometry_ps"]], out_shape=dem.shape, transform=wt, invert=True, all_touched=False
            )
            sl, tri, rel, size = derivatives_m(dem, MOON_M)
            n = count_valid(dem, sl, tri, rel, mask)
            n_elev = int(((dem != NODATA) & np.isfinite(dem) & mask).sum())
            dest = out_root / p["id"]
            tags = {
                "SITE": p["id"], "NAME": p["nombre_oficial"], "BODY": "moon",
                "WINDOW": "poligono_oficial_usgs", "CELL_M": str(MOON_M),
                "RELIEF_WINDOW_CELLS": str(size), "RELIEF_WINDOW_KM": str(RELIEF_KM),
            }
            write_cog(dest / "elevation_100m.tif", dem, wt, CRS_MOON_PS_RIO, tags)
            write_cog(dest / "slope_100m.tif", sl, wt, CRS_MOON_PS_RIO, tags)
            write_cog(dest / "roughness_100m.tif", tri, wt, CRS_MOON_PS_RIO, tags)
            write_cog(dest / "relative_relief_100m.tif", rel, wt, CRS_MOON_PS_RIO, tags)
            # máscara del polígono (1 dentro, nodata fuera)
            m_arr = np.where(mask, 1.0, NODATA).astype(np.float32)
            write_cog(dest / "polygon_mask_100m.tif", m_arr, wt, CRS_MOON_PS_RIO, tags)
            rec = {
                **{k: p[k] for k in (
                    "id", "nombre_oficial", "region_code",
                    "area_km2_atributo_usgs", "area_km2_calculada_estereografica",
                    "centroide_lat", "centroide_lon",
                )},
                "n_celdas_elevacion_en_poligono": n_elev,
                "n_celdas_validas_derivadas": n,
                "cumple_minimo_100": n >= 100,
                "relief_window_cells": size,
                "cell_m": MOON_M,
                "shape_recorte": [int(dem.shape[0]), int(dem.shape[1])],
            }
            results.append(rec)
            print(f"  {p['nombre_oficial']}: n_elev={n_elev} n_validas={n} area={p['area_km2_atributo_usgs']} km2")
    return results


# ---------------------------------------------------------------------------
# Marte: recortes MEGDR 128
# ---------------------------------------------------------------------------
def load_mola_tile(name: str):
    meta = MOLA_TILES[name]
    path = RAW_MOLA / f"{name}.img"
    arr = np.memmap(path, dtype=">i2", mode="r", shape=MOLA_SHAPE)
    transform = from_origin(meta["west"], meta["north"], 1.0 / MOLA_PPD, 1.0 / MOLA_PPD)
    return arr, transform, meta


def crop_mola(name, lat0, lon0, radio_km):
    """lon0 en grados este (0–360 o −180–180). Se trabaja en la longitud nativa de la tesela."""
    arr, transform, meta = load_mola_tile(name)
    lon = lon0 if lon0 >= meta["west"] - 1e-6 else lon0 + 360.0
    pad_deg = ((radio_km + PAD_KM) / (MARS_R / 1000.0)) * (180.0 / math.pi)
    coslat = max(math.cos(math.radians(lat0)), 0.15)
    lon_pad = pad_deg / coslat
    west, east = lon - lon_pad, lon + lon_pad
    south, north = lat0 - pad_deg, lat0 + pad_deg
    window = rasterio.windows.from_bounds(west, south, east, north, transform=transform)
    window = window.round_offsets().round_lengths()
    window = window.intersection(rasterio.windows.Window(0, 0, arr.shape[1], arr.shape[0]))
    crop = np.asarray(arr[window.row_off:window.row_off+window.height,
                          window.col_off:window.col_off+window.width], dtype=np.float32)
    crop = np.where((crop < -30000) | (crop > 30000), NODATA, crop)
    wt = rasterio.windows.transform(window, transform)
    # coordenadas de centros
    rows, cols = np.indices(crop.shape)
    lons = wt.c + (cols + 0.5) * wt.a
    lats = wt.f + (rows + 0.5) * wt.e
    mask = haversine_mask(lat0, lon, lats, lons, radio_km, MARS_R / 1000.0)
    mask &= (crop != NODATA) & np.isfinite(crop)
    return crop, wt, mask, meta


def prepare_mars(cfg_sites):
    out_root = OUT / "mars"
    results = []
    crs = CRS.from_wkt(
        'GEOGCS["Mars IAU2000 ocentric (MEGDR sphere 3396 km)",'
        'DATUM["Mars_MEGDR_sphere",SPHEROID["Mars_MEGDR",3396000,0]],'
        'PRIMEM["Reference Meridian",0],UNIT["degree",0.0174532925199433]]'
    )
    for s in cfg_sites:
        dest = out_root / s["id"]
        needed = [
            dest / "elevation_463m.tif", dest / "slope_463m.tif",
            dest / "roughness_463m.tif", dest / "relative_relief_463m.tif",
            dest / "window_mask_463m.tif",
        ]
        if all(f.exists() and f.stat().st_size > 1000 for f in needed):
            with rasterio.open(dest / "elevation_463m.tif") as e, \
                 rasterio.open(dest / "slope_463m.tif") as sds, \
                 rasterio.open(dest / "roughness_463m.tif") as r, \
                 rasterio.open(dest / "relative_relief_463m.tif") as rels, \
                 rasterio.open(dest / "window_mask_463m.tif") as mds:
                dem, sl, tri, rel, mask = e.read(1), sds.read(1), r.read(1), rels.read(1), mds.read(1) == 1.0
                n = count_valid(dem, sl, tri, rel, mask)
                n_elev = int(mask.sum())
                shape = [int(dem.shape[0]), int(dem.shape[1])]
                size = int(e.tags().get("RELIEF_WINDOW_CELLS") or odd_cells(MARS_M))
            rec = {
                "id": s["id"], "nombre": s["nombre"], "lat": s["lat"], "lon": s["lon"],
                "radio_km": s["radio_km"], "tesela": s["tesela_mola128"],
                "n_celdas_elevacion_en_ventana": n_elev,
                "n_celdas_validas_derivadas": n,
                "cumple_minimo_100": n >= 100,
                "relief_window_cells": size,
                "cell_m": MARS_M,
                "shape_recorte": shape,
                "recontado_de_archivos": True,
            }
            results.append(rec)
            print(f"  recorte Marte {s['id']} … n_elev={n_elev} n_validas={n} (ya existía)")
            continue
        print(f"  recorte Marte {s['id']} …", flush=True)
        dem, wt, mask, meta = crop_mola(s["tesela_mola128"].replace(".img", ""), s["lat"], s["lon"], s["radio_km"])
        sl, tri, rel, size = derivatives_geo(dem, wt, MARS_R)
        n = count_valid(dem, sl, tri, rel, mask)
        n_elev = int(mask.sum())
        dest = out_root / s["id"]
        tags = {
            "SITE": s["id"], "BODY": "mars", "TESLA": s["tesela_mola128"],
            "CELL_M": str(MARS_M), "RADIUS_KM": str(s["radio_km"]),
            "RELIEF_WINDOW_CELLS": str(size), "RELIEF_WINDOW_KM": str(RELIEF_KM),
        }
        write_cog(dest / "elevation_463m.tif", dem, wt, crs, tags)
        write_cog(dest / "slope_463m.tif", sl, wt, crs, tags)
        write_cog(dest / "roughness_463m.tif", tri, wt, crs, tags)
        write_cog(dest / "relative_relief_463m.tif", rel, wt, crs, tags)
        write_cog(dest / "window_mask_463m.tif", np.where(mask, 1.0, NODATA).astype(np.float32), wt, crs, tags)
        rec = {
            "id": s["id"], "nombre": s["nombre"], "lat": s["lat"], "lon": s["lon"],
            "radio_km": s["radio_km"], "tesela": s["tesela_mola128"],
            "n_celdas_elevacion_en_ventana": n_elev,
            "n_celdas_validas_derivadas": n,
            "cumple_minimo_100": n >= 100,
            "relief_window_cells": size,
            "cell_m": MARS_M,
            "shape_recorte": [int(dem.shape[0]), int(dem.shape[1])],
        }
        results.append(rec)
        print(f"    n_elev={n_elev} n_validas={n}")
    return results


# ---------------------------------------------------------------------------
# Tierra: GLO-90 a 463 m y 100 m
# ---------------------------------------------------------------------------
def glo_tiles_for(west, south, east, north):
    tiles = []
    for p in sorted(RAW_GLO.glob("Copernicus_DSM_COG_30_*.tif")):
        with rasterio.open(p) as ds:
            b = ds.bounds
            if b.right < west or b.left > east or b.top < south or b.bottom > north:
                continue
            tiles.append(p)
    return tiles


def mosaic_glo(west, south, east, north, dst_transform, width, height, dst_crs):
    """Reproyecta cada tesela solo a su ventana de destino (evita un dest de Ecuador entero)."""
    tiles = glo_tiles_for(west, south, east, north)
    if not tiles:
        raise SystemExit(f"Sin teselas GLO-90 para {west,south,east,north}")
    out = np.full((height, width), NODATA, dtype=np.float32)
    full = Window(0, 0, width, height)
    for i, p in enumerate(tiles, 1):
        with rasterio.open(p) as src:
            # intersección de bounds en el CRS de destino (acá 4326 == las teselas)
            b = src.bounds
            try:
                w = window_from_bounds(
                    max(b.left, west), max(b.bottom, south),
                    min(b.right, east), min(b.top, north),
                    transform=dst_transform,
                ).round_offsets().round_lengths()
            except Exception:
                continue
            w = w.intersection(full)
            if w.width <= 0 or w.height <= 0:
                continue
            wt = window_transform(w, dst_transform)
            arr = src.read(1).astype(np.float32)
            arr = np.where((arr == 0.0) | ~np.isfinite(arr), NODATA, arr)
            dest = reproject_array(
                arr, src.transform, src.crs,
                (int(w.height), int(w.width)), wt, dst_crs,
                NODATA, NODATA, Resampling.bilinear,
            )
        m = dest != NODATA
        r0, c0 = int(w.row_off), int(w.col_off)
        sl = out[r0:r0 + int(w.height), c0:c0 + int(w.width)]
        sl[m] = dest[m]
        del dest, arr
        if i % 20 == 0 or i == len(tiles):
            print(f"    teselas GLO {i}/{len(tiles)}", flush=True)
    gc.collect()
    return out, len(tiles)


def prepare_earth_sites(sites):
    results = []
    out_root = OUT / "earth" / "validation"
    for s in sites:
        if not s.get("entra_al_auc"):
            continue
        sid, lat, lon, buf = s["id"], float(s["lat"]), float(s["lon"]), float(s["buffer_km"])
        print(f"  Tierra {sid} …", flush=True)
        rec = {"id": sid, "lat": lat, "lon": lon, "buffer_km": buf, "escalas": {}}
        dest = out_root / sid
        for cell_m, tag in ((MARS_M, "463m"), (MOON_M, "100m")):
            paths = [
                dest / f"elevation_{tag}.tif", dest / f"slope_{tag}.tif",
                dest / f"roughness_{tag}.tif", dest / f"relative_relief_{tag}.tif",
            ]
            if all(f.exists() and f.stat().st_size > 1000 for f in paths):
                with rasterio.open(paths[0]) as e, rasterio.open(paths[1]) as sds, \
                     rasterio.open(paths[2]) as r, rasterio.open(paths[3]) as rels:
                    dem, sl, tri, relv = e.read(1), sds.read(1), r.read(1), rels.read(1)
                    transform = e.transform
                    size = int(e.tags().get("RELIEF_WINDOW_CELLS") or odd_cells(cell_m))
                    ntiles = e.tags().get("N_TILES")
                    nshp = [int(dem.shape[0]), int(dem.shape[1])]
                rows, cols = np.indices(dem.shape)
                xs = transform.c + (cols + 0.5) * transform.a
                ys = transform.f + (rows + 0.5) * transform.e
                mask = (xs**2 + ys**2) <= (buf * 1000.0) ** 2
                nv = count_valid(dem, sl, tri, relv, mask)
                rec["escalas"][tag] = {
                    "n_celdas_validas_en_buffer": nv,
                    "n_teselas_glo90": int(ntiles) if ntiles else None,
                    "relief_window_cells": size,
                    "cell_m": cell_m,
                    "shape": nshp,
                    "recontado_de_archivos": True,
                }
                print(f"    {tag}: n_validas_buffer={nv} (ya existía)")
                continue
            half = (buf + PAD_KM) * 1000.0
            crs = CRS.from_proj4(
                f"+proj=aeqd +lat_0={lat} +lon_0={lon} +R={EARTH_R} +units=m +no_defs +type=crs"
            )
            n = int(math.ceil(2 * half / cell_m)) + 2
            if n % 2 == 0:
                n += 1
            origin = -n * cell_m / 2.0
            transform = Affine(cell_m, 0, origin, 0, -cell_m, -origin)
            # bounds in lon/lat for tile selection (generous)
            pad_deg = ((buf + PAD_KM + 5) / (EARTH_R / 1000.0)) * (180 / math.pi) / max(math.cos(math.radians(lat)), 0.1)
            west, east = lon - pad_deg, lon + pad_deg
            south, north = lat - pad_deg * max(math.cos(math.radians(lat)), 0.1), lat + pad_deg * max(math.cos(math.radians(lat)), 0.1)
            # wrap for tile search
            dem, ntiles = mosaic_glo(west, south, east, north, transform, n, n, crs)
            sl, tri, rel, size = derivatives_m(dem, cell_m)
            # máscara del buffer oficial (círculo en AEQD ≈ haversina a esta escala)
            rows, cols = np.indices(dem.shape)
            xs = transform.c + (cols + 0.5) * transform.a
            ys = transform.f + (rows + 0.5) * transform.e
            mask = (xs**2 + ys**2) <= (buf * 1000.0) ** 2
            nv = count_valid(dem, sl, tri, rel, mask)
            dest = out_root / sid
            tags = {"SITE": sid, "SCALE": tag, "CELL_M": str(cell_m), "RELIEF_WINDOW_CELLS": str(size)}
            write_cog(dest / f"elevation_{tag}.tif", dem, transform, crs, tags)
            write_cog(dest / f"slope_{tag}.tif", sl, transform, crs, tags)
            write_cog(dest / f"roughness_{tag}.tif", tri, transform, crs, tags)
            write_cog(dest / f"relative_relief_{tag}.tif", rel, transform, crs, tags)
            rec["escalas"][tag] = {
                "n_celdas_validas_en_buffer": nv,
                "n_teselas_glo90": ntiles,
                "relief_window_cells": size,
                "cell_m": cell_m,
                "shape": [n, n],
            }
            print(f"    {tag}: n_validas_buffer={nv} teselas={ntiles}")
        results.append(rec)
    return results


def _ecuador_paths(out_root: Path, tag: str):
    return [
        out_root / f"ecuador_elevation_{tag}.tif",
        out_root / f"ecuador_slope_{tag}.tif",
        out_root / f"ecuador_roughness_{tag}.tif",
        out_root / f"ecuador_relative_relief_{tag}.tif",
    ]


def recount_ecuador_tag(out_root: Path, tag: str, width, height, deg, cell_m):
    paths = _ecuador_paths(out_root, tag)
    arrays = []
    for pth in paths:
        with rasterio.open(pth) as ds:
            arrays.append(ds.read(1))
    dem, sl, tri, rel = arrays
    nv = count_valid(dem, sl, tri, rel)
    n_dem = int(((dem != NODATA) & np.isfinite(dem)).sum())
    size = odd_cells(cell_m) if tag != "463m" else odd_cells(cell_m)
    # prefer the tag written on the elevation file
    with rasterio.open(paths[0]) as ds:
        size = int(ds.tags().get("RELIEF_WINDOW_CELLS") or size)
        ntiles = ds.tags().get("N_TILES")
    del arrays, dem, sl, tri, rel
    gc.collect()
    rec = {
        "width": width, "height": height, "cell_deg": deg, "cell_m_equator": cell_m,
        "n_teselas_glo90": int(ntiles) if ntiles else None,
        "n_celdas_validas_derivadas": nv,
        "relief_window_cells": size, "n_celdas_dem": n_dem,
        "recontado_de_archivos": True,
    }
    print(f"    (ya existía) n_dem={n_dem} n_validas={nv}")
    return rec


def prepare_ecuador():
    out_root = OUT / "earth" / "ecuador"
    out_root.mkdir(parents=True, exist_ok=True)
    crs = CRS.from_epsg(4326)
    results = {}
    for cell_m, tag, deg in ((MARS_M, "463m", DEG_MARS_EARTH), (MOON_M, "100m", DEG_MOON_EARTH)):
        west, south, east, north = ECUADOR["west"], ECUADOR["south"], ECUADOR["east"], ECUADOR["north"]
        width = int(math.ceil((east - west) / deg))
        height = int(math.ceil((north - south) / deg))
        transform = from_origin(west, north, deg, deg)
        print(f"  Ecuador {tag}: {width}×{height}, celda {deg:.6f}° ≈ {cell_m} m …", flush=True)
        paths = _ecuador_paths(out_root, tag)
        if all(pth.exists() and pth.stat().st_size > 1000 for pth in paths):
            results[tag] = recount_ecuador_tag(out_root, tag, width, height, deg, cell_m)
            continue
        dem, ntiles = mosaic_glo(west, south, east, north, transform, width, height, crs)
        print(f"    mosaico listo, calculando derivadas…", flush=True)
        n_dem = int(((dem != NODATA) & np.isfinite(dem)).sum())
        sl, tri, rel, size = derivatives_geo(dem, transform, EARTH_R)
        nv = count_valid(dem, sl, tri, rel)
        tags = {
            "REGION": "ecuador_plus_galapagos", "SCALE": tag, "CELL_M_EQUATOR": str(cell_m),
            "RELIEF_WINDOW_CELLS": str(size), "RELIEF_WINDOW_KM": str(RELIEF_KM),
            "SOURCE": "Copernicus DEM GLO-90; 0 exacto = nodata",
            "N_TILES": str(ntiles),
        }
        # Sin overviews en el 100 m mientras los arrays siguen en memoria.
        use_ov = tag == "463m"
        write_cog(out_root / f"ecuador_elevation_{tag}.tif", dem, transform, crs, tags, overviews=use_ov)
        del dem
        write_cog(out_root / f"ecuador_slope_{tag}.tif", sl, transform, crs, tags, overviews=use_ov)
        del sl
        write_cog(out_root / f"ecuador_roughness_{tag}.tif", tri, transform, crs, tags, overviews=use_ov)
        del tri
        write_cog(out_root / f"ecuador_relative_relief_{tag}.tif", rel, transform, crs, tags, overviews=use_ov)
        del rel
        gc.collect()
        results[tag] = {
            "width": width, "height": height, "cell_deg": deg, "cell_m_equator": cell_m,
            "n_teselas_glo90": ntiles, "n_celdas_validas_derivadas": nv,
            "relief_window_cells": size, "n_celdas_dem": n_dem,
        }
        print(f"    n_dem={n_dem} n_validas={nv}")
    return results


def main():
    os.environ.setdefault("GDAL_CACHEMAX", "256")
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = json.loads(CFG_PATH.read_text(encoding="utf-8"))
    print("1) Polígonos oficiales de las 9 regiones lunares")
    polys = official_polygons()
    (OUT / "moon_geometry_oficial.json").write_text(
        json.dumps([{k: v for k, v in p.items() if not k.startswith("geometry")} for p in polys],
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("2) Agregar LDEM_80S_20M → 100 m")
    ldem100 = aggregate_ldem_100m(OUT / "moon" / "ldem_80s_100m.tif")

    print("3) Ventanas lunares (polígono oficial, sin puntuar)")
    moon_n = prepare_moon(polys, ldem100)

    print("4) Ventanas de Marte (MOLA 128 ppd, sin puntuar)")
    mars_n = prepare_mars(cfg["sitios_objetivo"]["mars"])

    print("5) Tierra, 16 sitios del AUC, escalas 463 m y 100 m")
    catalog = json.loads((ROOT / "web/public/productos/catalogo.json").read_text(encoding="utf-8"))
    earth_n = prepare_earth_sites(catalog["sitios_validacion"])

    print("6) Ecuador + Galápagos, escalas 463 m y 100 m (derivadas, no el índice)")
    ecu = prepare_ecuador()

    manifest = {
        "estado": "preparado_sin_puntuar",
        "escalas_preespecificadas": {
            "marte_m": MARS_M,
            "luna_m": MOON_M,
            "luna_producto": "LDEM_80S_20M agregado 5×5 a 100 m",
            "motivo_100m_luna": (
                "El producto nativo es de 20 m (1,85 GB). A 20 m la Tierra no es comparable "
                "con el GLO-90 del paquete (~90 m en el ecuador; más grueso en longitud a "
                "latitudes altas) y haría falta GLO-30, que no está descargado. 100 m es un "
                "múltiplo exacto de 20 m (agregado 5×5) y queda a la escala nativa de GLO-90."
            ),
            "relieve_relativo": f"z − mediana en ventana física de {RELIEF_KM} km (la misma de la v1), no un número fijo de celdas",
        },
        "luna_regiones": moon_n,
        "marte_ventanas": mars_n,
        "tierra_validacion": earth_n,
        "ecuador": ecu,
        "no_se_corrio": "validación, umbrales, delta de Ecuador, mapa de clases, firmas de distancia",
    }
    (OUT / "preparacion_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("\n=== LISTO (sin puntuar) ===")
    print(json.dumps({
        "luna": [{k: r[k] for k in ("id", "nombre_oficial", "area_km2_atributo_usgs", "n_celdas_validas_derivadas")} for r in moon_n],
        "marte": [{k: r[k] for k in ("id", "n_celdas_validas_derivadas")} for r in mars_n],
        "ecuador": ecu,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
