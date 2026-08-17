# ============================================================
# ui/author_page.py
# ============================================================
"""
Page AUTEUR / CONTACT / FEEDBACK

Objectif :
- présenter l’application
- présenter l’auteur
- fournir des liens de contact réels
- rediriger les retours vers Google Form / LinkedIn / email
"""

import streamlit as st

from components.layout import page_header


def render_author_page() -> None:
    page_header("Auteur & Contact", "Présentation de l’auteur, contacts et retours utilisateurs")

    # --------------------------------------------------------
    # Auteur
    # --------------------------------------------------------
    st.markdown("### Auteur")

    st.markdown(
        """
<div class="card">
    <h3>Laté LAWSON</h3>
    <p><strong>Data Scientist</strong></p>
    <p>
        Je travaille sur l’ensemble du cycle de la donnée — exploration, préparation,
        modélisation et visualisation interactive — avec un souci de rendre ces analyses
        accessibles et exploitables.
    </p>
    <p>
        Ce projet illustre cette approche sur un cas concret : l’analyse de données
        spectrales (chimiométrie).
    </p>
</div>
""",
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # Contact
    # --------------------------------------------------------
    st.markdown("### Contact")

    c1, c2, c3 = st.columns(3, gap="large")

    with c1:
        st.markdown(
            """
<div class="card">
    <h4>📧 Email</h4>
    <p>
        <a href="mailto:latejeanjacques@gmail.com">
            latejeanjacques@gmail.com
        </a>
    </p>
    <p>Pour toute question, échange ou prise de contact directe.</p>
</div>
""",
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            """
<div class="card">
    <h4>💼 LinkedIn</h4>
    <p>
        <a href="https://www.linkedin.com/in/lat%C3%A9-lawson-452674218/" target="_blank">
            Voir mon profil LinkedIn
        </a>
    </p>
    <p>Présentation professionnelle, parcours et réseau.</p>
</div>
""",
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            """
<div class="card">
    <h4>📝 Feedback</h4>
    <p>
        <a href="https://docs.google.com/forms/d/e/1FAIpQLScMFp4vCwyoJb1SF5XM1NhjGSFHZahatHjMq2ifXFZB1ERwEQ/viewform?usp=dialog" target="_blank">
            Ouvrir le formulaire de feedback
        </a>
    </p>
    <p>Signaler un bug, proposer une idée ou suggérer une amélioration.</p>
</div>
""",
            unsafe_allow_html=True,
        )

    # --------------------------------------------------------
    # Retour utilisateur
    # --------------------------------------------------------
    st.markdown("### Retour utilisateur")

    st.markdown(
        """
<div class="card">
    <p>Vous pouvez utiliser le formulaire pour transmettre :</p>
    <ul>
        <li>des bugs ou comportements inattendus,</li>
        <li>des idées d’amélioration UX/UI,</li>
        <li>des besoins métiers ou scientifiques,</li>
        <li>des suggestions de nouvelles fonctionnalités.</li>
    </ul>
    <p>Les retours permettent d’améliorer progressivement l’application.</p>
</div>
""",
        unsafe_allow_html=True,
    )
