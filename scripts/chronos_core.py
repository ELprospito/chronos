import logging
import math
import csv
from collections import defaultdict
from datetime import datetime

import numpy as np
import rasterio
from rasterio.transform import rowcol, xy
from scipy import ndimage
from skimage import measure
import matplotlib.pyplot as plt
import folium

logger = logging.getLogger("chronos")


class ShorelineDetector:
    def __init__(self, b03_path, b08_path):
        self.b03_path = b03_path
        self.b08_path = b08_path
        self.transform = None
        self.ndwi = None
        self.mask = None
        self.shorelines = []

    def run(self):
        with rasterio.open(self.b03_path) as src:
            green = src.read(1).astype(np.float64)
            self.transform = src.transform
        with rasterio.open(self.b08_path) as src:
            nir = src.read(1).astype(np.float64)
        denom = green + nir
        denom[denom == 0] = 1e-6
        self.ndwi = (green - nir) / denom
        logger.info("NDWI calcule")

        mask = self.ndwi > 0.0
        mask = ndimage.binary_opening(mask, structure=np.ones((3, 3)))
        labeled, num = ndimage.label(mask)
        sizes = ndimage.sum(mask, labeled, range(1, num + 1))
        small = sizes < 50
        mask[small[labeled - 1]] = False
        self.mask = mask.astype(float)
        logger.info("Masque eau/terre nettoye")

        contours = measure.find_contours(self.mask, level=0.5)
        kept = []
        for c in contours:
            diffs = np.diff(c, axis=0)
            length_km = np.sum(np.sqrt((diffs ** 2).sum(axis=1))) * 10 / 1000
            if length_km >= 0.3:
                kept.append((c, length_km))
        kept.sort(key=lambda x: x[1], reverse=True)
        self.shorelines = kept
        if kept:
            logger.info(f"{len(kept)} contours retenus, ligne principale {kept[0][1]:.2f} km")
        else:
            logger.warning("Aucun contour retenu")
        return self

    def main_contour_lonlat(self):
        if not self.shorelines:
            return []
        contour = self.shorelines[0][0]
        return [list(xy(self.transform, row, col))[::-1] for row, col in contour]

    def save_map(self, output_path):
        plt.figure(figsize=(10, 10))
        plt.imshow(self.ndwi, cmap="RdYlGn_r")
        plt.colorbar(label="NDWI")
        for c, length in self.shorelines:
            color = "black" if length == self.shorelines[0][1] else "blue"
            plt.plot(c[:, 1], c[:, 0], color=color, linewidth=1)
        plt.title("Chronos - ligne de cote detectee")
        plt.savefig(output_path, dpi=150)
        logger.info(f"Carte NDWI sauvegardee : {output_path}")
        return self


class TransectMeasurer:
    def __init__(self, transects):
        self.transects = transects

    @staticmethod
    def destination_point(lon0, lat0, bearing_deg, distance_m):
        bearing = math.radians(bearing_deg)
        dlat = (distance_m * math.cos(bearing)) / 111320.0
        dlon = (distance_m * math.sin(bearing)) / (111320.0 * math.cos(math.radians(lat0)))
        return lon0 + dlon, lat0 + dlat

    def sample(self, field, transform, lon0, lat0, bearing_deg, max_len_m, step_m=10.0):
        h, w = field.shape
        distances, values = [], []
        for i in range(int(max_len_m / step_m)):
            d = i * step_m
            lon, lat = self.destination_point(lon0, lat0, bearing_deg, d)
            row, col = rowcol(transform, lon, lat)
            if 0 <= row < h and 0 <= col < w:
                distances.append(d)
                values.append(field[row, col])
        return np.array(distances), np.array(values)

    @staticmethod
    def find_crossing(distances, values, threshold=0.5):
        for i in range(1, len(values)):
            if values[i - 1] < threshold <= values[i]:
                frac = (threshold - values[i - 1]) / (values[i] - values[i - 1])
                return distances[i - 1] + frac * (distances[i] - distances[i - 1])
        return None

    def measure_all(self, mask, transform):
        results = {}
        for tid, lon0, lat0, bearing, max_len in self.transects:
            d, v = self.sample(mask, transform, lon0, lat0, bearing, max_len)
            crossing = self.find_crossing(d, v)
            if crossing is not None:
                results[tid] = crossing
                logger.info(f"Transect {tid} : {crossing:.1f} m")
        return results


class ErosionPredictor:
    def __init__(self, timeseries_path):
        self.timeseries_path = timeseries_path
        self.data = self._load()

    @staticmethod
    def decimal_year(date_str):
        d = datetime.strptime(date_str, "%Y-%m-%d")
        start, end = datetime(d.year, 1, 1), datetime(d.year + 1, 1, 1)
        return d.year + (d - start).total_seconds() / (end - start).total_seconds()

    def _load(self):
        data = defaultdict(list)
        with open(self.timeseries_path) as f:
            for row in csv.reader(f):
                if row:
                    date_str, tid, dist = row
                    data[tid].append((self.decimal_year(date_str), float(dist)))
        return data

    def fit_all(self):
        rates = {}
        for tid, points in sorted(self.data.items()):
            if len(points) < 2:
                continue
            years = np.array([p[0] for p in points])
            dists = np.array([p[1] for p in points])
            n = len(points)
            slope, intercept = np.polyfit(years, dists, 1)
            pred = slope * years + intercept
            residuals = dists - pred
            ss_res = np.sum(residuals ** 2)
            ss_tot = np.sum((dists - dists.mean()) ** 2)
            r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
            if n > 2:
                mse = ss_res / (n - 2)
                sxx = np.sum((years - years.mean()) ** 2)
                se = np.sqrt(mse / sxx)
            else:
                se = 0.0
            rates[tid] = {"slope": slope, "r2": r2, "se": se}
            logger.info(f"{tid} : taux {slope:.2f} m/an, R2={r2:.2f}, erreur-type={se:.2f}")
        return rates

    def bootstrap_projection(self, tid, horizon, n=20000, seed=42):
        points = self.data[tid]
        years = np.array([p[0] for p in points])
        dists = np.array([p[1] for p in points])
        rng = np.random.default_rng(seed)
        preds = []
        for _ in range(n):
            idx = rng.integers(0, len(years), len(years))
            y_s, d_s = years[idx], dists[idx]
            if len(set(y_s)) < 2:
                continue
            slope, intercept = np.polyfit(y_s, d_s, 1)
            preds.append(slope * horizon + intercept)
        return np.percentile(preds, [5, 50, 95])


class GlobalLinkAnalyzer:
    def __init__(self, sea_level_rise_mm_per_year=3.5, beach_slope=0.01):
        self.global_rate = (sea_level_rise_mm_per_year / 1000.0) / beach_slope

    def decompose(self, rates):
        decomposed = {}
        for tid, info in rates.items():
            measured_retreat = -info["slope"]
            local = measured_retreat - self.global_rate
            decomposed[tid] = {"mesure": measured_retreat, "mondial": self.global_rate, "local": local}
            logger.info(f"{tid} : mondial={self.global_rate:.2f} m/an, local={local:.2f} m/an")
        return decomposed


class FinancialRiskEvaluator:
    def __init__(self, valeur_m2_fcfa=10833, incertitude_pct=0.20,
                 largeur_segment_m=1000, horizon_annees=10, n_simulations=20000):
        self.valeur_m2_fcfa = valeur_m2_fcfa
        self.incertitude_pct = incertitude_pct
        self.largeur_segment_m = largeur_segment_m
        self.horizon_annees = horizon_annees
        self.n_simulations = n_simulations

    def estimate(self, slope, se, seed=42):
        rng = np.random.default_rng(seed)
        slope_samples = rng.normal(slope, se if se else 0.01, self.n_simulations)
        value_samples = rng.uniform(
            self.valeur_m2_fcfa * (1 - self.incertitude_pct),
            self.valeur_m2_fcfa * (1 + self.incertitude_pct),
            self.n_simulations,
        )
        recul = np.maximum(0.0, -slope_samples)
        losses = recul * self.largeur_segment_m * value_samples * self.horizon_annees
        p5, median, p95 = np.percentile(losses, [5, 50, 95])
        logger.info(f"Perte estimee : mediane {median:,.0f} FCFA (P5={p5:,.0f}, P95={p95:,.0f})")
        return p5, median, p95


class RiskRegister:
    def __init__(self, csv_path):
        self.csv_path = csv_path

    def score_all(self):
        rows = []
        with open(self.csv_path) as f:
            for row in csv.DictReader(f):
                criticite = int(row["criticite"])
                probabilite = int(row["probabilite"])
                mitigation = int(row["mitigation_existante"])
                score = criticite * probabilite * (6 - mitigation)
                rows.append((row["asset"], row["categorie_menace"], score))
        rows.sort(key=lambda x: x[2], reverse=True)
        if rows:
            logger.info(f"{len(rows)} actifs evalues, score max {rows[0][2]}")
        return rows


class DashboardBuilder:
    def __init__(self, lat_center, lon_center, zoom_start=14):
        self.map = folium.Map(location=[lat_center, lon_center], zoom_start=zoom_start, tiles="CartoDB positron")

    def add_coastline(self, coastline_lonlat, color="blue"):
        if coastline_lonlat:
            folium.PolyLine(coastline_lonlat, color=color, weight=2, opacity=0.8).add_to(self.map)
        return self

    def add_transect(self, tid, lon, lat, rate, perte):
        couleur = "red" if rate < 0 else "green"
        statut = "RECUL" if rate < 0 else "ACCRETION"
        popup = f"<b>{tid}</b><br>Taux : {rate:.2f} m/an ({statut})<br>Perte estimee (10 ans) : {perte:,.0f} FCFA"
        folium.CircleMarker(
            location=[lat, lon], radius=10, color=couleur, fill=True, fill_opacity=0.8, popup=popup,
        ).add_to(self.map)
        return self

    def save(self, output_path):
        self.map.save(output_path)
        logger.info(f"Dashboard sauvegarde : {output_path}")
        return self