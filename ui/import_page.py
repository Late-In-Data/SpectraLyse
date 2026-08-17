# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 12:00:44 2026

@author: late_jj
"""

# ============================================================
# ui/import_page.py
# ============================================================
"""
Page IMPORT & PRÉPARATION - version pro

Objectif :
- charger les données
- sélectionner intelligemment X / metadata
- diagnostiquer les valeurs manquantes
- nettoyer les données
- valider un dataset stable pour l’analyse

Cette page est le point d’entrée principal du workflow.
"""

import re
from typing import Tuple, List

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from core.data import (
    load_data,
    detect_spectral_columns,
    sort_columns_preserve_logic,
    missing_report,
    quality_overview,
)
from components.layout import page_header
from components.cards import kpi_card, info_card

DEMO_DATASET_PATH = "data/demo_cereals_nirs.csv"


# ============================================================
# Helpers
# ============================================================
def safe_preview_columns(cols: List[str], n: int = 25) -> List[str]:
    """
    Retourne un aperçu limité des colonnes pour affichage UI.
    """
    if not cols:
        return []
    return cols[:n]


def render_dataset_summary(df: pd.DataFrame) -> None:
    """
    Affiche un résumé KPI du dataset brut.
    """
    n_rows, n_cols = df.shape
    n_numeric = int(df.select_dtypes(include="number").shape[1])
    n_missing = int(df.isna().sum().sum())

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        kpi_card("Lignes", n_rows)
    with c2:
        kpi_card("Colonnes", n_cols)
    with c3:
        kpi_card("Colonnes numériques", n_numeric)
    with c4:
        kpi_card("Valeurs manquantes", n_missing)


def render_missing_diagnostics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Affiche le diagnostic des valeurs manquantes.
    """
    overview = quality_overview(df)
    report = overview["report"]
    total_na = overview["total_na"]
    pct_na = overview["pct_na"]
    n_empty_cols = overview["n_empty_cols"]
    n_rows_with_na = overview["n_rows_with_na"]

    st.markdown("### Diagnostic des valeurs manquantes")

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_card("NA totaux", total_na)
    with k2:
        kpi_card("% NA global", f"{pct_na:.2f}%")
    with k3:
        kpi_card("Colonnes vides", n_empty_cols)
    with k4:
        kpi_card("Lignes impactées", n_rows_with_na)

    left, right = st.columns([1.4, 1.0], gap="large")

    with left:
        if not report.empty:
            fig = px.bar(
                report.reset_index().rename(columns={"index": "Colonne"}),
                x="%",
                y="Colonne",
                orientation="h",
                title="Pourcentage de valeurs manquantes par colonne",
                color_discrete_sequence=["#0F766E"],
            )
            fig.update_layout(
                template="plotly_white",
                height=420,
                margin=dict(l=20, r=20, t=50, b=20),
            )
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Aucune valeur manquante détectée.")

    with right:
        st.dataframe(report, width="stretch", height=420)

    return report


def render_selection_summary(x_cols: List[str], meta_cols: List[str]) -> None:
    """
    Résumé visuel des colonnes X et metadata.
    """
    st.markdown("### Résumé de la sélection")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            """
            <div class="card">
                <strong>Colonnes spectrales (X)</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if x_cols:
            st.write(safe_preview_columns(x_cols, 30))
            if len(x_cols) > 30:
                st.caption(f"Aperçu limité aux 30 premières sur {len(x_cols)} colonnes.")
        else:
            st.warning("Aucune colonne X sélectionnée.")

    with c2:
        st.markdown(
            """
            <div class="card">
                <strong>Métadonnées</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if meta_cols:
            st.write(safe_preview_columns(meta_cols, 30))
            if len(meta_cols) > 30:
                st.caption(f"Aperçu limité aux 30 premières sur {len(meta_cols)} colonnes.")
        else:
            st.info("Aucune métadonnée sélectionnée.")


def render_cleaned_summary(
    df_clean: pd.DataFrame,
    x_cols_clean: List[str],
    meta_cols_clean: List[str],
) -> None:
    """
    Résumé du dataset nettoyé.
    """
    st.markdown("### Résultat après nettoyage")

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Lignes", df_clean.shape[0])
    with c2:
        kpi_card("Colonnes X", len(x_cols_clean))
    with c3:
        kpi_card("Métadonnées", len(meta_cols_clean))

    with st.expander("Aperçu des données nettoyées", expanded=False):
        st.dataframe(df_clean.head(50), width="stretch")


# ============================================================
# Sélection colonnes (widgets Streamlit)
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
        st.caption(
            "Mode Numérique : colonnes numériques dont le nom est interprétable comme une "
            "longueur d’onde. Les colonnes numériques non spectrales (ex. valeurs de "
            "référence chimique comme la protéine ou l’humidité) sont exclues automatiquement, "
            "car les mélanger aux spectres fausserait l’échelle et le tracé."
        )
        x_cols = [c for c in numeric_cols if c in spectral_map]

        excluded_numeric = [c for c in numeric_cols if c not in spectral_map]
        if excluded_numeric:
            st.caption(
                f"{len(excluded_numeric)} colonne(s) numérique(s) non spectrale(s) exclue(s) : "
                + ", ".join(str(c) for c in excluded_numeric[:10])
                + ("…" if len(excluded_numeric) > 10 else "")
            )

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
    x_cols = sort_columns_preserve_logic(x_cols, all_cols, spectral_map)

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
# Nettoyage des données (widgets Streamlit)
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


# ============================================================
# Page principale
# ============================================================
def render_import_page() -> None:
    """
    Rendu principal de la page Import.
    """
    page_header("Import & Préparation", "Chargez, diagnostiquez et nettoyez vos données")

    # --------------------------------------------------------
    # Bloc introduction
    # --------------------------------------------------------
    intro_left, intro_right = st.columns([2.3, 1.0], gap="large")

    with intro_left:
        st.markdown(
            """
            <div class="card">
                <h4>Workflow recommandé</h4>
                <p>
                1. Importer un fichier CSV ou Excel<br>
                2. Définir les colonnes spectrales X et les métadonnées<br>
                3. Diagnostiquer les valeurs manquantes<br>
                4. Nettoyer les données<br>
                5. Valider le dataset pour le reste de l’application
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with intro_right:
        info_card(
            "Conseil",
            "Vous pouvez sélectionner directement toutes les colonnes numériques, ou utiliser les modes Plage, Regex et Manuel pour affiner la sélection."
            )
        
    # --------------------------------------------------------
    # Upload
    # --------------------------------------------------------
    st.markdown("### Import du fichier")

    upload_col, demo_col = st.columns([2.4, 1.0], gap="large")

    with upload_col:
        uploaded_file = st.file_uploader(
            "Importer un fichier CSV ou Excel",
            type=["csv", "xlsx", "xls"],
            help="Formats supportés : CSV, XLSX, XLS",
        )

        if uploaded_file is not None:
            try:
                df = load_data(uploaded_file)
                st.session_state.raw_df = df.copy()
                st.session_state.file_name = uploaded_file.name
                st.success(f"Fichier chargé : {uploaded_file.name}")
            except Exception as e:
                st.error(f"Erreur lors du chargement : {e}")
                return

    with demo_col:
        st.markdown("**Pas de données sous la main ?**")
        if st.button(
            "Charger le jeu de données de démonstration",
            width="stretch",
        ):
            try:
                df = pd.read_csv(DEMO_DATASET_PATH)
                st.session_state.raw_df = df.copy()
                st.session_state.file_name = "demo_cereals_nirs.csv"
                st.success("Jeu de données de démonstration chargé.")
            except Exception as e:
                st.error(f"Erreur lors du chargement de la démo : {e}")

        st.caption(
            "Spectres NIR réels d’orge, de maïs et de blé "
            "(projet sensAIfood, CC BY 4.0 — voir data/SOURCE.md)."
        )

    if st.session_state.get("raw_df") is None:
        st.info("Veuillez importer un fichier ou charger le jeu de données de démonstration pour commencer.")
        return

    df = st.session_state.raw_df.copy()

    # --------------------------------------------------------
    # Résumé dataset
    # --------------------------------------------------------
    st.markdown("### Vue d’ensemble du dataset")
    render_dataset_summary(df)

    with st.expander("Aperçu des données brutes", expanded=False):
        st.dataframe(df.head(50), width="stretch")

    # --------------------------------------------------------
    # Sélection colonnes
    # --------------------------------------------------------
    st.markdown("### Sélection des colonnes")

    x_cols, meta_cols = select_columns_ui(df)

    # On met à jour provisoirement la session
    st.session_state.x_columns = x_cols
    st.session_state.meta_columns = meta_cols

    render_selection_summary(x_cols, meta_cols)

    # --------------------------------------------------------
    # Diagnostic NA
    # --------------------------------------------------------
    report = render_missing_diagnostics(df)

    # --------------------------------------------------------
    # Nettoyage
    # --------------------------------------------------------
    st.markdown("### Nettoyage des données")

    clean_left, clean_right = st.columns([2.0, 1.0], gap="large")

    with clean_left:
        df_clean, x_cols_clean, meta_cols_clean = clean_data(df, x_cols, meta_cols)

    with clean_right:
        info_card(
            "Nettoyage",
            "Choisissez une stratégie cohérente avec votre objectif analytique : ne supprimez pas trop agressivement sans vérifier l’impact sur les échantillons et les métadonnées."
        )

    render_cleaned_summary(df_clean, x_cols_clean, meta_cols_clean)

    # --------------------------------------------------------
    # Validation finale
    # --------------------------------------------------------
    st.markdown("### Validation du dataset")

    val_left, val_right = st.columns([1.4, 1.0], gap="large")

    with val_left:
        if st.button("Valider et figer le dataset", type="primary", width="stretch"):
            if not x_cols_clean:
                st.error("Aucune colonne spectrale valide n’a été sélectionnée.")
                return

            # On enregistre le dataset nettoyé
            st.session_state.cleaned_df = df_clean.copy()

            # On invalide tout ce qui dépend d’un ancien dataset
            st.session_state.processed_df = None
            st.session_state.reduction_results = {}

            # Colonnes mises à jour
            st.session_state.x_columns = x_cols_clean
            st.session_state.meta_columns = meta_cols_clean

            st.success("Dataset validé et prêt pour l’analyse.")

    with val_right:
        info_card(
            "Après validation",
            "Les pages Spectres, Prétraitements et PCA utiliseront ce dataset validé. Tout ancien prétraitement ou résultat PCA sera réinitialisé."
        )

    # --------------------------------------------------------
    # État final
    # --------------------------------------------------------
    if st.session_state.get("cleaned_df") is not None:
        st.markdown("### État actuel")
        st.success("Un dataset validé est actuellement disponible dans la session.")
        st.write(f"**Fichier actif :** {st.session_state.get('file_name', 'N/A')}")
        st.write(
            f"**Dimensions validées :** "
            f"{st.session_state.cleaned_df.shape[0]} lignes × {st.session_state.cleaned_df.shape[1]} colonnes"
        )