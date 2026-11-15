#!/usr/bin/env python3
"""Relieve sombreado uniforme para el globo del tablero (Luna, Marte y Tierra, datos NASA).

Método (igual para Luna, Marte y Tierra):
  * DEM promediado (bloques 3×3) a una malla fina y luego promediado por área exacta
    directamente en la malla Web Mercator de salida, 2048×2048, que cubre las esquinas WORLD
    de web/src/maps.ts (lon ±179,9°, lat ±85°). Así cada cráter cae en su latitud real y
    no hay escalones a latitudes altas.
  * Horn 3×3 en esa malla, acimut geográfico 315° (luz desde el noroeste), altura solar 45°.
  * Celda métrica a partir del radio del cuerpo: Mercator es conforme, la celda mide
    R·Δλ·cos φ en x y en y (= dx = R·Δλ·cos φ, dy = R·Δφ a esta escala).
  * Exageración vertical z = tamaño de píxel ecuatorial (m) / 1066, una sola por cuerpo.
  * Salida clip(hs, 0, 1)·255, sin percentiles ni gamma; alfa 255 en tierra, mar/nodata alfa 0.
  * Ecuador: lo mismo a 30" nativo (≈926,6 m, z = 0,87) sobre AREA_BOUNDS.completo, filas en
    y de Mercator, con una rampa de alfa de FEATHER_PX píxeles en los bordes del recuadro al
    este de 82°W, para que no se vea el corte sobre Colombia y Perú (Galápagos no se toca).

Cuerpos: luna (LOLA LDEM_64), marte (MOLA MEGDR 64 ppd), tierra (SRTMGL30 V002, global)
y ecuador (SRTMGL30 V002 a 30" nativo, recortado a AREA_BOUNDS.completo de maps.ts).

Tierra/Ecuador: los .DEM de SRTMGL30 vienen sin .hdr; formato GTOPO30: int16 big-endian,
6000 filas × 4800 columnas por tesela de 40° lon × 50° lat, celda 30" (1/120°), esquina
superior izquierda = nombre de la tesela (p. ej. W100N40 -> lon -100, lat 40). nodata = -9999
(no aparece en V002) y el mar viene como 0 m: 0 y -9999 se tratan como mar/nodata (alfa 0).
SRTMGL30 llega solo hasta 60°S: la Antártida queda transparente (alfa 0).

Solo lee los archivos originales (numpy + Pillow, sin GDAL). No toca δ ni el índice.

Uso:
  python3 web/scripts/basemap_relieve.py luna marte tierra ecuador
  python3 web/scripts/basemap_relieve.py --raw /ruta/a/data/raw --srtm /ruta/teselas --out web/public/basemap tierra
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
from PIL import Image

AZIMUTH_DEG = 315.0          # geográfico, horario desde el norte
ALTITUDE_DEG = 45.0
Z_DIVISOR = 1066.0           # z = tamaño de píxel ecuatorial en metros / 1066
FEATHER_PX = 120             # Ecuador: rampa de alfa en los bordes del recuadro (≈110 km)
FEATHER_DESDE_LON = -82.0    # solo al este de aquí (continente); Galápagos no se toca
OUT_W, OUT_H = 2048, 2048    # PNG Web Mercator
# Esquinas de la capa image en web/src/maps.ts (const WORLD)
WORLD_LON = 179.9
WORLD_LAT = 85.0

DEFAULT_RAW = Path("/workspace/analogs/data/raw")
DEFAULT_SRTM = Path("/workspace/data_nasa/srtmgl30/unz")   # *.DEM descomprimidos
R_TIERRA = 6371008.8                                        # radio medio IUGG (m)
# AREA_BOUNDS.completo de web/src/maps.ts (capa hs_ecuador, imageCoords)
ECUADOR = dict(oeste=-92.007, sur=-5.103, este=-74.997, norte=1.701)
DEFAULT_OUT = Path(__file__).resolve().parents[1] / "public" / "basemap"


# ---------------------------------------------------------------- lectura
def _block_mean(src: np.ndarray, scale: float, offset: float, f: int) -> np.ndarray:
    """Promedio por bloques f×f leyendo por franjas (memmap)."""
    h, w = src.shape
    out = np.empty((h // f, w // f), dtype=np.float64)
    step = f * 64
    for r0 in range(0, h, step):
        blk = src[r0:r0 + step].astype(np.float64) * scale + offset
        bh = blk.shape[0] // f
        out[r0 // f:r0 // f + bh] = blk[:bh * f].reshape(bh, f, w // f, f).mean(axis=(1, 3))
    return out


# SRTMGL30 V002: teselas GTOPO30 de 40° lon × 50° lat, celda 30", sin .hdr
SRTM_ROWS, SRTM_COLS, SRTM_CELL = 6000, 4800, 1.0 / 120.0


def _tesela_srtm(path: Path) -> tuple[np.ndarray, float, float]:
    n = path.name.upper()
    lon = (-1 if n[0] == "W" else 1) * int(n[1:4])
    lat = (-1 if n[4] == "S" else 1) * int(n[5:7])
    a = np.fromfile(path, dtype=">i2")
    assert a.size == SRTM_ROWS * SRTM_COLS, path
    return a.reshape(SRTM_ROWS, SRTM_COLS), lon, lat


CUERPOS = {
    # nombre: (radio m, archivo, fuente)
    "luna": (1737400.0, "hillshade_luna.png",
             "LOLA LDEM_64 (LRO-L-LOLA-3-RDR-V1, NASA PDS Geosciences)"),
    "marte": (3396000.0, "hillshade_marte.png",
              "MOLA MEGDR 64 ppd MEGT (MGS-M-MOLA-5-MEGDR-L3-V1.0, NASA PDS Geosciences)"),
    "tierra": (R_TIERRA, "hillshade_tierra.png",
               "SRTMGL30 V002 (NASA JPL / LP DAAC, doi:10.5067/MEaSUREs/SRTM/SRTMGL30.002)"),
}


# ------------------------------------------------- malla fina + Mercator nativo
# El sombreado se calcula directamente en la malla Mercator de salida (2048×2048 sobre WORLD).
# Cada fila es un promedio por área exacto de la malla fina (1/3 de la resolución nativa),
# así que a latitudes altas no hay escalones por ampliar una malla gruesa.
# Mercator es conforme: la celda mide R·Δλ·cos φ en x y en y (pendiente física real en cada fila).
# z es uno solo por cuerpo: tamaño de píxel ecuatorial (m) / 1066 (Luna 5,00; Marte 9,77;
# Tierra 18,33), así la misma pendiente física se sombrea igual a cualquier latitud.

def fino_luna(raw: Path):
    a = np.memmap(raw / "moon/lola_ldem64/ldem_64.img", dtype="<i2", mode="r", shape=(11520, 23040))
    return _block_mean(a, 0.5, 0.0, 3), None, 0.0, 3 / 64.0          # lon 0 en columna 0


def fino_marte(raw: Path):
    d = raw / "mars/mola_megdr64"
    t = {k: np.memmap(d / f"megt{k}gb.img", dtype=">i2", mode="r", shape=(5760, 11520))
         for k in ("90n000", "90n180", "00n000", "00n180")}
    z = np.vstack([np.hstack([_block_mean(t["90n000"], 1, 0, 3), _block_mean(t["90n180"], 1, 0, 3)]),
                   np.hstack([_block_mean(t["00n000"], 1, 0, 3), _block_mean(t["00n180"], 1, 0, 3)])])
    return z, None, 0.0, 3 / 64.0


def fino_tierra(srtm: Path):
    f = 3
    res = SRTM_CELL * f                                           # 1/40° ≈ 2,8 km
    H, W = int(round(180 / res)), int(round(360 / res))
    elev = np.zeros((H, W), np.float32); land = np.zeros((H, W), np.float32)
    teselas = sorted(srtm.glob("*.DEM"))
    assert len(teselas) == 27, f"se esperaban 27 teselas, hay {len(teselas)}"
    for p in teselas:
        a, lon, lat = _tesela_srtm(p)
        ok = (a != -9999) & (a != 0)                               # 0 m = mar en SRTMGL30 V002
        h, w = SRTM_ROWS // f, SRTM_COLS // f
        r0, c0 = int(round((90 - lat) / res)), int(round((lon + 180) / res))
        elev[r0:r0 + h, c0:c0 + w] = np.where(ok, a, 0).astype(np.float32).reshape(h, f, w, f).mean(axis=(1, 3))
        land[r0:r0 + h, c0:c0 + w] = ok.astype(np.float32).reshape(h, f, w, f).mean(axis=(1, 3))
    return elev, land, -180.0, res                                  # sur de 60°S: land = 0


def _rows_area_mean(a: np.ndarray, top: np.ndarray, bot: np.ndarray) -> np.ndarray:
    """Promedio exacto por área entre las filas fraccionarias [top, bot) (cumsum interpolado)."""
    cum = np.vstack([np.zeros((1, a.shape[1])), np.cumsum(a, axis=0, dtype=np.float64)])
    def C(x):
        i = np.clip(np.floor(x).astype(int), 0, a.shape[0] - 1)
        t = (x - i)[:, None]
        return cum[i] + (cum[i + 1] - cum[i]) * t
    return (C(bot) - C(top)) / (bot - top)[:, None]


def a_mercator_fino(a: np.ndarray, lon0: float, res: float) -> np.ndarray:
    H, W = a.shape
    # columnas: promedio por área sobre lon -179,9..179,9
    sh = int(round((-180.0 - lon0) / res)) % W                    # columna de lon -180
    a = np.roll(a, -sh, axis=1)
    x0, x1 = (180 - WORLD_LON) / res, (180 + WORLD_LON) / res
    im = Image.fromarray(a.astype(np.float32), mode="F")
    a = np.asarray(im.resize((OUT_W, H), Image.Resampling.BOX, box=(x0, 0, x1, H)), dtype=np.float64)
    # filas: bordes en y de Mercator, área exacta en latitud
    ymax = math.log(math.tan(math.pi / 4 + math.radians(WORLD_LAT) / 2))
    ye = ymax - np.arange(OUT_H + 1) * (2 * ymax / OUT_H)
    late = np.degrees(np.arctan(np.sinh(ye)))
    fr = (90.0 - late) / res
    return _rows_area_mean(a, fr[:-1], fr[1:])


def horn_mercator(z: np.ndarray, radius: float) -> tuple[np.ndarray, np.ndarray]:
    ymax = math.log(math.tan(math.pi / 4 + math.radians(WORLD_LAT) / 2))
    yc = ymax - (np.arange(OUT_H) + 0.5) * (2 * ymax / OUT_H)
    lat = np.degrees(np.arctan(np.sinh(yc)))
    cell = radius * math.radians(2 * WORLD_LON / OUT_W) * np.cos(np.radians(lat))   # m, conforme
    zf = np.full_like(cell, radius * math.radians(2 * WORLD_LON / OUT_W) / Z_DIVISOR)
    p = np.pad(z, ((1, 1), (0, 0)), mode="edge")
    W_ = lambda a: np.roll(a, 1, axis=1); E_ = lambda a: np.roll(a, -1, axis=1)
    up, mid, dn = p[:-2], p[1:-1], p[2:]
    c = cell[:, None]
    dzdx = ((E_(up) + 2 * E_(mid) + E_(dn)) - (W_(up) + 2 * W_(mid) + W_(dn))) / (8 * c)
    dzdn = ((W_(up) + 2 * up + E_(up)) - (W_(dn) + 2 * dn + E_(dn))) / (8 * c)
    nx, ny = -zf[:, None] * dzdx, -zf[:, None] * dzdn
    norm = np.sqrt(nx * nx + ny * ny + 1)
    az, alt = math.radians(AZIMUTH_DEG), math.radians(ALTITUDE_DEG)
    hs = (nx * math.sin(az) * math.cos(alt) + ny * math.cos(az) * math.cos(alt) + math.sin(alt)) / norm
    return hs, zf


FINOS = {"luna": fino_luna, "marte": fino_marte, "tierra": fino_tierra}


def procesar(nombre: str, raw: Path, out: Path, srtm: Path = DEFAULT_SRTM) -> dict:
    radius, archivo, fuente = CUERPOS[nombre]
    z, frac, lon0, res = FINOS[nombre](srtm if nombre == "tierra" else raw)
    zm = a_mercator_fino(z, lon0, res); del z
    alpha = (a_mercator_fino(frac, lon0, res) >= 0.5) if frac is not None else np.ones_like(zm, bool)
    hs, zf = horn_mercator(zm, radius)
    g = np.rint(np.clip(hs, 0, 1) * 255).astype(np.uint8)
    rgba = np.dstack([g, g, g, np.where(alpha, 255, 0).astype(np.uint8)])
    out.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, mode="RGBA").save(out / archivo, format="PNG", optimize=True)
    info = dict(cuerpo=nombre, archivo=archivo, fuente=fuente, radio_m=radius,
                pixel_ecuatorial_m=round(radius * math.radians(2 * WORLD_LON / OUT_W), 1),
                z=round(float(zf[0]), 3),
                negro_puro_pct=round(float((g[alpha] == 0).mean() * 100), 2),
                blanco_puro_pct=round(float((g[alpha] == 255).mean() * 100), 2),
                media=round(float(g[alpha].mean()), 1), visible_pct=round(float(alpha.mean() * 100), 1))
    print(info)
    return info


def procesar_ecuador(srtm: Path, out: Path) -> dict:
    """SRTMGL30 a 30" nativo sobre AREA_BOUNDS.completo (incluye Galápagos), filas en Mercator."""
    b = ECUADOR
    a, lon0, lat0 = _tesela_srtm(next(p for p in srtm.glob("*.DEM") if p.name.upper().startswith("W100N40")))
    assert (lon0, lat0) == (-100, 40)
    pad = 2
    r0 = int(math.floor((lat0 - b["norte"]) / SRTM_CELL)) - pad
    r1 = int(math.ceil((lat0 - b["sur"]) / SRTM_CELL)) + pad
    c0 = int(math.floor((b["oeste"] - lon0) / SRTM_CELL)) - pad
    c1 = int(math.ceil((b["este"] - lon0) / SRTM_CELL)) + pad
    sub = a[r0:r1, c0:c1].astype(np.float64)
    land = (sub != -9999) & (sub != 0)
    z = np.where(land, sub, 0.0)
    px_m = R_TIERRA * math.radians(SRTM_CELL)            # ≈ 926,6 m
    zf = px_m / Z_DIVISOR
    # Horn con celda métrica (dx = R·Δλ·cos φ por fila, dy = R·Δφ), sin vuelta en longitud
    lat_c = lat0 - (r0 + np.arange(sub.shape[0]) + 0.5) * SRTM_CELL
    dx = (px_m * np.cos(np.radians(lat_c)))[1:-1, None]
    dy = px_m
    up, mid, dn = z[:-2], z[1:-1], z[2:]
    L = lambda m: m[:, :-2]; C = lambda m: m[:, 1:-1]; Rr = lambda m: m[:, 2:]
    dzdx = ((Rr(up) + 2 * Rr(mid) + Rr(dn)) - (L(up) + 2 * L(mid) + L(dn))) / (8 * dx)
    dzdn = ((L(up) + 2 * C(up) + Rr(up)) - (L(dn) + 2 * C(dn) + Rr(dn))) / (8 * dy)
    nx, ny = -zf * dzdx, -zf * dzdn
    norm = np.sqrt(nx * nx + ny * ny + 1)
    az, alt = math.radians(AZIMUTH_DEG), math.radians(ALTITUDE_DEG)
    hs = (nx * math.sin(az) * math.cos(alt) + ny * math.cos(az) * math.cos(alt) + math.sin(alt)) / norm
    land_c = land[1:-1, 1:-1].astype(np.float64)
    gr0, gc0 = r0 + 1, c0 + 1                              # índice de tesela de hs[0,0]
    # salida: columnas lineales en lon, filas lineales en y de Mercator; 30" en el ecuador
    W = int(round((b["este"] - b["oeste"]) / SRTM_CELL))
    merc = lambda la: math.log(math.tan(math.pi / 4 + math.radians(la) / 2))
    yn, ys = merc(b["norte"]), merc(b["sur"])
    H = int(round((yn - ys) / math.radians(SRTM_CELL)))
    lat = np.degrees(np.arctan(np.sinh(yn - (np.arange(H) + 0.5) * (yn - ys) / H)))
    lon = b["oeste"] + (np.arange(W) + 0.5) * (b["este"] - b["oeste"]) / W
    fr = (lat0 - lat) / SRTM_CELL - 0.5 - gr0
    fc = (lon - lon0) / SRTM_CELL - 0.5 - gc0
    def bil(m):
        i0 = np.clip(np.floor(fr).astype(int), 0, m.shape[0] - 2); ti = np.clip(fr - i0, 0, 1)[:, None]
        j0 = np.clip(np.floor(fc).astype(int), 0, m.shape[1] - 2); tj = np.clip(fc - j0, 0, 1)[None, :]
        I0, I1, J0, J1 = i0[:, None], i0[:, None] + 1, j0[None, :], j0[None, :] + 1
        return (m[I0, J0] * (1 - tj) + m[I0, J1] * tj) * (1 - ti) + (m[I1, J0] * (1 - tj) + m[I1, J1] * tj) * ti
    g = np.rint(np.clip(bil(hs), 0, 1) * 255).astype(np.uint8)
    yy, xx = np.mgrid[0:H, 0:W]
    edge = np.minimum(np.minimum(yy, H - 1 - yy), np.minimum(xx, W - 1 - xx)).astype(np.float64)
    ramp = np.clip((edge + 0.5) / FEATHER_PX, 0, 1)
    ramp[:, lon < FEATHER_DESDE_LON] = 1.0
    alpha = np.rint(np.where(bil(land_c) >= 0.5, 255.0, 0.0) * ramp).astype(np.uint8)
    out.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.dstack([g, g, g, alpha]), mode="RGBA").save(out / "hillshade_ecuador.png", format="PNG", optimize=True)
    info = dict(cuerpo="ecuador", archivo="hillshade_ecuador.png", tamano=f"{W}x{H}", bounds=b,
                pixel_m=round(px_m, 1), z=round(zf, 3), tierra_pct=round(float((alpha > 0).mean() * 100), 1), feather_px=FEATHER_PX)
    print(info)
    return info


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cuerpos", nargs="*", choices=sorted([*CUERPOS, "ecuador"]),
                    help="por defecto: luna marte tierra ecuador")
    ap.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    ap.add_argument("--srtm", type=Path, default=DEFAULT_SRTM)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    a = ap.parse_args()
    for c in a.cuerpos or ["luna", "marte", "tierra", "ecuador"]:
        if c == "ecuador":
            procesar_ecuador(a.srtm, a.out)
        else:
            procesar(c, a.raw, a.out, a.srtm)


if __name__ == "__main__":
    main()
