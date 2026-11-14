# Nota de incertidumbre — ANALOG/delta v1 (datos reales)

Fecha de congelación de parámetros, firmas y umbrales: 14 de noviembre de 2026 (America/Guayaquil, UTC-5).

Esta nota acompaña los productos reales del índice de homología de superficie Tierra–Marte–Luna. El índice v1 usa solo **latitud (|lat|), elevación, pendiente y rugosidad (TRI 3×3)**, con pesos iguales. **No incluye albedo, inercia térmica ni ninguna variable meteorológica** (veredicto de Expertos). Por eso **no puede llamarse «clima análogo»** ni «análogo ambiental completo».

## Cómo se calculó (y qué quedó congelado)

1. Los parámetros de estandarización (`std_params`) y las firmas por banda A–G (mediana e IQR) se ajustaron **solo** sobre las muestras estratificadas de Marte (MOLA MEGDR 64 ppd) y de la Luna (LOLA LDEM_64), 56 000 celdas por cuerpo, sin mezclar los dos cuerpos ni usar celdas terrestres.
2. En cada sitio de validación se tomó la **mediana de las celdas válidas dentro del buffer** oficial (distancia haversina, radio de Expertos). No se eligió la «mejor» celda del buffer, para no inflar el AUC. También se archivó la celda central como referencia. Río Tinto, Ries y Sudbury se listan pero **no entran al AUC** (análogos no de superficie o cobertura actual no comparable) y no tienen ventana GLO-90 en esta entrega.
3. El umbral se fijó con la regla del **mínimo entre bandas** (`todas_min`, distancia euclídea) y el criterio de Youden, **solo** sobre los 16 sitios del AUC. Después se congeló. Ecuador no intervino en esa decisión.
4. Recién entonces se calculó δ Marte, δ Luna y el mapa de clases sobre Ecuador y Galápagos.

Askja permanece en el AUC con la coordenada confirmada **65.060, −16.640** y buffer de 6 km (punto medio de la colada Vikrahraun; Blasizzo et al., 2022, additional file 1, hoja «(1.1) Samples»). Se descarta 65.03, −16.78.

## Resultado de la validación

En datos reales el índice **no discrimina bien** los análogos etiquetados de los no análogos. Las cifras que siguen son del modo por defecto (`todas_min`, vector con |lat|, elevación absoluta). Los intervalos son el IC bootstrap al 95 %.

| Variante | AUC Marte (IC 95 %) | Sens. | Prec. | AUC Luna (IC 95 %) | Sens. | Prec. |
|---|---|---|---|---|---|---|
| todas_min, con \|lat\|, elevación absoluta (**defecto**) | **0.09** (0.00–0.29) | 1.00 | 0.50 | **0.25** (0.00–0.69) | 0.20 | 1.00 |
| banda_propia, con \|lat\|, absoluta | 0.09 (0.00–0.29) | 1.00 | 0.50 | 0.25 (0.00–0.69) | 0.20 | 1.00 |
| todas_min, sin latitud, absoluta | 0.13 (0.00–0.34) | 1.00 | 0.50 | 0.27 (0.00–0.71) | 0.20 | 1.00 |
| banda_propia, sin latitud, absoluta | 0.09 (0.00–0.29) | 1.00 | 0.50 | 0.25 (0.00–0.69) | 0.20 | 1.00 |
| todas_min, con \|lat\|, relieve relativo | 0.14 (0.00–0.38) | 1.00 | 0.50 | 0.36 (0.08–0.69) | 0.80 | 0.33 |
| banda_propia, con \|lat\|, relieve relativo | 0.14 (0.00–0.38) | 1.00 | 0.50 | 0.36 (0.08–0.69) | 0.80 | 0.33 |
| todas_min, sin latitud, relieve relativo | 0.17 (0.00–0.44) | 1.00 | 0.50 | 0.40 (0.06–0.79) | 0.40 | 0.40 |
| banda_propia, sin latitud, relieve relativo | 0.13 (0.00–0.33) | 1.00 | 0.50 | 0.42 (0.08–0.79) | 0.20 | 0.50 |
| **Modelo nulo (solo \|lat\|)** | **0.58** (0.25–0.88) | — | — | 0.22 (0.00–0.48) | — | — |

- Aciertos de clase en el AUC (defecto): **6 de 16**.
- DeLong pareado (con |lat| frente a sin latitud): Marte ΔAUC = −0.03, p = 0.60; Luna ΔAUC = −0.02, p = 0.48. No hay diferencia significativa.
- DeLong (elevación absoluta frente a relieve relativo): Marte ΔAUC = −0.05, p = 0.24; Luna ΔAUC = −0.11, p = 0.53. El relieve relativo mejora un poco el AUC, pero sigue por debajo de 0.5 y la diferencia no es significativa en esta muestra.
- El **modelo nulo de solo |lat|** obtiene un AUC de Marte **mayor** que el índice completo (0.58 frente a 0.09). Los positivos de Marte no están siendo ranqueados por su firma de superficie, y el índice invertido (AUC < 0.5) indica que varios no análogos quedan *más cerca* de la firma típica de Marte que los análogos etiquetados.

### Por qué ocurre (diagnóstico, no un ajuste)

A ~1 km, **Marte es un planeta muy suave** en el MEGDR: la mediana de pendiente de la banda A es 0.79° (IQR 0.34–1.90°) y la de TRI, 12 m. Los no análogos terrestres del conjunto (llanura agrícola de Bondville, bosque de Tapajós, Hyytiälä, etc.) también son casi planos a 1 km (pendientes 0.1–0.7°, TRI de unos pocos metros). En ese espacio, **Tapajós llega a δ Marte = 0.98**, más alto que Yungay, Askja o Haughton.

Al contrario, análogos con más relieve a esta escala (University Valley, Mauna Kea, Sverrefjell) se alejan de la mediana marciana. Meteor Crater (~1.2 km de diámetro) e Inferno Chasm quedan **casi planos** en la grilla de 1 km (pendiente mediana del buffer ≈ 0.5°) y el índice los acerca a Marte, no a la Luna.

Esto no se «arregló» tocando el umbral ni añadiendo clima: el método prohíbe reajustar con Ecuador y el índice v1 no admite meteorología. El mapa de clases es la consecuencia directa de un umbral de Youden congelado sobre un AUC invertido: el umbral de Marte queda en **0.13**, con sensibilidad 1.0 y **especificidad 0.0** (todos los no análogos también lo superan). El umbral lunar queda alto (0.79) y casi no hay celdas solo-Luna.


## Regla de bandas (`todas_min`) y el §5 del método

La v1 congelada usa `modo_bandas = todas_min`: al calcular δ de un lugar, lo compara con las firmas de las **siete** bandas de latitud (A–G) y se queda con la distancia más baja. Guarda cuál banda «ganó». La otra regla ya programada, `banda_propia`, solo usaría la banda de la |lat| de ese lugar. La v1 no se recalcula: el modo oficial sigue siendo `todas_min`.

El §5 del documento de método (`proyecto_ronald.txt`, «Muestreo por latitud») no describe esa regla de mínimo entre todas las bandas. El texto dice:

> La muestra de referencia planetaria no es un promedio global. Se construye así:
>
> 1. Se toman las latitudes de las estaciones demostrativas terrestres actuales.
> 2. Se añaden las franjas latitudinales donde ya se decidió extraer varias muestras.
> 3. En Marte y en la Luna se extraen celdas dentro de esas mismas bandas de latitud (y, si el diseño lo exige, bandas simétricas norte/sur).
> 4. Dentro de cada banda se muestrea de forma sistemática o aleatoria estratificada, con un número mínimo de celdas por banda, para no dejar que un solo sitio domine la firma.
>
> La latitud alinea el muestreo; no sustituye al resto de variables de superficie.

En resumen: el §5 alinea el muestreo de Marte y de la Luna con las mismas bandas de latitud de los sitios terrestres de referencia. Comparar un lugar con todas las bandas y quedarse con la más cercana (`todas_min`) no está en ese apartado. `banda_propia` se acerca más a «la misma banda de latitud», pero no es el modo oficial de la v1.

Ronald no aprobó esta diferencia y no eligió entre `todas_min` y `banda_propia`. La v1 se deja como está.

### Qué muestran los tiempos (America/Guayaquil, UTC-5)

No hay en el expediente un sello que permita afirmar que `todas_min` se eligió *antes* de ver el AUC real. Lo que sí está fechado, el 14 de noviembre de 2026:

- **13:22** (mtime de `pipeline/index.py`): el código ya tiene `todas_min` como valor por defecto, con la nota de que el §5 queda pendiente de confirmación de Ronald.
- **13:23**: las pruebas unitarias cubren ambos modos (`pipeline/tests/test_pipeline.py`).
- **13:27**: el catálogo MOCK ya describe `todas_min` como defecto, pendiente de esa confirmación. Ese archivo no es una corrida con datos reales.
- **13:36**: `data/processed/processing_summary.json` (estadísticos de los DEM remuestreados; no incluye AUC).
- **13:40:40**: campo `congelado_en` de `web/public/productos/catalogo.json`. En ese catálogo ya figuran los umbrales de Youden y el AUC (Marte 0,09, Luna 0,25). El script `pipeline/run_real.py` tiene el mismo mtime. La tabla `tabla_validacion.csv` y los rásteres oficiales (también la variante `banda_propia/`) tienen mtime **13:40:49–13:40:50**.
- **14:33**: acta `docs/version_congelada_v1.md`. Esa acta no recalculó los productos; indica mtime de productos a las 13:40 y calcula las huellas SHA-256 sobre esos archivos.

Con este registro se puede decir que el código ya listaba `todas_min` como defecto al menos 18 minutos antes del sello `congelado_en`. No se puede demostrar, solo con estos relojes, que nadie hubiera visto un AUC real antes de las 13:22, ni que la elección se haya cerrado sin mirar la validación. Por eso **no se afirma** que la regla se haya «decidido antes de ver el AUC».

## Ecuador, después del congelado

Con el umbral por defecto ya congelado, sobre 453 375 celdas terrestres de Ecuador y Galápagos:

| Clase | Celdas (defecto) | Lectura |
|---|---|---|
| Marte | 356 828 | Dominante: consecuencia del umbral bajo de Marte, no de una analogía contrastada |
| Ambos | 53 535 | δ Marte y δ Luna por encima de sus umbrales |
| Luna | 0 | Ninguna celda supera el umbral lunar sin superar también el de Marte |
| Ninguno | 43 012 | Sobre todo relieve andino alto y laderas muy pendientes (p. ej. Chimborazo, Cotopaxi, Cayambe, Fernandina: δ = 0 porque su distancia supera d_max) |
| Sin dato | 975 465 | Mar, nodata de GLO-90 (0 m exacto enmascarado) y bordes sin 8 vecinos para TRI |

Las demás variantes (incluida `banda_propia` y el relieve relativo) también producen un Ecuador **casi todo «Marte» o «ambos» y cero «solo Luna»**. No se eligió otra variante para «arreglar» el mapa. El modo oficial de la v1 sigue siendo `todas_min`, con |lat| y elevación absoluta. Ronald no aprobó esa regla ni eligió entre `todas_min` y `banda_propia`; ver la sección siguiente. El relieve relativo queda a la espera de una decisión del equipo sobre el §3.

Los rásteres **continuos** de similitud (δ Marte y δ Luna) son más informativos que el mapa de clases recortado por un umbral poco fiable. La máxima δ Marte de este recorte cae en una llanura baja (~19 m, pendiente 0.8°), coherente con el sesgo hacia terrenos suaves.

## Limitaciones de los datos (del README de datos)

1. La analogía es solo de superficie y únicamente con las variables comparables.
2. La resolución única de ~1 km suaviza el relieve local, sobre todo en los Andes y en cráteres o conos de unos pocos kilómetros (Meteor Crater ~1.2 km; University Valley con buffer de 3 km).
3. Marte se remuestrea de ~926 m (64 ppd) a ~1 km; no se usó el MEGDR de 128 ppd.
4. Luna: se parte de ~474 m (LDEM_64) y se pierden dos factores de 2 al pasar a 1 km. El LDEM de 128 ppd no se descargó.
5. Cobertura MOLA: interpolación entre huellas (huecos de hasta ~12 km cerca del ecuador) y datos más pobres por encima de ~87° de latitud.
6. LDEM 64: posibles artefactos en los bordes de las bandas de 45° (advertencia del rótulo). Datum vertical = esfera, no geoide lunar.
7. Los datums verticales no son el mismo tipo de superficie de referencia (areoide MOLA, esfera lunar de 1737.4 km, geoide EGM2008). La elevación absoluta no es homologable al metro. La variante de relieve relativo (elevación menos la mediana en una ventana de 15 × 15 celdas) está calculada y no es el modo por defecto, a la espera de la decisión del equipo (§3).
8. En Tierra, el 0 m exacto de GLO-90 se enmascaró; la costa y el agua interior pueden perder celdas. GLO-90 es más grueso en longitud en latitudes altas.
9. Inferno Chasm usa una coordenada de resumen LPSC, no de revista.
10. Albedo e inercia térmica no entran al índice v1 (tampoco la abundancia de roca) y no se descargaron.
11. Pendiente y TRI en proyección equirrectangular cerca de los polos son más inciertos: la celda geográfica se estrecha en metros de longitud. La banda G (80–90°) se muestreó porque es obligatoria para el polo sur lunar.
12. No hay un ráster global terrestre: solo Ecuador/Galápagos y las ventanas de validación.
13. La banda A no tiene positivos terrestres (Ecuador se evalúa ahí, no se calibra). La banda D es débil. La banda G no tiene estaciones terrestres.
14. `todas_min` solo es válida con distancia euclídea. Si se usara Mahalanobis por banda, la latitud saldría del vector automáticamente.

## Qué sí se puede afirmar, y qué no

- Sí: el flujo es reproducible, los parámetros están congelados, las fuentes (MOLA, LOLA, GLO-90) están documentadas y la validación está hecha con la lista verificada de Expertos.
- Sí: a 1 km, la firma típica de Marte (y, en menor grado, de la Luna) en pendiente y TRI se parece más a llanuras terrestres suaves que a varios análogos clásicos de campo, cuyo relieve distintivo no sobrevive a esa escala.
- No: no se puede presentar el mapa de clases de Ecuador como un inventario fiable de análogos. El umbral de Marte, congelado según la regla acordada, no tiene poder de discriminación en este conjunto.
- No: no se publica una capa climática. El clima no entra al índice y no se muestra un ráster de ejemplo, para no confundirlo con un dato real.

Una mejora futura (fuera de este MVP) pasaría por una resolución más fina en los análogos de pocos kilómetros, por la decisión sobre el relieve relativo, o por capas que Expertos ya rechazó para el v1 (albedo, inercia térmica). No por añadir meteorología al índice ni por retocar el umbral mirando Ecuador.

## Revisión §9 (v1.1): no aprobada — queda como trabajo futuro

El 14 de noviembre de 2026 (America/Guayaquil) el cliente **no aprobó** la v1.1. No se corre como resultado, no se congela y no aparece en el tablero. El entregable oficial es la **v1 por bandas**, congelada tal cual (`todas_min`, vector con |lat|, elevación absoluta, umbrales ya fijados).

Queda archivada en disco, marcada «NO aprobado / trabajo futuro», una idea de revisión que sustituiría las firmas por banda por firmas de sitios objetivo definidos a priori (Jezero, Gale, la zona de exploración Erebus Montes en Arcadia, la EZ DBDM en Deuteronilus, y las nueve regiones candidatas para el primer alunizaje de Artemis), con relieve relativo, pendiente y TRI a escala emparejada, sin latitud. Una corrida preliminar de las 13:50 (UTC-5) de ese mismo día usó ventanas y DEM superados; sus cifras se apartaron y no se usaron para elegir nada. El detalle permanece en `docs/cambio_metodo_sitios_objetivo.md` y `config/v1_1_sitios_objetivo.json` (estado: no_aprobado_trabajo_futuro).

El mapa que debe leerse en esta entrega es el continuo de δ, no el de clases.
