import sys
import numpy as np
import rasterio
from rasterio.transform import xy
from skimage import measure
import folium
from chronos_shoreline import load_band, compute_ndwi, clean_water_mask

LAT_CENTER, LON_CENTER = 6.154, 1.303

TRANSECTS = {
    "T1": (1.294799, 6.152089, -3.03, 323741900),
    "T2": (1.311280, 6.155743, 11.63, 0),
}


def main():
    if len(sys.argv) != 3:
        print("Usage : python chronos_dashboard.py B03.tiff B08.tiff")
        sys.exit(1)

    with rasterio.open(sys.argv[1]) as src:
        green = src.read(1).astype(np.float64)
        transform = src.transform
    with rasterio.open(sys.argv[2]) as src:
        nir = src.read(1).astype(np.float64)

    ndwi = compute_ndwi(green, nir)
    mask = clean_water_mask(ndwi)
    contours = measure.find_contours(mask.astype(float), level=0.5)
    lengths = [np.sum(np.sqrt((np.diff(c, axis=0) ** 2).sum(axis=1))) for c in contours]
    main_contour = contours[int(np.argmax(lengths))]

    coastline_lonlat = []
    for row, col in main_contour:
        lon, lat = xy(transform, row, col)
        coastline_lonlat.append([lat, lon])

    m = folium.Map(location=[LAT_CENTER, LON_CENTER], zoom_start=14, tiles="CartoDB positron")
    folium.PolyLine(coastline_lonlat, color="blue", weight=2, opacity=0.8).add_to(m)

    for tid, (lon, lat, rate, perte) in TRANSECTS.items():
        couleur = "red" if rate < 0 else "green"
        statut = "RECUL" if rate < 0 else "ACCRETION"
        popup = f"<b>{tid}</b><br>Taux : {rate:.2f} m/an ({statut})<br>Perte estimee (10 ans) : {perte:,.0f} FCFA"
        folium.CircleMarker(
            location=[lat, lon], radius=10, color=couleur, fill=True, fill_opacity=0.8, popup=popup,
        ).add_to(m)

    m.save("output/chronos_dashboard.html")
    print("Dashboard genere : output/chronos_dashboard.html")


if __name__ == "__main__":
    main()