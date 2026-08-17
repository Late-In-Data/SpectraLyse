# ============================================================
# ui/pca_page.py
# ============================================================
"""
Page PCA - version pro

Objectif :
- analyse multivariée claire
- visualisation scores + loadings
- interprétation rapide
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from core.reduction import compute_pca, pca_summary
from components.layout import page_header
from components.cards import plot_card, info_card


# ============================================================
# DATA
# ============================================================
def get_active_dataset():

    if st.session_state.get("processed_df") is not None:
        df = st.session_state.processed_df.copy()
    elif st.session_state.get("cleaned_df") is not None:
        df = st.session_state.cleaned_df.copy()
    else:
        return None, None

    cols = df.columns.tolist()

    x_cols = [c for c in st.session_state.get("x_columns", []) if c in cols]
    meta_cols = [c for c in st.session_state.get("meta_columns", []) if c in cols]

    if not x_cols:
        return None, None

    X = df[x_cols].apply(pd.to_numeric, errors="coerce")
    meta = df[meta_cols] if meta_cols else pd.DataFrame(index=df.index)

    return X, meta


# ============================================================
# VARIANCE PLOT
# ============================================================
def plot_variance(explained_df):

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=explained_df["Composante"],
            y=explained_df["Variance expliquée (%)"],
            name="Variance"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=explained_df["Composante"],
            y=explained_df["Variance cumulée (%)"],
            mode="lines+markers",
            name="Cumulée",
            yaxis="y2"
        )
    )

    fig.update_layout(
        template="plotly_white",
        height=350,
        yaxis=dict(title="Variance (%)"),
        yaxis2=dict(overlaying="y", side="right")
    )

    return fig


# ============================================================
# LOADINGS
# ============================================================
def plot_loadings(loadings_df, component):

    df = pd.DataFrame({
        "Variable": loadings_df.index,
        "Loading": loadings_df[component]
    })

    fig = px.line(df, x="Variable", y="Loading", color_discrete_sequence=["#0F766E"])

    fig.update_layout(
        template="plotly_white",
        height=350,
        title=f"Loadings {component}"
    )

    return fig


# ============================================================
# PAGE
# ============================================================
def render_pca_page():

    page_header("PCA", "Analyse en composantes principales")

    X, meta = get_active_dataset()

    if X is None:
        st.warning("Prépare les données dans l’onglet Import")
        return

    # --------------------------------------------------------
    # PARAMÈTRES
    # --------------------------------------------------------
    st.markdown("### Paramètres")

    c1, c2 = st.columns(2)

    with c1:
        n_comp = st.slider("Nombre de composantes", 2, min(10, X.shape[1]), 3)

    with c2:
        scale = st.checkbox("Standardiser", True)

    if st.button("Calculer PCA", type="primary"):

        scores, loadings, explained, model = compute_pca(
            X,
            n_components=n_comp,
            scale=scale
        )

        st.session_state.reduction_results["scores"] = scores
        st.session_state.reduction_results["loadings"] = loadings
        st.session_state.reduction_results["explained"] = explained

    if "scores" not in st.session_state.reduction_results:
        return

    scores = st.session_state.reduction_results["scores"]
    loadings = st.session_state.reduction_results["loadings"]
    explained = st.session_state.reduction_results["explained"]

    df_plot = pd.concat([meta, scores], axis=1)

    # --------------------------------------------------------
    # SCORE PLOT
    # --------------------------------------------------------
    st.markdown("### Score Plot")

    c1, c2, c3 = st.columns(3)

    with c1:
        x = st.selectbox("X", scores.columns)

    with c2:
        y = st.selectbox("Y", scores.columns, index=1)

    with c3:
        color = st.selectbox("Couleur", [None] + list(df_plot.columns))

    # Un symbole par catégorie en plus de la couleur, pour rester lisible même
    # en niveaux de gris ou en cas de daltonisme. Seulement si la variable est
    # catégorielle : sur une variable continue, cela forcerait un symbole par
    # valeur unique et casserait le dégradé continu de couleur.
    symbol = (
        color
        if color is not None and not pd.api.types.is_numeric_dtype(df_plot[color])
        else None
    )
    fig = px.scatter(df_plot, x=x, y=y, color=color, symbol=symbol)

    plot_card(fig)

    # --------------------------------------------------------
    # VARIANCE + LOADINGS
    # --------------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Variance expliquée")
        plot_card(plot_variance(explained))

    with col2:
        st.markdown("### Loadings")
        comp = st.selectbox("Composante", loadings.columns)
        plot_card(plot_loadings(loadings, comp))

    # --------------------------------------------------------
    # INTERPRÉTATION
    # --------------------------------------------------------
    st.markdown("### Interprétation")

    summary = pca_summary(explained)

    info_card(
        "Résumé PCA",
        f"""
        Variance expliquée :
        - 2 composantes : {summary['var_2_components']} %
        - 3 composantes : {summary['var_3_components']} %

        Qualité : {summary['quality']}
        """
    )