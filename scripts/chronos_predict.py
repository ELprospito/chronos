import sys
import csv
from collections import defaultdict
from datetime import datetime
import numpy as np


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


def fit_trend(points):
    if len(points) < 2:
        return None
    years = np.array([p[0] for p in points])
    dists = np.array([p[1] for p in points])
    slope, intercept = np.polyfit(years, dists, 1)
    pred = slope * years + intercept
    ss_res, ss_tot = np.sum((dists - pred) ** 2), np.sum((dists - dists.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return slope, intercept, r2


def main():
    if len(sys.argv) != 2:
        print("Usage : python chronos_predict.py chronos_timeseries.csv")
        sys.exit(1)

    data = load_timeseries(sys.argv[1])

    print(f"{'Transect':<10}{'Taux (m/an)':<14}{'R2':<8}")
    print("-" * 35)

    rows = []
    for tid, points in sorted(data.items()):
        fit = fit_trend(points)
        if fit is None:
            print(f"{tid:<10} pas assez de données")
            continue
        slope, intercept, r2 = fit
        print(f"{tid:<10}{slope:<14.2f}{r2:<8.2f}")
        rows.append((tid, slope, r2))

    with open("output/chronos_rates.csv", "w", newline="") as f:
        csv.writer(f).writerows([["transect_id", "rate_m_per_year", "r2"]] + rows)
    print("\noutput/chronos_rates.csv généré")


if __name__ == "__main__":
    main()