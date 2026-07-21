# -*- coding: utf-8 -*-
"""
Génère un jeu de données NIRS synthétique pour la démo de SpectraLyse.

Contexte simulé : essai agronomique sur blé.
Facteurs : Variété (3), Fertilisation azotée (3), Irrigation (2), Bloc (5 répétitions).
Cibles chimiques simulées : Protéine (%) et Humidité (%).
Spectres : NIR 950-1650 nm (pas de 4 nm), avec effets physiques
(diffusion multiplicative, offset additif, bruit) pour rendre les
prétraitements (SNV/MSC) visuellement pertinents, + quelques atypiques.
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
# Cibles chimiques de référence (corrélées aux facteurs)
# ------------------------------------------------------------
fert_effect = {"N0": -1.2, "N90": 0.0, "N180": 1.4}
variete_effect_prot = {"Apache": -0.3, "Rubisko": 0.5, "Fructidor": 0.1}
irrig_effect_humidite = {"Pluvial": -0.8, "Irrigué": 0.9}
variete_effect_humidite = {"Apache": 0.2, "Rubisko": -0.1, "Fructidor": 0.0}

proteine = (
    11.5
    + plan["Fertilisation"].map(fert_effect)
    + plan["Variete"].map(variete_effect_prot)
    + rng.normal(0, 0.35, n_samples)
).round(2)

humidite = (
    12.0
    + plan["Irrigation"].map(irrig_effect_humidite)
    + plan["Variete"].map(variete_effect_humidite)
    + rng.normal(0, 0.25, n_samples)
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

variete_shift = {"Apache": 0.00, "Rubisko": 0.01, "Fructidor": -0.01}

spectra = np.zeros((n_samples, n_vars))

for i, row in plan.iterrows():
    spec = baseline.copy()

    # Décalage léger propre à la variété (structure fine du signal)
    spec = spec + variete_shift[row["Variete"]]

    # Bande protéine (1er harmonique N-H, ~1200 nm) proportionnelle à la teneur
    spec += gaussian_band(wavelengths, center=1200, width=25, amplitude=0.015 * row["Proteine"])

    # Bande humidité (1er harmonique O-H, ~1450 nm) proportionnelle à la teneur
    spec += gaussian_band(wavelengths, center=1450, width=30, amplitude=0.02 * row["Humidite"])

    # Effets physiques : diffusion multiplicative + offset additif (à corriger par SNV/MSC)
    slope = rng.normal(1.0, 0.08)
    intercept = rng.normal(0.0, 0.02)
    spec = spec * slope + intercept

    # Bruit instrumental
    spec += rng.normal(0, 0.004, n_vars)

    spectra[i, :] = spec

# Quelques échantillons atypiques (mesure défectueuse / contamination)
outlier_idx = rng.choice(n_samples, size=3, replace=False)
for idx in outlier_idx:
    spectra[idx, :] = spectra[idx, :] * rng.normal(1.6, 0.05) + rng.normal(0.15, 0.02)
    spectra[idx, :] += rng.normal(0, 0.02, n_vars)

spectra_df = pd.DataFrame(spectra, columns=[str(w) for w in wavelengths])

# ------------------------------------------------------------
# Assemblage final
# ------------------------------------------------------------
demo_df = pd.concat([plan.reset_index(drop=True), spectra_df], axis=1)
demo_df = demo_df.sample(frac=1.0, random_state=7).reset_index(drop=True)  # mélange des lignes

output_path = "data/demo_ble_nirs.csv"
demo_df.to_csv(output_path, index=False)

print("Shape:", demo_df.shape)
print("Colonnes non spectrales:", list(plan.columns))
print("Atypiques injectés (index avant mélange):", sorted(outlier_idx.tolist()))
print("Aperçu:")
print(demo_df.iloc[:3, :10])
