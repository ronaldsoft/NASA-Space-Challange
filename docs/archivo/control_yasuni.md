# Control negativo: Parque Nacional Yasuní

El auditor midió, sobre el ráster congelado `todas_min`, una mediana de δ Marte de 0,953 en una caja aproximada de Yasuní (lat −1,6 a −0,4, lon −76,6 a −75,2; 20 748 celdas) y la comparó con Tapajós (0,98). Aquí se confirma con el polígono oficial y con las dos corridas. La v1 no se recalibró para este control.

## Polígono

Parque Nacional Yasuní, Ecuador. Fuente: UNEP-WCMC and IUCN (2026), Protected Planet, World Database on Protected and Conserved Areas (WDPCA), versión de octubre de 2026. Consulta del 14 de noviembre de 2026 al servicio [WDPCA MapServer](https://data-gis.unep-wcmc.org/server/rest/services/ProtectedPlanet/WDPCA/MapServer/1), `site_id` 186, designación Parque Nacional, IUCN II, State Verified, año 1992, autoridad Ministry of Environment. Copia local: `data/processed/controles/yasuni_pn_wdpa.geojson`.

Regla: celdas de 1 km de la grilla v1 cuyo **centro** cae dentro del polígono (`all_touched=False`). n = 10 272; nodata 0 %.

La caja del auditor (lat −1,6 a −0,4, lon −76,6 a −75,2) se reproduce como recorte rectangular: con centros de celda hay 20 770 celdas y mediana δ Marte 0,953 (`todas_min`); una ventana de 133 × 156 píxeles da exactamente 20 748 celdas y la misma mediana 0,953. El resultado oficial que se reporta es el del polígono, no el de la caja.

## Cifras (America/Guayaquil)

| Corrida | mediana δ Marte | IQR | Q1–Q3 | mediana δ Luna | IQR Luna |
|---|---|---|---|---|---|
| `todas_min` (previa) | 0,9543 | 0,0096 | 0,9489–0,9585 | 0,6851 | 0,0270 |
| `banda_propia` (oficial) | 0,9628 | 0,0078 | 0,9584–0,9662 | 0,6851 | 0,0270 |

En ambas, 0 % de las celdas tiene δ Marte < 0,05. El terreno, a 1 km, es el mismo (los rásteres de elevación, pendiente y TRI no dependen del modo): elevación mediana 228 m (IQR 34 m), pendiente mediana 0,30° (IQR 0,28°), TRI mediana 5,38 m (IQR 3,86 m).

## Tapajós

Está en la tabla de validación congelada, no en el recorte de Ecuador (la torre queda en Brasil, fuera del ráster). Sitio: FLONA Tapajós, torre LBA km 67 (BR-Sa1), −2,8567, −54,9589, buffer 10 km, n = 312, etiqueta no análogo, pendiente 0,701°, TRI 11,2 m, elevación 179 m. δ Marte: 0,9778 (`todas_min`) y 0,9819 (`banda_propia`). δ Luna: 0,7465 en ambas. El 0,98 del auditor es el redondeo de 0,9778.

Un δ alto en Yasuní y en Tapajós es coherente con terreno llano a 1 km. No se afirma analogía de clima, de bosque o de geología: el índice v1 no mira esas variables.
