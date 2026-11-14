#!/usr/bin/env python3
"""Capa extra de relieve relativo (z − mediana en ~15 km) y reproceso de Askja."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from numpy.lib.stride_tricks import sliding_window_view
from scipy.ndimage import median_filter
from rasterio.windows import Window

from config import (
    PROC_EARTH,
    PROC_MARS,
    PROC_MOON,
    PROC_VALID,
    PROCESSED,
    RAW_EARTH,
    RELIEF_WINDOW_KM,
    VALIDATION_SITES,
)
from download_earth import site_bounds
from process import (
    _crs_earth,
    _intersects,
    _open_writer,
    _overviews,
    _val,
    derivatives_from_dem,
    mosaic_tiles_to_grid,
    write_tif,
)
from terrain import NODATA, meters_per_degree

# Reexport CSV paths used by run_remaining
CSV_PATHS = [
    PROCESSED / "earth" / "validation_sites.csv",
    Path("/workspace") / "validacion_sitios.csv",
]


def window_cells(cell_m_equator: float, window_km: float = RELIEF_WINDOW_KM) -> int:
    """Número impar de celdas que aproxima window_km en el ecuador."""
    n = int(round((window_km * 1000.0) / cell_m_equator))
    if n % 2 == 0:
        n += 1
    return max(3, n)


def focal_nanmedian(
    z: np.ndarray,
    size: int,
    nodata: float = NODATA,
    wrap_x: bool = False,
    min_frac: float = 0.5,
    batch: int = 24,
) -> np.ndarray:
    """Mediana focal ignorando no-datos. `size` debe ser impar."""
    assert size % 2 == 1
    pad = size // 2
    z64 = z.astype(np.float64, copy=False)
    invalid = ~np.isfinite(z64) | (z64 == nodata)
    work = z64.copy()
    work[invalid] = np.nan
    if wrap_x:
        work = np.pad(work, ((pad, pad), (0, 0)), mode="constant", constant_values=np.nan)
        work = np.pad(work, ((0, 0), (pad, pad)), mode="wrap")
    else:
        work = np.pad(work, pad, mode="constant", constant_values=np.nan)

    h, w = z.shape
    out = np.full((h, w), np.nan, dtype=np.float64)
    min_n = max(1, int(np.ceil(min_frac * size * size)))
    for i0 in range(0, h, batch):
        i1 = min(h, i0 + batch)
        # sliding_window_view sobre filas [i0, i1) con halo
        sl = work[i0 : i1 + 2 * pad, :]
        wins = sliding_window_view(sl, (size, size))  # (i1-i0, w, size, size)
        flat = wins.reshape(wins.shape[0], wins.shape[1], -1)
        med = np.nanmedian(flat, axis=2)
        cnt = np.sum(np.isfinite(flat), axis=2)
        med = np.where(cnt >= min_n, med, np.nan)
        out[i0:i1] = med
        del wins, flat, med, cnt
    return out


def relative_relief_array(
    z: np.ndarray,
    size: int,
    nodata: float = NODATA,
    wrap_x: bool = False,
) -> np.ndarray:
    med = focal_nanmedian(z, size, nodata, wrap_x=wrap_x)
    out = np.full(z.shape, nodata, dtype=np.float32)
    valid = (z != nodata) & np.isfinite(z) & np.isfinite(med)
    out[valid] = (z[valid] - med[valid]).astype(np.float32)
    return out


def cell_m_from_ds(ds, radius_m: float | None = None) -> float:
    """Metros por celda en el ecuador, a partir de la resolución en grados."""
    # prefer tag
    tag = ds.tags().get("CELL_M_EQUATOR")
    if tag:
        try:
            return float(tag)
        except ValueError:
            pass
    deg = abs(ds.res[0])
    if radius_m is None:
        # heurística: si CRS es 4326 usamos WGS84
        radius_m = 6378137.0
    return meters_per_degree(radius_m) * deg



def relative_relief_scipy(src, size: int, nodata: float, wrap_x: bool) -> tuple[np.ndarray, dict]:
    """Mediana focal rápida para DEM casi sin huecos (Marte/Luna)."""
    z = src.read(1).astype(np.float32, copy=False)
    invalid = ~np.isfinite(z) | (z == nodata)
    fill = float(np.median(z[~invalid])) if (~invalid).any() else 0.0
    work = z.copy()
    work[invalid] = fill
    pad = size // 2
    if wrap_x:
        work = np.pad(work, ((pad, pad), (0, 0)), mode="edge")
        work = np.pad(work, ((0, 0), (pad, pad)), mode="wrap")
        med = median_filter(work, size=size, mode="nearest")
        med = med[pad:-pad, pad:-pad]
        del work
    else:
        med = median_filter(work, size=size, mode="nearest")
        del work
    rel = np.full(z.shape, nodata, dtype=np.float32)
    valid = ~invalid
    rel[valid] = z[valid] - med[valid]
    del med
    m = (rel != nodata) & np.isfinite(rel)
    stats = {
        "min": float(rel[m].min()) if m.any() else None,
        "max": float(rel[m].max()) if m.any() else None,
        "mean": float(rel[m].mean()) if m.any() else None,
        "n": int(m.sum()),
    }
    return rel, stats

def write_relief_from_elev(
    elev_path: Path,
    out_path: Path,
    radius_m: float,
    wrap_x: bool,
    window_km: float = RELIEF_WINDOW_KM,
    global_strips: bool = False,
) -> dict:
    """Lee un DEM de 1 km y escribe relieve relativo. Si global_strips, no carga todo el DEM."""
    with rasterio.open(elev_path) as src:
        cell_m = cell_m_from_ds(src, radius_m)
        size = window_cells(cell_m, window_km)
        tags = dict(src.tags())
        tags.update(
            {
                "VARIABLE": "relative_relief",
                "DEFINITION": f"elevacion - mediana en ventana {size}x{size} celdas (~{window_km} km en el ecuador)",
                "WINDOW_CELLS": str(size),
                "WINDOW_KM_EQUATOR": str(window_km),
                "NOTE": "Capa extra. Pendiente de decision si sustituye a la elevacion absoluta en el indice.",
            }
        )
        print(f"  {elev_path.name} -> {out_path.name}  ventana {size}x{size} (~{window_km} km), wrap_x={wrap_x}")

        nodata = src.nodata if src.nodata is not None else NODATA
        # Globos casi completos: mediana de scipy (rápida). Tierra con huecos: nanmedian.
        if global_strips or (src.width * src.height > 2_000_000 and wrap_x):
            rel, stats = relative_relief_scipy(src, size, nodata, wrap_x)
            write_tif(out_path, rel, src.transform, src.crs, NODATA, tags)
            del rel
            return {"path": str(out_path), "window_cells": size, "window_km": window_km, "stats": stats}

        if not global_strips:
            z = src.read(1)
            rel = relative_relief_array(z, size, nodata, wrap_x)
            write_tif(out_path, rel, src.transform, src.crs, NODATA, tags)
            m = (rel != NODATA) & np.isfinite(rel)
            stats = {
                "min": float(rel[m].min()) if m.any() else None,
                "max": float(rel[m].max()) if m.any() else None,
                "mean": float(rel[m].mean()) if m.any() else None,
                "n": int(m.sum()),
            }
            return {"path": str(out_path), "window_cells": size, "window_km": window_km, "stats": stats}

        # tiras para globos grandes (reserva)
        nodata = src.nodata if src.nodata is not None else NODATA
        pad = size // 2
        dst = _open_writer(out_path, src.width, src.height, src.transform, src.crs, tags)
        stats = {"min": np.inf, "max": -np.inf, "sum": 0.0, "n": 0}
        strip = 160
        for r0 in range(0, src.height, strip):
            r1 = min(src.height, r0 + strip)
            ha0 = max(0, r0 - pad)
            ha1 = min(src.height, r1 + pad)
            # si wrap en Y no aplica; en X sí (se maneja dentro de la tira leída a lo ancho)
            z = src.read(1, window=Window(0, ha0, src.width, ha1 - ha0))
            rel_h = relative_relief_array(z, size, nodata, wrap_x=wrap_x)
            off = r0 - ha0
            rel = rel_h[off : off + (r1 - r0)]
            dst.write(rel, 1, window=Window(0, r0, src.width, r1 - r0))
            m = (rel != NODATA) & np.isfinite(rel)
            if m.any():
                v = rel[m]
                stats["min"] = float(min(stats["min"], v.min()))
                stats["max"] = float(max(stats["max"], v.max()))
                stats["sum"] += float(v.sum())
                stats["n"] += int(m.sum())
            if r0 % (strip * 8) == 0:
                print(f"    tira relieve {r0}:{r1}/{src.height}")
        dst.close()
        _overviews(out_path)
        stats["mean"] = (stats["sum"] / stats["n"]) if stats["n"] else None
        stats.pop("sum")
        return {"path": str(out_path), "window_cells": size, "window_km": window_km, "stats": stats}


def enrich_samples(npz_path: Path, relief_tif: Path) -> None:
    """Añade relative_relief_m a las muestras existentes (mismas celdas)."""
    z = np.load(npz_path, allow_pickle=True)
    cols = [str(c) for c in z["columns"]]
    data = z["data"]
    extra = {k: z[k] for k in z.files if k not in {"columns", "data"}}
    lat_i, lon_i = cols.index("latitude"), cols.index("longitude")
    vals = np.full((data.shape[0],), np.nan, dtype=np.float32)
    with rasterio.open(relief_tif) as src:
        coords = list(zip(data[:, lon_i].tolist(), data[:, lat_i].tolist()))
        for i, (samp,) in enumerate(src.sample(coords)):
            v = float(samp)
            vals[i] = v if v != src.nodata and np.isfinite(v) else np.nan
    if "relative_relief_m" in cols:
        data[:, cols.index("relative_relief_m")] = vals
    else:
        cols.append("relative_relief_m")
        data = np.column_stack([data, vals])
    np.savez_compressed(npz_path, columns=np.array(cols), data=data, **extra)
    n_ok = int(np.isfinite(vals).sum())
    print(f"  muestras actualizadas {npz_path.name}: relief válido en {n_ok}/{len(vals)}")


def reprocess_askja() -> dict:
    """Rehace la ventana de Askja con la coordenada confirmada."""
    site = next(s for s in VALIDATION_SITES if s["id"] == "askja")
    west, south, east, north = site_bounds(site["lat"], site["lon"], site.get("buffer_km"))
    # Asegura que la ventana cubra bocas y frente de la colada + un poco de margen
    for lat, lon in ((65.0647, -16.7247), (65.0590, -16.5454)):
        w, s_, e, n = site_bounds(lat, lon, 2.0)  # 2 km + margen de config
        west, south, east, north = min(west, w), min(south, s_), max(east, e), max(north, n)

    from config import EARTH_1KM_DEG as EDEG, EARTH_RADIUS_M
    from terrain import grid_from_bounds

    tr, ww, hh = grid_from_bounds(west, south, east, north, EDEG)
    tiles = []
    for p in RAW_EARTH.glob("Copernicus_DSM_COG_30_*.tif"):
        with rasterio.open(p) as src:
            if _intersects(src.bounds, west, south, east, north):
                tiles.append(p)
    if not tiles:
        raise SystemExit(f"Sin teselas GLO-90 para Askja en {west,south,east,north}")
    print(f"  Askja ventana W{west:.4f} S{south:.4f} E{east:.4f} N{north:.4f}  teselas={len(tiles)}  grid={ww}x{hh}")
    dem = mosaic_tiles_to_grid(tiles, tr, ww, hh, _crs_earth())
    tags = {
        "BODY": "earth",
        "REGION": "askja",
        "SITE_LAT": str(site["lat"]),
        "SITE_LON": str(site["lon"]),
        "BUFFER_KM": str(site["buffer_km"]),
        "VERTICAL_DATUM": "EGM2008 (Copernicus DEM GLO-90)",
        "SOURCE": "Copernicus DEM GLO-90",
        "NOTE": "Coordenada confirmada Blasizzo et al. 2022; se descarta 65.03,-16.78",
    }
    sub = PROC_VALID / "askja"
    sub.mkdir(parents=True, exist_ok=True)
    info = derivatives_from_dem(dem, tr, EARTH_RADIUS_M, _crs_earth(), sub, "askja", tags)
    # relieve relativo de la ventana
    size = window_cells(meters_per_degree(EARTH_RADIUS_M) * EDEG)
    rel = relative_relief_array(dem, size, NODATA, wrap_x=False)
    rel_path = sub / "askja_relative_relief_1km.tif"
    write_tif(rel_path, rel, tr, _crs_earth(), NODATA, {**tags, "VARIABLE": "relative_relief"})
    col = int((site["lon"] - tr.c) / tr.a)
    row = int((site["lat"] - tr.f) / tr.e)
    cell = {}
    if 0 <= row < hh and 0 <= col < ww:
        cell = {
            "elevation_m": _val(dem[row, col]),
            "slope_deg": _val(rasterio.open(info["paths"]["slope"]).read(1)[row, col]),
            "roughness_tri_m": _val(rasterio.open(info["paths"]["roughness"]).read(1)[row, col]),
            "relative_relief_m": _val(rel[row, col]),
        }
    print(f"  Askja celda row={row} col={col} {cell}")
    return {
        **site,
        "window": {"west": west, "south": south, "east": east, "north": north, "width": ww, "height": hh},
        "cell": cell,
        "paths": {**info["paths"], "relative_relief": str(rel_path)},
        "stats": info["stats"],
    }


def rewrite_csv(earth_meta: dict) -> None:
    by_id = {s["id"]: s for s in earth_meta.get("validation_sites") or []}
    fields = [
        "id", "name", "lat", "lon", "buffer_km", "etiqueta", "clase",
        "elevation_m", "slope_deg", "roughness_tri_m", "relative_relief_m",
        "window_west", "window_south", "window_east", "window_north",
        "notas",
    ]
    rows = []
    for s in VALIDATION_SITES:
        info = by_id.get(s["id"], {})
        cell = info.get("cell") or {}
        win = info.get("window") or {}
        rows.append({
            "id": s["id"],
            "name": s["name"],
            "lat": s["lat"],
            "lon": s["lon"],
            "buffer_km": s["buffer_km"],
            "etiqueta": s["etiqueta"],
            "clase": s["clase"],
            "elevation_m": cell.get("elevation_m"),
            "slope_deg": cell.get("slope_deg"),
            "roughness_tri_m": cell.get("roughness_tri_m"),
            "relative_relief_m": cell.get("relative_relief_m"),
            "window_west": win.get("west"),
            "window_south": win.get("south"),
            "window_east": win.get("east"),
            "window_north": win.get("north"),
            "notas": s.get("notas", ""),
        })
    for path in CSV_PATHS:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writerows([]) if False else None
            w.writeheader()
            w.writerows(rows)
        print("CSV:", path)


def sample_relief_at_sites(earth_meta: dict) -> None:
    """Rellena relative_relief_m en cada sitio (si existe el ráster)."""
    for s in earth_meta.get("validation_sites") or []:
        paths = s.get("paths") or {}
        relp = paths.get("relative_relief") or paths.get("elevation", "").replace("_elevation_", "_relative_relief_")
        if not relp or not Path(relp).exists():
            continue
        lat = s.get("lat")
        lon = s.get("lon")
        with rasterio.open(relp) as src:
            r, c = src.index(lon, lat)
            if 0 <= r < src.height and 0 <= c < src.width:
                s.setdefault("cell", {})["relative_relief_m"] = _val(src.read(1)[r, c])


def main() -> int:
    from config import EARTH_RADIUS_M
    skip_earth = "--only-planetary" in sys.argv
    askja_info = None
    if skip_earth:
        print("== Omitiendo Tierra/Askja (ya calculados) ==")
        ecu_rel = {"path": str(PROC_EARTH / "ecuador_relative_relief_1km.tif")}
    else:
        print("== Reproceso Askja (65.060, -16.640, buffer 6 km) ==")
        askja_info = reprocess_askja()

        print("== Relieve relativo Ecuador y sitios de validación ==")
        ecu_elev = PROC_EARTH / "ecuador_elevation_1km.tif"
        ecu_rel = write_relief_from_elev(ecu_elev, PROC_EARTH / "ecuador_relative_relief_1km.tif", EARTH_RADIUS_M, False)
        print("  Ecuador relief", ecu_rel["stats"])

        # cada sitio (Askja ya tiene la capa)
        for d in sorted(PROC_VALID.iterdir()):
            if not d.is_dir():
                continue
            elev = d / f"{d.name}_elevation_1km.tif"
            if not elev.exists():
                continue
            if d.name == "askja":
                continue  # ya escrito
            out = d / f"{d.name}_relative_relief_1km.tif"
            info = write_relief_from_elev(elev, out, EARTH_RADIUS_M, False)

    print("== Relieve relativo Marte (tiras) ==")
    mars_rel = write_relief_from_elev(
        PROC_MARS / "mars_elevation_1km.tif",
        PROC_MARS / "mars_relative_relief_1km.tif",
        3_396_000.0,
        wrap_x=True,
        global_strips=True,
    )
    print("  Mars relief", mars_rel["stats"])

    print("== Relieve relativo Luna (tiras) ==")
    moon_rel = write_relief_from_elev(
        PROC_MOON / "moon_elevation_1km.tif",
        PROC_MOON / "moon_relative_relief_1km.tif",
        1_737_400.0,
        wrap_x=True,
        global_strips=True,
    )
    print("  Moon relief", moon_rel["stats"])

    print("== Actualizar muestras estratificadas ==")
    enrich_samples(PROC_MARS / "mars_latband_samples.npz", PROC_MARS / "mars_relative_relief_1km.tif")
    enrich_samples(PROC_MOON / "moon_latband_samples.npz", PROC_MOON / "moon_relative_relief_1km.tif")

    # metas
    earth_meta = json.loads((PROC_EARTH / "meta.json").read_text())
    if askja_info is not None:
        sites = earth_meta.get("validation_sites") or []
        sites = [s for s in sites if s.get("id") != "askja"]
        sites.append(askja_info)
        order = {s["id"]: i for i, s in enumerate(VALIDATION_SITES)}
        sites.sort(key=lambda s: order.get(s.get("id"), 999))
        earth_meta["validation_sites"] = sites
    earth_meta["relative_relief"] = {"ecuador": ecu_rel, "window_km": RELIEF_WINDOW_KM}
    sample_relief_at_sites(earth_meta)
    (PROC_EARTH / "meta.json").write_text(json.dumps(earth_meta, indent=2, ensure_ascii=False))

    mars_meta = json.loads((PROC_MARS / "meta.json").read_text())
    mars_meta["paths"]["relative_relief"] = mars_rel["path"]
    mars_meta["stats"]["relative_relief"] = mars_rel["stats"]
    (PROC_MARS / "meta.json").write_text(json.dumps(mars_meta, indent=2, ensure_ascii=False))

    moon_meta = json.loads((PROC_MOON / "meta.json").read_text())
    moon_meta["paths"]["relative_relief"] = moon_rel["path"]
    moon_meta["stats"]["relative_relief"] = moon_rel["stats"]
    (PROC_MOON / "meta.json").write_text(json.dumps(moon_meta, indent=2, ensure_ascii=False))

    summary = {"mars": mars_meta, "moon": moon_meta, "earth": earth_meta}
    (PROCESSED / "processing_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))

    rewrite_csv(earth_meta)

    import write_docs
    write_docs.main()
    print("Listo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
