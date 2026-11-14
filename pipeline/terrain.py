"""Pendiente y rugosidad calculadas sobre el DEM ya remuestreado."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

# Radio medio de la Tierra (m), solo para convertir grados → metros en una
# grilla geográfica terrestre. En Marte/Luna el llamador debe pasar
# res_x_m y res_y_m ya convertidos con el radio del cuerpo.
EARTH_RADIUS_M = 6_371_000.0


def cell_sizes_m(
    lat_center: NDArray,
    res_lat_deg: float,
    res_lon_deg: float,
    radius_m: float = EARTH_RADIUS_M,
) -> tuple[NDArray, float]:
    """Tamaño de celda en metros (x varía con la latitud, y es constante)."""
    res_y_m = abs(res_lat_deg) * (np.pi / 180.0) * radius_m
    res_x_m = abs(res_lon_deg) * (np.pi / 180.0) * radius_m * np.cos(np.deg2rad(lat_center))
    # Evitar división por cero en los polos.
    res_x_m = np.maximum(res_x_m, 1.0)
    return res_x_m, float(res_y_m)


def slope(
    elevation: NDArray,
    res_y_m: float | NDArray,
    res_x_m: float | NDArray,
) -> NDArray:
    """
    Pendiente en grados a partir de un DEM remuestreado.

    No interpolar un ráster de pendiente de otra resolución: esta función
    debe aplicarse después de ``resample_to_grid`` sobre el DEM.

    Parameters
    ----------
    elevation :
        Elevación en metros (filas = norte→sur o según la grilla).
        Los nodata deben ir como np.nan.
    res_y_m :
        Tamaño de celda en el eje de filas, en metros.
    res_x_m :
        Tamaño de celda en el eje de columnas, en metros (escalar o
        arreglo por fila / del mismo shape).
    """
    z = np.asarray(elevation, dtype=float)
    if z.ndim != 2:
        raise ValueError("elevation debe ser 2D")

    dz_dy = np.gradient(z, axis=0)
    dz_dx = np.gradient(z, axis=1)

    # np.gradient asume spacing=1 píxel; convertimos a metros.
    if np.isscalar(res_y_m):
        dz_dy = dz_dy / float(res_y_m)
    else:
        dz_dy = dz_dy / np.asarray(res_y_m, dtype=float)

    if np.isscalar(res_x_m):
        dz_dx = dz_dx / float(res_x_m)
    else:
        rx = np.asarray(res_x_m, dtype=float)
        if rx.ndim == 1:
            rx = rx[:, None]
        dz_dx = dz_dx / rx

    return np.degrees(np.arctan(np.sqrt(dz_dx**2 + dz_dy**2)))


def roughness_tri(elevation: NDArray) -> NDArray:
    """
    Índice de rugosidad del terreno (TRI) de Riley et al. (1999):

        TRI = sqrt( sum_{i=1..8} (z_i - z_c)^2 )

    sobre una ventana 3×3. Las celdas del borde o con vecino nodata
    quedan en np.nan. Alternativa prevista en el método: desviación
    estándar de la elevación en la misma ventana (ver ``roughness_std``).
    """
    z = np.asarray(elevation, dtype=float)
    if z.ndim != 2:
        raise ValueError("elevation debe ser 2D")
    padded = np.pad(z, 1, constant_values=np.nan)
    center = padded[1:-1, 1:-1]
    acc = np.zeros_like(center)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue
            neigh = padded[1 + di : z.shape[0] + 1 + di, 1 + dj : z.shape[1] + 1 + dj]
            acc = acc + (neigh - center) ** 2
    tri = np.sqrt(acc)
    return tri


def roughness_std(elevation: NDArray) -> NDArray:
    """Desviación estándar de la elevación en ventana 3×3 (alternativa al TRI)."""
    z = np.asarray(elevation, dtype=float)
    padded = np.pad(z, 1, constant_values=np.nan)
    stack = []
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            stack.append(
                padded[1 + di : z.shape[0] + 1 + di, 1 + dj : z.shape[1] + 1 + dj]
            )
    return np.nanstd(np.stack(stack, axis=0), axis=0, ddof=0)


def nan_box_mean(elevation: NDArray, width: int = 15) -> NDArray:
    """Media local ignorando nodata (ventana cuadrada impar, p. ej. 15 celdas)."""
    z = np.asarray(elevation, dtype=float)
    if width % 2 == 0:
        width += 1
    m = np.isfinite(z)
    val = np.where(m, z, 0.0)
    cnt = m.astype(float)
    def prefix(a: NDArray) -> NDArray:
        p = np.pad(a, ((1, 0), (1, 0)), constant_values=0.0)
        return np.cumsum(np.cumsum(p, axis=0), axis=1)
    pv, pc = prefix(val), prefix(cnt)
    r = width // 2
    nrows, ncols = z.shape
    ii, jj = np.ogrid[0:nrows, 0:ncols]
    r0 = np.clip(ii - r, 0, nrows)
    r1 = np.clip(ii + r + 1, 0, nrows)
    c0 = np.clip(jj - r, 0, ncols)
    c1 = np.clip(jj + r + 1, 0, ncols)
    sm = pv[r1, c1] - pv[r0, c1] - pv[r1, c0] + pv[r0, c0]
    n = pc[r1, c1] - pc[r0, c1] - pc[r1, c0] + pc[r0, c0]
    return np.where(n > 0, sm / n, np.nan)
