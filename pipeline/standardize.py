"""
Estandarización con parámetros congelados.

Los parámetros se calculan SOLO sobre el cuerpo de referencia (Marte o
Luna, nunca mezclados, nunca con datos de validación ni de Ecuador) y
después se aplican a la Tierra.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Iterable, Mapping

import numpy as np
from numpy.typing import NDArray


@dataclass
class StdParam:
    """Fila equivalente a la tabla ``std_params``."""

    body_ref: str  # 'moon' | 'mars'
    variable: str
    center: float
    scale: float
    method: str
    frozen_at: str

    def as_dict(self) -> dict:
        return asdict(self)


def fit_std_params(
    values_by_variable: Mapping[str, NDArray],
    body_ref: str,
    method: str = "zscore",
    frozen_at: str | None = None,
    min_scale: float = 1e-8,
) -> list[StdParam]:
    """
    Calcula centro y escala por variable sobre la referencia.

    Parameters
    ----------
    values_by_variable :
        Arreglos 1D de valores válidos de la referencia (Marte o Luna).
        No incluir celdas terrestres.
    body_ref :
        ``moon`` o ``mars``.
    method :
        ``zscore`` (media, desviación típica) o ``robust`` (mediana, IQR/1.349).
    frozen_at :
        Marca temporal ISO-8601; si falta, se usa el instante actual (UTC).
    """
    if body_ref not in {"moon", "mars"}:
        raise ValueError("body_ref debe ser 'moon' o 'mars' (nunca earth, nunca mezclados)")
    if method not in {"zscore", "robust"}:
        raise ValueError("method debe ser 'zscore' o 'robust'")
    if frozen_at is None:
        frozen_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    params: list[StdParam] = []
    for variable, raw in values_by_variable.items():
        x = np.asarray(raw, dtype=float)
        x = x[np.isfinite(x)]
        if x.size < 2:
            raise ValueError(f"no hay suficientes valores finitos para {variable}")
        if method == "zscore":
            center = float(np.mean(x))
            scale = float(np.std(x, ddof=1))
        else:
            q1, q3 = np.percentile(x, [25, 75])
            center = float(np.median(x))
            scale = float((q3 - q1) / 1.349)  # escala comparable a una desviación típica
        # Si la referencia no varía, una escala minúscula haría z explosivas.
        # Se toma 1 unidad de la variable como piso de la escala degenerada.
        if not np.isfinite(scale) or scale < min_scale:
            scale = max(1.0, min_scale)
        else:
            scale = max(scale, min_scale)
        params.append(
            StdParam(
                body_ref=body_ref,
                variable=variable,
                center=center,
                scale=scale,
                method=method,
                frozen_at=frozen_at,
            )
        )
    return params


def params_to_dict(params: Iterable[StdParam]) -> dict[str, StdParam]:
    return {p.variable: p for p in params}


def apply_std_params(
    values_by_variable: Mapping[str, NDArray],
    params: Iterable[StdParam],
) -> dict[str, NDArray]:
    """Aplica parámetros ya congelados. No recalcular centro ni escala."""
    lookup = params_to_dict(params)
    out: dict[str, NDArray] = {}
    for name, raw in values_by_variable.items():
        if name not in lookup:
            raise KeyError(f"no hay parámetros congelados para {name}")
        p = lookup[name]
        x = np.asarray(raw, dtype=float)
        out[name] = (x - p.center) / p.scale
    return out
