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

from typing import Optional, Tuple, List

import pandas as pd
import plotly.express as px
import streamlit as st

from core.data import (
    load_data,
    select_columns_ui,
    missing_report,
    clean_data,
)
from components.layout import page_header
from components.cards import kpi_card, info_card


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
    report = missing_report(df)

    total_na = int(df.isna().sum().sum())
    pct_na = (
        (total_na / (df.shape[0] * df.shape[1])) * 100
        if df.shape[0] > 0 and df.shape[1] > 0
        else 0.0
    )
    n_empty_cols = int(df.isna().all().sum())
    n_rows_with_na = int(df.isna().any(axis=1).sum())

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
            )
            fig.update_layout(
                template="plotly_white",
                height=420,
                margin=dict(l=20, r=20, t=50, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune valeur manquante détectée.")

    with right:
        st.dataframe(report, use_container_width=True, height=420)

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
        st.dataframe(df_clean.head(50), use_container_width=True)


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

    if st.session_state.get("raw_df") is None:
        st.info("Veuillez importer un fichier pour commencer.")
        return

    df = st.session_state.raw_df.copy()

    # --------------------------------------------------------
    # Résumé dataset
    # --------------------------------------------------------
    st.markdown("### Vue d’ensemble du dataset")
    render_dataset_summary(df)

    with st.expander("Aperçu des données brutes", expanded=False):
        st.dataframe(df.head(50), use_container_width=True)

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
        if st.button("Valider et figer le dataset", type="primary", use_container_width=True):
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