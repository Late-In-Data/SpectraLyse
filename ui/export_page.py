# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 14:52:08 2026

@author: late_jj
"""

# ============================================================
# ui/export_page.py
# ============================================================

"""
Page EXPORT / RÉSULTATS

Objectif :
- télécharger les jeux de données intermédiaires
- exporter les résultats PCA
- générer un rapport HTML autonome et léger de l'analyse
"""

import datetime as dt
import html
import io
import platform
import re
from importlib import metadata as importlib_metadata

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core.data import quality_overview
from components.layout import page_header
from components.cards import info_card
from components.plotting import plot_spectra_figure
from components.report_basket import render_basket_summary
from ui.pca_page import plot_variance


# ============================================================
# Exports CSV / Excel
# ============================================================
def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """
    Convertit un DataFrame en CSV encodé UTF-8.
    """
    return df.to_csv(index=True).encode("utf-8")


def dataframe_to_excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    """
    Convertit plusieurs DataFrames en un fichier Excel multi-feuilles.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name[:31], index=True)
    output.seek(0)
    return output.read()


def render_export_block(title: str, df: pd.DataFrame, file_stub: str) -> None:
    """
    Affiche un bloc d’export pour un DataFrame donné.
    """
    st.markdown(
        f"""
        <div class="card">
            <h4>{title}</h4>
            <p>{df.shape[0]} lignes × {df.shape[1]} colonnes</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)

    with c1:
        st.download_button(
            label="Télécharger en CSV",
            data=dataframe_to_csv_bytes(df),
            file_name=f"{file_stub}.csv",
            mime="text/csv",
            width="stretch",
        )

    with c2:
        xlsx_bytes = dataframe_to_excel_bytes({file_stub: df})
        st.download_button(
            label="Télécharger en Excel",
            data=xlsx_bytes,
            file_name=f"{file_stub}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
        )

    with st.expander("Aperçu"):
        st.dataframe(df.head(30), width="stretch")


# ============================================================
# Helpers rapport HTML
# ============================================================
def preview_list_html(items, max_items: int = 25) -> str:
    """
    Génère une petite liste HTML avec troncature.
    """
    if not items:
        return "<p class='muted'>Aucune</p>"

    shown = items[:max_items]
    lis = "".join(f"<li>{html.escape(str(x))}</li>" for x in shown)

    extra = ""
    if len(items) > max_items:
        extra = f"<p class='muted'>Aperçu limité à {max_items} sur {len(items)} éléments.</p>"

    return f"<ul>{lis}</ul>{extra}"


def df_to_html_table(df: pd.DataFrame | None, max_rows: int = 20) -> str:
    """
    Convertit un DataFrame en tableau HTML compact.
    """
    if df is None or df.empty:
        return "<p class='muted'>Aucune donnée disponible.</p>"

    return df.head(max_rows).to_html(
        index=True,
        classes="data-table",
        border=0,
        escape=True,
    )


def build_pca_score_plot_html(
    scores: pd.DataFrame | None,
    meta_df: pd.DataFrame | None,
) -> str:
    """
    Construit un score plot PCA interactif (PC1 vs PC2). Plotly est chargé
    une seule fois, globalement, via `_plotly_inline_scripts()` dans le
    <head> du rapport plutôt qu'ici.
    """
    if scores is None or scores.empty or scores.shape[1] < 2:
        return "<p class='muted'>Pas de résultats PCA disponibles pour la visualisation.</p>"

    plot_df = scores[["PC1", "PC2"]].copy()
    color_col = None

    if meta_df is not None and not meta_df.empty:
        candidates = [
            c for c in meta_df.columns
            if not pd.api.types.is_numeric_dtype(meta_df[c]) and 1 < meta_df[c].nunique() <= 15
        ]
        if candidates:
            color_col = candidates[0]
            plot_df[color_col] = meta_df.loc[plot_df.index, color_col].astype(str)

    fig = px.scatter(
        plot_df,
        x="PC1",
        y="PC2",
        color=color_col,
        symbol=color_col,
        title=f"Score plot PCA (coloré par {color_col})" if color_col else "Score plot PCA",
    )
    fig.update_layout(
        template="plotly_white",
        height=420,
        margin=dict(l=20, r=20, t=50, b=20),
    )

    return fig.to_html(full_html=False, include_plotlyjs=False)


def _plotly_inline_scripts() -> str:
    """
    Balises <script> chargeant Plotly, à placer une seule fois dans le
    <head> du rapport. Tous les graphiques du rapport sont ensuite
    construits avec include_plotlyjs=False : Plotly doit être disponible
    avant le premier <script> qui appelle Plotly.newPlot(...), donc dans le
    <head>, pas au milieu du corps du document.

    La librairie est embarquée directement dans le fichier (pas de CDN) :
    le rapport doit s'ouvrir et s'afficher correctement même sans connexion
    internet, ce qui n'est pas garanti avec un chargement externe. Le fichier
    est plus volumineux (quelques Mo de plus), mais reste un simple
    téléchargement ponctuel, pas une page consultée à répétition.
    """
    dummy_html = go.Figure().to_html(full_html=False, include_plotlyjs=True)
    setup_prefix = dummy_html[: dummy_html.find("<div id=")]
    scripts = re.findall(r"<script.*?</script>", setup_prefix, re.S)
    return "".join(scripts)


def build_pca_variance_plot_html(explained: pd.DataFrame | None) -> str:
    """
    Réutilise le graphique de variance expliquée de la page PCA.
    """
    if explained is None or explained.empty:
        return "<p class='muted'>Pas de résultats PCA disponibles pour la visualisation.</p>"

    fig = plot_variance(explained)
    return fig.to_html(full_html=False, include_plotlyjs=False)


def build_pca_loadings_plot_html(loadings: pd.DataFrame | None) -> str:
    """
    Loadings de toutes les composantes calculées, superposées sur un même
    graphique (plus lisible qu'un tableau brut de chiffres pour un rapport
    statique, où il n'y a pas de sélecteur de composante comme dans l'app).
    """
    if loadings is None or loadings.empty:
        return "<p class='muted'>Pas de loadings disponibles pour la visualisation.</p>"

    long_df = (
        loadings
        .reset_index()
        .rename(columns={"index": "Variable"})
        .melt(id_vars="Variable", var_name="Composante", value_name="Loading")
    )
    fig = px.line(long_df, x="Variable", y="Loading", color="Composante", title="Loadings PCA")
    fig.update_layout(
        template="plotly_white",
        height=380,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig.to_html(full_html=False, include_plotlyjs=False)


def render_saved_figures_html(entries: list[dict]) -> str:
    """
    Affiche une série de figures explicitement ajoutées au rapport par
    l'utilisateur (voir components/report_basket.py), chacune avec son
    étiquette de configuration (couleur, symbole, pipeline...).
    """
    blocks = []
    for entry in entries:
        blocks.append(
            f"<div style='margin-top:16px;'>"
            f"<p class='muted'><strong>{html.escape(entry['label'])}</strong></p>"
            f"{entry['html']}"
            f"</div>"
        )
    return "".join(blocks)


def build_preprocessing_comparison_html(
    cleaned_df: pd.DataFrame | None,
    processed_df: pd.DataFrame | None,
    x_cols: list[str],
    meta_df: pd.DataFrame | None,
    max_samples: int = 50,
) -> str:
    """
    Comparaison visuelle avant/après prétraitement, sur un sous-échantillon
    (séquentiel, pas aléatoire, pour que le rapport reste reproductible)
    afin de garder le fichier léger.
    """
    if cleaned_df is None or processed_df is None or not x_cols:
        return "<p class='muted'>Aucun prétraitement appliqué.</p>"

    x_cols_present = [c for c in x_cols if c in cleaned_df.columns and c in processed_df.columns]
    if not x_cols_present:
        return "<p class='muted'>Colonnes spectrales indisponibles pour la comparaison.</p>"

    idx = cleaned_df.index[:max_samples]
    X_before = cleaned_df.loc[idx, x_cols_present].apply(pd.to_numeric, errors="coerce")
    X_after = processed_df.loc[idx, x_cols_present].apply(pd.to_numeric, errors="coerce")
    meta_sample = (
        meta_df.loc[meta_df.index.intersection(idx)]
        if meta_df is not None and not meta_df.empty
        else None
    )

    fig_before = plot_spectra_figure(X_before, meta_sample, title="Avant prétraitement", height=340, opacity=0.4)
    fig_after = plot_spectra_figure(X_after, meta_sample, title="Après prétraitement", height=340, opacity=0.4)

    note = ""
    if len(cleaned_df) > max_samples:
        note = f"<p class='muted'>Aperçu limité à {max_samples} échantillon(s) sur {len(cleaned_df)}.</p>"

    return (
        "<div class='grid' style='grid-template-columns: 1fr 1fr;'>"
        f"<div>{fig_before.to_html(full_html=False, include_plotlyjs=False)}</div>"
        f"<div>{fig_after.to_html(full_html=False, include_plotlyjs=False)}</div>"
        f"</div>{note}"
    )


# ============================================================
# Construction du rapport HTML
# ============================================================
def build_html_report(
    file_name: str | None,
    raw_df: pd.DataFrame | None,
    cleaned_df: pd.DataFrame | None,
    processed_df: pd.DataFrame | None,
    x_cols: list[str],
    meta_cols: list[str],
    preprocess_steps: list[str],
    preprocess_params: dict,
    scores: pd.DataFrame | None,
    loadings: pd.DataFrame | None,
    explained: pd.DataFrame | None,
    meta_df: pd.DataFrame | None = None,
    project_name: str | None = None,
    author: str | None = None,
    notes: str | None = None,
    report_figures: list[dict] | None = None,
) -> str:
    """
    Construit un rapport HTML autonome et léger de l'analyse SpectraLyse.

    Le rapport reste volontairement compact : Plotly n'est chargé qu'une
    fois via CDN (pas de librairie embarquée en dur), et les tableaux
    sont tronqués à un nombre raisonnable de lignes.
    """
    generated_at = dt.datetime.now().strftime("%d/%m/%Y à %H:%M")
    plotly_inline_scripts = _plotly_inline_scripts()

    project_name_safe = html.escape(project_name) if project_name else None
    author_safe = html.escape(author) if author else None
    notes_html = html.escape(notes).replace("\n", "<br>") if notes and notes.strip() else None

    def shape_text(df):
        if df is None:
            return "Non disponible"
        return f"{df.shape[0]} × {df.shape[1]}"

    def metric(label: str, value) -> str:
        return f"""
    <div class='metric'>
        <div class='label'>{label}</div>
        <div class='value'>{value}</div>
    </div>
    """

    def package_version(package: str) -> str:
        try:
            return importlib_metadata.version(package)
        except importlib_metadata.PackageNotFoundError:
            return "non détectée"

    reproducibility_html = "".join(
        metric(label, version)
        for label, version in [
            ("Python", platform.python_version()),
            ("streamlit", package_version("streamlit")),
            ("pandas", package_version("pandas")),
            ("numpy", package_version("numpy")),
            ("scipy", package_version("scipy")),
            ("scikit-learn", package_version("scikit-learn")),
            ("plotly", package_version("plotly")),
        ]
    )

    # --------------------------------------------------------
    # Qualité des données (sur le dataset le plus avancé disponible)
    # --------------------------------------------------------
    quality_ref = cleaned_df if cleaned_df is not None else raw_df

    if quality_ref is not None and not quality_ref.empty:
        overview = quality_overview(quality_ref)
        report = overview["report"]
        total_na = overview["total_na"]
        pct_na = round(overview["pct_na"], 2)
        n_duplicates = overview["n_duplicates"]
        n_empty_cols = overview["n_empty_cols"]
        quality_score = round(max(0.0, 100 - pct_na - (5 if n_duplicates else 0)), 1)
        top_missing = report[report["Missing"] > 0].head(10)
        top_missing = top_missing.reset_index().rename(columns={"index": "Colonne", "%": "% manquant"})
        top_missing["% manquant"] = top_missing["% manquant"].round(2)
        top_missing_html = df_to_html_table(top_missing[["Colonne", "% manquant"]], max_rows=10)
    else:
        pct_na = 0.0
        n_duplicates = 0
        n_empty_cols = 0
        quality_score = 0.0
        top_missing_html = "<p class='muted'>Aucune donnée disponible.</p>"

    preprocess_steps_html = (
        "".join(f"<span class='badge'>{step}</span>" for step in preprocess_steps)
        if preprocess_steps else
        "<span class='muted'>Aucun prétraitement appliqué</span>"
    )

    preprocess_params_html = (
        "<pre>" + str(preprocess_params) + "</pre>"
        if preprocess_params else
        "<p class='muted'>Aucun paramètre enregistré.</p>"
    )

    report_figures = report_figures or []
    saved_pca = [f for f in report_figures if f["section"] == "pca"]
    saved_pretraitement = [f for f in report_figures if f["section"] == "pretraitement"]
    saved_spectres = [f for f in report_figures if f["section"] == "spectres"]

    # Les figures explicitement ajoutées par l'utilisateur (configurées comme
    # il le souhaite) remplacent la figure automatique par défaut, plutôt que
    # de s'y ajouter -> pas de doublon quand l'utilisateur a pris le temps de
    # choisir sa configuration.
    preprocess_comparison_html = (
        render_saved_figures_html(saved_pretraitement)
        if saved_pretraitement else
        build_preprocessing_comparison_html(cleaned_df, processed_df, x_cols, meta_df)
    )

    pca_plot_html = (
        render_saved_figures_html(saved_pca)
        if saved_pca else
        build_pca_score_plot_html(scores, meta_df)
    )
    pca_variance_plot_html = build_pca_variance_plot_html(explained)
    pca_loadings_plot_html = build_pca_loadings_plot_html(loadings)

    spectres_html = render_saved_figures_html(saved_spectres)
    spectres_nav_link = '<a href="#spectres">Spectres</a>' if saved_spectres else ""
    spectres_section_html = f"""
    <section class="card" id="spectres">
        <div class="section-heading">
            <h2><span class="section-icon">📈</span>Spectres</h2>
            <p class="section-subtitle">Graphiques ajoutés manuellement depuis la page Spectres.</p>
        </div>
        {spectres_html}
    </section>
    """ if saved_spectres else ""

    pca_summary_html = ""
    if explained is not None and not explained.empty:
        var2 = round(explained["Variance expliquée (%)"].iloc[:2].sum(), 2)
        var3 = round(explained["Variance expliquée (%)"].iloc[:3].sum(), 2) if len(explained) >= 3 else var2
        pca_summary_html = f"""
    <div class="grid">
        {metric("Variance (2 comp.)", f"{var2} %")}
        {metric("Variance (3 comp.)", f"{var3} %")}
        {metric("Composantes calculées", len(explained))}
    </div>
    """

    report_html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{project_name_safe or "SpectraLyse"} — Rapport d'analyse</title>
<style>
    :root {{
        --bg:#F7F9FC; --card:#FFFFFF; --text:#1F2937; --muted:#6B7280; --line:#E5E7EB;
        --primary:#0F766E; --primary-dark:#0B4F49; --accent:#0891B2;
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font-family:Inter, "Segoe UI", Arial, sans-serif; background:var(--bg); color:var(--text); }}
    header {{ background:linear-gradient(135deg,#0B4F49,#0F766E 55%,#0891B2); color:white; padding:38px 48px; }}
    header h1 {{ margin:0; font-size:32px; letter-spacing:-.02em; }}
    header p {{ margin:8px 0 0; color:#D1FAE5; font-size:15px; }}
    main {{ max-width:1180px; margin:0 auto; padding:24px; }}
    .card {{ background:var(--card); border-radius:16px; padding:22px; margin-bottom:20px; box-shadow:0 8px 24px rgba(15,23,42,.06); border:1px solid var(--line); }}
    .toc {{ display:flex; gap:14px; align-items:center; flex-wrap:wrap; position:sticky; top:0; z-index:10; }}
    .toc a {{ color:var(--primary-dark); text-decoration:none; font-weight:600; font-size:14px; }}
    .section-heading {{ margin-bottom:16px; border-left:4px solid var(--primary); padding-left:12px; }}
    .section-heading h2 {{ margin:0; font-size:21px; letter-spacing:-.01em; }}
    .section-icon {{ margin-right:6px; }}
    .section-subtitle {{ margin:4px 0 0; color:var(--muted); font-size:13px; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:12px; }}
    .metric {{ background:linear-gradient(180deg,#F8FAFC,#FFFFFF); border:1px solid var(--line); border-radius:12px; padding:14px; }}
    .label {{ color:var(--muted); font-size:12px; }}
    .value {{ margin-top:4px; font-size:20px; font-weight:800; word-break:break-word; color:var(--primary-dark); }}
    .muted {{ color:var(--muted); font-size:13px; }}
    .badge {{ display:inline-block; background:#E6F4F1; color:var(--primary); padding:6px 10px; border-radius:8px; margin:4px 6px 0 0; font-size:0.85rem; font-weight:600; }}
    .table-wrapper {{ overflow-x:auto; max-width:100%; border-radius:10px; border:1px solid var(--line); }}
    .data-table {{ width:100%; border-collapse:collapse; font-size:13px; background:white; }}
    .data-table th {{ background:#F0FDFA; color:var(--primary-dark); text-align:left; padding:8px 10px; border-bottom:1px solid #99F6E4; }}
    .data-table td {{ padding:7px 10px; border-bottom:1px solid #E5E7EB; vertical-align:top; }}
    .data-table tr:nth-child(even) td {{ background:#FAFBFF; }}
    details {{ border:1px solid var(--line); border-radius:12px; padding:10px 14px; margin:12px 0; background:#fff; }}
    summary {{ cursor:pointer; font-weight:700; color:#0B4F49; }}
    pre {{ white-space:pre-wrap; word-break:break-word; background:#F8FAFC; border:1px solid var(--line); border-radius:10px; padding:12px; font-size:13px; }}
    footer {{ text-align:center; color:var(--muted); font-size:12px; padding:24px; }}

    /* Impression / export PDF via le navigateur (Fichier → Imprimer) */
    @media print {{
        body {{ background: white; }}
        main {{ max-width: 100%; }}
        .toc {{ display: none; }}
        header, .metric, .badge, .data-table th {{
            print-color-adjust: exact;
            -webkit-print-color-adjust: exact;
        }}
        .card, .metric, .plot-card, details {{
            box-shadow: none;
            page-break-inside: avoid;
        }}
        .table-wrapper {{ overflow-x: visible; }}
        /* Les <details> fermés restent utiles à l'écran (pour explorer sans
        surcharger la page), mais sur papier il n'y a pas d'interaction
        possible : on force leur contenu visible à l'impression. */
        details:not([open]) > *:not(summary) {{
            display: block !important;
        }}
    }}
</style>
{plotly_inline_scripts}
</head>
<body>

<header>
    <h1>SpectraLyse — {project_name_safe or "Rapport d'analyse"}</h1>
    <p>
        Généré le {generated_at} · Fichier actif : {html.escape(file_name) if file_name else "Non disponible"}
        {" · Auteur : " + author_safe if author_safe else ""}
    </p>
</header>

<main>

    <nav class="toc card">
        <strong>Sommaire</strong>
        <a href="#resume">Résumé</a>
        <a href="#notes-auteur">Notes de l'auteur</a>
        <a href="#qualite">Qualité</a>
        <a href="#selection">Sélection</a>
        {spectres_nav_link}
        <a href="#pretraitement">Prétraitement</a>
        <a href="#pca">PCA</a>
        <a href="#apercu">Aperçu des données</a>
        <a href="#reproductibilite">Reproductibilité</a>
        <a href="#notes">Notes</a>
    </nav>

    <section class="card" id="resume">
        <div class="section-heading">
            <h2><span class="section-icon">📌</span>Résumé exécutif</h2>
            <p class="section-subtitle">Vue d'ensemble du dataset et de l'analyse.</p>
        </div>
        <div class="grid">
            {metric("Dataset brut", shape_text(raw_df))}
            {metric("Dataset nettoyé", shape_text(cleaned_df))}
            {metric("Dataset prétraité", shape_text(processed_df))}
            {metric("Colonnes X (spectrales)", len(x_cols))}
            {metric("Métadonnées", len(meta_cols))}
            {metric("Étapes de prétraitement", len(preprocess_steps))}
        </div>
    </section>

    <section class="card" id="notes-auteur">
        <div class="section-heading">
            <h2><span class="section-icon">📝</span>Notes de l'auteur</h2>
            <p class="section-subtitle">Observations et commentaires ajoutés avant la génération.</p>
        </div>
        <p>{notes_html or "<span class='muted'>Aucune note ajoutée.</span>"}</p>
    </section>

    <section class="card" id="qualite">
        <div class="section-heading">
            <h2><span class="section-icon">✓</span>Qualité des données</h2>
            <p class="section-subtitle">Valeurs manquantes, doublons et colonnes vides sur le dataset le plus avancé disponible.</p>
        </div>
        <div class="grid">
            {metric("Score qualité", f"{quality_score} / 100")}
            {metric("Taux de NA global", f"{pct_na} %")}
            {metric("Doublons", n_duplicates)}
            {metric("Colonnes entièrement vides", n_empty_cols)}
        </div>
        <details open>
            <summary>Colonnes avec le plus de valeurs manquantes</summary>
            <div class="table-wrapper">{top_missing_html}</div>
        </details>
    </section>

    <section class="card" id="selection">
        <div class="section-heading">
            <h2><span class="section-icon">🎯</span>Sélection des variables</h2>
            <p class="section-subtitle">Colonnes retenues comme variables spectrales (X) et comme métadonnées.</p>
        </div>
        <div class="grid" style="grid-template-columns: 1fr 1fr;">
            <div>
                <h3 style="font-size:14px;">Colonnes spectrales (X)</h3>
                {preview_list_html(x_cols, max_items=30)}
            </div>
            <div>
                <h3 style="font-size:14px;">Métadonnées</h3>
                {preview_list_html(meta_cols, max_items=30)}
            </div>
        </div>
    </section>

    {spectres_section_html}

    <section class="card" id="pretraitement">
        <div class="section-heading">
            <h2><span class="section-icon">⚙️</span>Prétraitement</h2>
            <p class="section-subtitle">Pipeline et paramètres appliqués aux spectres.</p>
        </div>
        <div>{preprocess_steps_html}</div>
        <div style="margin-top:16px;">{preprocess_comparison_html}</div>
        <details>
            <summary>Paramètres détaillés</summary>
            {preprocess_params_html}
        </details>
    </section>

    <section class="card" id="pca">
        <div class="section-heading">
            <h2><span class="section-icon">📈</span>Résultats PCA</h2>
            <p class="section-subtitle">Structure des données réduite en composantes principales.</p>
        </div>
        {pca_summary_html}
        <div style="margin-top:16px;">{pca_plot_html}</div>
        <div class="grid" style="grid-template-columns: 1fr 1fr; margin-top:16px;">
            <div>{pca_variance_plot_html}</div>
            <div>{pca_loadings_plot_html}</div>
        </div>
        <details>
            <summary>Tableau des scores PCA</summary>
            <div class="table-wrapper">{df_to_html_table(scores, max_rows=15)}</div>
        </details>
        <details>
            <summary>Tableau des loadings PCA</summary>
            <div class="table-wrapper">{df_to_html_table(loadings, max_rows=15)}</div>
        </details>
    </section>

    <section class="card" id="apercu">
        <div class="section-heading">
            <h2><span class="section-icon">👁️</span>Aperçu des données</h2>
            <p class="section-subtitle">Extraits limités pour garder le rapport léger.</p>
        </div>
        <details open>
            <summary>Dataset nettoyé</summary>
            <div class="table-wrapper">{df_to_html_table(cleaned_df, max_rows=15)}</div>
        </details>
        <details>
            <summary>Dataset prétraité</summary>
            <div class="table-wrapper">{df_to_html_table(processed_df, max_rows=15)}</div>
        </details>
    </section>

    <section class="card" id="reproductibilite">
        <div class="section-heading">
            <h2><span class="section-icon">🔁</span>Reproductibilité</h2>
            <p class="section-subtitle">Versions des bibliothèques utilisées pour générer ce rapport.</p>
        </div>
        <div class="grid">
            {reproducibility_html}
        </div>
    </section>

    <section class="card" id="notes">
        <div class="section-heading">
            <h2><span class="section-icon">⚠️</span>Notes méthodologiques</h2>
            <p class="section-subtitle">Points de prudence pour l'interprétation.</p>
        </div>
        <ul class="muted">
            <li>La PCA est une méthode linéaire et exploratoire : l'absence de groupes nets ne signifie pas l'absence de structure.</li>
            <li>Les prétraitements (SNV, MSC, Savitzky-Golay, normalisation) modifient l'interprétation des loadings : comparez toujours avant/après.</li>
            <li>Ce rapport reflète l'état de la session au moment de l'export ; régénérez-le après toute modification du pipeline.</li>
        </ul>
    </section>

</main>

<footer>SpectraLyse · Rapport généré automatiquement</footer>

</body>
</html>
"""
    return report_html


# ============================================================
# Page principale
# ============================================================
def render_export_page() -> None:
    """
    Rendu principal de la page Export.
    """
    page_header("Export / Résultats", "Téléchargez vos données et résultats")

    left, right = st.columns([2.2, 1.0], gap="large")

    with left:
        st.markdown(
            """
            <div class="card">
                <h3>Exports disponibles</h3>
                <p>
                Cette page permet de récupérer les différents objets produits dans l’application :
                données nettoyées, données prétraitées et résultats d’analyse PCA.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        info_card(
            "Conseil",
            "Exportez de préférence les données nettoyées ou prétraitées ainsi que les résultats PCA pour documenter vos analyses."
        )

    # --------------------------------------------------------
    # Datasets
    # --------------------------------------------------------
    st.markdown("### Données")

    raw_df = st.session_state.get("raw_df")
    cleaned_df = st.session_state.get("cleaned_df")
    processed_df = st.session_state.get("processed_df")

    if raw_df is not None:
        render_export_block("Dataset brut", raw_df, "dataset_brut")

    if cleaned_df is not None:
        render_export_block("Dataset nettoyé", cleaned_df, "dataset_nettoye")

    if processed_df is not None:
        render_export_block("Dataset prétraité", processed_df, "dataset_pretraite")

    if raw_df is None and cleaned_df is None and processed_df is None:
        st.info("Aucun dataset disponible pour l’export.")

    # --------------------------------------------------------
    # Résultats PCA
    # --------------------------------------------------------
    st.markdown("### Résultats PCA")

    reduction_results = st.session_state.get("reduction_results", {})

    scores = reduction_results.get("scores")
    loadings = reduction_results.get("loadings")
    explained = reduction_results.get("explained")

    if scores is not None:
        render_export_block("Scores PCA", scores, "pca_scores")

    if loadings is not None:
        render_export_block("Loadings PCA", loadings, "pca_loadings")

    if explained is not None:
        render_export_block("Variance expliquée PCA", explained, "pca_variance")

    if scores is None and loadings is None and explained is None:
        st.info("Aucun résultat PCA disponible pour l’export.")

    # --------------------------------------------------------
    # Figures sauvegardées pour le rapport
    # --------------------------------------------------------
    st.markdown("### Figures pour le rapport")
    st.caption(
        "Configure un graphique comme tu veux (couleur, symbole, prétraitement) sur sa page, "
        "puis clique sur « Ajouter au rapport ». Tu peux en sauvegarder plusieurs par section "
        "pour comparer différentes configurations dans le rapport final."
    )

    fig_left, fig_mid, fig_right = st.columns(3)
    with fig_left:
        st.markdown("**PCA**")
        render_basket_summary("pca", "PCA")
    with fig_mid:
        st.markdown("**Prétraitement**")
        render_basket_summary("pretraitement", "Prétraitement")
    with fig_right:
        st.markdown("**Spectres**")
        render_basket_summary("spectres", "Spectres")

    # --------------------------------------------------------
    # Rapport HTML
    # --------------------------------------------------------
    st.markdown("### Rapport HTML")
    st.caption("Rapport autonome et léger : Plotly n'est embarqué qu'une seule fois dans le fichier.")

    conf_left, conf_right = st.columns([1.2, 1.8], gap="large")

    with conf_left:
        project_name = st.text_input("Nom du projet (optionnel)", value="")
        author = st.text_input("Auteur (optionnel)", value="")

    with conf_right:
        notes = st.text_area(
            "Notes & commentaires (optionnel)",
            value="",
            height=100,
            placeholder="Observations, interprétations, conclusions...",
        )

    meta_cols = st.session_state.get("meta_columns", [])
    source_df = processed_df if processed_df is not None else cleaned_df
    meta_df = (
        source_df[[c for c in meta_cols if c in source_df.columns]]
        if source_df is not None and meta_cols
        else None
    )

    report_html = build_html_report(
        file_name=st.session_state.get("file_name"),
        raw_df=raw_df,
        cleaned_df=cleaned_df,
        processed_df=processed_df,
        x_cols=st.session_state.get("x_columns", []),
        meta_cols=meta_cols,
        preprocess_steps=st.session_state.get("preprocess_pipeline", []),
        preprocess_params=st.session_state.get("preprocess_params", {}),
        scores=scores,
        loadings=loadings,
        explained=explained,
        meta_df=meta_df,
        project_name=project_name,
        author=author,
        notes=notes,
        report_figures=st.session_state.get("report_figures", []),
    )

    report_slug = re.sub(r"[^a-z0-9]+", "_", project_name.strip().lower()).strip("_") if project_name.strip() else ""
    report_filename = f"spectralyse_report_{report_slug}.html" if report_slug else "spectralyse_report.html"

    st.download_button(
        label="Télécharger le rapport HTML",
        data=report_html.encode("utf-8"),
        file_name=report_filename,
        mime="text/html",
        width="stretch",
    )

    # --------------------------------------------------------
    # Export global Excel
    # --------------------------------------------------------
    st.markdown("### Export global")

    sheets = {}

    if raw_df is not None:
        sheets["dataset_brut"] = raw_df
    if cleaned_df is not None:
        sheets["dataset_nettoye"] = cleaned_df
    if processed_df is not None:
        sheets["dataset_pretraite"] = processed_df
    if scores is not None:
        sheets["pca_scores"] = scores
    if loadings is not None:
        sheets["pca_loadings"] = loadings
    if explained is not None:
        sheets["pca_variance"] = explained

    if sheets:
        all_bytes = dataframe_to_excel_bytes(sheets)
        st.download_button(
            label="Télécharger tous les résultats (Excel)",
            data=all_bytes,
            file_name="spectralyse_exports.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            width="stretch",
        )
    else:
        st.info("Aucun contenu disponible pour un export global.")
