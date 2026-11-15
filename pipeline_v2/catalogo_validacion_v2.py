"""Pasa a v2 las claves de validación que leen la cabecera y la UI (misma estructura de claves).
delta_* = percentil v2 / 100 (null si la celda está enmascarada o sin dato). Umbral = percentil 95.
Clase predicha: marte/luna/ambos/ninguno según percentil ≥95; un valor nulo cuenta como 0 (igual que en el AUC)."""
import json, sys, math
import numpy as np, rasterio
cat_p, met_p, ecu_p = sys.argv[1:4]
c = json.load(open(cat_p)); me = json.load(open(met_p))
U = 95.0
def pred(m, l):
    m = m or 0; l = l or 0
    return {(1, 1): "ambos", (1, 0): "marte", (0, 1): "luna", (0, 0): "ninguno"}[(m >= U, l >= U)]
v2 = {r["sitio"]: r for r in me["sitios"] + me["sitios_no_analogo"]}
pos_tp = {"marte": [0, 0], "luna": [0, 0]}  # [tp, n_pred]
for s in c["sitios_validacion"]:
    r = v2.get(s["nombre"])
    if r is None:  # Sudbury: fuera del AUC en v1 y v2
        s.update(delta_marte=None, delta_luna=None, clase_predicha="", acierto=False, excluido_auc=True, entra_al_auc=False)
        continue
    m, l = r["marte_v2"], r["luna_v2"]
    s["delta_marte"] = None if m is None else round(m / 100, 4)
    s["delta_luna"] = None if l is None else round(l / 100, 4)
    s["distancia_marte"] = None; s["distancia_luna"] = None
    s["clase_predicha"] = pred(m, l)
    s["acierto"] = s["clase_predicha"] == s["clase_conocida"]
    s["excluido_auc"] = False; s["entra_al_auc"] = True
    if m is None or l is None:
        s["nota_v2"] = "Sin valor v2 (máscara NASA MODIS IGBP o sin dato); en el AUC cuenta como 0."
    s["modo_bandas"] = "modelo_v2"
ex = [s for s in c["sitios_validacion"] if not s["excluido_auc"]]
ac = sum(s["acierto"] for s in ex)
def metr(body, key, auc_key):
    a = me["auc_sitios_conocidos"][auc_key]
    es_pos = lambda s: s["clase_conocida"] in (body, "ambos")
    pr = lambda s: s["clase_predicha"] in (body, "ambos")
    tp = sum(es_pos(s) and pr(s) for s in ex); fn = sum(es_pos(s) and not pr(s) for s in ex)
    fp = sum(not es_pos(s) and pr(s) for s in ex); tn = sum(not es_pos(s) and not pr(s) for s in ex)
    return {"threshold": U / 100, "sensitivity": round(tp / max(tp + fn, 1), 4), "precision": round(tp / (tp + fp), 4) if tp + fp else None,
            "specificity": round(tn / max(tn + fp, 1), 4), "auc": a["auc"], "agreement": round((tp + tn) / len(ex), 4),
            "metric": "percentil_95", "n_pos": a["n_pos"], "n_neg": a["n_neg"],
            "ic95_inferior": a["ic95_bootstrap"][0], "ic95_superior": a["ic95_bootstrap"][1]}
mm = metr("marte", "marte", "marte_v2"); ml = metr("luna", "luna", "luna_v2")
c["metricas_validacion"] = {"marte": {k: mm[k] for k in ("threshold", "sensitivity", "precision", "auc", "agreement")},
    "luna": {k: ml[k] for k in ("threshold", "sensitivity", "precision", "auc", "agreement")},
    "aciertos": ac, "aciertos_auc": ac, "n_sitios_auc": len(ex), "n_sitios": len(c["sitios_validacion"]),
    "ic95_marte": [mm["ic95_inferior"], mm["ic95_superior"]], "ic95_luna": [ml["ic95_inferior"], ml["ic95_superior"]],
    "version": "modelo_v2", "nota": "Umbral = percentil 95. AUC con 9 positivos de Marte o 6 de la Luna frente a 6 no análogos; en parte circular porque la máscara quita los no análogos."}
c["umbrales"] = {"mars": {**mm, "d_max": None}, "moon": {**ml, "d_max": None}}
# zonas prioritarias: valor de la celda v2 de 1 km; si está enmascarada, mediana de las celdas válidas a ≤3 km; si no hay, null
with rasterio.open(ecu_p) as r:
    A = r.read().astype(float); nd = r.nodata; T = r.transform
    if nd is not None: A[A == nd] = np.nan
    desc = r.descriptions
for z in c["zonas_prioritarias"]:
    col, row = ~T * (z["lon"], z["lat"]); row, col = int(row), int(col)
    vals = []
    for b in (0, 1):
        v = A[b, row, col]
        if np.isnan(v):
            w = A[b, max(row-3, 0):row+4, max(col-3, 0):col+4]; v = np.nanmedian(w) if np.isfinite(w).any() else np.nan
        vals.append(None if np.isnan(v) else float(v))
    m, l = vals
    z["delta_marte"] = None if m is None else round(m / 100, 4)
    z["delta_luna"] = None if l is None else round(l / 100, 4)
    z["clase"] = pred(m, l)
c["clases_ecuador_v2_nota"] = "Zonas: percentil v2 de la celda de 1 km (o mediana de celdas válidas a ≤3 km si está enmascarada)."
json.dump(c, open(cat_p, "w"), ensure_ascii=False, indent=2)
print("bandas", desc, "aciertos", ac, "de", len(ex)); print(json.dumps(c["metricas_validacion"], ensure_ascii=False))
for z in c["zonas_prioritarias"]: print(z["id"], z["delta_marte"], z["delta_luna"], z["clase"])
for s in c["sitios_validacion"]: print(s["id"], s["clase_conocida"], s["delta_marte"], s["delta_luna"], s["clase_predicha"], s["acierto"])
# Las cuatro zonas «Máxima similitud» se recolocan en el máximo v2 de su área (Galápagos: lon < -88).
if len(sys.argv) > 4:
    with rasterio.open(sys.argv[4]) as rv:
        V = rv.read().astype(float); VD = rv.descriptions; VT = rv.transform
    iel = [i for i, d in enumerate(VD) if d and "elev" in d.lower()][0]; isl = [i for i, d in enumerate(VD) if d and "pendiente" in d.lower()][0]
    H, W = A.shape[1:]
    lons = T.c + (np.arange(W) + 0.5) * T.a; lats = T.f + (np.arange(H) + 0.5) * T.e
    gal = np.broadcast_to(lons[None, :] < -88, (H, W))
    for z in c["zonas_prioritarias"]:
        if not z["id"].startswith("max_"): continue
        b = 0 if "_mars_" in z["id"] else 1
        sel = gal if z["area"] == "galapagos" else ~gal
        X = np.where(sel & np.isfinite(A[b]), A[b], -1); i, j = np.unravel_index(np.argmax(X), X.shape)
        la, lo = float(lats[i]), float(lons[j])
        cv, rv_ = ~VT * (lo, la); el = float(V[iel, int(rv_), int(cv)]); sl = float(V[isl, int(rv_), int(cv)])
        m, l = float(A[0, i, j]), float(A[1, i, j])
        z.update(lat=round(la, 4), lon=round(lo, 4), delta_marte=round(m / 100, 4), delta_luna=round(l / 100, 4), clase=pred(m, l),
                 elevacion_m=round(el, 1), pendiente_deg=round(sl, 2), rugosidad_tri=None, relieve_relativo_m=None)
        z["firma_superficie"] = {"latitud": round(la, 4), "elevacion_m": round(el, 1), "pendiente_deg": round(sl, 2), "rugosidad_tri": None}
        z["nota_v2"] = "Recolocada en el máximo del percentil v2 de su área; elevación GMTED2010 y pendiente del modelo v2."
        print("recolocada", z["id"], la, lo, m, l, z["clase"], el, sl)
    json.dump(c, open(cat_p, "w"), ensure_ascii=False, indent=2)
