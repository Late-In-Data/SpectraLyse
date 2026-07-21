# ============================================================
# tests/test_preprocessing.py
# ============================================================
"""
Tests unitaires pour core/preprocessing.py
"""

import numpy as np
import pandas as pd
import pytest

from core.preprocessing import (
    snv,
    msc,
    savgol_derivative,
    spectral_normalization,
    preprocess_pipeline,
    validate_preprocessing_params,
)


@pytest.fixture
def spectra_df():
    rng = np.random.default_rng(42)
    data = rng.normal(loc=1.0, scale=0.2, size=(10, 20))
    columns = [str(800 + i * 10) for i in range(20)]
    return pd.DataFrame(data, columns=columns)


# ============================================================
# SNV
# ============================================================
def test_snv_centers_and_scales_each_row(spectra_df):
    result = snv(spectra_df)

    row_means = result.to_numpy().mean(axis=1)
    row_stds = result.to_numpy().std(axis=1)

    assert np.allclose(row_means, 0, atol=1e-8)
    assert np.allclose(row_stds, 1, atol=1e-8)
    assert result.shape == spectra_df.shape
    assert list(result.columns) == list(spectra_df.columns)


def test_snv_handles_constant_row_without_division_by_zero():
    df = pd.DataFrame([[1.0, 1.0, 1.0, 1.0]])
    result = snv(df)

    assert not result.isna().any().any()
    assert np.allclose(result.to_numpy(), 0.0)


# ============================================================
# MSC
# ============================================================
def test_msc_preserves_shape(spectra_df):
    result = msc(spectra_df)

    assert result.shape == spectra_df.shape
    assert list(result.columns) == list(spectra_df.columns)
    assert not result.isna().any().any()


# ============================================================
# Savitzky-Golay
# ============================================================
def test_savgol_derivative_output_shape(spectra_df):
    result = savgol_derivative(spectra_df, window_length=5, polyorder=2, deriv=1)

    assert result.shape == spectra_df.shape


def test_savgol_derivative_odd_window_correction(spectra_df):
    # Fenêtre paire -> corrigée automatiquement en impaire
    result = savgol_derivative(spectra_df, window_length=6, polyorder=2, deriv=0)
    assert result.shape == spectra_df.shape


def test_savgol_derivative_raises_if_window_too_small_vs_polyorder(spectra_df):
    with pytest.raises(ValueError):
        savgol_derivative(spectra_df, window_length=3, polyorder=4, deriv=1)


def test_savgol_derivative_raises_if_window_too_large(spectra_df):
    with pytest.raises(ValueError):
        savgol_derivative(spectra_df, window_length=99, polyorder=2, deriv=1)


# ============================================================
# Normalisation
# ============================================================
@pytest.mark.parametrize("method", ["l1", "l2", "max"])
def test_spectral_normalization_methods(spectra_df, method):
    result = spectral_normalization(spectra_df, method=method)
    assert result.shape == spectra_df.shape


def test_spectral_normalization_l2_unit_norm(spectra_df):
    result = spectral_normalization(spectra_df, method="l2")
    norms = np.linalg.norm(result.to_numpy(), axis=1)
    assert np.allclose(norms, 1.0, atol=1e-6)


# ============================================================
# Pipeline
# ============================================================
def test_preprocess_pipeline_chains_steps(spectra_df):
    params = {
        "savgol_window": 5,
        "savgol_polyorder": 2,
        "savgol_deriv": 1,
        "normalization_method": "l2",
    }
    result = preprocess_pipeline(spectra_df, ["SNV", "Savitzky-Golay", "Normalisation"], params)

    assert result.shape == spectra_df.shape
    assert not result.isna().any().any()


def test_preprocess_pipeline_empty_steps_returns_copy(spectra_df):
    result = preprocess_pipeline(spectra_df, [], {})
    pd.testing.assert_frame_equal(result, spectra_df)


def test_preprocess_pipeline_unknown_step_raises(spectra_df):
    with pytest.raises(ValueError):
        preprocess_pipeline(spectra_df, ["INCONNU"], {})


# ============================================================
# Validation des paramètres
# ============================================================
def test_validate_preprocessing_params_ok(spectra_df):
    params = {"savgol_window": 5, "savgol_polyorder": 2}
    # Ne doit pas lever d'exception
    validate_preprocessing_params(params, spectra_df)


def test_validate_preprocessing_params_window_too_large(spectra_df):
    params = {"savgol_window": 99, "savgol_polyorder": 2}
    with pytest.raises(ValueError):
        validate_preprocessing_params(params, spectra_df)


def test_validate_preprocessing_params_window_leq_polyorder(spectra_df):
    params = {"savgol_window": 3, "savgol_polyorder": 4}
    with pytest.raises(ValueError):
        validate_preprocessing_params(params, spectra_df)
