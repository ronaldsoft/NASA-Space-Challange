# Pipeline de datos reales (superficie, ~1 km)

Prepara los DEM de Marte (MOLA MEGDR 64 ppd), la Luna (LOLA LDEM_64) y la Tierra (Copernicus DEM GLO-90) sobre una grilla geográfica de ~1 km, y recalcula pendiente (Horn) y rugosidad (TRI 3×3) sobre ese DEM remuestreado.

Documentación de lo descargado, datums, resoluciones y limitaciones: [`../data/README.md`](../data/README.md). Todo el texto de documentación está en español. Los nombres de los datasets (MOLA, LOLA, Copernicus GLO-90) se dejan en el idioma original.

## Cómo reproducir

```bash
cd /workspace/analogs/pipeline_real
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python download_planetary.py
.venv/bin/python download_earth.py
.venv/bin/python process.py          # grillas globales Marte/Luna + Tierra
.venv/bin/python run_remaining.py    # re-muestreo de bandas oficiales y docs
```

`run_remaining.py` también escribe la tabla de validación en `../data/processed/earth/validation_sites.csv` y en `/workspace/validacion_sitios.csv`.

## Scripts

- `config.py` — radios, celdas de 1 km, sitios oficiales de Expertos, bandas A–G
- `download_planetary.py` / `download_earth.py` — descargas públicas, sin autenticación
- `terrain.py` — remuestreo, pendiente Horn, TRI Wilson
- `process.py` — mosaicos, grillas de 1 km, muestreo estratificado
- `write_docs.py` — `variables.json`, `manifest.json` y README en español
