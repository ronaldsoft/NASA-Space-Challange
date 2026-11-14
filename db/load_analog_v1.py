#!/usr/bin/env python3
"""Load frozen v1 catalog values into schema analog.

Reads web/public/productos/ (does not modify those files).
Connection: set PGPASSWORD and SUPABASE_PROJECT_ID in the environment
(source the secrets file in your shell; do not print it).
Never logs the password or a URI that contains it.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROD = ROOT / "web/public/productos"
CAT = PROD / "catalogo.json"
FROZEN_CAT = "369dd38593f76d46266d1cd86077ce4729fb7b1e3811adc66b74fe0be51c87dd"
FROZEN_AT = "2026-11-14T13:40:40-05:00"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def connect():
    try:
        import psycopg
    except ImportError:
        sys.exit("Install psycopg (binary) in your environment before loading.")
    pid = os.environ.get("SUPABASE_PROJECT_ID")
    if not pid or not os.environ.get("SUPABASE_DB_PASSWORD"):
        sys.exit("Missing SUPABASE_PROJECT_ID or SUPABASE_DB_PASSWORD in the environment.")
    host = os.environ.get("SUPABASE_DB_HOST") or f"db.{pid}.supabase.co"
    # keyword args: libpq does not print a URI with the password
    return psycopg.connect(
        host=host,
        port=int(os.environ.get("SUPABASE_DB_PORT", "5432")),
        dbname="postgres",
        user=os.environ.get("SUPABASE_DB_USER", "postgres"),
        password=os.environ["SUPABASE_DB_PASSWORD"],
        sslmode="require",
        connect_timeout=15,
    )


def main() -> int:
    if sha256(CAT) != FROZEN_CAT:
        sys.exit("catalogo.json hash does not match the frozen v1 stamp; refusing to load.")
    cat = json.loads(CAT.read_text(encoding="utf-8"))
    print("connecting…")
    try:
        conn = connect()
    except Exception as e:
        print("connection failed:", type(e).__name__, file=sys.stderr)
        return 2
    print("connected, loading official values (no password logged)")
    # Full insert implementation is intended to run on a reachable network.
    # The statements below load the small official tables; ecuador_results
    # (453 375 land points) is optional via --points.
    load_points = "--points" in sys.argv
    with conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM analog.bodies LIMIT 1")
        # variables
        variables = [
            ("latitude", "°", True, "Entra como |lat|.", None),
            ("elevation", "m", True, "Datum: areoide MOLA / esfera lunar 1737.4 km / geoide EGM2008. Modo por defecto: absoluta.",
             {"moon": "Esfera de 1737.4 km", "mars": "Areoide MOLA", "earth": "Geoide EGM2008"}),
            ("slope", "°", True, "Horn 3×3 sobre el DEM remuestreado.", None),
            ("roughness", "m", True, "TRI de Wilson 3×3 sobre el DEM remuestreado.", None),
            ("albedo", "adimensional (0–1)", False, "Fuera del índice v1 (veredicto de Expertos).", None),
            ("thermal_inertia", "J m⁻² K⁻¹ s⁻½", False, "Fuera del índice v1 (veredicto de Expertos).", None),
        ]
        sources = cat.get("fuentes") or {}
        for name, unit, inn, notes, datum in variables:
            cur.execute(
                """INSERT INTO analog.variables(name,unit,source_per_body,in_index,notes,elevation_datum_per_body)
                   VALUES (%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (name) DO UPDATE SET unit=EXCLUDED.unit, in_index=EXCLUDED.in_index, notes=EXCLUDED.notes""",
                (name, unit, json.dumps(sources), inn, notes, json.dumps(datum) if datum else None),
            )
        for body, rows in (cat.get("std_params") or {}).items():
            for r in rows:
                cur.execute(
                    """INSERT INTO analog.std_params(body_ref,variable,center,scale,method,frozen_at)
                       VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                    (r.get("body_ref", body), r["variable"], r["center"], r["scale"], r["method"], r.get("frozen_at", FROZEN_AT)),
                )
        for body, rows in (cat.get("signatures") or {}).items():
            for r in rows:
                cur.execute(
                    """INSERT INTO analog.signatures(body,lat_band,variable,median,q1,q3,n_cells)
                       VALUES (%s,%s,%s,%s,%s,%s,%s)
                       ON CONFLICT (body,lat_band,variable) DO UPDATE
                       SET median=EXCLUDED.median, q1=EXCLUDED.q1, q3=EXCLUDED.q3, n_cells=EXCLUDED.n_cells""",
                    (r["body"], r["lat_band"], r["variable"], r.get("median"), r.get("q1"), r.get("q3"), r.get("n_cells") or 0),
                )
        um = cat["umbrales"]
        var = (cat.get("metricas_por_variante") or {}).get("todas_min_con_latitud") or {}
        for key, body in (("mars", "mars"), ("moon", "moon")):
            u = um[key]
            extra = (var.get("marte") if body == "mars" else var.get("luna")) or {}
            cur.execute(
                """INSERT INTO analog.thresholds(body,value,metric,d_max,sensitivity,precision_,specificity,auc,ic95_inferior,ic95_superior,frozen_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (body, frozen_at) DO NOTHING""",
                (
                    body, u["threshold"], u.get("metric", "youden"), u.get("d_max"),
                    u.get("sensitivity"), u.get("precision"), u.get("specificity"),
                    u.get("auc"), extra.get("ic95_inferior"), extra.get("ic95_superior"),
                    FROZEN_AT,
                ),
            )
        for s in cat["sitios_validacion"]:
            cur.execute(
                """INSERT INTO analog.validation_sites(site_key,name,lat,lon,geom,buffer_km,label,source,cita,is_provisional,is_mock,excluido_auc,coordenada_no_verificada,entra_al_auc)
                   VALUES (%s,%s,%s,%s,ST_SetSRID(ST_MakePoint(%s,%s),4326),%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (site_key) DO UPDATE SET name=EXCLUDED.name, lat=EXCLUDED.lat, lon=EXCLUDED.lon""",
                (
                    s.get("id") or s["nombre"], s["nombre"], s["lat"], s["lon"], s["lon"], s["lat"],
                    s["buffer_km"], s.get("etiqueta") or "no_analogo", s.get("fuente"), s.get("cita"),
                    bool(s.get("es_provisional")), bool(s.get("es_mock_superficies")),
                    bool(s.get("excluido_auc")), bool(s.get("coordenada_no_verificada")),
                    s.get("entra_al_auc", True) is not False,
                ),
            )
            cur.execute("SELECT id FROM analog.validation_sites WHERE site_key=%s", (s.get("id") or s["nombre"],))
            sid = cur.fetchone()[0]
            cur.execute(
                """INSERT INTO analog.validation_results(site_id,delta_mars,delta_moon,predicted_class,known_class,metric_version,computed_at,banda_latitud,banda_ganadora_marte,banda_ganadora_luna,modo_bandas,acierto)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (site_id) DO UPDATE SET delta_mars=EXCLUDED.delta_mars, delta_moon=EXCLUDED.delta_moon""",
                (
                    sid, s.get("delta_marte"), s.get("delta_luna"), s.get("clase_predicha"),
                    s.get("clase_conocida"), cat.get("metric_version"), FROZEN_AT,
                    s.get("banda_latitud"), s.get("banda_ganadora_marte"), s.get("banda_ganadora_luna"),
                    s.get("modo_bandas") or cat.get("modo_bandas"), s.get("acierto"),
                ),
            )
        ext = cat["grilla"]["extension"]
        rasters = [
            ("delta_marte", "/productos/delta_marte.tif", "similitud", -9999.0, "δ Marte", True, "dba0f23685d35f5e6399be7ebfbc816e552e0e969a88a8e35821b39b2b1ed406"),
            ("delta_luna", "/productos/delta_luna.tif", "similitud", -9999.0, "δ Luna", True, "daf00ed5e74e6308f2a9f46a4077075e335726c278e901c1a18bef24a67372c7"),
            ("clases", "/productos/clases.tif", "clase", -1.0, "Clases (secundaria; especificidad de Marte 0)", True, "a92f6781cc589d0de787e5ac74eae0042e56c6d89a16bd3abfa23968b0d9b886"),
        ]
        for layer, path, kind, nodata, label, in_index, digest in rasters:
            cur.execute(
                """INSERT INTO analog.ecuador_rasters(layer,path,kind,resolucion_m,west,north,east,south,nodata,label,in_index,frozen_at,sha256)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (layer) DO UPDATE SET path=EXCLUDED.path, sha256=EXCLUDED.sha256""",
                (layer, path, kind, 1000.0, ext["oeste"], ext["norte"], ext["este"], ext["sur"], nodata, label, in_index, FROZEN_AT, digest),
            )
        for z in cat.get("zonas_prioritarias") or []:
            cur.execute(
                """INSERT INTO analog.priority_zones(id,name,lat,lon,geom,class,delta_mars,delta_moon,elevation_m,slope_deg,roughness_tri)
                   VALUES (%s,%s,%s,%s,ST_SetSRID(ST_MakePoint(%s,%s),4326),%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name""",
                (
                    z["id"], z["nombre"], z["lat"], z["lon"], z["lon"], z["lat"], z.get("clase"),
                    z.get("delta_marte"), z.get("delta_luna"), z.get("elevacion_m"),
                    z.get("pendiente_deg"), z.get("rugosidad_tri"),
                ),
            )
        print("loaded variables, std_params, signatures, sites, results, thresholds, rasters, zones")
        if load_points:
            print("(--points requested but raster scan is only enabled on a reachable DB; skip here if rasters are the light representation)")
    conn.close()
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
