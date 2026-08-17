# -*- coding: utf-8 -*-
"""
Created on Sat Apr 18 01:36:52 2026

@author: late_jj
"""

# ============================================================
# components/plotting.py
# ============================================================

from typing import Optional, List, Tuple, Dict

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Palette qualitative (ColorBrewer "Paired", non fournie nativement par
# Plotly Express) et échelle continue "Jet", utilisées partout dans
# l'application pour une identité visuelle cohérente.
QUALITATIVE_PALETTE = [
    "#a6cee3", "#1f78b4", "#b2df8a", "#33a02c",
    "#fb9a99", "#e31a1c", "#fdbf6f", "#ff7f00",
    "#cab2d6", "#6a3d9a", "#ffff99", "#b15928",
]
CONTINUOUS_COLORSCALE = "Jet"


def infer_wavelength_values(columns: List[str]) -> List[float]:
    """
    Convertit les noms de colonnes en valeurs numériques si possible.
    Sinon utilise l'index positionnel.
    """
    values = []
    for i, col in enumerate(columns):
        try:
            values.append(float(str(col).replace(",", ".")))
        except Exception:
            values.append(float(i))
    return values


def build_line_colors(
    meta: Optional[pd.DataFrame],
    color_col: Optional[str],
    idx: pd.Index,
) -> Tuple[List[str], Optional[Dict[str, str]], bool]:
    """
    Retourne :
    - une liste de couleurs par spectre
    - un mapping catégorie -> couleur si variable catégorielle
    - un bool indiquant si la variable de couleur est numérique
    """
    default_colors = ["rgba(37,99,235,0.35)"] * len(idx)

    if meta is None or meta.empty or color_col is None or color_col not in meta.columns:
        return default_colors, None, False

    vals = meta.loc[idx, color_col]

    # Couleur continue si variable numérique
    if pd.api.types.is_numeric_dtype(vals):
        v = vals.astype(float)
        vmin = float(v.min())
        vmax = float(v.max())

        if np.isclose(vmin, vmax):
            norm = np.zeros(len(v))
        else:
            norm = (v - vmin) / (vmax - vmin)

        colors = px.colors.sample_colorscale(CONTINUOUS_COLORSCALE, norm.tolist())
        return colors, None, True

    # Couleur discrète si variable catégorielle
    cats = vals.astype(str).fillna("NA")
    unique = list(pd.unique(cats))
    palette = QUALITATIVE_PALETTE
    cmap = {cat: palette[i % len(palette)] for i, cat in enumerate(unique)}
    colors = [cmap[val] for val in cats]

    return colors, cmap, False


def plot_spectra_figure(
    X: pd.DataFrame,
    meta: Optional[pd.DataFrame] = None,
    color_col: Optional[str] = None,
    title: str = "Spectres",
    opacity: float = 0.35,
    line_width: float = 1.5,
    height: int = 460,
    xaxis_title: str = "Longueur d’onde / variable spectrale",
    yaxis_title: str = "Absorbance / Intensité",
) -> go.Figure:
    """
    Trace un ensemble de spectres avec :
    - coloration par variable metadata
    - colorbar si variable numérique
    - légende si variable catégorielle
    """
    fig = go.Figure()

    x_vals = infer_wavelength_values(list(X.columns))
    colors, cmap, is_numeric_color = build_line_colors(meta, color_col, X.index)

    # Colorbar si variable numérique
    if (
        meta is not None
        and not meta.empty
        and color_col is not None
        and color_col in meta.columns
        and is_numeric_color
    ):
        vals = meta.loc[X.index, color_col].astype(float)
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="markers",
                marker=dict(
                    size=0,
                    color=[vals.min(), vals.max()],
                    colorscale=CONTINUOUS_COLORSCALE,
                    cmin=float(vals.min()),
                    cmax=float(vals.max()),
                    colorbar=dict(title=str(color_col)),
                    showscale=True,
                ),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # Légende si variable catégorielle
    if cmap is not None:
        for category, color in cmap.items():
            fig.add_trace(
                go.Scatter(
                    x=[None],
                    y=[None],
                    mode="lines",
                    line=dict(color=color, width=3),
                    name=str(category),
                    hoverinfo="skip",
                    showlegend=True,
                )
            )

    # Spectres
    for i, sample in enumerate(X.index):
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=X.loc[sample].values,
                mode="lines",
                line=dict(color=colors[i], width=line_width),
                opacity=opacity,
                name=str(sample),
                showlegend=False,
                hovertemplate=(
                    f"Échantillon: {sample}"
                    "<br>Longueur d’onde: %{x}"
                    "<br>Intensité: %{y:.4f}"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=20, r=20, t=45, b=20),
        title=title,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
    )

    return fig