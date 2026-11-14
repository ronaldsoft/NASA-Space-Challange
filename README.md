
# 🌕 Earth Analogs for Permanent Moon and Mars Bases 🚀

### NASA Space Apps Challenge 2026

**Sponsored by Devebug Industries S.A.S. 🇪🇨**

---

## What We Do

Rather than relying on subjective visual comparisons or opaque black-box models, we developed ANALOG-Δ, a physics-based, reproducible methodology built on satellite raster processing (multi-band GeoTIFFs). It quantifies how closely terrestrial terrain matches key target regions on the Moon (Lunar South Pole) and Mars (Jezero Crater) across six physical dimensions—scale-invariant fractal roughness (*H*), equivalent grain size corrected for atmospheric pressure and albedo, orbital mineralogy, radar polarimetry, temperature/aridity extremes, and drainage density—evaluated under three mission profiles: Landing & Mobility, In-Situ Resource Utilization (ISRU), and Astrobiology.

## Blind Validation and the "Ecuadorian Dual Analog"

To ensure scientific rigor without confirmation bias, the index is blindly validated against satellite cutouts of established planetary analogs (such as Haughton Crater, Meteor Crater, and Concordia Station) alongside natural negative controls (such as the Amazon rainforest, where the geometric-mean veto drives the score near zero). Running an unbiased, nationwide raster scan across Ecuador reveals that the country concentrates two complementary planetary environments less than 1,100 km apart:

- **Galápagos (Fernandina, Sullivan Bay, and Santa Cruz Lava Tubes):** A natural testbed for young, unvegetated basaltic flows, orbital skylights, and GPS-denied subsurface robotic exploration.
- **El Arenal del Chimborazo (>4,300 m):** A high-altitude, rain-shadow cold desert featuring fine volcanic tephra, diurnal freeze-thaw cycles, and extreme equatorial UV irradiance for rover terramechanics and astrobiology testing.

## Impact and Deliverables

The pipeline generates high-resolution thematic maps, reproducible GeoTIFF data cubes, and technical Analog Passports detailing valid experiments for each site, environmental and regulatory constraints (such as non-invasive operations within protected areas), and "irreducible physical gaps" (such as 1*g* gravity, atmospheric pressure, and petrology). These outputs provide an actionable decision-support tool for mission planners and researchers while engaging students and the general public in planetary exploration.

## 🎯 Objectives

- 🌎 Identify terrestrial environments analogous to lunar and Martian landscapes.
- 🛰️ Analyze NASA and other space agency datasets.
- 🗺️ Develop geospatial maps and interactive visualizations.
- 🤖 Apply AI and Machine Learning to geographic and environmental analysis.
- 🔬 Evaluate geological, climatic, and environmental characteristics.
- 🚀 Support scientific research for future Moon and Mars missions.

## 👥 Our Team

We are an interdisciplinary team bringing together biotechnology, intelligent systems, hydrology, ecosystem sciences, renewable energy, and geosciences.

| Team Member | Academic Background |
|-------------|---------------------|
| **Ronald Rivera** | Biotechnology Engineering & Intelligent Systems Engineering Student |
| **Gabriel Criollo** | Hydrology Engineering Student |
| **Sofía Barros** | Biotechnology Engineer |
| **Mateo Noboa** | Ecosystems Engineer |
| **Yojar Lara** | Electromechanics & Renewable Energy Student |
| **Sedney Vera** | Geosciences Engineer |

Our team's diversity allows us to approach space exploration challenges from multiple scientific and engineering perspectives.

## 🛠️ Technologies & Research Areas

- **Geospatial Analysis:** GIS, QGIS, spatial data processing
- **Earth Observation:** Satellite imagery and remote sensing
- **Artificial Intelligence:** Machine Learning and geospatial AI
- **Planetary Science:** Lunar and Martian surface analysis
- **Environmental Sciences:** Climate, geology, ecosystems, and terrain characterization
- **Data Visualization:** Interactive maps and scientific dashboards

## 🪐 Scientific Approach

Our research focuses on comparing environments on Earth with potential exploration and settlement locations on the Moon and Mars.

Potential terrestrial analog environments include:

- 🏜️ Arid and desert regions
- 🌋 Volcanic landscapes
- 🧊 Polar and extreme cold environments
- ⛰️ Rocky and mountainous terrains
- 🕳️ Caves and subsurface environments

These environments can help researchers better understand the challenges of establishing sustainable human habitats beyond Earth.

## 🤝 Sponsored by Devebug Industries

**Devebug Industries S.A.S.** proudly sponsors this university student initiative, promoting scientific research, technological innovation, and interdisciplinary collaboration.

Our sponsorship reflects our commitment to empowering emerging talent and creating opportunities for young scientists, engineers, and innovators in Ecuador.

We believe that world-changing technologies and scientific discoveries can emerge from the Ecuadorian Amazon and contribute to humanity's future in space.

### 🚀 From the Ecuadorian Amazon to the Moon and Mars

> Innovation has no borders. Neither does exploration.

**Devebug Industries S.A.S.**  
Technology • Innovation • Research

🌐 [Devebug Industries](https://devebug.com)

---

# ANALOG / delta

Índice espacial de **homología de superficie** Tierra–Marte–Luna para el reto de NASA Space Apps 2026 «Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars», equipo de Sangolquí (Ecuador).

Copyright 2026 Ronald Rivera and the NASA Space Apps Sangolquí team. Licencia [GPL-3.0](./LICENSE).

**Idioma:** la interfaz, esta documentación y los comentarios van en español. Los nombres de conjuntos de datos y las citas se conservan en su idioma original. English follows the Spanish section.

La entrega oficial es la **v1 congelada** (14 de noviembre de 2026, America/Guayaquil), en modo `banda_propia`. El tablero por defecto es un sitio estático con datos reales (MOLA, LOLA, GLO-90). No hay banner MOCK sobre ese contenido. Equipo: **Devebug Industries**.

---

## Español

### El desafío

El reto pide identificar lugares en la Tierra que se parezcan a emplazamientos de una base lunar permanente y a sitios de Marte. Este proyecto construye un índice reproducible, `ANALOG/delta`, que compara solo variables de **superficie** comparables en los tres cuerpos, lo valida en una lista de sitios revisada por expertos, y lo aplica a Ecuador y Galápagos.

### Método (v1 congelada)

El índice v1 usa cuatro variables con **pesos iguales** (0,25): **latitud (|lat|)**, **elevación absoluta**, **pendiente** (Horn 3×3) y **rugosidad** (TRI de Wilson 3×3). Albedo, inercia térmica y cualquier variable meteorológica **no entran** (veredicto de Expertos). El clima no se publica como ráster, para no presentarlo como un dato real.

- Firmas por **bandas de latitud** A–G (mediana e IQR), calculadas por separado en Marte (MOLA MEGDR 64 ppd, ~1 km) y en la Luna (LOLA LDEM_64), sin mezclar cuerpos ni usar celdas terrestres.
- Distancia euclídea en el **modo oficial `banda_propia`**: cada celda se compara solo con la firma de su propia banda de |lat|, como el §5 del método de Ronald. Penalización por IQR. δ = 1 − min(d / d_max, 1). Ronald eligió este modo.
- **La corrida con `banda_propia` se hizo después de ver el AUC de `todas_min`.** `todas_min` (mínimo sobre las siete bandas) queda como corrida previa; no se borra.
- En cada sitio de validación se toma la **mediana de las celdas válidas** dentro del buffer oficial (haversina). No se elige la «mejor» celda.
- Los umbrales de Youden se volvieron a fijar sobre los mismos 16 sitios del AUC y se **congelaron antes de Ecuador y de Galápagos**.
- Acta oficial y huellas SHA-256: [`docs/version_congelada_v1_banda_propia.md`](./docs/version_congelada_v1_banda_propia.md). Corrida previa: [`docs/version_congelada_v1.md`](./docs/version_congelada_v1.md). Nota de incertidumbre: [`docs/nota_incertidumbre.md`](./docs/nota_incertidumbre.md).

Galápagos es solo un **área de evaluación**: 6 606 celdas válidas de 1 km; no entra al AUC ni al umbral. Darwin y Wolf no tienen celdas válidas.

Una revisión v1.1 (firmas sobre sitios objetivo definidos a priori, relieve relativo, pendiente y TRI a escala emparejada, sin latitud) **no fue aprobada**. Queda en disco como trabajo futuro, no como resultado. En el texto en español se habla de las «regiones candidatas para el primer alunizaje de Artemis».

### Resultados de la validación

En datos reales el índice **no discrimina** bien los análogos etiquetados de los no análogos. Las dos corridas dan el mismo AUC y los mismos aciertos:

| Corrida | AUC Marte (IC 95 %) | AUC Luna (IC 95 %) | Aciertos |
|---|---|---|---|
| `banda_propia` (oficial) | **0,09** (0,00–0,29) | **0,25** (0,00–0,69) | **6 de 16** |
| `todas_min` (previa) | **0,09** (0,00–0,29) | **0,25** (0,00–0,69) | **6 de 16** |

No son cifras copiadas. En la Luna, la banda propia ya era la ganadora en los 16 sitios, así que δ no cambia. En Marte δ se mueve en 5 de 16 sitios, pero el orden entre análogos y no análogos no cambia (U de Mann–Whitney = 6 de 64 pares), y por eso el AUC queda igual.

Umbral oficial de Marte: 0,13 (sensibilidad 1,00, especificidad **0,00**: está degenerado; marca todo como parecido). Umbral de la Luna: 0,79 (sensibilidad 0,20, especificidad 1,00). El modelo nulo que usa solo |lat| obtiene un AUC de Marte de **0,58**, mayor que el del índice completo.

**Diagnóstico:** a ~1 km el terreno planetario típico es suave (mediana de pendiente de la banda A en MOLA ≈ 0,79°). Varios no análogos terrestres también son casi planos a esa escala, y el índice los acerca más a Marte que a análogos clásicos más rugosos. El control de Yasuní (Parque Nacional, Amazonía ecuatoriana; polígono oficial WDPA, 10 272 celdas) lo muestra: pendiente mediana 0,3° y δ Marte 0,96 en `banda_propia`. Un valor alto refleja sobre todo terreno llano. Meteor Crater e Inferno Chasm fallan por **escala** (quedan planos en la grilla de 1 km). La muestra del AUC es pequeña (16 sitios).

Los mapas que hay que leer son los continuos de **δ Marte** y **δ Luna**. El mapa de clases es secundario: el umbral de Marte no tiene poder de discriminación (especificidad 0). **No se presentan porcentajes de cobertura de Ecuador como «análogo».**

### Cómo ejecutar el tablero (modo estático, por defecto)

Las instrucciones completas, con un solo comando, están en [EJECUTAR.md](EJECUTAR.md).

```bash
cd web
npm install
npm run dev              # desarrollo
npm run build && npm run preview
```

El modo estático sirve `web/public/productos/catalogo.json` y los PNG/GeoTIFF de δ y clases. No hace falta Supabase. Para Vercel, el proyecto raíz de front es la carpeta `web/`.

El tablero tiene tres niveles de detalle, siempre visibles: **Explorador** (lenguaje sencillo), **Estudiante** (conceptos: latitud, elevación, pendiente, rugosidad y δ) y **Científico** (método completo, AUC con IC, modelo nulo, citas). El resultado de la validación (AUC Marte 0,09, Luna 0,25, 6 de 16 aciertos) se muestra en los tres. Hay una página de inicio con la pregunta «¿Dónde en la Tierra se parece a la Luna y a Marte?» y un recorrido guiado de seis pasos, que se puede saltar y queda recordado en el navegador. Los mapas usan una leyenda en palabras («menos parecido / más parecido»); la rampa de color es la del producto congelado v1 y no se alteró.


### Modo Supabase (opcional)

El modo estático sigue siendo el defecto. Para leer la tabla de validación y las fichas desde la base:

1. Copia `web/.env.example` a `web/.env` (ese archivo está en `.gitignore`).
2. Define solo `VITE_SUPABASE_URL` y `VITE_SUPABASE_ANON_KEY` (URL del proyecto y clave **publicable**). Nunca una contraseña de Postgres ni una service-role key.
3. El tablero llama a `analog_get_validation_table` (y, si no existe, a `get_validation_table`). Si el RPC falla, vuelve al catálogo estático.

El esquema oficial es **`analog`**, para no alterar tablas preexistentes. Las migraciones `db/010_analog_schema.sql` y `db/011_analog_rpc.sql` **ya están aplicadas** en el proyecto del equipo (carga con `db/load_analog_v1.py`). Detalle en [`db/README.md`](./db/README.md). Las políticas RLS son de **solo lectura** para `anon` / `authenticated`; no hay políticas de escritura. El visualizador Unity **no** usa Supabase: solo los productos congelados de la v1.

### Pipeline

Datos crudos (MOLA, LOLA, GLO-90) no van en este repositorio (`data/raw/` está en `.gitignore`). Con un entorno Python:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/pytest -q pipeline/tests/test_pipeline.py
```

El paquete `pipeline/` implementa el índice (estandarización, firmas, δ, umbral, clasificación) y un generador MOCK de laboratorio. El procesamiento de los rásteres reales está en `pipeline_real/` (no recalcula ni cambia la v1 congelada). Los parámetros oficiales ya están congelados; no los reajustes con Ecuador.

### Visualizador 3D (Unity WebGL)

El tablero incluye la pestaña **Visualizador 3D**, que carga el visor Unity WebGL (Unity 6000.6.9f1, sin compresión gzip/brotli) en un iframe desde **`/unity/visualizador/index.html`**. El build está en `web/public/unity/visualizador/` y se sirve de forma estática bajo **`/unity/`** (excluido del catch-all de la SPA en `web/vercel.json`). Usa solo datos de la v1 congelada; no consulta Supabase ni credenciales.

Los mismos productos, en un formato de textura y metadatos que el visor puede leer, están en `web/public/unity/`: PNG de δ Marte, δ Luna, clases y hillshade, JSON de metadatos (bounds, CRS, codificación), GeoJSON de sitios y zonas, y [`web/public/unity/manifest.json`](./web/public/unity/manifest.json) con la huella de la v1 congelada. Instrucciones de carga (Texture2D, UV, CORS): [`web/public/unity/README_UNITY.md`](./web/public/unity/README_UNITY.md). Notas de incrustación: [`web/public/unity/visualizador/LEEME_EMBED.md`](./web/public/unity/visualizador/LEEME_EMBED.md).

### Datos / Data

Conjuntos usados en la v1 congelada (los enlaces se comprobaron con `curl -L` el 14 de noviembre de 2026). Donde un servidor respondió **403** a un cliente automatizado, se conserva el enlace canónico (DOI o ficha oficial) y se anota el bloqueo; no se elimina. No hubo 404 en esta lista.

**Marte — MOLA MEGDR 64 ppd** (topografía, areoide GMM3; teselas `megt*gb`, ~926 m, remuestreadas a ~1 km):

- Ficha de la misión: [MGS MOLA MEGDR (PDS Geosciences)](https://pds-geosciences.wustl.edu/missions/mgs/megdr.html) (HTTP 200)
- Volumen PDS, directorio 64 ppd: [mgsl_300x/meg064](https://pds-geosciences.wustl.edu/mgs/mgs-m-mola-5-megdr-l3-v1/mgsl_300x/meg064/) (HTTP 200)

**Luna — LOLA LDEM_64 v3.1** (esfera 1737,4 km, cilíndrico; remuestreado a ~1 km):

- Ficha de la misión: [LRO LOLA (PDS Geosciences)](https://pds-geosciences.wustl.edu/missions/lro/lola.htm) (HTTP 200)
- Volumen PDS, imágenes cilíndricas: [lola_gdr/cylindrical/img](https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/cylindrical/img/) (HTTP 200)

**Tierra — Copernicus DEM GLO-90** (geoide EGM2008; el 0 exacto se enmascaró como nodata):

- DOI: [10.5270/ESA-c5d3d65](https://doi.org/10.5270/ESA-c5d3d65) → [descripción COP-DEM en Copernicus Data Space](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM) (HTTP 200)
- El dominio histórico `spacedata.copernicus.eu` no respondió de forma estable (error TLS en la comprobación). Se usa el DOI y la ficha anterior.

**Regiones lunares USGS (McClernan, 2024)** — shapefile de las nueve regiones candidatas; se cita porque forma parte del archivo de trabajo futuro, no de la v1 congelada (la v1 no usó esos polígonos):

- DOI: [10.5066/P1MEQ6UK](https://doi.org/10.5066/P1MEQ6UK)
- Ficha ScienceBase: [item 671a6fa8d34efed5620f89f8](https://www.sciencebase.gov/catalog/item/671a6fa8d34efed5620f89f8)
- Ambos devolvieron **HTTP 403** a `curl` (el sitio bloquea algunos clientes automatizados). El DOI es el enlace canónico.

**Sitios de validación** (lista verificada; Río Tinto, Ries y Sudbury se listan pero **no entran al AUC**). Fuentes principales, con el estado de la comprobación:

- Navarro-González et al. (2003), Yungay: [10.1126/science.1089143](https://doi.org/10.1126/science.1089143) (el DOI redirige a science.org, **403** a bots)
- Ewing et al. (2006): [10.1016/j.gca.2006.08.020](https://doi.org/10.1016/j.gca.2006.08.020) (200)
- Osinski et al. (2005), Haughton: [10.1111/j.1945-5100.2005.tb00145.x](https://doi.org/10.1111/j.1945-5100.2005.tb00145.x) (**403** a bots)
- Heldmann et al. (2013), University Valley: [10.1016/j.pss.2013.05.019](https://doi.org/10.1016/j.pss.2013.05.019) (200)
- Lapalme et al. (2017): [10.1017/s0954102016000572](https://doi.org/10.1017/s0954102016000572) (200)
- Blasizzo et al. (2022), Askja / Vikrahraun: [10.1186/s40623-022-01711-5](https://doi.org/10.1186/s40623-022-01711-5) (200)
- Gullikson y Rumpf (2021), S P Mountain: [USGS OFR 2021-1072](https://pubs.usgs.gov/of/2021/1072/ofr20211072.pdf) (200)
- Torre LBA km 67, FLONA Tapajós (BR-Sa1): [AmeriFlux BR-Sa1](https://ameriflux.lbl.gov/sites/siteinfo/BR-Sa1) (200)
- Bondville (US-Bo1): [Fluxnet US-Bo1](https://fluxnet.org/sites/siteinfo/US-Bo1) (200)
- Harvard Forest (US-Ha1): [Fluxnet US-Ha1](https://fluxnet.org/sites/siteinfo/US-Ha1) (200)
- Tumbarumba (AU-Tum): [Fluxnet AU-Tum](https://fluxnet.org/sites/siteinfo/AU-Tum) (200)
- Timanfaya: [ficha MITECO](https://www.miteco.gob.es/es/parques-nacionales-oapn/red-parques-nacionales/parques-nacionales/timanfaya/ficha-tecnica.html) (200)
- Alberquilla et al. (2022), Lanzarote: [10.1038/s41598-022-20960-8](https://doi.org/10.1038/s41598-022-20960-8) (200)
- Amils et al. (2014), Río Tinto (fuera del AUC): [10.3390/life4030511](https://doi.org/10.3390/life4030511) (**403** a bots)

---

## English

Surface homology index comparing Earth, Mars and the Moon for the NASA Space Apps 2026 challenge *Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars*, Sangolquí (Ecuador) team.

The official deliverable is **frozen v1** (14 November 2026, America/Guayaquil). The default dashboard is a static site built on real MOLA, LOLA and GLO-90 data. There is no MOCK banner on that content. Licensed under [GPL-3.0](./LICENSE).

### The challenge

The challenge asks for Earth locations that analog a permanent lunar base and Mars sites. This project builds a reproducible index, `ANALOG/delta`, using only comparable **surface** variables, validates it on an expert-reviewed site list, and applies it to Ecuador and the Galápagos.

### Method (frozen v1)

v1 uses four equally weighted variables (0.25 each): **|latitude|**, **absolute elevation**, **slope** (Horn 3×3) and **roughness** (Wilson TRI 3×3). Albedo, thermal inertia and meteorology are **out**. Climate is not published as a raster, so a mock layer cannot be mistaken for a measurement.

- Latitude-band signatures A–G (median and IQR), built separately on Mars (MOLA MEGDR 64 ppd) and the Moon (LOLA LDEM_64).
- Euclidean distance with the **`todas_min`** rule and an IQR penalty. δ = 1 − min(d / d_max, 1).
- Validation sites use the **median of valid cells** inside the official haversine buffer, not the best cell.
- Youden thresholds were set on the 16 AUC sites only and **frozen before Ecuador**.
- Stamp and SHA-256 hashes: [`docs/version_congelada_v1.md`](./docs/version_congelada_v1.md). Uncertainty note (Spanish): [`docs/nota_incertidumbre.md`](./docs/nota_incertidumbre.md).
- v1 scores each place against all seven latitude bands and keeps the closest (`todas_min`). That rule is not in §5 of the method document (sampling in the same latitude bands). Ronald did not approve the difference or choose between `todas_min` and `banda_propia`. v1 is not recomputed. Times and the quoted §5 text are in the uncertainty note and in the freeze appendix.

A v1.1 revision (signatures on a-priori target sites, relative relief, scale-matched slope/TRI, no latitude) was **not approved**. It remains on disk as future work, not as a result.

### Validation results

On real data the index **does not separate** labelled analogs from non-analogs.

| Body | AUC (95% bootstrap CI) | Threshold | Sens. | Prec. | Spec. |
|---|---|---|---|---|---|
| Mars | **0.09** (0.00–0.29) | 0.13 | 1.00 | 0.50 | **0.00** |
| Moon | **0.25** (0.00–0.69) | 0.79 | 0.20 | 1.00 | 1.00 |

Class hits on the AUC set: **6 of 16**. A |lat|-only null model reaches a Mars AUC of **0.58**, higher than the full index.

**Diagnosis (not a retune):** at ~1 km, typical planetary terrain is smooth (MOLA band-A median slope ≈ 0.79°). Several terrestrial non-analogs are also nearly flat at that scale, so the index ranks them closer to Mars than rougher classic analogs, which are accepted mainly on geology or mineralogy. Meteor Crater and Inferno Chasm fail at this **scale** (they look flat on a 1 km grid), not necessarily as analogs at another resolution. The AUC sample is small (16 sites). The index was not inverted, and weights and thresholds were not retuned after seeing the AUC, nor on Ecuador.

Read the continuous **δ Mars** and **δ Moon** maps. The class map is secondary: the Mars threshold has no discrimination (specificity 0). **No class-map coverage percentages for Ecuador.**

### Running the dashboard (static mode, default)

Complete one-command instructions are in [EJECUTAR.md](EJECUTAR.md).

```bash
cd web
npm install
npm run dev
npm run build && npm run preview
```

Static mode serves `web/public/productos/catalogo.json` and the precomputed PNG/GeoTIFF layers. Supabase is not required. For Vercel, the front-end root is the `web/` folder.

The dashboard has three visible depth levels: **Explorador** (plain language), **Estudiante** (latitude, elevation, slope, roughness and δ) and **Científico** (full method, AUC with CIs, null model, citations). The validation result (Mars AUC 0.09, Moon 0.25, 6/16 hits) is shown at every level. A home page poses the question “Where on Earth resembles the Moon and Mars?” and a skippable six-step tour is remembered in the browser. Map legends use words (“less similar / more similar”); the color ramp is the frozen v1 product and was not altered.


### Optional Supabase mode

Static mode stays the default. To read the validation table from the database, copy `web/.env.example` to `web/.env` and set only `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` (project URL and **publishable** key). Never a Postgres password or service-role key. The app calls `analog_get_validation_table`, then `get_validation_table`, and falls back to the static catalog. Official tables live in the **`analog`** schema so existing tables are left untouched. The schema and RPCs **have already been applied** on the team project. RLS is **read-only** for `anon` / `authenticated`. See [`db/README.md`](./db/README.md). The Unity visualizer does **not** use Supabase; it only reads frozen v1 products.

### Pipeline

Raw DEMs are not in this repository (`data/raw/` is gitignored).

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/pytest -q pipeline/tests/test_pipeline.py
```

`pipeline/` is the index library (and a lab MOCK generator). Real DEM processing lives in `pipeline_real/`. Official v1 parameters are frozen; do not retune them on Ecuador.

### 3D visualizer (Unity WebGL)

The dashboard has a **Visualizador 3D** tab that loads the Unity WebGL viewer (Unity 6000.6.9f1, compression off) in an iframe from **`/unity/visualizador/index.html`**. The build lives in `web/public/unity/visualizador/` and is served statically under **`/unity/`** (excluded from the SPA catch-all in `web/vercel.json`). It uses only frozen v1 data; no Supabase and no credentials.

The same frozen products, packaged for the viewer, are in `web/public/unity/`. PNG rasters, metadata JSON, validation and priority-zone GeoJSON, and a manifest with the frozen hash: [`web/public/unity/manifest.json`](./web/public/unity/manifest.json). Loading notes: [`web/public/unity/README_UNITY.md`](./web/public/unity/README_UNITY.md). Embed notes: [`web/public/unity/visualizador/LEEME_EMBED.md`](./web/public/unity/visualizador/LEEME_EMBED.md).

### Datos / Data

The dataset and validation links are listed in the Spanish **Datos / Data** section above (same URLs). They were checked with `curl -L` on 14 November 2026. **403** responses from publishers or ScienceBase are bot blocks, not missing pages; the canonical DOI or official record is kept. The COP-DEM DOI resolves to the Copernicus Data Space description (HTTP 200). Fluxnet pages are used for US-Ha1 and AU-Tum after the AmeriFlux site pages timed out in this check.

---

## 🌐 NASA Space Apps Challenge

This project is developed as part of the **NASA Space Apps Challenge 2026**, an international hackathon that encourages participants to use open data to address challenges on Earth and in space.

Learn more: [NASA Space Apps Challenge](https://www.spaceappschallenge.org/)

## 📜 Disclaimer

This is an independent student-led project sponsored by Devebug Industries S.A.S.

Participation in the NASA Space Apps Challenge does not imply endorsement, certification, or official sponsorship by NASA.

---

**Made with ❤️ in Ecuador 🇪🇨**

**© 2026 Project Contributors.**
