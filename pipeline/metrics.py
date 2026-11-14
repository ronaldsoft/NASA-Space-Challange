"""
Métricas de validación: AUC, IC por bootstrap y prueba de DeLong pareada.

Sin dependencias distintas de NumPy. Textos y nombres pensados para el
informe en español.
"""

from __future__ import annotations

import math
from typing import Sequence

import numpy as np
from numpy.typing import NDArray


def _finite_binary(y: NDArray, *scores: NDArray) -> tuple[NDArray, ...]:
    y = np.asarray(y).astype(int)
    arrs = [np.asarray(s, dtype=float) for s in scores]
    m = np.isin(y, [0, 1])
    for a in arrs:
        m &= np.isfinite(a)
    return (y[m],) + tuple(a[m] for a in arrs)


def roc_auc(y_true: NDArray, scores: NDArray) -> float:
    """AUC trapezoidal (mismo criterio que pipeline.index.roc_auc)."""
    y, s = _finite_binary(y_true, scores)
    n_pos = int(np.sum(y == 1))
    n_neg = int(np.sum(y == 0))
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    order = np.argsort(-s, kind="mergesort")
    y = y[order]
    tpr = np.cumsum(y) / n_pos
    fpr = np.cumsum(1 - y) / n_neg
    tpr = np.concatenate(([0.0], tpr, [1.0]))
    fpr = np.concatenate(([0.0], fpr, [1.0]))
    return float(np.sum((tpr[1:] + tpr[:-1]) * 0.5 * np.diff(fpr)))


def _psi_matrix(pos: NDArray, neg: NDArray) -> NDArray:
    """psi(x, y) = 1_{x>y} + 0.5_{x=y}, forma (n_pos, n_neg)."""
    return (pos[:, None] > neg[None, :]).astype(float) + 0.5 * (pos[:, None] == neg[None, :])


def _delong_covariance(y: NDArray, score_list: Sequence[NDArray]) -> tuple[NDArray, NDArray]:
    """
    Vector de AUCs y matriz de covarianza de DeLong (k × k) para k scores
    pareados sobre las mismas observaciones.
    """
    y = np.asarray(y).astype(int)
    k = len(score_list)
    pos_idx = y == 1
    neg_idx = y == 0
    n = int(pos_idx.sum())
    m = int(neg_idx.sum())
    if n == 0 or m == 0:
        return np.full(k, np.nan), np.full((k, k), np.nan)

    v10 = np.zeros((k, n))
    v01 = np.zeros((k, m))
    aucs = np.zeros(k)
    for i, s in enumerate(score_list):
        s = np.asarray(s, dtype=float)
        psi = _psi_matrix(s[pos_idx], s[neg_idx])
        v10[i] = psi.mean(axis=1)
        v01[i] = psi.mean(axis=0)
        aucs[i] = psi.mean()

    s10 = np.cov(v10, ddof=1) if n > 1 else np.zeros((k, k))
    s01 = np.cov(v01, ddof=1) if m > 1 else np.zeros((k, k))
    if k == 1:
        s10 = np.array([[float(s10)]])
        s01 = np.array([[float(s01)]])
    cov = s10 / n + s01 / m
    return aucs, cov


def delong_paired(y_true: NDArray, scores_a: NDArray, scores_b: NDArray) -> dict:
    """
    Prueba de DeLong pareada: H0: AUC(a) = AUC(b).

    Devuelve ambos AUC, la diferencia (a − b), el estadístico z, el valor p
    bilateral y la varianza de la diferencia.
    """
    y, a, b = _finite_binary(y_true, scores_a, scores_b)
    aucs, cov = _delong_covariance(y, [a, b])
    diff = float(aucs[0] - aucs[1])
    var = float(cov[0, 0] + cov[1, 1] - 2 * cov[0, 1])
    if not np.isfinite(var) or var <= 0:
        z = float("nan")
        p = float("nan")
    else:
        z = diff / math.sqrt(var)
        p = float(math.erfc(abs(z) / math.sqrt(2.0)))  # 2 * (1-Phi(|z|))
    return {
        "auc_a": float(aucs[0]),
        "auc_b": float(aucs[1]),
        "diferencia": diff,
        "z": z,
        "p_valor": p,
        "varianza_diferencia": var,
    }


def bootstrap_auc_ci(
    y_true: NDArray,
    scores: NDArray,
    n_boot: int = 2000,
    seed: int = 2026,
    alpha: float = 0.05,
) -> dict:
    """IC bootstrap percentil (por defecto 95 %) del AUC."""
    y, s = _finite_binary(y_true, scores)
    auc = roc_auc(y, s)
    rng = np.random.default_rng(seed)
    n = y.size
    boots = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        yi, si = y[idx], s[idx]
        if yi.min() == yi.max():
            continue
        boots.append(roc_auc(yi, si))
    if len(boots) < 50:
        lo = hi = float("nan")
    else:
        lo, hi = np.percentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {
        "auc": float(auc),
        "ic95_inferior": float(lo),
        "ic95_superior": float(hi),
        "n_bootstrap": int(len(boots)),
        "semilla": seed,
    }


def null_abs_lat_auc(y_true: NDArray, latitudes: NDArray) -> dict:
    """
    Modelo nulo: el puntaje es |lat|. Los positivos de este conjunto están
    en latitudes altas, así que este AUC mide cuánto 'predice' solo la latitud.
    """
    y, lat = _finite_binary(y_true, latitudes)
    scores = np.abs(lat)
    ci = bootstrap_auc_ci(y, scores)
    return {"puntaje": "|lat|", **ci}
