// Traducciones al inglés de los textos de datosModelo.ts. Solo se cargan al aplicar el idioma inglés.

export const ESTACIONES_EN: { nombre?: string; lugar: string; tipo: string; estado: string }[] = [
  { lugar: "Utah, United States", tipo: "Habitat and extravehicular activity on arid terrain", estado: "Seasonal operation; 2026 reports" },
  { lugar: "Mauna Loa, Hawaii, United States", tipo: "Isolation and operations on volcanic terrain", estado: "Facility described as operational by its organization" },
  { lugar: "Cologne, Germany", tipo: "Tests on controlled simulated regolith", estado: "Opened in 2024" },
  { lugar: "Lanzarote, Spain", tipo: "Geology training and field traverses (a campaign program, not a base)", estado: "Campaign documented in 2026" },
  { lugar: "Houston, United States", tipo: "Isolation and human operations in a closed habitat (not a relief analog)", estado: "Campaigns of up to 45 days" },
];

export const TERRENOS_EN: Record<string, string> = {
  "Planicie polar": "Polar plain",
  "Cráter Gale": "Gale Crater",
  "Delta y cráter": "Delta and crater",
  "Planicie Chryse": "Chryse Planitia",
  "Planicie Utopia": "Utopia Planitia",
  "Cráter Gusev": "Gusev Crater",
  "Planicie Elysium": "Elysium Planitia",
  "Tierras altas y eyecta": "Highlands and ejecta",
  "Tierras altas Descartes": "Descartes Highlands",
  "Valle Taurus Littrow": "Taurus-Littrow Valley",
  "Tierras altas australes": "Southern highlands",
  "Cerca de Shioli": "Near Shioli",
  "Cuenca Apollo SPA": "Apollo basin (SPA)",
  "Von Kármán SPA": "Von Kármán (SPA)",
};

export const FUENTES_EN: Record<string, { dato: string; uso: string; cita?: string }> = {
  mola: { dato: "Mars relief: MOLA MEGDR 64 pixels per degree", uso: "Mars elevation and slope in the mission signatures", cita: "Smith, D. E. et al. (2001). Mars Orbiter Laser Altimeter: Experiment summary after the first year of global mapping of Mars. Journal of Geophysical Research 106(E10), 23689–23722. doi:10.1029/2000JE001364. Data: NASA PDS, volume MGS-M-MOLA-5-MEGDR-L3-V1.0." },
  tes: { dato: "Mars albedo: MGS TES, bolometric albedo at 8 pixels per degree", uso: "Mars radiometric signal in the signatures" },
  lola: { dato: "Moon relief: LOLA LDEM_64", uso: "Moon elevation and slope in the mission signatures", cita: "Smith, D. E. et al. (2010). The Lunar Orbiter Laser Altimeter investigation on the Lunar Reconnaissance Orbiter mission. Space Science Reviews 150, 209–241. doi:10.1007/s11214-009-9512-y. Data: NASA PDS, volume LRO-L-LOLA-3-RDR-V1.0." },
  lroc: { dato: "Moon reflectance: LROC WAC EMP at 643 nm within ±60° and a morphologic WAC mosaic in the polar regions", uso: "Moon radiometric signal in the signatures" },
  mcd43: { dato: "Earth albedo: MODIS MCD43C3 v061, shortwave white-sky albedo (0.05°)", uso: "Radiometric signal of each land cell and quality control (Albedo_Quality, Percent_Inputs, Percent_Snow)", cita: "Schaaf, C. and Wang, Z. (2021). MCD43C3 MODIS/Terra+Aqua BRDF/Albedo Albedo Daily L3 Global 0.05Deg CMG V061. NASA EOSDIS Land Processes DAAC. doi:10.5067/MODIS/MCD43C3.061." },
  esa_cci: { dato: "Land cover: ESA CCI Land Cover 2022 (300 m)", uso: "Mask: worldwide, the class nearest to the cell center; in Ecuador, the fraction of forest and water classes; one-pixel erosion in both", cita: "European Space Agency Climate Change Initiative (2022). Land cover map of 2022 [Dataset]." },
  gmted: { dato: "Earth relief: GMTED2010, 30 arc-second mean (USGS, not NASA)", uso: "Elevation and slope of each land cell", cita: "Danielson, J. J. and Gesch, D. B. (2011). Global Multi-resolution Terrain Elevation Data 2010 (GMTED2010). U.S. Geological Survey Open-File Report 2011–1073. doi:10.3133/ofr20111073." },
  misiones: { dato: "Coordinates of 24 landing missions (10 on Mars, 14 on the Moon)", uso: "Reference points for the signatures and markers on the Mars and Moon globes", cita: "Project table analog.v2_mission_signatures (Supabase). Coordinates: Orloff, R. W. (2000). Apollo by the Numbers: A Statistical Reference. NASA SP-2000-4029; NASA NSSDCA lunar fact sheets; USGS Gazetteer of Planetary Nomenclature (landing stations); mission pages from NASA Science, CNSA, JAXA and ISRO." },
  ne_paises: { dato: "Continents: Natural Earth 10m Admin 0 Countries v5.1.1", uso: "Group the most similar zones by continent", cita: "Natural Earth (NACIS). 1:10m Cultural Vectors, Admin 0 – Countries, v5.1.1. Public domain." },
  ne_regiones: { dato: "Terrain types: Natural Earth 10m Physical Labels (geographic regions) v5.0.0", uso: "Group by terrain type: deserts, plateaus, mountain ranges, plains and tundras", cita: "Natural Earth (NACIS). 1:10m Physical Vectors, Geography Regions (polygons), v5.0.0. Public domain." },
  gadm: { dato: "Ecuador provinces: GADM 4.1, level 1", uso: "Group the most similar zones in Ecuador by province", cita: "GADM (2022). Database of Global Administrative Areas, version 4.1. University of California, Davis." },
};

export const CAPAS_EN: Record<string, { nombre: string; linea: string }> = {
  marte: { nombre: "Similarity to Mars (0–100 index)", linea: "How close each cell is to the surface signature of the Mars landing sites, compared with the rest of Earth." },
  luna: { nombre: "Similarity to the Moon (0–100 index)", linea: "The same, against the Moon landing sites." },
  conjunta: { nombre: "Similarity to Mars and the Moon at once (0–100 index)", linea: "The lower of the two indices: high only if the cell resembles both." },
  mascara: { nombre: "Cells excluded by the ESA CCI 2022 mask", linea: "Transparent cells are not evaluated. Worldwide, the ESA CCI class nearest to the cell center decides; in Ecuador, the fraction of forest and water from 300 m; in both, one-pixel erosion. The global mask does not exclude all sub-pixel forest." },
  misiones: { nombre: "Reference landing sites of the index", linea: "Missions whose surface signature (elevation, slope and radiometric signal; median of 81 samples within a maximum radius of 5.66 km) is the reference for each cell on Earth." },
  misiones_fuera: { nombre: "Other Mars landings, outside the signature", linea: "Their signature is computed but they are not references of the index: their hydrogeomorphological evidence is medium, medium-high or not applicable." },
  estaciones: { nombre: "Analog facilities and programs (article Table 7)", linea: "They are compared by their testing function. They do not statistically validate the map and are not part of the calculation. PANGAEA is a campaign program with no fixed site and is not shown on the map." },
};

export const MORAN_EN: Record<string, string> = {
  "Elevación": "Elevation",
  Pendiente: "Slope",
  Albedo: "Albedo",
  "Similitud Marte": "Mars similarity",
  "Similitud Luna": "Moon similarity",
  "Similitud conjunta": "Joint similarity",
};

export const CLASES_EN: Record<string, string> = {
  "muy alta": "very high",
  alta: "high",
  moderada: "moderate",
  baja: "low",
  "muy baja": "very low",
};

export const CONTINENTES_EN: Record<string, string> = {
  Asia: "Asia",
  "Oceanía": "Oceania",
  "América del Sur": "South America",
  "América del Norte y Central": "North and Central America",
  "África": "Africa",
  Europa: "Europe",
};

export const TIPOS_EN: Record<string, string> = {
  "Sin región fisiográfica cartografiada": "other surfaces",
  "Llanuras y cuencas": "plains and basins",
  Desiertos: "deserts",
  Tundras: "tundras",
  Mesetas: "plateaus",
  "Cordilleras y montañas": "mountain ranges",
};
