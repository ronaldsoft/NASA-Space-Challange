# Base de datos / Database

Las migraciones `001_schema.sql`, `002_rpc.sql` y `003_seed_mock.sql` son el esquema original (esquema `public`) y una semilla **MOCK**. No las uses para cargar la v1 congelada.

La v1 oficial va en el esquema dedicado **`analog`**, para no tocar tablas preexistentes:

1. `010_analog_schema.sql` — PostGIS, tablas, RLS de solo lectura para `anon`/`authenticated`.
2. `011_analog_rpc.sql` — `analog_get_validation_table()` y `analog_get_zone_card(...)`.
3. `load_analog_v1.py` — carga los valores congelados desde `web/public/productos/` (requiere conexión Postgres).

Desde una red que alcance el puerto 5432 (o el session pooler 5432) de Supabase:

```bash
# Nombres de variables en el archivo de secretos; no imprimas los valores.
set -a && . /ruta/al/spaceapps_supabase.env && set +a
export PGPASSWORD="$SUPABASE_DB_PASSWORD"
psql "host=db.${SUPABASE_PROJECT_ID}.supabase.co port=5432 dbname=postgres user=postgres sslmode=require" \
  -f db/010_analog_schema.sql -f db/011_analog_rpc.sql
python3 db/load_analog_v1.py
```

Este entorno de desarrollo no pudo abrir el puerto 5432/6543 (tiempo de espera). El API HTTPS sí responde. En este box no se aplicaron las migraciones.

The original `001`–`003` files are the public-schema mock path. Official frozen v1 data belongs in the `analog` schema. This box could not open Postgres (TCP timeout); apply the scripts from a network that can reach Supabase port 5432.
