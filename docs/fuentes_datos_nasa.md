# Fuentes de datos y referencias, ANALOG/δ v1

Revisado el 14 de noviembre de 2026, 19:45–19:49 (hora de Ecuador, UTC−5). Cada enlace se probó con `curl -L` desde el servidor de trabajo. El estado es el código HTTP final después de las redirecciones.

- **403**: el sitio bloquea clientes automáticos. No se pudo verificar así, pero el enlace es el oficial y casi seguro funciona en un navegador. Los DOI con 403 se confirmaron por metadatos en Crossref o DataCite.
- **500**: la editorial falló con el cliente automático. El DOI existe en Crossref o DataCite.
- **206**: respuesta parcial a una petición por rango. Equivale a 200.

Esta revisión no cambia el DEM, el índice ni Supabase. Ronald pidió esperar su modelo antes de tocar datos.

## 1. Datos que entran al índice v1 (y la sustitución propuesta)

| Dataset | Institución | NASA | URL de ficha | URL de descarga | DOI | HTTP | Uso en el proyecto |
|---|---|---|---|---|---|---|---|
| MOLA MEGDR 64 ppd (teselas `megt*gb`) | NASA PDS Geosciences Node (Mars Global Surveyor) | Sí | https://pds-geosciences.wustl.edu/missions/mgs/megdr.html | https://pds-geosciences.wustl.edu/mgs/mgs-m-mola-5-megdr-l3-v1/mgsl_300x/meg064/ (ej. `megt00n000gb.img` y `.lbl`) | No tiene; se cita por el volumen PDS `MGS-M-MOLA-5-MEGDR-L3-V1.0` | 200 / 200 / 200 | Marte: elevación, pendiente Horn, TRI, firmas por banda A–G, δ Marte, hillshade de Marte |
| LOLA LDEM_64 (v3.1 según la v1 congelada) | NASA PDS Geosciences Node (Lunar Reconnaissance Orbiter) | Sí | https://pds-geosciences.wustl.edu/missions/lro/lola.htm | https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/cylindrical/img/ldem_64.img (y `ldem_64.lbl`) | No tiene; volumen PDS `LRO-L-LOLA-3-RDR-V1.0` | 200 / 200 / 200 | Luna: elevación, pendiente, TRI, firmas por banda, δ Luna, hillshade lunar |
| Copernicus DEM GLO-90 | ESA / Programa Copernicus (UE), con datos de Airbus | **No** | https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM | https://copernicus-dem-90m.s3.amazonaws.com/tileList.txt y `…/{TILE}/{TILE}.tif` | 10.5270/ESA-c5d3d65 | 200 / 200 | **Lo que usa hoy la Tierra**: elevación, pendiente y TRI de Ecuador, Galápagos y las ventanas de validación; máscara de agua (0 m exacto). (El hillshade de Ecuador ya no usa GLO-90: desde el 14 nov 2026 sale de SRTMGL30) |
| **NASADEM_HGT v001**, la sustitución propuesta | NASA JPL / LP DAAC (Earthdata) | Sí | https://www.earthdata.nasa.gov/data/catalog/lpcloud-nasadem-hgt-001 (lpdaac.usgs.gov/products/nasadem_hgtv001/ redirige aquí) | Búsqueda: https://search.earthdata.nasa.gov/search/granules?p=C2763264762-LPCLOUD · Tesela de ejemplo: https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/NASADEM_HGT.001/NASADEM_HGT_s01w080/NASADEM_HGT_s01w080.zip (pide inicio de sesión gratuito en Earthdata) · Guía: https://lpdaac.usgs.gov/documents/2237/NASADEM_User_Guide_V13.pdf | 10.5067/MEaSUREs/NASADEM/NASADEM_HGT.001 | 200 / 200 / 200 (redirige al login de Earthdata) / 200 | Reemplazaría a GLO-90 en la Tierra. 1 arcsec, geoide **EGM96** (no EGM2008). La capa `swb` (0 = tierra, 255 = agua) sirve como máscara de agua oficial |

## 2. Capas de contexto, polígonos y visualización

| Dataset | Institución | NASA | URL de ficha | URL de descarga | DOI | HTTP | Uso en el proyecto |
|---|---|---|---|---|---|---|---|
| Regiones candidatas Artemis III (McClernan, 2024), "Down Selected Artemis III Candidate Landing Site Navigational Grids" | USGS (gobierno de EE. UU., no es NASA) | **No** (pero el origen es NASA, ver nota) | https://doi.org/10.5066/P1MEQ6UK → https://www.sciencebase.gov/catalog/item/671a6fa8d34efed5620f89f8 | En la misma ficha de ScienceBase | 10.5066/P1MEQ6UK | 403 / 403 (DOI confirmado en DataCite) | Contexto de sitios lunares y archivo v1.1. **La v1 congelada no usa estos polígonos** |
| Anuncio NASA de las 9 regiones Artemis III (comunicado 24-136, 28 oct 2024) | NASA HQ | Sí | https://www.nasa.gov/news-release/nasa-provides-update-on-artemis-iii-moon-landing-regions/ | No tiene (comunicado con mapa) | No tiene | 200 | Fuente primaria de las regiones |
| LROC QuickMap | LROC / ASU, misión LRO de NASA | Sí (misión NASA, operada por ASU) | https://quickmap.lroc.asu.edu/ (redirige a quickmap.lroc.im-ldi.com) | Herramienta interactiva | No tiene | 206 | Según el metadato USGS, de aquí salen los polígonos de las regiones |
| GADM 4.1, Ecuador (provincia Galápagos) | GADM / Universidad de California, Davis | **No** | https://gadm.org/ | https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_ECU_shp.zip | No tiene | 200 / 200 | Polígonos por isla para contar celdas en Galápagos (`docs/galapagos_celdas_por_isla.md`) |
| Natural Earth 110m land | Natural Earth (NACIS), dominio público | **No** | https://www.naturalearthdata.com/ | Desde la misma web | No tiene | 200 | **Solo el contorno de tierra** del globo terrestre (`web/public/basemap/ne_110m_land.geojson`, capas `land-fill` y `land-line`). Desde el 14 nov 2026 ya no se usa su relieve SR_50M |
| SRTMGL30 V002 (NASA Shuttle Radar Topography Mission Global 30 arc second) | NASA JPL / LP DAAC (Earthdata) | Sí | https://www.earthdata.nasa.gov/data/catalog/lpcloud-srtmgl30-002 | 27 teselas `*.SRTMGL30.dem.zip` desde Earthdata (pide inicio de sesión gratuito) · Guía: https://lpdaac.usgs.gov/documents/179/SRTM_User_Guide_V3.pdf | 10.5067/MEaSUREs/SRTM/SRTMGL30.002 | 200 / 200 (DOI resuelve a la ficha) | Relieve del globo terrestre (`hillshade_tierra.png`) y relieve de Ecuador y Galápagos (`hillshade_ecuador.png`). Cubre 90°N–60°S. SRTM solo midió entre 60°N y 56°S (ficha LP DAAC), así que al norte de 60°N los valores no son SRTM: la ficha dice que el producto se armó para corresponder con GTOPO30 (USGS), que es de donde se espera que salgan, aunque la ficha de V002 no lo dice textualmente. Sin Antártida (queda transparente). **Solo visual: no entra en el índice ni en δ** |

## 3. Métodos

| Referencia | Editorial | NASA | URL | DOI | HTTP | Uso |
|---|---|---|---|---|---|---|
| Horn, B. K. P. (1981). Hill shading and the reflectance map. *Proceedings of the IEEE* 69(1) | IEEE | No (es un método, no un dato) | https://doi.org/10.1109/PROC.1981.11918 | 10.1109/PROC.1981.11918 | 500 en IEEE; confirmado en Crossref | Pendiente Horn 3×3 y hillshade |
| Wilson, M. F. J. et al. (2007). Multiscale Terrain Analysis of Multibeam Bathymetry Data for Habitat Mapping on the Continental Slope. *Marine Geodesy* 30 | Taylor & Francis | No (método) | https://doi.org/10.1080/01490410701295962 | 10.1080/01490410701295962 | 500 en T&F; confirmado en Crossref | **El TRI del código es el de Wilson 2007**: media de las diferencias absolutas con los 8 vecinos (`pipeline_real/write_docs.py`) |
| Riley, S. J. et al. (1999). A terrain ruggedness index… *Intermountain Journal of Sciences* 5 | Intermountain Journal of Sciences | No | No encontré una URL oficial verificable | No tiene DOI | — | **No se usa en v1.** La atribución que había en el mock visible se corrigió a Wilson 2007 |

## 4. Fuentes de los sitios de validación

Son artículos y fichas de sitio que justifican la etiqueta de cada sitio. **No entran como datos.** Los valores de cada sitio salen del DEM terrestre. No son de la NASA y no hace falta sustituirlos por NASA; lo que se exige es que la cita sea correcta.

| Sitio | Referencia | DOI / URL | HTTP | En el AUC |
|---|---|---|---|---|
| Yungay (Atacama) | Navarro-González et al. 2003, *Science* | 10.1126/science.1089143 | 403 (Crossref OK) | Sí |
| Yungay | Ewing et al. 2006, *GCA* | 10.1016/j.gca.2006.08.020 | 200 | Sí |
| Haughton | Osinski et al. 2005, *MAPS* | 10.1111/j.1945-5100.2005.tb00145.x | 403 (Crossref OK) | Sí |
| University Valley | Heldmann et al. 2013, *PSS* | 10.1016/j.pss.2013.05.019 | 200 | Sí |
| University Valley | Lapalme et al., *Antarctic Science* (Crossref: 2016 en línea; el repo dice 2017a) | 10.1017/s0954102016000572 | 200 | Sí |
| Askja / Vikrahraun | Blasizzo et al. 2022, *EPS* | 10.1186/s40623-022-01711-5 | 200 | Sí |
| Mauna Kea | Guinness et al. 2007, *JGR Planets* | 10.1029/2006je002822 | 403 (Crossref OK) | Sí |
| Mauna Kea | ten Kate et al. 2013, *J. Aerospace Eng.* | 10.1061/(asce)as.1943-5525.0000200 | 403 (Crossref OK) | Sí |
| Mauna Kea | Graham et al. 2015, *Adv. Space Res.* | 10.1016/j.asr.2015.01.024 | 200 | Sí |
| Sverrefjell | Treiman et al. 2002, *EPSL* | 10.1016/s0012-821x(02)00998-6 | 200 | Sí |
| Timanfaya | Martínez-Frías et al. 2017, *Episodes* | 10.18814/epiiugs/2017/v40i4/017035 | 500 (Crossref OK) | Sí |
| Timanfaya | Alberquilla et al. 2022, *Sci. Rep.* | 10.1038/s41598-022-20960-8 | 200 | Sí |
| Timanfaya | Ficha MITECO | https://www.miteco.gob.es/es/parques-nacionales-oapn/red-parques-nacionales/parques-nacionales/timanfaya/ficha-tecnica.html | 200 (README) | Sí |
| Meteor Crater | Lambert y Reimold (2023), *Front. Astron. Space Sci.* (corregido; el DOI no cambia) | 10.3389/fspas.2023.1186173 | 206 | Sí |
| S P Mountain | Gullikson y Rumpf 2021, USGS OFR 2021-1072 | https://pubs.usgs.gov/of/2021/1072/ofr20211072.pdf | 206 | Sí |
| Inferno Chasm | Greeley 1971, *Science* (Garry et al. 2015, LPSC 46 #1009, sin URL en el repo) | 10.1126/science.172.3984.722 | 403 (Crossref OK) | Sí |
| Tapajós BR-Sa1 | AmeriFlux | https://ameriflux.lbl.gov/sites/siteinfo/BR-Sa1 | 206 | Sí |
| Bondville US-Bo1 | AmeriFlux | 10.17190/AMF/1246036 | 206 | Sí |
| Harvard Forest US-Ha1 | AmeriFlux | 10.17190/AMF/1246059 | 206 | Sí |
| Tumbarumba AU-Tum | FLUXNET2015 | 10.18140/FLX/1440126 | 500 (DataCite OK) | Sí |
| Hainich DE-Hai | FLUXNET2015 | 10.18140/FLX/1440148 | 500 (DataCite OK) | Sí |
| Hyytiälä FI-Hyy | FLUXNET2015 | 10.18140/FLX/1440158 | 500 (DataCite OK) | Sí |
| Río Tinto | Amils et al. 2014, *Life* | 10.3390/life4030511 | 403 (Crossref OK) | No |
| Río Tinto | Fernández-Remolar et al. 2005, *EPSL* | 10.1016/j.epsl.2005.09.043 | 200 | No |
| Ries | Stöffler et al. 2013, *MAPS* | 10.1111/maps.12086 | 403 (Crossref OK) | No |
| Sudbury | Lowman 1992, *Rev. Geophys.* | 10.1029/92rg00755 | 403 (Crossref OK) | No |

## 5. Lo que todavía no es NASA y sus alternativas

| Elemento no NASA | Alternativa NASA | Verificado |
|---|---|---|
| Copernicus GLO-90 (Tierra: elevación, pendiente, TRI) | **NASADEM_HGT v001**, DOI 10.5067/MEaSUREs/NASADEM/NASADEM_HGT.001 | Sí, 200. Cambia el geoide (EGM96 en lugar de EGM2008) y hay que recalcular. Queda pendiente del modelo de Ronald |
| Máscara de agua de Galápagos (0 m exacto de GLO-90) | Capa `swb` de NASADEM. Otra opción: MODIS MOD44W v061 (https://www.earthdata.nasa.gov/data/catalog/lpcloud-mod44w-061, DOI 10.5067/MODIS/MOD44W.061) o SRTMSWBD v003 (https://www.earthdata.nasa.gov/data/catalog/lpcloud-srtmswbd-003, DOI 10.5067/MEaSUREs/SRTM/SRTMSWBD.003) | Sí, todas 200 |
| ~~Hillshade de Ecuador (de GLO-90)~~ | **Hecho (14 nov 2026):** ahora sale de SRTMGL30 V002 (NASA), DOI 10.5067/MEaSUREs/SRTM/SRTMGL30.002 | Sí |
| Natural Earth (contorno del globo) | **Relieve: hecho (14 nov 2026)**, el SR_50M se reemplazó por SRTMGL30 V002. **Contorno: sigue siendo Natural Earth 110m**, porque la NASA no publica un contorno de continentes listo para usar; se podría derivar de MOD44W | Sí |
| GADM (polígonos de las islas de Galápagos) | **No hay un equivalente NASA directo** con nombres de islas. Se pueden sacar los contornos de tierra con NASADEM `swb` o MOD44W, pero los nombres habría que asignarlos a mano | — |
| Regiones Artemis USGS (McClernan 2024) | La fuente primaria es la NASA: comunicado 24-136 (200). Según el metadato USGS, los polígonos salen de LROC QuickMap (misión LRO de NASA). La NASA no publica un shapefile propio. La v1 no los usa | Sí |
| Citas de sitios (revistas, AmeriFlux/FLUXNET del DOE, MITECO, USGS) | No aplica: son literatura, no datos | — |

## 6. Correcciones de cita (hechas el 14 de noviembre de 2026)

1. Meteor Crater: la cita "Osinski et al. (2023)" con DOI 10.3389/fspas.2023.1186173 se sustituyó por Lambert y Reimold (2023), *Front. Astron. Space Sci.* El DOI se mantiene.
2. TRI: donde se atribuía a Riley et al. 1999, ahora se cita Wilson, M. F. J. et al. (2007), *Marine Geodesy* 30, DOI 10.1080/01490410701295962. Es la definición que usa el código: media de las diferencias absolutas con los 8 vecinos (`pipeline_real/terrain.py`, `slope_and_tri`).
3. Las regiones Artemis USGS figuran como dato, pero la v1 congelada no las usa.
4. El README (sección inglesa) dice "real MOLA, LOLA and GLO-90 data". Si se cambia a NASADEM, hay que actualizarlo junto con `docs/galapagos_mascara_agua.md`, que hoy dice que no se mezcla NASADEM.

## 7. Relieve del globo (14 de noviembre de 2026)

Los cuatro relieves del dashboard (`web/public/basemap/hillshade_{luna,marte,tierra,ecuador}.png`) se generan con `web/scripts/basemap_relieve.py` con un solo método: Horn 3×3, luz desde el noroeste (315°) a 45°, celda métrica según el radio de cada cuerpo, z = tamaño de píxel ecuatorial / 1066, sin percentiles ni gamma, reproyectados a Web Mercator sobre las esquinas `WORLD` de `maps.ts`. Las fuentes son todas NASA: LOLA LDEM_64 (Luna), MOLA MEGDR 64 ppd (Marte) y SRTMGL30 V002 (Tierra y Ecuador). El detalle está en `web/public/basemap/FUENTE.txt`. Lo único no NASA que queda en el globo terrestre es el contorno de Natural Earth 110m. Estos relieves son solo visuales: no cambian el índice, δ ni Supabase.
