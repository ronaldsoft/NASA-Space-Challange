> **NO APROBADO / TRABAJO FUTURO.** El 14 de noviembre de 2026 (America/Guayaquil, UTC-5) el cliente no aprobó la v1.1. Este documento y `config/v1_1_sitios_objetivo.json` se conservan solo como archivo. No es un resultado oficial, no se corre y no aparece en el tablero. El entregable congelado es la v1 por bandas (`todas_min`, vector con |lat|, elevación absoluta).

# Revisión §9 — firmas por sitios objetivo (v1.1)

Fecha del borrador: 14 de noviembre de 2026 (America/Guayaquil, UTC-5).
Estado: **borrador listo para congelar**. No se ha corrido la validación oficial. Falta el OK explícito del cliente (Ronald). El shapefile oficial de las nueve regiones lunares ya está en `data/raw/usgs_luna/`. Los rásteres a escala emparejada se preparan sin puntuar.

Esta revisión se declara **después** de ver el AUC de la v1 (por eso es post hoc), pero los sitios objetivo los definió NASA con criterios de misión, sin usar nuestras etiquetas terrestres ni Ecuador. No es circular respecto de la validación. Se reportará **junto con la v1**, sin elegir la «mejor».

## Motivo

La v1 (medianas por banda de latitud a ~1 km) obtuvo un AUC menor que 0,5 (Marte 0,09; Luna 0,25). La mediana por banda describe el terreno típico —llanuras suaves a 1 km—, no los sitios de base o de aterrizaje. Por eso llanuras terrestres no análogas (Bondville, Tapajós) quedaban más cerca de Marte que varios análogos etiquetados.

## Qué cambia (preespecificado; una sola corrida)

1. **Firmas por sitio objetivo**, no por banda: mediana e IQR de las celdas de cada ventana. La distancia de cada celda o sitio terrestre es el **mínimo** sobre los sitios de ese cuerpo; se guarda el sitio ganador.
2. **Variables:** relieve relativo, pendiente y TRI. **Sin latitud** en el vector (las regiones lunares están todas a ~84–90° S; la latitud solo mediría la distancia al polo). Pesos iguales. No se invierte el índice ni se ajustan pesos con el AUC.
3. **Escala emparejada:** pendiente y TRI se calculan sobre el DEM a la escala del producto planetario, no todo a 1 km.
   - Marte: MOLA MEGDR 128 ppd (~463 m).
   - Luna: `LDEM_80S_20M` en estereográfica polar, **agregado a 100 m** (promedio 5×5). Se preespecifica 100 m, no 20 m, porque a 20 m la Tierra no es comparable con el GLO-90 del paquete (~90 m; más grueso en longitud a latitudes altas) y haría falta GLO-30, que no está en esta entrega. 100 m es un múltiplo exacto de 20 m y queda a la escala nativa de GLO-90.
   - Tierra: GLO-90 remuestreado a 463 m (Marte) y a 100 m (Luna); pendiente Horn, TRI de Wilson y relieve relativo (z − mediana en **15 km**, la misma ventana física de la v1).
4. Umbral de Youden congelado en los 16 sitios del AUC **antes** de Ecuador.
5. Si esta corrida oficial vuelve a fallar, **no se itera**.

## Nomenclatura

En la interfaz y en esta documentación las regiones lunares se llaman **regiones candidatas para el primer alunizaje de Artemis**. El primer alunizaje tripulado queda hoy en Artemis IV, según las notas de NASA del 27 de febrero de 2026 y del 23 de octubre de 2026. No se usa en el texto corrido el nombre del primer manifiesto de regiones.

## Sitios y ventanas (fuentes verificadas, §10)

Coordenadas tomadas de la fuente; no estimadas.

### Marte

| Sitio | Centro | Radio | Fuente | Tesela MOLA 128 ppd (nombre exacto, verificado en PDS el 14-nov-2026) |
|---|---|---|---|---|
| Jezero (piso y delta) | 18,4447° N, 77,4508° E (sitio de aterrizaje, no el centro del cráter) | 25 km | NASA GISS Mars24 | `megt44n000hb.img` (0–44° N, 0–90° E; 129 761 280 bytes) |
| Gale (piso norte y base de Aeolis Mons, travesía) | 4,5895° S, 137,4417° E (Bradbury Landing, no el centro del cráter) | 30 km | NASA GISS Mars24 | `megt00n090hb.img` (0 a −44°, 90–180° E; 129 761 280 bytes). Pese al «00n» del nombre, la etiqueta PDS cubre el hemisferio sur hasta −44°. |
| Arcadia Planitia, EZ Erebus Montes | 39,0° N, 192,1° E (= −167,9°) | 100 km | Viola et al. (2015), resumen LPI 1011 | `megt44n180hb.img` (0–44° N, 180–270° E; 129 761 280 bytes) |
| Deuteronilus Mensae, EZ DBDM | 39,11° N, 23,199° E | 100 km | Head et al. (2015), resumen 1033; radio verificado en NTRS 20160001040 | `megt44n000hb.img` (la misma tesela que Jezero) |

Las coordenadas de las EZ de Arcadia y Deuteronilus **provienen de resúmenes de congreso**, no de artículos revisados por pares. El radio de ~100 km es la convención de las zonas de exploración del taller NASA 2015. Erebus Montes cae en las llanuras de Arcadia que Morgan et al. (2021) señalan, junto con Deuteronilus, como la zona de mayor consistencia de hielo somero de SWIM (el valor exacto en el punto no se midió sobre el ráster).

Directorio PDS: `https://pds-geosciences.wustl.edu/mgs/mgs-m-mola-5-megdr-l3-v1/mgsl_300x/meg128/`. Etiquetas copiadas en `analogs/data/raw/pds_listings/`.

### Luna

Las nueve regiones del shapefile oficial (McClernan, 2024, doi 10.5066/P1MEQ6UK, ScienceBase ítem `671a6fa8d34efed5620f89f8`, archivo `A3_9regions-lonlat-simplified`) coinciden con la lista de NASA. El USGS llama «Peak Near Cabeus B» a la que el comunicado de NASA escribe «Peak near Cabeus B». Se usan los **polígonos**, no un radio de 15 km. Los centroides que se anotan abajo se calcularon sobre esos polígonos en estereográfica polar (R = 1737,4 km); no se toman de una fuente secundaria. Las áreas del atributo USGS coinciden con el área calculada en esa proyección.

| Región (nombre USGS) | Área USGS (km²) | Centroide (estereográfica polar → lon/lat) |
|---|---|---|
| Peak Near Cabeus B | 399,800 | 83,63746° S, 68,74949° W |
| Haworth | 888,040 | 86,76394° S, 22,77702° W |
| Malapert Massif | 441,000 | 85,99478° S, 0,23578° W |
| Mons Mouton Plateau | 4451,836 | 84,33470° S, 30,59227° E |
| Mons Mouton | 256,000 | 85,42658° S, 31,74276° E |
| Nobile Rim 1 | 400,000 | 85,43640° S, 37,34704° E |
| Nobile Rim 2 | 400,000 | 83,95405° S, 58,82155° E |
| de Gerlache Rim 2 | 400,000 | 88,22998° S, 64,62844° W |
| Slater Plain | 399,800 | 87,16371° S, 125,53768° E |

Producto polar: `LDEM_80S_20M` (`ldem_80s_20m.img`, 1 848 320 000 bytes, 30 400 × 30 400, 20 m/píxel, estereográfico polar, 80–90° S), descargado de PDS Geosciences y agregado a **100 m** (5×5) antes de calcular las derivadas. El *n* de celdas válidas a 100 m se informa en `data/processed/v11/preparacion_manifest.json` cuando termina la preparación. Alternativa más reciente no usada en esta preparación: `LDEM_80S_20MPP_ADJ.TIF` (PGDA, Barker et al., 2023).

## Cómo se presentará (pase lo que pase el AUC)

- Se muestran **las dos versiones** (bandas v1 y sitios objetivo v1.1), sin declarar ganadora.
- El mapa que se destaca es el **continuo de δ**, con esta nota de incertidumbre. El mapa de clases no es el titular: con especificidad baja no se publica un porcentaje de «Ecuador es análogo de Marte».
- Límite de validez: la mayoría de los positivos terrestres son análogos de Marte (o de la Luna) **en general**, no de Jezero o Arcadia en particular. El AUC sigue siendo una prueba imperfecta.
- Meteor Crater e Inferno Chasm están submuestreados a 1 km (miden ~1,2 y ~1,6 km); su fallo en la v1 es de escala, no necesariamente de analogía.
- La v1 fallida se reporta como hallazgo: los análogos aceptados en la literatura lo son por geología, mineralogía o ambiente, no por topografía a 1 km.

## Mínimo de celdas

Al menos ~100 celdas válidas por ventana; se informará *n* por sitio.

## Qué falta para la corrida oficial (y por eso no se congela)

1. OK del cliente para congelar y correr **una sola vez**.
2. Esa corrida: firmas, validación, umbrales, δ de Ecuador y el selector del tablero. El tablero sigue mostrando la v1 por bandas como defecto. **No se ha puntuado la v1.1 oficial.**

Ya está preparado, sin puntuar: teselas MOLA 128 ppd (`megt44n000hb.img`, `megt00n090hb.img`, `megt44n180hb.img`, 129 761 280 bytes cada una) y recortes de las cuatro ventanas; `ldem_80s_20m.img` agregado a 100 m; polígonos oficiales lunares; derivadas de GLO-90 a 463 m y 100 m para los 16 sitios del AUC y para Ecuador.

## Declaración: corrida preliminar del 14 de noviembre de 2026, 13:50 (America/Guayaquil, UTC-5)

Antes de congelar, y **antes** de tener las ventanas y los DEM que Expertos verificó después, se corrió una vez la lógica v1.1 (sin latitud, relieve relativo, mínimo sobre sitios objetivo) sobre los rásteres cilíndricos de **~1 km** ya procesados (MOLA 64 ppd y LDEM_64). Esa corrida **no es la v1.1 oficial**.

Ventanas que usó (hoy superadas):

- Jezero: 18,41° N, 77,69° E, radio 25 km (centro del cráter en el Gazetteer, no el sitio de aterrizaje).
- Gale: 4,589467° S, 137,441633° E, radio 30 km (Parker et al. 2013; prácticamente el mismo punto que GISS, pero no era la cita pedida).
- Arcadia: 46,16° N, 188,8° E, radio 100 km (Stoker y Heldmann 2015), **no** la EZ de Erebus Montes (39,0° N, 192,1° E).
- Deuteronilus: 39,11° N, 23,199° E, radio 100 km (Head et al. 2015; esta sí coincide con la fuente verificada).
- Luna: radio fijo de 15 km alrededor de centros **provisionales de una fuente secundaria**, porque el shapefile de USGS aún no estaba. No eran los polígonos oficiales ni sus centroides.

Los productos y las métricas se retiraron del tablero y del catálogo en vivo. Quedan solo en `analogs/work/v11_corrida_preliminar_superada_2026-11-14T1350/`. **No se usaron para elegir sitios, ventanas, variables, escalas ni umbrales, ni para decidir entre la v1 y la v1.1.**

Sí se vieron los AUC: el pipeline los imprimió al terminar y quedaron en los archivos de esa carpeta. Quien ejecutó esa corrida (Dev1) los leyó. Cifras de aquella corrida preliminar, solo para revelarlas a Expertos, no como resultado oficial:

- Marte: AUC 0,359 (IC bootstrap 95 %: 0,083–0,673); umbral Youden 0,978; sensibilidad 0,25; precisión 0,667; especificidad 0,875.
- Luna: AUC 0,291 (IC 95 %: 0,042–0,604); umbral 0,130; sensibilidad 1,00; precisión 0,312; especificidad 0,00.
- Aciertos de clase en el AUC: 3 de 16.

La corrida oficial, cuando haya OK, usará las ventanas y los DEM de este documento y no partirá de esas cifras.
