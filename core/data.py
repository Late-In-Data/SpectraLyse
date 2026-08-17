# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 11:58:50 2026

@author: late_jj
"""

# ============================================================
# core/data.py
# ============================================================
"""
Module DATA

Responsabilités :
- chargement des données
- détection des colonnes spectrales
- tri des colonnes
- diagnostic des valeurs manquantes

Aucune dépendance Streamlit hormis st.cache_data (mécanisme de
cache, pas de rendu). Les widgets d'import (sélection de colonnes,
nettoyage interactif) vivent dans ui/import_page.py, seul
consommateur de ces fonctions.
"""

from typing import Dict, List, Tuple

import pandas as pd
import streamlit as st


# ============================================================
# Chargement
# ============================================================
@st.cache_data(show_spinner=False)
def load_data(file) -> pd.DataFrame:
    """
    Charge un fichier CSV ou Excel.

    Parameters
    ----------
    file : UploadedFile
        Fichier Streamlit chargé par l'utilisateur.

    Returns
    -------
    pd.DataFrame
    """
    file_name = file.name.lower()

    if file_name.endswith(".csv"):
        file.seek(0)
        try:
            df = pd.read_csv(file)
        except Exception:
            df = None

        # pd.read_csv ne lève pas toujours d'exception sur un séparateur
        # incorrect : un CSV en ';' lu avec le séparateur ',' par défaut
        # est parfois accepté silencieusement comme une seule colonne.
        # On retente avec ';' si le résultat n'a qu'une seule colonne
        # alors que la première ligne en contient plusieurs.
        if df is None or (df.shape[1] <= 1 and ";" in str(df.columns[0] if len(df.columns) else "")):
            file.seek(0)
            df = pd.read_csv(file, sep=";")

        return df

    if file_name.endswith(".xlsx") or file_name.endswith(".xls"):
        file.seek(0)
        return pd.read_excel(file)

    raise ValueError("Format non supporté. Utilisez CSV, XLSX ou XLS.")


# ============================================================
# Détection colonnes spectrales
# ============================================================
def detect_spectral_columns(df: pd.DataFrame) -> Tuple[List[str], Dict[str, float]]:
    """
    Détecte les colonnes dont le nom peut être converti en float.

    Exemple :
    - '800.5' -> OK
    - '1450'  -> OK
    - 'DATE'  -> non

    Returns
    -------
    spectral_cols : list[str]
        Colonnes détectées comme longueurs d'onde.
    value_map : dict[str, float]
        Mapping colonne -> valeur numérique.
    """
    spectral_cols = []
    value_map = {}

    for col in df.columns:
        try:
            val = float(str(col).strip().replace(",", "."))
            spectral_cols.append(col)
            value_map[col] = val
        except Exception:
            continue

    spectral_cols = sorted(spectral_cols, key=lambda c: value_map[c])
    return spectral_cols, value_map


# ============================================================
# Tri des colonnes
# ============================================================
def sort_columns_preserve_logic(
    selected_cols: List[str],
    all_cols: List[str],
    spectral_map: Dict[str, float],
) -> List[str]:
    """
    Trie les colonnes :
    - d'abord les colonnes spectrales numériques dans l'ordre réel
    - puis les autres par ordre alphabétique
    """
    selected_cols = [c for c in selected_cols if c in all_cols]

    def sort_key(col):
        if col in spectral_map:
            return (0, spectral_map[col])
        return (1, str(col))

    return sorted(list(dict.fromkeys(selected_cols)), key=sort_key)


# ============================================================
# Diagnostic des valeurs manquantes
# ============================================================
def missing_report(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule un tableau de synthèse des valeurs manquantes.

    Returns
    -------
    pd.DataFrame
        Colonnes :
        - Missing
        - %
    """
    if df.empty:
        return pd.DataFrame(columns=["Missing", "%"])

    miss = df.isna().sum()
    pct = (miss / len(df)) * 100

    report = pd.DataFrame({
        "Missing": miss,
        "%": pct,
    }).sort_values("%", ascending=False)

    return report


def quality_overview(df: pd.DataFrame) -> Dict[str, object]:
    """
    Diagnostic de qualité consolidé (valeurs manquantes, colonnes vides,
    lignes impactées, doublons), utilisé à la fois par la page Import et
    par le rapport HTML pour éviter que les deux calculs ne divergent.

    Returns
    -------
    dict avec les clés :
        report          : DataFrame (sortie de missing_report)
        total_na        : int
        pct_na          : float (non arrondi, % de cellules manquantes)
        n_empty_cols    : int
        n_rows_with_na  : int
        n_duplicates    : int
    """
    report = missing_report(df)
    total_na = int(df.isna().sum().sum())
    n_cells = df.shape[0] * df.shape[1]
    pct_na = (total_na / n_cells) * 100 if n_cells > 0 else 0.0

    return {
        "report": report,
        "total_na": total_na,
        "pct_na": pct_na,
        "n_empty_cols": int(df.isna().all().sum()),
        "n_rows_with_na": int(df.isna().any(axis=1).sum()),
        "n_duplicates": int(df.duplicated().sum()),
    }
