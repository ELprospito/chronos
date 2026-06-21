# Chronos — Suivi satellite de l'érosion côtière à Lomé, Togo

Mesure, à partir d'images Sentinel-2 gratuites (Copernicus), la vitesse de recul du littoral togolais. Décompose les causes (locale vs changement climatique mondial), chiffre la perte économique avec son incertitude réelle, et projette l'évolution future.

## Le problème

Le littoral togolais recule de 10 à 15 m/an en moyenne, en grande partie causé par le barrage d'Akossombo (Ghana, bloque le transport sédimentaire) et la jetée du Port de Lomé (perturbe la dérive littorale).

## Méthodologie

1. **Extraction de la côte** — NDWI sur bandes Sentinel-2 (B03, B08), filtrage morphologique du bruit urbain
2. **Mesure temporelle** — transects géoréférencés (lat/lon, pas pixels), 4 dates (2017-2026)
3. **Régression statistique** — taux de recul par transect, validé par R²
4. **Lien climatique mondial** — règle de Bruun, décomposition local/mondial
5. **Incertitude financière** — simulation Monte-Carlo plutôt qu'un chiffre unique trompeur
6. **Registre de risque numérique** — méthode GRC standard pour infrastructures portuaires critiques
7. **Dashboard interactif** — carte Folium + application Streamlit

## Résultats clés

| Transect | Taux mesuré | R² | Cause locale | Cause mondiale | Perte estimée (10 ans) |
|---|---|---|---|---|---|
| T1 (proche port) | -3,03 m/an | 0,82 | 2,68 m/an | 0,35 m/an | 324 M FCFA (143-527 M) |
| T2 (plage ouverte) | +11,63 m/an | 0,77 | -11,98 m/an | 0,35 m/an | 0 FCFA |

## Installation

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Utilisation

```bash
python scripts\main.py "data\NOM_B03.tiff" "data\NOM_B08.tiff"
```

Lance tout le pipeline. Ouvre ensuite `output\chronos_dashboard.html`, ou lance `streamlit run app.py` pour la version interactive.

## Limites (honnêtes)

- 4 dates seulement, 2 points de mesure — échantillon modeste, pas une étude exhaustive
- Une image par date — sensible aux conditions de marée/vagues
- Prix du foncier basé sur une seule annonce, pas une étude de marché
- L'accrétion mesurée à T2 contredit partiellement la littérature généraliste — anomalie locale non expliquée avec certitude

## Licence

MIT