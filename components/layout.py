# ============================================================
# components/layout.py
# ============================================================
"""
Composants de layout réutilisables.

Responsabilités :
- chargement CSS
- headers de page
- sections visuelles
"""

import streamlit as st


def load_css() -> None:
    """
    Charge le fichier CSS global.
    """
    try:
        with open("assets/style.css", "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        # L'application continue même si le CSS n'est pas encore présent
        pass


def page_header(title: str, subtitle: str | None = None) -> None:
    """
    Header standardisé pour les pages.
    """
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)


def section(title: str) -> None:
    """
    Titre de section standardisé.
    """
    st.markdown(f"### {title}")