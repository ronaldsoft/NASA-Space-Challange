# Visualizador Unity (WebGL) — ANALOG/delta v1

Compilado con Unity 6000.6.9f1 en la MacBook de Ronald (proyecto: /Users/ussenterprise/localhost/SpaceApps/VisualizadorAnalog).
Compresión: desactivada (sirve tal cual en Vercel/estático, sin cabeceras Content-Encoding).

## Contenido
- index.html (responsive, en español) · Build/WebGL.{loader.js,framework.js,wasm,data}
- StreamingAssets/data/: visualizador.json (todo lo que muestra la UI, del catalogo.json v1 congelado),
  ecuador_*.png (relieve y capas δ Marte/δ Luna/clases sobre hillshade GLO-90), ecuador_altura_u16.bytes (630×252, uint16 LE, fila 0 = norte, máx 6018,8 m),
  textura_marte.png / textura_luna.png (relieve sombreado derivado de MOLA MEGDR 64 ppd y LOLA LDEM_64), GeoJSON de sitios de validación, zonas de Ecuador y sitios objetivo NASA (solo referencia), validacion_v1.json.

## Incrustar en el dashboard (/visualizador)
1. Copiar la carpeta completa:  mkdir -p /workspace/analogs/web/public/unity && cp -r /workspace/unity_webgl /workspace/analogs/web/public/unity/visualizador
   (Vite copia public/ a dist/; /unity/ ya está excluido del rewrite SPA en web/vercel.json)
2. Crear la ruta /visualizador con un iframe:
   <iframe src="/unity/visualizador/index.html" title="Visualizador 3D ANALOG v1"
           style="width:100%;height:calc(100vh - 64px);border:0" allow="fullscreen"></iframe>
3. Vercel: si se añade una cabecera de tipo, que .wasm salga como application/wasm (Vercel ya lo hace por defecto). No hace falta configurar Content-Encoding porque no hay .gz/.br.
4. No usar otra carpeta fuera de /unity/ (o /mock/, /productos/): el rewrite SPA de vercel.json reescribiría Build/*.wasm y StreamingAssets/* a index.html.
