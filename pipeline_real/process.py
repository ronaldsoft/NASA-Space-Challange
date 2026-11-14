#!/usr/bin/env python3
"""Construye las grillas de ~1 km (elevación, pendiente, TRI, latitud) por cuerpo."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.enums import Resampling as RioResampling
from rasterio.transform import Affine, from_origin
from rasterio.windows import Window

from config import (
    EARTH_1KM_DEG,
    EARTH_EPSG,
    EARTH_RADIUS_M,
    ECUADOR_BOUNDS,
    LAT_BANDS,
    LOLA_DEG,
    LOLA_PPD,
    MARS_1KM_DEG,
    MARS_RADIUS_M,
    MARS_WKT,
    MOLA_DEG,
    MOLA_PPD,
    MOLA_TILES,
    MOON_1KM_DEG,
    MOON_RADIUS_M,
    MOON_WKT,
    PROC_EARTH,
    PROC_MARS,
    PROC_MOON,
    PROC_VALID,
    PROCESSED,
    RAW_EARTH,
    RAW_MARS,
    RAW_MOON,
    SAMPLES_PER_BAND_HEMISPHERE,
    VALIDATION_SITES,
)
from download_earth import site_bounds
from terrain import (
    NODATA,
    grid_from_bounds,
    lat_for_rows,
    lon_for_cols,
    meters_per_degree,
    reproject_array,
    slope_and_tri,
    snapped_global_grid,
)

STRIP = 128  # filas de destino por tira (con halo)
OVERVIEWS = [2, 4, 8, 16, 32]


def _crs_mars():
    return CRS.from_wkt(MARS_WKT)


def _crs_moon():
    return CRS.from_wkt(MOON_WKT)


def _crs_earth():
    return CRS.from_epsg(EARTH_EPSG)


def _profile(width, height, transform, crs, dtype="float32", nodata=NODATA) -> dict:
    pred = 3 if dtype.startswith("float") else 2
    return dict(
        driver="GTiff",
        width=width,
        height=height,
        count=1,
        dtype=dtype,
        crs=crs,
        transform=transform,
        nodata=nodata,
        tiled=True,
        blockxsize=256,
        blockysize=256,
        compress="deflate",
        predictor=pred,
        zlevel=6,
        BIGTIFF="IF_SAFER",
        num_threads="all_cpus",
    )


def write_tif(path: Path, array: np.ndarray, transform, crs, nodata=NODATA, tags=None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = _profile(array.shape[1], array.shape[0], transform, crs, str(array.dtype), nodata)
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(array, 1)
        if tags:
            dst.update_tags(**tags)
    _overviews(path)
    return path


def _overviews(path: Path) -> None:
    try:
        with rasterio.open(path, "r+") as dst:
            factors = [f for f in OVERVIEWS if min(dst.width, dst.height) / f >= 16]
            if factors:
                dst.build_overviews(factors, RioResampling.average)
                dst.update_tags(ns="rio_overview", resampling="average")
    except Exception as exc:
        print(f"  (aviso) no se pudieron crear overviews en {path.name}: {exc}")


def _open_writer(path: Path, width, height, transform, crs, tags=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    profile = _profile(width, height, transform, crs)
    dst = rasterio.open(path, "w", **profile)
    if tags:
        dst.update_tags(**tags)
    return dst


# ---------------------------------------------------------------------------
# Marte / Luna: mosaico nativo y remuestreo por tiras
# ---------------------------------------------------------------------------

def write_mars_native() -> Path:
    """Mosaico global MEGT 64 ppd, lon [-180, 180], int16 metros (areoide MOLA)."""
    out = RAW_MARS / "mola_megt_64ppd_m180_180.tif"
    height, width = 11520, 23040
    transform = Affine(MOLA_DEG, 0, -180.0, 0, -MOLA_DEG, 90.0)
    tags = {
        "BODY": "mars",
        "DATUM_VERTICAL": "MOLA areoid (GMM3/mgm1025 grado 50)",
        "DATUM_HORIZONTAL": "IAU2000 planetocentric, esfera 3396.0 km (rotulo MEGDR)",
        "SOURCE": "MGS MOLA MEGDR 64 ppd topography (megt*gb)",
    }
    # Layout lon -180..180:
    #   cols 0..11519   <- tiles *180* (180..360 E) mapeados a -180..0
    #   cols 11520..    <- tiles *000* (0..180 E)
    mapping = {
        "megt90n180gb": (0, 0),
        "megt90n000gb": (0, 11520),
        "megt00n180gb": (5760, 0),
        "megt00n000gb": (5760, 11520),
    }
    if out.exists() and out.stat().st_size > 100_000_000:
        print(f"  mosaico nativo ya existe: {out}")
        return out
    tmp = out.with_suffix(".tif.tmp")
    profile = _profile(width, height, transform, _crs_mars(), "int16", None)
    # predictor 2 for int
    with rasterio.open(tmp, "w", **profile) as dst:
        dst.update_tags(**tags)
        for name, (r0, c0) in mapping.items():
            arr = np.memmap(RAW_MARS / f"{name}.img", dtype=">i2", mode="r", shape=(5760, 11520))
            # write in row chunks to limit buffers
            chunk = 720
            for i in range(0, 5760, chunk):
                block = np.asarray(arr[i : i + chunk], dtype=np.int16)
                h, w = block.shape
                dst.write(block, 1, window=Window(c0, r0 + i, w, h))
            del arr
    tmp.replace(out)
    print(f"  escrito {out} ({out.stat().st_size/1e6:.1f} MB)")
    return out


def write_moon_native() -> Path:
    """LDEM 64 ppd, HEIGHT = DN * 0.5 m, lon [-180, 180], float32."""
    out = RAW_MOON / "ldem_64_m180_180_meters.tif"
    height, width = 11520, 23040
    transform = Affine(LOLA_DEG, 0, -180.0, 0, -LOLA_DEG, 90.0)
    tags = {
        "BODY": "moon",
        "DATUM_VERTICAL": "esfera 1737.4 km (HEIGHT = DN * 0.5)",
        "DATUM_HORIZONTAL": "Mean Earth / Polar Axis DE421, esfera 1737.4 km",
        "SOURCE": "LRO LOLA LDEM_64 V3.1",
        "SCALING_FACTOR": "0.5",
    }
    if out.exists() and out.stat().st_size > 100_000_000:
        print(f"  mosaico nativo ya existe: {out}")
        return out
    src = np.memmap(RAW_MOON / "ldem_64.img", dtype="<i2", mode="r", shape=(11520, 23040))
    tmp = out.with_suffix(".tif.tmp")
    profile = _profile(width, height, transform, _crs_moon(), "float32", NODATA)
    with rasterio.open(tmp, "w", **profile) as dst:
        dst.update_tags(**tags)
        # Reordenar columnas 0..360 a -180..180
        # fuente: cols 0..11519 = lon 0..180; cols 11520..23039 = lon 180..360 = -180..0
        chunk = 360
        for r0 in range(0, height, chunk):
            r1 = min(height, r0 + chunk)
            block = np.asarray(src[r0:r1], dtype=np.float32) * 0.5
            reordered = np.empty_like(block)
            reordered[:, :11520] = block[:, 11520:]
            reordered[:, 11520:] = block[:, :11520]
            dst.write(reordered, 1, window=Window(0, r0, width, r1 - r0))
            del block, reordered
    del src
    tmp.replace(out)
    print(f"  escrito {out} ({out.stat().st_size/1e6:.1f} MB)")
    return out


def process_global_body(
    native_tif: Path,
    out_dir: Path,
    body: str,
    res_nominal: float,
    radius_m: float,
    crs,
    wrap_x: bool = True,
) -> dict:
    """Remuestrea un DEM global a ~1 km y calcula pendiente, TRI y latitud."""
    out_dir.mkdir(parents=True, exist_ok=True)
    dst_transform, dst_w, dst_h, res = snapped_global_grid(res_nominal)
    eq_m = meters_per_degree(radius_m) * res
    print(f"  {body}: grilla {dst_w} x {dst_h}, celda {res:.8f}° ≈ {eq_m:.2f} m en el ecuador")

    paths = {
        "elevation": out_dir / f"{body}_elevation_1km.tif",
        "slope": out_dir / f"{body}_slope_1km.tif",
        "roughness": out_dir / f"{body}_roughness_tri_1km.tif",
        "latitude": out_dir / f"{body}_latitude_1km.tif",
    }
    tags = {
        "BODY": body,
        "CELL_DEG": f"{res:.12f}",
        "CELL_M_EQUATOR": f"{eq_m:.4f}",
        "RADIUS_M": f"{radius_m}",
        "SLOPE_METHOD": "Horn 3x3, scale = radius * pi/180 * cos(lat)",
        "TRI_METHOD": "Wilson et al. (media de |dz| en 8 vecinos, DEM ya remuestreado)",
    }

    writers = {k: _open_writer(p, dst_w, dst_h, dst_transform, crs, tags) for k, p in paths.items()}

    # latitud: constante por fila — se escribe una vez
    lats = lat_for_rows(dst_transform, dst_h).astype(np.float32)
    # no cargamos un raster completo de latitud: escribimos por tiras

    stats = {k: {"min": np.inf, "max": -np.inf, "sum": 0.0, "n": 0} for k in ("elevation", "slope", "roughness")}

    def upd(key, arr):
        m = np.isfinite(arr) & (arr != NODATA)
        if not m.any():
            return
        v = arr[m]
        s = stats[key]
        s["min"] = float(min(s["min"], v.min()))
        s["max"] = float(max(s["max"], v.max()))
        s["sum"] += float(v.sum())
        s["n"] += int(m.sum())

    with rasterio.open(native_tif) as src:
        src_nodata = src.nodata
        for r0 in range(0, dst_h, STRIP):
            r1 = min(dst_h, r0 + STRIP)
            ha0 = max(0, r0 - 1)
            ha1 = min(dst_h, r1 + 1)
            win_h = ha1 - ha0
            win_transform = Affine(
                dst_transform.a, 0.0, dst_transform.c,
                0.0, dst_transform.e, dst_transform.f + ha0 * dst_transform.e,
            )
            # ventana fuente que cubre este destino + margen de remuestreo
            # bounds of dest halo
            west = win_transform.c
            north = win_transform.f
            east = west + dst_w * win_transform.a
            south = north + win_h * win_transform.e
            # un píxel de margen en el origen
            pad = 2 * abs(src.transform.a)
            src_win = rasterio.windows.from_bounds(
                west - pad, south - pad, east + pad, north + pad, transform=src.transform
            )
            src_win = src_win.intersection(Window(0, 0, src.width, src.height))
            src_win = src_win.round_offsets().round_lengths()
            src_arr = src.read(1, window=src_win, boundless=False, fill_value=src_nodata or 0)
            src_tr = rasterio.windows.transform(src_win, src.transform)
            dest = reproject_array(
                src_arr,
                src_tr,
                src.crs,
                (win_h, dst_w),
                win_transform,
                crs,
                src_nodata if src_nodata is not None else None,
                NODATA,
                RioResampling.bilinear,
            )
            sl, tri = slope_and_tri(dest, win_transform, radius_m, NODATA, wrap_x=wrap_x)
            # recorta el halo
            off = r0 - ha0
            length = r1 - r0
            elev_out = dest[off : off + length]
            sl_out = sl[off : off + length]
            tri_out = tri[off : off + length]
            lat_out = np.repeat(lats[r0:r1, None], dst_w, axis=1)

            win = Window(0, r0, dst_w, length)
            writers["elevation"].write(elev_out, 1, window=win)
            writers["slope"].write(sl_out, 1, window=win)
            writers["roughness"].write(tri_out, 1, window=win)
            writers["latitude"].write(lat_out, 1, window=win)
            upd("elevation", elev_out)
            upd("slope", sl_out)
            upd("roughness", tri_out)
            if r0 // STRIP % 10 == 0:
                print(f"    tira {r0}:{r1} / {dst_h}")

    for w in writers.values():
        w.close()
    for p in paths.values():
        _overviews(p)

    for k, s in stats.items():
        s["mean"] = (s["sum"] / s["n"]) if s["n"] else None
        s.pop("sum")
    return {
        "body": body,
        "width": dst_w,
        "height": dst_h,
        "cell_deg": res,
        "cell_m_equator": eq_m,
        "paths": {k: str(p) for k, p in paths.items()},
        "stats": stats,
        "radius_m": radius_m,
    }


# ---------------------------------------------------------------------------
# Tierra
# ---------------------------------------------------------------------------

def _copdem_masked(path: Path) -> tuple[np.ndarray, Affine, object]:
    with rasterio.open(path) as src:
        arr = src.read(1).astype(np.float32)
        # 0 exacto = agua / no-dato en GLO-90 (se documenta la limitación)
        arr = np.where((arr == 0.0) | ~np.isfinite(arr), NODATA, arr)
        return arr, src.transform, src.crs


def mosaic_tiles_to_grid(tile_paths: list[Path], transform, width, height, crs) -> np.ndarray:
    acc = np.zeros((height, width), dtype=np.float64)
    wgt = np.zeros((height, width), dtype=np.uint8)
    for i, p in enumerate(tile_paths):
        arr, tr, src_crs = _copdem_masked(p)
        dest = reproject_array(
            arr, tr, src_crs, (height, width), transform, crs,
            NODATA, NODATA, RioResampling.bilinear,
        )
        m = dest != NODATA
        acc[m] += dest[m]
        # saturación a 1: suficiente (teselas no deberían solaparse más que en bordes)
        wgt[m] = 1
        acc_m = dest  # silence unused in last iter
        if (i + 1) % 25 == 0:
            print(f"    teselas {i+1}/{len(tile_paths)}")
    out = np.full((height, width), NODATA, dtype=np.float32)
    m = wgt > 0
    out[m] = (acc[m] / wgt[m]).astype(np.float32)
    return out


def derivatives_from_dem(dem, transform, radius_m, crs, out_dir: Path, prefix: str, tags=None) -> dict:
    sl, tri = slope_and_tri(dem, transform, radius_m, NODATA, wrap_x=False)
    lats = lat_for_rows(transform, dem.shape[0]).astype(np.float32)
    lat = np.repeat(lats[:, None], dem.shape[1], axis=1)
    # enmascara latitud donde no hay DEM
    lat_out = np.where(dem != NODATA, lat, NODATA).astype(np.float32)
    paths = {}
    for key, arr in {
        "elevation": dem.astype(np.float32, copy=False),
        "slope": sl,
        "roughness": tri,
        "latitude": lat_out,
    }.items():
        p = out_dir / f"{prefix}_{key}_1km.tif"
        write_tif(p, arr, transform, crs, NODATA, tags)
        paths[key] = str(p)
    stats = {}
    for key, arr in {"elevation": dem, "slope": sl, "roughness": tri}.items():
        m = (arr != NODATA) & np.isfinite(arr)
        stats[key] = {
            "min": float(arr[m].min()) if m.any() else None,
            "max": float(arr[m].max()) if m.any() else None,
            "mean": float(arr[m].mean()) if m.any() else None,
            "n": int(m.sum()),
        }
    return {"paths": paths, "stats": stats, "shape": [int(dem.shape[0]), int(dem.shape[1])]}


def process_earth() -> dict:
    print("== Tierra / Copernicus GLO-90 ==")
    PROC_EARTH.mkdir(parents=True, exist_ok=True)
    PROC_VALID.mkdir(parents=True, exist_ok=True)
    crs = _crs_earth()
    tiles = sorted(RAW_EARTH.glob("Copernicus_DSM_COG_30_*.tif"))
    print(f"  teselas locales: {len(tiles)}")

    # Ecuador (caja que incluye Galápagos)
    b = ECUADOR_BOUNDS
    transform, w, h = grid_from_bounds(b["west"], b["south"], b["east"], b["north"], EARTH_1KM_DEG)
    eq_m = meters_per_degree(EARTH_RADIUS_M) * EARTH_1KM_DEG
    print(f"  Ecuador+Galápagos: {w} x {h}, celda {EARTH_1KM_DEG}° ≈ {eq_m:.2f} m en el ecuador")
    tags = {
        "BODY": "earth",
        "REGION": "ecuador_plus_galapagos",
        "CELL_DEG": str(EARTH_1KM_DEG),
        "CELL_M_EQUATOR": f"{eq_m:.4f}",
        "VERTICAL_DATUM": "EGM2008 (Copernicus DEM GLO-90)",
        "HORIZONTAL_DATUM": "EPSG:4326 WGS84",
        "SOURCE": "Copernicus DEM GLO-90 (AWS Open Data s3://copernicus-dem-90m)",
        "NODATA_NOTE": "Se trata 0 exacto como no-dato (mar / agua en GLO-90)",
    }
    dem = mosaic_tiles_to_grid(tiles, transform, w, h, crs)
    ecu = derivatives_from_dem(dem, transform, EARTH_RADIUS_M, crs, PROC_EARTH, "ecuador", tags)
    ecu["cell_deg"] = EARTH_1KM_DEG
    ecu["cell_m_equator"] = eq_m
    ecu["width"] = w
    ecu["height"] = h
    del dem

    # Ventanas de validación
    sites_out = []
    for s in VALIDATION_SITES:
        west, south, east, north = site_bounds(s["lat"], s["lon"], s.get("buffer_km"))
        tr, ww, hh = grid_from_bounds(west, south, east, north, EARTH_1KM_DEG)
        # teselas que intersectan
        site_tiles = []
        for p in tiles:
            # rápido: todas, pero reproject es barato en ventanas chicas; filtra por nombre si se puede
            site_tiles.append(p)
        # filtra por intersección real
        used = []
        for p in tiles:
            with rasterio.open(p) as src:
                if _intersects(src.bounds, west, south, east, north):
                    used.append(p)
        if not used:
            print(f"  AVISO: sin teselas para {s['id']}")
            continue
        dem = mosaic_tiles_to_grid(used, tr, ww, hh, crs)
        stags = dict(tags)
        stags["REGION"] = s["id"]
        stags["SITE_LAT"] = str(s["lat"])
        stags["SITE_LON"] = str(s["lon"])
        sub = PROC_VALID / s["id"]
        info = derivatives_from_dem(dem, tr, EARTH_RADIUS_M, crs, sub, s["id"], stags)
        # valor en la celda del sitio
        # col/row del punto
        col = int((s["lon"] - tr.c) / tr.a)
        row = int((s["lat"] - tr.f) / tr.e)
        sample = {}
        if 0 <= row < hh and 0 <= col < ww:
            sample = {
                "elevation_m": _val(dem[row, col]),
                "slope_deg": _val(rasterio.open(info["paths"]["slope"]).read(1)[row, col]),
                "roughness_tri_m": _val(rasterio.open(info["paths"]["roughness"]).read(1)[row, col]),
            }
        sites_out.append({
            **s,
            "window": {"west": west, "south": south, "east": east, "north": north, "width": ww, "height": hh},
            "cell": sample,
            "paths": info["paths"],
            "stats": info["stats"],
        })
        print(f"  sitio {s['id']}: elev={sample.get('elevation_m')} slope={sample.get('slope_deg')}")
        del dem

    return {"ecuador": ecu, "validation_sites": sites_out}


def _intersects(b, west, south, east, north) -> bool:
    return not (b.right < west or b.left > east or b.top < south or b.bottom > north)


def _val(x):
    x = float(x)
    if x == NODATA or not np.isfinite(x):
        return None
    return x


# ---------------------------------------------------------------------------
# Muestreo estratificado (Marte / Luna)
# ---------------------------------------------------------------------------

def stratified_sample(meta: dict, seed: int = 42) -> Path:
    """Muestras por banda de latitud (ambos hemisferios) sobre la grilla de 1 km."""
    body = meta["body"]
    out = PROCESSED / body / f"{body}_latband_samples.npz"
    rng = np.random.default_rng(seed)
    elev_p = meta["paths"]["elevation"]
    slope_p = meta["paths"]["slope"]
    tri_p = meta["paths"]["roughness"]
    records = []  # we'll stack at the end
    bands_info = []
    with rasterio.open(elev_p) as e, rasterio.open(slope_p) as s, rasterio.open(tri_p) as t:
        transform = e.transform
        height = e.height
        lats = lat_for_rows(transform, height)
        lons = lon_for_cols(transform, e.width)
        for band in LAT_BANDS:
            for sign, hemi in ((1.0, "N"), (-1.0, "S")):
                lo, hi = band["lat_min"], band["lat_max"]
                if hemi == "S":
                    lo, hi = -band["lat_max"], -band["lat_min"]
                rows = np.where((lats >= lo) & (lats < hi))[0]
                if rows.size == 0:
                    continue
                # lee solo esas filas
                win = Window(0, int(rows[0]), e.width, int(rows[-1] - rows[0] + 1))
                ev = e.read(1, window=win)
                sl = s.read(1, window=win)
                tr = t.read(1, window=win)
                valid = (ev != NODATA) & (sl != NODATA) & (tr != NODATA) & np.isfinite(ev)
                ys, xs = np.where(valid)
                n_avail = ys.size
                n = min(SAMPLES_PER_BAND_HEMISPHERE, n_avail)
                if n == 0:
                    bands_info.append({"band": band["id"], "hemi": hemi, "n": 0, "available": 0})
                    continue
                # muestreo sistemático + jitter: elige índices igualmente espaciados
                if n < n_avail:
                    idx = np.linspace(0, n_avail - 1, n, dtype=int)
                    # pequeño desplazamiento reproducible
                    jitter = rng.integers(0, max(1, n_avail // n), size=n)
                    idx = np.clip(idx + jitter, 0, n_avail - 1)
                    # único
                    idx = np.unique(idx)
                else:
                    idx = np.arange(n_avail)
                ys, xs = ys[idx], xs[idx]
                rr = ys + int(rows[0])
                rec = np.column_stack([
                    np.full(len(ys), lats[rr]),
                    np.full(len(ys), 0.0),  # lon filled next
                    ev[ys, xs],
                    sl[ys, xs],
                    tr[ys, xs],
                ])
                rec[:, 1] = lons[xs]
                records.append(rec)
                bands_info.append({
                    "band": band["id"],
                    "hemi": hemi,
                    "lat_min": lo,
                    "lat_max": hi,
                    "n": int(len(ys)),
                    "available": int(n_avail),
                })
                print(f"    muestra {body} {band['id']}{hemi}: {len(ys)} / {n_avail}")
    if records:
        data = np.vstack(records).astype(np.float32)
    else:
        data = np.zeros((0, 5), dtype=np.float32)
    np.savez_compressed(
        out,
        columns=np.array(["latitude", "longitude", "elevation_m", "slope_deg", "roughness_tri_m"]),
        data=data,
        body=np.array(body),
        bands=np.array(json.dumps(bands_info)),
    )
    print(f"  muestras {body}: {data.shape[0]} celdas -> {out}")
    meta["samples"] = {"path": str(out), "n": int(data.shape[0]), "bands": bands_info}
    return out


def main() -> int:
    print("Memoria / rutas OK. Inicio de procesamiento.")
    # Marte
    print("== Marte / MOLA MEGDR 64 ppd ==")
    mars_native = write_mars_native()
    mars_meta = process_global_body(
        mars_native, PROC_MARS, "mars", MARS_1KM_DEG, MARS_RADIUS_M, _crs_mars(), True
    )
    stratified_sample(mars_meta)
    (PROC_MARS / "meta.json").write_text(json.dumps(mars_meta, indent=2, ensure_ascii=False))

    # Luna
    print("== Luna / LOLA LDEM 64 ppd ==")
    moon_native = write_moon_native()
    moon_meta = process_global_body(
        moon_native, PROC_MOON, "moon", MOON_1KM_DEG, MOON_RADIUS_M, _crs_moon(), True
    )
    stratified_sample(moon_meta)
    (PROC_MOON / "meta.json").write_text(json.dumps(moon_meta, indent=2, ensure_ascii=False))

    # Tierra
    earth_meta = process_earth()
    (PROC_EARTH / "meta.json").write_text(json.dumps(earth_meta, indent=2, ensure_ascii=False))

    summary = {"mars": mars_meta, "moon": moon_meta, "earth": earth_meta}
    (PROCESSED / "processing_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False)
    )
    print("Procesamiento terminado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
