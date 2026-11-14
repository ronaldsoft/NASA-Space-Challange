#!/usr/bin/env python3
"""
Genera productos MOCK con la misma forma que las salidas reales.

Los valores son sintéticos: no provienen de MOLA, LOLA ni Copernicus DEM
GLO-90. Sirven para el flujo del dashboard y para las capturas del deck.
Etiquetarlo siempre como MOCK.

Uso (desde /workspace/analogs):

    .venv/bin/python -m pipeline.generate_mock
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline import (
    GeoTransform,
    MODO_BANDA_PROPIA,
    MODO_TODAS_MIN,
    build_signatures,
    choose_threshold,
    classify,
    delta_index,
    fit_std_params,
    roughness_tri,
    sample_by_lat_bands,
    slope,
    with_abs_latitude,
)
from pipeline.index import CLASS_NAMES, per_class_metrics
from pipeline.signatures import LatBand, assign_lat_band
from pipeline.terrain import cell_sizes_m, nan_box_mean
from pipeline.metrics import bootstrap_auc_ci, delong_paired, null_abs_lat_auc

FROZEN_AT = "2026-11-14T00:00:00Z"
SEED = 2026
INDEX_VARS = ("latitude", "elevation", "slope", "roughness")
VARS_SIN_LATITUD = ("elevation", "slope", "roughness")
MODO_DEFAULT = MODO_TODAS_MIN
INCLUIR_ASKJA = True
ELEVACION_MODO_DEFAULT = "absoluta"  # alternativa: "relieve_relativo"
ELEVACION_MODOS = ("absoluta", "relieve_relativo")

# Grilla MOCK a ≈ 1,1 km (0.01°), cercana a la resolución objetivo de 1 km.
# Si el ráster PNG resulta pesado se puede submuestrear solo la imagen.
RES_DEG = 0.01
EC_WEST, EC_EAST = -92.20, -75.00
EC_SOUTH, EC_NORTH = -5.10, 1.60

OUT_WEB = ROOT / "web" / "public" / "mock"
OUT_ROOT = ROOT
OUT_WORKSPACE = Path("/workspace")

# Bandas |lat| simétricas N/S (Expertos, validacion_parte1.md, apartado B).
# A no tiene positivos terrestres; D es débil (solo geológicos excluidos del
# AUC); G no tiene estación y se añade por diseño para el polo sur lunar.
BANDS = [
    LatBand("A", 0.0, 15.0),
    LatBand("B", 15.0, 30.0),
    LatBand("C", 30.0, 45.0),
    LatBand("D", 45.0, 60.0),
    LatBand("E", 60.0, 72.0),
    LatBand("F", 72.0, 80.0),
    LatBand("G", 80.0, 90.0),
]

# Conjunto de validación verificado por Expertos (validacion_parte1.md).
# Las variables de superficie (elevación, pendiente, rugosidad) de cada
# sitio son MOCK (sintéticas, a escala de 1 km). Coordenadas, buffers,
# etiquetas y citas provienen del documento verificado.
# Askja entra al AUC con coordenada confirmada (Blasizzo et al. 2022,
# archivo adicional 1, hoja "(1.1) Samples"): punto medio de la colada
# Vikrahraun. El valor antiguo 65.03, -16.78 queda descartado.
# incluir_askja=True por defecto; se puede apagar para una sensibilidad.
VALIDATION_SITES = [
    dict(nombre="Yungay, núcleo hiperárido del Atacama (Chile)", lat=-24.100, lon=-70.010, buffer_km=20,
         etiqueta="marciano", excluido_auc=False, coordenada_no_verificada=False,
         cita="Navarro-González et al. (2003), 10.1126/science.1089143; Ewing et al. (2006), 10.1016/j.gca.2006.08.020"),
    dict(nombre="Estructura de impacto de Haughton, isla Devon (Nunavut, Canadá)", lat=75.3667, lon=-89.6833, buffer_km=12,
         etiqueta="marciano", excluido_auc=False, coordenada_no_verificada=False,
         cita="Osinski et al. (2005), 10.1111/j.1945-5100.2005.tb00145.x"),
    dict(nombre="University Valley, Valles Secos de McMurdo (Antártida)", lat=-77.866, lon=160.726, buffer_km=3,
         etiqueta="marciano", excluido_auc=False, coordenada_no_verificada=False,
         cita="Heldmann et al. (2013), 10.1016/j.pss.2013.05.019; Lapalme et al. (2017a), 10.1017/s0954102016000572"),
    dict(nombre="Askja / colada basáltica Vikrahraun 1961 (Islandia)", lat=65.060, lon=-16.640, buffer_km=6,
         etiqueta="marciano", excluido_auc=False, coordenada_no_verificada=False,
         cita="Blasizzo et al. (2022), 10.1186/s40623-022-01711-5, additional file 1, hoja '(1.1) Samples': punto medio de la colada Vikrahraun entre bocas (65.0647, -16.7247) y frente (65.0590, -16.5454). Se descarta el valor anterior 65.03, -16.78 (queda 4–5 km fuera de la colada)."),
    dict(nombre="Conos de ceniza de la cumbre de Mauna Kea (Hawái, EE. UU.)", lat=19.8291, lon=-155.4629, buffer_km=10,
         etiqueta="ambos", excluido_auc=False, coordenada_no_verificada=False,
         cita="Guinness et al. (2007), 10.1029/2006je002822; ten Kate et al. (2013), 10.1061/(asce)as.1943-5525.0000200; Graham et al. (2015), 10.1016/j.asr.2015.01.024"),
    dict(nombre="Sverrefjell, complejo volcánico de Bockfjorden (Svalbard, Noruega)", lat=79.4305, lon=13.3072, buffer_km=5,
         etiqueta="marciano", excluido_auc=False, coordenada_no_verificada=False,
         cita="Treiman et al. (2002), 10.1016/s0012-821x(02)00998-6"),
    dict(nombre="Parque Nacional de Timanfaya, Lanzarote (España)", lat=29.0210, lon=-13.7744, buffer_km=8,
         etiqueta="ambos", excluido_auc=False, coordenada_no_verificada=False,
         cita="Martínez-Frías et al. (2017), 10.18814/epiiugs/2017/v40i4/017035; Alberquilla et al. (2022), 10.1038/s41598-022-20960-8"),
    dict(nombre="Meteor Crater (Barringer), Arizona (EE. UU.)", lat=35.0275, lon=-111.0222, buffer_km=3,
         etiqueta="lunar", excluido_auc=False, coordenada_no_verificada=False,
         cita="Impact Earth (Western University), ficha Barringer; contexto en Osinski et al. (2023), 10.3389/fspas.2023.1186173"),
    dict(nombre="S P Mountain (S P Crater), campo volcánico de San Francisco, Arizona (EE. UU.)", lat=35.5831, lon=-111.6336, buffer_km=8,
         etiqueta="ambos", excluido_auc=False, coordenada_no_verificada=False,
         cita="Gullikson y Rumpf (2021), USGS OFR 2021-1072, https://pubs.usgs.gov/of/2021/1072/ofr20211072.pdf"),
    dict(nombre="Inferno Chasm, llanura de Snake River / entorno de Craters of the Moon, Idaho (EE. UU.)", lat=42.9667, lon=-113.1903, buffer_km=5,
         etiqueta="lunar", excluido_auc=False, coordenada_no_verificada=False,
         cita="Garry et al. (2015), resumen LPSC 46, 1009 (coordenada de resumen, no de revista); Greeley (1971), 10.1126/science.172.3984.722"),
    # Excluidos del AUC de superficie (se listan, no calibran el umbral)
    dict(nombre="Peña de Hierro / cabecera del Río Tinto (Huelva, España)", lat=37.7267, lon=-6.5532, buffer_km=5,
         etiqueta="marciano", excluido_auc=True, coordenada_no_verificada=False,
         cita="Amils et al. (2014), 10.3390/life4030511; Fernández-Remolar et al. (2005), 10.1016/j.epsl.2005.09.043. Análogo solo geoquímico/mineralógico; excluido del AUC de superficie."),
    dict(nombre="Ries (Nördlinger Ries), Alemania", lat=48.8842, lon=10.5569, buffer_km=13,
         etiqueta="lunar", excluido_auc=True, coordenada_no_verificada=False,
         cita="Stöffler et al. (2013), 10.1111/maps.12086; IUGS Geoheritage. Cubeta con ciudad y agricultura; no usar como positivo de superficie."),
    dict(nombre="Cuenca de Sudbury, Ontario (Canadá)", lat=46.600, lon=-81.183, buffer_km=5,
         etiqueta="lunar", excluido_auc=True, coordenada_no_verificada=True,
         cita="Lowman (1992), 10.1029/92rg00755. Análogo geológico de cuenca tipo mare; cubierta de bosque, lagos y área urbana. Coordenada de catálogo [NO VERIFICADA] en ficha PASSC esta sesión. Sitio separado de Ries. Excluido del AUC de superficie."),
    # Negativos
    dict(nombre="FLONA Tapajós, torre LBA km 67 (BR-Sa1), Amazonía (Brasil)", lat=-2.8567, lon=-54.9589, buffer_km=10,
         etiqueta="no_analogo", excluido_auc=False, coordenada_no_verificada=False,
         cita="AmeriFlux BR-Sa1, https://ameriflux.lbl.gov/sites/siteinfo/BR-Sa1 ; IGBP EBF"),
    dict(nombre="Bondville, Illinois (US-Bo1), llanura agrícola (EE. UU.)", lat=40.0062, lon=-88.2904, buffer_km=5,
         etiqueta="no_analogo", excluido_auc=False, coordenada_no_verificada=False,
         cita="AmeriFlux US-Bo1, 10.17190/AMF/1246036 ; IGBP CRO"),
    dict(nombre="Harvard Forest EMS (US-Ha1), Massachusetts (EE. UU.)", lat=42.5378, lon=-72.1715, buffer_km=5,
         etiqueta="no_analogo", excluido_auc=False, coordenada_no_verificada=False,
         cita="AmeriFlux US-Ha1, 10.17190/AMF/1246059 ; IGBP DBF"),
    dict(nombre="Tumbarumba (AU-Tum), Nueva Gales del Sur (Australia)", lat=-35.6566, lon=148.1517, buffer_km=5,
         etiqueta="no_analogo", excluido_auc=False, coordenada_no_verificada=False,
         cita="FLUXNET AU-Tum, 10.18140/FLX/1440126 ; IGBP EBF"),
    dict(nombre="Hainich (DE-Hai), Turingia (Alemania)", lat=51.0792, lon=10.4522, buffer_km=5,
         etiqueta="no_analogo", excluido_auc=False, coordenada_no_verificada=False,
         cita="FLUXNET DE-Hai, 10.18140/FLX/1440148 ; IGBP DBF"),
    dict(nombre="Hyytiälä / SMEAR II (FI-Hyy), Finlandia", lat=61.8474, lon=24.2948, buffer_km=5,
         etiqueta="no_analogo", excluido_auc=False, coordenada_no_verificada=False,
         cita="FLUXNET FI-Hyy, 10.18140/FLX/1440158 ; IGBP ENF"),
]

# Rasgos sintéticos a escala de 1 km (MOCK). No son mediciones de campo.
SITE_FEATURES = {
    "Yungay, núcleo hiperárido del Atacama (Chile)": dict(elevation=1200, slope=4.0, roughness=80.0),
    "Estructura de impacto de Haughton, isla Devon (Nunavut, Canadá)": dict(elevation=180, slope=11.0, roughness=260.0),
    "University Valley, Valles Secos de McMurdo (Antártida)": dict(elevation=1700, slope=8.0, roughness=200.0),
    "Askja / colada basáltica Vikrahraun 1961 (Islandia)": dict(elevation=1100, slope=8.0, roughness=180.0),
    "Conos de ceniza de la cumbre de Mauna Kea (Hawái, EE. UU.)": dict(elevation=4000, slope=14.0, roughness=340.0),
    "Sverrefjell, complejo volcánico de Bockfjorden (Svalbard, Noruega)": dict(elevation=400, slope=10.0, roughness=220.0),
    "Parque Nacional de Timanfaya, Lanzarote (España)": dict(elevation=350, slope=7.0, roughness=160.0),
    "Meteor Crater (Barringer), Arizona (EE. UU.)": dict(elevation=1670, slope=16.0, roughness=420.0),
    "S P Mountain (S P Crater), campo volcánico de San Francisco, Arizona (EE. UU.)": dict(elevation=1900, slope=12.0, roughness=300.0),
    "Inferno Chasm, llanura de Snake River / entorno de Craters of the Moon, Idaho (EE. UU.)": dict(elevation=1500, slope=9.0, roughness=240.0),
    "Peña de Hierro / cabecera del Río Tinto (Huelva, España)": dict(elevation=350, slope=6.0, roughness=110.0),
    "Ries (Nördlinger Ries), Alemania": dict(elevation=430, slope=2.0, roughness=30.0),
    "Cuenca de Sudbury, Ontario (Canadá)": dict(elevation=300, slope=2.5, roughness=35.0),
    "FLONA Tapajós, torre LBA km 67 (BR-Sa1), Amazonía (Brasil)": dict(elevation=120, slope=1.0, roughness=16.0),
    "Bondville, Illinois (US-Bo1), llanura agrícola (EE. UU.)": dict(elevation=220, slope=0.4, roughness=10.0),
    "Harvard Forest EMS (US-Ha1), Massachusetts (EE. UU.)": dict(elevation=340, slope=3.0, roughness=40.0),
    "Tumbarumba (AU-Tum), Nueva Gales del Sur (Australia)": dict(elevation=1200, slope=5.0, roughness=50.0),
    "Hainich (DE-Hai), Turingia (Alemania)": dict(elevation=440, slope=4.0, roughness=45.0),
    "Hyytiälä / SMEAR II (FI-Hyy), Finlandia": dict(elevation=180, slope=2.0, roughness=25.0),
}

# TRI en metros sobre grilla de ≈ 1 km. Bandas A–G.
REF_DIST = {
    "mars": {
        "A": (900, 350, 5.5, 2.0, 120.0, 40.0),
        "B": (1100, 350, 4.8, 1.8, 110.0, 35.0),
        "C": (700, 400, 6.0, 2.2, 140.0, 45.0),
        "D": (500, 300, 4.0, 2.0, 100.0, 35.0),
        "E": (800, 350, 6.5, 2.2, 150.0, 45.0),
        "F": (600, 300, 8.5, 2.5, 200.0, 60.0),
        "G": (500, 280, 9.0, 2.5, 220.0, 60.0),
    },
    "moon": {
        "A": (4200, 1100, 13.0, 3.5, 360.0, 90.0),
        "B": (3800, 1100, 13.5, 3.5, 370.0, 90.0),
        "C": (2500, 900, 14.5, 3.5, 400.0, 100.0),
        "D": (2200, 850, 14.0, 3.5, 380.0, 100.0),
        "E": (2000, 800, 14.0, 3.5, 390.0, 100.0),
        "F": (1800, 800, 15.0, 4.0, 430.0, 110.0),
        "G": (1600, 750, 16.0, 4.0, 450.0, 110.0),
    },
}

# Elevación regional aproximada (MOCK) para el modo relieve_relativo:
# relieve = elevación - elevación regional de entorno.
SITE_REGIONAL_ELEV = {
    "Yungay, núcleo hiperárido del Atacama (Chile)": 1100,
    "Estructura de impacto de Haughton, isla Devon (Nunavut, Canadá)": 140,
    "University Valley, Valles Secos de McMurdo (Antártida)": 1550,
    "Askja / colada basáltica Vikrahraun 1961 (Islandia)": 900,
    "Conos de ceniza de la cumbre de Mauna Kea (Hawái, EE. UU.)": 3200,
    "Sverrefjell, complejo volcánico de Bockfjorden (Svalbard, Noruega)": 200,
    "Parque Nacional de Timanfaya, Lanzarote (España)": 200,
    "Meteor Crater (Barringer), Arizona (EE. UU.)": 1650,
    "S P Mountain (S P Crater), campo volcánico de San Francisco, Arizona (EE. UU.)": 1700,
    "Inferno Chasm, llanura de Snake River / entorno de Craters of the Moon, Idaho (EE. UU.)": 1400,
    "Peña de Hierro / cabecera del Río Tinto (Huelva, España)": 300,
    "Ries (Nördlinger Ries), Alemania": 420,
    "Cuenca de Sudbury, Ontario (Canadá)": 280,
    "FLONA Tapajós, torre LBA km 67 (BR-Sa1), Amazonía (Brasil)": 110,
    "Bondville, Illinois (US-Bo1), llanura agrícola (EE. UU.)": 215,
    "Harvard Forest EMS (US-Ha1), Massachusetts (EE. UU.)": 320,
    "Tumbarumba (AU-Tum), Nueva Gales del Sur (Australia)": 1100,
    "Hainich (DE-Hai), Turingia (Alemania)": 400,
    "Hyytiälä / SMEAR II (FI-Hyy), Finlandia": 170,
}

PRIORITY_SEEDS = [
    {"id": "chimborazo", "nombre": "Chimborazo (arenal y páramo)", "lat": -1.47, "lon": -78.82},
    {"id": "cotopaxi", "nombre": "Cotopaxi (páramo)", "lat": -0.68, "lon": -78.44},
    {"id": "antisana", "nombre": "Antisana", "lat": -0.48, "lon": -78.14},
    {"id": "el_altar", "nombre": "El Altar", "lat": -1.67, "lon": -78.41},
    {"id": "quilotoa", "nombre": "Quilotoa", "lat": -0.85, "lon": -78.90},
    {"id": "fernandina", "nombre": "Fernandina (Galápagos)", "lat": -0.37, "lon": -91.55},
    {"id": "cayambe", "nombre": "Cayambe", "lat": 0.03, "lon": -77.99},
    {"id": "sincholagua", "nombre": "Sincholagua", "lat": -0.54, "lon": -78.37},
]


def _clip(x, lo, hi):
    return np.minimum(np.maximum(x, lo), hi)


def make_reference(body: str, rng: np.random.Generator, n_per_band: int = 160) -> dict[str, np.ndarray]:
    lats, elevs, slopes, tris = [], [], [], []
    for band in BANDS:
        mu_e, sd_e, mu_s, sd_s, mu_t, sd_t = REF_DIST[body][band.name]
        # Mitad norte, mitad sur (bandas simétricas).
        u = rng.uniform(band.abs_lat_min + 0.2, band.abs_lat_max - 0.2, size=n_per_band)
        sign = rng.choice(np.array([-1.0, 1.0]), size=n_per_band)
        lat = u * sign
        elev = rng.normal(mu_e, sd_e, size=n_per_band)
        sl = _clip(rng.normal(mu_s, sd_s, size=n_per_band), 0.05, 60.0)
        tri = _clip(rng.normal(mu_t, sd_t, size=n_per_band), 0.2, 2000.0)
        lats.append(lat)
        elevs.append(elev)
        slopes.append(sl)
        tris.append(tri)
    return {
        "latitude": np.concatenate(lats),
        "elevation": np.concatenate(elevs),
        "slope": np.concatenate(slopes),
        "roughness": np.concatenate(tris),
    }


# Polígono aproximado del Ecuador continental (lon, lat) y elipses de Galápagos.
MAINLAND = np.array(
    [
        [-80.06, 1.47],
        [-79.00, 1.43],
        [-77.40, 1.20],
        [-75.40, 0.95],
        [-75.20, 0.10],
        [-75.40, -1.20],
        [-75.70, -2.20],
        [-76.90, -3.50],
        [-78.20, -4.75],
        [-79.20, -4.50],
        [-80.20, -3.40],
        [-81.05, -2.75],
        [-81.10, -1.50],
        [-80.90, -0.70],
        [-80.50, 0.40],
        [-80.06, 1.47],
    ]
)
GALAPAGOS = [
    # (lon, lat, radio_lon, radio_lat) islas principales
    (-91.55, -0.37, 0.18, 0.16),  # Fernandina
    (-91.15, -0.45, 0.55, 0.55),  # Isabela
    (-90.50, -0.65, 0.28, 0.22),  # Santiago / Santa Cruz zona
    (-90.32, -0.74, 0.22, 0.16),  # Santa Cruz
    (-90.05, -0.90, 0.18, 0.14),  # San Cristóbal
    (-90.02, -1.30, 0.14, 0.12),  # Española
    (-89.62, -1.00, 0.10, 0.08),  # pequeña
]


def point_in_poly(lon: np.ndarray, lat: np.ndarray, poly: np.ndarray) -> np.ndarray:
    x, y = lon, lat
    x0, y0 = poly[:-1, 0], poly[:-1, 1]
    x1, y1 = poly[1:, 0], poly[1:, 1]
    inside = np.zeros(x.shape, dtype=bool)
    for xa, ya, xb, yb in zip(x0, y0, x1, y1):
        cond = ((ya > y) != (yb > y)) & (x < (xb - xa) * (y - ya) / (yb - ya + 1e-16) + xa)
        inside ^= cond
    return inside


def ecuador_land_mask(lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
    land = point_in_poly(lon, lat, MAINLAND)
    for cx, cy, rx, ry in GALAPAGOS:
        land |= ((lon - cx) / rx) ** 2 + ((lat - cy) / ry) ** 2 <= 1.0
    return land


def synthetic_ecuador_dem(lon: np.ndarray, lat: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """DEM sintético con Andes, costa, Amazonía y conos de Galápagos."""
    z = np.zeros_like(lon)

    # Dos cordilleras andinas (occidental y oriental).
    west_axis = -79.00
    east_axis = -78.20
    ridge_w = 0.28
    along = np.exp(-((lat - -1.2) ** 2) / (3.5**2))  # más altos en el centro-sur
    z += 3800 * along * np.exp(-((lon - west_axis) ** 2) / (ridge_w**2))
    z += 4400 * along * np.exp(-((lon - east_axis) ** 2) / (ridge_w**2))
    # Interandino más bajo.
    z -= 800 * along * np.exp(-((lon + 78.55) ** 2) / (0.16**2))

    # Picos (añaden relieve local). sig en grados; más estrechos → más pendiente.
    peaks = [
        (-78.82, -1.47, 1600, 0.05),  # Chimborazo
        (-78.44, -0.68, 1300, 0.045),  # Cotopaxi
        (-78.14, -0.48, 1200, 0.045),  # Antisana
        (-77.99, 0.03, 1100, 0.045),  # Cayambe
        (-78.41, -1.67, 1000, 0.045),  # El Altar
        (-78.90, -0.85, 600, 0.04),  # Quilotoa
        (-78.37, -0.54, 500, 0.04),
    ]
    for px, py, amp, sig in peaks:
        z += amp * np.exp(-(((lon - px) ** 2 + (lat - py) ** 2) / (2 * sig**2)))

    # Costa baja al oeste de ~-80, Amazonía baja al este de ~-77.
    coast = 1 / (1 + np.exp((lon + 80.0) / 0.15))
    amazon = 1 / (1 + np.exp(-(lon + 77.2) / 0.25))
    z = z * (1 - 0.85 * coast) * (1 - 0.80 * amazon)
    z += 40 * (1 - amazon) * (1 - coast)
    z += 280 * amazon  # llanura amazónica
    z += 80 * coast

    # Galápagos: base de isla + conos.
    for cx, cy, rx, ry in GALAPAGOS:
        island = np.exp(-(((lon - cx) / (rx * 0.9)) ** 2 + ((lat - cy) / (ry * 0.9)) ** 2))
        z = np.where(island > 0.12, np.maximum(z, 80 + 900 * island), z)
    z += 1100 * np.exp(-(((lon + 91.55) ** 2 + (lat + 0.37) ** 2) / (2 * 0.06**2)))  # Fernandina

    # Ruido de alta frecuencia: aporta TRI residual, aparte de la pendiente regional.
    z += rng.normal(0, 8, size=z.shape)
    z += 25 * rng.normal(0, 1, size=z.shape) * (z > 1500)
    return _clip(z, 0, 6310)


def mock_climate(lon: np.ndarray, lat: np.ndarray) -> dict[str, np.ndarray]:
    """Climatología sintética: interpretación, no entra al índice."""
    # Precipitación: Amazonía muy húmeda, costa sur más seca, Andes orográfico.
    amazon = 1 / (1 + np.exp(-(lon + 77.2) / 0.25))
    dry_coast = 1 / (1 + np.exp((lon + 80.2) / 0.2)) * (lat < 0.2)
    precip = 3200 * amazon + 1400 * (1 - amazon) * (1 - dry_coast) + 200 * dry_coast
    precip += 400 * np.exp(-((lon + 78.6) ** 2) / 0.4)  # flancos andinos
    # Temperatura media baja en altura (se usará elevación aproximada por lat-lon).
    # Se rellena después si hace falta; aquí un campo de T a nivel del suelo.
    t_base = 27 - 0.4 * np.abs(lat) - 4 * (1 / (1 + np.exp((lon + 79) / 0.3)))
    return {"precip_mm": precip, "t_base_c": t_base}


def colorize_delta(values: np.ndarray, mask: np.ndarray, palette: list[tuple[int, int, int]]) -> np.ndarray:
    v = np.clip(np.where(mask, values, np.nan), 0.0, 1.0)
    n = len(palette) - 1
    idx = np.where(np.isfinite(v), v * n, 0.0)
    i0 = np.floor(idx).astype(int)
    i1 = np.minimum(i0 + 1, n)
    t = (idx - i0)[..., None]
    pal = np.array(palette, dtype=float)
    rgb = pal[i0] * (1 - t) + pal[i1] * t
    alpha = np.where(mask & np.isfinite(values), 210, 0)
    rgba = np.concatenate([rgb.astype(np.uint8), alpha[..., None].astype(np.uint8)], axis=-1)
    return rgba


def colorize_class(clas: np.ndarray, mask: np.ndarray) -> np.ndarray:
    colors = {
        0: (48, 52, 58, 150),  # ninguno
        1: (196, 86, 54, 220),  # marte
        2: (220, 214, 198, 220),  # luna
        3: (212, 160, 84, 230),  # ambos
    }
    rgba = np.zeros(clas.shape + (4,), dtype=np.uint8)
    for k, c in colors.items():
        sel = mask & (clas == k)
        rgba[sel] = c
    return rgba


def colorize_climate(precip: np.ndarray, mask: np.ndarray) -> np.ndarray:
    # De ámbar seco a azul húmedo (capa de interpretación).
    p = np.clip((precip - 200) / 3000, 0, 1)
    pal = [(180, 130, 60), (200, 190, 120), (120, 170, 150), (50, 110, 160), (30, 60, 130)]
    return colorize_delta(p, mask, pal)


def save_png(path: Path, rgba: np.ndarray) -> None:
    Image.fromarray(rgba, mode="RGBA").save(path)


def encode_f32(arr: np.ndarray) -> str:
    import base64

    return base64.b64encode(np.asarray(arr, dtype=np.float32).tobytes()).decode("ascii")


def encode_i8(arr: np.ndarray) -> str:
    import base64

    return base64.b64encode(np.asarray(arr, dtype=np.int8).tobytes()).decode("ascii")


def nearest_cell(lon, lat, lon_2d, lat_2d, mask):
    d2 = (lon_2d - lon) ** 2 + (lat_2d - lat) ** 2
    d2 = np.where(mask, d2, np.inf)
    idx = np.unravel_index(np.argmin(d2), d2.shape)
    return idx


def climate_card(elev, precip, t_base):
    # Gradiente aproximado 6.5 °C / 1000 m
    t_mean = float(t_base) - 6.5 * (float(elev) / 1000.0)
    t_min = t_mean - 6
    t_max = t_mean + 6
    p = float(precip)
    # Mes más húmedo / seco sintéticos (Amazonía más uniforme, interandino más estacional).
    if p > 2500:
        wet, dry, wet_m, dry_m = p / 9, p / 18, "abril", "agosto"
    elif p < 600:
        wet, dry, wet_m, dry_m = p / 6, p / 40, "febrero", "agosto"
    else:
        wet, dry, wet_m, dry_m = p / 8, p / 20, "abril", "agosto"
    return {
        "advertencia": "Interpretación, no entra al índice",
        "temperatura_media_c": round(t_mean, 1),
        "temperatura_min_c": round(t_min, 1),
        "temperatura_max_c": round(t_max, 1),
        "precipitacion_anual_mm": round(p, 0),
        "mes_mas_humedo": wet_m,
        "precipitacion_mes_humedo_mm": round(wet, 0),
        "mes_mas_seco": dry_m,
        "precipitacion_mes_seco_mm": round(dry, 0),
        "nota": "Homología de superficie frente a similitud climática temporal: no confundir ambas.",
    }


def main() -> None:
    rng = np.random.default_rng(SEED)
    OUT_WEB.mkdir(parents=True, exist_ok=True)

    # --- Referencias planetarias y firmas --------------------------------
    # La variable latitude entra al índice como |lat| (criterio de Expertos).
    refs = {body: make_reference(body, rng) for body in ("mars", "moon")}
    params = {}
    sigs = {}
    samples = {}
    for body, ref in refs.items():
        ref_abs = with_abs_latitude({k: ref[k] for k in INDEX_VARS})
        params[body] = fit_std_params(
            ref_abs,
            body_ref=body,
            method="zscore",
            frozen_at=FROZEN_AT,
        )
        samples[body] = sample_by_lat_bands(
            ref["latitude"],
            {k: ref_abs[k] for k in INDEX_VARS},
            BANDS,
            min_cells=50,
            rng=rng,
        )
        # sample_by_lat_bands reescribe latitude con el valor firmado; se
        # vuelve a |lat| para que la firma sea coherente con el índice.
        for band, smp in samples[body].items():
            if "latitude" in smp and smp["latitude"].size:
                smp["latitude"] = np.abs(smp["latitude"])
        sigs[body] = build_signatures(body, samples[body], INDEX_VARS)

    # --- Validación ------------------------------------------------------
    sites = []
    for s in VALIDATION_SITES:
        feat = SITE_FEATURES[s["nombre"]]
        row = {
            **s,
            "elevacion_m": feat["elevation"],
            "pendiente_deg": feat["slope"],
            "rugosidad_tri": feat["roughness"],
            "es_provisional": False,
            "es_mock_superficies": True,
        }
        sites.append(row)

    def site_values(rows):
        return {
            "latitude": np.array([r["lat"] for r in rows], float),
            "elevation": np.array([r["elevacion_m"] for r in rows], float),
            "slope": np.array([r["pendiente_deg"] for r in rows], float),
            "roughness": np.array([r["rugosidad_tri"] for r in rows], float),
        }

    vals = site_values(sites)
    site_bands = assign_lat_band(vals["latitude"], BANDS)

    # Askja entra al AUC si INCLUIR_ASKJA (por defecto True, coordenada ya confirmada).
    in_auc = []
    for r in sites:
        if "Askja" in r["nombre"] and not INCLUIR_ASKJA:
            r["excluido_auc"] = True
        in_auc.append(not r["excluido_auc"])
    in_auc = np.array(in_auc, dtype=bool)
    y_pos_all = {
        "mars": np.array([1 if r["etiqueta"] in {"marciano", "ambos"} else 0 for r in sites]),
        "moon": np.array([1 if r["etiqueta"] in {"lunar", "ambos"} else 0 for r in sites]),
    }

    def evaluar(modo: str, variables, vals_in):
        """Corre el índice de punta a punta (distancia, d_max, delta, umbral, AUC)."""
        dist = {}
        win = {}
        for body in ("mars", "moon"):
            d, _, wband = delta_index(
                vals_in, sigs[body], params[body],
                lat_band=site_bands, body_ref=body, d_max=1.0,
                iqr_penalty=0.5, modo_bandas=modo, variables=variables,
            )
            dist[body] = d
            win[body] = wband
        d_max = {}
        for body in ("mars", "moon"):
            pos = (y_pos_all[body] == 1) & in_auc
            dpos = dist[body][pos]
            d_max[body] = float(np.nanmax(dpos) * 1.15) if dpos.size else 1.0
            if not np.isfinite(d_max[body]) or d_max[body] <= 0:
                d_max[body] = 1.0
        delta = {}
        win2 = {}
        for body in ("mars", "moon"):
            d, de, wband = delta_index(
                vals_in, sigs[body], params[body],
                lat_band=site_bands, body_ref=body, d_max=d_max[body],
                iqr_penalty=0.5, modo_bandas=modo, variables=variables,
            )
            delta[body] = de
            win2[body] = wband
        y_m = y_pos_all["mars"][in_auc]
        y_l = y_pos_all["moon"][in_auc]
        thr = {
            "mars": choose_threshold(delta["mars"][in_auc], y_m, metric="youden", d_max=d_max["mars"]),
            "moon": choose_threshold(delta["moon"][in_auc], y_l, metric="youden", d_max=d_max["moon"]),
        }
        clas = classify(delta["mars"], delta["moon"], thr["mars"].threshold, thr["moon"].threshold)
        return {"dist": dist, "delta": delta, "win": win2, "d_max": d_max, "thr": thr, "clas": clas}

    # Variantes: ambos modos de bandas, y sensibilidad sin latitud en el vector.
    evals = {
        MODO_TODAS_MIN: evaluar(MODO_TODAS_MIN, INDEX_VARS, vals),
        MODO_BANDA_PROPIA: evaluar(MODO_BANDA_PROPIA, INDEX_VARS, vals),
        "todas_min_sin_latitud": evaluar(MODO_TODAS_MIN, VARS_SIN_LATITUD, vals),
    }
    # Variante relieve_relativo (pendiente de decisión del equipo, §3).
    vals_rel = dict(vals)
    vals_rel["elevation"] = np.array(
        [r["elevacion_m"] - SITE_REGIONAL_ELEV[r["nombre"]] for r in sites], float
    )
    evals["todas_min_relieve_relativo"] = evaluar(MODO_TODAS_MIN, INDEX_VARS, vals_rel)

    ev = evals[MODO_DEFAULT]
    distances, deltas, winners = ev["dist"], ev["delta"], ev["win"]
    d_max, thr = ev["d_max"], ev["thr"]

    def metricas_de(evx, etiqueta):
        y_m = y_pos_all["mars"][in_auc]
        y_l = y_pos_all["moon"][in_auc]
        sm, sl_ = evx["delta"]["mars"][in_auc], evx["delta"]["moon"][in_auc]
        return {
            "etiqueta": etiqueta,
            "marte": {**evx["thr"]["mars"].as_dict(), **{k: bootstrap_auc_ci(y_m, sm)[k] for k in ("ic95_inferior", "ic95_superior", "n_bootstrap")}},
            "luna": {**evx["thr"]["moon"].as_dict(), **{k: bootstrap_auc_ci(y_l, sl_)[k] for k in ("ic95_inferior", "ic95_superior", "n_bootstrap")}},
            "d_max": evx["d_max"],
        }

    metricas_por_variante = {
        "todas_min_con_latitud": metricas_de(evals[MODO_TODAS_MIN], "todas_min, vector con |lat| (defecto)"),
        "banda_propia_con_latitud": metricas_de(evals[MODO_BANDA_PROPIA], "banda_propia, vector con |lat|"),
        "todas_min_sin_latitud": metricas_de(evals["todas_min_sin_latitud"], "todas_min, sin latitud en el vector"),
        "todas_min_relieve_relativo": metricas_de(evals["todas_min_relieve_relativo"], "todas_min, elevación en modo relieve_relativo"),
    }
    y_m = y_pos_all["mars"][in_auc]
    y_l = y_pos_all["moon"][in_auc]
    delong = {
        "marte_con_vs_sin_latitud": delong_paired(
            y_m, evals[MODO_TODAS_MIN]["delta"]["mars"][in_auc],
            evals["todas_min_sin_latitud"]["delta"]["mars"][in_auc],
        ),
        "luna_con_vs_sin_latitud": delong_paired(
            y_l, evals[MODO_TODAS_MIN]["delta"]["moon"][in_auc],
            evals["todas_min_sin_latitud"]["delta"]["moon"][in_auc],
        ),
    }
    nulo = {
        "marte": null_abs_lat_auc(y_m, vals["latitude"][in_auc]),
        "luna": null_abs_lat_auc(y_l, vals["latitude"][in_auc]),
        "nota": "Modelo nulo: el puntaje es solo |lat|. Los positivos de este conjunto tienden a latitudes altas y podrían inflar el AUC del índice si la latitud domina.",
    }

    pred_names = [CLASS_NAMES[int(c)] for c in ev["clas"]]
    known_map = {"marciano": "marte", "lunar": "luna", "ambos": "ambos", "no_analogo": "ninguno"}
    known_names = [known_map[r["etiqueta"]] for r in sites]
    # Métricas por clase solo con los sitios que entran al AUC.
    class_metrics = per_class_metrics(
        [n for n, ok in zip(known_names, in_auc) if ok],
        [n for n, ok in zip(pred_names, in_auc) if ok],
    )

    for i, r in enumerate(sites):
        r["banda_latitud"] = str(site_bands[i])
        r["banda_ganadora_marte"] = str(winners["mars"][i])
        r["banda_ganadora_luna"] = str(winners["moon"][i])
        r["delta_marte"] = round(float(deltas["mars"][i]), 4)
        r["delta_luna"] = round(float(deltas["moon"][i]), 4)
        r["distancia_marte"] = round(float(distances["mars"][i]), 4)
        r["distancia_luna"] = round(float(distances["moon"][i]), 4)
        r["clase_predicha"] = pred_names[i]
        r["clase_conocida"] = known_names[i]
        r["acierto"] = pred_names[i] == known_names[i]
        r["entra_al_auc"] = not r["excluido_auc"]
        r["fuente"] = r["cita"]

    # --- Grilla de Ecuador -----------------------------------------------
    # Los umbrales y d_max ya están congelados con la misma regla
    # (mínimo entre bandas, si modo=todas_min) sobre el conjunto de
    # validación. A partir de aquí no se reajustan.
    res = RES_DEG
    west, north = EC_WEST, EC_NORTH
    ncols = int(round((EC_EAST - EC_WEST) / res))
    nrows = int(round((EC_NORTH - EC_SOUTH) / res))
    transform = GeoTransform(west=west, north=north, res_lon=res, res_lat=-res)
    cols, rows = np.meshgrid(np.arange(ncols), np.arange(nrows))
    lon, lat = transform.pixel_center(rows, cols)
    mask = ecuador_land_mask(lon, lat)

    dem = synthetic_ecuador_dem(lon, lat, rng)
    dem = np.where(mask, dem, np.nan)
    res_x_m, res_y_m = cell_sizes_m(lat, -res, res)
    sl = slope(dem, res_y_m=res_y_m, res_x_m=res_x_m[0] if False else res_x_m)
    # res_x_m is 2D already (from lat 2D)
    tri = roughness_tri(dem)
    sl = np.where(mask, sl, np.nan)
    tri = np.where(mask, tri, np.nan)

    climate = mock_climate(lon, lat)
    climate = {k: np.where(mask, v, np.nan) for k, v in climate.items()}

    grid_vals = {
        "latitude": lat,
        "elevation": dem,
        "slope": sl,
        "roughness": tri,
    }
    grid_bands = assign_lat_band(lat, BANDS)
    # Solo celdas de tierra con banda asignada.
    flat_mask = mask.ravel()
    delta_grid = {}
    dist_grid = {}
    win_grid = {}
    for body in ("mars", "moon"):
        gv = {k: v.ravel() for k, v in grid_vals.items()}
        # Celdas sin banda o agua: se dejan nan.
        dist, delta, win = delta_index(
            gv,
            sigs[body],
            params[body],
            lat_band=np.asarray(grid_bands).ravel(),
            body_ref=body,
            d_max=d_max[body],
            iqr_penalty=0.5,
            modo_bandas=MODO_DEFAULT,
        )
        dist = dist.reshape(lat.shape)
        delta = delta.reshape(lat.shape)
        win = np.asarray(win).reshape(lat.shape)
        dist = np.where(mask, dist, np.nan)
        delta = np.where(mask, delta, np.nan)
        dist_grid[body] = dist
        delta_grid[body] = delta
        win_grid[body] = win

    clas = classify(
        delta_grid["mars"],
        delta_grid["moon"],
        thr["mars"].threshold,
        thr["moon"].threshold,
        valid_mask=mask,
    )

    # --- Zonas prioritarias ----------------------------------------------
    zones = []
    for seed in PRIORITY_SEEDS:
        i, j = nearest_cell(seed["lon"], seed["lat"], lon, lat, mask)
        if not mask[i, j]:
            continue
        dm = float(delta_grid["mars"][i, j])
        dl = float(delta_grid["moon"][i, j])
        if not np.isfinite(dm) or not np.isfinite(dl):
            continue
        cl = CLASS_NAMES[int(clas[i, j])]
        elev = float(dem[i, j])
        zona = {
            "id": seed["id"],
            "nombre": seed["nombre"],
            "lat": seed["lat"],
            "lon": seed["lon"],
            "banda_latitud": str(grid_bands[i, j]),
            "elevacion_m": round(elev, 0),
            "pendiente_deg": round(float(sl[i, j]), 2),
            "rugosidad_tri": round(float(tri[i, j]), 2),
            "delta_marte": round(dm, 4),
            "delta_luna": round(dl, 4),
            "banda_ganadora_marte": str(win_grid["mars"][i, j]),
            "banda_ganadora_luna": str(win_grid["moon"][i, j]),
            "clase": cl,
            "firma_superficie": {
                "latitud": seed["lat"],
                "elevacion_m": round(elev, 0),
                "pendiente_deg": round(float(sl[i, j]), 2),
                "rugosidad_tri": round(float(tri[i, j]), 2),
            },
            "clima": climate_card(elev, climate["precip_mm"][i, j], climate["t_base_c"][i, j]),
        }
        zones.append(zona)
    # Añadir la celda terrestre con mayor similitud a Marte, si no está ya en la lista.
    if np.isfinite(delta_grid["mars"]).any():
        idx = np.nanargmax(np.where(mask, delta_grid["mars"], np.nan))
        i, j = np.unravel_index(idx, delta_grid["mars"].shape)
        already = any(abs(z["lat"] - float(lat[i, j])) < 0.15 and abs(z["lon"] - float(lon[i, j])) < 0.15 for z in zones)
        if (not already) and CLASS_NAMES[int(clas[i, j])] in {"marte", "ambos", "luna"}:
            elev = float(dem[i, j])
            zones.append({
                "id": "max_marte",
                "nombre": "Faldas orientales (Zamora-Chinchipe)",
                "lat": round(float(lat[i, j]), 4),
                "lon": round(float(lon[i, j]), 4),
                "banda_latitud": str(grid_bands[i, j]),
                "elevacion_m": round(elev, 0),
                "pendiente_deg": round(float(sl[i, j]), 2),
                "rugosidad_tri": round(float(tri[i, j]), 2),
                "delta_marte": round(float(delta_grid["mars"][i, j]), 4),
                "delta_luna": round(float(delta_grid["moon"][i, j]), 4),
                "banda_ganadora_marte": str(win_grid["mars"][i, j]),
                "banda_ganadora_luna": str(win_grid["moon"][i, j]),
                "clase": CLASS_NAMES[int(clas[i, j])],
                "firma_superficie": {
                    "latitud": round(float(lat[i, j]), 4),
                    "elevacion_m": round(elev, 0),
                    "pendiente_deg": round(float(sl[i, j]), 2),
                    "rugosidad_tri": round(float(tri[i, j]), 2),
                },
                "clima": climate_card(elev, climate["precip_mm"][i, j], climate["t_base_c"][i, j]),
            })
    # Priorizar las de mayor similitud (máximo de los dos deltas).
    zones.sort(key=lambda z: max(z["delta_marte"], z["delta_luna"]), reverse=True)

    # --- PNGs ------------------------------------------------------------
    pal_mars = [(20, 10, 8), (80, 30, 22), (150, 55, 35), (210, 100, 50), (240, 180, 90)]
    pal_moon = [(12, 12, 14), (50, 52, 58), (110, 110, 118), (180, 178, 172), (236, 232, 222)]
    save_png(OUT_WEB / "delta_marte.png", colorize_delta(delta_grid["mars"], mask, pal_mars))
    save_png(OUT_WEB / "delta_luna.png", colorize_delta(delta_grid["moon"], mask, pal_moon))
    save_png(OUT_WEB / "clases.png", colorize_class(clas, mask))
    save_png(OUT_WEB / "clima.png", colorize_climate(climate["precip_mm"], mask))

    # Variante punta a punta con modo banda_propia (Ecuador + umbrales propios).
    ev_own = evals[MODO_BANDA_PROPIA]
    own_dir = OUT_WEB / "banda_propia"
    own_dir.mkdir(parents=True, exist_ok=True)
    delta_own, clas_own_counts = {}, None
    for body in ("mars", "moon"):
        gv = {k: v.ravel() for k, v in grid_vals.items()}
        _, delta_o, _ = delta_index(
            gv, sigs[body], params[body],
            lat_band=np.asarray(grid_bands).ravel(),
            body_ref=body, d_max=ev_own["d_max"][body],
            iqr_penalty=0.5, modo_bandas=MODO_BANDA_PROPIA,
        )
        delta_o = np.where(mask, delta_o.reshape(lat.shape), np.nan)
        delta_own[body] = delta_o
    clas_own = classify(
        delta_own["mars"], delta_own["moon"],
        ev_own["thr"]["mars"].threshold, ev_own["thr"]["moon"].threshold,
        valid_mask=mask,
    )
    save_png(own_dir / "delta_marte.png", colorize_delta(delta_own["mars"], mask, pal_mars))
    save_png(own_dir / "delta_luna.png", colorize_delta(delta_own["moon"], mask, pal_moon))
    save_png(own_dir / "clases.png", colorize_class(clas_own, mask))
    clas_own_counts = {CLASS_NAMES[k]: int(np.sum((clas_own == k) & mask)) for k in (0, 1, 2, 3)}

    # --- Catálogo JSON ---------------------------------------------------
    variables = [
        {
            "nombre": "latitude",
            "unidad": "grados",
            "en_indice": True,
            "valor_nodata": None,
            "fuente_por_cuerpo": {
                "moon": "Coordenada planetocéntrica de la grilla (LRO/LOLA, Marco IAU)",
                "mars": "Coordenada planetocéntrica de la grilla (MOLA, Marco IAU)",
                "earth": "Coordenada geográfica WGS 84",
            },
            "resolucion_nativa_m_por_cuerpo": {"moon": 1000, "mars": 1000, "earth": 1000},
            "notas": "Proxy de régimen de insolación y clave de la banda de muestreo.",
        },
        {
            "nombre": "elevation",
            "unidad": "m",
            "en_indice": True,
            "valor_nodata": None,
            "fuente_por_cuerpo": {
                "moon": "LOLA (LRO) sobre la esfera de radio 1737.4 km",
                "mars": "MOLA, areoide MOLA",
                "earth": "Copernicus DEM GLO-90 (EGM2008). Se usa GLO-90 también fuera de Ecuador porque SRTM no cubre por encima de 60° (Isla Devon, Antártida).",
            },
            "resolucion_nativa_m_por_cuerpo": {"moon": 60, "mars": 463, "earth": 90},
            "datum_por_cuerpo": {
                "moon": "Esfera de 1737.4 km",
                "mars": "Areoide MOLA",
                "earth": "Geoide EGM2008 (Copernicus DEM GLO-90)",
            },
            "notas": "Pendiente y rugosidad se recalculan sobre el DEM ya remuestreado a 1 km.",
        },
        {
            "nombre": "slope",
            "unidad": "grados",
            "en_indice": True,
            "valor_nodata": None,
            "fuente_por_cuerpo": {
                "moon": "Calculada sobre LOLA remuestreado a 1 km",
                "mars": "Calculada sobre MOLA remuestreado a 1 km",
                "earth": "Calculada sobre Copernicus DEM GLO-90 remuestreado a 1 km",
            },
            "resolucion_nativa_m_por_cuerpo": {"moon": 1000, "mars": 1000, "earth": 1000},
            "notas": "No interpolar un ráster de pendiente de otra resolución.",
        },
        {
            "nombre": "roughness",
            "unidad": "m (TRI de Riley et al. 1999, ventana 3×3)",
            "en_indice": True,
            "valor_nodata": None,
            "fuente_por_cuerpo": {
                "moon": "TRI sobre LOLA remuestreado a 1 km",
                "mars": "TRI sobre MOLA remuestreado a 1 km",
                "earth": "TRI sobre Copernicus DEM GLO-90 remuestreado a 1 km",
            },
            "resolucion_nativa_m_por_cuerpo": {"moon": 1000, "mars": 1000, "earth": 1000},
            "notas": "Alternativa prevista: desviación estándar de la elevación en la misma ventana 3×3.",
        },
        {
            "nombre": "albedo",
            "unidad": "adimensional (0–1)",
            "en_indice": False,
            "valor_nodata": None,
            "fuente_por_cuerpo": {
                "moon": "LROC WAC (pendiente de confirmación)",
                "mars": "TES / THEMIS (pendiente de confirmación)",
                "earth": "Landsat 8/9 o MODIS (pendiente de confirmación)",
            },
            "resolucion_nativa_m_por_cuerpo": {"moon": 100, "mars": 300, "earth": 30},
            "notas": "Fuera del índice hasta que Expertos confirme que la definición es comparable en los tres cuerpos. El pipeline está listo para incluirla (en_indice=true).",
        },
        {
            "nombre": "thermal_inertia",
            "unidad": "J m⁻² K⁻¹ s⁻½",
            "en_indice": False,
            "valor_nodata": None,
            "fuente_por_cuerpo": {
                "moon": "Diviner (pendiente de confirmación)",
                "mars": "THEMIS / TES (pendiente de confirmación)",
                "earth": "Producto equivalente terrestre (pendiente de confirmación)",
            },
            "resolucion_nativa_m_por_cuerpo": {"moon": 200, "mars": 100, "earth": None},
            "notas": "Fuera del índice hasta que Expertos confirme comparabilidad. No hay variable meteorológica en el índice.",
        },
    ]

    bounds = {
        "oeste": transform.west,
        "norte": transform.north,
        "este": transform.east_of(ncols),
        "sur": transform.south_of(nrows),
    }

    catalog = {
        "mock": True,
        "aviso": "MOCK en las variables de superficie (elevación, pendiente, rugosidad). Coordenadas, buffers, etiquetas y citas del conjunto de validación son las verificadas por Expertos (validacion_parte1.md). Askja entra al AUC con la coordenada confirmada 65.060, -16.640 (buffer 6 km; Blasizzo et al., 2022, additional file 1).",
        "metric_version": "analog-delta-v1-superficie",
        "modo_bandas": MODO_DEFAULT,
        "modos_bandas_disponibles": [MODO_TODAS_MIN, MODO_BANDA_PROPIA],
        "nota_modo_bandas": "todas_min compara cada celda con las firmas de todas las bandas y conserva la distancia mínima y la banda ganadora (valor por defecto, pendiente de confirmación de Ronald sobre el §5). banda_propia solo usa la firma de la banda de |lat| de la celda. Ambos modos se corren de punta a punta; los rásteres por defecto son todas_min y la variante está en mock/banda_propia/.",
        "latitude_en_el_vector": "|lat| (grados de latitud absoluta)",
        "congelado_en": FROZEN_AT,
        "grilla": {
            "resolucion_objetivo_m": 1000,
            "resolucion_mock_deg": RES_DEG,
            "nota": "Producto MOCK calculado a 0.01° (≈ 1,1 km), cercano a la resolución objetivo de 1 km. Valores sintéticos.",
            "sistema": "geográfico, SRID 4326 nominal (planetocéntrico en Luna/Marte; WGS 84 en la Tierra). El campo body desambigua.",
            "filas": nrows,
            "columnas": ncols,
            "extension": bounds,
        },
        "variables_indice": list(INDEX_VARS),
        "pesos_por_defecto": {v: 0.25 for v in INDEX_VARS},
        "variables": variables,
        "bandas_latitud": [
            {"nombre": b.name, "abs_lat_min": b.abs_lat_min, "abs_lat_max": b.abs_lat_max} for b in BANDS
        ],
        "std_params": {body: [p.as_dict() for p in params[body]] for body in params},
        "signatures": {body: [s.as_dict() for s in sigs[body]] for body in sigs},
        "d_max": d_max,
        "umbrales": {
            "mars": {**thr["mars"].as_dict(), "cuerpo": "mars"},
            "moon": {**thr["moon"].as_dict(), "cuerpo": "moon"},
        },
        "metricas_validacion": {
            "marte": thr["mars"].as_dict(),
            "luna": thr["moon"].as_dict(),
            "precision_por_clase": class_metrics,
            "aciertos_auc": int(sum(r["acierto"] for r in sites if r["entra_al_auc"])),
            "n_sitios_auc": int(sum(1 for r in sites if r["entra_al_auc"])),
            "n_sitios": len(sites),
            "modo_bandas": MODO_DEFAULT,
        },
        "metricas_por_variante": metricas_por_variante,
        "delong_pareado": delong,
        "modelo_nulo_solo_abs_lat": nulo,
        "incluir_askja": INCLUIR_ASKJA,
        "elevacion_modo": ELEVACION_MODO_DEFAULT,
        "elevacion_modos_disponibles": list(ELEVACION_MODOS),
        "metricas_sensibilidad": metricas_por_variante,
        "clases_ecuador_banda_propia": clas_own_counts,
        "sitios_validacion": sites,
        "zonas_prioritarias": zones,
        "capas": {
            "delta_marte": {"archivo": "delta_marte.png", "tipo": "similitud", "cuerpo": "mars"},
            "delta_luna": {"archivo": "delta_luna.png", "tipo": "similitud", "cuerpo": "moon"},
            "clases": {"archivo": "clases.png", "tipo": "clase"},
            "clima": {
                "archivo": "clima.png",
                "tipo": "interpretacion",
                "etiqueta": "Interpretación, no entra al índice",
            },
        },
        "rasters": {
            "filas": nrows,
            "columnas": ncols,
            "extension": bounds,
            "nota": "Los valores continuos viajan en los PNG y en las fichas; no se incrusta la grilla completa en este JSON.",
        },
        "limitaciones": [
            "La analogía es parcial: solo cubre variables comparables en los tres cuerpos.",
            "Excluir la meteorología hace el índice más limpio, pero impide llamar «clima análogo» al resultado.",
            "La resolución única suaviza detalle local, sobre todo en los Andes. Este MOCK se calculó a ≈ 1,1 km (objetivo: 1 km).",
            "Marte y la Luna no se promedian en una sola firma.",
            "Albedo e inercia térmica no entran al índice (in_index=false). Expertos lo justifica en validacion_parte1.md, sección C: el albedo terrestre lo dominan vegetación y humedad; la inercia térmica aparente se invierte con modelos distintos en cada cuerpo. Tampoco entra la abundancia de roca.",
            "La variable latitude entra como |lat|. El modo de bandas por defecto es todas_min (distancia mínima entre bandas y banda ganadora). El modo banda_propia está implementado y se puede activar. El §5 del método de Ronald queda pendiente de su confirmación.",
            "La banda A (0–15°) no tiene positivos terrestres de superficie en este conjunto (Ecuador cae aquí). La firma de A sí existe (celdas ecuatoriales de Marte y de la Luna); lo que falta es validación en esa banda.",
            "La banda D (45–60°) es débil: en este conjunto solo Ries y Sudbury (geológicos, excluidos del AUC de superficie) y el negativo Hainich.",
            "La banda G (80–90°) no tiene estación terrestre en este conjunto. Se añade por diseño para el polo sur lunar (>~84° S), cuyo único análogo latitudinal sería la Antártida, y ni siquiera los Valles Secos (~77–78° S).",
            "Askja / Vikrahraun entra al AUC con coordenada confirmada 65.060, −16.640 y buffer de 6 km (punto medio de la colada, Blasizzo et al., 2022, additional file 1, hoja (1.1) Samples). Se descarta el valor de trabajo 65.03, −16.78. El parámetro incluir_askja (por defecto true) permite apagarlo en una sensibilidad.",
            "Río Tinto se excluye del AUC de superficie porque es análogo solo geoquímico/mineralógico. Ries y Sudbury se excluyen (y se tratan como sitios separados) porque la cubeta actual (ciudad, cultivo o bosque) no es homologable a una superficie lunar o marciana.",
            "Las superficies de los sitios de validación y el DEM de Ecuador de esta versión son MOCK (sintéticos).",
        ],
        "nota_de_incertidumbre": (
            "Askja entra al AUC con coordenada confirmada 65.060, −16.640 y buffer de 6 km "
            "(punto medio de la colada Vikrahraun; Blasizzo et al., 2022, additional file 1, hoja (1.1) Samples). "
            "Se descarta el valor de trabajo 65.03, −16.78. "
            "Banda A sin positivos terrestres (Ecuador cae ahí; la firma planetaria de A sí existe). "
            "Banda D débil; banda G sin estaciones, añadida por el polo sur lunar. "
            "Modo de bandas por defecto: todas_min, solo con distancia euclídea; si se usa Mahalanobis por banda, la latitud sale del vector automáticamente. "
            "Los umbrales se fijan con la misma regla del mínimo en la validación y se congelan antes de aplicar Ecuador. "
            "Se reportan el AUC con y sin latitud (DeLong pareado e IC bootstrap 95 %), un modelo nulo de solo |lat|, "
            "y la variante de elevación absoluta frente a relieve relativo (pendiente de decisión del equipo, §3). "
            "Umbral no debe extrapolarse como si fuera global."
        ),
    }

    def _jsonable(obj):
        if isinstance(obj, dict):
            return {k: _jsonable(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [_jsonable(v) for v in obj]
        if hasattr(obj, "item"):
            try:
                return obj.item()
            except Exception:
                pass
        if isinstance(obj, float) and (obj != obj):  # nan
            return None
        return obj

    (OUT_WEB / "catalogo.json").write_text(
        json.dumps(_jsonable(catalog), ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # CSV de validación (encabezados en español)
    fieldnames = [
        "sitio",
        "latitud",
        "longitud",
        "buffer_km",
        "banda_latitud",
        "banda_ganadora_marte",
        "banda_ganadora_luna",
        "elevacion_m",
        "pendiente_deg",
        "rugosidad_tri",
        "etiqueta_conocida",
        "clase_conocida",
        "delta_marte",
        "delta_luna",
        "clase_predicha",
        "acierto",
        "entra_al_auc",
        "excluido_auc",
        "coordenada_no_verificada",
        "cita",
        "es_mock_superficies",
        "modo_bandas",
    ]
    csv_rows = [
        {
            "sitio": r["nombre"],
            "latitud": r["lat"],
            "longitud": r["lon"],
            "buffer_km": r["buffer_km"],
            "banda_latitud": r["banda_latitud"],
            "banda_ganadora_marte": r["banda_ganadora_marte"],
            "banda_ganadora_luna": r["banda_ganadora_luna"],
            "elevacion_m": r["elevacion_m"],
            "pendiente_deg": r["pendiente_deg"],
            "rugosidad_tri": r["rugosidad_tri"],
            "etiqueta_conocida": r["etiqueta"],
            "clase_conocida": r["clase_conocida"],
            "delta_marte": r["delta_marte"],
            "delta_luna": r["delta_luna"],
            "clase_predicha": r["clase_predicha"],
            "acierto": "sí" if r["acierto"] else "no",
            "entra_al_auc": "sí" if r["entra_al_auc"] else "no",
            "excluido_auc": "sí" if r["excluido_auc"] else "no",
            "coordenada_no_verificada": "sí" if r["coordenada_no_verificada"] else "no",
            "cita": r["cita"],
            "es_mock_superficies": "sí",
            "modo_bandas": MODO_DEFAULT,
        }
        for r in sites
    ]

    def write_csv(path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(csv_rows)

    write_csv(OUT_ROOT / "tabla_validacion.csv")
    write_csv(OUT_WEB / "tabla_validacion.csv")
    write_csv(OUT_WORKSPACE / "tabla_validacion.csv")

    n_land = int(mask.sum())
    counts = {CLASS_NAMES[k]: int(np.sum((clas == k) & mask)) for k in (0, 1, 2, 3)}
    print("MOCK generado")
    print(f"  modo_bandas por defecto={MODO_DEFAULT}")
    print(f"  grilla {nrows}×{ncols}, celdas de tierra={n_land}")
    print(f"  umbral Marte={thr['mars'].threshold:.3f}  AUC={thr['mars'].auc:.3f}  sens={thr['mars'].sensitivity:.3f}  prec={thr['mars'].precision:.3f}")
    print(f"  umbral Luna={thr['moon'].threshold:.3f}  AUC={thr['moon'].auc:.3f}  sens={thr['moon'].sensitivity:.3f}  prec={thr['moon'].precision:.3f}")
    n_auc = sum(1 for r in sites if r["entra_al_auc"])
    n_ok = sum(1 for r in sites if r["entra_al_auc"] and r["acierto"])
    print(f"  aciertos AUC={n_ok}/{n_auc} (sitios totales={len(sites)}, excluidos={len(sites)-n_auc})")
    for modo, evx in evals.items():
        print(f"  sensibilidad {modo}: AUC Marte={evx['thr']['mars'].auc:.3f}  AUC Luna={evx['thr']['moon'].auc:.3f}")
    print(f"  clases Ecuador ({MODO_DEFAULT}): {counts}")
    print(f"  clases Ecuador (banda_propia): {clas_own_counts}")
    print(f"  zonas: {[z['nombre']+' '+z['clase'] for z in zones[:5]]}")
    print(f"  escrito en {OUT_WEB}")


if __name__ == "__main__":
    main()
