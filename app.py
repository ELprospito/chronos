import folium
import pandas as pd
import streamlit as st
from folium.plugins import Fullscreen
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Chronos | Érosion côtière à Lomé",
    page_icon="🌊",
    layout="wide",
)

CENTRE = [6.154, 1.303]

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
        "couleur": "#1E8449",
        "detail": "Accrétion (anomalie locale à investiguer)",
        "perte": None,
    },
]

CLIMAT_TAUX = 0.35
T1_TAUX = abs(TRANSECTS[0]["taux"])
PART_CLIMAT = CLIMAT_TAUX / T1_TAUX * 100

PERTE_CENTRALE = 324
PERTE_BASSE = 143
PERTE_HAUTE = 527
HORIZON_REFERENCE = 10

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
            f"Taux : {signe}{t['taux']:.2f} m/an<br>"
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
    kpi("recul", "T1, proche du port", f"{TRANSECTS[0]['taux']:.2f} m/an", "Recul du trait de côte"),
    unsafe_allow_html=True,
)
c2.markdown(
    kpi("gain", "T2, plage ouverte", f"+{TRANSECTS[1]['taux']:.2f} m/an", "Accrétion (anomalie locale)"),
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

tab_carte, tab_projection, tab_lecture, tab_methode = st.tabs(
    ["Carte des transects", "Projection", "Lecture des résultats", "Méthode"]
)

with tab_carte:
    f1, f2, f3 = st.columns([1, 1, 2])
    choix = f1.selectbox(
        "Zone affichée",
        ["Vue d'ensemble"] + [f"{t['id']}, {t['nom']}" for t in TRANSECTS],
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
    donnees = pd.DataFrame(
        {"Recul cumulé de T1 (m)": [T1_TAUX * a for a in annees]},
        index=pd.Index(annees, name="Années"),
    )
    st.line_chart(donnees, color="#C0392B", height=320)
    st.caption(
        "Projection simple : le taux mesuré est supposé constant. Elle ne tient pas compte "
        "d'éventuels ouvrages de protection ni de changements de dynamique sédimentaire."
    )

with tab_lecture:
    st.markdown(
        f"""
        <div class="lecture">
        <b>Ce que disent les mesures</b><br><br>
        À <b>T1</b>, près du port, la côte recule de <b>{T1_TAUX:.2f} m par an</b>.
        Le climat mondial (élévation du niveau de la mer, règle de Bruun) n'explique qu'environ
        <b>{CLIMAT_TAUX:.2f} m</b> de ce recul : le reste a donc une origine locale,
        probablement liée aux aménagements portuaires qui bloquent le transit des sédiments.
        <br><br>
        À <b>T2</b>, sur la plage ouverte, la côte avance de <b>{TRANSECTS[1]['taux']:.2f} m par an</b>.
        Cette valeur est exceptionnelle et doit être vérifiée sur le terrain
        (dépôt de sédiments, remblais, effet de la marée sur l'image).
        <br><br>
        À T1, la perte financière estimée sur dix ans atteint <b>{PERTE_CENTRALE} M FCFA</b>,
        avec une fourchette de {PERTE_BASSE} à {PERTE_HAUTE} M FCFA selon une simulation Monte-Carlo.
        </div>
        """,
        unsafe_allow_html=True,
    )

with tab_methode:
    st.markdown(
        """
        **Données** : images Sentinel-2 (programme Copernicus), 4 dates entre 2017 et 2026.

        **Détection du trait de côte** : indice NDWI (Normalized Difference Water Index), qui sépare
        l'eau de la terre, puis extraction de la ligne de côte sur chaque image.

        **Taux d'évolution** : distance parcourue par le trait de côte le long de chaque transect,
        rapportée au temps écoulé (en mètres par an).

        **Part climatique** : estimation du recul dû à la hausse du niveau de la mer avec la règle de Bruun.

        **Estimation financière** : simulation Monte-Carlo pour obtenir une valeur centrale et un intervalle.

        **Limites** : seulement 4 dates et 2 transects. Les résultats sont indicatifs
        et doivent être confirmés par des mesures de terrain avant toute décision.
        """
    )

st.markdown(
    """
    <div class="pied">
        Sources : Sentinel-2 (Copernicus) · Fond de carte © OpenStreetMap contributors, Esri<br>
        Méthodes : NDWI, règle de Bruun, simulation Monte-Carlo (n = 4 dates)
    </div>
    """,
    unsafe_allow_html=True,
)