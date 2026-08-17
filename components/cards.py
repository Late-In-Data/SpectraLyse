# ============================================================
# components/cards.py
# ============================================================
"""
Composants visuels de type cartes.

Responsabilités :
- cartes KPI
- cartes d'information
- cartes pour graphiques
"""

import streamlit as st


def kpi_card(title: str, value) -> None:
    """
    Affiche une carte KPI.
    """
    st.markdown(
        f"""
        <div class="card kpi">
            <div class="kpi-value">{value}</div>
            <div class="kpi-label">{title}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def info_card(title: str, content: str) -> None:
    """
    Affiche une carte d'information simple.
    """
    st.markdown(
        f"""
        <div class="card">
            <h4>{title}</h4>
            <p>{content}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def plot_card(fig) -> None:
    """
    Affiche une figure Plotly dans une carte visuelle.
    """
    st.markdown('<div class="plot-card">', unsafe_allow_html=True)
    st.plotly_chart(fig, width="stretch")
    st.markdown("</div>", unsafe_allow_html=True)