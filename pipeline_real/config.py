"""Rutas, constantes y sitios para la preparación de DEMs a 1 km."""

from __future__ import annotations

import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # /workspace/analogs
DATA = ROOT / "data"
RAW = DATA / "raw"
PROCESSED = DATA / "processed"

RAW_MARS = RAW / "mars" / "mola_megdr64"
RAW_MOON = RAW / "moon" / "lola_ldem64"
RAW_EARTH = RAW / "earth" / "copernicus_glo90"
TILELIST = RAW / "earth" / "tileList.txt"

PROC_MARS = PROCESSED / "mars"
PROC_MOON = PROCESSED / "moon"
PROC_EARTH = PROCESSED / "earth"
PROC_VALID = PROC_EARTH / "validation"

# --- Cuerpos: radios usados para pendiente (metros) ---
# Marte: esfera del propio rótulo MEGDR (A_AXIS_RADIUS = 3396.0 km).
# El datum vertical es el areoide MOLA (GMM3 / mgm1025, grado 50), no esta esfera.
MARS_RADIUS_M = 3_396_000.0
# Luna: esfera de 1737.4 km (rótulo LDEM).
MOON_RADIUS_M = 1_737_400.0
# Tierra: semieje mayor WGS84 (GDAL / geographic slope).
EARTH_RADIUS_M = 6_378_137.0

# --- Resolución nativa ---
MOLA_PPD = 64.0
LOLA_PPD = 64.0
MOLA_DEG = 1.0 / MOLA_PPD  # 0.015625° ≈ 926 m en el ecuador de Marte
LOLA_DEG = 1.0 / LOLA_PPD  # 0.015625° ≈ 474 m en el ecuador lunar

# --- Grilla objetivo ≈ 1 km en cada cuerpo ---
TARGET_METERS = 1000.0


def meters_per_degree(radius_m: float) -> float:
    return radius_m * math.pi / 180.0


def km_cell_deg(radius_m: float) -> float:
    return TARGET_METERS / meters_per_degree(radius_m)


MARS_1KM_DEG = km_cell_deg(MARS_RADIUS_M)  # ≈ 0.016873°
MOON_1KM_DEG = km_cell_deg(MOON_RADIUS_M)  # ≈ 0.032986°
EARTH_1KM_DEG = 0.009  # ≈ 1001.9 m en el ecuador WGS84

# --- URLs ---
MOLA_BASE = (
    "https://pds-geosciences.wustl.edu/mgs/mgs-m-mola-5-megdr-l3-v1/"
    "mgsl_300x/meg064"
)
MOLA_TILES = [
    "megt90n000gb",  #  90–0°N, 0–180°E
    "megt90n180gb",  #  90–0°N, 180–360°E
    "megt00n000gb",  #   0–90°S, 0–180°E
    "megt00n180gb",  #   0–90°S, 180–360°E
]
LOLA_IMG_URL = (
    "https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/"
    "data/lola_gdr/cylindrical/img/ldem_64.img"
)
LOLA_LBL_URL = LOLA_IMG_URL.replace(".img", ".lbl")
COP_BUCKET = "https://copernicus-dem-90m.s3.amazonaws.com"
COP_TILELIST_URL = f"{COP_BUCKET}/tileList.txt"

# Extensión Ecuador (continente + Galápagos) y sitios de validación.
ECUADOR_BOUNDS = {  # lon_min, lat_min, lon_max, lat_max
    "west": -92.0,
    "south": -5.1,
    "east": -75.0,
    "north": 1.7,
}

# Margen extra alrededor del buffer oficial, para derivar pendiente/TRI en 3x3.
VALIDATION_MARGIN_M = 8_000.0

# Lista OFICIAL de Expertos (validacion_parte1.md, 14-nov-2026).
# buffer_km es el radio/buffer indicado por Expertos; la ventana descargada
# usa buffer + margen. Etiquetas: marciano | lunar | ambos | no_analogo.
VALIDATION_SITES = [
    # --- positivos ---
    {
        "id": "yungay",
        "name": "Yungay / Atacama",
        "lat": -24.100,
        "lon": -70.010,
        "buffer_km": 20,
        "etiqueta": "marciano",
        "clase": "positivo",
        "notas": "Análogo marciano verificado. Fuente y citas en validacion_parte1.md.",
    },
    {
        "id": "haughton",
        "name": "Haughton / Devon Island",
        "lat": 75.3667,
        "lon": -89.6833,
        "buffer_km": 12,
        "etiqueta": "marciano",
        "clase": "positivo",
        "notas": "Cráter Haughton, Isla Devon. Análogo marciano verificado.",
    },
    {
        "id": "university_valley",
        "name": "University Valley / Valles Secos",
        "lat": -77.866,
        "lon": 160.726,
        "buffer_km": 3,
        "etiqueta": "marciano",
        "clase": "positivo",
        "notas": "University Valley (Antártida), no el genérico 'Dry Valleys'. Buffer 3 km.",
    },
    {
        "id": "askja",
        "name": "Askja / Vikrahraun",
        "lat": 65.060,
        "lon": -16.640,
        "buffer_km": 6,
        "etiqueta": "marciano",
        "clase": "positivo",
        "notas": "Coordenada confirmada: punto medio de la colada Vikrahraun (bocas 65.0647, -16.7247; frente 65.0590, -16.5454), archivo adicional 1 de Blasizzo et al. (2022), hoja (1.1) Samples. Se descarta 65.03, -16.78 (quedaba 4–5 km fuera de la colada). Radio 6 km. Permanece en el AUC.",
    },
    {
        "id": "mauna_kea",
        "name": "Mauna Kea (conos de cumbre)",
        "lat": 19.8291,
        "lon": -155.4629,
        "buffer_km": 10,
        "etiqueta": "ambos",
        "clase": "positivo",
        "notas": "Conos de la cumbre de Mauna Kea. Etiqueta: ambos (Marte y Luna).",
    },
    {
        "id": "sverrefjell",
        "name": "Sverrefjell / Svalbard",
        "lat": 79.4305,
        "lon": 13.3072,
        "buffer_km": 5,
        "etiqueta": "marciano",
        "clase": "positivo",
        "notas": "Sverrefjell, Svalbard. Análogo marciano.",
    },
    {
        "id": "timanfaya",
        "name": "Timanfaya / Lanzarote",
        "lat": 29.0210,
        "lon": -13.7744,
        "buffer_km": 8,
        "etiqueta": "ambos",
        "clase": "positivo",
        "notas": "Parque Nacional de Timanfaya, Lanzarote. Etiqueta: ambos.",
    },
    {
        "id": "meteor_crater",
        "name": "Meteor Crater",
        "lat": 35.0275,
        "lon": -111.0222,
        "buffer_km": 3,
        "etiqueta": "lunar",
        "clase": "positivo",
        "notas": "Barringer Crater, Arizona. Análogo lunar de impacto. El cráter (~1.2 km) queda mal resuelto a 1 km.",
    },
    {
        "id": "sp_mountain",
        "name": "SP Mountain / Flagstaff",
        "lat": 35.5831,
        "lon": -111.6336,
        "buffer_km": 8,
        "etiqueta": "ambos",
        "clase": "positivo",
        "notas": "SP Mountain, cerca de Flagstaff, Arizona. Etiqueta: ambos.",
    },
    {
        "id": "inferno_chasm",
        "name": "Inferno Chasm / Idaho",
        "lat": 42.9667,
        "lon": -113.1903,
        "buffer_km": 5,
        "etiqueta": "lunar",
        "clase": "positivo",
        "notas": "Coordenada de un resumen LPSC, no de una revista revisada por pares.",
    },
    # --- negativos (no análogos) ---
    {
        "id": "tapajos",
        "name": "Tapajós BR-Sa1",
        "lat": -2.8567,
        "lon": -54.9589,
        "buffer_km": 10,
        "etiqueta": "no_analogo",
        "clase": "negativo",
        "notas": "Sitio FLUXNET/AmeriFlux. No análogo. Teselas GLO-90 pueden faltar en algunos países.",
    },
    {
        "id": "bondville",
        "name": "Bondville US-Bo1",
        "lat": 40.0062,
        "lon": -88.2904,
        "buffer_km": 5,
        "etiqueta": "no_analogo",
        "clase": "negativo",
        "notas": "Sitio FLUXNET/AmeriFlux. No análogo.",
    },
    {
        "id": "harvard_forest",
        "name": "Harvard Forest US-Ha1",
        "lat": 42.5378,
        "lon": -72.1715,
        "buffer_km": 5,
        "etiqueta": "no_analogo",
        "clase": "negativo",
        "notas": "Sitio FLUXNET/AmeriFlux. No análogo.",
    },
    {
        "id": "tumbarumba",
        "name": "Tumbarumba AU-Tum",
        "lat": -35.6566,
        "lon": 148.1517,
        "buffer_km": 5,
        "etiqueta": "no_analogo",
        "clase": "negativo",
        "notas": "Sitio FLUXNET/AmeriFlux. No análogo.",
    },
    {
        "id": "hainich",
        "name": "Hainich DE-Hai",
        "lat": 51.0792,
        "lon": 10.4522,
        "buffer_km": 5,
        "etiqueta": "no_analogo",
        "clase": "negativo",
        "notas": "Sitio FLUXNET/AmeriFlux. No análogo.",
    },
    {
        "id": "hyytiala",
        "name": "Hyytiälä FI-Hyy",
        "lat": 61.8474,
        "lon": 24.2948,
        "buffer_km": 5,
        "etiqueta": "no_analogo",
        "clase": "negativo",
        "notas": "Sitio FLUXNET/AmeriFlux. No análogo.",
    },
]

# Sitios explícitamente fuera del AUC de superficie (no se descargan ni se procesan).
SITES_EXCLUDED = [
    {"id": "rio_tinto", "motivo": "Análogo solo geoquímico; fuera del AUC de superficie."},
    {"id": "ries", "motivo": "Análogo geológico de impacto, hoy cubierto de ciudad, cultivo o bosque."},
    {"id": "sudbury", "motivo": "Análogo geológico de impacto, hoy cubierto de ciudad, cultivo o bosque."},
    {"id": "iceland_highlands_generic", "motivo": "Sustituido por Askja/Vikrahraun."},
    {"id": "dry_valleys_generic", "motivo": "Sustituido por University Valley."},
]

# Bandas oficiales |lat| (simétricas N/S). G es obligatoria para el polo sur lunar (>~84°S).
LAT_BANDS = [
    {"id": "A", "lat_min": 0.0, "lat_max": 15.0, "motivo": "Sin positivos terrestres; Ecuador cae aquí (evaluación, no validación)."},
    {"id": "B", "lat_min": 15.0, "lat_max": 30.0, "motivo": "Mauna Kea, Timanfaya, Yungay."},
    {"id": "C", "lat_min": 30.0, "lat_max": 45.0, "motivo": "Meteor Crater, SP Mountain, Inferno Chasm; negativos Bondville, Harvard Forest, Tumbarumba."},
    {"id": "D", "lat_min": 45.0, "lat_max": 60.0, "motivo": "Banda débil (pocos positivos); negativo Hainich."},
    {"id": "E", "lat_min": 60.0, "lat_max": 72.0, "motivo": "Askja; negativo Hyytiälä."},
    {"id": "F", "lat_min": 72.0, "lat_max": 80.0, "motivo": "Haughton, University Valley, Sverrefjell."},
    {"id": "G", "lat_min": 80.0, "lat_max": 90.0, "motivo": "Obligatoria por diseño para el polo sur lunar (>~84°S). Ninguna estación terrestre cae aquí; el único análogo latitudinal sería la Antártida, y ni siquiera University Valley (~78°S)."},
]

# Muestras estratificadas por banda (celdas por banda y hemisferio).
SAMPLES_PER_BAND_HEMISPHERE = 4000

# Relieve relativo (capa extra, decisión de índice pendiente):
# elevación menos la mediana en una ventana de ~15 km sobre el DEM ya remuestreado.
RELIEF_WINDOW_KM = 15.0


# Fuentes notadas (no procesadas) de albedo / inercia térmica.
OPTIONAL_LAYERS = {
    "albedo": {
        "mars": {
            "producto": "TES Bolometric Albedo (global, ~8 ppd / ~7.5 km) o THEMIS/VIS",
            "url": "https://www.mars.asu.edu/data/tes_albedo/",
            "nota": "Disponible a escala global. Expertos: NO entra al índice v1. No se descarga.",
        },
        "moon": {
            "producto": "LROC WAC Hapke o mosaico de albedo 643 nm",
            "url": "https://wms.lroc.asu.edu/lroc/view_rdr/WAC_HAPKE",
            "nota": "Disponible a 100 m–global. Expertos: NO entra al índice v1 (tampoco la abundancia de roca). No se descarga.",
        },
        "earth": {
            "producto": "MODIS MCD43 albedo o Landsat",
            "url": "https://lpdaac.usgs.gov/products/mcd43a3v061/",
            "nota": "Disponible, pero la definición (banda, geometría, corrección) no es idéntica a TES/LROC.",
        },
    },
    "thermal_inertia": {
        "mars": {
            "producto": "TES Thermal Inertia y/o THEMIS Thermal Inertia",
            "url": "https://www.mars.asu.edu/data/tes_inertia/",
            "nota": "Producto global clásico de Marte. Expertos: NO entra al índice v1 (tampoco la abundancia de roca). No se descarga.",
        },
        "moon": {
            "producto": "Diviner rock abundance / thermal inertia (no es un mapa de TI equivalente en todo el globo de forma trivial)",
            "url": "https://pds-geosciences.wustl.edu/missions/lro/diviner.htm",
            "nota": "Disponible en productos derivados de Diviner. Expertos: NO entra al índice v1 (tampoco la abundancia de roca). No se descarga.",
        },
        "earth": {
            "producto": "No hay un producto global de inercia térmica homologable a TES/Diviner de acceso abierto y resolución comparable.",
            "url": None,
            "nota": "Es la capa más difícil de homologar en los tres cuerpos.",
        },
    },
}

MARS_WKT = """GEOGCRS["Mars IAU2000 ocentric (MEGDR sphere 3396 km)",
  DATUM["Mars_MEGDR_sphere",
    ELLIPSOID["Mars_MEGDR",3396000,0,LENGTHUNIT["metre",1]]],
  PRIMEM["Reference Meridian",0,ANGLEUNIT["degree",0.0174532925199433]],
  CS[ellipsoidal,2],
    AXIS["geodetic latitude (Lat)",north,ORDER[1],ANGLEUNIT["degree",0.0174532925199433]],
    AXIS["geodetic longitude (Lon)",east,ORDER[2],ANGLEUNIT["degree",0.0174532925199433]]]"""

MOON_WKT = """GEOGCRS["Moon ME/PA sphere 1737.4 km",
  DATUM["Moon_sphere_1737_4",
    ELLIPSOID["Moon_IAU",1737400,0,LENGTHUNIT["metre",1]]],
  PRIMEM["Reference Meridian",0,ANGLEUNIT["degree",0.0174532925199433]],
  CS[ellipsoidal,2],
    AXIS["geodetic latitude (Lat)",north,ORDER[1],ANGLEUNIT["degree",0.0174532925199433]],
    AXIS["geodetic longitude (Lon)",east,ORDER[2],ANGLEUNIT["degree",0.0174532925199433]]]"""

EARTH_EPSG = 4326
