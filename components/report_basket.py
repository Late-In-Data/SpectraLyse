# ============================================================
# components/report_basket.py
# ============================================================
"""
Panier de figures pour le rapport HTML.

Objectif :
- permettre à l'utilisateur de sauvegarder, depuis n'importe quelle page,
  une figure exactement comme il l'a configurée (couleur, symbole,
  prétraitement appliqué...), potentiellement plusieurs fois avec des
  réglages différents ;
- le rapport affiche ensuite ces figures sauvegardées, plutôt que de
  deviner une configuration automatiquement.

Chaque entrée est un dict : {id, section, label, html}. `section` sert à
regrouper les figures par partie du rapport ("pca", "pretraitement",
"spectres"). `html` est un fragment Plotly déjà rendu
(include_plotlyjs=False, la librairie étant chargée une seule fois dans
le <head> du rapport).
"""

from typing import List, Dict

import streamlit as st


def add_figure_to_report(section: str, label: str, html_fragment: str) -> None:
    """
    Ajoute une figure au panier. N'écrase rien : plusieurs figures peuvent
    coexister pour une même section (ex. deux prétraitements différents).
    """
    next_id = st.session_state.get("_report_figure_next_id", 0)
    st.session_state.report_figures.append({
        "id": next_id,
        "section": section,
        "label": label,
        "html": html_fragment,
    })
    st.session_state["_report_figure_next_id"] = next_id + 1


def get_figures(section: str) -> List[Dict]:
    return [f for f in st.session_state.get("report_figures", []) if f["section"] == section]


def remove_figure(figure_id: int) -> None:
    st.session_state.report_figures = [
        f for f in st.session_state.get("report_figures", []) if f["id"] != figure_id
    ]


def render_add_button(section: str, label: str, build_html) -> None:
    """
    Bouton générique "Ajouter au rapport". `build_html` est appelé
    uniquement au clic (pas à chaque rerun) pour éviter de reconstruire
    la figure inutilement.
    """
    if st.button(f"Ajouter au rapport : {label}", key=f"add_report_{section}_{label}"):
        add_figure_to_report(section, label, build_html())
        st.success(f"Ajouté au rapport : {label}")


def render_basket_summary(section: str, section_title: str) -> None:
    """
    Liste les figures déjà sauvegardées pour une section, avec suppression.
    À utiliser sur la page Export.
    """
    entries = get_figures(section)

    if not entries:
        st.caption(f"Aucune figure « {section_title} » ajoutée pour l'instant.")
        return

    for entry in entries:
        col_label, col_delete = st.columns([5, 1])
        with col_label:
            st.write(f"• {entry['label']}")
        with col_delete:
            if st.button("Retirer", key=f"remove_report_fig_{entry['id']}"):
                remove_figure(entry["id"])
                st.rerun()
