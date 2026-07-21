# -*- coding: utf-8 -*-
"""
Génère un jeu de données NIRS synthétique pour la démo de SpectraLyse.

Contexte simulé : essai agronomique sur blé.
Facteurs : Variété (3), Fertilisation azotée (3), Irrigation (2), Bloc (5 répétitions).
Cibles chimiques simulées : Protéine (%) et Humidité (%).

Objectif du design : que les facteurs agronomiques ressortent clairement en
PCA (pour une démo pédagogique), avec des effets physiques (diffusion,
offset) modérés pour rester réalistes sans noyer le signal.

Colonnes fictives ajoutées avec valeurs manquantes (pour démontrer le
nettoyage de données sur la page Import) :
- Commentaire_Terrain : colonne entièrement vide (100% NA)
- Capteur_Secondaire   : colonne partiellement renseignée (~35% NA)
"""

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)

# ------------------------------------------------------------
# Plan d'expérience
# ------------------------------------------------------------
varietes = ["Apache", "Rubisko", "Fructidor"]
fertilisations = ["N0", "N90", "N180"]  # kg N/ha
irrigations = ["Pluvial", "Irrigué"]
n_blocs = 5

rows = []
for variete in varietes:
    for fert in fertilisations:
        for irrig in irrigations:
            for bloc in range(1, n_blocs + 1):
                rows.append({
                    "Variete": variete,
                    "Fertilisation": fert,
                    "Irrigation": irrig,
                    "Bloc": f"B{bloc}",
                })

plan = pd.DataFrame(rows)
n_samples = len(plan)  # 3*3*2*5 = 90

# ------------------------------------------------------------
# Cibles chimiques de référence (fortement corrélées aux facteurs
# pour une démo pédagogique lisible)
# ------------------------------------------------------------
fert_effect = {"N0": -2.6, "N90": 0.0, "N180": 3.0}
variete_effect_prot = {"Apache": -0.4, "Rubisko": 0.6, "Fructidor": 0.1}
irrig_effect_humidite = {"Pluvial": -2.2, "Irrigué": 2.4}
variete_effect_humidite = {"Apache": 0.3, "Rubisko": -0.2, "Fructidor": 0.0}

proteine = (
    11.5
    + plan["Fertilisation"].map(fert_effect)
    + plan["Variete"].map(variete_effect_prot)
    + rng.normal(0, 0.25, n_samples)
).round(2)

humidite = (
    12.0
    + plan["Irrigation"].map(irrig_effect_humidite)
    + plan["Variete"].map(variete_effect_humidite)
    + rng.normal(0, 0.20, n_samples)
).round(2)

plan["Proteine"] = proteine
plan["Humidite"] = humidite
plan.insert(0, "Echantillon_ID", [f"ECH{idx+1:03d}" for idx in range(n_samples)])

# ------------------------------------------------------------
# Génération des spectres NIR synthétiques
# ------------------------------------------------------------
wavelengths = np.arange(950, 1651, 4)  # ~176 variables
n_vars = len(wavelengths)


def gaussian_band(wl, center, width, amplitude):
    return amplitude * np.exp(-0.5 * ((wl - center) / width) ** 2)


# Ligne de base "typique" d'un spectre NIR de grain (forme lissée)
baseline = (
    0.35
    + 0.15 * np.exp(-0.5 * ((wavelengths - 1100) / 250) ** 2)
    + 0.10 * np.exp(-0.5 * ((wavelengths - 1550) / 200) ** 2)
)

# Signature spectrale distincte par variété : décalage global + bosse
# large centrée sur une zone différente pour chaque variété (texture
# structurelle, indépendante de la chimie), avec une amplitude nette.
variete_signature = {
    "Apache":    {"offset": -0.05, "center": 1050, "width": 60, "amp": 0.05},
    "Rubisko":   {"offset": 0.04,  "center": 1300, "width": 60, "amp": -0.045},
    "Fructidor": {"offset": 0.00,  "center": 1550, "width": 60, "amp": 0.05},
}

# Signature spectrale distincte par niveau de fertilisation : bande
# d'identité centrée sur une zone dédiée (980 nm), séparée des bandes
# variété et des bandes chimiques, pour bien isoler l'effet en PCA.
fertilisation_signature = {
    "N0":   {"center": 980, "width": 30, "amp": -0.05},
    "N90":  {"center": 980, "width": 30, "amp": 0.0},
    "N180": {"center": 980, "width": 30, "amp": 0.05},
}

spectra = np.zeros((n_samples, n_vars))

for i, row in plan.iterrows():
    spec = baseline.copy()

    sig = variete_signature[row["Variete"]]
    spec = spec + sig["offset"]
    spec += gaussian_band(wavelengths, center=sig["center"], width=sig["width"], amplitude=sig["amp"])

    fert_sig = fertilisation_signature[row["Fertilisation"]]
    spec += gaussian_band(wavelengths, center=fert_sig["center"], width=fert_sig["width"], amplitude=fert_sig["amp"])

    # Bande protéine (1er harmonique N-H, ~1200 nm) — marquée par la fertilisation
    spec += gaussian_band(wavelengths, center=1200, width=25, amplitude=0.035 * row["Proteine"])

    # Bande humidité (1er harmonique O-H, ~1450 nm) — marquée par l'irrigation
    spec += gaussian_band(wavelengths, center=1450, width=30, amplitude=0.045 * row["Humidite"])

    # Effets physiques modérés : diffusion multiplicative + offset additif
    # (volontairement réduits pour ne pas noyer le signal agronomique)
    slope = rng.normal(1.0, 0.025)
    intercept = rng.normal(0.0, 0.008)
    spec = spec * slope + intercept

    # Bruit instrumental
    spec += rng.normal(0, 0.003, n_vars)

    spectra[i, :] = spec

spectra_df = pd.DataFrame(spectra, columns=[str(w) for w in wavelengths])

# ------------------------------------------------------------
# Assemblage + colonnes fictives avec NA (démo du nettoyage)
# ------------------------------------------------------------
demo_df = pd.concat([plan.reset_index(drop=True), spectra_df], axis=1)

# Colonne entièrement vide -> doit être supprimée automatiquement
demo_df["Commentaire_Terrain"] = np.nan

# Colonne partiellement renseignée (~35% manquant) -> à traiter via une
# stratégie de nettoyage (seuil de NA ou suppression de lignes)
capteur = rng.normal(20, 2, n_samples).round(2)
na_mask = rng.random(n_samples) < 0.35
capteur = capteur.astype(object)
capteur[na_mask] = np.nan
demo_df["Capteur_Secondaire"] = capteur

demo_df = demo_df.sample(frac=1.0, random_state=7).reset_index(drop=True)  # mélange des lignes

output_path = "data/demo_ble_nirs.csv"
demo_df.to_csv(output_path, index=False)

print("Shape:", demo_df.shape)
print("Colonnes non spectrales:", [c for c in demo_df.columns if c not in spectra_df.columns])
print("NA Commentaire_Terrain:", demo_df["Commentaire_Terrain"].isna().sum(), "/", n_samples)
print("NA Capteur_Secondaire:", demo_df["Capteur_Secondaire"].isna().sum(), "/", n_samples)
