# Metodología del modelo ANALOG v2 (15 nov 2026)

Documento técnico. Cifras de `data/processed/modelo_v2/` (`mascara_mcd12_resumen.json`, `metricas_v2.json`), generadas con `pipeline_v2/`. Semilla 20261115. El índice δ v1 (ver `docs/version_congelada_v1.md`) no se modificó.

## 1. Modelo

- Variables terrestres por celda: elevación (GMTED2010 mean 30"), pendiente y albedo de onda corta WSA (MODIS MCD43C3 v061, 13 sep 2026). Cada variable se lleva a su cuantil dentro de 100.000 puntos terrestres aleatorios (`puntos_globales_100k_por_astro.parquet`).
- Firmas planetarias: mediana en un vecindario de 9×9 puntos a 1 km (≈5 km) alrededor de 24 sitios de misión, llevada al cuantil dentro de 100.000 puntos del mismo cuerpo. Marte usa solo las 5 misiones con `hydro_outcome = alto` (Phoenix, Pathfinder, Perseverance, Opportunity, Curiosity); Luna usa las 14.
- Puntaje: distancia euclídea mínima del vector de la celda a las firmas del cuerpo; se convierte en percentil de supervivencia frente a las distancias de los 100.000 puntos terrestres (100 = más parecido que toda la muestra). Conjunta = mínimo de Marte y Luna.
- Escalas: global a 0,05° (7.200×3.600; `mapa_analogia_tierra_5km.tif`) y Ecuador a 1/120° (versión del artículo, `similitud_ecuador_1km.tif`). La reproducción independiente de Ecuador coincide en el 100 % de las celdas (diferencia máxima 0).
- Los percentiles no se reescalan tras la máscara: se conserva la referencia de 100.000 puntos.

## 2. Máscara NASA de cobertura (principal)

- Fuente: IGBP de MODIS MCD12Q1 v061, año 2022 (doi:10.5067/MODIS/MCD12Q1.061), leído de NASA GIBS (capa `MODIS_Combined_L3_IGBP_Land_Cover_Type_Annual`, matriz `500m`, paleta oficial `MODIS_IGBP_Land_Cover_Type.xml`, decodificación exacta de 18 colores).
- Global: nivel 6 de GIBS (0,00879°) agregado a la grilla de 0,05° como en MCD12C1 (doi:10.5067/MODIS/MCD12C1.061): fracción de bosque IGBP 1–5 y clase mayoritaria por celda.
- Reglas: fuera si bosque > 5 % o clase mayoritaria 1–5, con borde 3×3 (dilatación); fuera si la clase mayoritaria es 11 (humedal), 12 (cultivo), 13 (urbano) o 14 (mosaico de cultivo). Se suma a la máscara base del modelo (ESA CCI 2022, agua y borde).
- Ecuador: nivel 7 de GIBS (0,00439°, ~490 m) agregado a 1/120°; fuera la clase mayoritaria 1–5 y 11–14.
- El HDF de MCD12C1 no se descargó: el proceso no tuvo sesión de Earthdata. GIBS es la visualización oficial de MCD12Q1; MCD12C1 es la agregación de MCD12Q1 a 0,05°. Script listo: `pipeline_v2/mascara_mcd12.py` y `pipeline_v2/descargar_gibs_igbp.py`.

| Conjunto | Celdas | Marte ≥95 | Luna ≥95 | Conjunta ≥95 |
|---|---|---|---|---|
| Global, sin máscara NASA | 2.584.921 | 74.045 | 55.769 | 1.285 |
| Global, solo bosque (variante) | 2.493.627 | 63.146 | 52.864 | 1.249 |
| Global, bosque + cultivo/urbano/humedal (principal) | 2.197.719 | 44.693 | 38.387 | 1.144 |
| Ecuador 1 km, artículo | 10.193 | 709 | 241 | 0 (máx. 93) |
| Ecuador 1 km, con máscara NASA (principal) | 8.741 | 387 | 193 | 0 (máx. 93) |

Excluidas en global: 91.294 por bosque y 295.908 por uso. Sin dato IGBP: 85.160, todas al sur de 60°S (no se descargó la Antártida) y se conservan. En Ecuador salen 1318 celdas por uso (1105 por cultivo 12/14) y 134 por bosque IGBP. La conjunta global usa el mínimo de las bandas enteras; la bandera original del GeoTIFF (1.047) usa puntajes sin redondear.

## 3. Validación

### 3.1 AUC frente a sitios conocidos

Positivos: 12 sitios de `tabla_validacion.csv` (marcianos, lunares o ambos; se excluye Sudbury por coordenada no verificada). Negativos: 6 sitios de flujo en bosque o cultivo. Valor del sitio: mediana del percentil en un radio max(buffer, 10 km) sobre la grilla de 0,05°; celda enmascarada = 0.

- Marte (9 positivos): v1 sin máscara NASA 0,63 (IC 95 % bootstrap 0,296–0,944; Hanley-McNeil 0,339–0,92); v2 0,889 (IC 95 % bootstrap 0,722–1,0; Hanley-McNeil 0,718–1,0).
- Luna (6 positivos): v1 0,722 (IC 95 % bootstrap 0,361–1,0; Hanley-McNeil 0,423–1,0); v2 0,917 (IC 95 % bootstrap 0,75–1,0; Hanley-McNeil 0,741–1,0).
- El salto de AUC de v1 a v2 es en parte circular: los 6 negativos son bosques o cultivos y la máscara los elimina. No es evidencia de que el puntaje discrimine.

### 3.2 Recuperación frente a nulo de permutación espacial por bloques

1000 permutaciones; cada sitio se reubica en una celda elegible al azar de un bloque 10°×10° elegido al azar dentro de su misma franja de latitud de 10°; mismo radio y misma mediana de buffer (≥10 km) que el observado; celda sin dato = 0.

| Umbral | Recuperados v2 (de 12) | Media nula | p v2 | Recuperados v1 | p v1 |
|---|---|---|---|---|---|
| ≥90 | 1 | 1,08 | 0,6803 | 1 | 0,6783 |
| ≥95 | 1 | 0,33 | 0,2937 | 1 | 0,3117 |
| ≥97 | 1 | 0,15 | 0,1419 | 1 | 0,1139 |

Mediana del percentil de los 12 análogos: 17,5 (nulo 47,5; p = 0,985). Los análogos conocidos quedan por debajo de celdas tomadas al azar en su misma franja de latitud: el modelo no los recupera.

### 3.3 Jackknife (Jaccard del conjunto ≥95; criterio de estabilidad ≥0,95)

- Ecuador 1 km con máscara: quitar una misión → Marte 0,576–0,886 (mediana 0,653); Luna 0,777–1,0 (mediana 0,911). Quitar una variable → Marte 0,176, 0,21, 0,244; Luna 0,289, 0,151, 0,121 (elevación, pendiente, albedo).
- Muestra global de 100.000 puntos: quitar una misión → Marte 0,582–0,819 (mediana 0,655); Luna 0,817–0,997 (mediana 0,899). Quitar una variable → Marte 0,185, 0,228, 0,174; Luna 0,353, 0,183, 0,154 (elevación, pendiente, albedo).
- Ningún caso llega a 0,95. El conjunto ≥95 depende de qué misión entra (Phoenix pesa más en Marte) y de cada variable.

### 3.4 Sensibilidad del umbral

| Umbral | Global Marte | Global Luna | Global conjunta | Ecuador Marte | Ecuador Luna | Ecuador conjunta |
|---|---|---|---|---|---|---|
| ≥90 | 86.645 | 95.964 | 4.541 | 710 | 378 | 8 |
| ≥95 | 44.693 | 38.387 | 1.144 | 387 | 193 | 0 |
| ≥97 | 28.373 | 23.271 | 427 | 276 | 105 | 0 |

Jaccard global frente a ≥95: Marte 90 0,516, 97 0,635; Luna 90 0,4, 97 0,606.

## 4. Productos

- Teselas XYZ de 256 px en EPSG:3857, 5 clases (0–49, 50–74, 75–89, 90–94, 95–100), sin dato transparente: `web/public/productos/tiles/global/{marte,luna,conjunta}` z0–6; `global_sin_ecuador` z6 (Ecuador recortado con Natural Earth 10m admin-0); `ecuador` z5–9. El tablero cruza la opacidad entre zoom 5,5 y 6,5.
- GeoTIFF: `data/processed/modelo_v2/mapa_analogia_tierra_5km_v2.tif`, `similitud_ecuador_1km_v2.tif`, `igbp_cmg_2022_005.tif`, `igbp_ecuador_2022_1km.tif`.
- Supabase (`db/013_modelo_v2.sql`, esquema `analog`): `v2_reference_points` (300.000), `v2_mission_signatures` (24), `v2_terrestrial_stations` (29), `v2_candidates` (82.516: 81.936 global y 580 Ecuador), `v2_metrics` (10), `v2_layers` (9); RPC `analog_v2_*`.

## 5. Fuentes que no son NASA (limitación)

- **GMTED2010** (USGS/NGA; Danielson y Gesch, 2011, doi:10.3133/ofr20111073): elevación y pendiente terrestres del modelo v2. Sustituto NASA posible: SRTMGL30 V002 (doi:10.5067/MEaSUREs/SRTM/SRTMGL30.002) o NASADEM; no se recalculó.
- **ESA CCI Land Cover 2022 v2.1.1** (ESA/C3S, doi:10.24381/cds.006f2c9a): máscara base de bosque y agua del modelo original; la máscara NASA IGBP se suma, no la reemplaza.
- **Copernicus DEM GLO-90** (ESA, doi:10.5270/ESA-c5d3d65): solo en el índice δ v1, no en v2.
- Natural Earth 10m admin-0 (dominio público): solo para recortar Ecuador en las teselas z6.

## 6. Referencias verificadas (DOI resuelve, 15 nov 2026)

- Friedl, M., Sulla-Menashe, D. (2022). MCD12Q1 v061. NASA LP DAAC. doi:10.5067/MODIS/MCD12Q1.061
- Friedl, M., Sulla-Menashe, D. (2022). MCD12C1 v061. NASA LP DAAC. doi:10.5067/MODIS/MCD12C1.061
- Schaaf, C., Wang, Z. (2021). MCD43C3 v061. NASA LP DAAC. doi:10.5067/MODIS/MCD43C3.061
- Danielson, J. J., Gesch, D. B. (2011). Global Multi-resolution Terrain Elevation Data 2010 (GMTED2010). USGS OFR 2011-1073. doi:10.3133/ofr20111073
- Smith, D. E. et al. (2001). Mars Orbiter Laser Altimeter. JGR Planets 106(E10). doi:10.1029/2000JE001364
- Christensen, P. R. et al. (2001). Mars Global Surveyor Thermal Emission Spectrometer experiment. JGR 106(E10). doi:10.1029/2000JE001370
- Smith, D. E. et al. (2010). Initial observations from LOLA. GRL 37. doi:10.1029/2010GL043751
- Robinson, M. S. et al. (2010). LRO Camera (LROC) instrument overview. Space Sci. Rev. 150. doi:10.1007/s11214-010-9634-2
- Hanley, J. A., McNeil, B. J. (1982). The meaning and use of the area under a ROC curve. Radiology 143(1). doi:10.1148/radiology.143.1.7063747
- ESA/C3S. Land cover classification gridded maps from 1992 to present. doi:10.24381/cds.006f2c9a

NASA GIBS: https://gibs.earthdata.nasa.gov/ (WMTS sin inicio de sesión).
