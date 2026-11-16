# Visualizador Unity (WebGL) «Explorar Ecuador»

Compilado con Unity 6000.6.9f1 (proyecto: ~/localhost/SpaceApps/VisualizadorAnalog), compresión desactivada.

- index.html: pantalla de carga en español o inglés según `?lang=es|en` (por defecto inglés, igual que web/src/i18n.ts).
  El dashboard lo carga como `/unity/visualizador/index.html?lang=${LANG}`.
- Build/WebGL.{loader.js,framework.js,wasm,data}
- StreamingAssets/data/:
  - textos.es.json, textos.en.json: todos los textos de la interfaz.
  - visualizador.es.json, visualizador.en.json: cifras, capas, clases, estaciones y misiones, generados desde web/src/datosModelo.ts y datosModelo.en.ts.
  - ecuador_similitud_marte.png, ecuador_similitud_luna.png: índice 0–100 del modelo de Ecuador del artículo final (30″, máscara ESA CCI 2022, antes del filtro QA) en 5 clases, mismos colores que el mapa web, sobre relieve sombreado.
  - ecuador_relieve.png, ecuador_altura_u16.bytes (630×252, uint16 LE, fila 0 = norte, máx 6018,8 m): Copernicus DEM GLO-90.
  - textura_marte.png, textura_luna.png (MOLA MEGDR 64 ppd, LOLA LDEM_64), textura_tierra.png (Natural Earth 110m).
