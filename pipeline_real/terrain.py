"""Remuestreo, pendiente (Horn) y rugosidad TRI 3x3 sobre un DEM ya alineado."""

from __future__ import annotations

import math
from typing import Optional

import numpy as np
from rasterio.transform import Affine, array_bounds
from rasterio.warp import Resampling, reproject

NODATA = -9999.0


def lat_for_rows(transform: Affine, height: int) -> np.ndarray:
    """Latitud del centro de cada fila (aplica geotransformación con col=0)."""
    height = int(height)
    # y = d*col + e*row + f; centro de fila = row + 0.5, col = 0
    rows = np.arange(height, dtype=np.float64) + 0.5
    return np.asarray(transform.f + transform.d * 0.0 + transform.e * rows, dtype=np.float64)


def lon_for_cols(transform: Affine, width: int) -> np.ndarray:
    width = int(width)
    cols = np.arange(width, dtype=np.float64) + 0.5
    return np.asarray(transform.c + transform.a * cols + transform.b * 0.0, dtype=np.float64)


def meters_per_degree(radius_m: float) -> float:
    return radius_m * math.pi / 180.0


def slope_and_tri(
    z: np.ndarray,
    transform: Affine,
    radius_m: float,
    nodata: float = NODATA,
    wrap_x: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    """Pendiente en grados (Horn) y TRI de Wilson (media de |Δz| en ventana 3x3).

    `z` es un recorte (con halo de 1 píxel si se procesa por tiras).
    `transform` corresponde a ese recorte.
    Las filas de borde (sin 8 vecinos) y las celdas con vecino nulo salen nodata.
    En X se puede envolver la longitud (globo).
    """
    z = np.asarray(z, dtype=np.float64)
    n_rows, n_cols = z.shape
    valid = np.isfinite(z) & (z != nodata)

    if wrap_x:
        zpad = np.pad(z, ((1, 1), (1, 1)), mode="wrap")
        # overwrite north/south pad (wrap would be wrong in Y)
        zpad[0, 1:-1] = nodata
        zpad[-1, 1:-1] = nodata
        zpad[0, 0] = zpad[0, -1] = zpad[-1, 0] = zpad[-1, -1] = nodata
        vpad = np.pad(valid, ((1, 1), (1, 1)), mode="wrap")
        vpad[0, :] = False
        vpad[-1, :] = False
    else:
        zpad = np.full((n_rows + 2, n_cols + 2), nodata, dtype=np.float64)
        zpad[1:-1, 1:-1] = z
        vpad = np.zeros((n_rows + 2, n_cols + 2), dtype=bool)
        vpad[1:-1, 1:-1] = valid

    # neighbors a b c / d e f / g h i  (Horn)
    a, b, c = zpad[0:-2, 0:-2], zpad[0:-2, 1:-1], zpad[0:-2, 2:]
    d, e, f = zpad[1:-1, 0:-2], zpad[1:-1, 1:-1], zpad[1:-1, 2:]
    g, h, i = zpad[2:, 0:-2], zpad[2:, 1:-1], zpad[2:, 2:]
    va, vb, vc = vpad[0:-2, 0:-2], vpad[0:-2, 1:-1], vpad[0:-2, 2:]
    vd, ve, vf = vpad[1:-1, 0:-2], vpad[1:-1, 1:-1], vpad[1:-1, 2:]
    vg, vh, vi = vpad[2:, 0:-2], vpad[2:, 1:-1], vpad[2:, 2:]
    all8 = va & vb & vc & vd & ve & vf & vg & vh & vi

    lats = lat_for_rows(transform, n_rows)
    mpd = meters_per_degree(radius_m)
    px = float(abs(transform.a))
    py = float(abs(transform.e))
    # evite dx→0 en los polos
    coslat = np.cos(np.radians(np.clip(lats, -89.9, 89.9)))
    dx = (mpd * coslat * px)[:, None]  # (n_rows, 1)
    dy = mpd * py

    dzdx = ((c + 2.0 * f + i) - (a + 2.0 * d + g)) / (8.0 * dx)
    dzdy = ((g + 2.0 * h + i) - (a + 2.0 * b + c)) / (8.0 * dy)
    slope = np.degrees(np.arctan(np.sqrt(dzdx * dzdx + dzdy * dzdy)))

    diffs = np.stack(
        [
            np.abs(a - e),
            np.abs(b - e),
            np.abs(c - e),
            np.abs(d - e),
            np.abs(f - e),
            np.abs(g - e),
            np.abs(h - e),
            np.abs(i - e),
        ],
        axis=0,
    )
    tri = diffs.mean(axis=0)

    slope = np.where(all8, slope, nodata).astype(np.float32)
    tri = np.where(all8, tri, nodata).astype(np.float32)
    return slope, tri


def reproject_array(
    src: np.ndarray,
    src_transform: Affine,
    src_crs,
    dst_shape: tuple[int, int],
    dst_transform: Affine,
    dst_crs,
    src_nodata: Optional[float],
    dst_nodata: float = NODATA,
    resampling: Resampling = Resampling.bilinear,
) -> np.ndarray:
    dest = np.full(dst_shape, dst_nodata, dtype=np.float32)
    reproject(
        source=src.astype(np.float32, copy=False),
        destination=dest,
        src_transform=src_transform,
        src_crs=src_crs,
        src_nodata=src_nodata,
        dst_transform=dst_transform,
        dst_crs=dst_crs,
        dst_nodata=dst_nodata,
        resampling=resampling,
    )
    return dest


def grid_from_bounds(
    west: float,
    south: float,
    east: float,
    north: float,
    res: float,
    origin_west: float = -180.0,
    origin_north: float = 90.0,
) -> tuple[Affine, int, int]:
    """Grilla alineada a un origen global (mismo tamaño de celda y origen)."""
    col0 = int(math.floor((west - origin_west) / res + 1e-12))
    col1 = int(math.ceil((east - origin_west) / res - 1e-12))
    row0 = int(math.floor((origin_north - north) / res + 1e-12))
    row1 = int(math.ceil((origin_north - south) / res - 1e-12))
    width = max(1, col1 - col0)
    height = max(1, row1 - row0)
    transform = Affine(res, 0.0, origin_west + col0 * res, 0.0, -res, origin_north - row0 * res)
    return transform, width, height


def snapped_global_grid(res_nominal: float) -> tuple[Affine, int, int, float]:
    """Grilla global [-180,180] x [-90,90] con un número entero de celdas ≈ res_nominal."""
    width = int(round(360.0 / res_nominal))
    height = int(round(180.0 / res_nominal))
    res_x = 360.0 / width
    res_y = 180.0 / height
    # usamos res_x==res_y en la práctica (debe ser idéntico salvo redondeo)
    res = res_x
    # fuerza cobertura exacta
    height = int(round(180.0 / res))
    res_y = 180.0 / height
    transform = Affine(res, 0.0, -180.0, 0.0, -res_y, 90.0)
    return transform, width, height, res
