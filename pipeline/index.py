"""
Índice ANALOG/delta, umbral de validación y clasificación.

Distancia euclídea (o Mahalanobis si la covarianza es estable) en el
espacio estandarizado, con penalización de valores fuera del IQR de la
firma de la banda. Delta es una función decreciente acotada en [0, 1].

El índice se calcula dos veces: contra Marte y contra la Luna.
El umbral se fija en validación y no se reajusta en Ecuador.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence

import numpy as np
from numpy.typing import NDArray

from .signatures import Signature, signatures_for
from .standardize import StdParam, apply_std_params, params_to_dict

# Clases de homología (valores del ráster de clases).
CLASS_NODATA = -1
CLASS_NINGUNO = 0
CLASS_MARTE = 1
CLASS_LUNA = 2
CLASS_AMBOS = 3

CLASS_NAMES = {
    CLASS_NODATA: "nodata",
    CLASS_NINGUNO: "ninguno",
    CLASS_MARTE: "marte",
    CLASS_LUNA: "luna",
    CLASS_AMBOS: "ambos",
}

DEFAULT_VARIABLES = ("latitude", "elevation", "slope", "roughness")

# Comparación de firmas por banda. `todas_min` es el valor por defecto
# mientras Ronald confirma el §5 (Ecuador cae en la banda A, sin positivos).
MODO_TODAS_MIN = "todas_min"
MODO_BANDA_PROPIA = "banda_propia"
MODOS_BANDAS = (MODO_TODAS_MIN, MODO_BANDA_PROPIA)


def with_abs_latitude(values_by_variable: Mapping[str, NDArray]) -> dict[str, NDArray]:
    """La variable latitude entra al índice como |lat| (grados)."""
    out = {k: np.asarray(v, dtype=float) for k, v in values_by_variable.items()}
    if "latitude" in out:
        out["latitude"] = np.abs(out["latitude"])
    return out


def _stack(
    values: Mapping[str, NDArray], variables: Sequence[str]
) -> NDArray:
    cols = [np.asarray(values[v], dtype=float) for v in variables]
    return np.column_stack(cols) if cols else np.zeros((0, 0))


def _covariance_stable(X: NDArray, max_cond: float = 1e8) -> bool:
    if X.ndim != 2 or X.shape[0] < X.shape[1] + 5:
        return False
    finite = np.all(np.isfinite(X), axis=1)
    Y = X[finite]
    if Y.shape[0] < X.shape[1] + 5:
        return False
    cov = np.cov(Y, rowvar=False)
    if cov.ndim != 2:
        return False
    try:
        cond = np.linalg.cond(cov)
    except np.linalg.LinAlgError:
        return False
    return bool(np.isfinite(cond) and cond < max_cond)


def _mahalanobis(diff: NDArray, cov: NDArray) -> NDArray:
    inv = np.linalg.pinv(cov)
    # diff: (n, p)
    return np.sqrt(np.sum(diff @ inv * diff, axis=1))


def _distance_matrix(
    Z: NDArray,
    zvars: dict[str, tuple[float, float, float]],
    variables: Sequence[str],
    w: Mapping[str, float],
    iqr_penalty: float,
    use_mah: bool,
    cov: NDArray | None,
) -> NDArray:
    """Distancia de cada fila de Z a una firma ya estandarizada."""
    med = np.array([zvars[v][0] for v in variables])
    q1 = np.array([zvars[v][1] for v in variables])
    q3 = np.array([zvars[v][2] for v in variables])
    diff = Z - med[None, :]
    below = Z < q1[None, :]
    above = Z > q3[None, :]
    iqr = q3 - q1
    extra = np.zeros_like(diff)
    ok = iqr > 1e-6
    if np.any(ok):
        scale = np.where(ok, iqr, 1.0)
        extra_below = (q1[None, :] - Z) / scale[None, :]
        extra_above = (Z - q3[None, :]) / scale[None, :]
        extra = np.where(below & ok[None, :], extra_below, extra)
        extra = np.where(above & ok[None, :], extra_above, extra)
        extra = np.where(ok[None, :], extra, 0.0)
    penalized = diff + np.sign(diff + 1e-15) * (iqr_penalty * extra)
    ww = np.array([w[v] for v in variables])
    if use_mah and cov is not None:
        return _mahalanobis(penalized * np.sqrt(ww)[None, :], cov)
    return np.sqrt(np.sum(ww[None, :] * penalized**2, axis=1))


def delta_index(
    values_by_variable: Mapping[str, NDArray],
    signatures: Iterable[Signature],
    std_params: Iterable[StdParam],
    lat_band: str | Sequence[str] | NDArray,
    body_ref: str,
    weights: Mapping[str, float] | None = None,
    variables: Sequence[str] = DEFAULT_VARIABLES,
    iqr_penalty: float = 0.5,
    d_max: float = 1.0,
    distance: str = "euclidean",
    ref_matrix: NDArray | None = None,
    modo_bandas: str = MODO_TODAS_MIN,
    use_abs_lat: bool = True,
) -> tuple[NDArray, NDArray, NDArray]:
    """
    Distancia, delta y banda ganadora para cada celda.

    Parameters
    ----------
    modo_bandas :
        ``todas_min`` — compara contra las firmas de todas las bandas y
        se queda con la distancia mínima (y la banda ganadora). Es el
        valor por defecto, pendiente de confirmación del §5.
        ``banda_propia`` — solo la firma de la banda de |lat| de la celda.
    use_abs_lat :
        Si True y ``latitude`` está en el vector, se usa |lat|. Los
        parámetros y firmas deben haberse calculado también con |lat|.
    lat_band :
        Banda propia de cada celda (obligatoria en ``banda_propia``;
        en ``todas_min`` solo se usa como desempate documental).

    Returns
    -------
    distance, delta, banda_ganadora
    """
    if body_ref not in {"moon", "mars"}:
        raise ValueError("body_ref debe ser 'moon' o 'mars'")
    if modo_bandas not in MODOS_BANDAS:
        raise ValueError(f"modo_bandas debe ser uno de {MODOS_BANDAS}")

    variables = tuple(variables)
    # todas_min solo es válida con distancia euclídea si la latitud está en el
    # vector. Con Mahalanobis por banda la latitud bloquea en vez de penalizar:
    # se retira automáticamente (Expertos, §6.10).
    if modo_bandas == MODO_TODAS_MIN and distance == "mahalanobis" and "latitude" in variables:
        variables = tuple(v for v in variables if v != "latitude")

    values = dict(values_by_variable)
    if use_abs_lat:
        values = with_abs_latitude(values)

    n = len(np.asarray(next(iter(values.values()))))
    if weights is None:
        w = {v: 1.0 / len(variables) for v in variables}
    else:
        s = sum(weights[v] for v in variables)
        if s <= 0:
            raise ValueError("la suma de pesos debe ser positiva")
        w = {v: weights[v] / s for v in variables}

    # Solo se aplican los parámetros de las variables pedidas (p. ej. sensibilidad sin latitud).
    params_used = [p for p in std_params if p.variable in variables]
    z = apply_std_params({k: values[k] for k in variables}, params_used)
    Z = _stack(z, variables)
    lookup = params_to_dict(params_used)

    if np.isscalar(lat_band) or isinstance(lat_band, str):
        own_bands = np.full(n, str(lat_band))
    else:
        own_bands = np.asarray(lat_band).astype(str)

    sig_rows = [s for s in signatures if s.body == body_ref]
    band_names = sorted({s.lat_band for s in sig_rows})
    sig_z: dict[str, dict[str, tuple[float, float, float]]] = {}
    for bname in band_names:
        raw_sig = signatures_for(sig_rows, body_ref, bname)
        if any(v not in raw_sig or not np.isfinite(raw_sig[v].median) for v in variables):
            continue
        sig_z[bname] = {}
        for v in variables:
            p = lookup[v]
            s = raw_sig[v]
            sig_z[bname][v] = (
                (s.median - p.center) / p.scale,
                (s.q1 - p.center) / p.scale,
                (s.q3 - p.center) / p.scale,
            )

    use_mah = distance == "mahalanobis" and ref_matrix is not None and _covariance_stable(ref_matrix)
    cov = None
    if use_mah:
        finite = np.all(np.isfinite(ref_matrix), axis=1)
        cov = np.cov(ref_matrix[finite], rowvar=False)

    dist = np.full(n, np.nan, dtype=float)
    winner = np.full(n, "", dtype=object)

    if modo_bandas == MODO_BANDA_PROPIA:
        for bname, zvars in sig_z.items():
            mask = own_bands == bname
            if not np.any(mask):
                continue
            d = _distance_matrix(Z[mask], zvars, variables, w, iqr_penalty, use_mah, cov)
            dist[mask] = d
            winner[mask] = bname
    else:
        # todas_min: distancia a cada banda, se conserva el mínimo.
        for bname, zvars in sig_z.items():
            d = _distance_matrix(Z, zvars, variables, w, iqr_penalty, use_mah, cov)
            better = np.isnan(dist) | (d < dist)
            dist = np.where(better, d, dist)
            winner = np.where(better, bname, winner)

    d_max_v = float(d_max) if d_max and d_max > 0 else 1.0
    delta = 1.0 - np.minimum(dist / d_max_v, 1.0)
    return dist, delta, winner



@dataclass
class ThresholdResult:
    threshold: float
    sensitivity: float
    precision: float
    specificity: float
    auc: float
    agreement: float
    metric: str
    d_max: float
    n_pos: int
    n_neg: int
    curve: list[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        d = {
            "threshold": self.threshold,
            "sensitivity": self.sensitivity,
            "precision": self.precision,
            "specificity": self.specificity,
            "auc": self.auc,
            "agreement": self.agreement,
            "metric": self.metric,
            "d_max": self.d_max,
            "n_pos": self.n_pos,
            "n_neg": self.n_neg,
        }
        return d


def roc_auc(y_true: NDArray, scores: NDArray) -> float:
    """AUC trapezoidal para una etiqueta binaria y un índice continuo."""
    y = np.asarray(y_true).astype(int)
    s = np.asarray(scores, dtype=float)
    m = np.isfinite(s) & np.isin(y, [0, 1])
    y, s = y[m], s[m]
    n_pos = int(np.sum(y == 1))
    n_neg = int(np.sum(y == 0))
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    order = np.argsort(-s)
    y = y[order]
    tpr = np.cumsum(y) / n_pos
    fpr = np.cumsum(1 - y) / n_neg
    tpr = np.concatenate(([0.0], tpr, [1.0]))
    fpr = np.concatenate(([0.0], fpr, [1.0]))
    return float(np.sum((tpr[1:] + tpr[:-1]) * 0.5 * np.diff(fpr)))


def choose_threshold(
    delta: NDArray,
    y_true: NDArray,
    metric: str = "youden",
    d_max: float | None = None,
) -> ThresholdResult:
    """
    Elige el umbral que maximiza el acuerdo con la validación.

    ``y_true`` es binario (1 = análogo de ese cuerpo, 0 = no).
    ``metric``: ``youden`` (sensibilidad + especificidad − 1),
    ``agreement`` (exactitud) o ``f1``.
    """
    y = np.asarray(y_true).astype(int)
    s = np.asarray(delta, dtype=float)
    m = np.isfinite(s) & np.isin(y, [0, 1])
    y, s = y[m], s[m]
    n_pos = int(np.sum(y == 1))
    n_neg = int(np.sum(y == 0))
    auc = roc_auc(y, s)

    # Candidatos: valores únicos de delta (más extremos 0 y 1).
    candidates = np.unique(s)
    if candidates.size == 0:
        raise ValueError("no hay deltas finitos para fijar el umbral")

    curve = []
    best_key = -np.inf
    best = None
    for t in candidates:
        pred = s >= t
        tp = int(np.sum(pred & (y == 1)))
        fp = int(np.sum(pred & (y == 0)))
        tn = int(np.sum(~pred & (y == 0)))
        fn = int(np.sum(~pred & (y == 1)))
        sens = tp / n_pos if n_pos else 0.0
        spec = tn / n_neg if n_neg else 0.0
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        agr = (tp + tn) / (n_pos + n_neg) if (n_pos + n_neg) else 0.0
        f1 = (2 * prec * sens / (prec + sens)) if (prec + sens) else 0.0
        youden = sens + spec - 1.0
        row = {
            "threshold": float(t),
            "sensitivity": sens,
            "precision": prec,
            "specificity": spec,
            "agreement": agr,
            "f1": f1,
            "youden": youden,
        }
        curve.append(row)
        key = {"youden": youden, "agreement": agr, "f1": f1}[metric]
        # En empate, umbral más alto (menos falsos positivos).
        if key > best_key or (key == best_key and (best is None or t > best["threshold"])):
            best_key = key
            best = row

    assert best is not None
    return ThresholdResult(
        threshold=float(best["threshold"]),
        sensitivity=float(best["sensitivity"]),
        precision=float(best["precision"]),
        specificity=float(best["specificity"]),
        auc=float(auc),
        agreement=float(best["agreement"]),
        metric=metric,
        d_max=float(d_max) if d_max is not None else float("nan"),
        n_pos=n_pos,
        n_neg=n_neg,
        curve=curve,
    )


def per_class_metrics(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    labels: Sequence[str] = ("marte", "luna", "ambos", "ninguno"),
) -> dict[str, dict[str, float]]:
    """Precisión y sensibilidad por clase de homología."""
    yt = np.asarray(y_true)
    yp = np.asarray(y_pred)
    out: dict[str, dict[str, float]] = {}
    for lab in labels:
        tp = int(np.sum((yp == lab) & (yt == lab)))
        fp = int(np.sum((yp == lab) & (yt != lab)))
        fn = int(np.sum((yp != lab) & (yt == lab)))
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        sens = tp / (tp + fn) if (tp + fn) else 0.0
        out[lab] = {
            "precision": prec,
            "sensitivity": sens,
            "support": int(np.sum(yt == lab)),
        }
    return out


def classify(
    delta_mars: NDArray,
    delta_moon: NDArray,
    t_mars: float,
    t_moon: float,
    valid_mask: NDArray | None = None,
) -> NDArray:
    """
    Mapa de clases: marte, luna, ambos, ninguno; nodata si la máscara es falsa.

    Una celda puede ser análoga de uno, de ambos o de ninguno. Marte y la
    Luna no se promedian en una sola firma.
    """
    dm = np.asarray(delta_mars, dtype=float)
    dl = np.asarray(delta_moon, dtype=float)
    if valid_mask is None:
        valid = np.isfinite(dm) & np.isfinite(dl)
    else:
        valid = np.asarray(valid_mask, dtype=bool) & np.isfinite(dm) & np.isfinite(dl)

    out = np.full(dm.shape, CLASS_NODATA, dtype=int)
    mars = valid & (dm >= t_mars)
    moon = valid & (dl >= t_moon)
    out[valid] = CLASS_NINGUNO
    out[mars & ~moon] = CLASS_MARTE
    out[moon & ~mars] = CLASS_LUNA
    out[mars & moon] = CLASS_AMBOS
    return out
