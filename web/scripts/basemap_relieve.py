#!/usr/bin/env python3
"""Relieve sombreado uniforme para el globo del tablero (Luna y Marte, datos NASA PDS).

Método (igual para todos los cuerpos):
  * DEM promediado por área a una malla equirectangular de 2048×1024.
  * Horn 3×3, acimut geográfico 315° (luz desde el noroeste), altura solar 45°.
  * Celda métrica a partir del radio del cuerpo: dx = R·Δλ·cos φ, dy = R·Δφ.
  * Exageración vertical z = tamaño de píxel ecuatorial (m) / 1066.
  * Salida clip(hs, 0, 1)·255, sin percentiles ni gamma; alfa 255, nodata alfa 0.
  * Reproyección a Web Mercator 2048×2048 que cubre exactamente las esquinas WORLD
    de web/src/maps.ts (lon ±179.9°, lat ±85°), para que la capa image de MapLibre
    ponga cada cráter en su latitud real.

Solo lee los IMG originales del PDS (numpy + Pillow, sin GDAL). No toca δ ni el índice.

Uso:
  python3 web/scripts/basemap_relieve.py luna marte
  python3 web/scripts/basemap_relieve.py --raw /ruta/a/data/raw --out web/public/basemap luna
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
EQ_W, EQ_H = 2048, 1024      # malla equirectangular de cálculo
OUT_W, OUT_H = 2048, 2048    # PNG Web Mercator
# Esquinas de la capa image en web/src/maps.ts (const WORLD)
WORLD_LON = 179.9
WORLD_LAT = 85.0

DEFAULT_RAW = Path("/workspace/analogs/data/raw")
DEFAULT_OUT = Path(__file__).resolve().parents[1] / "public" / "basemap"


# ---------------------------------------------------------------- lectura PDS
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


def _area_resize(a: np.ndarray, w: int, h: int) -> np.ndarray:
    im = Image.fromarray(a.astype(np.float32), mode="F")
    return np.asarray(im.resize((w, h), Image.Resampling.BOX), dtype=np.float64)


def leer_luna(raw: Path) -> np.ndarray:
    """LOLA LDEM_64 (23040×11520, int16 LSB, 0.5 m/DN, lon 0→360 E, fila 0 = 90°N)."""
    p = raw / "moon/lola_ldem64/ldem_64.img"
    a = np.memmap(p, dtype="<i2", mode="r", shape=(11520, 23040))
    return _area_resize(_block_mean(a, 0.5, 0.0, 9), EQ_W, EQ_H)


def leer_marte(raw: Path) -> np.ndarray:
    """MOLA MEGDR 64 ppd (4 teselas 5760×11520, int16 MSB, m sobre el areoide)."""
    d = raw / "mars/mola_megdr64"
    t = {k: np.memmap(d / f"megt{k}gb.img", dtype=">i2", mode="r", shape=(5760, 11520))
         for k in ("90n000", "90n180", "00n000", "00n180")}
    norte = np.hstack([_block_mean(t["90n000"], 1, 0, 9), _block_mean(t["90n180"], 1, 0, 9)])
    sur = np.hstack([_block_mean(t["00n000"], 1, 0, 9), _block_mean(t["00n180"], 1, 0, 9)])
    return _area_resize(np.vstack([norte, sur]), EQ_W, EQ_H)


CUERPOS = {
    # nombre: (radio m, lector, archivo, fuente)
    "luna": (1737400.0, leer_luna, "hillshade_luna.png",
             "LOLA LDEM_64 (LRO-L-LOLA-3-RDR-V1, NASA PDS Geosciences)"),
    "marte": (3396000.0, leer_marte, "hillshade_marte.png",
              "MOLA MEGDR 64 ppd MEGT (MGS-M-MOLA-5-MEGDR-L3-V1.0, NASA PDS Geosciences)"),
}


# ---------------------------------------------------------------- sombreado
def horn_hillshade(z: np.ndarray, radius: float, zfactor: float) -> np.ndarray:
    """Horn 3×3 en malla equirectangular global (lon con vuelta, fila 0 = norte)."""
    h, w = z.shape
    dlam = 2 * math.pi / w
    dphi = math.pi / h
    lat = (90.0 - (np.arange(h) + 0.5) * 180.0 / h)
    dx = (radius * dlam * np.cos(np.radians(lat)))[:, None]
    dy = radius * dphi
    p = np.pad(z, ((1, 1), (0, 0)), mode="edge")
    W = lambda a: np.roll(a, 1, axis=1)   # vecino oeste
    E = lambda a: np.roll(a, -1, axis=1)  # vecino este
    up, mid, dn = p[:-2], p[1:-1], p[2:]
    dzdx = ((E(up) + 2 * E(mid) + E(dn)) - (W(up) + 2 * W(mid) + W(dn))) / (8 * dx)
    dzdn = ((W(up) + 2 * up + E(up)) - (W(dn) + 2 * dn + E(dn))) / (8 * dy)  # hacia el norte
    nx, ny, nz = -zfactor * dzdx, -zfactor * dzdn, np.ones_like(dzdx)
    norm = np.sqrt(nx * nx + ny * ny + nz * nz)
    az, alt = math.radians(AZIMUTH_DEG), math.radians(ALTITUDE_DEG)
    lx, ly, lz = math.sin(az) * math.cos(alt), math.cos(az) * math.cos(alt), math.sin(alt)
    return (nx * lx + ny * ly + nz * lz) / norm


# ---------------------------------------------------------------- Mercator
def a_mercator(hs: np.ndarray) -> np.ndarray:
    """Remuestrea (bilineal) la malla equirectangular a Web Mercator sobre WORLD."""
    h, w = hs.shape
    ymax = math.log(math.tan(math.pi / 4 + math.radians(WORLD_LAT) / 2))
    y = ymax - (np.arange(OUT_H) + 0.5) * (2 * ymax / OUT_H)
    lat = np.degrees(np.arctan(np.sinh(y)))
    lon = -WORLD_LON + (np.arange(OUT_W) + 0.5) * (2 * WORLD_LON / OUT_W)
    lon360 = np.mod(lon, 360.0)
    fr = (90.0 - lat) / 180.0 * h - 0.5
    fc = lon360 / 360.0 * w - 0.5
    r0 = np.clip(np.floor(fr).astype(int), 0, h - 2); tr = np.clip(fr - r0, 0, 1)
    c0 = np.floor(fc).astype(int); tc = fc - c0
    c0m, c1m = np.mod(c0, w), np.mod(c0 + 1, w)
    R0, R1 = r0[:, None], (r0 + 1)[:, None]
    TR, TC = tr[:, None], tc[None, :]
    top = hs[R0, c0m[None, :]] * (1 - TC) + hs[R0, c1m[None, :]] * TC
    bot = hs[R1, c0m[None, :]] * (1 - TC) + hs[R1, c1m[None, :]] * TC
    return top * (1 - TR) + bot * TR


def procesar(nombre: str, raw: Path, out: Path) -> dict:
    radius, lector, archivo, fuente = CUERPOS[nombre]
    dem = lector(raw)
    valid = np.isfinite(dem)
    dem = np.where(valid, dem, np.nanmedian(dem))
    px_m = radius * 2 * math.pi / EQ_W
    zf = px_m / Z_DIVISOR
    hs = horn_hillshade(dem, radius, zf)
    hs = np.where(valid, hs, np.nan)
    merc = a_mercator(np.nan_to_num(hs, nan=0.0))
    alpha = a_mercator(valid.astype(np.float64)) > 0.5
    g = np.rint(np.clip(merc, 0, 1) * 255).astype(np.uint8)
    rgba = np.dstack([g, g, g, np.where(alpha, 255, 0).astype(np.uint8)])
    out.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, mode="RGBA").save(out / archivo, format="PNG", optimize=True)
    info = dict(cuerpo=nombre, archivo=archivo, fuente=fuente, radio_m=radius,
                pixel_ecuatorial_m=round(px_m, 1), z=round(zf, 3),
                negro_puro_pct=round(float((g == 0).mean() * 100), 2),
                media=round(float(g.mean()), 1))
    print(info)
    return info


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cuerpos", nargs="*", default=["luna", "marte"], choices=sorted(CUERPOS))
    ap.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    a = ap.parse_args()
    for c in a.cuerpos:
        procesar(c, a.raw, a.out)


if __name__ == "__main__":
    main()
