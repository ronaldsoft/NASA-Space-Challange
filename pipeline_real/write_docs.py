#!/usr/bin/env python3
"""Escribe variables.json, manifest.json y el README de datos (en español)."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

from config import (
    COP_BUCKET,
    COP_TILELIST_URL,
    DATA,
    EARTH_1KM_DEG,
    EARTH_RADIUS_M,
    ECUADOR_BOUNDS,
    LAT_BANDS,
    LOLA_IMG_URL,
    LOLA_LBL_URL,
    MARS_RADIUS_M,
    MOLA_BASE,
    MOLA_TILES,
    MOON_RADIUS_M,
    OPTIONAL_LAYERS,
    PROCESSED,
    RAW,
    RAW_EARTH,
    SAMPLES_PER_BAND_HEMISPHERE,
    VALIDATION_SITES,
)
from terrain import meters_per_degree

TZ = timezone(timedelta(hours=-5))


def _load(path: Path):
    return json.loads(path.read_text()) if path.exists() else {}


def _now():
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M %Z") + " (America/Guayaquil, UTC-5)"


def build_variables(summary: dict) -> dict:
    mars = summary.get("mars") or {}
    moon = summary.get("moon") or {}
    ecu = (summary.get("earth") or {}).get("ecuador") or {}

    def body_block(name, meta, source):
        return {
            "unit": source["unit"],
            "descripcion": source["descripcion"],
            "fuente": source["fuente"],
            "url_fuente": source["url"],
            "resolucion_nativa": source["res_nativa"],
            "resolucion_producto": source.get("res_producto"),
            "nodata": -9999.0,
            "datum_horizontal": source["datum_h"],
            "datum_vertical": source["datum_v"],
            "celda_grilla_grados": meta.get("cell_deg"),
            "celda_grilla_m_ecuador": meta.get("cell_m_equator"),
            "estadisticos": (meta.get("stats") or {}).get(source.get("stat_key") or name),
            "ruta": (meta.get("paths") or {}).get(source.get("stat_key") or name),
            "notas": source.get("notas"),
        }

    mars_src_e = {
        "unit": "m",
        "descripcion": "Elevación respecto al areoide MOLA.",
        "fuente": "MGS MOLA MEGDR (topografía, 64 ppd, productos megt*gb) — PDS Geosciences Node",
        "url": f"{MOLA_BASE}/",
        "res_nativa": "64 ppd (0.015625°, ≈ 926 m en el ecuador de Marte)",
        "res_producto": "≈ 1 km (ver celda_grilla_*)",
        "datum_h": "IAU2000 planetocéntrico, longitudes este, esfera de 3396.0 km (rótulo MEGDR)",
        "datum_v": "Areoide MOLA (GMM3 / mgm1025, grado y orden 50). Topografía = radio planetario − radio del areoide.",
        "stat_key": "elevation",
        "notas": "El producto nativo ya viene interpolado donde no hay disparos MOLA. Cobertura más pobre cerca del ecuador y en los polos (>87°).",
    }
    moon_src_e = {
        "unit": "m",
        "descripcion": "Altura relativa a la esfera de 1737.4 km (HEIGHT = DN × 0.5).",
        "fuente": "LRO LOLA LDEM_64 V3.1 — PDS Geosciences Node",
        "url": LOLA_IMG_URL,
        "res_nativa": "64 ppd (0.015625°, ≈ 473.8 m en el ecuador lunar); registro de píxel",
        "res_producto": "≈ 1 km (ver celda_grilla_*)",
        "datum_h": "Mean Earth / Polar Axis de DE421, longitudes este, esfera de 1737.4 km",
        "datum_v": "Esfera de 1737.4 km (no el geoide lunar / potencial).",
        "stat_key": "elevation",
        "notas": "El rótulo advierte posibles artefactos en los bordes de las bandas de 45° de latitud.",
    }
    earth_src_e = {
        "unit": "m",
        "descripcion": "Elevación sobre el geoide EGM2008 (Copernicus DEM).",
        "fuente": "Copernicus DEM GLO-90 (COG, AWS Open Data, s3://copernicus-dem-90m)",
        "url": COP_BUCKET + "/",
        "res_nativa": "3 arco-segundos (≈ 90 m en el ecuador); en latitudes altas las teselas reducen la resolución en longitud (p. ej. 9\" a ~75°)",
        "res_producto": "0.009° (≈ 1001.9 m en el ecuador WGS84)",
        "datum_h": "EPSG:4326 (WGS84)",
        "datum_v": "EGM2008",
        "stat_key": "elevation",
        "notas": "Se trata el valor exacto 0 como no-dato (mar y gran parte de las aguas en GLO-90). Las elevaciones reales de exactamente 0 m quedan enmascaradas. Se usó GLO-90 y no SRTM para cubrir sitios de validación por encima de 60° (Devon Island, Svalbard, Islandia, valles secos antárticos).",
    }

    slope_nota = (
        "Recalculada sobre el DEM ya remuestreado a ≈1 km (método Horn 3×3). "
        "La escala horizontal es radius·π/180·cos(latitud), con radio del cuerpo documentado. "
        "No se interpoló un ráster de pendiente de otra resolución."
    )
    tri_nota = (
        "Índice de rugosidad del terreno (TRI) de Wilson et al.: media de las diferencias "
        "absolutas de elevación entre la celda y sus 8 vecinos (ventana 3×3), en metros, "
        "calculado sobre el DEM ya remuestreado. Requiere los 8 vecinos válidos."
    )

    def slope_src(elev_src, radius_name):
        return {
            "unit": "grados",
            "descripcion": "Pendiente topográfica (método de Horn).",
            "fuente": elev_src["fuente"],
            "url": elev_src["url"],
            "res_nativa": "derivada; no nativa",
            "res_producto": elev_src["res_producto"],
            "datum_h": elev_src["datum_h"],
            "datum_v": "no aplica (derivada)",
            "stat_key": "slope",
            "notas": slope_nota + f" Radio usado: {radius_name}.",
        }

    def tri_src(elev_src):
        return {
            "unit": "m",
            "descripcion": "Rugosidad local TRI (Wilson, ventana 3×3).",
            "fuente": elev_src["fuente"],
            "url": elev_src["url"],
            "res_nativa": "derivada; no nativa",
            "res_producto": elev_src["res_producto"],
            "datum_h": elev_src["datum_h"],
            "datum_v": "no aplica (derivada)",
            "stat_key": "roughness",
            "notas": tri_nota,
        }

    def lat_src(elev_src, meta):
        return {
            "unit": "grados (planetocéntricos / geodésicos según el cuerpo)",
            "descripcion": "Latitud del centro de la celda de la grilla de ≈1 km.",
            "fuente": "calculada a partir de la geotransformación de la grilla",
            "url": None,
            "res_nativa": "no aplica",
            "res_producto": elev_src["res_producto"],
            "datum_h": elev_src["datum_h"],
            "datum_v": "no aplica",
            "stat_key": "latitude",
            "notas": "Entra al índice ANALOG/delta como proxy de régimen de insolación y como clave de las bandas de muestreo. No sustituye al resto de variables de superficie.",
        }

    variables = {
        "indice": {
            "entran": ["latitude", "elevation", "slope", "roughness"],
            "no_entran": [
                "temperatura",
                "precipitacion",
                "humedad",
                "viento",
                "nubosidad",
                "cualquier climatología",
            ],
            "fuera_del_indice": ["albedo", "thermal_inertia"],
            "nota": (
                "El documento metodológico prohíbe variables meteorológicas en el índice. "
                "Expertos confirmó que el albedo y la inercia térmica (tampoco la abundancia de roca) "
                "NO entran al índice v1. No se descargaron. El índice queda con latitud, elevación, pendiente y rugosidad, pesos iguales."
            ),
        },
        "mars": {
            "latitude": body_block("latitude", mars, lat_src(mars_src_e, mars)),
            "elevation": body_block("elevation", mars, mars_src_e),
            "slope": body_block("slope", mars, slope_src(mars_src_e, f"{MARS_RADIUS_M:.0f} m")),
            "roughness": body_block("roughness", mars, tri_src(mars_src_e)),
        },
        "moon": {
            "latitude": body_block("latitude", moon, lat_src(moon_src_e, moon)),
            "elevation": body_block("elevation", moon, moon_src_e),
            "slope": body_block("slope", moon, slope_src(moon_src_e, f"{MOON_RADIUS_M:.0f} m")),
            "roughness": body_block("roughness", moon, tri_src(moon_src_e)),
        },
        "earth": {
            "latitude": body_block("latitude", ecu, lat_src(earth_src_e, ecu)),
            "elevation": body_block("elevation", ecu, earth_src_e),
            "slope": body_block("slope", ecu, slope_src(earth_src_e, f"{EARTH_RADIUS_M:.0f} m (semieje WGS84)")),
            "roughness": body_block("roughness", ecu, tri_src(earth_src_e)),
            "cobertura": {
                "ecuador_y_galapagos": ECUADOR_BOUNDS,
                "sitios_validacion": [s["id"] for s in VALIDATION_SITES],
                "nota": "No se descargó un DEM global terrestre: solo Ecuador + Galápagos y ventanas de ~50 km (más margen) alrededor de los sitios de validación.",
            },
        },
        "capas_opcionales_no_procesadas": OPTIONAL_LAYERS,
        "capa_extra_relieve_relativo": {
            "en_el_indice_v1": False,
            "unit": "m",
            "descripcion": "Elevación menos la mediana de elevación en una ventana de 15×15 celdas (≈ 15 km en el ecuador), calculada sobre el DEM ya remuestreado a 1 km.",
            "estado": "Pendiente de decisión del equipo: podría sustituir a la elevación absoluta, porque los datums verticales de los tres cuerpos no son homologables al metro.",
            "archivos": {
                "mars": (mars.get("paths") or {}).get("relative_relief"),
                "moon": (moon.get("paths") or {}).get("relative_relief"),
                "earth_ecuador": str((Path(__file__).resolve().parents[1] / "data/processed/earth/ecuador_relative_relief_1km.tif")) if True else None,
            },
            "estadisticos": {
                "mars": (mars.get("stats") or {}).get("relative_relief"),
                "moon": (moon.get("stats") or {}).get("relative_relief"),
            },
        },
    }
    # rutas de latitud
    for body, meta in (("mars", mars), ("moon", moon)):
        variables[body]["latitude"]["ruta"] = (meta.get("paths") or {}).get("latitude")
        variables[body]["latitude"]["estadisticos"] = {
            "min": -90.0,
            "max": 90.0,
            "nota": "Ráster de latitud del centro de cada celda, cubre el globo.",
        }
    if ecu.get("paths"):
        variables["earth"]["latitude"]["ruta"] = ecu["paths"].get("latitude")
    return variables


def build_manifest(summary: dict) -> dict:
    raw_mars = list(sorted((RAW / "mars" / "mola_megdr64").glob("megt*.img")))
    raw_moon = list(sorted((RAW / "moon" / "lola_ldem64").glob("ldem_64.img")))
    raw_earth = list(sorted(RAW_EARTH.glob("Copernicus_DSM_COG_30_*.tif")))
    return {
        "generado": _now(),
        "grillas_objetivo": {
            "earth": {
                "cell_deg": EARTH_1KM_DEG,
                "cell_m_equator": meters_per_degree(EARTH_RADIUS_M) * EARTH_1KM_DEG,
                "origen": "(-180°, 90°), lon oeste–este, lat norte–sur",
            },
            "mars": {
                "cell_deg": (summary.get("mars") or {}).get("cell_deg"),
                "cell_m_equator": (summary.get("mars") or {}).get("cell_m_equator"),
                "shape": [(summary.get("mars") or {}).get("width"), (summary.get("mars") or {}).get("height")],
            },
            "moon": {
                "cell_deg": (summary.get("moon") or {}).get("cell_deg"),
                "cell_m_equator": (summary.get("moon") or {}).get("cell_m_equator"),
                "shape": [(summary.get("moon") or {}).get("width"), (summary.get("moon") or {}).get("height")],
            },
        },
        "descargas_crudas": {
            "mars_mola": {
                "urls": [f"{MOLA_BASE}/{n}.img" for n in MOLA_TILES]
                + [f"{MOLA_BASE}/{n}.lbl" for n in MOLA_TILES],
                "archivos": [str(p) for p in raw_mars],
                "bytes": sum(p.stat().st_size for p in raw_mars),
            },
            "moon_lola": {
                "urls": [LOLA_IMG_URL, LOLA_LBL_URL],
                "archivos": [str(p) for p in raw_moon],
                "bytes": sum(p.stat().st_size for p in raw_moon),
            },
            "earth_copernicus_glo90": {
                "catalogo": COP_TILELIST_URL,
                "patron_url": COP_BUCKET + "/{TILE}/{TILE}.tif",
                "n_teselas": len(raw_earth),
                "bytes": sum(p.stat().st_size for p in raw_earth),
                "directorio": str(RAW_EARTH),
            },
        },
        "productos": summary,
        "bandas_latitud_provisionales": LAT_BANDS,
        "sitios_validacion_provisionales": VALIDATION_SITES,
        "muestras_por_banda_y_hemisferio": SAMPLES_PER_BAND_HEMISPHERE,
    }


def build_readme(summary: dict, manifest: dict) -> str:
    mars = summary.get("mars") or {}
    moon = summary.get("moon") or {}
    earth = summary.get("earth") or {}
    ecu = earth.get("ecuador") or {}
    lines = []
    a = lines.append
    a("# Datos de superficie a ~1 km — Marte, Luna y Tierra")
    a("")
    a(f"Generado: { _now() }")
    a("")
    a("Este directorio reúne los datos **reales** de elevación (y las derivadas de pendiente y rugosidad) usados para el índice ANALOG/delta del reto NASA Space Apps *Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars*. El documento metodológico de referencia es `/workspace/proyecto_ronald.txt`.")
    a("")
    a("## Qué entra al índice")
    a("")
    a("Solo variables de superficie: **latitud, elevación, pendiente y rugosidad (TRI 3×3)**. Cero variables meteorológicas. Expertos confirmó que el **albedo y la inercia térmica no entran** al índice v1 (tampoco la abundancia de roca); no se descargaron. Se documenta su disponibilidad al final, por si el índice se ampliará en una versión posterior.")
    a("")
    a("Pendiente y rugosidad se recalcularon **después** de remuestrear el DEM a ~1 km; no se interpolaron rásteres derivados de otra resolución.")
    a("")
    a("## Grillas de ~1 km")
    a("")
    a("Cada cuerpo tiene su propia celda equivalente a ~1 km en el ecuador (no se usa el mismo tamaño en grados, porque los radios son distintos). Todas las grillas están en coordenadas geográficas, origen en (−180°, 90°), longitudes este, rango de longitud [−180, 180].")
    a("")
    a("| Cuerpo | Radio usado para la pendiente y el tamaño de celda | Celda (°) | Celda (m, ecuador) | Tamaño de la grilla |")
    a("|---|---|---|---|---|")
    a(f"| Tierra (WGS84, semieje mayor) | {EARTH_RADIUS_M:.0f} m | {EARTH_1KM_DEG} | {meters_per_degree(EARTH_RADIUS_M)*EARTH_1KM_DEG:.2f} | recortes regionales, no el globo |")
    a(f"| Marte (esfera del rótulo MEGDR) | {MARS_RADIUS_M:.0f} m | {mars.get('cell_deg')} | {mars.get('cell_m_equator')} | {mars.get('width')} × {mars.get('height')} |")
    a(f"| Luna (esfera 1737.4 km) | {MOON_RADIUS_M:.0f} m | {moon.get('cell_deg')} | {moon.get('cell_m_equator')} | {moon.get('width')} × {moon.get('height')} |")
    a("")
    a("Los tres productos globales de Marte y de la Luna se generaron a 1 km en el globo completo (no fue necesario recurrir a un producto más grueso ni al muestreo por bandas como único producto; el muestreo estratificado se entrega además, para las firmas).")
    a("")
    a("## Marte — MOLA MEGDR")
    a("")
    a("- **Producto:** MGS MOLA Mission Experiment Gridded Data Record, topografía (MEGT), 64 píxeles por grado (~926 m/píxel en el ecuador).")
    a(f"- **URL base:** {MOLA_BASE}/")
    a("- **Archivos:** " + ", ".join(f"`{n}.img` / `.lbl`" for n in MOLA_TILES) + " (cuatro teselas de 90° × 180°, 16-bit big-endian, metros).")
    a("- **Datum horizontal:** IAU2000, planetocéntrico, longitudes positivas hacia el este. El rótulo declara un elipsoide/esfera de **3396.0 km**.")
    a("- **Datum vertical:** areoide MOLA derivado del modelo de potencial Goddard **GMM3 (mgm1025)** evaluado a grado y orden 50. La topografía es el radio planetario menos el radio del areoide.")
    a("- **No-dato:** el rótulo no declara un valor nulo; las celdas sin disparos van interpoladas. En los productos de 1 km se usa −9999 en los bordes polares de las derivadas (sin 8 vecinos).")
    a("- **Procesado:** mosaico a longitudes [−180, 180], remuestreo bilinear a la grilla de ~1 km, pendiente Horn y TRI de Wilson sobre ese DEM.")
    a("")
    if mars.get("stats"):
        st = mars["stats"]
        a(f"- **Estadísticos (1 km):** elevación {st.get('elevation')}; pendiente {st.get('slope')}; TRI {st.get('roughness')}.")
        a("")
    a("## Luna — LOLA LDEM")
    a("")
    a("- **Producto:** LRO LOLA Global Digital Elevation Model, `LDEM_64`, versión 3.1 (creación 2019-03-15).")
    a(f"- **URL:** {LOLA_IMG_URL}")
    a(f"- **Rótulo:** {LOLA_LBL_URL}")
    a("- **Formato nativo:** 23040 × 11520, 16-bit little-endian, **factor de escala 0.5** (HEIGHT = DN × 0.5 m), registro de píxel, 64 ppd (≈ 473.8 m/píxel en el ecuador).")
    a("- **Datum horizontal:** Mean Earth / Polar Axis de DE421, longitudes este.")
    a("- **Datum vertical:** esfera de **1737.4 km** (no el geoide lunar). El radio planetario es HEIGHT + 1 737 400 m.")
    a("- **Procesado:** igual que Marte (mosaico [−180, 180], remuestreo bilinear a ~1 km, Horn y TRI).")
    a("")
    if moon.get("stats"):
        st = moon["stats"]
        a(f"- **Estadísticos (1 km):** elevación {st.get('elevation')}; pendiente {st.get('slope')}; TRI {st.get('roughness')}.")
        a("")
    a("## Tierra — Copernicus DEM GLO-90")
    a("")
    a("- **Producto:** Copernicus DEM GLO-90 (COG de 3 arco-segundos) en AWS Open Data, **sin autenticación** (`s3://copernicus-dem-90m`).")
    a(f"- **Catálogo:** {COP_TILELIST_URL}")
    a(f"- **Patrón:** `{COP_BUCKET}/{{TILE}}/{{TILE}}.tif`")
    a(f"- **Teselas descargadas:** {manifest['descargas_crudas']['earth_copernicus_glo90']['n_teselas']} ({manifest['descargas_crudas']['earth_copernicus_glo90']['bytes']/1e6:.1f} MB). Las teselas pedidas que no figuran en el catálogo corresponden sobre todo a océano (p. ej. el agua entre el Ecuador continental y Galápagos).")
    a("- **Cobertura:**")
    a(f"  - Ecuador continental y Galápagos, caja `lon {ECUADOR_BOUNDS['west']}…{ECUADOR_BOUNDS['east']}`, `lat {ECUADOR_BOUNDS['south']}…{ECUADOR_BOUNDS['north']}`.")
    a("  - Ventanas de ~50 × 50 km (más un margen para la ventana 3×3) en cada sitio de validación provisional.")
    a("- **Datum horizontal:** EPSG:4326 (WGS84). **Datum vertical:** EGM2008.")
    a("- **No-dato:** GLO-90 no trae etiqueta `nodata`; el mar (y buena parte de las aguas) aparece como **0 exacto**. Se enmascara el 0. Limitación: una celda terrestre que midiera exactamente 0 m también queda fuera.")
    a("- **Latitudes altas:** a ~75°N/S las teselas GLO-90 vienen con menos columnas (p. ej. 400 en vez de 1200), es decir resolución más gruesa en longitud (~9\"). Es un diseño del producto, no un error. Por eso se usó GLO-90 y no SRTM, que no cubre por encima de 60° (Devon Island, Svalbard, Islandia, valles secos antárticos).")
    a("")
    if ecu.get("stats"):
        a(f"- **Estadísticos Ecuador+Galápagos (1 km):** elevación {ecu['stats'].get('elevation')}; pendiente {ecu['stats'].get('slope')}; TRI {ecu['stats'].get('roughness')}.")
        a("")
    a("### Sitios de validación (lista provisional)")
    a("")
    a("Sitios verificados por Expertos (`/workspace/validacion_parte1.md`). Se excluyen Río Tinto, Ries, Sudbury y los genéricos de Islandia y de los Valles Secos (fuera del AUC de superficie o sustituidos por un sitio más preciso).")
    a("")
    a("| id | nombre | lat | lon | buffer (km) | etiqueta | clase | notas |")
    a("|---|---|---|---|---|---|---|---|")
    for s in VALIDATION_SITES:
        notas = s.get("notas", "").replace("|", "/")
        a(f"| `{s['id']}` | {s['name']} | {s['lat']} | {s['lon']} | {s['buffer_km']} | {s['etiqueta']} | {s['clase']} | {notas} |")
    a("")
    a("Los rásteres de cada ventana están en `processed/earth/validation/<id>/`.")
    a("")
    a("## Derivadas (pendiente y TRI)")
    a("")
    a("- **Pendiente:** método de Horn (3×3), en grados. Distancia horizontal = `R · π/180 · cos(latitud)` en X y `R · π/180` en Y, con el radio documentado de cada cuerpo (en los polos se limita |lat| a 89.9° para evitar dx → 0). En Marte y la Luna la longitud se envuelve (±180°).")
    a("- **Rugosidad:** TRI de Wilson et al. (2007), media de |z_vecino − z_centro| en los 8 vecinos, en metros. No usa distancia horizontal (es variabilidad de elevación). Se exige que los 8 vecinos sean válidos.")
    a("")
    a("## Muestras estratificadas (firmas)")
    a("")
    a(f"Además de los GeoTIFF globales, hay un muestreo por bandas de latitud oficiales (A–G, simétricas N/S; la banda G es obligatoria para el polo sur lunar, >~84°S), con hasta {SAMPLES_PER_BAND_HEMISPHERE} celdas por banda y hemisferio, en `processed/mars/mars_latband_samples.npz` y `processed/moon/moon_latband_samples.npz`. Marte y la Luna no se mezclan.")
    a("")
    a("Bandas oficiales |lat| (se aplican a N y a S):")
    a("")
    for b in LAT_BANDS:
        a(f"- `{b['id']}`: {b['lat_min']}–{b['lat_max']} — {b['motivo']}")
    a("")
    a("## Estructura de archivos")
    a("")
    a("```")
    a("data/")
    a("  README.md                  (este archivo)")
    a("  raw/")
    a("    mars/mola_megdr64/       IMG + LBL + mosaico nativo 64 ppd")
    a("    moon/lola_ldem64/        LDEM_64 IMG + LBL + mosaico en metros")
    a("    earth/copernicus_glo90/  teselas GLO-90")
    a("  processed/")
    a("    variables.json")
    a("    manifest.json")
    a("    processing_summary.json")
    a("    mars/  moon/             GeoTIFF ~1 km (elevación, pendiente, TRI, latitud, relieve relativo) + muestras .npz")
    a("    earth/ecuador_*_1km.tif  Ecuador + Galápagos")
    a("    earth/validation/<sitio>/")
    a("```")
    a("")
    a("Los scripts reproducibles están en `/workspace/analogs/pipeline_real/` (`download_planetary.py`, `download_earth.py`, `process.py`, `write_docs.py`).")
    a("")
    a("## Relieve relativo (capa extra, no entra aún al índice v1)")
    a("")
    a("Además de la elevación absoluta, se calcula una capa de **relieve relativo**: la elevación de la celda menos la **mediana** de las elevaciones en una ventana de 15 × 15 celdas (≈ 15 km en el ecuador) sobre el DEM ya remuestreado a 1 km, en Marte, la Luna, Ecuador y cada ventana de validación. En los globos planetarios la ventana se envuelve en longitud. Hace falta al menos la mitad de vecinos válidos.")
    a("")
    a("Esta capa está pendiente de decisión del equipo: podría sustituir a la elevación absoluta en el índice, porque los datums verticales de los tres cuerpos no son homologables al metro (areoide MOLA, esfera lunar de 1737.4 km, geoide EGM2008). Hasta que se decida, **no entra al índice v1**. Archivos: `*_relative_relief_1km.tif` y la columna `relative_relief_m` en las muestras `.npz` y en la tabla de validación.")
    a("")
    a("## Limitaciones (para la nota de incertidumbre)")
    a("")
    a("1. **La analogía es solo de superficie** y únicamente con las variables comparables. No se puede llamar «clima análogo» al índice.")
    a("2. **La resolución única de ~1 km suaviza el relieve local**, sobre todo en los Andes y en cráteres o conos de unos pocos kilómetros (p. ej. Meteor Crater tiene ~1.2 km de diámetro: en la grilla de 1 km queda mal resuelto).")
    a("3. **Marte a 64 ppd nativos (~926 m) se remuestrea ligeramente hacia ~1 km**; no se usó el MEGDR de 128 ppd (~463 m) para acotar tiempo y memoria. La diferencia de escala es pequeña frente al paso a 1 km.")
    a("4. **Luna: se parte de 474 m y se pierden dos factores de 2 al pasar a 1 km.** El LDEM de 128 ppd no se descargó (sería ~2 GB).")
    a("5. **Cobertura MOLA:** hay interpolación entre huellas (huecos de hasta ~12 km cerca del ecuador) y datos más pobres por encima de ~87° de latitud.")
    a("6. **LDEM 64:** posibles artefactos en los bordes de las bandas de 45° (advertencia del rótulo). Datum vertical = esfera, no geoide lunar.")
    a("7. **Los datums verticales no son el mismo tipo de superficie de referencia** (areoide MOLA, esfera lunar, geoide EGM2008). La elevación se compara como variable relativa / de relieve, no como cota absoluta homologable al metro.")
    a("8. **Tierra: 0 m exacto enmascarado**; costa y agua interior pueden perder celdas. GLO-90 es más grueso en longitud en latitudes altas.")
    a("9. **Askja** quedó con coordenada confirmada (65.060, −16.640; Blasizzo et al., 2022) y permanece en el AUC; se descartó 65.03, −16.78. **Inferno Chasm** usa una coordenada de resumen LPSC, no de revista. University Valley (3 km de buffer) y Meteor Crater (~1.2 km de diámetro) quedan muy suavizados a 1 km.")
    a("10. **Albedo e inercia térmica no entran al índice v1** (veredicto de Expertos; tampoco la abundancia de roca). No se descargaron.")
    a("11. **Pendiente y TRI en proyección equirrectangular cerca de los polos** son más inciertos: la celda de 1 km geográfico se estrecha mucho en metros de longitud (se aplica la corrección cos(lat), pero la forma de la celda no es un km×km). La banda G (80–90°) se muestreó igualmente porque es obligatoria para el polo sur lunar. El LDEM_64 cilíndrico sí cubre ambos polos; no fue necesario un producto polar estereográfico aparte.")
    a("12. No se entregó un ráster global terrestre: solo Ecuador/Galápagos y las ventanas de validación.")
    a("")
    a("## Albedo e inercia térmica (fuera del índice; no se descargaron)")
    a("")
    a(json.dumps(OPTIONAL_LAYERS, indent=2, ensure_ascii=False))
    a("")
    a("## Cómo reproducir")
    a("")
    a("```bash")
    a("cd /workspace/analogs/pipeline_real")
    a("python3 -m venv .venv && .venv/bin/pip install -r requirements.txt")
    a(".venv/bin/python download_planetary.py")
    a(".venv/bin/python download_earth.py")
    a(".venv/bin/python process.py")
    a(".venv/bin/python write_docs.py")
    a("```")
    a("")
    return "\n".join(lines) + "\n"


def main() -> int:
    summary = _load(PROCESSED / "processing_summary.json")
    variables = build_variables(summary)
    manifest = build_manifest(summary)
    (PROCESSED / "variables.json").write_text(json.dumps(variables, indent=2, ensure_ascii=False))
    (PROCESSED / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    readme = build_readme(summary, manifest)
    (DATA / "README.md").write_text(readme)
    (PROCESSED / "README.md").write_text(
        "Los productos procesados se describen en el [README principal de datos](../README.md).\n"
    )
    print("Escritos:")
    print(" ", PROCESSED / "variables.json")
    print(" ", PROCESSED / "manifest.json")
    print(" ", DATA / "README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
