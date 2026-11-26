"""
Chronos — Suivi de l'érosion côtière à Lomé (Togo)
Mesure satellite (Sentinel-2), lien avec le climat mondial et estimation financière, 2017-2026.
"""

import folium
import streamlit as st
from folium.plugins import Fullscreen
from streamlit_folium import st_folium

# ---------------------------------------------------------------------------
# Configuration de la page
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Chronos | Érosion côtière à Lomé",
    page_icon="🌊",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Données (modifier ici si les résultats changent)
# ---------------------------------------------------------------------------
MAP_CENTER = [6.154, 1.303]

TRANSECTS = [
    {
        "id": "T1",
        "nom": "Proche du port",
        "lat": 6.152089,
        "lon": 1.294799,
        "taux": -3.03,
        "couleur": "#C0392B",
        "detail": "Recul du trait de côte",
        "perte": "324 M FCFA (intervalle 143-527 M)",
    },
    {
        "id": "T2",
        "nom": "Plage ouverte",
        "lat": 6.155743,
        "lon": 1.311280,
        "taux": 11.63,
        "couleur": "#1E8449",
        "detail": "Accrétion (anomalie locale à investiguer)",
        "perte": None,
    },
]

CLIMAT_TAUX = 0.35  # m/an, part climatique mondiale (règle de Bruun)
T1_TAUX = abs(TRANSECTS[0]["taux"])

# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Inter:wght@400;500;600&display=swap');

    :root {
        --ocean: #0B3C5D;
        --ocean-clair: #D9E8F2;
        --sable: #F6F1E7;
        --encre: #1B2A35;
        --gris: #5E6C76;
        --recul: #C0392B;
        --gain: #1E8449;
        --neutre: #7A8791;
    }

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: var(--encre); }
    .block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1200px; }
    #MainMenu, footer, header [data-testid="stToolbar"] { visibility: hidden; }

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
        border-radius: 6px; padding: 1.1rem 1.2rem; height: 100%;
    }
    .kpi.recul { border-left-color: var(--recul); }
    .kpi.gain { border-left-color: var(--gain); }
    .kpi.climat { border-left-color: var(--ocean); }
    .kpi .label { font-size: 0.88rem; color: var(--gris); font-weight: 500; margin-bottom: 0.35rem; }
    .kpi .valeur {
        font-family: 'Fraunces', serif; font-size: 2.1rem; font-weight: 700;
        color: var(--encre); line-height: 1.1;
    }
    .kpi .note { font-size: 0.85rem; color: var(--gris); margin-top: 0.45rem; }
    .kpi.recul .note { color: var(--recul); font-weight: 500; }
    .kpi.gain .note { color: var(--gain); font-weight: 500; }

    h2, h3 { font-family: 'Fraunces', serif !important; color: var(--ocean) !important; }

    .legende { display: flex; gap: 1.6rem; flex-wrap: wrap; font-size: 0.92rem; color: var(--gris); margin: 0.4rem 0 0.8rem 0; }
    .legende span.pt {
        display: inline-block; width: 12px; height: 12px; border-radius: 50%;
        margin-right: 0.45rem; vertical-align: middle;
    }

    .lecture {
        background: var(--sable); border-radius: 6px;
        padding: 1rem 1.3rem; font-size: 0.97rem; line-height: 1.6;
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

# ---------------------------------------------------------------------------
# En-tête
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Indicateurs clés
# ---------------------------------------------------------------------------
part_climat = CLIMAT_TAUX / T1_TAUX * 100

k1, k2, k3, k4 = st.columns(4)

k1.markdown(
    f"""
    <div class="kpi recul">
        <div class="label">T1, proche du port</div>
        <div class="valeur">{TRANSECTS[0]['taux']:.2f} m/an</div>
        <div class="note">Recul du trait de côte</div>
    </div>
    """,
    unsafe_allow_html=True,
)
k2.markdown(
    f"""
    <div class="kpi gain">
        <div class="label">T2, plage ouverte</div>
        <div class="valeur">+{TRANSECTS[1]['taux']:.2f} m/an</div>
        <div class="note">Accrétion (anomalie locale)</div>
    </div>
    """,
    unsafe_allow_html=True,
)
k3.markdown(
    f"""
    <div class="kpi climat">
        <div class="label">Part du climat mondial</div>
        <div class="valeur">{CLIMAT_TAUX:.2f} m/an</div>
        <div class="note">Règle de Bruun, soit environ {part_climat:.0f} % du recul de T1</div>
    </div>
    """,
    unsafe_allow_html=True,
)
k4.markdown(
    """
    <div class="kpi">
        <div class="label">Perte estimée à T1 sur 10 ans</div>
        <div class="valeur">324 M FCFA</div>
        <div class="note">Intervalle : 143 à 527 M FCFA</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")

# ---------------------------------------------------------------------------
# Onglets
# ---------------------------------------------------------------------------
tab_carte, tab_lecture, tab_methode = st.tabs(["Carte des transects", "Lecture des résultats", "Méthode"])

# ----- Carte ---------------------------------------------------------------
with tab_carte:
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

    carte = folium.Map(
        location=MAP_CENTER,
        zoom_start=14,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri, Maxar, Earthstar Geographics",
        name="Satellite",
    ).add_to(carte)

    for t in TRANSECTS:
        signe = "+" if t["taux"] > 0 else ""
        ligne_perte = f"<br>Perte estimée : {t['perte']}" if t["perte"] else ""
        popup_html = (
            f"<div style='font-family:Inter,sans-serif;font-size:13px;line-height:1.5'>"
            f"<b>{t['id']} : {t['nom']}</b><br>"
            f"Taux : {signe}{t['taux']:.2f} m/an<br>"
            f"{t['detail']}{ligne_perte}</div>"
        )
        folium.CircleMarker(
            location=[t["lat"], t["lon"]],
            radius=12,
            color=t["couleur"],
            weight=3,
            fill=True,
            fill_color=t["couleur"],
            fill_opacity=0.65,
            tooltip=f"{t['id']} : {t['nom']}",
            popup=folium.Popup(popup_html, max_width=280),
        ).add_to(carte)

    Fullscreen(position="topright").add_to(carte)
    folium.LayerControl(position="topright", collapsed=True).add_to(carte)

    st_folium(carte, use_container_width=True, height=520, returned_objects=[])

# ----- Lecture -------------------------------------------------------------
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
        À T1, la perte financière estimée sur dix ans atteint <b>324 M FCFA</b>,
        avec une fourchette de 143 à 527 M FCFA selon une simulation Monte-Carlo.
        </div>
        """,
        unsafe_allow_html=True,
    )

# ----- Méthode -------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Pied de page
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="pied">
        Sources : Sentinel-2 (Copernicus) · Fond de carte © OpenStreetMap contributors, Esri<br>
        Méthodes : NDWI, règle de Bruun, simulation Monte-Carlo (n = 4 dates)
    </div>
    """,
    unsafe_allow_html=True,
)