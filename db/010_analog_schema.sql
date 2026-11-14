-- Esquema dedicado `analog` para la v1 congelada.
-- No modifica tablas de public ni de otros esquemas.
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE SCHEMA IF NOT EXISTS analog;

CREATE TABLE IF NOT EXISTS analog.bodies (
  id   text PRIMARY KEY,
  name text NOT NULL,
  CONSTRAINT bodies_id_check CHECK (id IN ('moon', 'mars', 'earth'))
);
INSERT INTO analog.bodies (id, name) VALUES
  ('moon', 'Luna'), ('mars', 'Marte'), ('earth', 'Tierra')
ON CONFLICT (id) DO NOTHING;

CREATE TABLE IF NOT EXISTS analog.variables (
  name                         text PRIMARY KEY,
  unit                         text NOT NULL,
  source_per_body              jsonb NOT NULL DEFAULT '{}'::jsonb,
  native_resolution_m_per_body jsonb NOT NULL DEFAULT '{}'::jsonb,
  nodata_value                 double precision,
  in_index                     boolean NOT NULL DEFAULT false,
  notes                        text,
  elevation_datum_per_body     jsonb
);

CREATE TABLE IF NOT EXISTS analog.std_params (
  body_ref   text NOT NULL CHECK (body_ref IN ('moon', 'mars')),
  variable   text NOT NULL REFERENCES analog.variables (name) ON DELETE RESTRICT,
  center     double precision NOT NULL,
  scale      double precision NOT NULL,
  method     text NOT NULL,
  frozen_at  timestamptz NOT NULL,
  PRIMARY KEY (body_ref, variable, method, frozen_at)
);

CREATE TABLE IF NOT EXISTS analog.signatures (
  body      text NOT NULL CHECK (body IN ('moon', 'mars')),
  lat_band  text NOT NULL,
  variable  text NOT NULL REFERENCES analog.variables (name) ON DELETE RESTRICT,
  median    double precision,
  q1        double precision,
  q3        double precision,
  n_cells   integer NOT NULL CHECK (n_cells >= 0),
  PRIMARY KEY (body, lat_band, variable)
);

CREATE TABLE IF NOT EXISTS analog.validation_sites (
  id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  site_key   text UNIQUE,
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
  coordenada_no_verificada boolean NOT NULL DEFAULT false,
  entra_al_auc boolean NOT NULL DEFAULT true
);
CREATE INDEX IF NOT EXISTS validation_sites_geom_gist ON analog.validation_sites USING GIST (geom);

CREATE TABLE IF NOT EXISTS analog.validation_results (
  site_id         uuid PRIMARY KEY REFERENCES analog.validation_sites (id) ON DELETE CASCADE,
  delta_mars      double precision,
  delta_moon      double precision,
  predicted_class text CHECK (predicted_class IN ('marte', 'luna', 'ambos', 'ninguno')),
  known_class     text CHECK (known_class IN ('marte', 'luna', 'ambos', 'ninguno')),
  metric_version  text,
  computed_at     timestamptz NOT NULL DEFAULT now(),
  banda_latitud   text,
  banda_ganadora_marte text,
  banda_ganadora_luna text,
  modo_bandas     text,
  acierto         boolean
);

CREATE TABLE IF NOT EXISTS analog.thresholds (
  body        text NOT NULL CHECK (body IN ('moon', 'mars')),
  value       double precision NOT NULL,
  metric      text NOT NULL,
  d_max       double precision,
  sensitivity double precision,
  precision_  double precision,
  specificity double precision,
  auc         double precision,
  ic95_inferior double precision,
  ic95_superior double precision,
  frozen_at   timestamptz NOT NULL,
  PRIMARY KEY (body, frozen_at)
);

-- Representación ligera por defecto: metadatos de los rásteres congelados.
-- analog.ecuador_results puede cargarse además (puntos a 1 km de tierra).
CREATE TABLE IF NOT EXISTS analog.ecuador_results (
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
CREATE INDEX IF NOT EXISTS ecuador_results_geom_gist ON analog.ecuador_results USING GIST (geom);
CREATE INDEX IF NOT EXISTS ecuador_results_class_idx ON analog.ecuador_results (class);

CREATE TABLE IF NOT EXISTS analog.ecuador_rasters (
  layer        text PRIMARY KEY,
  path         text NOT NULL,
  kind         text NOT NULL,
  resolucion_m double precision,
  west         double precision,
  north        double precision,
  east         double precision,
  south        double precision,
  nodata       double precision,
  label        text,
  in_index     boolean NOT NULL DEFAULT true,
  frozen_at    timestamptz,
  sha256       text
);

CREATE TABLE IF NOT EXISTS analog.priority_zones (
  id          text PRIMARY KEY,
  name        text NOT NULL,
  lat         double precision NOT NULL,
  lon         double precision NOT NULL,
  geom        geometry(Point, 4326),
  class       text,
  delta_mars  double precision,
  delta_moon  double precision,
  elevation_m double precision,
  slope_deg   double precision,
  roughness_tri double precision
);

ALTER TABLE analog.bodies             ENABLE ROW LEVEL SECURITY;
ALTER TABLE analog.variables          ENABLE ROW LEVEL SECURITY;
ALTER TABLE analog.std_params         ENABLE ROW LEVEL SECURITY;
ALTER TABLE analog.signatures         ENABLE ROW LEVEL SECURITY;
ALTER TABLE analog.validation_sites   ENABLE ROW LEVEL SECURITY;
ALTER TABLE analog.validation_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE analog.thresholds         ENABLE ROW LEVEL SECURITY;
ALTER TABLE analog.ecuador_results    ENABLE ROW LEVEL SECURITY;
ALTER TABLE analog.ecuador_rasters    ENABLE ROW LEVEL SECURITY;
ALTER TABLE analog.priority_zones     ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS analog_bodies_select ON analog.bodies;
DROP POLICY IF EXISTS analog_variables_select ON analog.variables;
DROP POLICY IF EXISTS analog_std_params_select ON analog.std_params;
DROP POLICY IF EXISTS analog_signatures_select ON analog.signatures;
DROP POLICY IF EXISTS analog_validation_sites_select ON analog.validation_sites;
DROP POLICY IF EXISTS analog_validation_results_select ON analog.validation_results;
DROP POLICY IF EXISTS analog_thresholds_select ON analog.thresholds;
DROP POLICY IF EXISTS analog_ecuador_results_select ON analog.ecuador_results;
DROP POLICY IF EXISTS analog_ecuador_rasters_select ON analog.ecuador_rasters;
DROP POLICY IF EXISTS analog_priority_zones_select ON analog.priority_zones;

CREATE POLICY analog_bodies_select ON analog.bodies FOR SELECT USING (true);
CREATE POLICY analog_variables_select ON analog.variables FOR SELECT USING (true);
CREATE POLICY analog_std_params_select ON analog.std_params FOR SELECT USING (true);
CREATE POLICY analog_signatures_select ON analog.signatures FOR SELECT USING (true);
CREATE POLICY analog_validation_sites_select ON analog.validation_sites FOR SELECT USING (true);
CREATE POLICY analog_validation_results_select ON analog.validation_results FOR SELECT USING (true);
CREATE POLICY analog_thresholds_select ON analog.thresholds FOR SELECT USING (true);
CREATE POLICY analog_ecuador_results_select ON analog.ecuador_results FOR SELECT USING (true);
CREATE POLICY analog_ecuador_rasters_select ON analog.ecuador_rasters FOR SELECT USING (true);
CREATE POLICY analog_priority_zones_select ON analog.priority_zones FOR SELECT USING (true);

-- Sin políticas de INSERT/UPDATE/DELETE para anon ni authenticated.
GRANT USAGE ON SCHEMA analog TO anon, authenticated;
GRANT SELECT ON
  analog.bodies, analog.variables, analog.std_params, analog.signatures,
  analog.validation_sites, analog.validation_results, analog.thresholds,
  analog.ecuador_results, analog.ecuador_rasters, analog.priority_zones
TO anon, authenticated;
