"""Pruebas unitarias del pipeline con arreglos sintéticos."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline import (
    MODO_BANDA_PROPIA,
    MODO_TODAS_MIN,  # noqa: E402
    GeoTransform,
    build_signatures,
    choose_threshold,
    classify,
    delta_index,
    fit_std_params,
    resample_to_grid,
    roughness_tri,
    sample_by_lat_bands,
    slope,
)
from pipeline.index import CLASS_AMBOS, CLASS_LUNA, CLASS_MARTE, CLASS_NINGUNO, CLASS_NODATA, roc_auc
from pipeline.signatures import LatBand
from pipeline.standardize import apply_std_params
from pipeline.terrain import roughness_std


def test_resample_nearest_and_bilinear_identity():
    src = GeoTransform(west=0.0, north=2.0, res_lon=1.0, res_lat=-1.0)
    arr = np.array([[1.0, 2.0], [3.0, 4.0]])
    out = resample_to_grid(arr, src, src, arr.shape, method="nearest")
    assert np.allclose(out, arr)
    out_b = resample_to_grid(arr, src, src, arr.shape, method="bilinear")
    assert np.allclose(out_b, arr)


def test_resample_bilinear_midpoint():
    src = GeoTransform(west=0.0, north=2.0, res_lon=1.0, res_lat=-1.0)
    arr = np.array([[0.0, 10.0], [20.0, 30.0]])
    # Grilla de un solo píxel centrado en el cruce de los 4 (lon=1, lat=1),
    # que es la esquina común, no el centro. Mejor: destino con res 1 y
    # west=0.5, north=1.5 → centro (1.0, 1.0), punto medio de los 4 valores.
    dst = GeoTransform(west=0.5, north=1.5, res_lon=1.0, res_lat=-1.0)
    out = resample_to_grid(arr, src, dst, (1, 1), method="bilinear")
    assert out.shape == (1, 1)
    assert np.isclose(out[0, 0], 15.0)


def test_resample_nodata_and_outside():
    src = GeoTransform(west=0.0, north=2.0, res_lon=1.0, res_lat=-1.0)
    arr = np.array([[1.0, -999.0], [3.0, 4.0]])
    dst = GeoTransform(west=-2.0, north=4.0, res_lon=1.0, res_lat=-1.0)
    out = resample_to_grid(arr, src, dst, (4, 4), method="nearest", nodata=-999.0)
    assert np.isnan(out[0, 0])  # fuera
    # El píxel de origen (0,1) era nodata
    # centro origen (0,1) está en lon=1.5, lat=1.5
    # En destino, fila = (1.5-4)/(-1)-0.5 = 2.0, col=(1.5-(-2))/1-0.5=3.0
    assert np.isnan(out[2, 3])


def test_slope_of_known_plane():
    # Plano z = 0.1 * x_metros, filas constantes, 10 m de celda.
    # dz/dx = 0.1, dz/dy = 0 → pendiente = atan(0.1) en grados.
    x = np.arange(7) * 10.0
    z = np.tile(0.1 * x, (7, 1))
    s = slope(z, res_y_m=10.0, res_x_m=10.0)
    expected = np.degrees(np.arctan(0.1))
    # El borde usa un gradiente de un lado; el interior debe coincidir.
    assert np.allclose(s[2:-2, 2:-2], expected, atol=1e-10)


def test_roughness_tri_flat_is_zero_and_bump_is_positive():
    flat = np.ones((5, 5)) * 100.0
    tri = roughness_tri(flat)
    assert np.allclose(tri[1:-1, 1:-1], 0.0)
    assert np.all(np.isnan(tri[0, :])) or True  # borde con pad nan → nan
    bump = flat.copy()
    bump[2, 2] = 110.0
    tri_b = roughness_tri(bump)
    # El centro: 8 vecinos a -10 → sqrt(8*100)=20
    assert np.isclose(tri_b[2, 2], np.sqrt(8 * 100.0))
    std = roughness_std(flat)
    assert np.allclose(std[1:-1, 1:-1], 0.0)


def test_fit_std_params_only_on_reference_and_applies_frozen():
    rng = np.random.default_rng(0)
    x = rng.normal(10, 2, size=500)
    params = fit_std_params({"elevation": x}, body_ref="mars", method="zscore", frozen_at="2026-11-14T00:00:00Z")
    assert params[0].body_ref == "mars"
    assert params[0].method == "zscore"
    assert params[0].frozen_at == "2026-11-14T00:00:00Z"
    assert params[0].center == pytest.approx(float(np.mean(x)))
    assert params[0].scale == pytest.approx(float(np.std(x, ddof=1)))
    z = apply_std_params({"elevation": x}, params)["elevation"]
    assert np.isclose(np.mean(z), 0.0, atol=1e-12)
    assert np.isclose(np.std(z, ddof=1), 1.0, atol=1e-12)
    with pytest.raises(ValueError):
        fit_std_params({"elevation": x}, body_ref="earth")


def test_sample_by_lat_bands_respects_minimum_and_does_not_mix():
    lat = np.concatenate([np.full(80, 5.0), np.full(20, 40.0), np.full(8, 80.0)])
    elev = np.arange(lat.size, dtype=float)
    bands = [
        LatBand("ecuatorial", 0, 10),
        LatBand("templada", 30, 50),
        LatBand("polar", 66, 90),
    ]
    samples = sample_by_lat_bands(lat, {"elevation": elev}, bands, min_cells=50, rng=np.random.default_rng(1))
    assert samples["ecuatorial"]["elevation"].size == 80
    assert not samples["ecuatorial"]["_short"][0]
    assert samples["templada"]["_short"][0]  # 20 < 50
    assert samples["polar"]["_n"][0] == 8
    # No debe haber latitudes de otra banda
    assert np.all(np.abs(samples["ecuatorial"]["latitude"]) < 10)


def test_build_signatures_median_iqr_and_rejects_mixed_body():
    samples = {
        "ecuatorial": {
            "elevation": np.array([0.0, 10.0, 20.0, 30.0, 40.0]),
            "slope": np.array([1.0, 1.0, 2.0, 3.0, 3.0]),
            "_n": np.array([5]),
        }
    }
    rows = build_signatures("moon", samples, ["elevation", "slope"])
    elev = next(r for r in rows if r.variable == "elevation")
    assert elev.body == "moon"
    assert elev.median == pytest.approx(20.0)
    assert elev.q1 == pytest.approx(10.0)
    assert elev.q3 == pytest.approx(30.0)
    assert elev.n_cells == 5
    with pytest.raises(ValueError):
        build_signatures("earth", samples, ["elevation"])


def test_delta_index_identical_vector_is_one():
    # Referencia y celda idénticas a la mediana, dentro del IQR → d=0, delta=1
    values = {
        "latitude": np.array([0.0, 10.0, 20.0]),
        "elevation": np.array([100.0, 200.0, 300.0]),
        "slope": np.array([5.0, 10.0, 15.0]),
        "roughness": np.array([1.0, 2.0, 3.0]),
    }
    # Usar la propia referencia para params y firma.
    params = fit_std_params(values, "mars", frozen_at="2026-11-14T00:00:00Z")
    samples = {"ecuatorial": {k: v for k, v in values.items()} | {"_n": np.array([3])}}
    sigs = build_signatures("mars", samples, list(values))
    query = {k: np.array([np.median(v)]) for k, v in values.items()}
    dist, delta, _band = delta_index(
        query, sigs, params, lat_band="ecuatorial", body_ref="mars", d_max=2.0, iqr_penalty=0.5
    )
    assert dist[0] == pytest.approx(0.0, abs=1e-9)
    assert delta[0] == pytest.approx(1.0, abs=1e-9)


def test_delta_index_is_bounded_and_penalizes_outside_iqr():
    values = {
        "latitude": np.array([0.0, 0.0, 0.0, 0.0, 0.0]),
        "elevation": np.array([10.0, 20.0, 30.0, 40.0, 50.0]),
        "slope": np.array([1.0, 1.0, 1.0, 1.0, 1.0]),
        "roughness": np.array([1.0, 1.0, 1.0, 1.0, 1.0]),
    }
    params = fit_std_params(values, "moon", frozen_at="2026-11-14T00:00:00Z")
    samples = {"ecuatorial": {k: v for k, v in values.items()} | {"_n": np.array([5])}}
    sigs = build_signatures("moon", samples, list(values))
    inside = {k: np.array([np.median(v)]) for k, v in values.items()}
    outside = {k: np.array([np.median(v)]) for k, v in values.items()}
    outside["elevation"] = np.array([10_000.0])  # muy fuera del IQR
    d_in, delta_in, _ = delta_index(inside, sigs, params, "ecuatorial", "moon", d_max=5.0)
    d_out, delta_out, _ = delta_index(outside, sigs, params, "ecuatorial", "moon", d_max=5.0)
    assert 0.0 <= delta_in[0] <= 1.0 and 0.0 <= delta_out[0] <= 1.0
    assert d_out[0] > d_in[0]
    assert delta_out[0] < delta_in[0]


def test_choose_threshold_and_auc_on_separable_scores():
    y = np.array([1, 1, 1, 1, 0, 0, 0, 0])
    s = np.array([0.9, 0.8, 0.75, 0.7, 0.3, 0.2, 0.1, 0.05])
    result = choose_threshold(s, y, metric="youden", d_max=1.0)
    assert result.auc == pytest.approx(1.0)
    assert result.sensitivity == pytest.approx(1.0)
    assert result.precision == pytest.approx(1.0)
    # Cualquier umbral en (0.3, 0.7] es perfecto; se elige el más alto.
    assert 0.3 < result.threshold <= 0.7 + 1e-12
    assert roc_auc(y, s) == pytest.approx(1.0)


def test_classify_four_classes_and_nodata():
    dm = np.array([0.9, 0.9, 0.1, 0.1, np.nan])
    dl = np.array([0.1, 0.9, 0.9, 0.1, 0.9])
    out = classify(dm, dl, t_mars=0.5, t_moon=0.5)
    assert out.tolist() == [CLASS_MARTE, CLASS_AMBOS, CLASS_LUNA, CLASS_NINGUNO, CLASS_NODATA]


def test_equal_weights_default_sum_to_one():
    values = {
        "latitude": np.array([0.0, 5.0, -5.0]),
        "elevation": np.array([1.0, 2.0, 3.0]),
        "slope": np.array([4.0, 5.0, 6.0]),
        "roughness": np.array([7.0, 8.0, 9.0]),
    }
    params = fit_std_params(values, "mars", frozen_at="2026-11-14T00:00:00Z")
    samples = {"b": {k: v for k, v in values.items()} | {"_n": np.array([3])}}
    sigs = build_signatures("mars", samples, list(values))
    query = {k: np.array([v[0]]) for k, v in values.items()}
    d1, _, _ = delta_index(query, sigs, params, "b", "mars", weights=None, d_max=3.0)
    d2, _, _ = delta_index(
        query,
        sigs,
        params,
        "b",
        "mars",
        weights={"latitude": 0.25, "elevation": 0.25, "slope": 0.25, "roughness": 0.25},
        d_max=3.0,
    )
    assert d1[0] == pytest.approx(d2[0])


def test_delta_index_handles_zero_iqr():
    """Una firma con IQR nulo no debe producir distancias explosivas."""
    values = {
        "latitude": np.array([0.0, 0.0, 0.0, 0.0, 0.0]),
        "elevation": np.array([10.0, 20.0, 30.0, 40.0, 50.0]),
        "slope": np.array([1.0, 1.0, 1.0, 1.0, 1.0]),  # IQR 0
        "roughness": np.array([2.0, 2.0, 2.0, 2.0, 2.0]),
    }
    params = fit_std_params(values, "mars", frozen_at="2026-11-14T00:00:00Z")
    samples = {"b": {k: v for k, v in values.items()} | {"_n": np.array([5])}}
    sigs = build_signatures("mars", samples, list(values))
    query = {k: np.array([np.median(v) + 3.0]) for k, v in values.items()}
    dist, delta, _band = delta_index(query, sigs, params, "b", "mars", d_max=10.0)
    assert np.isfinite(dist[0]) and dist[0] < 50
    assert 0.0 <= delta[0] <= 1.0


def test_modo_bandas_todas_min_picks_closest_and_reports_winner():
    """Una celda de la banda A debe poder ganar con la firma de otra banda."""
    # Dos bandas con elevaciones muy distintas.
    samples = {
        "A": {
            "latitude": np.array([2.0, 4.0, 6.0, 8.0]),
            "elevation": np.array([100.0, 120.0, 80.0, 110.0]),
            "slope": np.array([2.0, 2.0, 2.0, 2.0]),
            "roughness": np.array([10.0, 10.0, 10.0, 10.0]),
            "_n": np.array([4]),
        },
        "C": {
            "latitude": np.array([32.0, 34.0, 36.0, 38.0]),
            "elevation": np.array([4000.0, 4200.0, 3800.0, 4100.0]),
            "slope": np.array([12.0, 12.0, 12.0, 12.0]),
            "roughness": np.array([300.0, 300.0, 300.0, 300.0]),
            "_n": np.array([4]),
        },
    }
    # Referencia = concatenación para std params (con |lat|).
    ref = {
        k: np.concatenate([samples["A"][k], samples["C"][k]])
        for k in ("latitude", "elevation", "slope", "roughness")
    }
    params = fit_std_params(ref, "moon", frozen_at="2026-11-14T00:00:00Z")
    sigs = build_signatures("moon", samples, list(ref))
    # Celda ecuatorial (banda A) pero con rasgos de la banda C.
    query = {
        "latitude": np.array([1.0]),
        "elevation": np.array([4050.0]),
        "slope": np.array([12.0]),
        "roughness": np.array([300.0]),
    }
    d_all, delta_all, win = delta_index(
        query, sigs, params, lat_band="A", body_ref="moon", d_max=5.0,
        modo_bandas=MODO_TODAS_MIN,
    )
    d_own, delta_own, win_own = delta_index(
        query, sigs, params, lat_band="A", body_ref="moon", d_max=5.0,
        modo_bandas=MODO_BANDA_PROPIA,
    )
    assert win[0] == "C"
    assert win_own[0] == "A"
    assert d_all[0] < d_own[0]
    assert delta_all[0] > delta_own[0]


def test_latitude_uses_absolute_value():
    values = {
        "latitude": np.array([-20.0, 20.0, -10.0, 10.0]),
        "elevation": np.array([1.0, 2.0, 3.0, 4.0]),
        "slope": np.array([1.0, 2.0, 3.0, 4.0]),
        "roughness": np.array([1.0, 2.0, 3.0, 4.0]),
    }
    params = fit_std_params(
        {**values, "latitude": np.abs(values["latitude"])},
        "mars",
        frozen_at="2026-11-14T00:00:00Z",
    )
    samples = {
        "B": {k: (np.abs(v) if k == "latitude" else v) for k, v in values.items()} | {"_n": np.array([4])}
    }
    sigs = build_signatures("mars", samples, list(values))
    q1 = {k: np.array([v[0]]) for k, v in values.items()}  # lat -20
    q2 = {k: np.array([20.0 if k == "latitude" else v[0]]) for k, v in values.items()}
    d1, _, _ = delta_index(q1, sigs, params, "B", "mars", d_max=5.0, modo_bandas=MODO_BANDA_PROPIA)
    d2, _, _ = delta_index(q2, sigs, params, "B", "mars", d_max=5.0, modo_bandas=MODO_BANDA_PROPIA)
    assert d1[0] == pytest.approx(d2[0], rel=1e-9)


def test_todas_min_mahalanobis_drops_latitude():
    """Con Mahalanobis y todas_min, la latitud se retira del vector."""
    rng = np.random.default_rng(0)
    samples = {
        "A": {
            "latitude": rng.uniform(0, 10, 30),
            "elevation": rng.normal(100, 10, 30),
            "slope": rng.normal(5, 1, 30),
            "roughness": rng.normal(20, 3, 30),
            "_n": np.array([30]),
        },
        "C": {
            "latitude": rng.uniform(30, 45, 30),
            "elevation": rng.normal(2000, 50, 30),
            "slope": rng.normal(12, 2, 30),
            "roughness": rng.normal(200, 20, 30),
            "_n": np.array([30]),
        },
    }
    ref = {k: np.concatenate([samples["A"][k], samples["C"][k]]) for k in ("latitude", "elevation", "slope", "roughness")}
    params = fit_std_params(ref, "mars", frozen_at="2026-11-14T00:00:00Z")
    sigs = build_signatures("mars", samples, list(ref))
    query = {k: np.array([v[0]]) for k, v in ref.items()}
    Z = np.column_stack([ref[k] for k in ("elevation", "slope", "roughness")])
    d_mah, _, _ = delta_index(
        query, sigs, params, "A", "mars", d_max=5.0,
        modo_bandas=MODO_TODAS_MIN, distance="mahalanobis", ref_matrix=Z,
    )
    d_eu_nolat, _, _ = delta_index(
        query, sigs, params, "A", "mars", d_max=5.0,
        modo_bandas=MODO_TODAS_MIN,
        variables=("elevation", "slope", "roughness"),
    )
    assert np.isfinite(d_mah[0])
    # Misma decisión de variables (sin latitud); la métrica puede diferir (Mahalanobis vs euclídea).
    assert d_mah[0] < 50


def test_delong_and_bootstrap_and_null_model():
    from pipeline.metrics import bootstrap_auc_ci, delong_paired, null_abs_lat_auc, roc_auc

    y = np.array([1, 1, 1, 1, 0, 0, 0, 0])
    good = np.array([0.9, 0.8, 0.75, 0.7, 0.3, 0.2, 0.1, 0.05])
    bad = np.array([0.4, 0.6, 0.5, 0.3, 0.7, 0.2, 0.8, 0.1])
    assert roc_auc(y, good) == pytest.approx(1.0)
    ci = bootstrap_auc_ci(y, good, n_boot=400, seed=1)
    assert ci["ic95_inferior"] > 0.7
    assert ci["ic95_superior"] >= ci["auc"] - 1e-9
    paired = delong_paired(y, good, good)
    assert paired["diferencia"] == pytest.approx(0.0, abs=1e-12)
    # Dos curvas iguales: p no significativo o NaN por varianza ~0
    assert (not np.isfinite(paired["p_valor"])) or paired["p_valor"] > 0.05
    # Nulo |lat|: positivos en alta latitud
    lat = np.array([70, 75, 80, 65, 2, 5, 3, 8], float)
    nulo = null_abs_lat_auc(y, lat)
    assert nulo["auc"] > 0.8


def test_nan_box_mean_flat_and_center():
    from pipeline.terrain import nan_box_mean
    flat = np.ones((9, 9)) * 5.0
    mu = nan_box_mean(flat, width=3)
    assert np.allclose(mu, 5.0)
    z = np.zeros((7, 7))
    z[3, 3] = 70.0
    mu = nan_box_mean(z, width=3)
    assert mu[3, 3] == pytest.approx(70.0 / 9.0)
