"""Métricas de validación del modelo v2 (seco, reproducible, semilla fija).
Uso: python metricas_v2.py <hackaton/outputs> <dir_modelo_v2> <tabla_validacion.csv> <salida.json>
"""
import json, sys, math
import numpy as np, pandas as pd, rasterio
from scipy.stats import norm

H, M, TV, OUT = sys.argv[1:5]
rng = np.random.default_rng(20261115)
G = np.linspace(0, 1, 1001)
F = ["elevation_m", "slope_deg", "albedo"]
pts = pd.read_parquet(f"{H}/puntos_globales_100k_por_astro.parquet")
sites = pd.read_csv(f"{H}/firmas_misiones_5km.csv")
Q = {b: {f: np.quantile(pts.loc[pts.body == b, f].dropna(), G) for f in F} for b in ["earth", "mars", "moon"]}
qf = lambda b, f, x: np.interp(x, Q[b][f], G, left=0, right=1)

def firmas(body, excluir=None):
    s = sites[(sites.body == body) & ((sites.hydro_outcome == "alto") if body == "mars" else True)]
    if excluir is not None: s = s[s.mission != excluir]
    return s, np.stack([qf(body, f, s[f + "_median_5km"].to_numpy()) for f in F], 1).astype(np.float32)

def dist(x, R):
    d = np.full(len(x), np.inf, np.float32)
    for r in R: d = np.minimum(d, np.sqrt(((x - r) ** 2).sum(1)))
    return d

ep = pts[pts.body == "earth"].dropna(subset=F)
XB = np.stack([qf("earth", f, ep[f].to_numpy()) for f in F], 1).astype(np.float32)

def puntaje(x, body, excluir=None, vars_=(0, 1, 2)):
    _, R = firmas(body, excluir)
    v = list(vars_)
    bg = np.sort(dist(XB[:, v], R[:, v]))
    d = dist(x[:, v], R[:, v])
    return np.round(100 * (len(bg) - np.searchsorted(bg, d, side="left")) / len(bg))

def jacc(a, b):
    u = (a | b).sum(); return float((a & b).sum() / u) if u else 1.0

res = {"semilla": 20261115}
# ---------- Ecuador 1 km (artículo) : reproducción ----------
var = rasterio.open(f"{H}/articulo/recursos/geodatos/variables_ecuador_1km.tif").read().astype(np.float32)
sim = rasterio.open(f"{H}/articulo/recursos/geodatos/similitud_ecuador_1km.tif").read()
simv2 = rasterio.open(f"{M}/similitud_ecuador_1km_v2.tif").read()
ok = sim[0] != 255; ok2 = simv2[0] != 255
XE = np.stack([qf("earth", f, var[i][ok]) for i, f in enumerate(F)], 1).astype(np.float32)
rep = {}
for i, b in enumerate(["mars", "moon"]):
    p = puntaje(XE, b); rep[b] = {"coincidencia_exacta": float(np.mean(p == sim[i][ok])), "dif_max": float(np.abs(p - sim[i][ok]).max())}
res["reproduccion_ecuador_1km"] = rep
m2 = ok2[ok]  # celdas que sobreviven a la máscara NASA dentro del vector XE

# ---------- Jackknife de misiones y de variables (Jaccard del conjunto >=95) ----------
def jk(X, mask, etiqueta):
    out = {}
    for b in ["mars", "moon"]:
        full = puntaje(X, b)[mask] >= 95
        s, _ = firmas(b)
        mis = {}
        for m in s.mission:
            mis[m] = round(jacc(full, puntaje(X, b, excluir=m)[mask] >= 95), 3)
        vs = {}
        for k, nom in enumerate(F):
            keep = tuple(j for j in range(3) if j != k)
            vs["sin_" + nom] = round(jacc(full, puntaje(X, b, vars_=keep)[mask] >= 95), 3)
        vals = list(mis.values())
        out[b] = {"n_ge95": int(full.sum()), "misiones": mis, "misiones_min": min(vals), "misiones_mediana": float(np.median(vals)),
                  "variables": vs}
    return out
res["jackknife_ecuador_v2"] = jk(XE, m2, "ecuador")
# muestra global: 100k puntos terrestres (GMTED + MCD43C3, 1 km) que forman el fondo del modelo
res["jackknife_global_muestra100k"] = jk(XB, np.ones(len(XB), bool), "global")

# ---------- Validación con sitios análogos conocidos sobre el mapa global ----------
tv = pd.read_csv(TV)
g1 = rasterio.open(f"{H}/mapa_analogia_tierra_5km.tif").read()
g2 = rasterio.open(f"{M}/mapa_analogia_tierra_5km_v2.tif").read()

def valor(g, banda, lat, lon, rkm):
    rkm = max(rkm, 10.0)
    r0 = int((90 - lat) / 0.05); c0 = int((lon + 180) / 0.05)
    dr = int(math.ceil(rkm / 5.5597)); dc = int(math.ceil(rkm / (5.5597 * max(math.cos(math.radians(lat)), 0.05))))
    w = g[banda, max(0, r0 - dr):r0 + dr + 1, max(0, c0 - dc):c0 + dc + 1]
    w = w[w != 255]
    return float(np.median(w)) if w.size else np.nan

tv["banda"] = tv.clase_conocida.map({"marte": 0, "luna": 1, "ambos": 0, "ninguno": -1})
pos = tv[(tv.clase_conocida != "ninguno") & (tv.coordenada_no_verificada != "sí")].copy()
neg = tv[tv.clase_conocida == "ninguno"].copy()
for nom, g in (("v1", g1), ("v2", g2)):
    for df in (pos, neg):
        df[f"marte_{nom}"] = [valor(g, 0, a, o, r) for a, o, r in zip(df.latitud, df.longitud, df.buffer_km)]
        df[f"luna_{nom}"] = [valor(g, 1, a, o, r) for a, o, r in zip(df.latitud, df.longitud, df.buffer_km)]
    pos[f"propio_{nom}"] = np.where(pos.banda == 1, pos[f"luna_{nom}"], pos[f"marte_{nom}"])
    pos.loc[pos.clase_conocida == "ambos", f"propio_{nom}"] = pos.loc[pos.clase_conocida == "ambos", [f"marte_{nom}", f"luna_{nom}"]].max(1)

def auc(p, n):
    p = np.asarray(p); n = np.asarray(n)
    return float(((p[:, None] > n[None]).sum() + 0.5 * (p[:, None] == n[None]).sum()) / (len(p) * len(n)))

def hanley(a, n1, n2):
    q1 = a / (2 - a); q2 = 2 * a * a / (1 + a)
    se = math.sqrt((a * (1 - a) + (n1 - 1) * (q1 - a * a) + (n2 - 1) * (q2 - a * a)) / (n1 * n2))
    return [round(a - 1.96 * se, 3), round(a + 1.96 * se, 3)]

def boot(p, n, B=10000):
    p = np.asarray(p); n = np.asarray(n); v = []
    for _ in range(B):
        v.append(auc(rng.choice(p, len(p)), rng.choice(n, len(n))))
    return [round(float(np.quantile(v, .025)), 3), round(float(np.quantile(v, .975)), 3)]

aucs = {}
for nom in ("v1", "v2"):
    for cuerpo, sel, col in (("marte", pos.clase_conocida.isin(["marte", "ambos"]), "marte"), ("luna", pos.clase_conocida.isin(["luna", "ambos"]), "luna")):
        # sin dato (enmascarado o fuera de malla) = 0: el modelo no lo propone
        p = pos.loc[sel, f"{col}_{nom}"].fillna(0).to_numpy(); n = neg[f"{col}_{nom}"].fillna(0).to_numpy()
        a = auc(p, n)
        aucs[f"{cuerpo}_{nom}"] = {"auc": round(a, 3), "n_pos": int(len(p)), "n_neg": int(len(n)), "ic95_bootstrap": boot(p, n), "ic95_hanley_mcneil": hanley(a, len(p), len(n))}
res["auc_sitios_conocidos"] = aucs
res["sitios"] = pos[["sitio", "clase_conocida", "marte_v1", "luna_v1", "propio_v1", "marte_v2", "luna_v2", "propio_v2"]].round(1).replace({np.nan: None}).to_dict("records")
res["sitios_no_analogo"] = neg[["sitio", "marte_v1", "luna_v1", "marte_v2", "luna_v2"]].round(1).replace({np.nan: None}).to_dict("records")

# ---------- Recuperación frente a nulo de permutación espacial por bloques ----------
def nulo(g, umbrales=(90, 95, 97), N=2000, blk=10.0):
    elig = g[0] != 255
    rows, cols = np.nonzero(elig)
    lat = 90 - (rows + .5) * .05; lon = -180 + (cols + .5) * .05
    bid_lat = np.floor((lat + 90) / blk).astype(int); bid_lon = np.floor((lon + 180) / blk).astype(int)
    obs = pos.copy(); col = "propio_" + ("v2" if g is g2 else "v1")
    o = obs[col].fillna(0).to_numpy()
    resu = {}
    sims = {u: [] for u in umbrales}; simmed = []
    por_franja = {}
    for k, r in obs.iterrows():
        f = int(np.floor((r.latitud + 90) / blk))
        idx = np.nonzero(bid_lat == f)[0]
        if idx.size == 0: idx = np.arange(rows.size)
        por_franja[k] = idx
    for _ in range(N):
        vals = []
        for k, r in obs.iterrows():
            idx = por_franja[k]
            blks = np.unique(bid_lon[idx]); b = rng.choice(blks)
            cand = idx[bid_lon[idx] == b]; j = rng.choice(cand)
            la, lo = lat[j], lon[j]
            if r.clase_conocida == "ambos":
                v = np.nanmax([valor(g, 0, la, lo, r.buffer_km), valor(g, 1, la, lo, r.buffer_km)])
            else:
                v = valor(g, 1 if r.banda == 1 else 0, la, lo, r.buffer_km)
            vals.append(0 if np.isnan(v) else v)
        vals = np.array(vals)
        for u in umbrales: sims[u].append(int((vals >= u).sum()))
        simmed.append(float(np.median(vals)))
    for u in umbrales:
        ob = int((o >= u).sum()); s = np.array(sims[u])
        resu[f"umbral_{u}"] = {"recuperados": ob, "de": int(len(o)), "nulo_media": round(float(s.mean()), 2), "nulo_p95": float(np.quantile(s, .95)),
                               "p_valor": round(float((1 + (s >= ob).sum()) / (1 + N)), 4)}
    om = float(np.median(o)); sm = np.array(simmed)
    resu["mediana_percentil"] = {"observada": om, "nulo_media": round(float(sm.mean()), 1), "p_valor": round(float((1 + (sm >= om).sum()) / (1 + N)), 4)}
    resu["diseno"] = f"{N} permutaciones; cada sitio se reubica en una celda elegible al azar de un bloque {blk:.0f}°×{blk:.0f}° elegido al azar dentro de su misma franja de latitud de {blk:.0f}°; mismo radio y misma mediana de buffer (≥10 km) que el observado; celda sin dato = 0."
    return resu
res["recuperacion_nulo_bloques"] = {"v1": nulo(g1, N=1000), "v2": nulo(g2, N=1000)}

# ---------- Sensibilidad al umbral ----------
sens = {}
for u in (90, 95, 97):
    v = g2[0] != 255; ve = simv2[0] != 255
    sens[str(u)] = {
        "global_v2": {"marte": int((v & (g2[0] >= u)).sum()), "luna": int((v & (g2[1] >= u)).sum()), "conjunta_min": int((v & (np.minimum(g2[0], g2[1]) >= u)).sum()), "celdas": int(v.sum())},
        "ecuador_v2": {"marte": int((ve & (simv2[0] >= u)).sum()), "luna": int((ve & (simv2[1] >= u)).sum()), "conjunta_min": int((ve & (simv2[2] >= u)).sum()), "celdas": int(ve.sum())},
    }
for b, i in (("marte", 0), ("luna", 1)):
    a95 = (g2[i] != 255) & (g2[i] >= 95)
    sens[f"jaccard_global_{b}"] = {"90_vs_95": round(jacc((g2[i] != 255) & (g2[i] >= 90), a95), 3), "97_vs_95": round(jacc((g2[i] != 255) & (g2[i] >= 97), a95), 3)}
res["sensibilidad_umbral"] = sens
json.dump(res, open(OUT, "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ("sitios", "sitios_no_analogo")}, ensure_ascii=False, indent=1))
