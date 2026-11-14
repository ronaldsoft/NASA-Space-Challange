# Máscara de agua en la v1 (pendiente y TRI)

Fecha: 14 de noviembre de 2026 (America/Guayaquil, UTC-5). Equipo: Devebug Industries.

Pregunta de Expertos (`/workspace/validacion_galapagos.md`): aplicar una máscara de agua **antes** de calcular pendiente, TRI y relieve, para que el borde costa–mar no infle los valores.

## Qué hace ya la v1

No se cambian los productos oficiales de Ecuador ni el recorte de Galápagos: la v1 **ya deja el mar fuera de la ventana 3×3**.

1. Al leer las teselas Copernicus GLO-90, `_copdem_masked` en `pipeline_real/process.py` trata el **0,0 exacto** como nodata (comentario en el código: «0 exacto = agua / no-dato en GLO-90»). Las etiquetas del GeoTIFF lo registran: `NODATA_NOTE` y `VERTICAL_DATUM = EGM2008 (Copernicus DEM GLO-90)`. No se mezcla SRTM ni NASADEM (EGM96).
2. `slope_and_tri` en `pipeline_real/terrain.py` exige los **8 vecinos válidos** (`all8`). Si un vecino es nodata (mar), la celda sale nodata en pendiente y en TRI. El índice δ solo se calcula donde pendiente y TRI son válidos: la máscara de `delta_marte` coincide con la de pendiente (453 375 celdas).

## Cifras sobre el ráster congelado

- Elevación válida pero pendiente/TRI nulos (franja costera ya excluida del índice): **7 124** celdas en toda la grilla; **1 391** en la caja de Galápagos; **5 720** en el continente.
- Ninguna celda con pendiente válida tiene un vecino de elevación nulo (0 casos `slope` válido sin `all8`).
- No queda ningún 0,0 exacto entre las elevaciones finitas.
- En las celdas que sí entran al índice, la primera corona frente al mar no está inflada: en Galápagos la pendiente mediana del anillo costero es **1,78°**, frente a **2,89°** en el interior; en el continente, **0,33°** frente a **0,76°**. Las celdas válidas con elevación &lt; 5 m tienen pendiente baja (mediana 0,03° en el continente; solo 2 celdas en Galápagos, 0,13°).

## Qué no es

Esto no es la Water Body Mask (WBM) oficial de Copernicus, sino el proxy «0 exacto = agua» más la regla de los 8 vecinos. Tras el remuestreo bilineal quedan algunas elevaciones no nulas cerca de la costa (mínimo −2,85 m; 37 celdas con |z| &lt; 0,5 m). En las celdas que el índice sí usa, no se ve un escalón costa–mar que infle pendiente o TRI.

## Galápagos, AUC y umbral

Galápagos se evalúa con los umbrales ya congelados de `banda_propia`. **No entra al AUC ni al cálculo del umbral** (esos se fijaron solo sobre los 16 sitios de validación). No se recalibró nada con las islas. No se produjo una versión «con máscara WBM» aparte, porque la exclusión del agua en la ventana 3×3 ya está en la v1.

## ¿Valdría la pena lo mismo en la costa de Ecuador?

No se hace en esta entrega. El mismo mecanismo ya aplica a todo el ráster (Ecuador continental y Galápagos): el mar a 0 m es nodata y la franja con vecino de mar queda fuera del índice. El anillo costero que sí entra no muestra pendiente inflada. Una WBM formal podría revisar las pocas celdas con elevación residual no nula; sería una refinación a probar en una corrida futura (con n y mediana de δ con y sin esa máscara), no un cambio silencioso de los productos oficiales.
