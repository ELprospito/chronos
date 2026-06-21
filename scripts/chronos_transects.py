import sys
import csv
import math
import numpy as np
import rasterio
from scipy import ndimage
from rasterio.transform import rowcol
from chronos_shoreline import compute_ndwi

TRANSECTS = [
    ("T1", 1.294799, 6.152089, 157.3, 1000),
    ("T2", 1.311280, 6.155743, 189.3, 1000),
]


def clean_water_mask(ndwi, threshold=0.0, min_size=50):
    mask = ndwi > threshold
    mask = ndimage.binary_opening(mask, structure=np.ones((3, 3)))
    labeled, num = ndimage.label(mask)
    sizes = ndimage.sum(mask, labeled, range(1, num + 1))
    small = sizes < min_size
    mask[small[labeled - 1]] = False
    return mask.astype(float)


def destination_point(lon0, lat0, bearing_deg, distance_m):
    bearing = math.radians(bearing_deg)
    dlat = (distance_m * math.cos(bearing)) / 111320.0
    dlon = (distance_m * math.sin(bearing)) / (111320.0 * math.cos(math.radians(lat0)))
    return lon0 + dlon, lat0 + dlat


def sample_along_transect(field, transform, lon0, lat0, bearing_deg, max_len_m, step_m=10.0):
    distances, values = [], []
    h, w = field.shape
    for i in range(int(max_len_m / step_m)):
        d = i * step_m
        lon, lat = destination_point(lon0, lat0, bearing_deg, d)
        row, col = rowcol(transform, lon, lat)
        if 0 <= row < h and 0 <= col < w:
            distances.append(d)
            values.append(field[row, col])
    return np.array(distances), np.array(values)


def find_shoreline_crossing(distances, values, threshold=0.5):
    for i in range(1, len(values)):
        if values[i - 1] < threshold <= values[i]:
            frac = (threshold - values[i - 1]) / (values[i] - values[i - 1])
            return distances[i - 1] + frac * (distances[i] - distances[i - 1])
    return None


def main():
    if len(sys.argv) != 4:
        print("Usage : python chronos_transects.py B03.tiff B08.tiff AAAA-MM-JJ")
        sys.exit(1)

    with rasterio.open(sys.argv[1]) as src:
        green = src.read(1).astype(np.float64)
        transform = src.transform
    with rasterio.open(sys.argv[2]) as src:
        nir = src.read(1).astype(np.float64)

    date = sys.argv[3]
    ndwi = compute_ndwi(green, nir)
    mask = clean_water_mask(ndwi)

    writer = csv.writer(sys.stdout)
    for tid, lon0, lat0, bearing, max_len in TRANSECTS:
        distances, values = sample_along_transect(mask, transform, lon0, lat0, bearing, max_len)
        crossing = find_shoreline_crossing(distances, values)
        if crossing is not None:
            writer.writerow([date, tid, f"{crossing:.1f}"])


if __name__ == "__main__":
    main()