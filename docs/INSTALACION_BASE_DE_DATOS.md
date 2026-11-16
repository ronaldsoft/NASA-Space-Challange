# Instalación de la base de datos y ejecución de la aplicación

ANALOG — análogos terrestres de la Luna y de Marte. NASA Space Apps Challenge 2026, Devebug Industries.

Este documento sirve para reproducir la base Postgres en **tu** proyecto de Supabase o en un Postgres local, y para levantar el tablero. No uses las credenciales del proyecto del equipo.

El tablero funciona sin base de datos: modo estático, con `web/public/productos/`. La base es opcional y entrega métricas, misiones, estaciones y candidatos por RPC.

Nunca pongas una contraseña de Postgres ni una *service-role key* en el frontend, en `.env.local` ni en Vercel.

## 1. Requisitos

- Git.
- Node.js 20 o superior (`./levantar.sh` lo comprueba).
- Python 3.10 o superior, solo para generar la carga o las teselas.
- Cliente `psql` (PostgreSQL 15 o 17). En Supabase el motor del equipo es Postgres 17 con PostGIS 3.3 en el esquema `extensions`.
- Opcional: Docker o un Postgres local con PostGIS; CLI de Supabase; Unity 6000.6.9f1 con el módulo WebGL.

Los paquetes de Python **no** están todos en `requirements.txt` de la raíz (ese archivo solo lista `numpy`, `Pillow` y `pytest`). Instala lo que vayas a usar:

```bash
python3 -m venv .venv && . .venv/bin/activate

# Carga del modelo actual (db/load_modelo_v2.py)
pip install numpy pandas rasterio pyarrow

# Teselas (pipeline_v2/teselas_v2.py)
pip install numpy rasterio pillow pyshp

# Carga de la v1 (db/load_analog_v1.py), solo si la necesitas
pip install "psycopg[binary]"
```

## 2. Estructura del repositorio

```
NASA-Space-Challange/
  db/
    001_schema.sql                 # esquema original en public (mock; no es el modelo oficial)
    002_rpc.sql                    # RPC mock en public
    003_seed_mock.sql              # semilla mock; no la uses para reproducir el modelo
    010_analog_schema.sql          # esquema oficial analog, PostGIS, tablas v1, RLS
    011_analog_rpc.sql             # analog_get_validation_table, analog_get_zone_card
    012_corrida_banda_propia.sql   # corrida oficial v1 (umbrales, rásteres, zonas)
    013_modelo_v2.sql              # tablas y RPC del modelo actual
    load_analog_v1.py              # carga v1 desde catalogo.json (ver limitación en §4)
    load_modelo_v2.py              # genera los INSERT del modelo actual; no se conecta a la base
  data/processed/modelo_v2/        # GeoTIFF y métricas (los .tif no están en git)
  pipeline_v2/                     # máscara IGBP, métricas, teselas
  web/                             # tablero Vite
    public/productos/tiles/        # teselas XYZ (sí van en el repositorio, ~122 MB)
    public/unity/                  # visor WebGL
    .env.example
  docs/fuentes_datos_nasa.md
  docs/metodologia_v2.md
```

Tres conjuntos de datos **no** están en el repositorio y hay que pedirlos al equipo:

1. `hackaton/outputs/`: `puntos_globales_100k_por_astro.parquet`, `firmas_misiones_5km.csv`, `catalogo_misiones_articulo.csv`, `estaciones_terrestres_articulo.csv` y `revision/estaciones_originales.csv`. En la máquina del equipo viven en `~/localhost/hackaton/outputs/`.
2. Los GeoTIFF de `data/processed/modelo_v2/`, ignorados por `data/.gitignore`: `mapa_analogia_tierra_5km_v2.tif`, `similitud_ecuador_1km_v2.tif`, `igbp_cmg_2022_005.tif`, `igbp_ecuador_2022_1km.tif`. En un clon limpio solo aparecen `metricas_v2.json` y `mascara_mcd12_resumen.json`.
3. Los lotes SQL que genera `load_modelo_v2.py` (~45 MB) tampoco están en git; se regeneran con (1) y (2).

Sin (1) y (2) puedes crear el esquema y correr el tablero en modo estático (las teselas sí están en git), pero no podrás llenar las tablas del modelo actual.

## 3. Crear la base de datos

Orden oficial: `010` → `011` → carga v1 (opcional) → `012` (opcional; los resultados de validación exigen sitios v1) → `013` → lotes del modelo actual.

`001`, `002` y `003` no hacen falta para este modelo. Crean tablas mock en `public` y no sustituyen al esquema `analog`.

Qué crea cada migración:

| Archivo | Efecto |
|---|---|
| `001_schema.sql` | Extensión PostGIS y tablas en `public` (`bodies`, `variables`, `cells`, firmas, validación, umbrales, etc.). |
| `002_rpc.sql` | `get_validation_table()` y `get_zone_card()` en `public`. |
| `003_seed_mock.sql` | Semilla mock. No la ejecutes para una reproducción oficial. |
| `010_analog_schema.sql` | Esquema `analog`; tablas v1 (`bodies`, `variables`, `std_params`, `signatures`, `validation_sites`, `validation_results`, `thresholds`, `ecuador_results`, `ecuador_rasters`, `priority_zones`); RLS de solo lectura; `GRANT` a `anon` y `authenticated`. |
| `011_analog_rpc.sql` | `public.analog_get_validation_table()` y `public.analog_get_zone_card(text)`. |
| `012_corrida_banda_propia.sql` | Columnas `corrida` y `area`; la clave de `validation_results` pasa a `(site_id, corrida)`; inserta umbrales, metadatos de rásteres y zonas de la corrida `banda_propia`. Los resultados de validación solo se insertan si ya hay filas en `analog.validation_sites`. |
| `013_modelo_v2.sql` | Tablas `analog.v2_reference_points`, `v2_mission_signatures`, `v2_terrestrial_stations`, `v2_candidates`, `v2_metrics`, `v2_layers`, y los RPC `public.analog_v2_*`. No borra las tablas v1. |

### A. Supabase (proyecto nuevo)

1. Crea un proyecto en [supabase.com](https://supabase.com) (Postgres 15 o posterior; el del equipo usa 17).
2. En Database → Extensions, comprueba que `postgis` está instalada en el esquema `extensions`. En un proyecto nuevo suele venir así.
3. Aplica las migraciones en orden, con `psql` (preferible) o con el SQL Editor.

```bash
# Valores en el entorno; no los imprimas.
# <TU_PROJECT_REF> es el id del proyecto (el subdominio de https://<ref>.supabase.co).
# <TU_DB_PASSWORD> es la contraseña de la base (Settings → Database),
# no la clave publicable ni la service-role key.

export PGPASSWORD='<TU_DB_PASSWORD>'
export PGSSLMODE=require
psql "host=db.<TU_PROJECT_REF>.supabase.co port=5432 dbname=postgres user=postgres" \
  -v ON_ERROR_STOP=1 \
  -f db/010_analog_schema.sql \
  -f db/011_analog_rpc.sql \
  -f db/012_corrida_banda_propia.sql \
  -f db/013_modelo_v2.sql
```

Si el puerto 5432 está bloqueado, usa el *Session pooler* (modo sesión, no transacción):

```text
host=<TU_REGION>.pooler.supabase.com
port=5432
user=postgres.<TU_PROJECT_REF>
dbname=postgres
sslmode=require
```

No uses el *Transaction pooler* (puerto 6543) para migraciones ni para los lotes grandes.

En el SQL Editor: pega y ejecuta `010`, `011`, `013` (y `012` si la quieres), de un archivo por vez. No pegues ahí los lotes de 300.000 puntos.

CLI de Supabase, opcional, enlazada a **tu** proyecto:

```bash
npx supabase db execute --file db/010_analog_schema.sql
# igual con 011, 012 y 013
```

En Settings → API, el esquema expuesto por defecto es `public`. Basta, porque los RPC viven en `public`. Si quieres leer `analog.v2_*` por REST directo, añade `analog` a los esquemas expuestos.

### B. Postgres local o Docker

PostGIS tiene que quedar en el esquema `extensions`, igual que en Supabase. Si lo instalas en `public`, `013_modelo_v2.sql` falla: usa `extensions.geometry` y `extensions.ST_*`. No lo sustituyas por un `DOMAIN`: un dominio no acepta el modificador `(Point, 4326)`.

```bash
docker run -d --name analog-pg \
  -e POSTGRES_PASSWORD='<TU_DB_PASSWORD>' \
  -e POSTGRES_DB=analog \
  -p 5432:5432 \
  postgis/postgis:17-3.5
```

Cuando acepte conexiones:

```bash
psql "host=127.0.0.1 port=5432 dbname=analog user=postgres" <<'SQL'
CREATE SCHEMA IF NOT EXISTS extensions;
CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA extensions;
DO $$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'anon') THEN
    CREATE ROLE anon NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'authenticated') THEN
    CREATE ROLE authenticated NOLOGIN;
  END IF;
END $$;
ALTER DATABASE analog SET search_path TO public, extensions;
SQL
```

Reconecta para tomar el `search_path` y aplica las migraciones:

```bash
psql "host=127.0.0.1 port=5432 dbname=analog user=postgres" \
  -v ON_ERROR_STOP=1 \
  -f db/010_analog_schema.sql \
  -f db/011_analog_rpc.sql \
  -f db/012_corrida_banda_propia.sql \
  -f db/013_modelo_v2.sql
```

Sin Docker, en Debian o Ubuntu:

```bash
sudo apt install postgresql-17 postgresql-17-postgis-3
sudo -u postgres createdb analog
# Los mismos SQL de esquema, roles y search_path, y después las migraciones.
```

`010` ejecuta `CREATE EXTENSION IF NOT EXISTS postgis` sin esquema. Si ya está en `extensions`, no hace nada. Las columnas `geometry` de `010` resuelven bien si `search_path` incluye `extensions`.

## 4. Cargar los datos

### 4.1 Modelo actual (hace falta para los RPC `analog_v2_*`)

`db/load_modelo_v2.py` **no** se conecta a la base: escribe lotes `INSERT ... ON CONFLICT` y un `resumen.json`. Ejecútalo desde la **raíz del repositorio**, porque lee `web/public/productos/tabla_validacion.csv` con ruta relativa.

```bash
# <HACKATON_OUTPUTS> es la carpeta outputs/ del modelo
# (en el equipo: ~/localhost/hackaton/outputs).
python3 db/load_modelo_v2.py \
  <HACKATON_OUTPUTS> \
  data/processed/modelo_v2 \
  web/public/productos/tiles/teselas.json \
  /tmp/sql013
```

Filas esperadas (`resumen.json` y, al aplicar, las tablas):

| Tabla | Filas |
|---|---|
| `analog.v2_reference_points` | 300.000 (100.000 por cuerpo: Tierra, Marte, Luna) |
| `analog.v2_mission_signatures` | 24 (19 usadas en el modelo: 5 de Marte con `hydro_outcome = alto` y las 14 de la Luna) |
| `analog.v2_terrestrial_stations` | 29 (5 `estacion_original`, 5 `instalacion`, 19 `sitio_validacion`) |
| `analog.v2_candidates` | 82.516 (81.936 globales y 580 de Ecuador; celdas con `max(pct_marte, pct_luna) ≥ 95`) |
| `analog.v2_metrics` | 10 (9 claves de `metricas_v2.json` más `mascara_nasa_igbp`) |
| `analog.v2_layers` | 9 (3 fuentes × 3 bandas) |

Lotes: 50 de puntos, 1 de misiones, 1 de estaciones, 11 de candidatos, 1 de métricas, 1 de capas.

Aplícalos con el usuario `postgres` (o equivalente que evite el RLS). No uses la clave publicable.

```bash
export PGPASSWORD='<TU_DB_PASSWORD>'
export PGSSLMODE=require
for f in /tmp/sql013/*.sql; do
  echo "$f"
  psql "host=db.<TU_PROJECT_REF>.supabase.co port=5432 dbname=postgres user=postgres" \
    -v ON_ERROR_STOP=1 -f "$f"
done
```

En local, cambia el `host` y usa `dbname=analog`. El bucle respeta el orden alfabético de los prefijos `10_`, `20_`, …, que es el correcto.

Comprobación:

```sql
SELECT 'v2_reference_points' AS tabla, count(*) FROM analog.v2_reference_points
UNION ALL SELECT 'v2_mission_signatures', count(*) FROM analog.v2_mission_signatures
UNION ALL SELECT 'v2_terrestrial_stations', count(*) FROM analog.v2_terrestrial_stations
UNION ALL SELECT 'v2_candidates', count(*) FROM analog.v2_candidates
UNION ALL SELECT 'v2_candidates_global', count(*) FROM analog.v2_candidates WHERE scope = 'global'
UNION ALL SELECT 'v2_candidates_ecuador', count(*) FROM analog.v2_candidates WHERE scope = 'ecuador'
UNION ALL SELECT 'v2_metrics', count(*) FROM analog.v2_metrics
UNION ALL SELECT 'v2_layers', count(*) FROM analog.v2_layers
ORDER BY 1;

-- RPC que usa el tablero
SELECT count(*) FROM public.analog_v2_get_layers();        -- 9
SELECT count(*) FROM public.analog_v2_get_missions();      -- 24
SELECT kind, count(*) FROM public.analog_v2_get_stations() GROUP BY 1;
SELECT jsonb_object_keys(public.analog_v2_get_metrics());
-- Claves: auc_sitios_conocidos, jackknife_ecuador_v2, jackknife_global_muestra100k,
-- mascara_nasa_igbp, recuperacion_nulo_bloques, reproduccion_ecuador_1km,
-- semilla, sensibilidad_umbral, sitios, sitios_no_analogo

SELECT count(*) FROM public.analog_v2_candidates_bbox(
  'ecuador', 'marte', -92, -5.1, -75, 2, 95, 2000);
-- 387 celdas de Ecuador con índice de Marte ≥ 95 (el RPC recorta a 2.000)
```

Esas cifras se comprobaron el 15 de noviembre de 2026 (hora de Ecuador, UTC−5) en el proyecto del equipo, solo como referencia de conteo. En tu copia deben coincidir.

### 4.2 v1 oficial (opcional)

`db/load_analog_v1.py` lee `web/public/productos/catalogo.json` y exige la huella SHA-256 `369dd38593f76d46266d1cd86077ce4729fb7b1e3811adc66b74fe0be51c87dd`, la del commit `3b820e7`. El `catalogo.json` actual ya incorpora el modelo del 15 de noviembre y no coincide; el script se niega a cargar.

Para llenar las tablas v1: restaura ese archivo desde `3b820e7`, ejecuta el script y después vuelve a dejar el catálogo actual (el tablero lo necesita). El orden es `010`, `011`, `python3 db/load_analog_v1.py`, `012`. Si corres el script después de `012`, el `ON CONFLICT (site_id)` de `validation_results` deja de ser válido, porque la clave pasó a `(site_id, corrida)`.

El script usa `SUPABASE_PROJECT_ID` y `SUPABASE_DB_PASSWORD`, y de forma opcional `SUPABASE_DB_HOST`, `SUPABASE_DB_PORT` (5432) y `SUPABASE_DB_USER` (`postgres`). No imprime la contraseña.

Sin esa carga, `012` igual inserta 2 umbrales, 9 metadatos de rásteres y 12 zonas; `validation_sites` y `validation_results` quedan en 0. El tablero actual se apoya en el catálogo estático y en los RPC del modelo actual, así que la v1 en la base no es imprescindible.

## 5. RLS y permisos

Todas las tablas de `analog` tienen RLS activado. Hay políticas `FOR SELECT` para `anon` y `authenticated` con `USING (true)`. No hay políticas ni `GRANT` de INSERT, UPDATE o DELETE para esos roles. Las migraciones sí hacen `GRANT USAGE ON SCHEMA analog` y `GRANT SELECT` sobre las tablas.

Los RPC viven en `public`, son `SECURITY INVOKER` y `STABLE`, solo leen, y tienen `GRANT EXECUTE` a `anon` y `authenticated`:

- `analog_v2_get_layers()`
- `analog_v2_get_metrics()`
- `analog_v2_get_missions()`
- `analog_v2_get_stations()`
- `analog_v2_candidates_bbox(p_scope, p_banda, p_west, p_south, p_east, p_north, p_min, p_limit)`
- `analog_v2_nearest_candidates(p_lat, p_lon, p_km, p_scope, p_limit)`
- `analog_v2_points_sample(p_body, p_limit, p_solo_elegibles)`
- De la 011: `analog_get_validation_table()`, `analog_get_zone_card(text)`

La carga debe hacerse con el rol `postgres` (contraseña de la base, `<TU_DB_PASSWORD>`). Si cargas por la API REST, usa la *service-role key* (`<TU_SERVICE_ROLE_KEY>`), que evita el RLS; esa clave no entra nunca en el frontend. El rol `anon` (clave publicable, `<TU_CLAVE_PUBLICABLE>`) puede leer y no puede escribir.

## 6. Teselas

Están en `web/public/productos/tiles/`: XYZ de 256 px, EPSG:3857, cinco clases (0–49, 50–74, 75–89, 90–94, 95–100), sin dato transparente. Van en git (~29.800 PNG, unos 122 MB). Metadatos en `teselas.json`.

| Capa | Zooms | Teselas con dato |
|---|---|---|
| `global/{marte,luna,conjunta}` | 0–6 | 1.847 cada una |
| `global_sin_ecuador/{marte,luna,conjunta}` | 6 | 1.218 cada una (Ecuador recortado) |
| `ecuador/{marte,luna,conjunta}` | 5–9 | 80 cada una |

El tablero cruza la opacidad entre zoom 5,5 y 6,5: al alejarse, el modelo global; al acercarse, Ecuador y el global sin Ecuador.

Para regenerarlas hacen falta los GeoTIFF de `data/processed/modelo_v2/` (no están en git) y el shapefile Natural Earth 10 m admin-0, campo `ADM0_A3 = ECU`. Descarga: <https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_countries.zip>.

```bash
python3 pipeline_v2/teselas_v2.py \
  data/processed/modelo_v2 \
  /ruta/ne_10m_admin_0_countries.shp \
  web/public/productos/tiles
```

Sobrescribe `web/public/productos/tiles/` y reescribe `teselas.json`. La versión actual del script colorea la banda de Marte en una rampa rojiza (`rgba_marte`); Luna y conjunta mantienen la rampa original.

Esos rásteres los genera `pipeline_v2/` (máscara MCD12Q1 vía GIBS y métricas) a partir de `hackaton/outputs/` y de las fuentes de `docs/fuentes_datos_nasa.md`. Volver a producir los GeoTIFF desde las fuentes brutas (GMTED2010, MCD43C3, MOLA, LOLA, etc.) no se detalla aquí; ver `docs/metodologia_v2.md`.

## 7. Correr la aplicación

### 7.1 En local

```bash
cd web
cp .env.example .env.local
```

En `web/.env.local` define solo esto:

```bash
VITE_SUPABASE_URL=<TU_SUPABASE_URL>
VITE_SUPABASE_ANON_KEY=<TU_CLAVE_PUBLICABLE>
```

`<TU_SUPABASE_URL>` es `https://<TU_PROJECT_REF>.supabase.co`. `<TU_CLAVE_PUBLICABLE>` es la *anon* / *publishable key* (Settings → API). El código también acepta el alias `VITE_SUPABASE_KEY`, pero usa el nombre de `.env.example`. Nunca pongas `<TU_DB_PASSWORD>` ni `<TU_SERVICE_ROLE_KEY>` en este archivo.

```bash
npm install
npm run dev          # Vite; en general http://127.0.0.1:5173/
npm test             # vitest
npm run build        # tsc --noEmit && vite build
npm run preview      # http://127.0.0.1:4173/
```

Desde la raíz, `./levantar.sh` instala, compila y sirve en el puerto 4173, con el visor Unity incluido. Hace falta Node 20+. Si el 4173 está ocupado: `PUERTO=4174 ./levantar.sh`.

Si no defines las dos variables, o si el RPC falla, el tablero usa `web/public/productos/catalogo.json` y las teselas estáticas. El visor Unity no consulta Supabase.

Vite incrusta las `VITE_*` en el build: después de cambiar `.env.local` hay que volver a compilar (`npm run build` o `./levantar.sh`).

### 7.2 En tu propio Vercel

1. Root Directory: `web`. El `web/vercel.json` ya está (SPA y cabeceras CORS para `/unity/`).
2. Variables de entorno del proyecto, en Production y Preview: `VITE_SUPABASE_URL` y `VITE_SUPABASE_ANON_KEY`. Nunca la contraseña de la base ni la *service-role key*.
3. En Supabase, Authentication → URL Configuration, añade la URL de Vercel si el navegador bloquea las peticiones.
4. Despliega:

```bash
cd web
npx vercel --prod
```

O conecta el repositorio en el panel de Vercel, con Root Directory `web`. Tras cambiar una variable `VITE_*`, lanza un deploy nuevo.

Un plan Hobby alcanza para el sitio estático. Teselas y visor Unity suman decenas de MB.

## 8. Visualizador Unity (Explorar Ecuador)

El build WebGL publicado está en `web/public/unity/visualizador/` y se sirve en `/unity/visualizador/`. Unity 6000.6.9f1, compresión WebGL desactivada. El tablero lo carga en un iframe.

El proyecto de Unity, en el equipo, está en `~/localhost/SpaceApps/VisualizadorAnalog`. `BuildScript.BuildWebGL` escribe en `../Build/WebGL` (o sea, `~/localhost/SpaceApps/Build/WebGL`).

Para recompilar, **no uses `construir.sh`**. Ese script extrae `unity_src.tgz` sobre el proyecto y pisa el código y los datos actuales. Usa el editor o, en lote:

```bash
# Unity 6000.6.9f1 con el módulo WebGL instalado.
/Applications/Unity/Hub/Editor/6000.6.9f1/Unity.app/Contents/MacOS/Unity \
  -batchmode -quit -nographics \
  -projectPath /ruta/a/VisualizadorAnalog \
  -buildTarget WebGL \
  -executeMethod BuildScript.BuildWebGL \
  -logFile /tmp/unity_webgl.log
```

Copia el contenido de `Build/WebGL/` sobre `web/public/unity/visualizador/` y vuelve a `npm run build`. El menú `ANALOG/Construir WebGL` llama al mismo método.

## 9. Problemas frecuentes

**CORS.** El tablero llama a `<TU_SUPABASE_URL>/rest/v1/rpc/analog_v2_*` con la clave publicable. Si el navegador bloquea, añade el origen (local y Vercel) en Authentication → URL Configuration. El API de Supabase suele aceptar orígenes de navegador con la anon key; el síntoma de un fallo es que el tablero cae al catálogo estático. `web/vercel.json` ya envía CORS para `/unity/*`. No abras el visor con `file://`.

**El RPC falla y el tablero «no usa la base».** Es el respaldo previsto: vuelve a `catalogo.json`. Comprueba que aplicaste la 013, que `v2_metrics` y `v2_layers` tienen filas, y que las `VITE_*` existían al compilar.

**Variables de entorno.** En el frontend solo `VITE_SUPABASE_URL` y `VITE_SUPABASE_ANON_KEY`. Si faltan, modo estático. Un error habitual es pegar la *service-role key* en el cliente: esa clave evita el RLS y no debe salir del servidor de carga.

**`013` falla con `type "extensions.geometry" does not exist` o `type modifier is not allowed`.** PostGIS no está en el esquema `extensions`, o lo sustituiste por un `DOMAIN`. Instálalo con `CREATE EXTENSION postgis WITH SCHEMA extensions`.

**Roles `anon` / `authenticated` no existen** (Postgres local). Créalos como en §3.B; si no, los `GRANT` de 010 y 013 fallan.

**El puerto 5432 de Supabase no responde.** Usa el Session pooler o una red que deje salir a ese puerto. Algunos entornos alcanzan el API HTTPS y no el 5432.

**Cargas grandes.** Los 50+11 lotes pesan unos 45 MB. No los pegues en el SQL Editor. Usa `psql -f` con `ON_ERROR_STOP=1`, conexión directa o Session pooler, no Transaction pooler. Si un lote falla a mitad, puedes repetirlo: son `ON CONFLICT DO NOTHING` o `DO UPDATE`.

**`load_analog_v1.py` sale con `catalogo.json hash does not match`.** El catálogo actual no es el de la v1 congelada. Ver §4.2.

**`npm run test:sql`.** `package.json` apunta a `../db/test_sql.mjs`, que no está en el repositorio. Usa `npm test`.

**Teselas 404 o el mapa interpreta un `index.html` como imagen.** En `vite preview`, un PNG ausente puede devolver la SPA con 200. El generador escribe teselas transparentes para evitarlo; no borres a mano los PNG «vacíos».

## 10. Fuentes de los datos

La lista verificada, con DOI y URL, está en [`docs/fuentes_datos_nasa.md`](fuentes_datos_nasa.md). El método (percentiles, máscara IGBP, AUC, umbral ≥95) está en [`docs/metodologia_v2.md`](metodologia_v2.md).

Resumen de lo que entra al modelo actual:

- Elevación y pendiente: Marte, MOLA MEGDR (NASA PDS); Luna, LOLA LDEM_64 (NASA PDS); Tierra, GMTED2010 (USGS/NGA, doi:10.3133/ofr20111073). GMTED no es NASA; queda como limitación declarada.
- Albedo: Tierra, MODIS MCD43C3 v061 (doi:10.5067/MODIS/MCD43C3.061); Marte, TES; Luna, LROC WAC.
- Máscara de cobertura: MODIS MCD12Q1 v061 (doi:10.5067/MODIS/MCD12Q1.061) leída de NASA GIBS y agregada al estilo MCD12C1 (doi:10.5067/MODIS/MCD12C1.061). El HDF de MCD12C1 no se descargó.
- Máscara base de bosque y agua: ESA CCI Land Cover 2022 (doi:10.24381/cds.006f2c9a); limitación, no es NASA.
- Recorte de Ecuador en las teselas z6: Natural Earth 10 m admin-0, dominio público.
- Firmas: 24 sitios de aterrizaje; el modelo usa 19 (5 de Marte con resultado hidrológico alto y las 14 de la Luna).
