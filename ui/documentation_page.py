# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 14:19:56 2026

@author: late_jj
"""

# ============================================================
# ui/documentation_page.py
# ============================================================
"""
Page DOCUMENTATION - version pro

Objectif :
- fournir une documentation intégrée claire et utile
- expliquer le workflow de l'application
- documenter les méthodes disponibles
- donner des bonnes pratiques d'utilisation
"""

import streamlit as st

from components.layout import page_header
from components.cards import info_card


def method_card(title: str, definition: str, objective: str, usage: str, limits: str, interpretation: str) -> None:
    """
    Affiche une fiche méthode structurée.
    """
    st.markdown(
        f"""
        <div class="card">
            <h4>{title}</h4>
            <p><strong>Définition :</strong> {definition}</p>
            <p><strong>Objectif :</strong> {objective}</p>
            <p><strong>Quand utiliser :</strong> {usage}</p>
            <p><strong>Limites :</strong> {limits}</p>
            <p><strong>Interprétation :</strong> {interpretation}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_documentation_page() -> None:
    """
    Rendu principal de la page Documentation.
    """
    page_header("Documentation", "Guide utilisateur et fiches méthodes")

    # --------------------------------------------------------
    # Introduction
    # --------------------------------------------------------
    left, right = st.columns([2.2, 1.0], gap="large")

    with left:
        st.markdown(
            """
            <div class="card">
                <h3>Bienvenue dans la documentation</h3>
                <p>
                Cette section vous aide à comprendre le fonctionnement de l’application,
                le rôle des différentes pages et les principes des méthodes utilisées
                pour l’analyse spectrale.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        info_card(
            "Conseil",
            "Commencez par la page Import & Préparation, puis poursuivez avec Spectres, Prétraitements et PCA."
        )

    # --------------------------------------------------------
    # Guide utilisateur
    # --------------------------------------------------------
    st.markdown("### 1. Guide utilisateur")

    st.markdown(
        """
        <div class="card">
            <h4>Workflow recommandé</h4>
            <ol>
                <li>Importer un fichier CSV ou Excel</li>
                <li>Définir les colonnes spectrales X et les métadonnées</li>
                <li>Diagnostiquer les valeurs manquantes</li>
                <li>Nettoyer les données</li>
                <li>Visualiser les spectres</li>
                <li>Appliquer un pipeline de prétraitement si nécessaire</li>
                <li>Explorer les données avec la PCA</li>
            </ol>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2, gap="large")

    with c1:
        info_card(
            "Page Accueil",
            "Vue synthétique du dataset actif : KPI, aperçu rapide des spectres et point d’entrée du workflow."
        )
        info_card(
            "Page Import & Préparation",
            "Chargement du fichier, sélection des colonnes spectrales, diagnostic des NA et validation du dataset."
        )
        info_card(
            "Page Spectres",
            "Visualisation interactive des spectres, coloration par variable, moyennes par groupe et statistiques simples."
        )

    with c2:
        info_card(
            "Page Prétraitements",
            "Construction et application d’un pipeline de prétraitement spectral avec comparaison avant/après."
        )
        info_card(
            "Page PCA",
            "Exploration multivariée avec score plot, variance expliquée, loadings et résumé interprétatif."
        )
        info_card(
            "Page Documentation",
            "Référence intégrée pour comprendre les méthodes, les usages et les bonnes pratiques."
        )

    # --------------------------------------------------------
    # Fiches méthodes
    # --------------------------------------------------------
    st.markdown("### 2. Documentation des méthodes")

    tab1, tab2, tab3 = st.tabs(["Prétraitements", "Exploration", "Bonnes pratiques"])

    with tab1:
        method_card(
            title="SNV (Standard Normal Variate)",
            definition="Transformation appliquée spectre par spectre, consistant à centrer puis réduire chaque spectre individuellement.",
            objective="Réduire les effets de diffusion et les variations d’échelle entre échantillons.",
            usage="Utile lorsque les spectres présentent des variations multiplicatives ou additifs liées à la granulométrie, à l’épaisseur ou à la diffusion.",
            limits="Peut amplifier le bruit si les spectres sont très instables ou de mauvaise qualité.",
            interpretation="Après SNV, les spectres sont comparables en forme relative plutôt qu’en amplitude brute."
        )

        method_card(
            title="MSC (Multiplicative Scatter Correction)",
            definition="Correction basée sur une régression linéaire de chaque spectre par rapport à une référence, souvent le spectre moyen.",
            objective="Corriger les effets multiplicatifs et additifs de diffusion.",
            usage="Particulièrement utile pour les données NIR où les effets physiques perturbent l’intensité globale.",
            limits="Le choix implicite de la référence influence le résultat ; la méthode n’est pas toujours idéale pour tous les jeux de données.",
            interpretation="Les spectres corrigés sont davantage alignés sur une structure chimique commune."
        )

        method_card(
            title="Savitzky-Golay",
            definition="Filtre polynomial local utilisé pour lisser les spectres et/ou calculer des dérivées.",
            objective="Réduire le bruit et améliorer la résolution des bandes spectrales.",
            usage="Utile avant PCA lorsque l’on veut mieux mettre en évidence certaines structures fines.",
            limits="Des paramètres mal choisis peuvent lisser excessivement ou déformer le signal.",
            interpretation="La dérivée première aide souvent à corriger la ligne de base ; la dérivée seconde accentue les détails fins mais peut augmenter le bruit."
        )

        method_card(
            title="Normalisation",
            definition="Transformation ramenant les spectres à une échelle comparable selon une norme donnée (L1, L2 ou max).",
            objective="Limiter l’influence des différences globales d’amplitude.",
            usage="Utile lorsque l’intensité absolue est moins importante que la forme du spectre.",
            limits="Peut masquer des variations d’amplitude réellement informatives.",
            interpretation="Les spectres sont comparés sur une base plus relative qu’absolue."
        )

    with tab2:
        method_card(
            title="PCA (Principal Component Analysis)",
            definition="Méthode de réduction de dimension qui projette les données dans un espace de plus faible dimension en maximisant la variance expliquée.",
            objective="Explorer la structure des données, détecter des groupes, tendances ou atypiques.",
            usage="Très utile comme première analyse exploratoire sur des données spectrales nettoyées et éventuellement prétraitées.",
            limits="Méthode linéaire : elle ne capture pas toutes les structures non linéaires possibles.",
            interpretation="Les scores représentent les échantillons dans l’espace réduit ; les loadings indiquent quelles variables spectrales contribuent aux composantes."
        )

    with tab3:
        st.markdown(
            """
            <div class="card">
                <h4>Bonnes pratiques</h4>
                <ul>
                    <li>Vérifiez toujours les valeurs manquantes avant d’aller vers l’analyse.</li>
                    <li>Ne multipliez pas les prétraitements sans justification scientifique.</li>
                    <li>Comparez systématiquement les spectres avant et après prétraitement.</li>
                    <li>Interprétez les loadings avec prudence : une contribution forte n’implique pas automatiquement une causalité chimique directe.</li>
                    <li>Regardez les atypiques potentiels avant de conclure sur une structure de groupes.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # --------------------------------------------------------
    # FAQ rapide
    # --------------------------------------------------------
    st.markdown("### 3. Questions fréquentes")

    with st.expander("Comment choisir les colonnes spectrales ?"):
        st.write(
            "Le mode Plage ou Regex est souvent le plus efficace lorsque les longueurs d’onde sont codées dans les noms de colonnes."
        )

    with st.expander("Pourquoi prétraiter les spectres ?"):
        st.write(
            "Les prétraitements aident à corriger des effets physiques ou instrumentaux pour mieux révéler l’information chimique utile."
        )

    with st.expander("Pourquoi la PCA ne montre-t-elle pas toujours des groupes nets ?"):
        st.write(
            "Parce que la PCA est une méthode exploratoire linéaire. L’absence de groupes nets peut refléter une réalité du dataset, un bruit important ou un besoin de prétraitement différent."
        )

    # --------------------------------------------------------
    # Liens utiles
    # --------------------------------------------------------
    st.markdown("### 4. Liens utiles")

    st.markdown(
        """
        <div class="card">
            <ul>
                <li>Scikit-learn : PCA</li>
                <li>SciPy : Savitzky-Golay</li>
                <li>Plotly Python</li>
                <li>Streamlit Documentation</li>
                <li>Documentation générale sur la chimiométrie et l’analyse spectrale</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )