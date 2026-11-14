# Versión congelada: ANALOG/delta v1

- **Fecha de esta acta:** 14 de noviembre de 2026, 14:33 (America/Guayaquil, UTC-5).
- **Fecha de congelación de parámetros, firmas y umbrales:** 14 de noviembre de 2026, 13:40:40 (America/Guayaquil, UTC-5), campo `congelado_en` del catálogo.
- **Versión:** ANALOG/delta v1 real (firmas por bandas de latitud). Identificador en catálogo: `ANALOG/delta v1 real 2026-11-14`.

Esta es la versión oficial del entregable. Los parámetros no se modifican después de esta acta.

## Qué quedó congelado (sin cambios)

- Índice de superficie con cuatro variables de pesos iguales (0,25): **|lat|**, **elevación absoluta**, **pendiente** (Horn 3×3) y **rugosidad** (TRI de Wilson 3×3).
- Firmas por **bandas de latitud** A–G; modo de distancia **`todas_min`**.
- Umbrales de Youden fijados solo sobre los 16 sitios del AUC, antes de Ecuador:
  - Marte: 0,1304 (sensibilidad 1,00; precisión 0,50; especificidad 0,00).
  - Luna: 0,7915 (sensibilidad 0,20; precisión 1,00; especificidad 1,00).
- Validación oficial (bootstrap 2000 / 1990 repeticiones, IC 95 %):
  - **AUC Marte 0,09** (0,00–0,29).
  - **AUC Luna 0,25** (0,00–0,69).
  - Aciertos de clase en el AUC: **6 de 16**.
- El clima no entra al índice y no se publica. No hay banner MOCK sobre contenido real.

La v1.1 (firmas de sitios objetivo) **no forma parte** de esta congelación: el 14 de noviembre de 2026 el cliente no la aprobó. Queda en disco como «NO aprobado / trabajo futuro» (`config/v1_1_sitios_objetivo.json`, `docs/cambio_metodo_sitios_objetivo.md`).

## Huellas SHA-256 de configuración y productos

Calculadas el 14 de noviembre de 2026, 14:33 (America/Guayaquil) sobre los archivos de `web/public/productos/` que sirve el tablero estático.

| Archivo | SHA-256 |
|---|---|
| `catalogo.json` | `369dd38593f76d46266d1cd86077ce4729fb7b1e3811adc66b74fe0be51c87dd` |
| `tabla_validacion.csv` | `7ff7856cc3581e31b1a55f32b5a5cc48191a5160bf677dd3437a0968e4a95218` |
| `delta_marte.png` | `0152dfb637616e246d3c946f702ed251266c1a0db2c7d8bc6bfaf5fec30b0d4b` |
| `delta_marte.tif` | `dba0f23685d35f5e6399be7ebfbc816e552e0e969a88a8e35821b39b2b1ed406` |
| `delta_luna.png` | `5eb786ef217863e0f022127c5d3e1ee1c07099ccc1646b26d750cda00e684dc6` |
| `delta_luna.tif` | `daf00ed5e74e6308f2a9f46a4077075e335726c278e901c1a18bef24a67372c7` |
| `clases.png` | `c9fedb0c7931fda40311ccf1556266cb1165ceea9de12abfb0c519363e6997af` |
| `clases.tif` | `a92f6781cc589d0de787e5ac74eae0042e56c6d89a16bd3abfa23968b0d9b886` |

La copia de entrega `/workspace/tabla_validacion.csv` tiene la misma huella que `web/public/productos/tabla_validacion.csv`.

Los rásteres y la tabla de validación no se recalcularon para esta acta (mtime de productos: 13:40, America/Guayaquil). El catálogo de esos productos se dejó en modo v1 puro (sin selector ni resultados de la v1.1).

## Apéndice: modo de bandas y el §5 del método

Este apéndice no modifica los parámetros, umbrales, productos ni huellas de arriba. Solo deja constancia de una diferencia con el documento de método.

La v1 oficial usa `modo_bandas = todas_min`: δ se calcula como la menor distancia a las firmas de las siete bandas de latitud A–G. El otro modo ya programado, `banda_propia`, compararía cada lugar solo con la banda de su propia |lat|. Ronald no aprobó esa diferencia y no eligió entre las dos reglas. La v1 no se recalcula.

Esa regla no aparece en el §5 («Muestreo por latitud») de `proyecto_ronald.txt`. Ese apartado pide construir la muestra planetaria en las mismas bandas de latitud de las estaciones terrestres de referencia (y en franjas ya previstas), con muestreo estratificado dentro de cada banda: «En Marte y en la Luna se extraen celdas dentro de esas mismas bandas de latitud». La latitud, dice el texto, «alinea el muestreo; no sustituye al resto de variables de superficie».

Tiempos del 14 de noviembre de 2026 (America/Guayaquil, UTC-5), sin inferir más de lo que fechan:

- 13:22 — `pipeline/index.py` ya tiene `todas_min` como defecto, pendiente de confirmación de Ronald sobre el §5.
- 13:23 — pruebas de ambos modos.
- 13:27 — catálogo MOCK (no es un AUC real) describe el mismo defecto.
- 13:36 — `processing_summary.json` de los DEM; no trae AUC.
- 13:40:40 — `congelado_en` en `catalogo.json`, con umbrales de Youden y AUC (0,09 / 0,25). Mtime de `pipeline/run_real.py` igual. Rásteres y `tabla_validacion.csv`: 13:40:49–13:40:50.
- 14:33 — esta acta; las huellas de la tabla anterior se calcularon sobre esos productos, sin recalcularlos.

El código ya listaba el defecto 18 minutos antes del sello de congelación. Eso no basta para afirmar que `todas_min` se decidió antes de ver el AUC real. El detalle está en `docs/nota_incertidumbre.md`.
