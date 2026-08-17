# Provenance des données de démonstration

`demo_cereals_nirs.csv` est dérivé de données réelles publiées par le
projet **sensAIfood** — spectres proche infrarouge (NIR) de céréales
avec valeurs de référence de laboratoire.

- **Sous-ensemble utilisé** : "Perten set" (orge, maïs, blé — 150 échantillons
  par espèce, 950-1650 nm, protéine et humidité mesurées en laboratoire)
- **Source** : Zenodo, DOI [10.5281/zenodo.15838136](https://zenodo.org/records/15838136)
- **Auteur des données** : Dr. Martin Lagerholm (Perten/PerkinElmer), collectées
  sur plusieurs spectromètres, années et pays, dans le cadre du projet
  sensAIfood (COST Action IG19145)
- **Licence** : CC BY 4.0 (Creative Commons Attribution 4.0 International)

Les fichiers bruts (un par espèce, tels que publiés) sont dans
`data/raw/sensAIfood_perten/`. Le fichier `demo_cereals_nirs.csv` est
généré à partir de ces fichiers par `scripts/prepare_demo_dataset.py`,
qui fusionne les 3 espèces et convertit les valeurs manquantes du jeu de
données source (codées `0`/`"Unknown"`) en NaN.
