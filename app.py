import altair as alt
import folium
import pandas as pd
import streamlit as st
from folium.plugins import Fullscreen
from scipy.stats import linregress
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Chronos | Érosion côtière à Lomé",
    page_icon="🌊",
    layout="wide",
)

CENTRE = [6.154, 1.303]
GITHUB = "https://github.com/ELprospito/chronos"

FONDS = {
    "Satellite": {
        "tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "attr": "Esri, Maxar, Earthstar Geographics",
    },
    "Plan": {"tiles": "OpenStreetMap", "attr": None},
}

TRANSECTS = [
    {
        "id": "T1",
        "nom": "proche du port",
        "lat": 6.152089,
        "lon": 1.294799,
        "taux": -3.03,
        "r2": 0.82,
        "erreur": 1.01,
        "couleur": "#C0392B",
        "detail": "Recul du trait de côte",
        "perte": "324 M FCFA (intervalle 143-527 M)",
    },
    {
        "id": "T2",
        "nom": "plage ouverte",
        "lat": 6.155743,
        "lon": 1.311280,
        "taux": 11.63,
        "r2": 0.77,
        "erreur": 4.55,
        "couleur": "#1E8449",
        "detail": "Accrétion (anomalie locale à investiguer)",
        "perte": None,
    },
]

LIBELLES = {t["id"]: f"{t['id']}, {t['nom']}" for t in TRANSECTS}
COULEURS = {LIBELLES[t["id"]]: t["couleur"] for t in TRANSECTS}

DATES = ["2017-10-01", "2020-03-29", "2023-05-03", "2026-05-29"]
POSITIONS = {
    "T1": [325, 305, 305, 295],
    "T2": [205, 195, 225, 305],
}

CLIMAT_TAUX = 0.35
T1_TAUX = abs(TRANSECTS[0]["taux"])
PART_CLIMAT = CLIMAT_TAUX / T1_TAUX * 100
PART_LOCALE = T1_TAUX - CLIMAT_TAUX

PERTE_CENTRALE = 324
PERTE_BASSE = 143
PERTE_HAUTE = 527
HORIZON_REFERENCE = 10

RISQUES = [
    ("Système de gestion des conteneurs", 5, "Ransomware", 3, 2),
    ("Grues automatisées", 4, "Panne réseau OT/IT", 2, 3),
    ("Système de navigation AIS", 5, "Brouillage GPS", 2, 1),
    ("Plateforme douanière", 4, "Panne fournisseur tiers", 3, 2),
    ("Système de contrôle d'accès portuaire", 3, "Vol d'identifiants", 3, 2),
    ("Réseau électrique SCADA", 5, "Panne électrique prolongée", 2, 3),
]

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Inter:wght@400;500;600&display=swap');

    :root {
        --ocean: #0B3C5D;
        --sable: #F6F1E7;
        --encre: #1B2A35;
        --gris: #5E6C76;
        --recul: #C0392B;
        --gain: #1E8449;
        --neutre: #7A8791;
    }

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: var(--encre); }
    .block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1200px; }
    #MainMenu, footer { visibility: hidden; }

    .hero { padding: 1.2rem 0 0.4rem 0; }
    .hero h1 {
        font-family: 'Fraunces', serif; font-weight: 700;
        font-size: 2.7rem; line-height: 1.12; color: var(--ocean);
        margin: 0 0 0.6rem 0; padding: 0;
    }
    .hero p { font-size: 1.08rem; color: var(--gris); max-width: 46rem; line-height: 1.55; margin: 0; }

    .kpi {
        background: #FFFFFF; border: 1px solid #E3E8EC;
        border-left: 5px solid var(--neutre);
        border-radius: 6px; padding: 1.1rem 1.2rem;
        height: 100%; min-height: 10rem;
    }
    .kpi.recul { border-left-color: var(--recul); }
    .kpi.gain { border-left-color: var(--gain); }
    .kpi.climat { border-left-color: var(--ocean); }
    .kpi .label { font-size: 0.88rem; color: var(--gris); font-weight: 500; margin-bottom: 0.35rem; }
    .kpi .valeur {
        font-family: 'Fraunces', serif; font-size: 2.1rem; font-weight: 700;
        color: var(--encre); line-height: 1.1;
    }
    .kpi .note { font-size: 0.85rem; color: var(--gris); margin-top: 0.45rem; line-height: 1.45; }
    .kpi.recul .note { color: var(--recul); font-weight: 500; }
    .kpi.gain .note { color: var(--gain); font-weight: 500; }

    .legende { display: flex; gap: 1.6rem; flex-wrap: wrap; font-size: 0.92rem; color: var(--gris); margin: 0.2rem 0 0.8rem 0; }
    .legende span.pt {
        display: inline-block; width: 12px; height: 12px; border-radius: 50%;
        margin-right: 0.45rem; vertical-align: middle;
    }

    .lecture {
        background: var(--sable); border-radius: 6px;
        padding: 1.1rem 1.4rem; font-size: 0.98rem; line-height: 1.65;
    }
    .pied { color: var(--gris); font-size: 0.85rem; margin-top: 2rem; line-height: 1.6; }
    .pied a { color: var(--ocean); }

    @media (max-width: 640px) {
        .hero h1 { font-size: 2rem; }
        .kpi .valeur { font-size: 1.7rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def kpi(classe, label, valeur, note):
    return (
        f'<div class="kpi {classe}">'
        f'<div class="label">{label}</div>'
        f'<div class="valeur">{valeur}</div>'
        f'<div class="note">{note}</div>'
        f"</div>"
    )


def serie_complete():
    lignes = []
    for tid, valeurs in POSITIONS.items():
        for date, position in zip(DATES, valeurs):
            lignes.append(
                {
                    "Date": pd.Timestamp(date),
                    "Transect": LIBELLES[tid],
                    "Position (m)": position,
                }
            )
    return pd.DataFrame(lignes)


def calculer_taux(sous_serie):
    x = (sous_serie["Date"] - sous_serie["Date"].min()).dt.days / 365.25
    resultat = linregress(x, sous_serie["Position (m)"])
    r2 = resultat.rvalue**2 if len(sous_serie) >= 3 else None
    erreur = resultat.stderr if len(sous_serie) >= 3 else None
    return resultat.slope, r2, erreur


def construire_carte(fond, focus):
    if focus is None:
        centre, zoom = CENTRE, 14
    else:
        centre, zoom = [focus["lat"], focus["lon"]], 16

    config = FONDS[fond]
    if config["attr"]:
        carte = folium.Map(
            location=centre, zoom_start=zoom, tiles=config["tiles"],
            attr=config["attr"], control_scale=True,
        )
    else:
        carte = folium.Map(
            location=centre, zoom_start=zoom, tiles=config["tiles"], control_scale=True,
        )

    for t in TRANSECTS:
        signe = "+" if t["taux"] > 0 else ""
        ligne_perte = f"<br>Perte estimée : {t['perte']}" if t["perte"] else ""
        popup_html = (
            "<div style='font-family:Inter,sans-serif;font-size:13px;line-height:1.5'>"
            f"<b>{t['id']}, {t['nom']}</b><br>"
            f"Taux : {signe}{t['taux']:.2f} m/an (R² = {t['r2']:.2f})<br>"
            f"{t['detail']}{ligne_perte}</div>"
        )
        actif = focus is not None and focus["id"] == t["id"]
        folium.CircleMarker(
            location=[t["lat"], t["lon"]],
            radius=15 if actif else 11,
            color="white",
            weight=3,
            fill=True,
            fill_color=t["couleur"],
            fill_opacity=0.95,
            tooltip=f"{t['id']}, {t['nom']}",
            popup=folium.Popup(popup_html, max_width=280),
        ).add_to(carte)

    Fullscreen(position="topright").add_to(carte)
    return carte


def graphique_evolution(donnees):
    base = alt.Chart(donnees).encode(
        x=alt.X("Date:T", title="Date de l'image", axis=alt.Axis(format="%Y")),
        y=alt.Y("Position (m):Q", title="Position du trait de côte (m)", scale=alt.Scale(zero=False)),
        color=alt.Color(
            "Transect:N",
            scale=alt.Scale(domain=list(COULEURS.keys()), range=list(COULEURS.values())),
            legend=alt.Legend(title=None, orient="top"),
        ),
    )
    tendance = base.transform_regression("Date", "Position (m)", groupby=["Transect"]).mark_line(
        strokeDash=[6, 4], strokeWidth=2
    )
    points = base.mark_point(filled=True, size=120, opacity=1).encode(
        tooltip=[
            alt.Tooltip("Transect:N"),
            alt.Tooltip("Date:T", format="%d/%m/%Y"),
            alt.Tooltip("Position (m):Q"),
        ]
    )
    return (tendance + points).properties(height=360)


def graphique_risques(tableau):
    return (
        alt.Chart(tableau)
        .mark_bar(color="#0B3C5D")
        .encode(
            x=alt.X("Score:Q", title="Score de risque"),
            y=alt.Y("Actif:N", sort="-x", title=None),
            tooltip=["Actif", "Menace", "Criticité", "Probabilité", "Mitigation", "Score"],
        )
        .properties(height=280)
    )


st.markdown(
    """
    <div class="hero">
        <h1>Chronos : l'érosion côtière de Lomé, mesurée depuis l'espace</h1>
        <p>
            Dix ans d'images Sentinel-2 (2017-2026) pour mesurer l'évolution du trait de côte,
            isoler la part due au climat mondial et chiffrer le coût de l'inaction.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")

c1, c2, c3, c4 = st.columns(4)
c1.markdown(
    kpi("recul", "T1, proche du port", f"{TRANSECTS[0]['taux']:.2f} m/an",
        f"Recul, R² = {TRANSECTS[0]['r2']:.2f}, erreur-type ±{TRANSECTS[0]['erreur']:.2f}"),
    unsafe_allow_html=True,
)
c2.markdown(
    kpi("gain", "T2, plage ouverte", f"+{TRANSECTS[1]['taux']:.2f} m/an",
        f"Accrétion (anomalie), R² = {TRANSECTS[1]['r2']:.2f}, erreur-type ±{TRANSECTS[1]['erreur']:.2f}"),
    unsafe_allow_html=True,
)
c3.markdown(
    kpi("climat", "Part du climat mondial", f"{CLIMAT_TAUX:.2f} m/an",
        f"Règle de Bruun, soit environ {PART_CLIMAT:.0f} % du recul de T1"),
    unsafe_allow_html=True,
)
c4.markdown(
    kpi("", "Perte estimée à T1 sur 10 ans", f"{PERTE_CENTRALE} M FCFA",
        f"Intervalle : {PERTE_BASSE} à {PERTE_HAUTE} M FCFA"),
    unsafe_allow_html=True,
)

st.write("")

tab_carte, tab_evolution, tab_projection, tab_risques, tab_methode = st.tabs(
    ["Carte des transects", "Évolution mesurée", "Projection", "Risques du port", "Méthode et données"]
)

with tab_carte:
    f1, f2, f3 = st.columns([1, 1, 2])
    choix = f1.selectbox(
        "Zone affichée",
        ["Vue d'ensemble"] + [LIBELLES[t["id"]] for t in TRANSECTS],
    )
    fond = f2.radio("Fond de carte", list(FONDS.keys()), horizontal=True)

    focus = None
    for t in TRANSECTS:
        if choix.startswith(t["id"]):
            focus = t

    st.markdown(
        """
        <div class="legende">
            <div><span class="pt" style="background:#C0392B"></span>Recul du trait de côte</div>
            <div><span class="pt" style="background:#1E8449"></span>Accrétion (gain de terre)</div>
            <div>Cliquez sur un point pour voir le détail.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st_folium(
        construire_carte(fond, focus),
        use_container_width=True,
        height=520,
        returned_objects=[],
        key=f"carte-{fond}-{choix}",
    )

with tab_evolution:
    serie = serie_complete()
    dates_choisies = st.multiselect(
        "Images utilisées pour le calcul",
        options=DATES,
        default=DATES,
        format_func=lambda d: pd.Timestamp(d).strftime("%d/%m/%Y"),
    )

    if len(dates_choisies) < 2:
        st.warning("Sélectionnez au moins deux dates pour calculer une tendance.")
    else:
        selection = serie[serie["Date"].isin([pd.Timestamp(d) for d in dates_choisies])]

        e1, e2 = st.columns(2)
        for colonne, t in zip((e1, e2), TRANSECTS):
            sous = selection[selection["Transect"] == LIBELLES[t["id"]]]
            taux, r2, erreur = calculer_taux(sous)
            details = (
                f"R² = {r2:.2f}, erreur-type ±{erreur:.2f}"
                if r2 is not None
                else "Deux dates seulement : pas de mesure d'incertitude"
            )
            colonne.markdown(
                kpi(
                    "recul" if taux < 0 else "gain",
                    f"{LIBELLES[t['id']]} : taux recalculé",
                    f"{taux:+.2f} m/an",
                    details,
                ),
                unsafe_allow_html=True,
            )

        st.write("")
        st.altair_chart(graphique_evolution(selection), width="stretch")
        st.caption(
            "Chaque point est une position mesurée sur une image Sentinel-2. "
            "Une valeur qui baisse indique un recul vers les terres, une valeur qui monte indique un gain. "
            "Décochez une date pour voir si la tendance tient sans elle."
        )

    st.markdown(
        f"""
        <div class="lecture">
        <b>Ce que disent les mesures</b><br><br>
        À <b>T1</b>, près du port, la côte recule de <b>{T1_TAUX:.2f} m par an</b>.
        Le climat mondial (élévation du niveau de la mer, règle de Bruun) n'explique que
        <b>{CLIMAT_TAUX:.2f} m</b> de ce recul : il reste <b>{PART_LOCALE:.2f} m par an</b>
        d'origine locale. Les aménagements portuaires qui perturbent le transit des sédiments
        sont une piste à confirmer sur le terrain.
        <br><br>
        À <b>T2</b>, sur la plage ouverte, la côte avance de <b>{TRANSECTS[1]['taux']:.2f} m par an</b>,
        avec une incertitude élevée (±{TRANSECTS[1]['erreur']:.2f}). Cette valeur est exceptionnelle
        et doit être vérifiée avant toute conclusion.
        </div>
        """,
        unsafe_allow_html=True,
    )

with tab_projection:
    horizon = st.slider("Horizon de projection (années)", 1, 30, 10)

    recul = T1_TAUX * horizon
    facteur = horizon / HORIZON_REFERENCE
    centrale = PERTE_CENTRALE * facteur
    basse = PERTE_BASSE * facteur
    haute = PERTE_HAUTE * facteur

    p1, p2, p3 = st.columns(3)
    p1.markdown(
        kpi("recul", f"Recul cumulé de T1 en {horizon} ans", f"{recul:.1f} m", "Extrapolation linéaire du taux mesuré"),
        unsafe_allow_html=True,
    )
    p2.markdown(
        kpi("", f"Perte estimée en {horizon} ans", f"{centrale:,.0f} M FCFA".replace(",", " "),
            "Valeur centrale, proportionnelle à la durée"),
        unsafe_allow_html=True,
    )
    p3.markdown(
        kpi("", "Fourchette", f"{basse:,.0f} à {haute:,.0f}".replace(",", " "), "En millions de FCFA"),
        unsafe_allow_html=True,
    )

    st.write("")
    annees = list(range(0, horizon + 1))
    projection = pd.DataFrame(
        {"Recul cumulé de T1 (m)": [T1_TAUX * a for a in annees]},
        index=pd.Index(annees, name="Années"),
    )
    st.line_chart(projection, color="#C0392B", height=320)
    st.caption(
        "Projection simple : le taux mesuré est supposé constant. Elle ne tient pas compte "
        "d'éventuels ouvrages de protection ni de changements de dynamique sédimentaire."
    )

with tab_risques:
    tableau_risques = pd.DataFrame(
        RISQUES, columns=["Actif", "Criticité", "Menace", "Probabilité", "Mitigation"]
    )
    tableau_risques["Score"] = (
        tableau_risques["Criticité"]
        * tableau_risques["Probabilité"]
        * (6 - tableau_risques["Mitigation"])
    )
    tableau_risques = tableau_risques.sort_values("Score", ascending=False).reset_index(drop=True)

    st.markdown("**Risques numériques des actifs du port**")
    st.altair_chart(graphique_risques(tableau_risques), width="stretch")
    st.dataframe(tableau_risques, width="stretch", hide_index=True)
    st.caption(
        "Score = criticité × probabilité × (6 − mitigation existante). "
        "Criticité, probabilité et mitigation sont notées de 1 à 5."
    )

with tab_methode:
    st.markdown(
        """
        **Données** : images Sentinel-2 L2A (programme Copernicus), bandes B03 (vert) et B08 (proche infrarouge),
        4 dates entre 2017 et 2026.

        **Détection du trait de côte** : indice NDWI (Normalized Difference Water Index), qui sépare
        l'eau de la terre, puis extraction de la ligne de côte sur chaque image.

        **Taux d'évolution** : régression linéaire de la position du trait de côte le long de chaque
        transect en fonction du temps (en mètres par an).

        **Part climatique** : estimation du recul dû à la hausse du niveau de la mer avec la règle de Bruun.

        **Estimation financière** : simulation Monte-Carlo pour obtenir une valeur centrale (médiane)
        et un intervalle (percentiles 5 et 95).
        """
    )

    st.warning(
        "**Limites.** Seulement 4 dates et 2 transects. L'image de 2026 couvre une emprise plus petite "
        "que les trois autres (519 × 395 pixels contre 1038 × 789), et la tendance de T2 en dépend fortement : "
        "elle doit être confirmée par des mesures de terrain avant toute décision."
    )

    donnees_export = serie_complete().copy()
    donnees_export["Date"] = donnees_export["Date"].dt.strftime("%Y-%m-%d")

    d1, d2 = st.columns(2)
    d1.download_button(
        "Télécharger les positions par date (CSV)",
        donnees_export.to_csv(index=False).encode("utf-8-sig"),
        file_name="chronos_positions.csv",
        mime="text/csv",
    )
    taux_export = pd.DataFrame(
        [
            {
                "Transect": t["id"],
                "Taux (m/an)": t["taux"],
                "R2": t["r2"],
                "Erreur-type": t["erreur"],
            }
            for t in TRANSECTS
        ]
    )
    d2.download_button(
        "Télécharger les taux (CSV)",
        taux_export.to_csv(index=False).encode("utf-8-sig"),
        file_name="chronos_taux.csv",
        mime="text/csv",
    )

st.markdown(
    f"""
    <div class="pied">
        Sources : Sentinel-2 (Copernicus) · Fonds de carte © OpenStreetMap contributors, Esri<br>
        Méthodes : NDWI, règle de Bruun, simulation Monte-Carlo (n = 4 dates)<br>
        Code source : <a href="{GITHUB}" target="_blank">{GITHUB}</a>
    </div>
    """,
    unsafe_allow_html=True,
)