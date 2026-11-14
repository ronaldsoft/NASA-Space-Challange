# Celdas válidas por isla (Galápagos)

Fecha: 14 de noviembre de 2026 (America/Guayaquil, UTC-5). Equipo: Devebug Industries.

Se cuenta una celda de 1 km si su **centro** cae dentro del polígono de la isla (`all_touched = False`) y la celda es válida en la máscara oficial de pendiente / TRI / δ de la v1 `banda_propia`.

**Fuente del polígono:** GADM versión 4.1, capa `gadm41_ECU_1.shp`, provincia Galápagos, 53 partes explotadas y nombradas por el centro oficial de cada isla. Global Administrative Areas (GADM), 18 July 2022, University of California, Davis. https://gadm.org/ — archivo: https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_ECU_shp.zip.

GADM permite uso académico y no comercial y **no se redistribuye el shapefile**. En el repositorio solo van las cifras derivadas (`data/processed/galapagos/celdas_por_isla.json` y `web/public/productos/galapagos/celdas_por_isla.json`).

Darwin y Wolf están en la grilla y en GADM, pero **no tienen celdas válidas a 1 km** (islas demasiado pequeñas tras el remuestreo y la máscara de vecinos). El recorte publicado de Galápagos (−91,800 a −89,118, −1,548 a 0,783) no alcanza esas dos islas; como no aportan celdas válidas, el total del recorte sigue siendo **6 606**.

Galápagos **no entra al AUC ni al umbral**.

| Isla | Celdas válidas (1 km) | Mediana δ Marte | Mediana δ Luna | Mediana pendiente (°) |
|---|---:|---:|---:|---:|
| Isabela | 4 128 | 0,8761 | 0,7460 | 2,90 |
| Santa Cruz | 839 | 0,9466 | 0,7912 | 1,83 |
| Fernandina | 527 | 0,7642 | 0,7557 | 4,42 |
| Santiago | 451 | 0,9163 | 0,7812 | 2,36 |
| San Cristóbal | 414 | 0,9161 | 0,7933 | 2,33 |
| Floreana | 107 | 0,8550 | 0,8648 | 3,18 |
| Marchena | 80 | 0,9125 | 0,8138 | 2,49 |
| Española | 24 | 0,9484 | 0,8046 | 1,72 |
| Pinta | 24 | 0,6214 | 0,7280 | 6,02 |
| Santa Fe | 5 | 0,9262 | 0,7974 | 1,65 |
| Baltra | 4 | 0,9657 | 0,7182 | 0,78 |
| Pinzón | 2 | 0,6399 | 0,6991 | 3,68 |
| Genovesa | 1 | 0,9631 | 0,6957 | 0,55 |
| Rábida | 0 | — | — | — |
| Seymour Norte | 0 | — | — | — |
| Plaza Sur | 0 | — | — | — |
| Wolf | 0 | — | — | — |
| Darwin | 0 | — | — | — |
| Otras islas (15 islotes GADM) | 0 | — | — | — |
| **Total** | **6 606** | | | |
