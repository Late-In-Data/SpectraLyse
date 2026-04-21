# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 11:58:07 2026

@author: late_jj
"""

# ============================================================
# app.py
# ============================================================
"""
Application principale Streamlit pour l'analyse spectrale.

Rôle :
- initialiser l'application
- gérer la navigation
- router vers les pages
- gérer l'état global

Architecture :
- UI séparée dans /ui
- logique dans /core
- utilitaires dans /utils
"""

import streamlit as st
# ============================================================
# CONFIGURATION STREAMLIT
# ============================================================

# IMPORTANT :
# set_page_config doit être le tout premier appel Streamlit
st.set_page_config(
    page_title="Spectral Analysis App",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Import des pages APRES set_page_config
from ui.import_page import render_import_page
from ui.spectra_page import render_spectra_page
from ui.preprocessing_page import render_preprocessing_page
from ui.pca_page import render_pca_page

# ============================================================
# INITIALISATION SESSION STATE
# ============================================================

def init_session_state():
    """
    Initialise toutes les variables globales utilisées dans l'application.
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


# ============================================================
# SIDEBAR
# ============================================================

def render_sidebar():
    """
    Affiche la sidebar avec navigation + état dataset.
    """

    st.sidebar.title("🧭 Navigation")

    page = st.sidebar.radio(
        "Pages",
        [
            "Import",
            "Spectres",
            "Prétraitements",
            "PCA",
        ],
    )

    st.sidebar.divider()

    st.sidebar.markdown("## 📊 Dataset")

    if st.session_state.raw_df is None:
        st.sidebar.info("Aucune donnée chargée")
    else:
        st.sidebar.success("Données chargées")

        if st.session_state.cleaned_df is not None:
            st.sidebar.write(
                f"Clean: {st.session_state.cleaned_df.shape}"
            )

        if st.session_state.processed_df is not None:
            st.sidebar.write("Prétraité ✔️")

        st.sidebar.write(f"X: {len(st.session_state.x_columns)}")
        st.sidebar.write(f"Meta: {len(st.session_state.meta_columns)}")

    return page


# ============================================================
# ROUTING
# ============================================================

def main():
    """
    Fonction principale.
    """

    init_session_state()

    page = render_sidebar()

    # Routing vers les pages
    if page == "Import":
        render_import_page()

    elif page == "Spectres":
        render_spectra_page()

    elif page == "Prétraitements":
        render_preprocessing_page()

    elif page == "PCA":
        render_pca_page()


# ============================================================
# EXECUTION
# ============================================================

if __name__ == "__main__":
    main()
    
    
    
