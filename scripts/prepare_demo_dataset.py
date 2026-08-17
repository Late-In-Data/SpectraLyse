# -*- coding: utf-8 -*-
"""
Prépare le jeu de données de démonstration de SpectraLyse à partir de
données NIR réelles (spectromètre Perten, projet sensAIfood).

Source : sensAIfood cereal NIR data (Perten set) — orge, maïs, blé,
150 échantillons par espèce, référence protéine/humidité réelle.
Zenodo, DOI 10.5281/zenodo.15838136, licence CC BY 4.0.
Voir data/SOURCE.md pour l'attribution complète.

Ce script :
- fusionne les 3 fichiers bruts (data/raw/sensAIfood_perten/) en un seul
  dataset multi-espèces,
- convertit les placeholders de valeur manquante du jeu de données source
  (Year = 0, Spectrometer/Country = "0", Variety = "Unknown") en vraies
  valeurs manquantes (NaN), pour que le diagnostic de NA de l'application
  reflète la réalité du jeu de données plutôt que ces conventions internes.
"""

import pandas as pd

RAW_DIR = "data/raw/sensAIfood_perten"
FILES = [
    "Barley_sensAIfood_Perten.csv",
    "Corn_sensAIfood_Perten.csv",
    "Wheat_sensAIfood_Perten.csv",
]
OUTPUT_PATH = "data/demo_cereals_nirs.csv"


def clean_species_file(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    df["Year"] = df["Year"].replace(0, pd.NA)
    df["Spectrometer"] = df["Spectrometer"].replace("0", pd.NA)
    df["Country"] = df["Country"].replace("0", pd.NA)
    df["Variety"] = df["Variety"].replace("Unknown", pd.NA)

    return df


def main() -> None:
    dfs = [clean_species_file(f"{RAW_DIR}/{f}") for f in FILES]
    merged = pd.concat(dfs, axis=0, ignore_index=True)

    merged.to_csv(OUTPUT_PATH, index=False)

    print("Shape:", merged.shape)
    print("Espèces:", merged["Cereal"].value_counts().to_dict())
    print("NA par colonne (métadonnées) :")
    print(merged[["Spectrometer", "Variety", "Country", "Year"]].isna().sum())


if __name__ == "__main__":
    main()
