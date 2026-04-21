# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 11:59:39 2026

@author: late_jj
"""

# ============================================================
# core/preprocessing.py
# ============================================================
"""
Module PREPROCESSING

Responsabilités :
- transformations spectrales
- pipeline de prétraitement
- validation des paramètres

Toutes les fonctions ici sont indépendantes de Streamlit UI.
"""

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
from sklearn.preprocessing import normalize


# ============================================================
# SNV
# ============================================================

def snv(X: pd.DataFrame) -> pd.DataFrame:
    """
    Standard Normal Variate (ligne par ligne).

    Corrige les effets multiplicatifs et additifs.

    Parameters
    ----------
    X : DataFrame (n_samples, n_variables)

    Returns
    -------
    DataFrame
    """

    arr = X.to_numpy(dtype=float)

    mean = arr.mean(axis=1, keepdims=True)
    std = arr.std(axis=1, keepdims=True)

    std[std == 0] = 1.0  # éviter division par zéro

    transformed = (arr - mean) / std

    return pd.DataFrame(transformed, index=X.index, columns=X.columns)


# ============================================================
# MSC
# ============================================================

def msc(X: pd.DataFrame) -> pd.DataFrame:
    """
    Multiplicative Scatter Correction.

    Corrige diffusion et offset.

    Returns
    -------
    DataFrame
    """

    arr = X.to_numpy(dtype=float)

    ref = arr.mean(axis=0)

    corrected = np.zeros_like(arr)

    for i in range(arr.shape[0]):
        sample = arr[i]

        slope, intercept = np.polyfit(ref, sample, 1)

        if slope == 0:
            slope = 1

        corrected[i] = (sample - intercept) / slope

    return pd.DataFrame(corrected, index=X.index, columns=X.columns)


# ============================================================
# SAVITZKY-GOLAY
# ============================================================

def savgol_derivative(
    X: pd.DataFrame,
    window_length: int,
    polyorder: int,
    deriv: int
) -> pd.DataFrame:
    """
    Filtre Savitzky-Golay + dérivée.

    Parameters
    ----------
    window_length : doit être impair
    polyorder : ordre du polynôme
    deriv : ordre de dérivée

    Returns
    -------
    DataFrame
    """

    arr = X.to_numpy(dtype=float)

    # validation
    if window_length % 2 == 0:
        window_length += 1

    if window_length <= polyorder:
        raise ValueError("window_length doit être > polyorder")

    if window_length > arr.shape[1]:
        raise ValueError("window_length trop grand")

    transformed = savgol_filter(
        arr,
        window_length=window_length,
        polyorder=polyorder,
        deriv=deriv,
        axis=1,
    )

    return pd.DataFrame(transformed, index=X.index, columns=X.columns)


# ============================================================
# NORMALISATION
# ============================================================

def spectral_normalization(
    X: pd.DataFrame,
    method: str = "l2"
) -> pd.DataFrame:
    """
    Normalisation des spectres.

    method : 'l1', 'l2', 'max'
    """

    arr = X.to_numpy(dtype=float)

    transformed = normalize(arr, norm=method, axis=1)

    return pd.DataFrame(transformed, index=X.index, columns=X.columns)


# ============================================================
# PIPELINE
# ============================================================

def preprocess_pipeline(
    X: pd.DataFrame,
    steps: list,
    params: dict
) -> pd.DataFrame:
    """
    Applique un pipeline de prétraitement.

    Parameters
    ----------
    X : DataFrame
    steps : list of str
        Exemple : ["SNV", "Savitzky-Golay"]
    params : dict

    Returns
    -------
    DataFrame
    """

    X_proc = X.copy()

    for step in steps:

        if step == "SNV":
            X_proc = snv(X_proc)

        elif step == "MSC":
            X_proc = msc(X_proc)

        elif step == "Savitzky-Golay":
            X_proc = savgol_derivative(
                X_proc,
                window_length=params["savgol_window"],
                polyorder=params["savgol_polyorder"],
                deriv=params["savgol_deriv"],
            )

        elif step == "Normalisation":
            X_proc = spectral_normalization(
                X_proc,
                method=params["normalization_method"],
            )

        else:
            raise ValueError(f"Étape inconnue : {step}")

    return X_proc


# ============================================================
# VALIDATION PARAMÈTRES
# ============================================================

def validate_preprocessing_params(params, X):
    """
    Vérifie que les paramètres sont cohérents.
    """

    n_vars = X.shape[1]

    if params["savgol_window"] > n_vars:
        raise ValueError("Fenêtre Savitzky-Golay trop grande")

    if params["savgol_window"] <= params["savgol_polyorder"]:
        raise ValueError("window_length doit être > polyorder")