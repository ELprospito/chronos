import sys
import numpy as np
import rasterio
from scipy import ndimage
from skimage import measure
import matplotlib.pyplot as plt


def load_band(path):
    with rasterio.open(path) as src:
        return src.read(1).astype(np.float64)


def compute_ndwi(green, nir):
    denom = green + nir
    denom[denom == 0] = 1e-6
    return (green - nir) / denom


def clean_water_mask(ndwi, threshold=0.0, min_size=50):
    mask = ndwi > threshold
    mask = ndimage.binary_opening(mask, structure=np.ones((3, 3)))
    labeled, num = ndimage.label(mask)
    sizes = ndimage.sum(mask, labeled, range(1, num + 1))
    small = sizes < min_size
    mask[small[labeled - 1]] = False
    return mask


def extract_shoreline(mask, min_length_km=0.3, resolution_m=10.0):
    contours = measure.find_contours(mask.astype(float), level=0.5)
    kept = []
    for c in contours:
        diffs = np.diff(c, axis=0)
        length_km = np.sum(np.sqrt((diffs ** 2).sum(axis=1))) * resolution_m / 1000
        if length_km >= min_length_km:
            kept.append((c, length_km))
    kept.sort(key=lambda x: x[1], reverse=True)
    return kept


def main():
    if len(sys.argv) != 3:
        print("Usage : python chronos_shoreline.py B03.tiff B08.tiff")
        sys.exit(1)

    green = load_band(sys.argv[1])
    nir = load_band(sys.argv[2])
    ndwi = compute_ndwi(green, nir)
    mask = clean_water_mask(ndwi)
    shorelines = extract_shoreline(mask)

    print(f"Contours retenus (>= 0.3 km) : {len(shorelines)}")
    if shorelines:
        print(f"Ligne de côte principale     : {shorelines[0][1]:.2f} km")
    total = sum(l for _, l in shorelines)
    print(f"Longueur totale retenue      : {total:.2f} km")

    plt.figure(figsize=(10, 10))
    plt.imshow(ndwi, cmap="RdYlGn_r")
    plt.colorbar(label="NDWI")
    for c, length in shorelines:
        color = "black" if length == shorelines[0][1] else "blue"
        plt.plot(c[:, 1], c[:, 0], color=color, linewidth=1)
    plt.title("Chronos - ligne de côte détectée")
    plt.savefig("output/chronos_shoreline_output.png", dpi=150)
    print("Carte sauvegardée : output/chronos_shoreline_output.png")


if __name__ == "__main__":
    main()