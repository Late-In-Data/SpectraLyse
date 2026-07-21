# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 12:00:05 2026

@author: late_jj
"""

# ============================================================
# core/reduction.py
# ============================================================
"""
Module REDUCTION

Responsabilités :
- PCA
- préparation des données

Aucune dépendance Streamlit.
"""

import numpy as np
import pandas as pd

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler


# ============================================================
# VALIDATION DES DONNÉES
# ============================================================

def validate_X(X: pd.DataFrame):
    """
    Vérifie que X est exploitable.
    """

    if X is None or X.empty:
        raise ValueError("X est vide.")

    if not isinstance(X, pd.DataFrame):
        raise ValueError("X doit être un DataFrame.")

    if X.isna().any().any():
        raise ValueError("Des valeurs manquantes subsistent dans X.")

    if X.shape[0] < 2 or X.shape[1] < 2:
        raise ValueError("Pas assez de données pour une réduction de dimension.")


# ============================================================
# PCA
# ============================================================

def compute_pca(
    X: pd.DataFrame,
    n_components: int = 5,
    scale: bool = True
):
    """
    Calcul PCA complet.

    Returns
    -------
    scores_df : DataFrame
    loadings_df : DataFrame
    explained_df : DataFrame
    model : PCA object
    """

    validate_X(X)

    arr = X.to_numpy(dtype=float)

    if scale:
        scaler = StandardScaler()
        arr = scaler.fit_transform(arr)

    n_components = min(n_components, arr.shape[0], arr.shape[1])

    pca = PCA(n_components=n_components)
    scores = pca.fit_transform(arr)
    loadings = pca.components_.T

    # DataFrames
    scores_df = pd.DataFrame(
        scores,
        columns=[f"PC{i+1}" for i in range(scores.shape[1])],
        index=X.index
    )

    loadings_df = pd.DataFrame(
        loadings,
        columns=[f"PC{i+1}" for i in range(loadings.shape[1])],
        index=X.columns
    )

    explained_df = pd.DataFrame({
        "Composante": [f"PC{i+1}" for i in range(len(pca.explained_variance_ratio_))],
        "Variance expliquée (%)": pca.explained_variance_ratio_ * 100,
        "Variance cumulée (%)": np.cumsum(pca.explained_variance_ratio_) * 100,
    })

    return scores_df, loadings_df, explained_df, pca


# ============================================================
# INTERPRÉTATION PCA (BONUS PRO)
# ============================================================

def pca_summary(explained_df):
    """
    Génère un résumé simple de la PCA.
    """

    var_2 = explained_df["Variance expliquée (%)"].iloc[:2].sum()
    var_3 = explained_df["Variance expliquée (%)"].iloc[:3].sum()

    summary = {
        "var_2_components": round(var_2, 2),
        "var_3_components": round(var_3, 2),
        "quality": (
            "Bonne" if var_2 > 70 else
            "Moyenne" if var_2 > 50 else
            "Faible"
        )
    }

    return summary
