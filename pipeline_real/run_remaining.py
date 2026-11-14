#!/usr/bin/env python3
"""Re-muestrea bandas oficiales, procesa Tierra (Ecuador + sitios) y escribe docs/CSV."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from config import DATA, PROCESSED, PROC_EARTH, PROC_MARS, PROC_MOON, VALIDATION_SITES, SITES_EXCLUDED
from process import process_earth, stratified_sample
import write_docs

CSV_PATHS = [
    PROCESSED / "earth" / "validation_sites.csv",
    Path("/workspace") / "validacion_sitios.csv",
]


def write_csv(earth_meta: dict) -> None:
    by_id = {s["id"]: s for s in earth_meta.get("validation_sites") or []}
    fields = [
        "id", "name", "lat", "lon", "buffer_km", "etiqueta", "clase",
        "elevation_m", "slope_deg", "roughness_tri_m",
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
            w.writeheader()
            w.writerows(rows)
        print("CSV:", path)


def main() -> int:
    print("== Re-muestreo oficial Marte ==")
    mars_meta = json.loads((PROC_MARS / "meta.json").read_text())
    # drop old samples
    stratified_sample(mars_meta)
    (PROC_MARS / "meta.json").write_text(json.dumps(mars_meta, indent=2, ensure_ascii=False))

    print("== Re-muestreo oficial Luna (incluye banda G, polo sur) ==")
    moon_meta = json.loads((PROC_MOON / "meta.json").read_text())
    # moon meta may be missing if process was killed before writing it
    if "paths" not in moon_meta or "body" not in moon_meta:
        moon_meta = {
            "body": "moon",
            "width": 10916,
            "height": 5458,
            "cell_deg": 0.03297911322828875,
            "cell_m_equator": 1000.04,
            "paths": {
                "elevation": str(PROC_MOON / "moon_elevation_1km.tif"),
                "slope": str(PROC_MOON / "moon_slope_1km.tif"),
                "roughness": str(PROC_MOON / "moon_roughness_tri_1km.tif"),
                "latitude": str(PROC_MOON / "moon_latitude_1km.tif"),
            },
            "radius_m": 1737400.0,
            "stats": {},
        }
    # ensure paths
    moon_meta.setdefault("body", "moon")
    moon_meta.setdefault("paths", {
        "elevation": str(PROC_MOON / "moon_elevation_1km.tif"),
        "slope": str(PROC_MOON / "moon_slope_1km.tif"),
        "roughness": str(PROC_MOON / "moon_roughness_tri_1km.tif"),
        "latitude": str(PROC_MOON / "moon_latitude_1km.tif"),
    })
    stratified_sample(moon_meta)
    (PROC_MOON / "meta.json").write_text(json.dumps(moon_meta, indent=2, ensure_ascii=False))

    print("== Tierra (Ecuador + sitios oficiales) ==")
    earth_meta = process_earth()
    earth_meta["sitios_excluidos"] = SITES_EXCLUDED
    (PROC_EARTH / "meta.json").write_text(json.dumps(earth_meta, indent=2, ensure_ascii=False))

    summary = {"mars": mars_meta, "moon": moon_meta, "earth": earth_meta}
    (PROCESSED / "processing_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False)
    )
    write_csv(earth_meta)
    write_docs.main()
    print("Listo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
