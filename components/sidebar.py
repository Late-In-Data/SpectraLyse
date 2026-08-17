# ============================================================
# components/sidebar.py
# ============================================================

"""
Sidebar principale de l'application.

Responsabilités :
- navigation
- état rapide du dataset
- affichage du branding
"""

import os
import streamlit as st

from core.version import APP_VERSION


def render_sidebar() -> str:
    """
    Affiche la sidebar et retourne la page sélectionnée.
    Gère aussi la navigation pilotée par st.session_state["nav_page"].
    """

    pages = [
        "Accueil",
        "Import",
        "Spectres",
        "Prétraitements",
        "PCA",
        "Export",
        "Documentation",
        "Auteur & Contact",
    ]

    # --------------------------------------------------------
    # Branding
    # --------------------------------------------------------
    if os.path.exists("assets/logo.png"):
        st.sidebar.image("assets/logo.png", width="stretch")

    st.sidebar.markdown("### Navigation")

    # --------------------------------------------------------
    # Gestion de la page active
    # --------------------------------------------------------
    if "nav_page" not in st.session_state:
        st.session_state["nav_page"] = "Accueil"

    current_page = st.session_state["nav_page"]
    if current_page not in pages:
        current_page = "Accueil"
        st.session_state["nav_page"] = "Accueil"

    selected_page = st.sidebar.radio(
        "Navigation",
        pages,
        index=pages.index(current_page),
        label_visibility="collapsed",
        key="sidebar_radio_page",
    )

    # Synchronisation de l'état
    st.session_state["nav_page"] = selected_page

    # --------------------------------------------------------
    # État du dataset
    # --------------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.markdown("### État du dataset")

    raw_df = st.session_state.get("raw_df")
    cleaned_df = st.session_state.get("cleaned_df")
    processed_df = st.session_state.get("processed_df")

    if raw_df is None:
        st.sidebar.info("Aucune donnée chargée")
    else:
        st.sidebar.success("Données chargées")

        file_name = st.session_state.get("file_name")
        if file_name:
            st.sidebar.write(f"**Fichier :** {file_name}")

        st.sidebar.write(f"**Colonnes X :** {len(st.session_state.get('x_columns', []))}")
        st.sidebar.write(f"**Métadonnées :** {len(st.session_state.get('meta_columns', []))}")

        if cleaned_df is not None:
            st.sidebar.write(f"**Dataset validé :** {cleaned_df.shape[0]} × {cleaned_df.shape[1]}")

        if processed_df is not None:
            st.sidebar.write("**Prétraitement :** appliqué")
        else:
            st.sidebar.write("**Prétraitement :** non appliqué")

    st.sidebar.markdown("---")
    st.sidebar.caption(f"SpectraLyse • v{APP_VERSION}")

    return selected_page