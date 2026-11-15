export const INDEX_VARS = ["latitude", "elevation", "slope", "roughness"] as const;
export type IndexVar = (typeof INDEX_VARS)[number];
export type Weights = Record<IndexVar, number>;

export const DEFAULT_WEIGHTS: Weights = {
  latitude: 0.25,
  elevation: 0.25,
  slope: 0.25,
  roughness: 0.25,
};

export const VAR_LABELS: Record<IndexVar, string> = {
  latitude: "Latitud",
  elevation: "Elevación",
  slope: "Pendiente",
  roughness: "Rugosidad",
};

export const CLASS_LABELS: Record<string, string> = {
  marte: "Marte",
  luna: "Luna",
  ambos: "Ambos",
  ninguno: "Ninguno",
  nodata: "Sin dato",
};

export const LABEL_TO_CLASS: Record<string, string> = {
  marciano: "marte",
  lunar: "luna",
  ambos: "ambos",
  no_analogo: "ninguno",
};

export type Nivel = "explorador" | "estudiante" | "cientifico";

export const NIVELES: { id: Nivel; label: string; hint: string }[] = [
  { id: "explorador", label: "Explorador", hint: "Lenguaje sencillo, para empezar de cero" },
  { id: "estudiante", label: "Estudiante", hint: "Conceptos intermedios: latitud, elevación, pendiente, rugosidad y δ" },
  { id: "cientifico", label: "Científico", hint: "Método completo, métricas, citas e incertidumbre" },
];

export type Vista =
  | "inicio"
  | "similitud-marte"
  | "similitud-luna"
  | "visualizador"
  | "validacion"
  | "incertidumbre"
  | "trabajo-futuro"
  | "clases";

export interface Extension {
  oeste: number;
  norte: number;
  este: number;
  sur: number;
}

export interface SitioValidacion {
  nombre: string;
  lat: number;
  lon: number;
  buffer_km: number;
  etiqueta: string;
  fuente: string;
  elevacion_m: number;
  pendiente_deg: number;
  rugosidad_tri: number;
  es_provisional: boolean;
  banda_latitud: string;
  delta_marte: number;
  delta_luna: number;
  distancia_marte: number;
  distancia_luna: number;
  clase_predicha: string;
  clase_conocida: string;
  acierto: boolean;
  banda_ganadora_marte?: string;
  banda_ganadora_luna?: string;
  cita?: string;
  excluido_auc?: boolean;
  coordenada_no_verificada?: boolean;
  entra_al_auc?: boolean;
}

export interface ZonaPrioritaria {
  id: string;
  nombre: string;
  lat: number;
  lon: number;
  banda_latitud: string;
  elevacion_m: number;
  pendiente_deg: number;
  rugosidad_tri: number;
  delta_marte: number;
  delta_luna: number;
  clase: string;
  firma_superficie: {
    latitud: number;
    elevacion_m: number;
    pendiente_deg: number;
    rugosidad_tri: number;
  };
  banda_ganadora_marte?: string;
  banda_ganadora_luna?: string;
  clima: {
    advertencia: string;
    disponible?: boolean;
    temperatura_media_c?: number;
    temperatura_min_c?: number;
    temperatura_max_c?: number;
    precipitacion_anual_mm?: number;
    mes_mas_humedo?: string;
    precipitacion_mes_humedo_mm?: number;
    mes_mas_seco?: string;
    precipitacion_mes_seco_mm?: number;
    nota: string;
  };
}

export interface Catalogo {
  mock: boolean;
  aviso: string;
  metric_version: string;
  congelado_en: string;
  grilla: {
    resolucion_objetivo_m: number;
    resolucion_deg?: number;
    resolucion_mock_deg?: number;
    n_celdas_tierra?: number;
    nota: string;
    sistema: string;
    filas: number;
    columnas: number;
    extension: Extension;
  };
  variables_indice: string[];
  pesos_por_defecto: Weights;
  variables: unknown[];
  bandas_latitud: { nombre: string; abs_lat_min: number; abs_lat_max: number }[];
  std_params: Record<
    string,
    { body_ref: string; variable: string; center: number; scale: number; method: string; frozen_at: string }[]
  >;
  signatures: Record<
    string,
    { body: string; lat_band: string; variable: string; median: number; q1: number; q3: number; n_cells: number }[]
  >;
  d_max: { mars: number; moon: number };
  umbrales: Record<
    string,
    {
      threshold: number;
      sensitivity: number;
      precision: number;
      specificity: number;
      auc: number;
      metric: string;
      d_max: number;
      n_pos: number;
      n_neg: number;
      cuerpo: string;
    }
  >;
  metricas_validacion: {
    marte: { threshold: number; sensitivity: number; precision: number; auc: number; agreement: number };
    luna: { threshold: number; sensitivity: number; precision: number; auc: number; agreement: number };
    precision_por_clase: Record<string, { precision: number; sensitivity: number; support: number }>;
    aciertos?: number;
    aciertos_auc?: number;
    n_sitios_auc?: number;
    n_sitios: number;
    version?: string;
    ic95_marte?: [number, number];
    ic95_luna?: [number, number];
    nota?: string;
  };
  sitios_validacion: SitioValidacion[];
  zonas_prioritarias: ZonaPrioritaria[];
  capas: Record<string, { archivo: string; tipo: string; cuerpo?: string; etiqueta?: string }>;
  limitaciones: string[];
  modo_bandas?: string;
  nota_de_incertidumbre?: string;
  nota_modo_bandas?: string;
  metricas_por_variante?: unknown;
  delong_pareado?: unknown;
  modelo_nulo_solo_abs_lat?: unknown;
  incluir_askja?: boolean;
  elevacion_modo?: string;
  capa_clima?: { disponible?: boolean; etiqueta?: string; nota?: string };
  clases_ecuador?: Record<string, number>;
  /** Modelo v2 (teselas, máscara NASA IGBP y métricas). Viene de catalogo.json o de Supabase (analog_v2_*). */
  modelo_v2?: {
    mascara?: unknown;
    metricas?: Record<string, unknown>;
    teselas?: Record<string, number>;
    capas?: unknown[];
    fuente_datos?: "catalogo" | "supabase";
    [k: string]: unknown;
  };
}

export interface DataSource {
  readonly kind: "mock" | "supabase";
  load(): Promise<Catalogo>;
}
