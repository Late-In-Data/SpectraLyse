# ============================================================
# app.py
# ============================================================
"""
Point d’entrée principal de l’application Streamlit.

Responsabilités :
- configurer Streamlit
- initialiser le session_state
- charger le style global
- afficher la sidebar
- router vers les pages UI

Important :
- st.set_page_config() doit être le premier appel Streamlit
- les imports des pages sont faits dans main() pour éviter
  les erreurs de type StreamlitSetPageConfigMustBeFirstCommandError
"""

import streamlit as st

# IMPORTANT : premier appel Streamlit de toute l'application
st.set_page_config(
    page_title="SpectraLyse",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

def init_session_state() -> None:
    """
    Initialise les variables globales de session.
    """
    defaults = {
        "raw_df": None,
        "cleaned_df": None,
        "processed_df": None,
        "x_columns": [],
        "meta_columns": [],
        "preprocess_pipeline": [],
        "preprocess_params": {
            "savgol_window": 11,
            "savgol_polyorder": 2,
            "savgol_deriv": 1,
            "normalization_method": "l2",
        },
        "reduction_results": {},
        "file_name": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def main() -> None:
    """
    Fonction principale de l'application.
    """
    # Imports ici pour éviter les appels Streamlit prématurés
    from components.layout import load_css
    from components.sidebar import render_sidebar

    from ui.home_page import render_home_page
    from ui.import_page import render_import_page
    from ui.spectra_page import render_spectra_page
    from ui.preprocessing_page import render_preprocessing_page
    from ui.pca_page import render_pca_page
    from ui.documentation_page import render_documentation_page
    from ui.author_page import render_author_page
    from ui.export_page import render_export_page

    init_session_state()
    load_css()

    page = render_sidebar()

    if page == "Accueil":
        render_home_page()

    elif page == "Import":
        render_import_page()

    elif page == "Spectres":
        render_spectra_page()

    elif page == "Prétraitements":
        render_preprocessing_page()

    elif page == "PCA":
        render_pca_page()
    
    elif page == "Export":
        render_export_page()

    elif page == "Documentation":
        render_documentation_page()

    elif page == "Auteur & Contact":
        render_author_page()

if __name__ == "__main__":
    main()