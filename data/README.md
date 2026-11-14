# Datos de superficie a ~1 km — Marte, Luna y Tierra

Generado: 2026-11-14 13:37 UTC-05:00 (America/Guayaquil, UTC-5)

Este directorio reúne los datos **reales** de elevación (y las derivadas de pendiente y rugosidad) usados para el índice ANALOG/delta del reto NASA Space Apps *Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars*. El documento metodológico de referencia es `/workspace/proyecto_ronald.txt`.

## Qué entra al índice

Solo variables de superficie: **latitud, elevación, pendiente y rugosidad (TRI 3×3)**. Cero variables meteorológicas. Expertos confirmó que el **albedo y la inercia térmica no entran** al índice v1 (tampoco la abundancia de roca); no se descargaron. Se documenta su disponibilidad al final, por si el índice se ampliará en una versión posterior.

Pendiente y rugosidad se recalcularon **después** de remuestrear el DEM a ~1 km; no se interpolaron rásteres derivados de otra resolución.

## Grillas de ~1 km

Cada cuerpo tiene su propia celda equivalente a ~1 km en el ecuador (no se usa el mismo tamaño en grados, porque los radios son distintos). Todas las grillas están en coordenadas geográficas, origen en (−180°, 90°), longitudes este, rango de longitud [−180, 180].

| Cuerpo | Radio usado para la pendiente y el tamaño de celda | Celda (°) | Celda (m, ecuador) | Tamaño de la grilla |
|---|---|---|---|---|
| Tierra (WGS84, semieje mayor) | 6378137 m | 0.009 | 1001.88 | recortes regionales, no el globo |
| Marte (esfera del rótulo MEGDR) | 3396000 m | 0.016871309401068516 | 999.9858141897964 | 21338 × 10669 |
| Luna (esfera 1737.4 km) | 1737400 m | 0.03297911322828875 | 1000.0372070991035 | 10916 × 5458 |

Los tres productos globales de Marte y de la Luna se generaron a 1 km en el globo completo (no fue necesario recurrir a un producto más grueso ni al muestreo por bandas como único producto; el muestreo estratificado se entrega además, para las firmas).

## Marte — MOLA MEGDR

- **Producto:** MGS MOLA Mission Experiment Gridded Data Record, topografía (MEGT), 64 píxeles por grado (~926 m/píxel en el ecuador).
- **URL base:** https://pds-geosciences.wustl.edu/mgs/mgs-m-mola-5-megdr-l3-v1/mgsl_300x/meg064/
- **Archivos:** `megt90n000gb.img` / `.lbl`, `megt90n180gb.img` / `.lbl`, `megt00n000gb.img` / `.lbl`, `megt00n180gb.img` / `.lbl` (cuatro teselas de 90° × 180°, 16-bit big-endian, metros).
- **Datum horizontal:** IAU2000, planetocéntrico, longitudes positivas hacia el este. El rótulo declara un elipsoide/esfera de **3396.0 km**.
- **Datum vertical:** areoide MOLA derivado del modelo de potencial Goddard **GMM3 (mgm1025)** evaluado a grado y orden 50. La topografía es el radio planetario menos el radio del areoide.
- **No-dato:** el rótulo no declara un valor nulo; las celdas sin disparos van interpoladas. En los productos de 1 km se usa −9999 en los bordes polares de las derivadas (sin 8 vecinos).
- **Procesado:** mosaico a longitudes [−180, 180], remuestreo bilinear a la grilla de ~1 km, pendiente Horn y TRI de Wilson sobre ese DEM.

- **Estadísticos (1 km):** elevación {'min': -8194.7509765625, 'max': 21185.93359375, 'n': 227655122, 'mean': -720.5229723933029}; pendiente {'min': 0.0, 'max': 85.83189392089844, 'n': 227612446, 'mean': 1.5209176605175623}; TRI {'min': 0.0, 'max': 2388.824951171875, 'n': 227612446, 'mean': 17.775643989828218}.

## Luna — LOLA LDEM

- **Producto:** LRO LOLA Global Digital Elevation Model, `LDEM_64`, versión 3.1 (creación 2019-03-15).
- **URL:** https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/cylindrical/img/ldem_64.img
- **Rótulo:** https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/cylindrical/img/ldem_64.lbl
- **Formato nativo:** 23040 × 11520, 16-bit little-endian, **factor de escala 0.5** (HEIGHT = DN × 0.5 m), registro de píxel, 64 ppd (≈ 473.8 m/píxel en el ecuador).
- **Datum horizontal:** Mean Earth / Polar Axis de DE421, longitudes este.
- **Datum vertical:** esfera de **1737.4 km** (no el geoide lunar). El radio planetario es HEIGHT + 1 737 400 m.
- **Procesado:** igual que Marte (mosaico [−180, 180], remuestreo bilinear a ~1 km, Horn y TRI).

- **Estadísticos (1 km):** elevación {'min': -9100.2724609375, 'max': 10748.22265625, 'n': 59579528, 'mean': -519.4149205075945}; pendiente {'min': 0.0001350257807644084, 'max': 88.95797729492188, 'n': 59557696, 'mean': 6.149780886419784}; TRI {'min': 0.07916259765625, 'max': 1027.1783447265625, 'n': 59557696, 'mean': 71.71557677449444}.

## Tierra — Copernicus DEM GLO-90

- **Producto:** Copernicus DEM GLO-90 (COG de 3 arco-segundos) en AWS Open Data, **sin autenticación** (`s3://copernicus-dem-90m`).
- **Catálogo:** https://copernicus-dem-90m.s3.amazonaws.com/tileList.txt
- **Patrón:** `https://copernicus-dem-90m.s3.amazonaws.com/{TILE}/{TILE}.tif`
- **Teselas descargadas:** 116 (415.9 MB). Las teselas pedidas que no figuran en el catálogo corresponden sobre todo a océano (p. ej. el agua entre el Ecuador continental y Galápagos).
- **Cobertura:**
  - Ecuador continental y Galápagos, caja `lon -92.0…-75.0`, `lat -5.1…1.7`.
  - Ventanas de ~50 × 50 km (más un margen para la ventana 3×3) en cada sitio de validación provisional.
- **Datum horizontal:** EPSG:4326 (WGS84). **Datum vertical:** EGM2008.
- **No-dato:** GLO-90 no trae etiqueta `nodata`; el mar (y buena parte de las aguas) aparece como **0 exacto**. Se enmascara el 0. Limitación: una celda terrestre que midiera exactamente 0 m también queda fuera.
- **Latitudes altas:** a ~75°N/S las teselas GLO-90 vienen con menos columnas (p. ej. 400 en vez de 1200), es decir resolución más gruesa en longitud (~9"). Es un diseño del producto, no un error. Por eso se usó GLO-90 y no SRTM, que no cubre por encima de 60° (Devon Island, Svalbard, Islandia, valles secos antárticos).

- **Estadísticos Ecuador+Galápagos (1 km):** elevación {'min': -2.8543505668640137, 'max': 6018.81201171875, 'mean': 820.3034057617188, 'n': 460499}; pendiente {'min': 0.00012465960753615946, 'max': 33.05157470703125, 'mean': 3.1822874546051025, 'n': 453375}; TRI {'min': 0.008026123046875, 'max': 518.236328125, 'mean': 53.36087417602539, 'n': 453375}.

### Sitios de validación (lista provisional)

Sitios verificados por Expertos (`/workspace/validacion_parte1.md`). Se excluyen Río Tinto, Ries, Sudbury y los genéricos de Islandia y de los Valles Secos (fuera del AUC de superficie o sustituidos por un sitio más preciso).

| id | nombre | lat | lon | buffer (km) | etiqueta | clase | notas |
|---|---|---|---|---|---|---|---|
| `yungay` | Yungay / Atacama | -24.1 | -70.01 | 20 | marciano | positivo | Análogo marciano verificado. Fuente y citas en validacion_parte1.md. |
| `haughton` | Haughton / Devon Island | 75.3667 | -89.6833 | 12 | marciano | positivo | Cráter Haughton, Isla Devon. Análogo marciano verificado. |
| `university_valley` | University Valley / Valles Secos | -77.866 | 160.726 | 3 | marciano | positivo | University Valley (Antártida), no el genérico 'Dry Valleys'. Buffer 3 km. |
| `askja` | Askja / Vikrahraun | 65.06 | -16.64 | 6 | marciano | positivo | Coordenada confirmada: punto medio de la colada Vikrahraun (bocas 65.0647, -16.7247; frente 65.0590, -16.5454), archivo adicional 1 de Blasizzo et al. (2022), hoja (1.1) Samples. Se descarta 65.03, -16.78 (quedaba 4–5 km fuera de la colada). Radio 6 km. Permanece en el AUC. |
| `mauna_kea` | Mauna Kea (conos de cumbre) | 19.8291 | -155.4629 | 10 | ambos | positivo | Conos de la cumbre de Mauna Kea. Etiqueta: ambos (Marte y Luna). |
| `sverrefjell` | Sverrefjell / Svalbard | 79.4305 | 13.3072 | 5 | marciano | positivo | Sverrefjell, Svalbard. Análogo marciano. |
| `timanfaya` | Timanfaya / Lanzarote | 29.021 | -13.7744 | 8 | ambos | positivo | Parque Nacional de Timanfaya, Lanzarote. Etiqueta: ambos. |
| `meteor_crater` | Meteor Crater | 35.0275 | -111.0222 | 3 | lunar | positivo | Barringer Crater, Arizona. Análogo lunar de impacto. El cráter (~1.2 km) queda mal resuelto a 1 km. |
| `sp_mountain` | SP Mountain / Flagstaff | 35.5831 | -111.6336 | 8 | ambos | positivo | SP Mountain, cerca de Flagstaff, Arizona. Etiqueta: ambos. |
| `inferno_chasm` | Inferno Chasm / Idaho | 42.9667 | -113.1903 | 5 | lunar | positivo | Coordenada de un resumen LPSC, no de una revista revisada por pares. |
| `tapajos` | Tapajós BR-Sa1 | -2.8567 | -54.9589 | 10 | no_analogo | negativo | Sitio FLUXNET/AmeriFlux. No análogo. Teselas GLO-90 pueden faltar en algunos países. |
| `bondville` | Bondville US-Bo1 | 40.0062 | -88.2904 | 5 | no_analogo | negativo | Sitio FLUXNET/AmeriFlux. No análogo. |
| `harvard_forest` | Harvard Forest US-Ha1 | 42.5378 | -72.1715 | 5 | no_analogo | negativo | Sitio FLUXNET/AmeriFlux. No análogo. |
| `tumbarumba` | Tumbarumba AU-Tum | -35.6566 | 148.1517 | 5 | no_analogo | negativo | Sitio FLUXNET/AmeriFlux. No análogo. |
| `hainich` | Hainich DE-Hai | 51.0792 | 10.4522 | 5 | no_analogo | negativo | Sitio FLUXNET/AmeriFlux. No análogo. |
| `hyytiala` | Hyytiälä FI-Hyy | 61.8474 | 24.2948 | 5 | no_analogo | negativo | Sitio FLUXNET/AmeriFlux. No análogo. |

Los rásteres de cada ventana están en `processed/earth/validation/<id>/`.

## Derivadas (pendiente y TRI)

- **Pendiente:** método de Horn (3×3), en grados. Distancia horizontal = `R · π/180 · cos(latitud)` en X y `R · π/180` en Y, con el radio documentado de cada cuerpo (en los polos se limita |lat| a 89.9° para evitar dx → 0). En Marte y la Luna la longitud se envuelve (±180°).
- **Rugosidad:** TRI de Wilson et al. (2007), media de |z_vecino − z_centro| en los 8 vecinos, en metros. No usa distancia horizontal (es variabilidad de elevación). Se exige que los 8 vecinos sean válidos.

## Muestras estratificadas (firmas)

Además de los GeoTIFF globales, hay un muestreo por bandas de latitud oficiales (A–G, simétricas N/S; la banda G es obligatoria para el polo sur lunar, >~84°S), con hasta 4000 celdas por banda y hemisferio, en `processed/mars/mars_latband_samples.npz` y `processed/moon/moon_latband_samples.npz`. Marte y la Luna no se mezclan.

Bandas oficiales |lat| (se aplican a N y a S):

- `A`: 0.0–15.0 — Sin positivos terrestres; Ecuador cae aquí (evaluación, no validación).
- `B`: 15.0–30.0 — Mauna Kea, Timanfaya, Yungay.
- `C`: 30.0–45.0 — Meteor Crater, SP Mountain, Inferno Chasm; negativos Bondville, Harvard Forest, Tumbarumba.
- `D`: 45.0–60.0 — Banda débil (pocos positivos); negativo Hainich.
- `E`: 60.0–72.0 — Askja; negativo Hyytiälä.
- `F`: 72.0–80.0 — Haughton, University Valley, Sverrefjell.
- `G`: 80.0–90.0 — Obligatoria por diseño para el polo sur lunar (>~84°S). Ninguna estación terrestre cae aquí; el único análogo latitudinal sería la Antártida, y ni siquiera University Valley (~78°S).

## Estructura de archivos

```
data/
  README.md                  (este archivo)
  raw/
    mars/mola_megdr64/       IMG + LBL + mosaico nativo 64 ppd
    moon/lola_ldem64/        LDEM_64 IMG + LBL + mosaico en metros
    earth/copernicus_glo90/  teselas GLO-90
  processed/
    variables.json
    manifest.json
    processing_summary.json
    mars/  moon/             GeoTIFF ~1 km (elevación, pendiente, TRI, latitud, relieve relativo) + muestras .npz
    earth/ecuador_*_1km.tif  Ecuador + Galápagos
    earth/validation/<sitio>/
```

Los scripts reproducibles están en `/workspace/analogs/pipeline_real/` (`download_planetary.py`, `download_earth.py`, `process.py`, `write_docs.py`).

## Relieve relativo (capa extra, no entra aún al índice v1)

Además de la elevación absoluta, se calcula una capa de **relieve relativo**: la elevación de la celda menos la **mediana** de las elevaciones en una ventana de 15 × 15 celdas (≈ 15 km en el ecuador) sobre el DEM ya remuestreado a 1 km, en Marte, la Luna, Ecuador y cada ventana de validación. En los globos planetarios la ventana se envuelve en longitud. Hace falta al menos la mitad de vecinos válidos.

Esta capa está pendiente de decisión del equipo: podría sustituir a la elevación absoluta en el índice, porque los datums verticales de los tres cuerpos no son homologables al metro (areoide MOLA, esfera lunar de 1737.4 km, geoide EGM2008). Hasta que se decida, **no entra al índice v1**. Archivos: `*_relative_relief_1km.tif` y la columna `relative_relief_m` en las muestras `.npz` y en la tabla de validación.

## Limitaciones (para la nota de incertidumbre)

1. **La analogía es solo de superficie** y únicamente con las variables comparables. No se puede llamar «clima análogo» al índice.
2. **La resolución única de ~1 km suaviza el relieve local**, sobre todo en los Andes y en cráteres o conos de unos pocos kilómetros (p. ej. Meteor Crater tiene ~1.2 km de diámetro: en la grilla de 1 km queda mal resuelto).
3. **Marte a 64 ppd nativos (~926 m) se remuestrea ligeramente hacia ~1 km**; no se usó el MEGDR de 128 ppd (~463 m) para acotar tiempo y memoria. La diferencia de escala es pequeña frente al paso a 1 km.
4. **Luna: se parte de 474 m y se pierden dos factores de 2 al pasar a 1 km.** El LDEM de 128 ppd no se descargó (sería ~2 GB).
5. **Cobertura MOLA:** hay interpolación entre huellas (huecos de hasta ~12 km cerca del ecuador) y datos más pobres por encima de ~87° de latitud.
6. **LDEM 64:** posibles artefactos en los bordes de las bandas de 45° (advertencia del rótulo). Datum vertical = esfera, no geoide lunar.
7. **Los datums verticales no son el mismo tipo de superficie de referencia** (areoide MOLA, esfera lunar, geoide EGM2008). La elevación se compara como variable relativa / de relieve, no como cota absoluta homologable al metro.
8. **Tierra: 0 m exacto enmascarado**; costa y agua interior pueden perder celdas. GLO-90 es más grueso en longitud en latitudes altas.
9. **Askja** quedó con coordenada confirmada (65.060, −16.640; Blasizzo et al., 2022) y permanece en el AUC; se descartó 65.03, −16.78. **Inferno Chasm** usa una coordenada de resumen LPSC, no de revista. University Valley (3 km de buffer) y Meteor Crater (~1.2 km de diámetro) quedan muy suavizados a 1 km.
10. **Albedo e inercia térmica no entran al índice v1** (veredicto de Expertos; tampoco la abundancia de roca). No se descargaron.
11. **Pendiente y TRI en proyección equirrectangular cerca de los polos** son más inciertos: la celda de 1 km geográfico se estrecha mucho en metros de longitud (se aplica la corrección cos(lat), pero la forma de la celda no es un km×km). La banda G (80–90°) se muestreó igualmente porque es obligatoria para el polo sur lunar. El LDEM_64 cilíndrico sí cubre ambos polos; no fue necesario un producto polar estereográfico aparte.
12. No se entregó un ráster global terrestre: solo Ecuador/Galápagos y las ventanas de validación.

## Albedo e inercia térmica (fuera del índice; no se descargaron)

{
  "albedo": {
    "mars": {
      "producto": "TES Bolometric Albedo (global, ~8 ppd / ~7.5 km) o THEMIS/VIS",
      "url": "https://www.mars.asu.edu/data/tes_albedo/",
      "nota": "Disponible a escala global. Expertos: NO entra al índice v1. No se descarga."
    },
    "moon": {
      "producto": "LROC WAC Hapke o mosaico de albedo 643 nm",
      "url": "https://wms.lroc.asu.edu/lroc/view_rdr/WAC_HAPKE",
      "nota": "Disponible a 100 m–global. Expertos: NO entra al índice v1 (tampoco la abundancia de roca). No se descarga."
    },
    "earth": {
      "producto": "MODIS MCD43 albedo o Landsat",
      "url": "https://lpdaac.usgs.gov/products/mcd43a3v061/",
      "nota": "Disponible, pero la definición (banda, geometría, corrección) no es idéntica a TES/LROC."
    }
  },
  "thermal_inertia": {
    "mars": {
      "producto": "TES Thermal Inertia y/o THEMIS Thermal Inertia",
      "url": "https://www.mars.asu.edu/data/tes_inertia/",
      "nota": "Producto global clásico de Marte. Expertos: NO entra al índice v1 (tampoco la abundancia de roca). No se descarga."
    },
    "moon": {
      "producto": "Diviner rock abundance / thermal inertia (no es un mapa de TI equivalente en todo el globo de forma trivial)",
      "url": "https://pds-geosciences.wustl.edu/missions/lro/diviner.htm",
      "nota": "Disponible en productos derivados de Diviner. Expertos: NO entra al índice v1 (tampoco la abundancia de roca). No se descarga."
    },
    "earth": {
      "producto": "No hay un producto global de inercia térmica homologable a TES/Diviner de acceso abierto y resolución comparable.",
      "url": null,
      "nota": "Es la capa más difícil de homologar en los tres cuerpos."
    }
  }
}

## Cómo reproducir

```bash
cd /workspace/analogs/pipeline_real
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python download_planetary.py
.venv/bin/python download_earth.py
.venv/bin/python process.py
.venv/bin/python write_docs.py
```

