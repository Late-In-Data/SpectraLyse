# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 12:16:30 2026

@author: late_jj
"""

import streamlit as st

# DOIT être le premier appel Streamlit de toute l'application
st.set_page_config(
    page_title="Spectral Analysis App",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_session_state():
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


def render_sidebar():
    st.sidebar.title("🧭 Navigation")

    page = st.sidebar.radio(
        "Pages",
        ["Import", "Spectres", "Prétraitements", "PCA"],
    )

    st.sidebar.divider()
    st.sidebar.markdown("## 📊 Dataset")

    if st.session_state.raw_df is None:
        st.sidebar.info("Aucune donnée chargée")
    else:
        st.sidebar.success("Données chargées")

        if st.session_state.cleaned_df is not None:
            st.sidebar.write(f"Clean: {st.session_state.cleaned_df.shape}")

        if st.session_state.processed_df is not None:
            st.sidebar.write("Prétraité ✔️")

        st.sidebar.write(f"X: {len(st.session_state.x_columns)}")
        st.sidebar.write(f"Meta: {len(st.session_state.meta_columns)}")

    return page


def main():
    # imports ici pour éviter tout appel Streamlit prématuré
    from ui.import_page import render_import_page
    from ui.spectra_page import render_spectra_page
    from ui.preprocessing_page import render_preprocessing_page
    from ui.pca_page import render_pca_page

    init_session_state()
    page = render_sidebar()

    if page == "Import":
        render_import_page()
    elif page == "Spectres":
        render_spectra_page()
    elif page == "Prétraitements":
        render_preprocessing_page()
    elif page == "PCA":
        render_pca_page()


if __name__ == "__main__":
    main()