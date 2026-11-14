# Exportación Unity (WebGL) — ANALOG/delta v1 congelada

Estos archivos son una **lectura** de los productos oficiales de la v1 (14 de noviembre de 2026, America/Guayaquil). No recalculan el índice. En un despliegue estático (por ejemplo Vercel) viven en la ruta pública `/unity/`.

Manifiesto: `/unity/manifest.json`. Incluye la huella SHA-256 del catálogo congelado (`docs/version_congelada_v1.md`).

## Contenido

| Archivo | Uso |
|---|---|
| `delta_marte.png` / `delta_luna.png` | Textura de datos: RGBA 8 bits, R=G=B = `round(δ × 255)`, alpha 0 = no-dato, 255 = válido. δ ∈ [0, 1]. |
| `delta_marte_preview.png` / `delta_luna_preview.png` | La misma grilla, coloreada para inspección visual. |
| `clases.png` | Textura de clases: 0 = ninguno, 1 = Marte, 2 = Luna, 3 = ambos, 255 / alpha 0 = no-dato. **Secundaria:** el umbral de Marte tiene especificidad 0; no usarla como inventario ni para porcentajes de cobertura. |
| `hillshade.png` | Sombreado del DEM GLO-90 a ~1 km (solo visual; acimut 315°, elevación 45°). |
| `*.json` (mismo nombre que cada PNG) | Metadatos: bounds lon/lat, CRS, ancho/alto, affine, codificación, no-dato. |
| `sitios_validacion.geojson` | 19 sitios de validación con los resultados oficiales (δ, clases, acierto, si entra al AUC). |
| `zonas_prioritarias.geojson` | Zonas prioritarias de Ecuador (puntos). |

Grilla común: 1890 × 756 celdas, 0,009° (~1 km), CRS **EPSG:4326** (WGS 84). Extensión: oeste −92,007°, sur −5,103°, este −74,997°, norte 1,701°. La fila 0 es el norte; el origen del affine está en la esquina superior izquierda.

## Cómo cargar las texturas en Unity

1. Descarga o incluye los PNG (por `UnityWebRequestTexture` desde `/unity/...` o como `Resources`).
2. `Texture2D tex = DownloadHandlerTexture.GetContent(req);`  
   En importación: desactiva *sRGB* en las texturas de **datos** (δ y clases) si vas a leer el byte como valor; deja sRGB en las vistas previas y el hillshade. `Filter Mode = Point` (sin interpolación bilinear sobre clases o δ cuantizado). `Wrap Mode = Clamp`.
3. Cada texel `(col, rowUnity)` debe mapearse a la celda de la grilla. Unity pone `uv.y = 0` abajo; esta PNG tiene la fila 0 arriba. Usa:

```csharp
// uv en [0,1] sobre un plano que representa el recorte de Ecuador
int col = Mathf.Clamp((int)(uv.x * width), 0, width - 1);
int rowSrc = Mathf.Clamp((int)((1f - uv.y) * height), 0, height - 1); // origen norte
Color32 c = tex.GetPixel(col, rowSrc); // si la textura no está volteada
if (c.a == 0) { /* nodata */ }
float delta = c.r / 255f;              // texturas de δ
int clase = c.r;                       // textura de clases (0,1,2,3)
```

Si Unity voltea la textura al importar, no apliques el `(1 - uv.y)` o márcala como *Flip V*.

4. De lon/lat a UV del plano (el plano cubre exactamente los bounds del JSON):

```csharp
float u = (lon - boundsOeste) / (boundsEste - boundsOeste);
float v = (lat - boundsSur)  / (boundsNorte - boundsSur); // v=0 al sur, v=1 al norte
```

5. Sitios y zonas: parsea los GeoJSON (`coordinates` = `[lon, lat]`) y coloca prefabs con la misma fórmula. El campo `buffer_km` es el radio oficial en el suelo, no en UV.

Un shader sencillo puede colorear δ (0 = oscuro, 1 = claro) leyendo el canal R y recortando con alpha.

## CORS y origen

- Si el visualizador WebGL va **incrustado en el mismo sitio** que sirve `/unity/` (el dashboard en Vercel), las peticiones son del mismo origen y no hace falta CORS.
- Si lo cargas desde otro origen (otro dominio, o un build WebGL alojado aparte), el servidor debe enviar `Access-Control-Allow-Origin` para `/unity/*`. El `web/vercel.json` del dashboard incluye esa cabecera para esta carpeta. No abras los JSON con `file://` (los navegadores bloquean el fetch).
- Los PNG no pesan más de ~1 MB cada uno; conviene un `UnityWebRequest` con caché y no descomprimir a RGBA32 de 32 bits si no hace falta.

## Versión

v1 congelada, 14 de noviembre de 2026. No modificar estos archivos para «mejorar» el índice: cualquier cambio visual debe partir de una nueva exportación, no de reeditar el PNG a mano.
