# Diagnóstico de la v1 — Devebug Industries

El índice v1, con datos reales, **no separa** bien los análogos etiquetados de los no análogos. Eso ocurre en las dos corridas.

## Las dos corridas

| Corrida | Hora (America/Guayaquil) | AUC Marte (IC 95 %) | AUC Luna (IC 95 %) | Aciertos |
|---|---|---|---|---|
| `todas_min` (previa) | 14 nov 2026, 13:40:40 | 0,09375 (0,00–0,29) | 0,2545 (0,00–0,69) | 6 de 16 |
| `banda_propia` (oficial, §5) | 14 nov 2026, 15:31:26 | 0,09375 (0,00–0,29) | 0,2545 (0,00–0,69) | 6 de 16 |

**La corrida con `banda_propia` se hizo después de ver el AUC de `todas_min`.** El AUC no cambió. Sí cambió el mapa de δ Marte (el `d_max` de Marte pasó de 5,784 a 7,105) y el mapa de clases. El mapa de δ Luna es idéntico. El modelo nulo que usa solo |lat| da AUC Marte 0,58, mayor que el del índice. Los umbrales de Youden oficiales son 0,1304 (Marte; especificidad 0) y 0,7915 (Luna). No se dan porcentajes de cobertura.

## Por qué falla, a 1 km

A ~1 km, Marte en el MEGDR es muy suave: pendiente mediana de la banda A 0,79° (IQR 0,34–1,90°) y TRI 12 m. Los no análogos casi planos (Bondville, Tapajós, Hyytiälä) quedan cerca de esa firma. Tapajós da δ Marte 0,9778 (`todas_min`) y 0,9819 (`banda_propia`). Análogos con más relieve a esta escala (University Valley, Mauna Kea, Sverrefjell) se alejan. Meteor Crater e Inferno Chasm quedan casi planos en la grilla de 1 km.

## Control en Yasuní

En el polígono oficial del Parque Nacional Yasuní (n = 10 272 celdas, 0 % nodata; pendiente mediana 0,30°, TRI 5,38 m) la mediana de δ Marte es 0,954 (`todas_min`) y 0,963 (`banda_propia`). Un valor alto indica sobre todo terreno llano a 1 km. Detalle y fuente del polígono: `docs/control_yasuni.md`.

## Galápagos

La grilla v1 de 1 km ya incluía las islas principales (6 606 celdas). Darwin y Wolf no tienen celdas válidas a esta resolución. Con `banda_propia`, la mediana de δ Marte es 0,894 y la de δ Luna, 0,766. Se evalúan con los umbrales congelados de `banda_propia`, **sin entrar al AUC ni al umbral** y sin recalibrar. El conteo por isla (polígono GADM 4.1; Isabela 4 128, Santa Cruz 839, Fernandina 527, …; Darwin y Wolf = 0) está en `docs/galapagos_celdas_por_isla.md`.

La v1 ya deja el mar fuera de la ventana 3×3 de pendiente y TRI (0 exacto de GLO-90 = nodata; se exigen 8 vecinos válidos). No se produjo una máscara extra ni se tocaron los productos oficiales. Evidencia: `docs/galapagos_mascara_agua.md`. El tablero permite ver el continente y Galápagos por separado.
