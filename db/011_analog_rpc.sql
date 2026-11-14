-- RPC en esquema public (expuesto por PostgREST) que leen solo analog.*
CREATE OR REPLACE FUNCTION public.analog_get_validation_table()
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
  cita               text,
  es_provisional     boolean,
  es_mock            boolean,
  entra_al_auc       boolean,
  excluido_auc       boolean,
  banda_latitud      text,
  banda_ganadora_marte text,
  banda_ganadora_luna text
)
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path = analog, public
AS $$
  SELECT
    s.name, s.lat, s.lon, s.buffer_km, s.label,
    r.known_class, r.delta_mars, r.delta_moon, r.predicted_class,
    COALESCE(r.acierto, r.predicted_class = r.known_class),
    s.source, s.cita, s.is_provisional, s.is_mock,
    s.entra_al_auc, s.excluido_auc,
    r.banda_latitud, r.banda_ganadora_marte, r.banda_ganadora_luna
  FROM analog.validation_sites s
  LEFT JOIN analog.validation_results r ON r.site_id = s.id
  ORDER BY s.name;
$$;

CREATE OR REPLACE FUNCTION public.analog_get_zone_card(p_nombre text DEFAULT NULL)
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
LANGUAGE sql
STABLE
SECURITY INVOKER
SET search_path = analog, public
AS $$
  SELECT z.name, z.lat, z.lon, z.elevation_m, z.slope_deg, z.roughness_tri,
         z.delta_mars, z.class, z.delta_moon, TRUE
  FROM analog.priority_zones z
  WHERE p_nombre IS NULL OR z.name = p_nombre OR z.id = p_nombre
  ORDER BY GREATEST(COALESCE(z.delta_mars,0), COALESCE(z.delta_moon,0)) DESC;
$$;

GRANT EXECUTE ON FUNCTION public.analog_get_validation_table() TO anon, authenticated;
GRANT EXECUTE ON FUNCTION public.analog_get_zone_card(text) TO anon, authenticated;
