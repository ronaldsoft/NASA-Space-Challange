"""Actualiza web/public/productos/catalogo.json para el modelo v2 sin quitar claves (los campos
numéricos de δ v1 se conservan porque la tabla de validación y los puntos aún los usan)."""
import json, sys
cat_p, mask_p, met_p, tiles_p = sys.argv[1:5]
c = json.load(open(cat_p)); mk = json.load(open(mask_p)); me = json.load(open(met_p)); tl = json.load(open(tiles_p))
def n(x): return f"{x:,}".replace(",", ".")
g = mk["global"]["principal_bosque_y_uso"]; e = mk["ecuador"]["principal_bosque_y_uso"]
c["metric_version"] = "ANALOG v2 (percentil frente a firmas de misiones, máscara NASA MODIS IGBP) 2026-11-15"
c["aviso"] = (f"Modelo v2: percentil de similitud de cada celda terrestre con las firmas de misiones (elevación, pendiente y albedo). "
  f"Global a 0,05° con {n(g['celdas'])} celdas tras la máscara NASA MODIS IGBP (bosque, cultivos, urbano y humedal fuera): "
  f"{n(g['marte_ge95'])} celdas ≥95 para Marte, {n(g['luna_ge95'])} para la Luna y {n(g['conjunta_ge95_min'])} conjuntas. "
  f"Ecuador a 1 km (artículo) con {n(e['celdas'])} celdas: {e['marte_ge95']} ≥95 Marte, {e['luna_ge95']} Luna y {e['conjunta_ge95']} conjuntas. "
  "Elevación terrestre GMTED2010 (USGS, no NASA) y máscara base ESA CCI (no NASA): limitación declarada.")
c["capas"] = {**c.get("capas", {}),
  "modelo_v2": {"tipo": "xyz", "tile_size": 256, "crs": "EPSG:3857",
    "global": "/productos/tiles/global/{banda}/{z}/{x}/{y}.png", "global_zoom": [0, 6],
    "global_sin_ecuador": "/productos/tiles/global_sin_ecuador/{banda}/{z}/{x}/{y}.png", "global_sin_ecuador_zoom": [6, 6],
    "ecuador": "/productos/tiles/ecuador/{banda}/{z}/{x}/{y}.png", "ecuador_zoom": [5, 9],
    "bandas": ["marte", "luna", "conjunta"], "clases": tl["clases"], "rgba": tl["rgba"], "cruce_opacidad_zoom": [5.5, 6.5]}}
c["fuentes"] = {**c["fuentes"],
  "earth_v2_elevacion": "GMTED2010 mean 30\" (USGS/NGA, no NASA) — limitación",
  "earth_v2_albedo": "MODIS MCD43C3 v061 albedo WSA onda corta (NASA LP DAAC)",
  "earth_v2_mascara": "MODIS MCD12Q1 v061 IGBP 2022 vía NASA GIBS (MODIS_Combined_L3_IGBP_Land_Cover_Type_Annual), agregado a 0,05° como MCD12C1",
  "earth_v2_mascara_base": "ESA CCI Land Cover 2022 v2.1.1 300 m (ESA, no NASA) — limitación",
  "mars_v2": "MGS MOLA MEGDR y TES albedo (NASA PDS)", "moon_v2": "LRO LOLA LDEM_64 y LROC WAC (NASA PDS)"}
lim = [l for l in c.get("limitaciones", [])]
lim += ["v2: la elevación terrestre es GMTED2010 (USGS/NGA) y la máscara base es ESA CCI 2022; ninguna es NASA. Copernicus GLO-90 (ESA) solo queda en el índice δ v1.",
        f"v2: el AUC alto frente a los 6 sitios no análogos es en parte circular: esos sitios son bosques o cultivos y la máscara los elimina. Solo {me['recuperacion_nulo_bloques']['v2']['umbral_95']['recuperados']} de {me['recuperacion_nulo_bloques']['v2']['umbral_95']['de']} análogos conocidos quedan ≥95 (p = {me['recuperacion_nulo_bloques']['v2']['umbral_95']['p_valor']} frente al nulo por bloques).",
        f"v2: el conjunto ≥95 no es estable: Jaccard mínimo al quitar una misión {me['jackknife_ecuador_v2']['mars']['misiones_min']} (Marte) y {me['jackknife_ecuador_v2']['moon']['misiones_min']} (Luna) en Ecuador; al quitar una variable cae a 0,12–0,29.",
        "v2: la máscara IGBP se tomó de las teselas de NASA GIBS (visualización de MCD12Q1); el HDF de MCD12C1 no se descargó en esta corrida."]
c["limitaciones"] = lim
c["nota_de_incertidumbre"] = ("Modelo v2: percentiles empíricos frente a 100.000 puntos terrestres; no son probabilidades de éxito ni de habitabilidad. "
  "La recuperación de análogos conocidos no supera al azar espacial y el conjunto ≥95 cambia al quitar una misión o una variable. Úsalo como mapa de pistas.")
c["modelo_v2"] = {"mascara": mk, "metricas": me, "teselas": tl["teselas"],
  "metodologia": "docs/metodologia_v2.md", "generado": "2026-11-15"}
json.dump(c, open(cat_p, "w"), ensure_ascii=False, indent=2)
print("ok", len(c))
