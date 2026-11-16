// Generado el 15 nov 2026 desde los rásteres del artículo final (~/localhost/hackaton/outputs):
// mapa_analogia_tierra_5km.tif (máscara ESA CCI 2022; conjunta = mínimo de las bandas redondeadas) y
// similitud_ecuador_1km.tif (30″, fracción forestal y de agua ESA CCI). Índice en escala 0–100, antes del filtro QA.
// Área = número de celdas × área de la celda a su latitud (R = 6 371,0088 km).
export const ZONAS = {
 "global_marte": {
  "total_area_km2": 1492862,
  "total_celdas": 74045,
  "filas": [
   {
    "continente": "Asia",
    "tipo": "Sin región fisiográfica cartografiada",
    "area_km2": 312843,
    "indice_medio": 97.3,
    "indice_max": 100
   },
   {
    "continente": "Europa",
    "tipo": "Llanuras y cuencas",
    "area_km2": 161890,
    "indice_medio": 97.4,
    "indice_max": 100
   },
   {
    "continente": "Europa",
    "tipo": "Sin región fisiográfica cartografiada",
    "area_km2": 134610,
    "indice_medio": 97.3,
    "indice_max": 100
   },
   {
    "continente": "Asia",
    "tipo": "Llanuras y cuencas",
    "area_km2": 120146,
    "indice_medio": 97.2,
    "indice_max": 100
   },
   {
    "continente": "Oceanía",
    "tipo": "Sin región fisiográfica cartografiada",
    "area_km2": 105650,
    "indice_medio": 97.2,
    "indice_max": 100
   },
   {
    "continente": "América del Sur",
    "tipo": "Llanuras y cuencas",
    "area_km2": 87728,
    "indice_medio": 97.5,
    "indice_max": 100
   },
   {
    "continente": "América del Sur",
    "tipo": "Sin región fisiográfica cartografiada",
    "area_km2": 80452,
    "indice_medio": 97.2,
    "indice_max": 100
   },
   {
    "continente": "América del Norte y Central",
    "tipo": "Sin región fisiográfica cartografiada",
    "area_km2": 76749,
    "indice_medio": 97.2,
    "indice_max": 100
   },
   {
    "continente": "África",
    "tipo": "Sin región fisiográfica cartografiada",
    "area_km2": 68755,
    "indice_medio": 97.2,
    "indice_max": 100
   },
   {
    "continente": "Oceanía",
    "tipo": "Llanuras y cuencas",
    "area_km2": 64943,
    "indice_medio": 97.0,
    "indice_max": 100
   }
  ],
  "por_tipo": [
   {
    "tipo": "Sin región fisiográfica cartografiada",
    "area_km2": 779218
   },
   {
    "tipo": "Tundras",
    "area_km2": 29591
   },
   {
    "tipo": "Llanuras y cuencas",
    "area_km2": 460938
   },
   {
    "tipo": "Mesetas",
    "area_km2": 103628
   },
   {
    "tipo": "Cordilleras y montañas",
    "area_km2": 88347
   },
   {
    "tipo": "Desiertos",
    "area_km2": 31138
   }
  ]
 },
 "global_luna": {
  "total_area_km2": 1337684,
  "total_celdas": 55769,
  "filas": [
   {
    "continente": "África",
    "tipo": "Desiertos",
    "area_km2": 200273,
    "indice_medio": 96.8,
    "indice_max": 100
   },
   {
    "continente": "Asia",
    "tipo": "Sin región fisiográfica cartografiada",
    "area_km2": 184288,
    "indice_medio": 97.5,
    "indice_max": 100
   },
   {
    "continente": "África",
    "tipo": "Sin región fisiográfica cartografiada",
    "area_km2": 114474,
    "indice_medio": 97.3,
    "indice_max": 100
   },
   {
    "continente": "Oceanía",
    "tipo": "Mesetas",
    "area_km2": 109888,
    "indice_medio": 97.3,
    "indice_max": 100
   },
   {
    "continente": "Asia",
    "tipo": "Llanuras y cuencas",
    "area_km2": 108366,
    "indice_medio": 97.6,
    "indice_max": 100
   },
   {
    "continente": "América del Norte y Central",
    "tipo": "Llanuras y cuencas",
    "area_km2": 101107,
    "indice_medio": 97.0,
    "indice_max": 100
   },
   {
    "continente": "América del Sur",
    "tipo": "Sin región fisiográfica cartografiada",
    "area_km2": 66469,
    "indice_medio": 97.4,
    "indice_max": 100
   },
   {
    "continente": "América del Sur",
    "tipo": "Llanuras y cuencas",
    "area_km2": 61074,
    "indice_medio": 97.4,
    "indice_max": 100
   },
   {
    "continente": "Europa",
    "tipo": "Llanuras y cuencas",
    "area_km2": 43673,
    "indice_medio": 97.3,
    "indice_max": 100
   },
   {
    "continente": "Asia",
    "tipo": "Mesetas",
    "area_km2": 38652,
    "indice_medio": 97.3,
    "indice_max": 100
   }
  ],
  "por_tipo": [
   {
    "tipo": "Sin región fisiográfica cartografiada",
    "area_km2": 449909
   },
   {
    "tipo": "Tundras",
    "area_km2": 18977
   },
   {
    "tipo": "Llanuras y cuencas",
    "area_km2": 344818
   },
   {
    "tipo": "Mesetas",
    "area_km2": 208571
   },
   {
    "tipo": "Cordilleras y montañas",
    "area_km2": 64128
   },
   {
    "tipo": "Desiertos",
    "area_km2": 251282
   }
  ]
 },
 "ecuador_marte": {
  "total_area_km2": 1327.4,
  "total_celdas": 1547,
  "evaluables": 17236,
  "area_evaluable_km2": 14791,
  "max": 100,
  "mediana": 16,
  "p25": 10,
  "p75": 80,
  "media": 40.9,
  "clases": [
   {
    "clase": "0–49",
    "celdas": 10346,
    "area_km2": 8878.6
   },
   {
    "clase": "50–74",
    "celdas": 1814,
    "area_km2": 1557.1
   },
   {
    "clase": "75–89",
    "celdas": 2433,
    "area_km2": 2088.0
   },
   {
    "clase": "90–94",
    "celdas": 1096,
    "area_km2": 940.4
   },
   {
    "clase": "95–100",
    "celdas": 1547,
    "area_km2": 1327.4
   }
  ],
  "filas": [
   {
    "zona": "Guayas",
    "celdas": 705,
    "area_km2": 605.0,
    "indice_medio": 97.7,
    "indice_max": 100
   },
   {
    "zona": "Santa Elena",
    "celdas": 450,
    "area_km2": 386.1,
    "indice_medio": 97.7,
    "indice_max": 100
   },
   {
    "zona": "Manabi",
    "celdas": 280,
    "area_km2": 240.4,
    "indice_medio": 97.3,
    "indice_max": 100
   },
   {
    "zona": "Loja",
    "celdas": 46,
    "area_km2": 39.4,
    "indice_medio": 98.3,
    "indice_max": 100
   },
   {
    "zona": "El Oro",
    "celdas": 45,
    "area_km2": 38.6,
    "indice_medio": 97.6,
    "indice_max": 99
   },
   {
    "zona": "Los Rios",
    "celdas": 11,
    "area_km2": 9.4,
    "indice_medio": 96.5,
    "indice_max": 99
   },
   {
    "zona": "Galápagos",
    "celdas": 1,
    "area_km2": 0.9,
    "indice_medio": 98.0,
    "indice_max": 98
   }
  ]
 },
 "ecuador_luna": {
  "total_area_km2": 316.7,
  "total_celdas": 369,
  "evaluables": 17236,
  "area_evaluable_km2": 14791,
  "max": 100,
  "mediana": 12,
  "p25": 6,
  "p75": 43,
  "media": 26.3,
  "clases": [
   {
    "clase": "0–49",
    "celdas": 13687,
    "area_km2": 11745.4
   },
   {
    "clase": "50–74",
    "celdas": 1985,
    "area_km2": 1703.6
   },
   {
    "clase": "75–89",
    "celdas": 861,
    "area_km2": 739.0
   },
   {
    "clase": "90–94",
    "celdas": 334,
    "area_km2": 286.7
   },
   {
    "clase": "95–100",
    "celdas": 369,
    "area_km2": 316.7
   }
  ],
  "filas": [
   {
    "zona": "Guayas",
    "celdas": 224,
    "area_km2": 192.3,
    "indice_medio": 97.2,
    "indice_max": 100
   },
   {
    "zona": "Galápagos",
    "celdas": 63,
    "area_km2": 54.1,
    "indice_medio": 95.5,
    "indice_max": 98
   },
   {
    "zona": "Orellana",
    "celdas": 27,
    "area_km2": 23.2,
    "indice_medio": 97.2,
    "indice_max": 100
   },
   {
    "zona": "Sucumbios",
    "celdas": 26,
    "area_km2": 22.3,
    "indice_medio": 97.8,
    "indice_max": 99
   },
   {
    "zona": "Santa Elena",
    "celdas": 10,
    "area_km2": 8.6,
    "indice_medio": 98.2,
    "indice_max": 99
   },
   {
    "zona": "Manabi",
    "celdas": 7,
    "area_km2": 6.0,
    "indice_medio": 96.4,
    "indice_max": 99
   },
   {
    "zona": "Los Rios",
    "celdas": 5,
    "area_km2": 4.3,
    "indice_medio": 98.6,
    "indice_max": 100
   },
   {
    "zona": "Loja",
    "celdas": 3,
    "area_km2": 2.6,
    "indice_medio": 98.0,
    "indice_max": 99
   },
   {
    "zona": "El Oro",
    "celdas": 1,
    "area_km2": 0.9,
    "indice_medio": 99.0,
    "indice_max": 99
   }
  ]
 },
 "ecuador_conjunta": {
  "total_area_km2": 1.7,
  "total_celdas": 2,
  "evaluables": 17236,
  "area_evaluable_km2": 14791,
  "max": 98,
  "mediana": 10,
  "p25": 5,
  "p75": 42,
  "media": 24.0,
  "clases": [
   {
    "clase": "0–49",
    "celdas": 13984,
    "area_km2": 12000.4
   },
   {
    "clase": "50–74",
    "celdas": 2380,
    "area_km2": 2042.6
   },
   {
    "clase": "75–89",
    "celdas": 838,
    "area_km2": 719.2
   },
   {
    "clase": "90–94",
    "celdas": 32,
    "area_km2": 27.5
   },
   {
    "clase": "95–100",
    "celdas": 2,
    "area_km2": 1.7
   }
  ],
  "filas": [
   {
    "zona": "Galápagos",
    "celdas": 1,
    "area_km2": 0.9,
    "indice_medio": 98.0,
    "indice_max": 98
   },
   {
    "zona": "Loja",
    "celdas": 1,
    "area_km2": 0.9,
    "indice_medio": 96.0,
    "indice_max": 96
   }
  ]
 }
} as const;
