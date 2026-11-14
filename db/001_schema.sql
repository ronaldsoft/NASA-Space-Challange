-- =============================================================================
-- Índice ANALOG/delta — esquema (Supabase / PostGIS)
-- NASA Space Apps 2026 · Ecuador
-- Documento rector: proyecto_ronald.txt
-- =============================================================================
-- Aplicar en este orden: 001_schema.sql → 002_rpc.sql → 003_seed_mock.sql
--
-- El índice compara condiciones de SUPERFICIE (latitud, elevación, pendiente,
-- rugosidad). Cero variables meteorológicas. Albedo e inercia térmica quedan
-- documentados con en_indice = false hasta que Expertos confirme que son
-- comparables en los tres cuerpos.
--
-- SRID 4326 es NOMINAL: lon/lat planetocéntricos en Luna y Marte, WGS 84 en
-- la Tierra. La columna `body` desambigua. No calcular distancias terrestres
-- entre cuerpos distintos.
--
-- Grilla objetivo: geográfica común, 1 km. Pendiente y rugosidad se
-- recalculan sobre el DEM ya remuestreado.
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS bodies (
  id   text PRIMARY KEY,
  name text NOT NULL,
  CONSTRAINT bodies_id_check CHECK (id IN ('moon', 'mars', 'earth'))
);

INSERT INTO bodies (id, name) VALUES
  ('moon',  'Luna'),
  ('mars',  'Marte'),
  ('earth', 'Tierra')
ON CONFLICT (id) DO NOTHING;

-- -----------------------------------------------------------------------------
-- variables
-- Unidad, fuente por cuerpo, resolución nativa por cuerpo, valor no-dato,
-- si entra al índice, notas (incluido el datum de elevación).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS variables (
  name                         text PRIMARY KEY,
  unit                         text NOT NULL,
  source_per_body              jsonb NOT NULL DEFAULT '{}'::jsonb,
  native_resolution_m_per_body jsonb NOT NULL DEFAULT '{}'::jsonb,
  nodata_value                 double precision,
  in_index                     boolean NOT NULL DEFAULT false,
  notes                        text,
  elevation_datum_per_body     jsonb
);

COMMENT ON TABLE variables IS
  'Catálogo de variables. Solo las filas con in_index = true entran al ANALOG/delta. '
  'Ninguna variable meteorológica debe tener in_index = true.';
COMMENT ON COLUMN variables.elevation_datum_per_body IS
  'Para elevation: Tierra geoide EGM2008 (Copernicus DEM GLO-90), Marte areoide MOLA, '
  'Luna esfera de 1737.4 km.';
COMMENT ON COLUMN variables.in_index IS
  'false para albedo e inercia térmica hasta confirmación de Expertos.';

-- -----------------------------------------------------------------------------
-- cells
-- Celdas de la grilla común (1 km). En el MVP no se cargan todas las celdas
-- planetarias; sí las de validación, las zonas prioritarias y, si cabe, un
-- recorte de Ecuador.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cells (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  body            text NOT NULL REFERENCES bodies (id) ON DELETE RESTRICT,
  lat             double precision NOT NULL,
  lon             double precision NOT NULL,
  geom            geometry(Point, 4326),
  elevation_m     double precision,
  slope_deg       double precision,
  roughness_tri   double precision,
  albedo          double precision,
  thermal_inertia double precision,
  valid_mask      boolean NOT NULL DEFAULT true,
  CONSTRAINT cells_unique UNIQUE (body, lat, lon)
);

CREATE INDEX IF NOT EXISTS cells_geom_gist ON cells USING GIST (geom);
CREATE INDEX IF NOT EXISTS cells_body_idx ON cells (body);
CREATE INDEX IF NOT EXISTS cells_body_valid_idx ON cells (body, valid_mask);

COMMENT ON TABLE cells IS
  'Celdas de la grilla geográfica común. geom usa SRID 4326 nominal (ver encabezado).';

-- -----------------------------------------------------------------------------
-- std_params
-- Calculados SOLO sobre la referencia (moon | mars), congelados y aplicados
-- después a la Tierra. Nunca recalcular con validación ni con Ecuador.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS std_params (
  body_ref   text NOT NULL CHECK (body_ref IN ('moon', 'mars')),
  variable   text NOT NULL REFERENCES variables (name) ON DELETE RESTRICT,
  center     double precision NOT NULL,
  scale      double precision NOT NULL,
  method     text NOT NULL,
  frozen_at  timestamptz NOT NULL,
  PRIMARY KEY (body_ref, variable, method, frozen_at)
);

COMMENT ON TABLE std_params IS
  'Parámetros de estandarización congelados. body_ref es solo moon o mars.';

-- -----------------------------------------------------------------------------
-- signatures
-- Mediana e IQR por cuerpo, banda de latitud y variable.
-- Marte y Luna nunca mezclados.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS signatures (
  body      text NOT NULL CHECK (body IN ('moon', 'mars')),
  lat_band  text NOT NULL,
  variable  text NOT NULL REFERENCES variables (name) ON DELETE RESTRICT,
  median    double precision,
  q1        double precision,
  q3        double precision,
  n_cells   integer NOT NULL CHECK (n_cells >= 0),
  PRIMARY KEY (body, lat_band, variable)
);

CREATE INDEX IF NOT EXISTS signatures_body_band_idx ON signatures (body, lat_band);

COMMENT ON TABLE signatures IS
  'Firmas de referencia por banda de latitud. Marte y Luna no se mezclan.';

-- -----------------------------------------------------------------------------
-- validation_sites / validation_results
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS validation_sites (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name       text NOT NULL,
  lat        double precision NOT NULL,
  lon        double precision NOT NULL,
  geom       geometry(Point, 4326),
  buffer_km  double precision NOT NULL DEFAULT 10,
  label      text NOT NULL CHECK (label IN ('marciano', 'lunar', 'ambos', 'no_analogo')),
  source     text,
  cita       text,
  is_provisional boolean NOT NULL DEFAULT false,
  is_mock    boolean NOT NULL DEFAULT false,
  excluido_auc boolean NOT NULL DEFAULT false,
  coordenada_no_verificada boolean NOT NULL DEFAULT false
);

CREATE INDEX IF NOT EXISTS validation_sites_geom_gist ON validation_sites USING GIST (geom);
CREATE INDEX IF NOT EXISTS validation_sites_label_idx ON validation_sites (label);

CREATE TABLE IF NOT EXISTS validation_results (
  site_id         uuid PRIMARY KEY REFERENCES validation_sites (id) ON DELETE CASCADE,
  delta_mars      double precision,
  delta_moon      double precision,
  predicted_class text CHECK (predicted_class IN ('marte', 'luna', 'ambos', 'ninguno')),
  known_class     text CHECK (known_class IN ('marte', 'luna', 'ambos', 'ninguno')),
  metric_version  text,
  computed_at     timestamptz NOT NULL DEFAULT now(),
  banda_ganadora_marte text,
  banda_ganadora_luna text,
  modo_bandas     text
);

-- -----------------------------------------------------------------------------
-- thresholds  (un umbral por cuerpo, congelado en validación)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS thresholds (
  body       text NOT NULL CHECK (body IN ('moon', 'mars')),
  value      double precision NOT NULL,
  metric     text NOT NULL,
  d_max      double precision,
  sensitivity double precision,
  precision  double precision,
  auc        double precision,
  frozen_at  timestamptz NOT NULL,
  PRIMARY KEY (body, frozen_at)
);

COMMENT ON TABLE thresholds IS
  'Umbral de análogo fijado en validación y no reajustado en Ecuador.';

-- -----------------------------------------------------------------------------
-- ecuador_results (celdas o zonas) y referencia a rásteres
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ecuador_results (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  lat         double precision NOT NULL,
  lon         double precision NOT NULL,
  geom        geometry(Point, 4326),
  delta_mars  double precision,
  delta_moon  double precision,
  class       text NOT NULL CHECK (class IN ('marte', 'luna', 'ambos', 'ninguno')),
  valid_mask  boolean NOT NULL DEFAULT true,
  name        text,
  is_priority boolean NOT NULL DEFAULT false
);

CREATE INDEX IF NOT EXISTS ecuador_results_geom_gist ON ecuador_results USING GIST (geom);
CREATE INDEX IF NOT EXISTS ecuador_results_class_idx ON ecuador_results (class);

CREATE TABLE IF NOT EXISTS ecuador_rasters (
  layer        text PRIMARY KEY,
  path         text NOT NULL,
  kind         text NOT NULL, -- similitud | clase | interpretacion
  resolucion_m double precision,
  west         double precision,
  north        double precision,
  east         double precision,
  south        double precision,
  nodata       double precision,
  label        text,
  in_index     boolean NOT NULL DEFAULT true,
  frozen_at    timestamptz
);

COMMENT ON TABLE ecuador_rasters IS
  'Rutas a los rásteres precalculados de Ecuador (similitud, clases, clima). '
  'La capa de clima lleva in_index = false y la etiqueta de interpretación.';

-- -----------------------------------------------------------------------------
-- Lectura pública para el tablero (ajustar antes de habilitar escrituras)
-- -----------------------------------------------------------------------------
ALTER TABLE bodies             ENABLE ROW LEVEL SECURITY;
ALTER TABLE variables          ENABLE ROW LEVEL SECURITY;
ALTER TABLE cells              ENABLE ROW LEVEL SECURITY;
ALTER TABLE std_params         ENABLE ROW LEVEL SECURITY;
ALTER TABLE signatures         ENABLE ROW LEVEL SECURITY;
ALTER TABLE validation_sites   ENABLE ROW LEVEL SECURITY;
ALTER TABLE validation_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE thresholds         ENABLE ROW LEVEL SECURITY;
ALTER TABLE ecuador_results    ENABLE ROW LEVEL SECURITY;
ALTER TABLE ecuador_rasters    ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
  -- Políticas idempotentes
  PERFORM 1;
END $$;

DROP POLICY IF EXISTS bodies_public_read ON bodies;
DROP POLICY IF EXISTS variables_public_read ON variables;
DROP POLICY IF EXISTS cells_public_read ON cells;
DROP POLICY IF EXISTS std_params_public_read ON std_params;
DROP POLICY IF EXISTS signatures_public_read ON signatures;
DROP POLICY IF EXISTS validation_sites_public_read ON validation_sites;
DROP POLICY IF EXISTS validation_results_public_read ON validation_results;
DROP POLICY IF EXISTS thresholds_public_read ON thresholds;
DROP POLICY IF EXISTS ecuador_results_public_read ON ecuador_results;
DROP POLICY IF EXISTS ecuador_rasters_public_read ON ecuador_rasters;

CREATE POLICY bodies_public_read             ON bodies             FOR SELECT USING (true);
CREATE POLICY variables_public_read          ON variables          FOR SELECT USING (true);
CREATE POLICY cells_public_read              ON cells              FOR SELECT USING (true);
CREATE POLICY std_params_public_read         ON std_params         FOR SELECT USING (true);
CREATE POLICY signatures_public_read         ON signatures         FOR SELECT USING (true);
CREATE POLICY validation_sites_public_read   ON validation_sites   FOR SELECT USING (true);
CREATE POLICY validation_results_public_read ON validation_results FOR SELECT USING (true);
CREATE POLICY thresholds_public_read         ON thresholds         FOR SELECT USING (true);
CREATE POLICY ecuador_results_public_read    ON ecuador_results    FOR SELECT USING (true);
CREATE POLICY ecuador_rasters_public_read    ON ecuador_rasters    FOR SELECT USING (true);

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
    GRANT SELECT ON
      bodies, variables, cells, std_params, signatures,
      validation_sites, validation_results, thresholds,
      ecuador_results, ecuador_rasters
    TO anon, authenticated;
  END IF;
END $$;
