# Cómo ejecutar ANALOG / delta

Un solo comando, en la raíz del repositorio, instala las dependencias, compila el tablero y sirve **todo** (el tablero y el visualizador 3D de Unity) en un único servidor, en el puerto 4173:

```bash
./levantar.sh
```

Luego abre http://127.0.0.1:4173/ (tablero, con el globo). El visualizador queda incrustado en la misma aplicación:

- pestaña **Visualizador 3D**;
- en la vista del globo, el botón **Ver en 3D (Unity)** abre el mismo visor en un panel lateral (en el teléfono, a pantalla completa, con un botón **Cerrar**), sin abrir otra pestaña.

La dirección directa del visor, en el mismo servidor, es http://127.0.0.1:4173/unity/visualizador/.

Para detenerlo: Ctrl+C. Para usar otro puerto libre: `PUERTO=4174 ./levantar.sh`.

## English summary

From the repository root, `./levantar.sh` installs dependencies, builds the site and serves the dashboard and the embedded Unity visualizer on **one** server, port 4173. Open http://127.0.0.1:4173/. Requirements: Node 20+ and git. The default is static mode (no `.env`). Optional Supabase mode uses only `VITE_SUPABASE_URL` and the publishable key in `web/.env.local`, never a database password. To stop the server: Ctrl+C.

## Requisitos

- **Node.js 20 o superior** (el script comprueba la versión).
- **git**, si clonas el repositorio o un bundle.
- **Python 3** solo hace falta si quieres volver a correr el pipeline o sus pruebas, no para ver el tablero.

## Modo estático (el defecto)

No hace falta ningún archivo `.env`. El tablero lee `web/public/productos/catalogo.json` y las capas congeladas de la v1. `./levantar.sh` termina en `vite preview` de la carpeta `web/dist`.

## Modo Supabase (opcional)

Si quieres que la tabla de validación y las fichas se lean de la base:

1. Copia `web/.env.example` a `web/.env.local` (ese archivo no se publica).
2. Define solo `VITE_SUPABASE_URL` y la clave publicable (`VITE_SUPABASE_ANON_KEY`). Nunca la contraseña de la base ni una service-role key.
3. Vuelve a correr `./levantar.sh` (hay que recompilar para que Vite tome las variables).

Si el RPC falla, el tablero vuelve al catálogo estático. El visualizador Unity no usa Supabase.

## Pruebas

En `web/`:

```bash
cd web
npm test          # vitest: textos del índice (fraseParecido, etc.)
```

El pipeline, si tienes el entorno Python del repositorio:

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/pytest -q pipeline/tests/test_pipeline.py
```

No hace falta correr el pipeline para levantar el tablero.

## Problemas frecuentes

- **Puerto 4173 ocupado.** El preview usa `--strictPort` y no se pasa a otro puerto solo. Cierra el proceso que lo está usando (`ss -ltnp | grep 4173` o `lsof -i :4173`) o arranca con `PUERTO=4174 ./levantar.sh`.
- **Caché de Vite o de npm.** Si el build falla de forma rara, borra `web/node_modules` y `web/dist` y vuelve a correr `./levantar.sh`. En `web/.npmrc` ya está `legacy-peer-deps=true`, que hace falta para `npm ci`.
- **El visualizador no carga.** Tiene que servirse por http, no abriendo `index.html` con `file://`. Usa el servidor de `./levantar.sh` (puerto 4173) o la pestaña y el panel del tablero, que apuntan a `/unity/visualizador/`.

## Qué no está todavía en el README

El README guarda tal cual las secciones del equipo, el patrocinio y el texto de Ronald (What We Do, Blind Validation, Impact). Esas partes no se reescriben aquí. El README técnico en español y en inglés todavía describe la corrida previa `todas_min` como si fuera el modo oficial; la v1 oficial es `banda_propia` (después de ver el AUC de `todas_min`). Galápagos es solo área de evaluación. El detalle está en `docs/version_congelada_v1_banda_propia.md` y en `docs/nota_incertidumbre.md`.

## GitHub Pages (opcional)

No se publica solo. En el repositorio hay un flujo `GitHub Pages` que se dispara a mano (`workflow_dispatch`), no en cada push. Compila el tablero con `VITE_BASE=/NASA-Space-Challange/` (el nombre del repo público). En GitHub hay que tener Pages con “GitHub Actions” como origen y lanzar ese flujo. La URL queda en `https://ronaldsoft.github.io/NASA-Space-Challange/`. En local, `./levantar.sh` sigue sirviendo todo en el puerto 4173, con la base `/`.
