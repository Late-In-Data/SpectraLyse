# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 12:02:39 2026

@author: late_jj
"""

# ============================================================
# ui/preprocessing_page.py
# ============================================================
"""
Page PRÉTRAITEMENTS - version pro

Responsabilités :
- construire un pipeline de prétraitement
- régler les paramètres de chaque étape
- comparer spectres avant / après
- résumer le pipeline
- appliquer les transformations à tout le dataset

Prétraitements disponibles :
- SNV
- MSC
- Savitzky-Golay
- Normalisation
"""

from typing import Optional, Tuple, List, Dict

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

from core.preprocessing import (
    preprocess_pipeline,
    validate_preprocessing_params,
)
from components.layout import page_header
from components.cards import plot_card
from components.plotting import plot_spectra_figure

# ============================================================
# Données actives
# ============================================================
def get_active_dataset() -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Retourne X et metadata du dataset actif.

    Priorité :
    1. processed_df si présent
    2. cleaned_df sinon

    Les colonnes supprimées sont filtrées pour éviter les erreurs.
    """
    if st.session_state.get("processed_df") is not None:
        df = st.session_state.processed_df.copy()
    elif st.session_state.get("cleaned_df") is not None:
        df = st.session_state.cleaned_df.copy()
    else:
        return None, None

    available_cols = df.columns.tolist()

    x_cols = [c for c in st.session_state.get("x_columns", []) if c in available_cols]
    meta_cols = [
        c for c in st.session_state.get("meta_columns", [])
        if c in available_cols and c not in x_cols
    ]

    st.session_state.x_columns = x_cols
    st.session_state.meta_columns = meta_cols

    if not x_cols:
        return None, None

    X = df[x_cols].copy()
    X = X.apply(pd.to_numeric, errors="coerce")

    meta = df[meta_cols].copy() if meta_cols else pd.DataFrame(index=df.index)
    return X, meta

# ============================================================
# UI pipeline
# ============================================================
def render_pipeline_builder() -> List[str]:
    """
    Panneau de sélection du pipeline.
    L'ordre du multiselect correspond à l'ordre d'application.
    """
    available_steps = ["SNV", "MSC", "Savitzky-Golay", "Normalisation"]

    st.markdown("### Pipeline de prétraitement")
    st.caption("Sélectionne les étapes dans l’ordre souhaité.")

    steps = st.multiselect(
        "Étapes",
        options=available_steps,
        default=st.session_state.get("preprocess_pipeline", []),
    )

    st.session_state.preprocess_pipeline = steps
    return steps


def render_parameters_panel(X: pd.DataFrame) -> Dict:
    """
    Panneau des paramètres du pipeline.
    """
    st.markdown("### Paramètres")

    params = st.session_state.get("preprocess_params", {}).copy()

    # valeurs par défaut de sécurité
    params.setdefault("savgol_window", 11)
    params.setdefault("savgol_polyorder", 2)
    params.setdefault("savgol_deriv", 1)
    params.setdefault("normalization_method", "l2")

    if "Savitzky-Golay" in st.session_state.get("preprocess_pipeline", []):
        max_window = min(51, X.shape[1] if X.shape[1] % 2 == 1 else X.shape[1] - 1)
        max_window = max(max_window, 3)

        current_window = int(params["savgol_window"])
        if current_window > max_window:
            current_window = max_window
        if current_window % 2 == 0:
            current_window = max(3, current_window - 1)

        params["savgol_window"] = st.slider(
            "Fenêtre Savitzky-Golay",
            min_value=3,
            max_value=max_window,
            value=current_window,
            step=2,
        )

        params["savgol_polyorder"] = st.slider(
            "Ordre polynomial",
            min_value=1,
            max_value=5,
            value=int(params["savgol_polyorder"]),
        )

        params["savgol_deriv"] = st.selectbox(
            "Ordre de dérivée",
            options=[0, 1, 2],
            index=[0, 1, 2].index(int(params["savgol_deriv"])),
        )

    if "Normalisation" in st.session_state.get("preprocess_pipeline", []):
        params["normalization_method"] = st.selectbox(
            "Type de normalisation",
            options=["l1", "l2", "max"],
            index=["l1", "l2", "max"].index(params["normalization_method"]),
        )

    st.session_state.preprocess_params = params
    return params


def build_pipeline_summary(steps: List[str], params: Dict) -> List[str]:
    """
    Construit un résumé lisible du pipeline.
    """
    summary = []

    for step in steps:
        if step == "SNV":
            summary.append("SNV")
        elif step == "MSC":
            summary.append("MSC")
        elif step == "Savitzky-Golay":
            summary.append(
                f"Savitzky-Golay ({params['savgol_window']}, {params['savgol_polyorder']}, d={params['savgol_deriv']})"
            )
        elif step == "Normalisation":
            summary.append(f"Normalisation ({params['normalization_method']})")

    return summary


# ============================================================
# Page principale
# ============================================================
def render_preprocessing_page() -> None:
    """
    Rendu principal de la page Prétraitements.
    """
    X, meta = get_active_dataset()

    if X is None:
        st.warning("Veuillez d’abord préparer les données dans la page Import.")
        return

    page_header("Prétraitements", "Comparez l’effet des prétraitements sur vos spectres")

    # --------------------------------------------------------
    # Layout principal : panneau gauche + centre
    # --------------------------------------------------------
    left_col, right_col = st.columns([1.1, 2.4], gap="large")

    with left_col:
        steps = render_pipeline_builder()
        params = render_parameters_panel(X)

        st.write("")
        st.markdown("### Application")

        apply_clicked = st.button("Appliquer", type="primary", use_container_width=True)

        if steps:
            st.write("")
            st.markdown(
                """
                <div class="card">
                    <strong>Info prétraitement</strong><br><br>
                    Les prétraitements permettent de corriger les effets de diffusion,
                    lisser les spectres, dériver le signal ou normaliser l’échelle
                    entre échantillons.
                </div>
                """,
                unsafe_allow_html=True,
            )

    with right_col:
        st.markdown("### Comparaison avant / après")

        top_controls = st.columns([1.2, 1.2, 1.2])
        with top_controls[0]:
            color_options = [None] + list(meta.columns) if meta is not None else [None]
            color_col = st.selectbox("Colorer par", color_options, index=0)
        with top_controls[1]:
            pct_show = st.slider("Pourcentage affiché", min_value=1, max_value=100, value=30, step=1)
        with top_controls[2]:
            preview_mode = st.radio("Sélection", ["Séquentielle", "Aléatoire"], horizontal=True)
        n_total = len(X)
        n_preview = max(1, int(np.ceil(n_total * pct_show / 100)))
        
        if pct_show >= 100:
            preview_idx = X.index
        else:
            if preview_mode == "Aléatoire":
                preview_idx = np.random.choice(X.index, size=n_preview, replace=False)
            else:
                preview_idx = X.index[:n_preview]

        X_preview = X.loc[preview_idx].copy()
        meta_preview = meta.loc[preview_idx].copy() if meta is not None and not meta.empty else pd.DataFrame(index=X_preview.index)

        # Calcul preview après
        try:
            validate_preprocessing_params(params, X_preview)
            X_after_preview = preprocess_pipeline(X_preview, steps, params) if steps else X_preview.copy()
        except Exception as e:
            st.error(f"Erreur paramètres : {e}")
            return

        g1, g2 = st.columns(2)

        with g1:
            fig_before = plot_spectra_figure(
                X=X_preview,
                meta=meta_preview,
                color_col=color_col,
                title="Avant prétraitement",
                opacity=0.45,
                line_width=1.3,
                height=360,
                xaxis_title="Longueur d’onde (nm)",
                yaxis_title="Intensité / Absorbance",
            )
            plot_card(fig_before)

        with g2:
            fig_after = plot_spectra_figure(
                X=X_after_preview,
                meta=meta_preview,
                color_col=color_col,
                title="Après prétraitement",
                opacity=0.45,
                line_width=1.3,
                height=360,
                xaxis_title="Longueur d’onde (nm)",
                yaxis_title="Intensité / Absorbance",
            )
            plot_card(fig_after)
        
        st.markdown("### Résumé de l’aperçu")
        r1, r2, r3 = st.columns(3)
        with r1:
            st.metric("Spectres affichés", f"{len(X_preview)} / {len(X)}")
        with r2:
            st.metric("Pourcentage affiché", f"{pct_show}%")
        with r3:
            st.metric("Variables spectrales", X_preview.shape[1])

        # Résumé du pipeline
        st.markdown("### Résumé du pipeline")

        summary_steps = build_pipeline_summary(steps, params)

        sum_left, sum_right = st.columns([2, 1.2])

        with sum_left:
            if summary_steps:
                badges = " ".join(
                    [f"<span style='display:inline-block;background:#E6F4F1;color:#0F766E;padding:6px 10px;border-radius:8px;margin:4px;font-size:13px;'>{s}</span>" for s in summary_steps]
                )
                st.markdown(f"<div class='card'>{badges}</div>", unsafe_allow_html=True)
            else:
                st.info("Aucun prétraitement sélectionné.")

        with sum_right:
            st.markdown(
                """
                <div class="card">
                    <strong>Conseil</strong><br><br>
                    Évite d’empiler trop de prétraitements sans justification chimio-
                    métrique. Compare systématiquement avant / après.
                </div>
                """,
                unsafe_allow_html=True,
            )

    # --------------------------------------------------------
    # Application au dataset complet
    # --------------------------------------------------------
    if apply_clicked:
        try:
            validate_preprocessing_params(params, X)
            X_full_processed = preprocess_pipeline(X, steps, params) if steps else X.copy()

            df_full = pd.concat([meta, X_full_processed], axis=1)
            st.session_state.processed_df = df_full

            # On invalide les anciens résultats de réduction de dimension
            st.session_state.reduction_results = {}

            st.success("Prétraitement appliqué à tout le dataset.")
        except Exception as e:
            st.error(f"Erreur lors de l’application du pipeline : {e}")