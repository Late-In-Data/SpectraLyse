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
- fournir une sortie exploitable hors de l’application
"""

import io
import pandas as pd
import streamlit as st

from components.layout import page_header
from components.cards import info_card


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
            use_container_width=True,
        )

    with c2:
        xlsx_bytes = dataframe_to_excel_bytes({file_stub: df})
        st.download_button(
            label="Télécharger en Excel",
            data=xlsx_bytes,
            file_name=f"{file_stub}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with st.expander("Aperçu"):
        st.dataframe(df.head(30), use_container_width=True)


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

    # Compatibilité avec tes différentes clés possibles
    scores = reduction_results.get("scores")
    if scores is None:
        scores = reduction_results.get("PCA_scores")
    
    loadings = reduction_results.get("loadings")
    if loadings is None:
        loadings = reduction_results.get("PCA_loadings")
    
    explained = reduction_results.get("explained")
    if explained is None:
        explained = reduction_results.get("PCA_explained")

    if scores is not None:
        render_export_block("Scores PCA", scores, "pca_scores")

    if loadings is not None:
        render_export_block("Loadings PCA", loadings, "pca_loadings")

    if explained is not None:
        render_export_block("Variance expliquée PCA", explained, "pca_variance")

    if scores is None and loadings is None and explained is None:
        st.info("Aucun résultat PCA disponible pour l’export.")
        
    #
    st.markdown("### Rapport HTML")

    report_html = build_html_report(
        file_name=st.session_state.get("file_name"),
        raw_df=raw_df,
        cleaned_df=cleaned_df,
        processed_df=processed_df,
        x_cols=st.session_state.get("x_columns", []),
        meta_cols=st.session_state.get("meta_columns", []),
        preprocess_steps=st.session_state.get("preprocess_pipeline", []),
        preprocess_params=st.session_state.get("preprocess_params", {}),
        scores=scores,
        loadings=loadings,
        explained=explained,
    )
    
    st.download_button(
        label="Télécharger le rapport HTML",
        data=report_html.encode("utf-8"),
        file_name="spectralyse_report.html",
        mime="text/html",
        use_container_width=True,
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
            file_name="spectralab_exports.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    else:
        st.info("Aucun contenu disponible pour un export global.")
        
# %%
import datetime as dt
def ensure_dataframe(obj, column_name: str = "Valeur") -> pd.DataFrame | None:
    """
    Convertit un objet éventuel en DataFrame pour export/aperçu.
    """
    if obj is None:
        return None
    if isinstance(obj, pd.DataFrame):
        return obj
    if isinstance(obj, pd.Series):
        return obj.to_frame(name=obj.name or column_name)
    return pd.DataFrame(obj)


def preview_list_html(items, max_items: int = 25) -> str:
    """
    Génère une petite liste HTML avec troncature.
    """
    if not items:
        return "<p class='muted'>Aucune</p>"

    shown = items[:max_items]
    lis = "".join(f"<li>{str(x)}</li>" for x in shown)

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
        classes="report-table",
        border=0,
        escape=False,
    )

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
) -> str:
    """
    Construit un rapport HTML synthétique de l'analyse.
    """
    generated_at = dt.datetime.now().strftime("%d/%m/%Y %H:%M")

    def shape_text(df):
        if df is None:
            return "Non disponible"
        return f"{df.shape[0]} lignes × {df.shape[1]} colonnes"

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

    html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Rapport SpectraLyse</title>
<style>
    body {{
        font-family: Inter, Segoe UI, Arial, sans-serif;
        background: #F7F9FC;
        color: #1F2937;
        margin: 0;
        padding: 32px;
    }}
    .container {{
        max-width: 1200px;
        margin: 0 auto;
    }}
    h1 {{
        font-size: 2rem;
        margin-bottom: 0.25rem;
    }}
    h2 {{
        margin-top: 2rem;
        margin-bottom: 0.75rem;
        font-size: 1.45rem;
    }}
    h3 {{
        margin-top: 0;
        margin-bottom: 0.75rem;
        font-size: 1.05rem;
    }}
    p, li {{
        font-size: 0.96rem;
        line-height: 1.5;
    }}
    .muted {{
        color: #6B7280;
    }}
    .grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        margin-top: 1rem;
    }}
    .card {{
        background: white;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        padding: 18px 20px;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
        margin-bottom: 18px;
    }}
    .badge {{
        display: inline-block;
        background: #E6F4F1;
        color: #0F766E;
        padding: 6px 10px;
        border-radius: 8px;
        margin: 4px 6px 4px 0;
        font-size: 0.86rem;
        font-weight: 600;
    }}
    .kpi {{
        background: white;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        padding: 18px;
    }}
    .kpi-title {{
        color: #6B7280;
        font-size: 0.85rem;
        margin-bottom: 8px;
    }}
    .kpi-value {{
        font-size: 1.4rem;
        font-weight: 700;
        color: #0F766E;
    }}
    .report-table {{
        width: 100%;
        border-collapse: collapse;
        background: white;
        font-size: 0.92rem;
    }}
    .report-table th,
    .report-table td {{
        border: 1px solid #E5E7EB;
        padding: 8px 10px;
        text-align: left;
        vertical-align: top;
    }}
    .report-table th {{
        background: #F3F4F6;
    }}
    pre {{
        white-space: pre-wrap;
        word-break: break-word;
        background: #F8FAFC;
        border: 1px solid #E5E7EB;
        border-radius: 10px;
        padding: 12px;
    }}
</style>
</head>
<body>
<div class="container">

    <h1>Rapport SpectraLyse</h1>
    <p class="muted">Généré le {generated_at}</p>

    <div class="card">
        <h3>Informations générales</h3>
        <p><strong>Fichier actif :</strong> {file_name or "Non disponible"}</p>
        <p>
            Rapport synthétique de l'analyse incluant les jeux de données disponibles,
            la sélection des variables, le pipeline de prétraitement et les résultats PCA.
        </p>
    </div>

    <h2>Vue d’ensemble</h2>
    <div class="grid">
        <div class="kpi">
            <div class="kpi-title">Dataset brut</div>
            <div class="kpi-value">{shape_text(raw_df)}</div>
        </div>
        <div class="kpi">
            <div class="kpi-title">Dataset nettoyé</div>
            <div class="kpi-value">{shape_text(cleaned_df)}</div>
        </div>
        <div class="kpi">
            <div class="kpi-title">Dataset prétraité</div>
            <div class="kpi-value">{shape_text(processed_df)}</div>
        </div>
        <div class="kpi">
            <div class="kpi-title">Colonnes X</div>
            <div class="kpi-value">{len(x_cols)}</div>
        </div>
        <div class="kpi">
            <div class="kpi-title">Métadonnées</div>
            <div class="kpi-value">{len(meta_cols)}</div>
        </div>
        <div class="kpi">
            <div class="kpi-title">Étapes de prétraitement</div>
            <div class="kpi-value">{len(preprocess_steps)}</div>
        </div>
    </div>

    <h2>Sélection des colonnes</h2>
    <div class="card">
        <h3>Colonnes spectrales (X)</h3>
        {preview_list_html(x_cols, max_items=30)}
    </div>

    <div class="card">
        <h3>Métadonnées</h3>
        {preview_list_html(meta_cols, max_items=30)}
    </div>

    <h2>Prétraitements</h2>
    <div class="card">
        <h3>Pipeline sélectionné</h3>
        <div>{preprocess_steps_html}</div>
    </div>

    <div class="card">
        <h3>Paramètres</h3>
        {preprocess_params_html}
    </div>

    <h2>Résultats PCA</h2>
    <div class="card">
        <h3>Scores PCA</h3>
        {df_to_html_table(scores, max_rows=20)}
    </div>

    <div class="card">
        <h3>Loadings PCA</h3>
        {df_to_html_table(loadings, max_rows=20)}
    </div>

    <div class="card">
        <h3>Variance expliquée</h3>
        {df_to_html_table(explained, max_rows=20)}
    </div>

    <h2>Aperçu des données</h2>
    <div class="card">
        <h3>Dataset nettoyé</h3>
        {df_to_html_table(cleaned_df, max_rows=20)}
    </div>

    <div class="card">
        <h3>Dataset prétraité</h3>
        {df_to_html_table(processed_df, max_rows=20)}
    </div>

</div>
</body>
</html>
"""
    return html