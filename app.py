import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Chronos | Erosion Cotiere", page_icon="🌊", layout="wide")

st.title("🌊 Chronos — Suivi de l'erosion cotiere a Lome")
st.markdown("Mesure satellite, lien climatique mondial, et estimation financiere (2017-2026)")
st.divider()

st.subheader("Resultats mesures")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="T1 - Taux mesure", value="-3.03 m/an", delta="Recul", delta_color="inverse")
with col2:
    st.metric(label="T2 - Taux mesure", value="+11.63 m/an", delta="Accretion (anomalie)")
with col3:
    st.metric(label="Part climatique mondiale", value="0.35 m/an", delta="Regle de Bruun")
with col4:
    st.metric(label="Perte estimee T1 (10 ans)", value="324 M FCFA", delta="Intervalle : 143-527 M", delta_color="off")

st.divider()
st.subheader("Carte des transects")

m = folium.Map(location=[6.154, 1.303], zoom_start=14, tiles="CartoDB positron")

folium.CircleMarker(
    location=[6.152089, 1.294799],
    radius=12,
    color="red",
    fill=True,
    fill_opacity=0.7,
    popup="<b>T1 - proche du port</b><br>Recul : 3.03 m/an<br>Perte estimee : 324M FCFA (143-527M)",
).add_to(m)

folium.CircleMarker(
    location=[6.155743, 1.311280],
    radius=12,
    color="green",
    fill=True,
    fill_opacity=0.7,
    popup="<b>T2 - plage ouverte</b><br>Accretion : 11.63 m/an<br>Anomalie locale a investiguer",
).add_to(m)

st_folium(m, width=1200, height=500)

st.caption("Sentinel-2 (Copernicus) - methode NDWI - regle de Bruun - Monte-Carlo - n=4 dates")