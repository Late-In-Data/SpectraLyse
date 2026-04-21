# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 11:58:50 2026

@author: late_jj
"""

# ============================================================
# core/data.py
# ============================================================
"""
Module DATA - version pro

Responsabilités :
- chargement des données
- détection des colonnes spectrales
- sélection intelligente des colonnes X / metadata
- diagnostic des valeurs manquantes
- nettoyage interactif et robuste

Ce module contient de la logique métier + des widgets Streamlit
spécifiquement liés au workflow d'import et de préparation.
"""

import io
import re
from typing import Dict, List, Tuple

import numpy as np
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
            return pd.read_csv(file)
        except Exception:
            file.seek(0)
            return pd.read_csv(file, sep=";")

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
# Utilitaires UI colonnes
# ============================================================
def _safe_preview(cols: List[str], n: int = 25) -> List[str]:
    """
    Retourne les n premières colonnes pour aperçu.
    """
    return cols[:n] if cols else []


def _sort_columns_preserve_logic(
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
# Sélection colonnes
# ============================================================
def select_columns_ui(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    """
    Interface Streamlit de sélection des colonnes X et metadata.

    Modes disponibles :
    - Auto : toutes les colonnes numériques
    - Plage : détection colonnes spectrales convertibles en float
    - Regex : sélection via regex
    - Manuel : sélection libre

    Returns
    -------
    x_cols : list[str]
    meta_cols : list[str]
    """
    all_cols = df.columns.tolist()
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    spectral_cols, spectral_map = detect_spectral_columns(df)

    previous_x = st.session_state.get("x_columns", [])
    previous_meta = st.session_state.get("meta_columns", [])

    mode = st.radio(
        "Mode de sélection",
        ["Numérique", "Plage", "Regex", "Manuel"],
        horizontal=True,
    )

    x_cols: List[str] = []

    # --------------------------------------------------------
    # Mode Numérique
    # --------------------------------------------------------
    if mode == "Numérique":
        st.caption("Mode Numérique : toutes les colonnes numériques sont proposées comme X.")
        x_cols = numeric_cols.copy()
    
        with st.expander("Voir / ajuster les colonnes numériques sélectionnées", expanded=True):
            x_cols = st.multiselect(
                "Colonnes X numériques",
                options=all_cols,
                default=[c for c in x_cols if c in all_cols],
                key="numeric_x_cols",
            )

    # --------------------------------------------------------
    # Mode Plage
    # --------------------------------------------------------
    elif mode == "Plage":
        st.caption(
            "Mode Plage : sélection des colonnes dont le nom est interprétable comme une longueur d’onde."
        )

        if spectral_cols:
            values = list(spectral_map.values())

            c1, c2 = st.columns(2)
            with c1:
                wl_min = st.number_input(
                    "Longueur d’onde min",
                    value=float(min(values)),
                    key="wl_min",
                )
            with c2:
                wl_max = st.number_input(
                    "Longueur d’onde max",
                    value=float(max(values)),
                    key="wl_max",
                )

            x_cols = [
                c for c in spectral_cols
                if wl_min <= spectral_map[c] <= wl_max
            ]

            st.info(f"{len(x_cols)} colonne(s) sélectionnée(s) dans la plage.")

            with st.expander("Voir / ajuster les colonnes détectées", expanded=True):
                x_cols = st.multiselect(
                    "Colonnes X détectées par plage",
                    options=spectral_cols,
                    default=x_cols,
                    key="range_x_cols",
                )
        else:
            st.warning("Aucune colonne spectrale détectée automatiquement.")
            x_cols = st.multiselect(
                "Colonnes X",
                options=all_cols,
                default=[c for c in previous_x if c in all_cols],
                key="range_fallback_x_cols",
            )

    # --------------------------------------------------------
    # Mode Regex
    # --------------------------------------------------------
    elif mode == "Regex":
        st.caption(
            r"Exemple utile pour les longueurs d’onde : ^\d+([.,]\d+)?$"
        )

        pattern = st.text_input(
            "Regex de sélection",
            value=r"^\d+([.,]\d+)?$",
            help="Exemple : ^\\d+([.,]\\d+)?$ sélectionne 800.7, 1450, 2200.5 mais pas DATE ou PROTEINES.",
            key="regex_select_pattern",
        )

        try:
            x_cols = [c for c in all_cols if re.search(pattern, str(c))]
            st.info(f"{len(x_cols)} colonne(s) trouvée(s) par la regex.")
        except re.error as e:
            st.error(f"Regex invalide : {e}")
            x_cols = []

        with st.expander("Voir / ajuster les colonnes trouvées", expanded=True):
            x_cols = st.multiselect(
                "Colonnes X trouvées par regex",
                options=all_cols,
                default=x_cols,
                key="regex_x_cols",
            )

    # --------------------------------------------------------
    # Mode Manuel
    # --------------------------------------------------------
    else:
        x_cols = st.multiselect(
            "Colonnes X",
            options=all_cols,
            default=[c for c in previous_x if c in all_cols],
            key="manual_x_cols",
        )

    # --------------------------------------------------------
    # Exclusion regex
    # --------------------------------------------------------
    st.markdown("#### Exclusion rapide")

    exclude_pattern = st.text_input(
        "Regex d’exclusion (optionnel)",
        value="",
        help="Exemple : DATE|PC|EAU|PROTEINES",
        key="regex_exclude_pattern",
    )

    if exclude_pattern:
        try:
            before = len(x_cols)
            x_cols = [c for c in x_cols if not re.search(exclude_pattern, str(c))]
            removed = before - len(x_cols)
            if removed > 0:
                st.info(f"{removed} colonne(s) exclue(s) par la regex d’exclusion.")
        except re.error as e:
            st.error(f"Regex d’exclusion invalide : {e}")

    # Tri final
    x_cols = _sort_columns_preserve_logic(x_cols, all_cols, spectral_map)

    # --------------------------------------------------------
    # Définition metadata
    # --------------------------------------------------------
    remaining_cols = [c for c in all_cols if c not in x_cols]

    st.markdown("#### Définition des métadonnées")

    meta_mode = st.radio(
        "Mode pour les métadonnées",
        ["Automatique", "Manuel"],
        horizontal=True,
        key="meta_mode",
    )

    if meta_mode == "Automatique":
        meta_cols = remaining_cols
    else:
        meta_cols = st.multiselect(
            "Colonnes metadata",
            options=remaining_cols,
            default=[c for c in previous_meta if c in remaining_cols],
            key="manual_meta_cols",
        )

    meta_cols = [c for c in remaining_cols if c in meta_cols or meta_mode == "Automatique"]

    # --------------------------------------------------------
    # Résumé rapide
    # --------------------------------------------------------
    st.success(f"{len(x_cols)} colonne(s) X | {len(meta_cols)} métadonnée(s)")
    return x_cols, meta_cols


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


# ============================================================
# Nettoyage des données
# ============================================================
def clean_data(
    df: pd.DataFrame,
    x_cols: List[str],
    meta_cols: List[str],
) -> Tuple[pd.DataFrame, List[str], List[str]]:
    """
    Nettoyage interactif du dataset.

    Fonctionnalités :
    - suppression manuelle de colonnes
    - suppression colonnes entièrement vides
    - suppression colonnes au-dessus d’un seuil de NA
    - suppression lignes avec NA selon plusieurs stratégies

    Returns
    -------
    df_clean : pd.DataFrame
    x_cols_clean : list[str]
    meta_cols_clean : list[str]
    """
    df_clean = df.copy()

    st.markdown("#### Paramètres de nettoyage")
    # --------------------------------------------------------
    # Colonnes entièrement vides
    # --------------------------------------------------------
    drop_empty_cols = st.checkbox(
        "Supprimer automatiquement les colonnes entièrement vides",
        value=True,
        key="drop_empty_cols",
    )

    if drop_empty_cols and len(df_clean) > 0:
        empty_cols = df_clean.columns[df_clean.isna().all()].tolist()
        if empty_cols:
            df_clean = df_clean.drop(columns=empty_cols, errors="ignore")
            st.info(f"{len(empty_cols)} colonne(s) entièrement vide(s) supprimée(s).")

    # Mise à jour des colonnes après suppressions
    available_cols = df_clean.columns.tolist()
    x_cols = [c for c in x_cols if c in available_cols]
    meta_cols = [c for c in meta_cols if c in available_cols and c not in x_cols]

    # --------------------------------------------------------
    # Stratégie NA
    # --------------------------------------------------------
    st.markdown("#### Gestion des valeurs manquantes restantes")

    strategy = st.radio(
        "Choisissez une stratégie",
        [
            "Ne rien faire",
            "Supprimer les lignes avec au moins un NA dans X",
            "Supprimer les lignes avec au moins un NA dans tout le tableau",
            "Supprimer les lignes avec au moins un NA dans des colonnes choisies",
            "Supprimer les lignes avec au moins un NA dans des métadonnées choisies",
            "Supprimer les lignes entièrement vides sur des colonnes choisies",
            "Supprimer les colonnes au-dessus d’un seuil de NA",
        ],
        key="na_strategy",
    )

    # --------------------------------------------------------
    # Colonnes > seuil de NA
    # --------------------------------------------------------
    if strategy == "Supprimer les colonnes au-dessus d’un seuil de NA":
        threshold = st.slider(
            "Seuil maximal de NA (%)",
            min_value=0,
            max_value=100,
            value=50,
            key="na_threshold",
        )

        report = missing_report(df_clean)
        cols_threshold = report.index[report["%"] > threshold].tolist()

        if cols_threshold:
            df_clean = df_clean.drop(columns=cols_threshold, errors="ignore")
            st.info(f"{len(cols_threshold)} colonne(s) supprimée(s) car > {threshold}% de NA.")
        else:
            st.success("Aucune colonne ne dépasse le seuil choisi.")

    # --------------------------------------------------------
    # Lignes avec NA dans X
    # --------------------------------------------------------
    elif strategy == "Supprimer les lignes avec au moins un NA dans X":
        if x_cols:
            before = len(df_clean)
            df_clean = df_clean.dropna(subset=x_cols)
            st.info(f"{before - len(df_clean)} ligne(s) supprimée(s) à cause de NA dans X.")
        else:
            st.warning("Aucune colonne X disponible pour cette opération.")

    # --------------------------------------------------------
    # Lignes avec NA dans tout le tableau
    # --------------------------------------------------------
    elif strategy == "Supprimer les lignes avec au moins un NA dans tout le tableau":
        before = len(df_clean)
        df_clean = df_clean.dropna()
        st.info(f"{before - len(df_clean)} ligne(s) supprimée(s) à cause de NA dans tout le tableau.")

    # --------------------------------------------------------
    # Lignes avec NA dans colonnes choisies
    # --------------------------------------------------------
    elif strategy == "Supprimer les lignes avec au moins un NA dans des colonnes choisies":
        selected_cols = st.multiselect(
            "Colonnes à utiliser pour supprimer les lignes contenant des NA",
            options=df_clean.columns.tolist(),
            default=x_cols[: min(5, len(x_cols))] if x_cols else [],
            key="na_selected_cols",
        )

        if selected_cols:
            before = len(df_clean)
            df_clean = df_clean.dropna(subset=selected_cols)
            st.info(f"{before - len(df_clean)} ligne(s) supprimée(s) sur les colonnes choisies.")
        else:
            st.warning("Sélectionnez au moins une colonne.")

    # --------------------------------------------------------
    # Lignes avec NA dans métadonnées choisies
    # --------------------------------------------------------
    elif strategy == "Supprimer les lignes avec au moins un NA dans des métadonnées choisies":
        if not meta_cols:
            st.warning("Aucune métadonnée disponible pour cette opération.")
        else:
            selected_meta = st.multiselect(
                "Métadonnées à utiliser pour supprimer les lignes contenant des NA",
                options=meta_cols,
                default=meta_cols[: min(5, len(meta_cols))],
                key="na_selected_meta",
            )

            if selected_meta:
                before = len(df_clean)
                df_clean = df_clean.dropna(subset=selected_meta)
                st.info(f"{before - len(df_clean)} ligne(s) supprimée(s) sur les métadonnées choisies.")
            else:
                st.warning("Sélectionnez au moins une métadonnée.")

    # --------------------------------------------------------
    # Lignes entièrement vides sur un sous-ensemble
    # --------------------------------------------------------
    elif strategy == "Supprimer les lignes entièrement vides sur des colonnes choisies":
        selected_subset = st.multiselect(
            "Colonnes à vérifier",
            options=df_clean.columns.tolist(),
            default=meta_cols[: min(5, len(meta_cols))] if meta_cols else [],
            key="na_empty_subset",
        )

        if selected_subset:
            mask_all_missing = df_clean[selected_subset].isna().all(axis=1)
            removed = int(mask_all_missing.sum())
            df_clean = df_clean.loc[~mask_all_missing].copy()
            st.info(f"{removed} ligne(s) supprimée(s) car entièrement vides sur le sous-ensemble choisi.")
        else:
            st.warning("Sélectionnez au moins une colonne.")

    # --------------------------------------------------------
    # Mise à jour finale des colonnes
    # --------------------------------------------------------
    final_cols = df_clean.columns.tolist()
    x_cols_clean = [c for c in x_cols if c in final_cols]
    meta_cols_clean = [c for c in meta_cols if c in final_cols and c not in x_cols_clean]

    st.caption(
        f"Après nettoyage : {df_clean.shape[0]} lignes × {df_clean.shape[1]} colonnes | "
        f"{len(x_cols_clean)} colonne(s) X | {len(meta_cols_clean)} métadonnée(s)"
    )

    return df_clean, x_cols_clean, meta_cols_clean