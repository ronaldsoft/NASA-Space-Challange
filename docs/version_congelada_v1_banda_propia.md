# Acta de congelación — ANALOG/delta v1, corrida `banda_propia`

Equipo: Devebug Industries. Fecha de esta corrida: **14 de noviembre de 2026, 15:31:26** (America/Guayaquil, UTC-5).

Esta es la corrida oficial de la v1. El único cambio respecto de la corrida de las 13:40 es el modo de bandas: `modo_bandas = banda_propia` (cada celda se compara solo con la firma de su propia banda de |lat|), como indica el §5 del método. Las variables, los pesos (0,25 iguales), `elevacion_modo = absoluta`, los `std_params` y las firmas son los de la corrida de las 13:40. No se recalibró nada con Ecuador ni con Galápagos.

**La corrida con `banda_propia` se hizo después de ver el AUC de `todas_min`.** Esa corrida previa no se borra: queda en `data/processed/corrida_previa_todas_min/`, `web/public/productos/corrida_previa_todas_min/` y en el acta `docs/version_congelada_v1.md`.

Los umbrales de Youden se volvieron a fijar con el mismo procedimiento y los mismos 16 sitios (Río Tinto, Ries y Sudbury siguen fuera del AUC). Luego se aplicaron, ya congelados, a Ecuador continental y a Galápagos. Galápagos se evalúa solo con `banda_propia`. Los PNG oficiales coinciden exactamente con los que la corrida de las 13:40 había escrito en `productos/banda_propia/` (misma métrica, mismos umbrales, mismos mapas).

## Comparación de las dos corridas

| Corrida | Hora (UTC-5) | AUC Marte (IC 95 %) | AUC Luna (IC 95 %) | Aciertos |
|---|---|---|---|---|
| `todas_min` (previa) | 13:40:40 | 0,09375 (0,00–0,29) | 0,2545 (0,00–0,69) | 6 de 16 |
| `banda_propia` (oficial) | 15:31:26 | 0,09375 (0,00–0,29) | 0,2545 (0,00–0,69) | 6 de 16 |

Umbrales de Youden de la corrida oficial: Marte **0,1304** (sensibilidad 1,0, especificidad 0,0); Luna **0,7915** (sensibilidad 0,2, especificidad 1,0). En la práctica coinciden con los de `todas_min`. El `d_max` de Marte sí cambia (5,784 en `todas_min`, 7,105 en `banda_propia`); el de la Luna es el mismo (1,652). El mapa de δ Marte y el de clases cambian; el de δ Luna es idéntico (misma huella SHA-256). El modelo nulo de solo |lat| no depende del modo: AUC Marte 0,58 (0,25–0,88), AUC Luna 0,22 (0,00–0,48). La diferencia de AUC entre modos es 0; el estadístico de DeLong no está definido (varianza 0).

## Por qué el AUC coincide con el de `todas_min`

El AUC es el mismo en las dos corridas (Marte 0,09375, Luna 0,2545). No son cifras copiadas.

- Luna: en los 16 sitios del AUC, la banda ganadora de `todas_min` ya era la banda propia (16 de 16). δ Luna es idéntica; `delta_luna.png` tiene la misma huella SHA-256 `5eb786ef217863e0f022127c5d3e1ee1c07099ccc1646b26d750cda00e684dc6`.
- Marte: la banda ganadora cambia en 5 de 16 sitios y δ se mueve (`d_max` de 5,784 a 7,105). El mapa cambia: `delta_marte.png` oficial `47839ad203cccc08fb0e8cdb0d9f2e7aaf08f3abebb0fdaa3bdd2cadd9685982`, corrida previa `0152dfb637616e246d3c946f702ed251266c1a0db2c7d8bc6bfaf5fec30b0d4b`.
- El orden entre análogos y no análogos no cambia. El U de Mann–Whitney es el mismo (6 de 64 pares). AUC = U / (8 × 8) = 6/64 = 0,09375.


## Huellas SHA-256 de los productos oficiales (`banda_propia`)

| Archivo | SHA-256 |
|---|---|
| catalogo.json | bf54d0c5d35ce0a0baf28cf4ad7c570724a413c2ce1e08700b29fd5796fa602f |
| tabla_validacion.csv | 101f7a789ca7f7c1a9c61767ac78f06653410c4367bf5e54e3e6e7e5b046fcf8 |
| delta_marte.png | 47839ad203cccc08fb0e8cdb0d9f2e7aaf08f3abebb0fdaa3bdd2cadd9685982 |
| delta_marte.tif | 1fac4f7418cca4c28462ecc4354aba2e64352b551a85c4529c7ffc62d7d0d011 |
| delta_luna.png | 5eb786ef217863e0f022127c5d3e1ee1c07099ccc1646b26d750cda00e684dc6 |
| delta_luna.tif | daf00ed5e74e6308f2a9f46a4077075e335726c278e901c1a18bef24a67372c7 |
| clases.png | 72ec3e247e950e3f42a6ad4e97951ebcb2d7b833a7a37b5253ba6ae212d90272 |
| clases.tif | c00ec958e12dfb55cc46fad62306328670b79760102c026a3365a779378a89a9 |

## Recortes de área (mismos rásteres, sin recomputar)

Galápagos ya estaba en la grilla v1 de 1 km (6 606 celdas de tierra). Darwin y Wolf no tienen celdas válidas a esta resolución. Ecuador continental y Galápagos son recortes de los productos oficiales, sin cambiar el índice.

| Área | n celdas | % nodata del recorte | mediana δ Marte | mediana δ Luna |
|---|---|---|---|---|
| Galápagos (lon −91,800 a −89,118, lat −1,548 a 0,783) | 6 606 | 91,44 | 0,894 | 0,766 |
| Ecuador continental (lon −81,252 a −74,997, lat −5,103 a 1,701) | 446 657 | 14,99 | 0,955 | 0,685 |

### SHA-256 Galápagos (`web/public/productos/galapagos/`)

| Archivo | SHA-256 |
|---|---|
| delta_marte.png | 9213c6ed4030bdc0e25809b0a7af13499779510536c3a57a71c29ea6ac5a2e21 |
| delta_marte.tif | 701f20dc173b4de6e28be5934a1b543397bb9243273f3385bc6272fe117e6359 |
| delta_luna.png | 86d32247147ca64c7b4a4269e162f005b4823ee4949c369240b435d3fb9ca172 |
| delta_luna.tif | 8b8a12829f60b96d6ca733454b096df7d5e99e4fc73b79744982d6218ba89355 |
| clases.png | 8ba71b163f85e6a732bc8b47ff208a1dfa0d39142cf928c295f404a6ccfd0f46 |
| clases.tif | 796877d9a4910fe9e0023c99da2b319cc8e506210b5428ad12067be29f2ba767 |

### SHA-256 Ecuador continental (`web/public/productos/ecuador_continental/`)

| Archivo | SHA-256 |
|---|---|
| delta_marte.png | e62d28be782a76c879300c95d4a0fe343e3b1cc1b984260ae82bfab53b6dc7cd |
| delta_marte.tif | b87cdb640a9ad1d901f11648224c1c3e9057d6fbe2d589244f22ca26070f07fd |
| delta_luna.png | 2b5762899fe7057157fe2d8976463fe75280b3a83f5779b9cd568ef08299564d |
| delta_luna.tif | 71ea93857cc559ed2374a3a9305f7b8bd818bf5ba55f11351daf2b1508fcca01 |
| clases.png | 529552054dfd8ee0149d0736c79d83487dfdda2095e6a2b33528d9f93c83b42b |
| clases.tif | fd6c2bac0ba5c124ee5c0ffc4eca9ae2c629ccb7b00899954b5d0b724d21eea7 |

`elevacion_modo` es **absoluta**. No se usó relieve relativo.
