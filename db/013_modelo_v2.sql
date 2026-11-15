-- 013_modelo_v2: tablas aditivas del modelo v2 en el esquema `analog`.
-- No borra ni modifica tablas v1. PostGIS vive en el esquema `extensions`. Solo lectura pública (RLS SELECT para anon/authenticated).
CREATE SCHEMA IF NOT EXISTS analog;

CREATE TABLE IF NOT EXISTS analog.v2_reference_points (
  body          text     NOT NULL CHECK (body IN ('earth','mars','moon')),
  point_id      integer  NOT NULL,
  lat           double precision NOT NULL,
  lon           double precision NOT NULL,
  elevation_m   real,
  slope_deg     real,
  albedo        real,
  q_elevation   real,            -- cuantil de la variable dentro de su propio cuerpo (0–1)
  q_slope       real,
  q_albedo      real,
  pct_marte     smallint CHECK (pct_marte BETWEEN 0 AND 100),  -- solo Tierra: percentil de analogía v2
  pct_luna      smallint CHECK (pct_luna  BETWEEN 0 AND 100),
  igbp_clase    smallint,        -- solo Tierra: clase IGBP mayoritaria (MCD12Q1 2022) en la celda 0,05°
  elegible_v2   boolean,         -- solo Tierra: sobrevive a la máscara NASA (bosque, 11–14)
  elevation_source text,
  albedo_source    text,
  PRIMARY KEY (body, point_id)
);
CREATE INDEX IF NOT EXISTS v2_points_body_pct_idx ON analog.v2_reference_points (body, pct_marte DESC, pct_luna DESC);
CREATE INDEX IF NOT EXISTS v2_points_latlon_idx ON analog.v2_reference_points (lat, lon);

CREATE TABLE IF NOT EXISTS analog.v2_mission_signatures (
  body            text NOT NULL CHECK (body IN ('mars','moon')),
  mission         text NOT NULL,
  lat             double precision NOT NULL,
  lon             double precision NOT NULL,
  hydro_outcome   text,
  traverse_km     real,
  usada_en_modelo boolean NOT NULL,  -- Marte: solo hydro_outcome = 'alto'; Luna: todas
  elevation_m_median_5km real,
  slope_deg_median_5km   real,
  albedo_median_5km      real,
  q_elevation     real,
  q_slope         real,
  q_albedo        real,
  periodo         text,
  resultado       text,
  terreno         text,
  source_url      text,
  PRIMARY KEY (body, mission)
);

CREATE TABLE IF NOT EXISTS analog.v2_terrestrial_stations (
  station_key   text PRIMARY KEY,
  kind          text NOT NULL CHECK (kind IN ('estacion_original','instalacion','sitio_validacion')),
  name          text NOT NULL,
  lat           double precision,
  lon           double precision,
  etiqueta      text,
  pct_marte_v2  real,
  pct_luna_v2   real,
  info          jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS analog.v2_candidates (
  scope         text NOT NULL CHECK (scope IN ('global','ecuador')),
  cell_id       bigint NOT NULL,   -- fila*ancho+columna de la grilla de origen
  lat           double precision NOT NULL,
  lon           double precision NOT NULL,
  pct_marte     smallint NOT NULL,
  pct_luna      smallint NOT NULL,
  pct_conjunta  smallint NOT NULL,
  igbp_clase    smallint,
  geom          extensions.geometry(Point, 4326) GENERATED ALWAYS AS (extensions.ST_SetSRID(extensions.ST_MakePoint(lon, lat), 4326)) STORED,
  PRIMARY KEY (scope, cell_id)
);
CREATE INDEX IF NOT EXISTS v2_cand_geom_idx ON analog.v2_candidates USING gist (geom);
CREATE INDEX IF NOT EXISTS v2_cand_scope_marte_idx ON analog.v2_candidates (scope, pct_marte DESC);
CREATE INDEX IF NOT EXISTS v2_cand_scope_luna_idx ON analog.v2_candidates (scope, pct_luna DESC);
CREATE INDEX IF NOT EXISTS v2_cand_scope_conj_idx ON analog.v2_candidates (scope, pct_conjunta DESC);

CREATE TABLE IF NOT EXISTS analog.v2_metrics (
  key        text PRIMARY KEY,
  value      jsonb NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS analog.v2_layers (
  layer_id     text PRIMARY KEY,          -- p. ej. global/marte
  fuente       text NOT NULL CHECK (fuente IN ('global','global_sin_ecuador','ecuador')),
  banda        text NOT NULL CHECK (banda IN ('marte','luna','conjunta')),
  url_template text NOT NULL,
  tile_size    integer NOT NULL DEFAULT 256,
  minzoom      smallint NOT NULL,
  maxzoom      smallint NOT NULL,
  n_teselas    integer,
  clases       jsonb NOT NULL,
  rgba         jsonb NOT NULL,
  notas        text
);

DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['v2_reference_points','v2_mission_signatures','v2_terrestrial_stations','v2_candidates','v2_metrics','v2_layers'] LOOP
    EXECUTE format('ALTER TABLE analog.%I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('DROP POLICY IF EXISTS %I ON analog.%I', t || '_select', t);
    EXECUTE format('CREATE POLICY %I ON analog.%I FOR SELECT TO anon, authenticated USING (true)', t || '_select', t);
    EXECUTE format('GRANT SELECT ON analog.%I TO anon, authenticated', t);
  END LOOP;
END $$;
GRANT USAGE ON SCHEMA analog TO anon, authenticated;

-- ---------- RPC (esquema public, SECURITY INVOKER, solo lectura) ----------
CREATE OR REPLACE FUNCTION public.analog_v2_get_layers()
RETURNS SETOF analog.v2_layers LANGUAGE sql STABLE SET search_path = '' AS $$
  SELECT * FROM analog.v2_layers ORDER BY fuente, banda;
$$;

CREATE OR REPLACE FUNCTION public.analog_v2_get_metrics()
RETURNS jsonb LANGUAGE sql STABLE SET search_path = '' AS $$
  SELECT coalesce(jsonb_object_agg(key, value), '{}'::jsonb) FROM analog.v2_metrics;
$$;

CREATE OR REPLACE FUNCTION public.analog_v2_get_missions()
RETURNS SETOF analog.v2_mission_signatures LANGUAGE sql STABLE SET search_path = '' AS $$
  SELECT * FROM analog.v2_mission_signatures ORDER BY body, mission;
$$;

CREATE OR REPLACE FUNCTION public.analog_v2_get_stations()
RETURNS SETOF analog.v2_terrestrial_stations LANGUAGE sql STABLE SET search_path = '' AS $$
  SELECT * FROM analog.v2_terrestrial_stations ORDER BY kind, name;
$$;

CREATE OR REPLACE FUNCTION public.analog_v2_candidates_bbox(
  p_scope text DEFAULT 'ecuador', p_banda text DEFAULT 'marte',
  p_west double precision DEFAULT -92, p_south double precision DEFAULT -5.1,
  p_east double precision DEFAULT -75, p_north double precision DEFAULT 2,
  p_min smallint DEFAULT 95, p_limit integer DEFAULT 2000)
RETURNS TABLE (scope text, lat double precision, lon double precision, pct_marte smallint, pct_luna smallint, pct_conjunta smallint, igbp_clase smallint)
LANGUAGE sql STABLE SET search_path = '' AS $$
  SELECT c.scope, c.lat, c.lon, c.pct_marte, c.pct_luna, c.pct_conjunta, c.igbp_clase
  FROM analog.v2_candidates c
  WHERE c.scope = p_scope
    AND c.geom OPERATOR(extensions.&&) extensions.ST_MakeEnvelope(p_west, p_south, p_east, p_north, 4326)
    AND CASE p_banda WHEN 'luna' THEN c.pct_luna WHEN 'conjunta' THEN c.pct_conjunta ELSE c.pct_marte END >= p_min
  ORDER BY CASE p_banda WHEN 'luna' THEN c.pct_luna WHEN 'conjunta' THEN c.pct_conjunta ELSE c.pct_marte END DESC
  LIMIT least(greatest(p_limit, 1), 10000);
$$;

CREATE OR REPLACE FUNCTION public.analog_v2_nearest_candidates(
  p_lat double precision, p_lon double precision, p_km double precision DEFAULT 50,
  p_scope text DEFAULT NULL, p_limit integer DEFAULT 20)
RETURNS TABLE (scope text, lat double precision, lon double precision, pct_marte smallint, pct_luna smallint, pct_conjunta smallint, igbp_clase smallint, km double precision)
LANGUAGE sql STABLE SET search_path = '' AS $$
  SELECT c.scope, c.lat, c.lon, c.pct_marte, c.pct_luna, c.pct_conjunta, c.igbp_clase,
         extensions.ST_Distance(c.geom::extensions.geography, extensions.ST_SetSRID(extensions.ST_MakePoint(p_lon, p_lat), 4326)::extensions.geography) / 1000.0 AS km
  FROM analog.v2_candidates c
  WHERE (p_scope IS NULL OR c.scope = p_scope)
    AND extensions.ST_DWithin(c.geom::extensions.geography, extensions.ST_SetSRID(extensions.ST_MakePoint(p_lon, p_lat), 4326)::extensions.geography, p_km * 1000)
  ORDER BY km
  LIMIT least(greatest(p_limit, 1), 500);
$$;

CREATE OR REPLACE FUNCTION public.analog_v2_points_sample(p_body text DEFAULT 'earth', p_limit integer DEFAULT 2000, p_solo_elegibles boolean DEFAULT true)
RETURNS TABLE (body text, point_id integer, lat double precision, lon double precision, elevation_m real, slope_deg real, albedo real, pct_marte smallint, pct_luna smallint, igbp_clase smallint)
LANGUAGE sql STABLE SET search_path = '' AS $$
  SELECT p.body, p.point_id, p.lat, p.lon, p.elevation_m, p.slope_deg, p.albedo, p.pct_marte, p.pct_luna, p.igbp_clase
  FROM analog.v2_reference_points p
  WHERE p.body = p_body AND (NOT p_solo_elegibles OR p.body <> 'earth' OR p.elegible_v2)
  ORDER BY p.point_id
  LIMIT least(greatest(p_limit, 1), 20000);
$$;

GRANT EXECUTE ON FUNCTION public.analog_v2_get_layers(), public.analog_v2_get_metrics(), public.analog_v2_get_missions(),
  public.analog_v2_get_stations(), public.analog_v2_candidates_bbox(text, text, double precision, double precision, double precision, double precision, smallint, integer),
  public.analog_v2_nearest_candidates(double precision, double precision, double precision, text, integer),
  public.analog_v2_points_sample(text, integer, boolean) TO anon, authenticated;
