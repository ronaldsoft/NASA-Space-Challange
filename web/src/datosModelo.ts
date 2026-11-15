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

export interface MisionFirma {
  cuerpo: "marte" | "luna";
  mision: string;
  /** Año de aterrizaje (primeros 4 dígitos de «periodo»). */
  anio: number;
  periodo: string;
  lat: number;
  lon: number;
  terreno: string;
  /** usada_en_modelo: true = entra en la firma con la que se calcula el índice. */
  usada: boolean;
  fuente: string;
}

/** «4,5895° S · 137,4417° E» con los decimales tal como vienen en los datos. */
export function coordTexto(lat: number, lon: number): string {
  const n = (v: number) => String(Math.abs(v)).replace(".", ",");
  return `${n(lat)}° ${lat < 0 ? "S" : "N"} · ${n(lon)}° ${lon < 0 ? "O" : "E"}`;
}

/**
 * Sitios de aterrizaje con firma de superficie: analog.v2_mission_signatures (Supabase,
 * RPC analog_v2_get_missions), leído el 15 nov 2026. Lat/lon planetocéntricas, longitud este de −180 a 180.
 * En Marte solo entran en la firma las misiones con resultado hidrológico «alto»; en la Luna, las 14.
 */
export const MISIONES: MisionFirma[] = [
  { cuerpo: "marte", mision: "Pathfinder", anio: 1997, periodo: "1997-07 a 1997-09", lat: 19.17, lon: -33.21, terreno: "Ares Vallis", usada: true, fuente: "https://science.nasa.gov/resource/mars-pathfinder-landing-site/" },
  { cuerpo: "marte", mision: "Opportunity", anio: 2004, periodo: "2004-01 a 2018-06", lat: -1.9462, lon: -5.5266, terreno: "Meridiani Planum", usada: true, fuente: "https://science.nasa.gov/mission/mars-exploration-rovers-spirit-and-opportunity/" },
  { cuerpo: "marte", mision: "Phoenix", anio: 2008, periodo: "2008-05 a 2008-11", lat: 68.22, lon: -125.75, terreno: "Planicie polar", usada: true, fuente: "https://science.nasa.gov/mission/mars-phoenix/" },
  { cuerpo: "marte", mision: "Curiosity", anio: 2012, periodo: "2012-08 a 2026-11", lat: -4.5895, lon: 137.4417, terreno: "Cráter Gale", usada: true, fuente: "https://science.nasa.gov/blogs/perseverance-mars-rover/2026/10/12/nasas-perseverance-sets-off-world-record-for-total-distance-driven/" },
  { cuerpo: "marte", mision: "Perseverance", anio: 2021, periodo: "2021-02 a 2026-11", lat: 18.4447, lon: 77.4508, terreno: "Delta y cráter", usada: true, fuente: "https://science.nasa.gov/blogs/perseverance-mars-rover/2026/10/12/nasas-perseverance-sets-off-world-record-for-total-distance-driven/" },
  { cuerpo: "marte", mision: "Viking 1", anio: 1976, periodo: "1976-07 a 1982-11", lat: 22.27, lon: -48.264, terreno: "Planicie Chryse", usada: false, fuente: "https://science.nasa.gov/mission/viking/" },
  { cuerpo: "marte", mision: "Viking 2", anio: 1976, periodo: "1976-09 a 1980-04", lat: 47.64, lon: 134.29, terreno: "Planicie Utopia", usada: false, fuente: "https://science.nasa.gov/mission/viking/" },
  { cuerpo: "marte", mision: "Spirit", anio: 2004, periodo: "2004-01 a 2010-03", lat: -14.5692, lon: 175.4729, terreno: "Cráter Gusev", usada: false, fuente: "https://science.nasa.gov/mission/mars-exploration-rovers-spirit-and-opportunity/" },
  { cuerpo: "marte", mision: "InSight", anio: 2018, periodo: "2018-11 a 2022-12", lat: 4.502, lon: 135.623, terreno: "Planicie Elysium", usada: false, fuente: "https://science.nasa.gov/mission/insight/" },
  { cuerpo: "marte", mision: "Zhurong", anio: 2021, periodo: "2021-05 a 2022-05", lat: 25.066, lon: 109.925, terreno: "Utopia Planitia", usada: false, fuente: "https://www.nature.com/articles/s41597-026-07034-4" },
  { cuerpo: "luna", mision: "Apollo 11", anio: 1969, periodo: "1969-07", lat: 0.67416, lon: 23.47314, terreno: "Mare Tranquillitatis", usada: true, fuente: "https://www.nasa.gov/wp-content/uploads/2023/04/sp-4029.pdf" },
  { cuerpo: "luna", mision: "Apollo 12", anio: 1969, periodo: "1969-11", lat: -3.0128, lon: -23.4219, terreno: "Oceanus Procellarum", usada: true, fuente: "https://www.nasa.gov/wp-content/uploads/2023/04/sp-4029.pdf" },
  { cuerpo: "luna", mision: "Luna 17 / Lunokhod 1", anio: 1970, periodo: "1970-11 a 1971-09", lat: 38.28, lon: -35, terreno: "Mare Imbrium", usada: true, fuente: "https://science.nasa.gov/wp-content/uploads/2023/09/DSC_monograph24.pdf" },
  { cuerpo: "luna", mision: "Apollo 14", anio: 1971, periodo: "1971-02", lat: -3.64589, lon: -17.47194, terreno: "Tierras altas y eyecta", usada: true, fuente: "https://www.nasa.gov/wp-content/uploads/2023/04/sp-4029.pdf" },
  { cuerpo: "luna", mision: "Apollo 15", anio: 1971, periodo: "1971-07 a 1971-08", lat: 26.13239, lon: 3.6333, terreno: "Hadley Apennine", usada: true, fuente: "https://nssdc.gsfc.nasa.gov/planetary/lunar/apollo_lrv.html" },
  { cuerpo: "luna", mision: "Apollo 16", anio: 1972, periodo: "1972-04", lat: -8.9734, lon: 15.5011, terreno: "Tierras altas Descartes", usada: true, fuente: "https://nssdc.gsfc.nasa.gov/planetary/lunar/apollo_lrv.html" },
  { cuerpo: "luna", mision: "Apollo 17", anio: 1972, periodo: "1972-12", lat: 20.1911, lon: 30.7723, terreno: "Valle Taurus Littrow", usada: true, fuente: "https://nssdc.gsfc.nasa.gov/planetary/lunar/apollo_lrv.html" },
  { cuerpo: "luna", mision: "Luna 24", anio: 1976, periodo: "1976-08", lat: 12.75, lon: 62.2, terreno: "Mare Crisium", usada: true, fuente: "https://nssdc.gsfc.nasa.gov/planetary/lunar/lunarussr.html" },
  { cuerpo: "luna", mision: "Chang'e-3 / Yutu", anio: 2013, periodo: "2013-12 a 2016", lat: 44.12, lon: -19.51, terreno: "Mare Imbrium", usada: true, fuente: "https://planetarynames.wr.usgs.gov/Feature/15415" },
  { cuerpo: "luna", mision: "Chang'e-4 / Yutu-2", anio: 2019, periodo: "2019-01 a fecha indeterminada", lat: -45.457, lon: 177.588, terreno: "Von Kármán SPA", usada: true, fuente: "https://planetarynames.wr.usgs.gov/SearchResults?Feature+Type=59_Statio&Target=16_Moon" },
  { cuerpo: "luna", mision: "Chang'e-5", anio: 2020, periodo: "2020-12", lat: 43.06, lon: -51.92, terreno: "Oceanus Procellarum", usada: true, fuente: "https://planetarynames.wr.usgs.gov/SearchResults?Feature+Type=59_Statio&Target=16_Moon" },
  { cuerpo: "luna", mision: "Chandrayaan-3", anio: 2023, periodo: "2023-08 a 2023-09", lat: -69.367621, lon: 32.348126, terreno: "Tierras altas australes", usada: true, fuente: "https://www.isro.gov.in/ISRO_EN/Chandrayaan3_Details.html" },
  { cuerpo: "luna", mision: "SLIM", anio: 2024, periodo: "2024-01 a 2024-08", lat: -13.3, lon: 25.2, terreno: "Cerca de Shioli", usada: true, fuente: "https://darts.isas.jaxa.jp/en/missions/slim" },
  { cuerpo: "luna", mision: "Chang'e-6", anio: 2024, periodo: "2024-06", lat: -41.63, lon: -153.98, terreno: "Cuenca Apollo SPA", usada: true, fuente: "https://planetarynames.wr.usgs.gov/SearchResults?Feature+Type=59_Statio&Target=16_Moon" },
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
    uso: "Puntos de referencia de las firmas y marcadores de los globos de Marte y la Luna",
    cita: "Tabla analog.v2_mission_signatures del proyecto (Supabase). Coordenadas: Orloff, R. W. (2000). Apollo by the Numbers: A Statistical Reference. NASA SP-2000-4029; NASA NSSDCA, fichas lunares; USGS Gazetteer of Planetary Nomenclature (estaciones de aterrizaje); fichas de misión de NASA Science, CNSA, JAXA e ISRO.",
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
  misiones: {
    nombre: "Sitios de aterrizaje usados para entrenar el modelo",
    linea: "Misiones cuya firma de superficie (elevación, pendiente y albedo en 5 km) define a qué se parece cada celda de la Tierra.",
  },
  misiones_fuera: {
    nombre: "Otros aterrizajes en Marte, fuera de la firma",
    linea: "Tienen firma calculada pero no entran en el índice: su resultado hidrológico no es «alto».",
  },
  estaciones: {
    nombre: "Estaciones análogas permanentes",
    linea: "Instalaciones activas hoy en el mundo. Son referencia, no entran al cálculo.",
  },
} as const;

/** Paleta real de las teselas de la Luna y la conjunta (pipeline_v2/teselas_v2.py, CLASES y RGBA). */
export const CLASES_TESELA = [
  { rango: "0,95–1,00", nombre: "muy alta", rgb: "rgb(252,236,60)" },
  { rango: "0,90–0,94", nombre: "alta", rgb: "rgb(248,150,64)" },
  { rango: "0,75–0,89", nombre: "moderada", rgb: "rgb(208,74,118)" },
  { rango: "0,50–0,74", nombre: "baja", rgb: "rgb(118,42,160)" },
  { rango: "0,00–0,49", nombre: "muy baja", rgb: "rgb(45,40,110)" },
];

/** Marte en rampa rojiza (teselas_v2.py, RGBA_MARTE): mismas clases, solo cambia el color. */
export const CLASES_TESELA_MARTE = [
  { rango: "0,95–1,00", nombre: "muy alta", rgb: "rgb(255,190,130)" },
  { rango: "0,90–0,94", nombre: "alta", rgb: "rgb(228,110,60)" },
  { rango: "0,75–0,89", nombre: "moderada", rgb: "rgb(186,64,40)" },
  { rango: "0,50–0,74", nombre: "baja", rgb: "rgb(128,40,30)" },
  { rango: "0,00–0,49", nombre: "muy baja", rgb: "rgb(74,26,22)" },
];

export function clasesTesela(banda: "marte" | "luna" | "conjunta") {
  return banda === "marte" ? CLASES_TESELA_MARTE : CLASES_TESELA;
}

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
