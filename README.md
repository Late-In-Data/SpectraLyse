# SpectraLyse

Application Streamlit pour l'exploration et le prétraitement de données spectrales proche infrarouge (NIRS), orientée analyse chimiométrique.

## À propos

SpectraLyse couvre le flux de travail complet d'une analyse NIRS : import et nettoyage des données, visualisation des spectres, prétraitement, exploration par analyse en composantes principales (PCA) et export des résultats.

L'application guide chaque étape avec un diagnostic explicite des valeurs manquantes, une sélection assistée des colonnes spectrales et une comparaison visuelle avant/après prétraitement, plutôt que de se limiter à des sorties brutes.

## Fonctionnalités

- Import de fichiers CSV ou Excel, avec détection automatique du séparateur et des colonnes spectrales
- Diagnostic et nettoyage des valeurs manquantes, avec plusieurs stratégies au choix
- Visualisation interactive des spectres : filtrage par métadonnées, plage spectrale, moyennes par groupe
- Pipeline de prétraitement configurable : SNV, MSC, Savitzky-Golay, normalisation L1/L2/max
- PCA avec score plot, variance expliquée, loadings et résumé interprétatif
- Export des données et résultats en CSV, Excel et rapport HTML autonome
- Documentation intégrée détaillant chaque méthode (définition, usage, limites, interprétation)

## Structure du projet

```
core/         logique métier (chargement, prétraitement, PCA), indépendante de Streamlit
ui/           pages de l'application
components/   éléments d'interface réutilisables (cartes, mise en page, graphiques)
tests/        tests unitaires (pytest) sur core/
scripts/      préparation du jeu de données de démonstration
data/         jeu de données de démonstration et données brutes associées
```

## Installation

Nécessite Python 3.11 ou plus récent.

```bash
pip install -r requirements.txt
```

## Lancement

```bash
streamlit run app.py
```

L'application s'ouvre sur http://localhost:8501. La page Import propose un jeu de données de démonstration à charger directement, sans préparation préalable : des spectres NIR réels d'orge, de maïs et de blé, avec valeurs de protéine et d'humidité mesurées en laboratoire.

## Tests

```bash
pytest
```

## Jeu de données de démonstration

Le jeu de données fourni provient du projet sensAIfood (spectres NIR de céréales), sous licence CC BY 4.0. Voir [data/SOURCE.md](data/SOURCE.md) pour l'attribution complète et l'origine des fichiers.

## Technologies

Python, Streamlit, Plotly, pandas, NumPy, SciPy, scikit-learn.
