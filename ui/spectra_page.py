# ============================================================
# ui/spectra_page.py
# ============================================================

"""
Page SPECTRES - version pro enrichie

Responsabilités :
- affichage interactif des spectres
- coloration par variable metadata
- filtre par métadonnées
- sélection de plage spectrale
- sous-échantillonnage par pourcentage
- moyenne par groupe
- statistiques simples
- export HTML
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.layout import page_header
from components.cards import plot_card, info_card

from components.plotting import (
    infer_wavelength_values,
    plot_spectra_figure,
    QUALITATIVE_PALETTE,
)
from components.report_basket import add_figure_to_report

# ============================================================
# Helpers dataset
# ============================================================
def get_active_dataset():
    """
    Retourne X et metadata à partir du dataset actif.
    Priorité :
    1. processed_df
    2. cleaned_df
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


def get_numeric_like_columns(columns):
    """
    Retourne les colonnes convertibles en float et leur mapping numérique.
    """
    valid_cols = []
    mapping = {}

    for col in columns:
        try:
            val = float(str(col).replace(",", "."))
            valid_cols.append(col)
            mapping[col] = val
        except Exception:
            continue

    valid_cols = sorted(valid_cols, key=lambda c: mapping[c])
    return valid_cols, mapping


# ============================================================
# Filtre metadata
# ============================================================
def apply_metadata_filter(X: pd.DataFrame, meta: pd.DataFrame):
    """
    Filtre X et meta selon une métadonnée choisie.
    """
    if meta is None or meta.empty:
        return X, meta

    st.markdown("### Filtre par métadonnées")

    filterable_cols = list(meta.columns)

    c1, c2 = st.columns([1.2, 2.0])

    with c1:
        filter_col = st.selectbox(
            "Colonne de filtre",
            options=[None] + filterable_cols,
            index=0,
        )

    if filter_col is None:
        return X, meta

    series = meta[filter_col]

    with c2:
        if pd.api.types.is_numeric_dtype(series):
            s = series.astype(float)
            min_val = float(np.nanmin(s))
            max_val = float(np.nanmax(s))

            val_range = st.slider(
                "Plage de valeurs",
                min_value=min_val,
                max_value=max_val,
                value=(min_val, max_val),
            )

            mask = s.between(val_range[0], val_range[1], inclusive="both")

        else:
            values = sorted(series.astype(str).fillna("NA").unique().tolist())
            selected_values = st.multiselect(
                "Valeurs à conserver",
                options=values,
                default=values,
            )

            s = series.astype(str).fillna("NA")
            mask = s.isin(selected_values)

    X_f = X.loc[mask].copy()
    meta_f = meta.loc[mask].copy()

    st.caption(f"{len(X_f)} échantillon(s) conservé(s) après filtrage.")
    return X_f, meta_f


# ============================================================
# Filtre spectral
# ============================================================
def apply_spectral_range_filter(X: pd.DataFrame):
    """
    Filtre les colonnes spectrales selon une plage min/max si possible.
    """
    st.markdown("### Plage spectrale")

    numeric_like_cols, wl_map = get_numeric_like_columns(X.columns.tolist())

    if not numeric_like_cols:
        st.info("Les noms de colonnes spectrales ne sont pas tous convertibles en nombres. La plage spectrale n’est pas disponible sur ce dataset.")
        return X

    wl_min = float(min(wl_map.values()))
    wl_max = float(max(wl_map.values()))

    c1, c2 = st.columns(2)

    with c1:
        user_min = st.number_input("Longueur d’onde min", value=wl_min)

    with c2:
        user_max = st.number_input("Longueur d’onde max", value=wl_max)

    selected_cols = [
        c for c in numeric_like_cols
        if user_min <= wl_map[c] <= user_max
    ]

    if not selected_cols:
        st.warning("Aucune variable spectrale dans la plage choisie.")
        return X.iloc[:, :0]

    X_range = X[selected_cols].copy()
    st.caption(f"{X_range.shape[1]} variable(s) spectrale(s) conservée(s) dans la plage [{user_min}, {user_max}].")
    return X_range


# ============================================================
# Moyennes par groupe
# ============================================================
def plot_group_means(X: pd.DataFrame, meta: pd.DataFrame, group_col=None):
    """
    Affiche les spectres moyens par groupe si group_col est catégorielle.
    """
    if meta is None or meta.empty or group_col is None or group_col not in meta.columns:
        return None

    if pd.api.types.is_numeric_dtype(meta[group_col]):
        return None

    tmp = X.copy()
    tmp[group_col] = meta[group_col].astype(str)

    x_vals = infer_wavelength_values(list(X.columns))
    fig = go.Figure()

    palette = QUALITATIVE_PALETTE

    for i, grp in enumerate(pd.unique(tmp[group_col])):
        grp_df = tmp[tmp[group_col] == grp].drop(columns=[group_col])
        mean_spec = grp_df.mean(axis=0)

        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=mean_spec.values,
                mode="lines",
                name=str(grp),
                line=dict(color=palette[i % len(palette)], width=2.5),
            )
        )

    fig.update_layout(
        template="plotly_white",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
        title="Moyennes par groupe",
        xaxis_title="Longueur d’onde / variable spectrale",
        yaxis_title="Absorbance",
    )

    return fig


# ============================================================
# Export
# ============================================================
def build_html_download(fig: go.Figure, file_name: str = "spectres_interactifs.html"):
    """
    Propose le téléchargement HTML de la figure.
    """
    html_str = fig.to_html(include_plotlyjs="cdn", full_html=True)
    st.download_button(
        label="📄 Exporter la figure",
        data=html_str,
        file_name=file_name,
        mime="text/html",
    )


# ============================================================
# Page principale
# ============================================================
def render_spectra_page():
    """
    Rendu principal de la page Spectres.
    """
    X, meta = get_active_dataset()

    if X is None:
        st.warning("Veuillez d’abord préparer les données dans la page Import.")
        return

    page_header("Spectres", "Visualisez et comparez vos spectres")

    # --------------------------------------------------------
    # Filtres
    # --------------------------------------------------------
    X_f, meta_f = apply_metadata_filter(X, meta)
    X_f = apply_spectral_range_filter(X_f)

    if X_f is None or X_f.empty or X_f.shape[1] == 0:
        st.warning("Aucune donnée spectrale disponible après filtrage.")
        return

    # --------------------------------------------------------
    # Options d'affichage
    # --------------------------------------------------------
    st.markdown("### Options d'affichage")

    top_left, top_right = st.columns([6, 1])

    with top_left:
        c1, c2, c3 = st.columns([2, 2, 2])

        with c1:
            color_options = [None] + list(meta_f.columns) if meta_f is not None and not meta_f.empty else [None]
            color_col = st.selectbox("Colorer par", color_options, index=0)

        with c2:
            opacity_pct = st.slider("Transparence", 5, 100, 30)
            opacity = opacity_pct / 100.0

        with c3:
            line_width = st.slider("Épaisseur des lignes", 1.0, 4.0, 1.5, 0.1)

    with top_right:
        st.write("")
        st.write("")
        export_placeholder = st.empty()

    # --------------------------------------------------------
    # Sous-échantillonnage par %
    # --------------------------------------------------------
    control1, control2 = st.columns([1.6, 1.6])

    with control1:
        pct_show = st.slider(
            "Pourcentage de spectres affichés",
            min_value=1,
            max_value=100,
            value=100,
            step=1,
        )

    with control2:
        mode_sampling = st.radio(
            "Sélection des spectres",
            ["Séquentielle", "Aléatoire"],
            horizontal=True,
        )

    n_total = len(X_f)
    n_show = max(1, int(np.ceil(n_total * pct_show / 100)))

    if pct_show >= 100:
        selected_idx = X_f.index
    else:
        if mode_sampling == "Aléatoire":
            selected_idx = np.random.choice(X_f.index, size=n_show, replace=False)
        else:
            selected_idx = X_f.index[:n_show]

    X_sub = X_f.loc[selected_idx].copy()
    meta_sub = meta_f.loc[selected_idx].copy() if meta_f is not None and not meta_f.empty else pd.DataFrame(index=X_sub.index)

    # --------------------------------------------------------
    # Graphe principal
    # --------------------------------------------------------
    fig_main = plot_spectra_figure(
        X=X_sub,
        meta=meta_sub,
        color_col=color_col,
        opacity=opacity,
        line_width=line_width,
        title="Spectres",
        height=460,
        xaxis_title="Longueur d’onde / variable spectrale",
        yaxis_title="Absorbance / Intensité",
    )

    with export_placeholder:
        build_html_download(fig_main)

    plot_card(fig_main)

    main_label = "Spectres" + (f" (coloré par {color_col})" if color_col else "")
    if st.button("Ajouter ce graphique au rapport", key="add_report_spectra_main"):
        add_figure_to_report(
            "spectres", main_label, fig_main.to_html(full_html=False, include_plotlyjs=False)
        )
        st.success(f"Ajouté au rapport : {main_label}")

    # --------------------------------------------------------
    # Moyennes par groupe
    # --------------------------------------------------------
    st.markdown("### Moyennes par groupe")
    fig_group = plot_group_means(X_sub, meta_sub, color_col)
    if fig_group is not None:
        plot_card(fig_group)

        group_label = f"Moyennes par groupe (coloré par {color_col})"
        if st.button("Ajouter ce graphique au rapport", key="add_report_spectra_group"):
            add_figure_to_report(
                "spectres", group_label, fig_group.to_html(full_html=False, include_plotlyjs=False)
            )
            st.success(f"Ajouté au rapport : {group_label}")
    else:
        info_card(
            "Moyennes par groupe",
            "Choisissez une variable catégorielle dans 'Colorer par' pour afficher les spectres moyens par groupe."
        )

    # --------------------------------------------------------
    # Résumé
    # --------------------------------------------------------
    st.markdown("### Résumé")
    info1, info2, info3, info4, info5 = st.columns(5)

    with info1:
        st.metric("Spectres affichés", f"{len(X_sub)} / {len(X_f)}")

    with info2:
        st.metric("Pourcentage affiché", f"{pct_show}%")

    with info3:
        st.metric("Variables spectrales", X_sub.shape[1])

    with info4:
        n_groups = (
            meta_sub[color_col].nunique()
            if meta_sub is not None
            and not meta_sub.empty
            and color_col is not None
            and color_col in meta_sub.columns
            and not pd.api.types.is_numeric_dtype(meta_sub[color_col])
            else 0
        )
        st.metric("Groupes", n_groups)

    with info5:
        remaining_na = int(X_sub.isna().sum().sum())
        st.metric("NA restants dans X", remaining_na)