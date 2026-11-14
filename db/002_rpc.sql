-- =============================================================================
-- RPC de lectura para el tablero
-- =============================================================================

CREATE OR REPLACE FUNCTION get_validation_table()
RETURNS TABLE (
  sitio              text,
  latitud            double precision,
  longitud           double precision,
  buffer_km          double precision,
  etiqueta_conocida  text,
  clase_conocida     text,
  delta_marte        double precision,
  delta_luna         double precision,
  clase_predicha     text,
  acierto            boolean,
  fuente             text,
  es_provisional     boolean,
  es_mock            boolean
)
LANGUAGE sql
STABLE
SECURITY INVOKER
AS $$
  SELECT
    s.name,
    s.lat,
    s.lon,
    s.buffer_km,
    s.label,
    r.known_class,
    r.delta_mars,
    r.delta_moon,
    r.predicted_class,
    (r.predicted_class = r.known_class) AS acierto,
    s.source,
    s.is_provisional,
    s.is_mock
  FROM validation_sites s
  LEFT JOIN validation_results r ON r.site_id = s.id
  ORDER BY s.name;
$$;

COMMENT ON FUNCTION get_validation_table() IS
  'Tabla de validación: índice, clase predicha y clase conocida por sitio.';

CREATE OR REPLACE FUNCTION get_zone_card(p_nombre text DEFAULT NULL, p_lat double precision DEFAULT NULL, p_lon double precision DEFAULT NULL)
RETURNS TABLE (
  nombre         text,
  latitud        double precision,
  longitud       double precision,
  elevacion_m    double precision,
  pendiente_deg  double precision,
  rugosidad_tri  double precision,
  delta_marte    double precision,
  clase          text,
  delta_luna     double precision,
  es_prioritaria boolean
)
LANGUAGE plpgsql
STABLE
SECURITY INVOKER
AS $$
BEGIN
  IF p_nombre IS NOT NULL THEN
    RETURN QUERY
    SELECT e.name, e.lat, e.lon, c.elevation_m, c.slope_deg, c.roughness_tri,
           e.delta_mars, e.class, e.delta_moon, e.is_priority
    FROM ecuador_results e
    LEFT JOIN cells c
      ON c.body = 'earth' AND c.lat = e.lat AND c.lon = e.lon
    WHERE e.name = p_nombre
    LIMIT 1;
    RETURN;
  END IF;

  IF p_lat IS NOT NULL AND p_lon IS NOT NULL THEN
    RETURN QUERY
    SELECT e.name, e.lat, e.lon, c.elevation_m, c.slope_deg, c.roughness_tri,
           e.delta_mars, e.class, e.delta_moon, e.is_priority
    FROM ecuador_results e
    LEFT JOIN cells c
      ON c.body = 'earth' AND c.lat = e.lat AND c.lon = e.lon
    ORDER BY (e.lat - p_lat)^2 + (e.lon - p_lon)^2
    LIMIT 1;
    RETURN;
  END IF;

  RETURN QUERY
  SELECT e.name, e.lat, e.lon, c.elevation_m, c.slope_deg, c.roughness_tri,
         e.delta_mars, e.class, e.delta_moon, e.is_priority
  FROM ecuador_results e
  LEFT JOIN cells c
    ON c.body = 'earth' AND c.lat = e.lat AND c.lon = e.lon
  WHERE e.is_priority
  ORDER BY GREATEST(e.delta_mars, e.delta_moon) DESC NULLS LAST;
END;
$$;

COMMENT ON FUNCTION get_zone_card(text, double precision, double precision) IS
  'Ficha de una zona prioritaria de Ecuador (latitud, elevación, firma). '
  'El clima no se devuelve aquí: va en una capa aparte de interpretación.';

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
    GRANT EXECUTE ON FUNCTION get_validation_table() TO anon, authenticated;
    GRANT EXECUTE ON FUNCTION get_zone_card(text, double precision, double precision) TO anon, authenticated;
  END IF;
END $$;
