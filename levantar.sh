#!/usr/bin/env bash
# Un solo comando: instala, compila y sirve el tablero y el visualizador 3D
# en un único servidor (vite preview) en el puerto 4173.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PUERTO="${PUERTO:-4173}"

if ! command -v node >/dev/null 2>&1; then
  echo "Hace falta Node.js 20 o superior. No se encontró 'node' en el PATH." >&2
  exit 1
fi

MAJOR="$(node -p "process.versions.node.split('.')[0]")"
if [ "$MAJOR" -lt 20 ]; then
  echo "Hace falta Node.js 20 o superior. Esta máquina tiene $(node -v)." >&2
  exit 1
fi

cd "$ROOT/web"
echo "Instalando dependencias (npm ci)…"
npm ci
echo "Compilando el tablero…"
npm run build
echo
echo "Sirviendo el tablero y el visualizador 3D en un solo servidor, puerto ${PUERTO}."
echo "  Tablero:       http://127.0.0.1:${PUERTO}/"
echo "  Visualizador:  http://127.0.0.1:${PUERTO}/unity/visualizador/"
echo "Para detenerlo: Ctrl+C."
echo
exec npx vite preview --host --port "$PUERTO" --strictPort
