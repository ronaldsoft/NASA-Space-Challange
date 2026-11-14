"""
Firmas de referencia por banda de latitud.

Marte y la Luna no se mezclan. Cada banda se resume con mediana e IQR
(q1, q3). Las bandas se definen a partir de las latitudes de las
estaciones de validación (y bandas extra del diseño, p. ej. ecuatorial
para evaluar Ecuador).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable, Mapping, Sequence

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class LatBand:
    """Banda de latitud en valor absoluto (se muestrean ambos hemisferios)."""

    name: str
    abs_lat_min: float
    abs_lat_max: float

    def contains(self, lat: NDArray | float) -> NDArray:
        a = np.abs(np.asarray(lat, dtype=float))
        # La última banda (p. ej. G, 80–90) incluye el polo (|lat| = 90).
        if self.abs_lat_max >= 90:
            return (a >= self.abs_lat_min) & (a <= 90.0)
        return (a >= self.abs_lat_min) & (a < self.abs_lat_max)


@dataclass
class Signature:
    """Fila equivalente a la tabla ``signatures``."""

    body: str
    lat_band: str
    variable: str
    median: float
    q1: float
    q3: float
    n_cells: int

    def as_dict(self) -> dict:
        return asdict(self)


def assign_lat_band(lat: NDArray | float, bands: Sequence[LatBand]) -> np.ndarray:
    """Devuelve el nombre de banda para cada latitud (o '')."""
    lat_arr = np.asarray(lat, dtype=float)
    names = np.full(lat_arr.shape, "", dtype=object)
    for b in bands:
        names[b.contains(lat_arr)] = b.name
    return names if names.shape != () else names.item()


def sample_by_lat_bands(
    latitudes: NDArray,
    values_by_variable: Mapping[str, NDArray],
    bands: Sequence[LatBand],
    min_cells: int = 50,
    max_cells: int | None = None,
    rng: np.random.Generator | None = None,
) -> dict[str, dict[str, NDArray]]:
    """
    Muestreo estratificado por banda de latitud.

    Si una banda tiene al menos ``min_cells`` celdas válidas, se toma una
    muestra aleatoria de tamaño min(n, max_cells) o todas si max_cells es
    None, pero nunca menos de ``min_cells`` cuando hay suficientes.
    Si hay menos que el mínimo, se devuelve lo que hay y se deja constancia
    con la clave ``_short``.
    """
    if rng is None:
        rng = np.random.default_rng()
    lat = np.asarray(latitudes, dtype=float)
    n = lat.size
    for v in values_by_variable.values():
        if np.asarray(v).size != n:
            raise ValueError("todas las variables deben tener la misma longitud que latitudes")

    finite = np.ones(n, dtype=bool)
    for v in values_by_variable.values():
        finite &= np.isfinite(v)
    finite &= np.isfinite(lat)

    out: dict[str, dict[str, NDArray]] = {}
    for band in bands:
        mask = band.contains(lat) & finite
        idx = np.flatnonzero(mask)
        short = idx.size < min_cells
        if idx.size == 0:
            out[band.name] = {
                "latitude": np.array([]),
                "_n": np.array([0]),
                "_short": np.array([True]),
            }
            for name in values_by_variable:
                out[band.name][name] = np.array([])
            continue
        take = idx
        if max_cells is not None and idx.size > max_cells:
            take = rng.choice(idx, size=max_cells, replace=False)
        elif idx.size > min_cells and max_cells is None:
            # Se conservan todas las celdas válidas de la banda.
            take = idx
        sample: dict[str, NDArray] = {
            "latitude": lat[take],
            "_n": np.array([take.size]),
            "_short": np.array([short]),
        }
        for name, arr in values_by_variable.items():
            sample[name] = np.asarray(arr)[take]
        out[band.name] = sample
    return out


def build_signatures(
    body: str,
    samples_by_band: Mapping[str, Mapping[str, NDArray]],
    variables: Sequence[str],
) -> list[Signature]:
    """Mediana, q1 y q3 por banda y variable. ``body`` es 'moon' o 'mars'."""
    if body not in {"moon", "mars"}:
        raise ValueError("las firmas no deben mezclar Marte y Luna ni usar 'earth'")
    rows: list[Signature] = []
    for band, sample in samples_by_band.items():
        n = int(np.asarray(sample.get("_n", [0]))[0]) if "_n" in sample else None
        for var in variables:
            x = np.asarray(sample.get(var, []), dtype=float)
            x = x[np.isfinite(x)]
            if n is None:
                n_cells = int(x.size)
            else:
                n_cells = n
            if x.size == 0:
                rows.append(
                    Signature(
                        body=body,
                        lat_band=band,
                        variable=var,
                        median=float("nan"),
                        q1=float("nan"),
                        q3=float("nan"),
                        n_cells=0,
                    )
                )
                continue
            q1, med, q3 = np.percentile(x, [25, 50, 75])
            rows.append(
                Signature(
                    body=body,
                    lat_band=band,
                    variable=var,
                    median=float(med),
                    q1=float(q1),
                    q3=float(q3),
                    n_cells=n_cells,
                )
            )
    return rows


def signatures_for(
    rows: Iterable[Signature], body: str, lat_band: str
) -> dict[str, Signature]:
    return {s.variable: s for s in rows if s.body == body and s.lat_band == lat_band}
