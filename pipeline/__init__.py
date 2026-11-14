"""
Pipeline del índice ANALOG/delta.

Compara condiciones de superficie de la Tierra con firmas de Marte y de la
Luna por separado. No usa variables meteorológicas en el índice.

Funciones públicas (nombres estables para pruebas y para el flujo real):

- resample_to_grid
- slope
- roughness_tri
- fit_std_params
- sample_by_lat_bands
- build_signatures
- delta_index
- choose_threshold
- classify
"""

from .index import (
    MODO_BANDA_PROPIA,
    MODO_TODAS_MIN,
    choose_threshold,
    classify,
    delta_index,
    with_abs_latitude,
)
from .resample import GeoTransform, resample_to_grid
from .signatures import build_signatures, sample_by_lat_bands
from .standardize import apply_std_params, fit_std_params
from .terrain import roughness_tri, slope

__all__ = [
    "GeoTransform",
    "apply_std_params",
    "build_signatures",
    "MODO_BANDA_PROPIA",
    "MODO_TODAS_MIN",
    "choose_threshold",
    "classify",
    "delta_index",
    "fit_std_params",
    "resample_to_grid",
    "roughness_tri",
    "sample_by_lat_bands",
    "slope",
    "with_abs_latitude",
]

# Variables que entran al índice (v1, pendiente de albedo / inercia térmica).
INDEX_VARIABLES = ("latitude", "elevation", "slope", "roughness")
