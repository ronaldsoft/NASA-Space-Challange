// Datos del tablero que no vienen de las teselas: estaciones, fuentes, métricas y nombres de capas.
// Cifras de métricas: analog.v2_metrics (Supabase) = metricas_v2.json del repositorio.

export interface Estacion {
  nombre: string;
  lugar: string;
  lat: number;
  lon: number;
  tipo: string;
  estado: string;
  fuente: string;
}

/** Estaciones análogas permanentes y activas (revisado el 15 nov 2026 contra la fuente de cada una). */
export const ESTACIONES: Estacion[] = [
  {
    nombre: "Mars Desert Research Station (MDRS)",
    lugar: "Hanksville, Utah, EE. UU.",
    lat: 38.406278,
    lon: -110.791792,
    tipo: "Hábitat de campo en desierto (Mars Society)",
    estado: "Instalación fija; temporada 2025–26 de octubre a mayo",
    fuente: "https://www.marssociety.org/news/2025/10/17/mars-society-launches-2025-26-mdrs-field-season-with-crew-319-as-part-of-the-worlds-biggest-analog-project/",
  },
  {
    nombre: "Flashline Mars Arctic Research Station (FMARS)",
    lugar: "Isla Devon, Nunavut, Canadá",
    lat: 75.431319,
    lon: -89.823386,
    tipo: "Hábitat de campo ártico (Mars Society)",
    estado: "Instalación fija; tripulación 19 en julio de 2026",
    fuente: "https://www.marssociety.org/news/2026/07/24/from-vikings-legacy-to-tomorrows-mars-crew-19-completes-devon-island-analog-mission/",
  },
  {
    nombre: "Estación Concordia",
    lugar: "Domo C, Antártida",
    lat: -75.09978,
    lon: 123.332196,
    tipo: "Base antártica todo el año (IPEV y PNRA) usada por la ESA como análogo",
    estado: "Invernada 2026 (DC21) con 13 personas",
    fuente: "https://blogs.esa.int/concordia/2026/02/23/lets-wrap-this-up/",
  },
  {
    nombre: "HERA, Human Exploration Research Analog",
    lugar: "Johnson Space Center, Houston, EE. UU.",
    lat: 29.558333,
    lon: -95.088889,
    tipo: "Hábitat cerrado de aislamiento (NASA)",
    estado: "Instalación fija de NASA; su hábitat se usará en la misión de un año prevista no antes de agosto de 2027",
    fuente: "https://www.nasa.gov/humans-in-space/nasa-seeks-volunteers-for-new-yearlong-simulated-moon-mars-mission/",
  },
  {
    nombre: "LUNA Analog Facility",
    lugar: "Colonia, Alemania (junto al Centro Europeo de Astronautas)",
    lat: 50.851944,
    lon: 7.131111,
    tipo: "Nave con regolito simulado (ESA y DLR)",
    estado: "Instalación fija inaugurada en septiembre de 2024",
    fuente: "https://www.dlr.de/en/research-and-transfer/featured-topics/mission-moon/the-luna-moon-facility",
  },
];

export interface Fuente {
  id: string;
  dato: string;
  uso: string;
  cita: string;
  url: string;
}

export const FUENTES: Record<string, Fuente> = {
  mola: {
    id: "mola",
    dato: "Relieve de Marte: MOLA MEGDR 64 píxeles por grado",
    uso: "Elevación y pendiente de Marte en las firmas de misión",
    cita: "Smith, D. E. et al. (2001). Mars Orbiter Laser Altimeter: Experiment summary after the first year of global mapping of Mars. Journal of Geophysical Research 106(E10), 23689–23722. doi:10.1029/2000JE001364. Datos: NASA PDS, volumen MGS-M-MOLA-5-MEGDR-L3-V1.0.",
    url: "https://pds-geosciences.wustl.edu/missions/mgs/megdr.html",
  },
  tes: {
    id: "tes",
    dato: "Albedo de Marte: MGS TES, albedo bolométrico 8 píxeles por grado",
    uso: "Señal radiométrica de Marte en las firmas",
    cita: "Christensen, P. R. et al. (2001). Mars Global Surveyor Thermal Emission Spectrometer experiment: Investigation description and surface science results. Journal of Geophysical Research 106(E10), 23823–23871. doi:10.1029/2000JE001370.",
    url: "https://doi.org/10.1029/2000JE001370",
  },
  lola: {
    id: "lola",
    dato: "Relieve de la Luna: LOLA LDEM_64",
    uso: "Elevación y pendiente de la Luna en las firmas de misión",
    cita: "Smith, D. E. et al. (2010). The Lunar Orbiter Laser Altimeter investigation on the Lunar Reconnaissance Orbiter mission. Space Science Reviews 150, 209–241. doi:10.1007/s11214-009-9512-y. Datos: NASA PDS, volumen LRO-L-LOLA-3-RDR-V1.0.",
    url: "https://pds-geosciences.wustl.edu/missions/lro/lola.htm",
  },
  lroc: {
    id: "lroc",
    dato: "Reflectancia de la Luna: LROC WAC 643 nm",
    uso: "Señal radiométrica de la Luna en las firmas",
    cita: "Robinson, M. S. et al. (2010). Lunar Reconnaissance Orbiter Camera (LROC) instrument overview. Space Science Reviews 150, 81–124. doi:10.1007/s11214-010-9634-2.",
    url: "https://doi.org/10.1007/s11214-010-9634-2",
  },
  mcd43: {
    id: "mcd43",
    dato: "Albedo de la Tierra: MODIS MCD43C3 v061 (0,05°)",
    uso: "Señal radiométrica de cada celda terrestre",
    cita: "Schaaf, C. y Wang, Z. (2021). MCD43C3 MODIS/Terra+Aqua BRDF/Albedo Albedo Daily L3 Global 0.05Deg CMG V061. NASA EOSDIS Land Processes DAAC. doi:10.5067/MODIS/MCD43C3.061.",
    url: "https://doi.org/10.5067/MODIS/MCD43C3.061",
  },
  mcd12: {
    id: "mcd12",
    dato: "Cobertura del suelo: MODIS MCD12Q1 v061, clases IGBP 2022",
    uso: "Máscara de bosque, humedales, cultivos y zonas urbanas",
    cita: "Friedl, M. y Sulla-Menashe, D. (2022). MCD12Q1 MODIS/Terra+Aqua Land Cover Type Yearly L3 Global 500m SIN Grid V061. NASA EOSDIS Land Processes DAAC. doi:10.5067/MODIS/MCD12Q1.061. Teselas leídas de NASA GIBS.",
    url: "https://doi.org/10.5067/MODIS/MCD12Q1.061",
  },
  gmted: {
    id: "gmted",
    dato: "Relieve de la Tierra: GMTED2010, media 30 segundos de arco (USGS, no NASA)",
    uso: "Elevación y pendiente de cada celda terrestre",
    cita: "Danielson, J. J. y Gesch, D. B. (2011). Global Multi-resolution Terrain Elevation Data 2010 (GMTED2010). U.S. Geological Survey Open-File Report 2011–1073. doi:10.3133/ofr20111073.",
    url: "https://doi.org/10.3133/ofr20111073",
  },
  misiones: {
    id: "misiones",
    dato: "Coordenadas de 24 misiones de aterrizaje (10 en Marte, 14 en la Luna)",
    uso: "Puntos de referencia de las firmas",
    cita: "Orloff, R. W. (2000). Apollo by the Numbers: A Statistical Reference. NASA SP-2000-4029; NASA NSSDCA, fichas lunares; USGS Gazetteer of Planetary Nomenclature (estaciones de aterrizaje); fichas de misión de NASA Science, CNSA, JAXA e ISRO.",
    url: "https://www.nasa.gov/wp-content/uploads/2023/04/sp-4029.pdf",
  },
  ne_paises: {
    id: "ne_paises",
    dato: "Continentes: Natural Earth 10m Admin 0 Countries v5.1.1",
    uso: "Agrupar por continente las zonas más parecidas",
    cita: "Natural Earth (NACIS). 1:10m Cultural Vectors, Admin 0 – Countries, v5.1.1. Dominio público.",
    url: "https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_countries.zip",
  },
  ne_regiones: {
    id: "ne_regiones",
    dato: "Tipos de terreno: Natural Earth 10m Physical Labels (regiones geográficas) v5.0.0",
    uso: "Agrupar por tipo de terreno: desiertos, mesetas, cordilleras, llanuras y tundras",
    cita: "Natural Earth (NACIS). 1:10m Physical Vectors, Geography Regions (polígonos), v5.0.0. Dominio público.",
    url: "https://naciscdn.org/naturalearth/10m/physical/ne_10m_geography_regions_polys.zip",
  },
  gadm: {
    id: "gadm",
    dato: "Provincias de Ecuador: GADM 4.1, nivel 1",
    uso: "Agrupar por provincia las zonas más parecidas de Ecuador",
    cita: "GADM (2022). Database of Global Administrative Areas, versión 4.1. Universidad de California, Davis.",
    url: "https://gadm.org/",
  },
};

export const FUENTES_MAPA: Record<"marte" | "luna" | "conjunta", string[]> = {
  marte: ["mola", "tes", "gmted", "mcd43", "mcd12", "misiones", "ne_paises", "ne_regiones", "gadm"],
  luna: ["lola", "lroc", "gmted", "mcd43", "mcd12", "misiones", "ne_paises", "ne_regiones", "gadm"],
  conjunta: ["mola", "tes", "lola", "lroc", "gmted", "mcd43", "mcd12", "misiones", "gadm"],
};

/** Nombre visible de cada capa y una línea de explicación. */
export const CAPAS = {
  marte: {
    nombre: "Similitud con Marte (índice 0–1)",
    linea: "Qué tan cerca está cada celda de la firma de superficie de los sitios de aterrizaje en Marte, comparada con el resto de la Tierra.",
  },
  luna: {
    nombre: "Similitud con la Luna (índice 0–1)",
    linea: "Lo mismo, frente a los sitios de aterrizaje en la Luna.",
  },
  conjunta: {
    nombre: "Similitud con Marte y la Luna a la vez (índice 0–1)",
    linea: "El menor de los dos índices: alto solo si la celda se parece a ambos.",
  },
  mascara: {
    nombre: "Máscara de vegetación y cultivos excluidos",
    linea: "Celdas transparentes: bosque, humedales, cultivos, zonas urbanas y mosaicos agrícolas según MODIS. No se evalúan.",
  },
  estaciones: {
    nombre: "Estaciones análogas permanentes",
    linea: "Instalaciones activas hoy en el mundo. Son referencia, no entran al cálculo.",
  },
} as const;

/** Paleta real de las teselas (pipeline_v2/teselas_v2.py, CLASES y RGBA). */
export const CLASES_TESELA = [
  { rango: "0,95–1,00", nombre: "muy alta", rgb: "rgb(252,236,60)" },
  { rango: "0,90–0,94", nombre: "alta", rgb: "rgb(248,150,64)" },
  { rango: "0,75–0,89", nombre: "moderada", rgb: "rgb(208,74,118)" },
  { rango: "0,50–0,74", nombre: "baja", rgb: "rgb(118,42,160)" },
  { rango: "0,00–0,49", nombre: "muy baja", rgb: "rgb(45,40,110)" },
];

/** analog.v2_metrics → auc_sitios_conocidos, recuperacion_nulo_bloques, jackknife_*, sensibilidad_umbral. */
export const METRICAS = {
  auc_marte: { v: 0.889, ic: [0.722, 1.0], pos: 9, neg: 6 },
  auc_luna: { v: 0.917, ic: [0.75, 1.0], pos: 6, neg: 6 },
  recuperacion: { umbral: 0.95, recuperados: 1, de: 12, nulo_media: 0.33, p: 0.2937, permutaciones: 1000 },
  jaccard_variable_ecuador: { marte: [0.176, 0.244], luna: [0.121, 0.289] },
  jaccard_variable_global: { marte: [0.174, 0.228], luna: [0.154, 0.353] },
  jaccard_mision_ecuador: { marte: [0.576, 0.886], luna: [0.777, 1.0] },
  global: { celdas: 2197719, marte95: 44693, luna95: 38387, conjunta95: 1144 },
  ecuador: { celdas: 8741, marte95: 387, luna95: 193, conjunta95: 0, conjunta_max: 0.93 },
  mascara: { bosque: 91294, uso: 295908 },
};
