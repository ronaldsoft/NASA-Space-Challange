"""Remuestreo a una grilla geográfica común."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class GeoTransform:
    """
    Transformación afín sencilla de una grilla geográfica.

    El píxel (fila 0, col 0) tiene su esquina noroeste en (west, north).
    res_lon es positivo hacia el este; res_lat es negativo si el norte está arriba.
    """

    west: float
    north: float
    res_lon: float
    res_lat: float  # normalmente negativo

    @property
    def east(self) -> float:
        raise RuntimeError("use east_of(ncols)")

    def east_of(self, ncols: int) -> float:
        return self.west + ncols * self.res_lon

    def south_of(self, nrows: int) -> float:
        return self.north + nrows * self.res_lat

    def pixel_center(self, row: NDArray | int, col: NDArray | int) -> tuple[NDArray, NDArray]:
        lon = self.west + (np.asarray(col) + 0.5) * self.res_lon
        lat = self.north + (np.asarray(row) + 0.5) * self.res_lat
        return lon, lat

    def coord_to_index(self, lon: NDArray, lat: NDArray) -> tuple[NDArray, NDArray]:
        col = (np.asarray(lon) - self.west) / self.res_lon - 0.5
        row = (np.asarray(lat) - self.north) / self.res_lat - 0.5
        return row, col


def resample_to_grid(
    array: NDArray,
    src: GeoTransform,
    dst: GeoTransform,
    dst_shape: tuple[int, int],
    method: str = "bilinear",
    nodata: float | None = None,
) -> NDArray:
    """
    Remuestrea un arreglo 2D a la grilla destino.

    Parameters
    ----------
    array :
        Ráster de origen (filas × columnas). Compatible con el array de
        rasterio/xarray (se usa solo el ndarray).
    src, dst :
        Transformaciones geográfica de origen y destino.
    dst_shape :
        (filas, columnas) de la grilla destino.
    method :
        ``nearest`` o ``bilinear``. La resolución objetivo del proyecto es
        1 km; pendiente y rugosidad deben recalcularse sobre el DEM ya
        remuestreado, no interpolarse desde derivados de otra resolución.
    nodata :
        Valor nulo del origen; en el destino se escribe np.nan.

    Returns
    -------
    ndarray flotante de forma dst_shape, con np.nan en nodata o fuera de
    la extensión de origen.
    """
    if method not in {"nearest", "bilinear"}:
        raise ValueError(f"método no soportado: {method}")

    src_arr = np.asarray(array, dtype=float)
    if src_arr.ndim != 2:
        raise ValueError("array debe ser 2D")
    nrows_src, ncols_src = src_arr.shape
    if nodata is not None:
        src_arr = src_arr.copy()
        src_arr[src_arr == nodata] = np.nan

    rows = np.arange(dst_shape[0])
    cols = np.arange(dst_shape[1])
    cc, rr = np.meshgrid(cols, rows)
    lon, lat = dst.pixel_center(rr, cc)
    src_r, src_c = src.coord_to_index(lon, lat)

    out = np.full(dst_shape, np.nan, dtype=float)

    if method == "nearest":
        r0 = np.rint(src_r).astype(int)
        c0 = np.rint(src_c).astype(int)
        valid = (r0 >= 0) & (r0 < nrows_src) & (c0 >= 0) & (c0 < ncols_src)
        out[valid] = src_arr[r0[valid], c0[valid]]
        return out

    # Bilineal. Se admite el rango de centros [0, n-1]; en el último
    # índice (fraccionaria = 0) se toma esa celda (r0 = n-2, dr = 1).
    valid = (
        np.isfinite(src_r)
        & np.isfinite(src_c)
        & (src_r >= 0)
        & (src_r <= nrows_src - 1)
        & (src_c >= 0)
        & (src_c <= ncols_src - 1)
    )
    r0 = np.floor(src_r).astype(int)
    c0 = np.floor(src_c).astype(int)
    r0 = np.clip(r0, 0, max(nrows_src - 2, 0))
    c0 = np.clip(c0, 0, max(ncols_src - 2, 0))
    r1 = r0 + 1
    c1 = c0 + 1
    dr = src_r[valid] - r0[valid]
    dc = src_c[valid] - c0[valid]
    v00 = src_arr[r0[valid], c0[valid]]
    v01 = src_arr[r0[valid], c1[valid]]
    v10 = src_arr[r1[valid], c0[valid]]
    v11 = src_arr[r1[valid], c1[valid]]
    # Si algún vecino es nan, el resultado es nan (no inventar dato).
    out[valid] = (
        v00 * (1 - dr) * (1 - dc)
        + v01 * (1 - dr) * dc
        + v10 * dr * (1 - dc)
        + v11 * dr * dc
    )
    return out
