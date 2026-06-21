import sys
import csv
from collections import defaultdict
from datetime import datetime
import numpy as np

VALEUR_M2_FCFA = 10833
VALEUR_INCERTITUDE_PCT = 0.20
LARGEUR_SEGMENT_M = 1000
HORIZON_ANNEES = 10
N_SIMULATIONS = 20000


def decimal_year(date_str):
    d = datetime.strptime(date_str, "%Y-%m-%d")
    start, end = datetime(d.year, 1, 1), datetime(d.year + 1, 1, 1)
    return d.year + (d - start).total_seconds() / (end - start).total_seconds()


def load_timeseries(path):
    data = defaultdict(list)
    with open(path) as f:
        for row in csv.reader(f):
            if row:
                date_str, tid, dist = row
                data[tid].append((decimal_year(date_str), float(dist)))
    return data


def slope_and_se(points):
    years = np.array([p[0] for p in points])
    dists = np.array([p[1] for p in points])
    n = len(points)
    slope, intercept = np.polyfit(years, dists, 1)
    pred = slope * years + intercept
    residuals = dists - pred
    sse = np.sum(residuals ** 2)
    mse = sse / (n - 2)
    sxx = np.sum((years - years.mean()) ** 2)
    se = np.sqrt(mse / sxx)
    return slope, se


def monte_carlo_loss(slope, se):
    rng = np.random.default_rng(42)
    slope_samples = rng.normal(slope, se, N_SIMULATIONS)
    value_samples = rng.uniform(
        VALEUR_M2_FCFA * (1 - VALEUR_INCERTITUDE_PCT),
        VALEUR_M2_FCFA * (1 + VALEUR_INCERTITUDE_PCT),
        N_SIMULATIONS,
    )
    recul = np.maximum(0.0, -slope_samples)
    return recul * LARGEUR_SEGMENT_M * value_samples * HORIZON_ANNEES


def main():
    if len(sys.argv) != 2:
        print("Usage : python chronos_finance_uncertainty.py chronos_timeseries.csv")
        sys.exit(1)

    data = load_timeseries(sys.argv[1])

    print(f"{'Transect':<10}{'Mediane (FCFA)':<20}{'P5':<20}{'P95'}")
    print("-" * 70)

    for tid, points in sorted(data.items()):
        slope, se = slope_and_se(points)
        losses = monte_carlo_loss(slope, se)
        p5, median, p95 = np.percentile(losses, [5, 50, 95])
        print(f"{tid:<10}{median:<20,.0f}{p5:<20,.0f}{p95:,.0f}")

    print()
    print("Intervalle large car n=4 dates seulement : c est une mesure honnete")
    print("de l incertitude reelle, pas une faiblesse a cacher.")


if __name__ == "__main__":
    main()