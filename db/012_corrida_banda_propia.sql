-- db/012_corrida_banda_propia.sql
-- Idempotente. Carga la corrida oficial banda_propia (15:31:26 America/Guayaquil)
-- y deja la corrida previa todas_min. No contiene credenciales. NO ejecutar desde este agente:
-- Chief lo corre por el conector.
BEGIN;

-- Columnas de corrida y área, con valor por defecto para las filas ya cargadas.
ALTER TABLE analog.thresholds ADD COLUMN IF NOT EXISTS corrida text;
UPDATE analog.thresholds SET corrida = 'todas_min' WHERE corrida IS NULL;
ALTER TABLE analog.thresholds ALTER COLUMN corrida SET DEFAULT 'todas_min';

ALTER TABLE analog.validation_results ADD COLUMN IF NOT EXISTS corrida text;
UPDATE analog.validation_results SET corrida = COALESCE(corrida, modo_bandas, 'todas_min') WHERE corrida IS NULL;
ALTER TABLE analog.validation_results ALTER COLUMN corrida SET DEFAULT 'todas_min';
-- Ampliar la clave primaria para guardar las dos corridas.
ALTER TABLE analog.validation_results DROP CONSTRAINT IF EXISTS validation_results_pkey;
ALTER TABLE analog.validation_results ADD CONSTRAINT validation_results_pkey PRIMARY KEY (site_id, corrida);

ALTER TABLE analog.ecuador_rasters ADD COLUMN IF NOT EXISTS area text;
ALTER TABLE analog.ecuador_rasters ADD COLUMN IF NOT EXISTS corrida text;
UPDATE analog.ecuador_rasters SET area = COALESCE(area, 'ecuador_mas_galapagos'), corrida = COALESCE(corrida, 'todas_min');
ALTER TABLE analog.ecuador_rasters ALTER COLUMN area SET DEFAULT 'ecuador_mas_galapagos';
ALTER TABLE analog.ecuador_rasters ALTER COLUMN corrida SET DEFAULT 'todas_min';

ALTER TABLE analog.priority_zones ADD COLUMN IF NOT EXISTS area text;
ALTER TABLE analog.priority_zones ADD COLUMN IF NOT EXISTS corrida text;
UPDATE analog.priority_zones SET corrida = COALESCE(corrida, 'todas_min');
UPDATE analog.priority_zones SET area = CASE WHEN lon < -85 THEN 'galapagos' ELSE 'ecuador_continental' END WHERE area IS NULL;
ALTER TABLE analog.ecuador_results ADD COLUMN IF NOT EXISTS area text;
ALTER TABLE analog.ecuador_results ADD COLUMN IF NOT EXISTS corrida text;
UPDATE analog.ecuador_results SET corrida = COALESCE(corrida, 'todas_min');
UPDATE analog.ecuador_results SET area = CASE WHEN lon < -85 THEN 'galapagos' ELSE 'ecuador_continental' END WHERE area IS NULL;

-- Umbrales oficiales banda_propia (PK body, frozen_at: no pisan los de 13:40).
INSERT INTO analog.thresholds (body, value, metric, d_max, sensitivity, precision_, specificity, auc, ic95_inferior, ic95_superior, frozen_at, corrida)
VALUES ('mars', 0.13043478260869557, 'youden', 7.104575532239943, 1.0, 0.5, 0.0, 0.09375,
 0.0,
 0.2857142857142857,
 timestamptz '2026-11-14T15:31:26-05:00', 'banda_propia')
ON CONFLICT (body, frozen_at) DO UPDATE SET
  value = EXCLUDED.value, metric = EXCLUDED.metric, d_max = EXCLUDED.d_max,
  sensitivity = EXCLUDED.sensitivity, precision_ = EXCLUDED.precision_,
  specificity = EXCLUDED.specificity, auc = EXCLUDED.auc,
  ic95_inferior = EXCLUDED.ic95_inferior, ic95_superior = EXCLUDED.ic95_superior,
  corrida = EXCLUDED.corrida;
INSERT INTO analog.thresholds (body, value, metric, d_max, sensitivity, precision_, specificity, auc, ic95_inferior, ic95_superior, frozen_at, corrida)
VALUES ('moon', 0.7915472614686689, 'youden', 1.651817219714007, 0.2, 1.0, 1.0, 0.2545454545454546,
 0.0,
 0.6923076923076923,
 timestamptz '2026-11-14T15:31:26-05:00', 'banda_propia')
ON CONFLICT (body, frozen_at) DO UPDATE SET
  value = EXCLUDED.value, metric = EXCLUDED.metric, d_max = EXCLUDED.d_max,
  sensitivity = EXCLUDED.sensitivity, precision_ = EXCLUDED.precision_,
  specificity = EXCLUDED.specificity, auc = EXCLUDED.auc,
  ic95_inferior = EXCLUDED.ic95_inferior, ic95_superior = EXCLUDED.ic95_superior,
  corrida = EXCLUDED.corrida;

-- Resultados de validación (banda_propia), enlazados por site_key o por nombre.
-- Requiere que analog.validation_sites ya esté cargado.
INSERT INTO analog.validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at, banda_latitud, banda_ganadora_marte, banda_ganadora_luna, modo_bandas, acierto, corrida)
SELECT vs.id, 0.8594, 0.756, 'marte', 'marte',
 'ANALOG/delta v1 banda_propia', timestamptz '2026-11-14T15:31:26-05:00', 'B', 'B', 'B',
 'banda_propia', TRUE, 'banda_propia'
FROM analog.validation_sites vs
WHERE vs.site_key = 'yungay' OR vs.name = 'Yungay, núcleo hiperárido del Atacama (Chile)'
ON CONFLICT (site_id, corrida) DO UPDATE SET
  delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at,
  banda_latitud = EXCLUDED.banda_latitud, banda_ganadora_marte = EXCLUDED.banda_ganadora_marte,
  banda_ganadora_luna = EXCLUDED.banda_ganadora_luna, modo_bandas = EXCLUDED.modo_bandas,
  acierto = EXCLUDED.acierto;
INSERT INTO analog.validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at, banda_latitud, banda_ganadora_marte, banda_ganadora_luna, modo_bandas, acierto, corrida)
SELECT vs.id, 0.9147, 0.672, 'marte', 'marte',
 'ANALOG/delta v1 banda_propia', timestamptz '2026-11-14T15:31:26-05:00', 'F', 'F', 'F',
 'banda_propia', TRUE, 'banda_propia'
FROM analog.validation_sites vs
WHERE vs.site_key = 'haughton' OR vs.name = 'Estructura de impacto de Haughton, isla Devon (Nunavut, Canadá)'
ON CONFLICT (site_id, corrida) DO UPDATE SET
  delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at,
  banda_latitud = EXCLUDED.banda_latitud, banda_ganadora_marte = EXCLUDED.banda_ganadora_marte,
  banda_ganadora_luna = EXCLUDED.banda_ganadora_luna, modo_bandas = EXCLUDED.modo_bandas,
  acierto = EXCLUDED.acierto;
INSERT INTO analog.validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at, banda_latitud, banda_ganadora_marte, banda_ganadora_luna, modo_bandas, acierto, corrida)
SELECT vs.id, 0.1304, 0.4115, 'marte', 'marte',
 'ANALOG/delta v1 banda_propia', timestamptz '2026-11-14T15:31:26-05:00', 'F', 'F', 'F',
 'banda_propia', TRUE, 'banda_propia'
FROM analog.validation_sites vs
WHERE vs.site_key = 'university_valley' OR vs.name = 'University Valley, Valles Secos de McMurdo (Antártida)'
ON CONFLICT (site_id, corrida) DO UPDATE SET
  delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at,
  banda_latitud = EXCLUDED.banda_latitud, banda_ganadora_marte = EXCLUDED.banda_ganadora_marte,
  banda_ganadora_luna = EXCLUDED.banda_ganadora_luna, modo_bandas = EXCLUDED.modo_bandas,
  acierto = EXCLUDED.acierto;
INSERT INTO analog.validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at, banda_latitud, banda_ganadora_marte, banda_ganadora_luna, modo_bandas, acierto, corrida)
SELECT vs.id, 0.7841, 0.6357, 'marte', 'marte',
 'ANALOG/delta v1 banda_propia', timestamptz '2026-11-14T15:31:26-05:00', 'E', 'E', 'E',
 'banda_propia', TRUE, 'banda_propia'
FROM analog.validation_sites vs
WHERE vs.site_key = 'askja' OR vs.name = 'Askja / colada basáltica Vikrahraun 1961 (Islandia)'
ON CONFLICT (site_id, corrida) DO UPDATE SET
  delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at,
  banda_latitud = EXCLUDED.banda_latitud, banda_ganadora_marte = EXCLUDED.banda_ganadora_marte,
  banda_ganadora_luna = EXCLUDED.banda_ganadora_luna, modo_bandas = EXCLUDED.modo_bandas,
  acierto = EXCLUDED.acierto;
INSERT INTO analog.validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at, banda_latitud, banda_ganadora_marte, banda_ganadora_luna, modo_bandas, acierto, corrida)
SELECT vs.id, 0.2208, 0.1304, 'marte', 'ambos',
 'ANALOG/delta v1 banda_propia', timestamptz '2026-11-14T15:31:26-05:00', 'B', 'B', 'B',
 'banda_propia', FALSE, 'banda_propia'
FROM analog.validation_sites vs
WHERE vs.site_key = 'mauna_kea' OR vs.name = 'Conos de ceniza de la cumbre de Mauna Kea (Hawái, EE. UU.)'
ON CONFLICT (site_id, corrida) DO UPDATE SET
  delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at,
  banda_latitud = EXCLUDED.banda_latitud, banda_ganadora_marte = EXCLUDED.banda_ganadora_marte,
  banda_ganadora_luna = EXCLUDED.banda_ganadora_luna, modo_bandas = EXCLUDED.modo_bandas,
  acierto = EXCLUDED.acierto;
INSERT INTO analog.validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at, banda_latitud, banda_ganadora_marte, banda_ganadora_luna, modo_bandas, acierto, corrida)
SELECT vs.id, 0.2901, 0.7082, 'marte', 'marte',
 'ANALOG/delta v1 banda_propia', timestamptz '2026-11-14T15:31:26-05:00', 'F', 'F', 'F',
 'banda_propia', TRUE, 'banda_propia'
FROM analog.validation_sites vs
WHERE vs.site_key = 'sverrefjell' OR vs.name = 'Sverrefjell, complejo volcánico de Bockfjorden (Svalbard, Noruega)'
ON CONFLICT (site_id, corrida) DO UPDATE SET
  delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at,
  banda_latitud = EXCLUDED.banda_latitud, banda_ganadora_marte = EXCLUDED.banda_ganadora_marte,
  banda_ganadora_luna = EXCLUDED.banda_ganadora_luna, modo_bandas = EXCLUDED.modo_bandas,
  acierto = EXCLUDED.acierto;
INSERT INTO analog.validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at, banda_latitud, banda_ganadora_marte, banda_ganadora_luna, modo_bandas, acierto, corrida)
SELECT vs.id, 0.9136, 0.7915, 'ambos', 'ambos',
 'ANALOG/delta v1 banda_propia', timestamptz '2026-11-14T15:31:26-05:00', 'B', 'B', 'B',
 'banda_propia', TRUE, 'banda_propia'
FROM analog.validation_sites vs
WHERE vs.site_key = 'timanfaya' OR vs.name = 'Parque Nacional de Timanfaya, Lanzarote (España)'
ON CONFLICT (site_id, corrida) DO UPDATE SET
  delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at,
  banda_latitud = EXCLUDED.banda_latitud, banda_ganadora_marte = EXCLUDED.banda_ganadora_marte,
  banda_ganadora_luna = EXCLUDED.banda_ganadora_luna, modo_bandas = EXCLUDED.modo_bandas,
  acierto = EXCLUDED.acierto;
INSERT INTO analog.validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at, banda_latitud, banda_ganadora_marte, banda_ganadora_luna, modo_bandas, acierto, corrida)
SELECT vs.id, 0.9527, 0.5109, 'marte', 'luna',
 'ANALOG/delta v1 banda_propia', timestamptz '2026-11-14T15:31:26-05:00', 'C', 'C', 'C',
 'banda_propia', FALSE, 'banda_propia'
FROM analog.validation_sites vs
WHERE vs.site_key = 'meteor_crater' OR vs.name = 'Meteor Crater (Barringer), Arizona (EE. UU.)'
ON CONFLICT (site_id, corrida) DO UPDATE SET
  delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at,
  banda_latitud = EXCLUDED.banda_latitud, banda_ganadora_marte = EXCLUDED.banda_ganadora_marte,
  banda_ganadora_luna = EXCLUDED.banda_ganadora_luna, modo_bandas = EXCLUDED.modo_bandas,
  acierto = EXCLUDED.acierto;
INSERT INTO analog.validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at, banda_latitud, banda_ganadora_marte, banda_ganadora_luna, modo_bandas, acierto, corrida)
SELECT vs.id, 0.9374, 0.5465, 'marte', 'ambos',
 'ANALOG/delta v1 banda_propia', timestamptz '2026-11-14T15:31:26-05:00', 'C', 'C', 'C',
 'banda_propia', FALSE, 'banda_propia'
FROM analog.validation_sites vs
WHERE vs.site_key = 'sp_mountain' OR vs.name = 'S P Mountain (S P Crater), campo volcánico de San Francisco, Arizona (EE. UU.)'
ON CONFLICT (site_id, corrida) DO UPDATE SET
  delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at,
  banda_latitud = EXCLUDED.banda_latitud, banda_ganadora_marte = EXCLUDED.banda_ganadora_marte,
  banda_ganadora_luna = EXCLUDED.banda_ganadora_luna, modo_bandas = EXCLUDED.modo_bandas,
  acierto = EXCLUDED.acierto;
INSERT INTO analog.validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at, banda_latitud, banda_ganadora_marte, banda_ganadora_luna, modo_bandas, acierto, corrida)
SELECT vs.id, 0.9533, 0.5372, 'marte', 'luna',
 'ANALOG/delta v1 banda_propia', timestamptz '2026-11-14T15:31:26-05:00', 'C', 'C', 'C',
 'banda_propia', FALSE, 'banda_propia'
FROM analog.validation_sites vs
WHERE vs.site_key = 'inferno_chasm' OR vs.name = 'Inferno Chasm, llanura de Snake River / entorno de Craters of the Moon, Idaho (EE. UU.)'
ON CONFLICT (site_id, corrida) DO UPDATE SET
  delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at,
  banda_latitud = EXCLUDED.banda_latitud, banda_ganadora_marte = EXCLUDED.banda_ganadora_marte,
  banda_ganadora_luna = EXCLUDED.banda_ganadora_luna, modo_bandas = EXCLUDED.modo_bandas,
  acierto = EXCLUDED.acierto;
INSERT INTO analog.validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at, banda_latitud, banda_ganadora_marte, banda_ganadora_luna, modo_bandas, acierto, corrida)
SELECT vs.id, 0.9819, 0.7465, 'marte', 'ninguno',
 'ANALOG/delta v1 banda_propia', timestamptz '2026-11-14T15:31:26-05:00', 'A', 'A', 'A',
 'banda_propia', FALSE, 'banda_propia'
FROM analog.validation_sites vs
WHERE vs.site_key = 'tapajos' OR vs.name = 'FLONA Tapajós, torre LBA km 67 (BR-Sa1), Amazonía (Brasil)'
ON CONFLICT (site_id, corrida) DO UPDATE SET
  delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at,
  banda_latitud = EXCLUDED.banda_latitud, banda_ganadora_marte = EXCLUDED.banda_ganadora_marte,
  banda_ganadora_luna = EXCLUDED.banda_ganadora_luna, modo_bandas = EXCLUDED.modo_bandas,
  acierto = EXCLUDED.acierto;
INSERT INTO analog.validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at, banda_latitud, banda_ganadora_marte, banda_ganadora_luna, modo_bandas, acierto, corrida)
SELECT vs.id, 0.9667, 0.6294, 'marte', 'ninguno',
 'ANALOG/delta v1 banda_propia', timestamptz '2026-11-14T15:31:26-05:00', 'C', 'C', 'C',
 'banda_propia', FALSE, 'banda_propia'
FROM analog.validation_sites vs
WHERE vs.site_key = 'bondville' OR vs.name = 'Bondville, Illinois (US-Bo1), llanura agrícola (EE. UU.)'
ON CONFLICT (site_id, corrida) DO UPDATE SET
  delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at,
  banda_latitud = EXCLUDED.banda_latitud, banda_ganadora_marte = EXCLUDED.banda_ganadora_marte,
  banda_ganadora_luna = EXCLUDED.banda_ganadora_luna, modo_bandas = EXCLUDED.modo_bandas,
  acierto = EXCLUDED.acierto;
INSERT INTO analog.validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at, banda_latitud, banda_ganadora_marte, banda_ganadora_luna, modo_bandas, acierto, corrida)
SELECT vs.id, 0.9711, 0.7096, 'marte', 'ninguno',
 'ANALOG/delta v1 banda_propia', timestamptz '2026-11-14T15:31:26-05:00', 'C', 'C', 'C',
 'banda_propia', FALSE, 'banda_propia'
FROM analog.validation_sites vs
WHERE vs.site_key = 'harvard_forest' OR vs.name = 'Harvard Forest EMS (US-Ha1), Massachusetts (EE. UU.)'
ON CONFLICT (site_id, corrida) DO UPDATE SET
  delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at,
  banda_latitud = EXCLUDED.banda_latitud, banda_ganadora_marte = EXCLUDED.banda_ganadora_marte,
  banda_ganadora_luna = EXCLUDED.banda_ganadora_luna, modo_bandas = EXCLUDED.modo_bandas,
  acierto = EXCLUDED.acierto;
INSERT INTO analog.validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at, banda_latitud, banda_ganadora_marte, banda_ganadora_luna, modo_bandas, acierto, corrida)
SELECT vs.id, 0.8995, 0.6836, 'marte', 'ninguno',
 'ANALOG/delta v1 banda_propia', timestamptz '2026-11-14T15:31:26-05:00', 'C', 'C', 'C',
 'banda_propia', FALSE, 'banda_propia'
FROM analog.validation_sites vs
WHERE vs.site_key = 'tumbarumba' OR vs.name = 'Tumbarumba (AU-Tum), Nueva Gales del Sur (Australia)'
ON CONFLICT (site_id, corrida) DO UPDATE SET
  delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at,
  banda_latitud = EXCLUDED.banda_latitud, banda_ganadora_marte = EXCLUDED.banda_ganadora_marte,
  banda_ganadora_luna = EXCLUDED.banda_ganadora_luna, modo_bandas = EXCLUDED.modo_bandas,
  acierto = EXCLUDED.acierto;
INSERT INTO analog.validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at, banda_latitud, banda_ganadora_marte, banda_ganadora_luna, modo_bandas, acierto, corrida)
SELECT vs.id, 0.8764, 0.7213, 'marte', 'ninguno',
 'ANALOG/delta v1 banda_propia', timestamptz '2026-11-14T15:31:26-05:00', 'D', 'D', 'D',
 'banda_propia', FALSE, 'banda_propia'
FROM analog.validation_sites vs
WHERE vs.site_key = 'hainich' OR vs.name = 'Hainich (DE-Hai), Turingia (Alemania)'
ON CONFLICT (site_id, corrida) DO UPDATE SET
  delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at,
  banda_latitud = EXCLUDED.banda_latitud, banda_ganadora_marte = EXCLUDED.banda_ganadora_marte,
  banda_ganadora_luna = EXCLUDED.banda_ganadora_luna, modo_bandas = EXCLUDED.modo_bandas,
  acierto = EXCLUDED.acierto;
INSERT INTO analog.validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at, banda_latitud, banda_ganadora_marte, banda_ganadora_luna, modo_bandas, acierto, corrida)
SELECT vs.id, 0.9498, 0.5983, 'marte', 'ninguno',
 'ANALOG/delta v1 banda_propia', timestamptz '2026-11-14T15:31:26-05:00', 'E', 'E', 'E',
 'banda_propia', FALSE, 'banda_propia'
FROM analog.validation_sites vs
WHERE vs.site_key = 'hyytiala' OR vs.name = 'Hyytiälä / SMEAR II (FI-Hyy), Finlandia'
ON CONFLICT (site_id, corrida) DO UPDATE SET
  delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at,
  banda_latitud = EXCLUDED.banda_latitud, banda_ganadora_marte = EXCLUDED.banda_ganadora_marte,
  banda_ganadora_luna = EXCLUDED.banda_ganadora_luna, modo_bandas = EXCLUDED.modo_bandas,
  acierto = EXCLUDED.acierto;
INSERT INTO analog.validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at, banda_latitud, banda_ganadora_marte, banda_ganadora_luna, modo_bandas, acierto, corrida)
SELECT vs.id, NULL, NULL, NULL, 'marte',
 'ANALOG/delta v1 banda_propia', timestamptz '2026-11-14T15:31:26-05:00', 'C', NULL, NULL,
 'banda_propia', NULL, 'banda_propia'
FROM analog.validation_sites vs
WHERE vs.site_key = 'rio_tinto' OR vs.name = 'Peña de Hierro / cabecera del Río Tinto (Huelva, España)'
ON CONFLICT (site_id, corrida) DO UPDATE SET
  delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at,
  banda_latitud = EXCLUDED.banda_latitud, banda_ganadora_marte = EXCLUDED.banda_ganadora_marte,
  banda_ganadora_luna = EXCLUDED.banda_ganadora_luna, modo_bandas = EXCLUDED.modo_bandas,
  acierto = EXCLUDED.acierto;
INSERT INTO analog.validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at, banda_latitud, banda_ganadora_marte, banda_ganadora_luna, modo_bandas, acierto, corrida)
SELECT vs.id, NULL, NULL, NULL, 'luna',
 'ANALOG/delta v1 banda_propia', timestamptz '2026-11-14T15:31:26-05:00', 'D', NULL, NULL,
 'banda_propia', NULL, 'banda_propia'
FROM analog.validation_sites vs
WHERE vs.site_key = 'ries' OR vs.name = 'Ries (Nördlinger Ries), Alemania'
ON CONFLICT (site_id, corrida) DO UPDATE SET
  delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at,
  banda_latitud = EXCLUDED.banda_latitud, banda_ganadora_marte = EXCLUDED.banda_ganadora_marte,
  banda_ganadora_luna = EXCLUDED.banda_ganadora_luna, modo_bandas = EXCLUDED.modo_bandas,
  acierto = EXCLUDED.acierto;
INSERT INTO analog.validation_results (site_id, delta_mars, delta_moon, predicted_class, known_class, metric_version, computed_at, banda_latitud, banda_ganadora_marte, banda_ganadora_luna, modo_bandas, acierto, corrida)
SELECT vs.id, NULL, NULL, NULL, 'luna',
 'ANALOG/delta v1 banda_propia', timestamptz '2026-11-14T15:31:26-05:00', 'D', NULL, NULL,
 'banda_propia', NULL, 'banda_propia'
FROM analog.validation_sites vs
WHERE vs.site_key = 'sudbury' OR vs.name = 'Cuenca de Sudbury, Ontario (Canadá)'
ON CONFLICT (site_id, corrida) DO UPDATE SET
  delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  predicted_class = EXCLUDED.predicted_class, known_class = EXCLUDED.known_class,
  metric_version = EXCLUDED.metric_version, computed_at = EXCLUDED.computed_at,
  banda_latitud = EXCLUDED.banda_latitud, banda_ganadora_marte = EXCLUDED.banda_ganadora_marte,
  banda_ganadora_luna = EXCLUDED.banda_ganadora_luna, modo_bandas = EXCLUDED.modo_bandas,
  acierto = EXCLUDED.acierto;

-- Metadatos de rásteres (no se cargan los 453 375 puntos aquí).
INSERT INTO analog.ecuador_rasters (layer, path, kind, resolucion_m, west, north, east, south, nodata, label, in_index, frozen_at, sha256, area, corrida)
VALUES ('delta_marte_banda_propia', '/productos/delta_marte.tif', 'cog', 1000, -92.007, 1.7010000000000076, -74.99700000000001, -5.102999999999992,
 -9999, 'δ Marte, corrida oficial banda_propia, recorte completo', TRUE, timestamptz '2026-11-14T15:31:26-05:00', '1fac4f7418cca4c28462ecc4354aba2e64352b551a85c4529c7ffc62d7d0d011', 'completo', 'banda_propia')
ON CONFLICT (layer) DO UPDATE SET
  path = EXCLUDED.path, kind = EXCLUDED.kind, resolucion_m = EXCLUDED.resolucion_m,
  west = EXCLUDED.west, north = EXCLUDED.north, east = EXCLUDED.east, south = EXCLUDED.south,
  nodata = EXCLUDED.nodata, label = EXCLUDED.label, frozen_at = EXCLUDED.frozen_at,
  sha256 = EXCLUDED.sha256, area = EXCLUDED.area, corrida = EXCLUDED.corrida;
INSERT INTO analog.ecuador_rasters (layer, path, kind, resolucion_m, west, north, east, south, nodata, label, in_index, frozen_at, sha256, area, corrida)
VALUES ('delta_luna_banda_propia', '/productos/delta_luna.tif', 'cog', 1000, -92.007, 1.7010000000000076, -74.99700000000001, -5.102999999999992,
 -9999, 'δ Luna, corrida oficial banda_propia, recorte completo', TRUE, timestamptz '2026-11-14T15:31:26-05:00', 'daf00ed5e74e6308f2a9f46a4077075e335726c278e901c1a18bef24a67372c7', 'completo', 'banda_propia')
ON CONFLICT (layer) DO UPDATE SET
  path = EXCLUDED.path, kind = EXCLUDED.kind, resolucion_m = EXCLUDED.resolucion_m,
  west = EXCLUDED.west, north = EXCLUDED.north, east = EXCLUDED.east, south = EXCLUDED.south,
  nodata = EXCLUDED.nodata, label = EXCLUDED.label, frozen_at = EXCLUDED.frozen_at,
  sha256 = EXCLUDED.sha256, area = EXCLUDED.area, corrida = EXCLUDED.corrida;
INSERT INTO analog.ecuador_rasters (layer, path, kind, resolucion_m, west, north, east, south, nodata, label, in_index, frozen_at, sha256, area, corrida)
VALUES ('clases_banda_propia', '/productos/clases.tif', 'cog', 1000, -92.007, 1.7010000000000076, -74.99700000000001, -5.102999999999992,
 -1, 'Clases v1 (secundario; no usar como inventario)', TRUE, timestamptz '2026-11-14T15:31:26-05:00', 'c00ec958e12dfb55cc46fad62306328670b79760102c026a3365a779378a89a9', 'completo', 'banda_propia')
ON CONFLICT (layer) DO UPDATE SET
  path = EXCLUDED.path, kind = EXCLUDED.kind, resolucion_m = EXCLUDED.resolucion_m,
  west = EXCLUDED.west, north = EXCLUDED.north, east = EXCLUDED.east, south = EXCLUDED.south,
  nodata = EXCLUDED.nodata, label = EXCLUDED.label, frozen_at = EXCLUDED.frozen_at,
  sha256 = EXCLUDED.sha256, area = EXCLUDED.area, corrida = EXCLUDED.corrida;
INSERT INTO analog.ecuador_rasters (layer, path, kind, resolucion_m, west, north, east, south, nodata, label, in_index, frozen_at, sha256, area, corrida)
VALUES ('delta_marte_galapagos_banda_propia', '/productos/galapagos/delta_marte.tif', 'cog', 1000, -91.80000000000001, 0.7830000000000077, -89.11800000000001, -1.5479999999999923,
 -9999, 'δ Marte galapagos', TRUE, timestamptz '2026-11-14T15:31:26-05:00', '701f20dc173b4de6e28be5934a1b543397bb9243273f3385bc6272fe117e6359', 'galapagos', 'banda_propia')
ON CONFLICT (layer) DO UPDATE SET
  path = EXCLUDED.path, kind = EXCLUDED.kind, resolucion_m = EXCLUDED.resolucion_m,
  west = EXCLUDED.west, north = EXCLUDED.north, east = EXCLUDED.east, south = EXCLUDED.south,
  nodata = EXCLUDED.nodata, label = EXCLUDED.label, frozen_at = EXCLUDED.frozen_at,
  sha256 = EXCLUDED.sha256, area = EXCLUDED.area, corrida = EXCLUDED.corrida;
INSERT INTO analog.ecuador_rasters (layer, path, kind, resolucion_m, west, north, east, south, nodata, label, in_index, frozen_at, sha256, area, corrida)
VALUES ('delta_luna_galapagos_banda_propia', '/productos/galapagos/delta_luna.tif', 'cog', 1000, -91.80000000000001, 0.7830000000000077, -89.11800000000001, -1.5479999999999923,
 -9999, 'δ Luna galapagos', TRUE, timestamptz '2026-11-14T15:31:26-05:00', '8b8a12829f60b96d6ca733454b096df7d5e99e4fc73b79744982d6218ba89355', 'galapagos', 'banda_propia')
ON CONFLICT (layer) DO UPDATE SET
  path = EXCLUDED.path, kind = EXCLUDED.kind, resolucion_m = EXCLUDED.resolucion_m,
  west = EXCLUDED.west, north = EXCLUDED.north, east = EXCLUDED.east, south = EXCLUDED.south,
  nodata = EXCLUDED.nodata, label = EXCLUDED.label, frozen_at = EXCLUDED.frozen_at,
  sha256 = EXCLUDED.sha256, area = EXCLUDED.area, corrida = EXCLUDED.corrida;
INSERT INTO analog.ecuador_rasters (layer, path, kind, resolucion_m, west, north, east, south, nodata, label, in_index, frozen_at, sha256, area, corrida)
VALUES ('clases_galapagos_banda_propia', '/productos/galapagos/clases.tif', 'cog', 1000, -91.80000000000001, 0.7830000000000077, -89.11800000000001, -1.5479999999999923,
 -1, 'Clases galapagos (secundario)', TRUE, timestamptz '2026-11-14T15:31:26-05:00', '796877d9a4910fe9e0023c99da2b319cc8e506210b5428ad12067be29f2ba767', 'galapagos', 'banda_propia')
ON CONFLICT (layer) DO UPDATE SET
  path = EXCLUDED.path, kind = EXCLUDED.kind, resolucion_m = EXCLUDED.resolucion_m,
  west = EXCLUDED.west, north = EXCLUDED.north, east = EXCLUDED.east, south = EXCLUDED.south,
  nodata = EXCLUDED.nodata, label = EXCLUDED.label, frozen_at = EXCLUDED.frozen_at,
  sha256 = EXCLUDED.sha256, area = EXCLUDED.area, corrida = EXCLUDED.corrida;
INSERT INTO analog.ecuador_rasters (layer, path, kind, resolucion_m, west, north, east, south, nodata, label, in_index, frozen_at, sha256, area, corrida)
VALUES ('delta_marte_ecuador_continental_banda_propia', '/productos/ecuador_continental/delta_marte.tif', 'cog', 1000, -81.25200000000001, 1.7010000000000076, -74.99700000000001, -5.102999999999992,
 -9999, 'δ Marte ecuador_continental', TRUE, timestamptz '2026-11-14T15:31:26-05:00', 'b87cdb640a9ad1d901f11648224c1c3e9057d6fbe2d589244f22ca26070f07fd', 'ecuador_continental', 'banda_propia')
ON CONFLICT (layer) DO UPDATE SET
  path = EXCLUDED.path, kind = EXCLUDED.kind, resolucion_m = EXCLUDED.resolucion_m,
  west = EXCLUDED.west, north = EXCLUDED.north, east = EXCLUDED.east, south = EXCLUDED.south,
  nodata = EXCLUDED.nodata, label = EXCLUDED.label, frozen_at = EXCLUDED.frozen_at,
  sha256 = EXCLUDED.sha256, area = EXCLUDED.area, corrida = EXCLUDED.corrida;
INSERT INTO analog.ecuador_rasters (layer, path, kind, resolucion_m, west, north, east, south, nodata, label, in_index, frozen_at, sha256, area, corrida)
VALUES ('delta_luna_ecuador_continental_banda_propia', '/productos/ecuador_continental/delta_luna.tif', 'cog', 1000, -81.25200000000001, 1.7010000000000076, -74.99700000000001, -5.102999999999992,
 -9999, 'δ Luna ecuador_continental', TRUE, timestamptz '2026-11-14T15:31:26-05:00', '71ea93857cc559ed2374a3a9305f7b8bd818bf5ba55f11351daf2b1508fcca01', 'ecuador_continental', 'banda_propia')
ON CONFLICT (layer) DO UPDATE SET
  path = EXCLUDED.path, kind = EXCLUDED.kind, resolucion_m = EXCLUDED.resolucion_m,
  west = EXCLUDED.west, north = EXCLUDED.north, east = EXCLUDED.east, south = EXCLUDED.south,
  nodata = EXCLUDED.nodata, label = EXCLUDED.label, frozen_at = EXCLUDED.frozen_at,
  sha256 = EXCLUDED.sha256, area = EXCLUDED.area, corrida = EXCLUDED.corrida;
INSERT INTO analog.ecuador_rasters (layer, path, kind, resolucion_m, west, north, east, south, nodata, label, in_index, frozen_at, sha256, area, corrida)
VALUES ('clases_ecuador_continental_banda_propia', '/productos/ecuador_continental/clases.tif', 'cog', 1000, -81.25200000000001, 1.7010000000000076, -74.99700000000001, -5.102999999999992,
 -1, 'Clases ecuador_continental (secundario)', TRUE, timestamptz '2026-11-14T15:31:26-05:00', 'fd6c2bac0ba5c124ee5c0ffc4eca9ae2c629ccb7b00899954b5d0b724d21eea7', 'ecuador_continental', 'banda_propia')
ON CONFLICT (layer) DO UPDATE SET
  path = EXCLUDED.path, kind = EXCLUDED.kind, resolucion_m = EXCLUDED.resolucion_m,
  west = EXCLUDED.west, north = EXCLUDED.north, east = EXCLUDED.east, south = EXCLUDED.south,
  nodata = EXCLUDED.nodata, label = EXCLUDED.label, frozen_at = EXCLUDED.frozen_at,
  sha256 = EXCLUDED.sha256, area = EXCLUDED.area, corrida = EXCLUDED.corrida;

-- Zonas prioritarias de la corrida oficial (id + corrida vía id sufijo).
INSERT INTO analog.priority_zones (id, name, lat, lon, geom, class, delta_mars, delta_moon, elevation_m, slope_deg, roughness_tri, area, corrida)
VALUES ('chimborazo__banda_propia', 'Chimborazo (arenal y páramo)', -1.47, -78.82,
 ST_SetSRID(ST_MakePoint(-78.82, -1.47), 4326),
 'ninguno', 0.0, 0.0,
 6018.8, 10.08, 416.59,
 'ecuador_continental', 'banda_propia')
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name, lat = EXCLUDED.lat, lon = EXCLUDED.lon, geom = EXCLUDED.geom,
  class = EXCLUDED.class, delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  elevation_m = EXCLUDED.elevation_m, slope_deg = EXCLUDED.slope_deg, roughness_tri = EXCLUDED.roughness_tri,
  area = EXCLUDED.area, corrida = EXCLUDED.corrida;
INSERT INTO analog.priority_zones (id, name, lat, lon, geom, class, delta_mars, delta_moon, elevation_m, slope_deg, roughness_tri, area, corrida)
VALUES ('cotopaxi__banda_propia', 'Cotopaxi (páramo)', -0.68, -78.44,
 ST_SetSRID(ST_MakePoint(-78.44, -0.68), 4326),
 'ninguno', 0.0, 0.0,
 5589.7, 10.87, 355.8,
 'ecuador_continental', 'banda_propia')
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name, lat = EXCLUDED.lat, lon = EXCLUDED.lon, geom = EXCLUDED.geom,
  class = EXCLUDED.class, delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  elevation_m = EXCLUDED.elevation_m, slope_deg = EXCLUDED.slope_deg, roughness_tri = EXCLUDED.roughness_tri,
  area = EXCLUDED.area, corrida = EXCLUDED.corrida;
INSERT INTO analog.priority_zones (id, name, lat, lon, geom, class, delta_mars, delta_moon, elevation_m, slope_deg, roughness_tri, area, corrida)
VALUES ('antisana__banda_propia', 'Antisana', -0.48, -78.14,
 ST_SetSRID(ST_MakePoint(-78.14, -0.48), 4326),
 'ninguno', 0.0, 0.0,
 5501.4, 10.12, 378.02,
 'ecuador_continental', 'banda_propia')
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name, lat = EXCLUDED.lat, lon = EXCLUDED.lon, geom = EXCLUDED.geom,
  class = EXCLUDED.class, delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  elevation_m = EXCLUDED.elevation_m, slope_deg = EXCLUDED.slope_deg, roughness_tri = EXCLUDED.roughness_tri,
  area = EXCLUDED.area, corrida = EXCLUDED.corrida;
INSERT INTO analog.priority_zones (id, name, lat, lon, geom, class, delta_mars, delta_moon, elevation_m, slope_deg, roughness_tri, area, corrida)
VALUES ('el_altar__banda_propia', 'El Altar', -1.67, -78.41,
 ST_SetSRID(ST_MakePoint(-78.41, -1.67), 4326),
 'marte', 0.4939, 0.1469,
 4740.2, 7.52, 118.69,
 'ecuador_continental', 'banda_propia')
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name, lat = EXCLUDED.lat, lon = EXCLUDED.lon, geom = EXCLUDED.geom,
  class = EXCLUDED.class, delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  elevation_m = EXCLUDED.elevation_m, slope_deg = EXCLUDED.slope_deg, roughness_tri = EXCLUDED.roughness_tri,
  area = EXCLUDED.area, corrida = EXCLUDED.corrida;
INSERT INTO analog.priority_zones (id, name, lat, lon, geom, class, delta_mars, delta_moon, elevation_m, slope_deg, roughness_tri, area, corrida)
VALUES ('quilotoa__banda_propia', 'Quilotoa', -0.85, -78.9,
 ST_SetSRID(ST_MakePoint(-78.9, -0.85), 4326),
 'marte', 0.7869, 0.4004,
 3620.3, 0.53, 66.38,
 'ecuador_continental', 'banda_propia')
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name, lat = EXCLUDED.lat, lon = EXCLUDED.lon, geom = EXCLUDED.geom,
  class = EXCLUDED.class, delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  elevation_m = EXCLUDED.elevation_m, slope_deg = EXCLUDED.slope_deg, roughness_tri = EXCLUDED.roughness_tri,
  area = EXCLUDED.area, corrida = EXCLUDED.corrida;
INSERT INTO analog.priority_zones (id, name, lat, lon, geom, class, delta_mars, delta_moon, elevation_m, slope_deg, roughness_tri, area, corrida)
VALUES ('fernandina__banda_propia', 'Fernandina (Galápagos)', -0.37, -91.55,
 ST_SetSRID(ST_MakePoint(-91.55, -0.37), 4326),
 'ninguno', 0.0, 0.0,
 621.5, 13.66, 236.1,
 'galapagos', 'banda_propia')
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name, lat = EXCLUDED.lat, lon = EXCLUDED.lon, geom = EXCLUDED.geom,
  class = EXCLUDED.class, delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  elevation_m = EXCLUDED.elevation_m, slope_deg = EXCLUDED.slope_deg, roughness_tri = EXCLUDED.roughness_tri,
  area = EXCLUDED.area, corrida = EXCLUDED.corrida;
INSERT INTO analog.priority_zones (id, name, lat, lon, geom, class, delta_mars, delta_moon, elevation_m, slope_deg, roughness_tri, area, corrida)
VALUES ('cayambe__banda_propia', 'Cayambe', 0.03, -77.99,
 ST_SetSRID(ST_MakePoint(-77.99, 0.03), 4326),
 'ninguno', 0.0, 0.0,
 5321.4, 18.43, 263.49,
 'ecuador_continental', 'banda_propia')
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name, lat = EXCLUDED.lat, lon = EXCLUDED.lon, geom = EXCLUDED.geom,
  class = EXCLUDED.class, delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  elevation_m = EXCLUDED.elevation_m, slope_deg = EXCLUDED.slope_deg, roughness_tri = EXCLUDED.roughness_tri,
  area = EXCLUDED.area, corrida = EXCLUDED.corrida;
INSERT INTO analog.priority_zones (id, name, lat, lon, geom, class, delta_mars, delta_moon, elevation_m, slope_deg, roughness_tri, area, corrida)
VALUES ('sincholagua__banda_propia', 'Sincholagua', -0.54, -78.37,
 ST_SetSRID(ST_MakePoint(-78.37, -0.54), 4326),
 'marte', 0.5238, 0.1909,
 4448.2, 5.62, 124.96,
 'ecuador_continental', 'banda_propia')
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name, lat = EXCLUDED.lat, lon = EXCLUDED.lon, geom = EXCLUDED.geom,
  class = EXCLUDED.class, delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  elevation_m = EXCLUDED.elevation_m, slope_deg = EXCLUDED.slope_deg, roughness_tri = EXCLUDED.roughness_tri,
  area = EXCLUDED.area, corrida = EXCLUDED.corrida;
INSERT INTO analog.priority_zones (id, name, lat, lon, geom, class, delta_mars, delta_moon, elevation_m, slope_deg, roughness_tri, area, corrida)
VALUES ('max_mars_ecuador_continental__banda_propia', 'Máxima similitud a Marte', -4.9275, -80.9685,
 ST_SetSRID(ST_MakePoint(-80.9685, -4.9275), 4326),
 'marte', 0.9924, 0.761,
 19.1, 0.76, 11.67,
 'ecuador_continental', 'banda_propia')
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name, lat = EXCLUDED.lat, lon = EXCLUDED.lon, geom = EXCLUDED.geom,
  class = EXCLUDED.class, delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  elevation_m = EXCLUDED.elevation_m, slope_deg = EXCLUDED.slope_deg, roughness_tri = EXCLUDED.roughness_tri,
  area = EXCLUDED.area, corrida = EXCLUDED.corrida;
INSERT INTO analog.priority_zones (id, name, lat, lon, geom, class, delta_mars, delta_moon, elevation_m, slope_deg, roughness_tri, area, corrida)
VALUES ('max_moon_ecuador_continental__banda_propia', 'Máxima similitud a la Luna', -4.4145, -81.2385,
 ST_SetSRID(ST_MakePoint(-81.2385, -4.4145), 4326),
 'ambos', 0.8269, 0.9593,
 119.5, 3.49, 54.49,
 'ecuador_continental', 'banda_propia')
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name, lat = EXCLUDED.lat, lon = EXCLUDED.lon, geom = EXCLUDED.geom,
  class = EXCLUDED.class, delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  elevation_m = EXCLUDED.elevation_m, slope_deg = EXCLUDED.slope_deg, roughness_tri = EXCLUDED.roughness_tri,
  area = EXCLUDED.area, corrida = EXCLUDED.corrida;
INSERT INTO analog.priority_zones (id, name, lat, lon, geom, class, delta_mars, delta_moon, elevation_m, slope_deg, roughness_tri, area, corrida)
VALUES ('max_mars_galapagos__banda_propia', 'Máxima similitud a Marte (Galápagos)', -1.3815, -89.6895,
 ST_SetSRID(ST_MakePoint(-89.6895, -1.3815), 4326),
 'marte', 0.9705, 0.7588,
 127.5, 0.9, 16.01,
 'galapagos', 'banda_propia')
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name, lat = EXCLUDED.lat, lon = EXCLUDED.lon, geom = EXCLUDED.geom,
  class = EXCLUDED.class, delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  elevation_m = EXCLUDED.elevation_m, slope_deg = EXCLUDED.slope_deg, roughness_tri = EXCLUDED.roughness_tri,
  area = EXCLUDED.area, corrida = EXCLUDED.corrida;
INSERT INTO analog.priority_zones (id, name, lat, lon, geom, class, delta_mars, delta_moon, elevation_m, slope_deg, roughness_tri, area, corrida)
VALUES ('max_moon_galapagos__banda_propia', 'Máxima similitud a la Luna (Galápagos)', -1.3005, -90.4815,
 ST_SetSRID(ST_MakePoint(-90.4815, -1.3005), 4326),
 'ambos', 0.8222, 0.8777,
 124.7, 3.75, 52.71,
 'galapagos', 'banda_propia')
ON CONFLICT (id) DO UPDATE SET
  name = EXCLUDED.name, lat = EXCLUDED.lat, lon = EXCLUDED.lon, geom = EXCLUDED.geom,
  class = EXCLUDED.class, delta_mars = EXCLUDED.delta_mars, delta_moon = EXCLUDED.delta_moon,
  elevation_m = EXCLUDED.elevation_m, slope_deg = EXCLUDED.slope_deg, roughness_tri = EXCLUDED.roughness_tri,
  area = EXCLUDED.area, corrida = EXCLUDED.corrida;

COMMIT;
