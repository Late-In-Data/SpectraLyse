# ============================================================
# tests/test_reduction.py
# ============================================================
"""
Tests unitaires pour core/reduction.py
"""

import numpy as np
import pandas as pd
import pytest

from core.reduction import validate_X, compute_pca, pca_summary


@pytest.fixture
def spectra_df():
    rng = np.random.default_rng(0)
    data = rng.normal(size=(30, 15))
    columns = [str(800 + i * 10) for i in range(15)]
    return pd.DataFrame(data, columns=columns)


# ============================================================
# validate_X
# ============================================================
def test_validate_X_raises_on_none():
    with pytest.raises(ValueError):
        validate_X(None)


def test_validate_X_raises_on_empty():
    with pytest.raises(ValueError):
        validate_X(pd.DataFrame())


def test_validate_X_raises_on_nan(spectra_df):
    df = spectra_df.copy()
    df.iloc[0, 0] = np.nan
    with pytest.raises(ValueError):
        validate_X(df)


def test_validate_X_raises_on_too_few_samples():
    df = pd.DataFrame({"800": [1.0], "900": [2.0]})
    with pytest.raises(ValueError):
        validate_X(df)


def test_validate_X_passes_on_valid_data(spectra_df):
    # Ne doit pas lever d'exception
    validate_X(spectra_df)


# ============================================================
# compute_pca
# ============================================================
def test_compute_pca_output_shapes(spectra_df):
    scores, loadings, explained, model = compute_pca(spectra_df, n_components=3, scale=True)

    assert scores.shape == (30, 3)
    assert loadings.shape == (15, 3)
    assert list(explained["Composante"]) == ["PC1", "PC2", "PC3"]
    assert scores.index.equals(spectra_df.index)
    assert loadings.index.equals(spectra_df.columns)


def test_compute_pca_variance_cumulative_is_nondecreasing(spectra_df):
    _, _, explained, _ = compute_pca(spectra_df, n_components=5, scale=True)
    cumulative = explained["Variance cumulée (%)"].to_numpy()
    assert np.all(np.diff(cumulative) >= -1e-9)


def test_compute_pca_caps_n_components_to_data_size():
    df = pd.DataFrame({"800": [1.0, 2.0, 3.0], "900": [2.0, 3.0, 1.0]})
    scores, loadings, explained, model = compute_pca(df, n_components=10, scale=True)

    # Ne peut pas dépasser min(n_samples, n_features) = 2
    assert scores.shape[1] == 2


# ============================================================
# pca_summary
# ============================================================
def test_pca_summary_quality_levels():
    explained_good = pd.DataFrame({"Variance expliquée (%)": [50, 30, 10]})
    explained_medium = pd.DataFrame({"Variance expliquée (%)": [30, 25, 10]})
    explained_low = pd.DataFrame({"Variance expliquée (%)": [20, 10, 5]})

    assert pca_summary(explained_good)["quality"] == "Bonne"
    assert pca_summary(explained_medium)["quality"] == "Moyenne"
    assert pca_summary(explained_low)["quality"] == "Faible"


def test_pca_summary_values_rounded():
    explained = pd.DataFrame({"Variance expliquée (%)": [40.123, 20.456, 10.0]})
    summary = pca_summary(explained)

    assert summary["var_2_components"] == round(40.123 + 20.456, 2)
    assert summary["var_3_components"] == round(40.123 + 20.456 + 10.0, 2)
