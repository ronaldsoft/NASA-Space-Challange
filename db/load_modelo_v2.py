"""Genera los INSERT por lotes de la migración 013_modelo_v2 (idempotentes: ON CONFLICT DO NOTHING/UPDATE).
Uso: python db/load_modelo_v2.py <hackaton/outputs> <data/processed/modelo_v2> <tiles/teselas.json> <dir_sql_salida>
Los lotes se aplican con psql (-f) o, si el puerto 5432 no es accesible, con el execute_sql del MCP de Supabase.
"""
import json, math, os, sys
import numpy as np, pandas as pd, rasterio

H, M, TJ, OUT = sys.argv[1:5]
os.makedirs(OUT, exist_ok=True)
G = np.linspace(0, 1, 1001); F = ["elevation_m", "slope_deg", "albedo"]
pts = pd.read_parquet(f"{H}/puntos_globales_100k_por_astro.parquet")
sites = pd.read_csv(f"{H}/firmas_misiones_5km.csv")
Q = {b: {f: np.quantile(pts.loc[pts.body == b, f].dropna(), G) for f in F} for b in ["earth", "mars", "moon"]}
qf = lambda b, f, x: np.interp(x, Q[b][f], G, left=0, right=1)

def lit(v):
    if v is None: return "NULL"
    if isinstance(v, (bool, np.bool_)): return "true" if v else "false"
    if isinstance(v, (int, np.integer)): return str(int(v))
    if isinstance(v, (float, np.floating)):
        return "NULL" if not math.isfinite(float(v)) else repr(round(float(v), 6))
    return "'" + str(v).replace("'", "''") + "'"

def escribir(nombre, tabla, cols, filas, conflicto, lote=6000):
    n = 0
    for i in range(0, len(filas), lote):
        vals = ",\n".join("(" + ",".join(lit(x) for x in f) + ")" for f in filas[i:i + lote])
        open(f"{OUT}/{nombre}_{i // lote:03d}.sql", "w").write(
            f"INSERT INTO analog.{tabla} ({','.join(cols)}) VALUES\n{vals}\n{conflicto};\n"); n += 1
    return n

# --- modelo (igual que pipeline_v2/metricas_v2.py) ---
def firmas(body):
    s = sites[(sites.body == body) & ((sites.hydro_outcome == "alto") if body == "mars" else True)]
    return np.stack([qf(body, f, s[f + "_median_5km"].to_numpy()) for f in F], 1).astype(np.float32)
def dist(x, R):
    d = np.full(len(x), np.inf, np.float32)
    for r in R: d = np.minimum(d, np.sqrt(((x - r) ** 2).sum(1)))
    return d
ep = pts[pts.body == "earth"]
ok3 = ep[F].notna().all(axis=1).to_numpy()
XB = np.stack([qf("earth", f, ep[f].to_numpy()) for f in F], 1).astype(np.float32)
pct = {}
for b in ["mars", "moon"]:
    R = firmas(b); bg = np.sort(dist(XB[ok3], R)); d = dist(XB, R)
    p = np.round(100 * (len(bg) - np.searchsorted(bg, d, side="left")) / len(bg))
    p[~ok3] = np.nan; pct[b] = p
igbp = rasterio.open(f"{M}/igbp_cmg_2022_005.tif"); fb, may = igbp.read(1), igbp.read(2)
r_ = np.clip(((90 - ep.latitude.to_numpy()) / 0.05).astype(int), 0, 3599); c_ = np.clip(((ep.longitude.to_numpy() + 180) / 0.05).astype(int), 0, 7199)
cls = may[r_, c_]; frac = fb[r_, c_]
eleg = (cls != 255) & ~((frac > 5) | ((cls >= 1) & (cls <= 5))) & ~np.isin(cls, [11, 12, 13, 14]) & ok3

filas = []
for body in ["earth", "mars", "moon"]:
    sub = pts[pts.body == body]
    q = {f: qf(body, f, sub[f].to_numpy()) for f in F}
    for k, r in enumerate(sub.itertuples()):
        e = body == "earth"
        filas.append((body, r.point_id, r.latitude, r.longitude, r.elevation_m, r.slope_deg, r.albedo,
                      q["elevation_m"][k] if pd.notna(r.elevation_m) else None, q["slope_deg"][k] if pd.notna(r.slope_deg) else None,
                      q["albedo"][k] if pd.notna(r.albedo) else None,
                      (None if not e or np.isnan(pct["mars"][k]) else int(pct["mars"][k])),
                      (None if not e or np.isnan(pct["moon"][k]) else int(pct["moon"][k])),
                      (int(cls[k]) if e and cls[k] != 255 else None), (bool(eleg[k]) if e else None),
                      r.elevation_source, r.albedo_source))
res = {"v2_reference_points": len(filas)}
lotes = {"puntos": escribir("10_puntos", "v2_reference_points", ["body","point_id","lat","lon","elevation_m","slope_deg","albedo","q_elevation","q_slope","q_albedo","pct_marte","pct_luna","igbp_clase","elegible_v2","elevation_source","albedo_source"], filas, "ON CONFLICT (body, point_id) DO NOTHING")}

cm = pd.read_csv(f"{H}/catalogo_misiones_articulo.csv")
fm = []
for r in cm.itertuples():
    usada = (r.hydro_outcome == "alto") if r.body == "mars" else True
    fm.append((r.body, r.mission, r.latitude, r.longitude, r.hydro_outcome, r.traverse_km, usada, r.elevation_m_median_5km, r.slope_deg_median_5km,
               r.albedo_median_5km, qf(r.body, "elevation_m", r.elevation_m_median_5km), qf(r.body, "slope_deg", r.slope_deg_median_5km),
               qf(r.body, "albedo", r.albedo_median_5km), getattr(r, "period", None), getattr(r, "principal_result", None), getattr(r, "terrain_type", None), r.source_url))
res["v2_mission_signatures"] = len(fm)
lotes["misiones"] = escribir("20_misiones", "v2_mission_signatures", ["body","mission","lat","lon","hydro_outcome","traverse_km","usada_en_modelo","elevation_m_median_5km","slope_deg_median_5km","albedo_median_5km","q_elevation","q_slope","q_albedo","periodo","resultado","terreno","source_url"], fm, "ON CONFLICT (body, mission) DO NOTHING")

me = json.load(open(f"{M}/metricas_v2.json")); mk = json.load(open(f"{M}/mascara_mcd12_resumen.json"))
st = []
eo = pd.read_csv(f"{H}/revision/estaciones_originales.csv")
for r in eo.itertuples():
    st.append((f"orig_{r.id}", "estacion_original", r.station, r.latitude, r.longitude, None, None, None, json.dumps({k: (None if pd.isna(v) else v) for k, v in r._asdict().items() if k != "Index"}, ensure_ascii=False, default=float)))
et = pd.read_csv(f"{H}/estaciones_terrestres_articulo.csv")
for i, r in enumerate(et.itertuples()):
    st.append((f"inst_{i+1}", "instalacion", r.name, None, None, r.relevance, None, None, json.dumps({"ubicacion": r.location, "funcion": r.function, "estado": r.verified_status, "fuente": r.source_url}, ensure_ascii=False)))
tv = pd.read_csv("web/public/productos/tabla_validacion.csv")
v2s = {s["sitio"]: s for s in me["sitios"]}; v2n = {s["sitio"]: s for s in me["sitios_no_analogo"]}
for i, r in enumerate(tv.itertuples()):
    s = v2s.get(r.sitio) or v2n.get(r.sitio) or {}
    st.append((f"val_{i+1:02d}", "sitio_validacion", r.sitio, r.latitud, r.longitud, r.etiqueta_conocida, s.get("marte_v2"), s.get("luna_v2"),
               json.dumps({"buffer_km": r.buffer_km, "cita": r.cita, "entra_al_auc_v1": r.entra_al_auc, "coordenada_no_verificada": r.coordenada_no_verificada, "marte_v1": s.get("marte_v1"), "luna_v1": s.get("luna_v1")}, ensure_ascii=False)))
res["v2_terrestrial_stations"] = len(st)
lotes["estaciones"] = escribir("30_estaciones", "v2_terrestrial_stations", ["station_key","kind","name","lat","lon","etiqueta","pct_marte_v2","pct_luna_v2","info"], st,
  "ON CONFLICT (station_key) DO UPDATE SET pct_marte_v2 = EXCLUDED.pct_marte_v2, pct_luna_v2 = EXCLUDED.pct_luna_v2, info = EXCLUDED.info")

cand = []
g = rasterio.open(f"{M}/mapa_analogia_tierra_5km_v2.tif").read()
rr, cc = np.nonzero((g[0] != 255) & (np.maximum(g[0], g[1]) >= 95))
for a, b in zip(rr, cc):
    cand.append(("global", int(a) * 7200 + int(b), round(90 - (a + .5) * .05, 4), round(-180 + (b + .5) * .05, 4), int(g[0, a, b]), int(g[1, a, b]), int(g[2, a, b]), int(may[a, b]) if may[a, b] != 255 else None))
ed = rasterio.open(f"{M}/similitud_ecuador_1km_v2.tif"); e = ed.read(); t = ed.transform
ie = rasterio.open(f"{M}/igbp_ecuador_2022_1km.tif").read(1)
rr, cc = np.nonzero((e[0] != 255) & (np.maximum(e[0], e[1]) >= 95))
for a, b in zip(rr, cc):
    cand.append(("ecuador", int(a) * ed.width + int(b), round(t.f + (a + .5) * t.e, 5), round(t.c + (b + .5) * t.a, 5), int(e[0, a, b]), int(e[1, a, b]), int(e[2, a, b]), int(ie[a, b]) if ie[a, b] != 255 else None))
res["v2_candidates"] = len(cand); res["v2_candidates_ecuador"] = sum(1 for c in cand if c[0] == "ecuador")
lotes["candidatos"] = escribir("40_candidatos", "v2_candidates", ["scope","cell_id","lat","lon","pct_marte","pct_luna","pct_conjunta","igbp_clase"], cand, "ON CONFLICT (scope, cell_id) DO NOTHING", lote=8000)

mets = [(k, json.dumps(v, ensure_ascii=False)) for k, v in me.items()] + [("mascara_nasa_igbp", json.dumps(mk, ensure_ascii=False))]
res["v2_metrics"] = len(mets)
lotes["metricas"] = escribir("50_metricas", "v2_metrics", ["key","value"], mets, "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now()")

tl = json.load(open(TJ)); lay = []
zr = {"global": (0, 6), "global_sin_ecuador": (6, 6), "ecuador": (5, 9)}
for f, (z0, z1) in zr.items():
    for b in ["marte", "luna", "conjunta"]:
        lay.append((f"{f}/{b}", f, b, f"/productos/tiles/{f}/{b}/{{z}}/{{x}}/{{y}}.png", 256, z0, z1, tl["teselas"].get(f"{f}/{b}"), json.dumps(tl["clases"], ensure_ascii=False), json.dumps(tl["rgba"]),
                    "Cruce de opacidad z5,5–6,5: global al alejarse; Ecuador (y global sin Ecuador) al acercarse."))
res["v2_layers"] = len(lay)
lotes["capas"] = escribir("60_capas", "v2_layers", ["layer_id","fuente","banda","url_template","tile_size","minzoom","maxzoom","n_teselas","clases","rgba","notas"], lay,
  "ON CONFLICT (layer_id) DO UPDATE SET n_teselas = EXCLUDED.n_teselas, clases = EXCLUDED.clases, rgba = EXCLUDED.rgba, notas = EXCLUDED.notas")
json.dump({"filas": res, "lotes": lotes}, open(f"{OUT}/resumen.json", "w"), indent=1)
print(json.dumps({"filas": res, "lotes": lotes}, indent=1))
