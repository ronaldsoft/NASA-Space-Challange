import { CAPAS_EN, CLASES_EN, ESTACIONES_EN, FUENTES_EN, MORAN_EN, TERRENOS_EN } from "./datosModelo.en";
import { isEn } from "./i18n";
// Datos del tablero que no vienen de las teselas: estaciones, fuentes, métricas y nombres de capas.
// Cifras: artículo final «Analogía planetaria del relieve a escala global y en Ecuador con evaluación
// estadística y control de calidad» (revisión del 15 nov 2026), tablas 3 a 7. No se leen de Supabase.

export interface Estacion {
  nombre: string;
  lugar: string;
  /** null = sin sede fija (no se dibuja en el mapa). */
  lat: number | null;
  lon: number | null;
  tipo: string;
  estado: string;
  fuente: string;
}

/**
 * Instalaciones y programas de la Tabla 7 del artículo final (contraste funcional, no validan el mapa).
 * El artículo no geolocaliza las instalaciones: las coordenadas del marcador son de la fuente indicada en cada una.
 * PANGAEA es un programa itinerante de campañas, sin sede fija: no lleva marcador (lat/lon null).
 */
export const ESTACIONES: Estacion[] = [
  {
    nombre: "MDRS (Mars Desert Research Station)",
    lugar: "Utah, Estados Unidos",
    lat: 38.406278,
    lon: -110.791792,
    tipo: "Hábitat y actividad extravehicular en terreno árido",
    estado: "Operación por temporadas; informes 2026",
    fuente: "https://reports.marssociety.org/2026/",
  },
  {
    nombre: "HI-SEAS",
    lugar: "Mauna Loa, Hawái, Estados Unidos",
    lat: 19.602378,
    lon: -155.487192,
    tipo: "Aislamiento y operaciones en terreno volcánico",
    estado: "Instalación descrita como operativa por su entidad",
    fuente: "https://www.hi-seas.org/",
  },
  {
    nombre: "LUNA",
    lugar: "Colonia, Alemania",
    lat: 50.851944,
    lon: 7.131111,
    tipo: "Pruebas sobre regolito simulado controlado",
    estado: "Inaugurada en 2024",
    fuente: "https://www.esa.int/Newsroom/Press_Releases/ESA-DLR_lunar_analogue_facility_inaugurated",
  },
  {
    nombre: "PANGAEA",
    lugar: "Lanzarote, España",
    lat: null,
    lon: null,
    tipo: "Formación geológica y travesías de campo (programa de campañas, no una base)",
    estado: "Campaña documentada en 2026",
    fuente: "https://www.esa.int/Newsroom/Press_Releases/Media_Invitation_PANGAEA_astronaut_training_in_Lanzarote",
  },
  {
    nombre: "HERA (Human Exploration Research Analog)",
    lugar: "Houston, Estados Unidos",
    lat: 29.558333,
    lon: -95.088889,
    tipo: "Aislamiento y operaciones humanas en hábitat cerrado (no es un análogo de relieve)",
    estado: "Campañas de hasta 45 días",
    fuente: "https://www.nasa.gov/mission/hera/",
  },
];

/** Estaciones con sede fija, las únicas que se dibujan en el mapa. */
export const ESTACIONES_MAPA = () => ESTACIONES.filter((e): e is Estacion & { lat: number; lon: number } => e.lat != null && e.lon != null);

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

/** «4,5895° S · 137,4417° E» (es) o «4.5895° S · 137.4417° E» (en), con los decimales tal como vienen en los datos. */
export function coordTexto(lat: number, lon: number): string {
  const n = (v: number) => (isEn ? String(Math.abs(v)) : String(Math.abs(v)).replace(".", ","));
  return `${n(lat)}° ${lat < 0 ? "S" : "N"} · ${n(lon)}° ${lon < 0 ? (isEn ? "W" : "O") : "E"}`;
}

/**
 * Sitios de aterrizaje con firma de superficie: analog.v2_mission_signatures (Supabase,
 * RPC analog_v2_get_missions), leído el 15 nov 2026. Lat/lon planetocéntricas, longitud este de −180 a 180.
 * Referencias del índice (artículo, «Normalización y modelos a dos escalas»): en Marte, Phoenix, Pathfinder,
 * Perseverance, Opportunity y Curiosity; en la Luna, los 14 sitios. 19 firmas de referencia en total.
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
    dato: "Reflectancia de la Luna: LROC WAC EMP a 643 nm entre ±60° y mosaico WAC morfológico en las regiones polares",
    uso: "Señal radiométrica de la Luna en las firmas",
    cita: "Robinson, M. S. et al. (2010). Lunar Reconnaissance Orbiter Camera (LROC) instrument overview. Space Science Reviews 150, 81–124. doi:10.1007/s11214-010-9634-2.",
    url: "https://doi.org/10.1007/s11214-010-9634-2",
  },
  mcd43: {
    id: "mcd43",
    dato: "Albedo de la Tierra: MODIS MCD43C3 v061, albedo de cielo blanco de onda corta (0,05°)",
    uso: "Señal radiométrica de cada celda terrestre y control de calidad (Albedo_Quality, Percent_Inputs, Percent_Snow)",
    cita: "Schaaf, C. y Wang, Z. (2021). MCD43C3 MODIS/Terra+Aqua BRDF/Albedo Albedo Daily L3 Global 0.05Deg CMG V061. NASA EOSDIS Land Processes DAAC. doi:10.5067/MODIS/MCD43C3.061.",
    url: "https://doi.org/10.5067/MODIS/MCD43C3.061",
  },
  esa_cci: {
    id: "esa_cci",
    dato: "Cobertura del suelo: ESA CCI Land Cover 2022 (300 m)",
    uso: "Máscara: en el mundo, clase más próxima al centro de la celda; en Ecuador, fracción de clases forestales y agua; erosión de un píxel en ambos",
    cita: "European Space Agency Climate Change Initiative (2022). Land cover map of 2022 [Conjunto de datos].",
    url: "https://climate.esa.int/en/projects/land-cover/",
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
  marte: ["mola", "tes", "gmted", "mcd43", "esa_cci", "misiones", "ne_paises", "ne_regiones", "gadm"],
  luna: ["lola", "lroc", "gmted", "mcd43", "esa_cci", "misiones", "ne_paises", "ne_regiones", "gadm"],
  conjunta: ["mola", "tes", "lola", "lroc", "gmted", "mcd43", "esa_cci", "misiones", "gadm"],
};

/** Nombre visible de cada capa y una línea de explicación. */
export const CAPAS = {
  marte: {
    nombre: "Similitud con Marte (índice 0–100)",
    linea: "Qué tan cerca está cada celda de la firma de superficie de los sitios de aterrizaje en Marte, comparada con el resto de la Tierra.",
  },
  luna: {
    nombre: "Similitud con la Luna (índice 0–100)",
    linea: "Lo mismo, frente a los sitios de aterrizaje en la Luna.",
  },
  conjunta: {
    nombre: "Similitud con Marte y la Luna a la vez (índice 0–100)",
    linea: "El menor de los dos índices: alto solo si la celda se parece a ambos.",
  },
  mascara: {
    nombre: "Celdas excluidas por la máscara ESA CCI 2022",
    linea: "Celdas transparentes: no se evalúan. En el mundo cuenta la clase ESA CCI más próxima al centro de la celda; en Ecuador, la fracción de bosque y agua desde 300 m; en ambos, erosión de un píxel. La máscara global no excluye todo el bosque subpíxel.",
  },
  misiones: {
    nombre: "Sitios de aterrizaje de referencia del índice",
    linea: "Misiones cuya firma de superficie (elevación, pendiente y señal radiométrica; mediana de 81 muestras en un radio máximo de 5,66 km) sirve de referencia para cada celda de la Tierra.",
  },
  misiones_fuera: {
    nombre: "Otros aterrizajes en Marte, fuera de la firma",
    linea: "Tienen firma calculada pero no son referencias del índice: su evidencia hidrogeomorfológica es media, medio-alta o no aplica.",
  },
  estaciones: {
    nombre: "Instalaciones y programas análogos (Tabla 7 del artículo)",
    linea: "Se comparan por su función de ensayo. No validan estadísticamente el mapa ni entran al cálculo. PANGAEA es un programa de campañas sin sede fija y no aparece en el mapa.",
  },
} as const;

/** Paleta real de las teselas de la Luna y la conjunta (pipeline_v2/teselas_v2.py, CLASES y RGBA). Clases del artículo, índice 0–100. */
export const CLASES_TESELA = [
  { rango: "95–100", nombre: "muy alta", rgb: "rgb(252,236,60)" },
  { rango: "90–94", nombre: "alta", rgb: "rgb(248,150,64)" },
  { rango: "75–89", nombre: "moderada", rgb: "rgb(208,74,118)" },
  { rango: "50–74", nombre: "baja", rgb: "rgb(118,42,160)" },
  { rango: "0–49", nombre: "muy baja", rgb: "rgb(45,40,110)" },
];

/** Marte en rampa rojiza (teselas_v2.py, RGBA_MARTE): mismas clases, solo cambia el color. */
export const CLASES_TESELA_MARTE = [
  { rango: "95–100", nombre: "muy alta", rgb: "rgb(255,190,130)" },
  { rango: "90–94", nombre: "alta", rgb: "rgb(228,110,60)" },
  { rango: "75–89", nombre: "moderada", rgb: "rgb(186,64,40)" },
  { rango: "50–74", nombre: "baja", rgb: "rgb(128,40,30)" },
  { rango: "0–49", nombre: "muy baja", rgb: "rgb(74,26,22)" },
];

export function clasesTesela(banda: "marte" | "luna" | "conjunta") {
  return banda === "marte" ? CLASES_TESELA_MARTE : CLASES_TESELA;
}

/** Cifras del artículo final (15 nov 2026). Índice en escala 0–100; áreas en km². */
export const METRICAS = {
  umbral: 95,
  /** Tabla 5: exclusión de misión, 9 misiones marcianas (5 altas frente a 4 medias o medio-altas, sin InSight). */
  evaluacion_mision: {
    global: { auc: 0.4, p: 0.683, asignaciones: 126 },
    ecuador: { auc: 0.4, p: 0.714, asignaciones: 126 },
    misiones: 9,
    altas: 5,
    medias: 4,
    auc_procedimiento_original: 0.3,
  },
  /** Sensibilidad: Jaccard por área de la selección ≥95 al retirar un precedente marciano. */
  jaccard_retiro: { phoenix: 0.516, opportunity: 0.905 },
  /** Tabla 4: I de Moran en Ecuador, 5 000 celdas, 8 vecinos, 199 permutaciones (p mínima resoluble 0,005). */
  moran: {
    celdas: 5000,
    vecinos: 8,
    permutaciones: 199,
    p: 0.005,
    filas: [
      { variable: "Elevación", i: 0.994 },
      { variable: "Pendiente", i: 0.719 },
      { variable: "Albedo", i: 0.817 },
      { variable: "Similitud Marte", i: 0.976 },
      { variable: "Similitud Luna", i: 0.866 },
      { variable: "Similitud conjunta", i: 0.883 },
    ],
  },
  /** Modelo global a 0,05° y Tabla 3 (retención tras QA≤1, puntajes históricos sin recalibrar). */
  global: {
    celdas: 2584921,
    area_mkm2: 57.76,
    marte95: 74045,
    luna95: 55769,
    conjunta95: 1285,
    conjunta95_km2: 30889,
    conjunta95_historica: 1047,
    conjunta95_historica_km2: 25306,
    qa1: {
      celdas: 1233642,
      area_km2: 30785216,
      marte95: 29080,
      marte95_km2: 602224,
      luna95: 25512,
      luna95_km2: 613341,
      conjunta95: 832,
      conjunta95_km2: 20758,
      pct_area: 53.3,
      pct_area_conjunta: 67.2,
    },
  },
  /** Ecuador a 30″ y Tabla 6 (retención por calidad radiométrica y terreno). */
  ecuador: {
    celdas: 17236,
    huellas_modis: 1416,
    marte95: 1547,
    luna95: 369,
    conjunta95: 2,
    grupo_marte: { celdas: 386, km2: 331 },
    grupo_luna: { celdas: 70, km2: 60 },
    qa2: { celdas: 3308, marte95: 0, luna95: 0, conjunta95: 0 },
    qa1: { celdas: 391, marte95: 0, luna95: 0, conjunta95: 0, pct: 2.27 },
    qa1_terreno: { celdas: 29, km2: 24.89, max_marte: 18, max_luna: 48, max_conjunta: 18 },
    qa255: 505,
    qa_conjuntas: [3, 5],
    urbano: 475,
    nieve_hielo: 108,
    mixta: 1103,
  },
  /** Muestra lunar: registros EMP y del mosaico morfológico polar, con sus medianas. */
  luna_muestra: { emp: 86807, polar: 13193, mediana_emp: 0.104, mediana_polar: 0.049 },
};

/* ---------------- Inglés: se traducen los textos en el sitio, una sola vez al cargar ---------------- */
if (isEn) {
  ESTACIONES.forEach((e, i) => Object.assign(e, ESTACIONES_EN[i]));
  MISIONES.forEach((m) => {
    m.terreno = TERRENOS_EN[m.terreno] ?? m.terreno;
  });
  for (const k of Object.keys(FUENTES)) Object.assign(FUENTES[k], FUENTES_EN[k]);
  for (const k of Object.keys(CAPAS_EN)) Object.assign((CAPAS as Record<string, object>)[k], CAPAS_EN[k]);
  METRICAS.moran.filas.forEach((f) => (f.variable = MORAN_EN[f.variable] ?? f.variable));
  for (const c of [...CLASES_TESELA, ...CLASES_TESELA_MARTE]) c.nombre = CLASES_EN[c.nombre] ?? c.nombre;
}

/** Rango de clase 0–100 («95–100»); se deja la función por compatibilidad: no hay decimales. */
export function rangoTxt(r: string): string {
  return isEn ? r.replace(/,/g, ".") : r;
}
