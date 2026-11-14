#!/usr/bin/env python3
"""Descarga teselas Copernicus DEM GLO-90 (AWS Open Data, sin autenticación)."""

from __future__ import annotations

import math
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from config import (
    COP_BUCKET,
    COP_TILELIST_URL,
    EARTH_RADIUS_M,
    ECUADOR_BOUNDS,
    RAW_EARTH,
    TILELIST,
    VALIDATION_MARGIN_M,
    VALIDATION_SITES,
)


def tile_name(lat_south: int, lon_west: int) -> str:
    """Nombre de carpeta/archivo GLO-90 (sur y oeste del tesela de 1°)."""
    lat_tok = f"N{lat_south:02d}" if lat_south >= 0 else f"S{abs(lat_south):02d}"
    lon_tok = f"E{lon_west:03d}" if lon_west >= 0 else f"W{abs(lon_west):03d}"
    return f"Copernicus_DSM_COG_30_{lat_tok}_00_{lon_tok}_00_DEM"


def tiles_for_bounds(west: float, south: float, east: float, north: float) -> list[str]:
    """Teselas de 1° que intersectan un recuadro [west,south,east,north] en lon/lat.

    Soporta recuadros que cruzan el antimeridiano (west > east).
    """
    names: set[str] = set()

    def lon_range(w: float, e: float) -> range:
        # west edge integers that intersect [w, e]
        lo = math.floor(w)
        hi = math.floor(e - 1e-12)  # if e is integer, last tile west is e-1
        return range(int(lo), int(hi) + 1)

    lat_souths = range(int(math.floor(south)), int(math.floor(north - 1e-12)) + 1)

    if west <= east:
        lon_wests = list(lon_range(west, east))
    else:
        lon_wests = list(lon_range(west, 180.0)) + list(lon_range(-180.0, east))

    for ls in lat_souths:
        for lw in lon_wests:
            # normalize lon to [-180, 179]
            lw_n = ((lw + 180) % 360) - 180
            names.add(tile_name(ls, lw_n))
    return sorted(names)


def site_bounds(lat: float, lon: float, buffer_km: float | None = None) -> tuple[float, float, float, float]:
    """Recuadro en grados: buffer oficial (km) más margen, para pendiente/TRI."""
    buf_m = (float(buffer_km) * 1000.0) if buffer_km is not None else 25_000.0
    half = buf_m + VALIDATION_MARGIN_M
    mpd = EARTH_RADIUS_M * math.pi / 180.0
    dlat = half / mpd
    clon = max(0.15, abs(math.cos(math.radians(lat))))
    dlon = half / (mpd * clon)
    return lon - dlon, lat - dlat, lon + dlon, lat + dlat


def required_tiles() -> list[str]:
    names = set(
        tiles_for_bounds(
            ECUADOR_BOUNDS["west"],
            ECUADOR_BOUNDS["south"],
            ECUADOR_BOUNDS["east"],
            ECUADOR_BOUNDS["north"],
        )
    )
    for s in VALIDATION_SITES:
        w, s_, e, n = site_bounds(s["lat"], s["lon"], s.get("buffer_km"))
        names.update(tiles_for_bounds(w, s_, e, n))
    return sorted(names)


def load_available() -> set[str]:
    if not TILELIST.exists():
        TILELIST.parent.mkdir(parents=True, exist_ok=True)
        subprocess.check_call(
            ["curl", "-fsSL", "--retry", "5", "-o", str(TILELIST), COP_TILELIST_URL]
        )
    return {line.strip() for line in TILELIST.read_text().splitlines() if line.strip()}


def tile_url(name: str) -> str:
    return f"{COP_BUCKET}/{name}/{name}.tif"


def download_one(name: str, dest_dir: Path) -> tuple[str, str, int]:
    dest = dest_dir / f"{name}.tif"
    if dest.exists() and dest.stat().st_size > 1000:
        return name, "exists", dest.stat().st_size
    tmp = dest.with_suffix(".tif.part")
    cmd = [
        "curl",
        "-fL",
        "--retry",
        "5",
        "--retry-delay",
        "2",
        "--retry-all-errors",
        "-C",
        "-",
        "-o",
        str(tmp),
        tile_url(name),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        if tmp.exists():
            tmp.unlink()
        return name, f"fail:{r.returncode}", 0
    tmp.rename(dest)
    return name, "ok", dest.stat().st_size


def main() -> int:
    RAW_EARTH.mkdir(parents=True, exist_ok=True)
    wanted = required_tiles()
    available = load_available()
    to_fetch = [n for n in wanted if n in available]
    missing_in_catalog = [n for n in wanted if n not in available]
    print(f"Teselas requeridas: {len(wanted)}")
    print(f"Presentes en el catálogo GLO-90: {len(to_fetch)}")
    print(f"No existen (océano u otra causa): {len(missing_in_catalog)}")
    if missing_in_catalog:
        print("  ausentes:", ", ".join(missing_in_catalog[:20]), ("..." if len(missing_in_catalog) > 20 else ""))

    ok = fail = skipped = 0
    bytes_new = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(download_one, n, RAW_EARTH) for n in to_fetch]
        for i, fut in enumerate(as_completed(futs), 1):
            name, status, size = fut.result()
            if status == "ok":
                ok += 1
                bytes_new += size
            elif status == "exists":
                skipped += 1
            else:
                fail += 1
                print(f"  FALLO {name}: {status}")
            if i % 20 == 0 or i == len(to_fetch):
                print(f"  progreso {i}/{len(to_fetch)}  ok={ok} cache={skipped} fail={fail}")
    print(f"Listo. nuevas={ok} cache={skipped} fallos={fail} descargado={bytes_new/1e6:.1f} MB")
    (RAW_EARTH / "tiles_requested.txt").write_text(
        "\n".join(wanted) + "\n"
    )
    (RAW_EARTH / "tiles_missing_catalog.txt").write_text(
        "\n".join(missing_in_catalog) + "\n"
    )
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
