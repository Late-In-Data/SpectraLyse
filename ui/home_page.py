# # ============================================================
# # ui/home_page.py
# # ============================================================

# """
# Page ACCUEIL - version vitrine / orientation

# Objectif :
# - présenter SpectraLyse
# - montrer les fonctionnalités clés
# - illustrer le workflow utilisateur
# - afficher quelques visuels d'exemple
# - éviter de dupliquer la logique de la page Import
# """

import streamlit as st
from components.layout import page_header
from components.cards import info_card

def render_feature_card(title: str, description: str, icon: str = "🔹"):
    st.markdown(
        f"""
<div class="card">
    <h4>{icon} {title}</h4>
    <p>{description}</p>
</div>
""",
        unsafe_allow_html=True,
    )

def render_step_card(number: int, title: str, description: str):
    st.markdown(
        f"""
<div class="card">
    <h4>Étape {number} - {title}</h4>
    <p>{description}</p>
</div>
""",
        unsafe_allow_html=True,
    )

def render_home_page():
    page_header(
        "SpectraLyse",
        "Plateforme d’analyse spectrale, de prétraitement et d’exploration chimiométrique",
    )

    # --------------------------------------------------------
    # Introduction
    # --------------------------------------------------------
    st.markdown(
        """
<div class="card">
    <p>
        SpectraLyse est une application conçue pour faciliter l’analyse de données spectrales
        dans un environnement scientifique clair, lisible et cohérent.
    </p>
    <p>
        Elle permet de préparer les jeux de données, visualiser les spectres,
        appliquer des prétraitements, explorer la structure des données par PCA
        et exporter les résultats utiles.
    </p>
</div>
""",
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # Infos rapides
    # --------------------------------------------------------
    st.markdown("### Informations")

    i1, i2, i3 = st.columns(3, gap="large")
    with i1:
        info_card("Version", "v0.1")
    with i2:
        info_card("Statut", "Application en développement actif")
    with i3:
        info_card("Orientation", "Analyse spectrale / chimiométrie / data science")

    # --------------------------------------------------------
    # Fonctionnalités
    # --------------------------------------------------------
    st.markdown("### Fonctionnalités principales")

    f1, f2, f3, f4 = st.columns(4, gap="large")

    with f1:
        render_feature_card(
            "Visualiser les spectres",
            "Tracer les spectres, filtrer par métadonnées, sélectionner une plage spectrale et comparer visuellement les profils.",
            "📈",
        )

    with f2:
        render_feature_card(
            "Prétraiter les données",
            "Appliquer SNV, MSC, Savitzky-Golay et normalisation dans un pipeline configurable.",
            "⚙️",
        )

    with f3:
        render_feature_card(
            "Explorer par PCA",
            "Étudier la structure des données, visualiser les scores, les loadings et les variables contributives.",
            "🧭",
        )

    with f4:
        render_feature_card(
            "Exporter les résultats",
            "Télécharger les jeux de données intermédiaires et les résultats d’analyse.",
            "📦",
        )

    # --------------------------------------------------------
    # Workflow
    # --------------------------------------------------------
    st.markdown("### Workflow")

    w1, w2, w3 = st.columns(3, gap="large")

    with w1:
        render_step_card(
            1,
            "Importer et préparer",
            "Chargez un fichier CSV ou Excel, définissez les variables spectrales et les métadonnées, puis nettoyez le dataset.",
        )

    with w2:
        render_step_card(
            2,
            "Visualiser et prétraiter",
            "Examinez les spectres, filtrez selon les métadonnées et testez différents prétraitements avant l’analyse.",
        )

    with w3:
        render_step_card(
            3,
            "Explorer et exporter",
            "Lancez la PCA, interprétez les résultats et exportez les tables utiles pour votre travail scientifique.",
        )

    # --------------------------------------------------------
    # Cas d’usage
    # --------------------------------------------------------
    st.markdown("### Cas d’usage")

    u1, u2 = st.columns(2, gap="large")

    with u1:
        st.markdown(
            """
<div class="card">
    <h4>Applications possibles</h4>
    <ul>
        <li>Analyse exploratoire de jeux de données spectraux</li>
        <li>Comparaison de lots, groupes ou variétés</li>
        <li>Étude de l’effet de prétraitements spectraux</li>
        <li>Préparation avant modélisation supervisée</li>
    </ul>
</div>
""",
            unsafe_allow_html=True,
        )

    with u2:
        st.markdown(
            """
<div class="card">
    <h4>Public visé</h4>
    <p>
        L’application s’adresse aux utilisateurs qui souhaitent structurer
        leur exploration de données spectrales dans une interface simple,
        cohérente et orientée analyse scientifique.
    </p>
</div>
""",
            unsafe_allow_html=True,
        )