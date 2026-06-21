import sys
import csv
from collections import defaultdict
from datetime import datetime
import numpy as np

HORIZONS = [2036, 2041, 2046]
N_BOOTSTRAP = 20000


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


def bootstrap_projection(years, dists, horizon, rng, n=N_BOOTSTRAP):
    preds = []
    for _ in range(n):
        idx = rng.integers(0, len(years), len(years))
        y_s, d_s = years[idx], dists[idx]
        if len(set(y_s)) < 2:
            continue
        slope, intercept = np.polyfit(y_s, d_s, 1)
        preds.append(slope * horizon + intercept)
    return np.array(preds)


def main():
    if len(sys.argv) != 2:
        print("Usage : python chronos_projection.py chronos_timeseries.csv")
        sys.exit(1)

    data = load_timeseries(sys.argv[1])
    rng = np.random.default_rng(42)

    for tid, points in sorted(data.items()):
        years = np.array([p[0] for p in points])
        dists = np.array([p[1] for p in points])
        current = dists[np.argmax(years)]
        print(f"\n{tid} (position actuelle : {current:.0f} m)")
        for h in HORIZONS:
            preds = bootstrap_projection(years, dists, h, rng)
            p5, med, p95 = np.percentile(preds, [5, 50, 95])
            print(f"  {h} : mediane {med:.0f} m (P5={p5:.0f}, P95={p95:.0f})")


if __name__ == "__main__":
    main()