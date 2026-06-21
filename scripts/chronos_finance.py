import sys
import csv

VALEUR_M2_FCFA = 10833
LARGEUR_SEGMENT_M = 1000
HORIZON_ANNEES = 10


def main():
    if len(sys.argv) != 2:
        print("Usage : python chronos_finance.py chronos_rates.csv")
        sys.exit(1)

    total = 0.0
    print(f"{'Transect':<10}{'Perte/an (FCFA)':<20}{'Perte sur ' + str(HORIZON_ANNEES) + ' ans'}")
    print("-" * 60)

    with open(sys.argv[1]) as f:
        for row in csv.DictReader(f):
            rate = float(row["rate_m_per_year"])
            recul_m_an = max(0.0, -rate)
            perte_an = recul_m_an * LARGEUR_SEGMENT_M * VALEUR_M2_FCFA
            perte_horizon = perte_an * HORIZON_ANNEES
            total += perte_horizon
            print(f"{row['transect_id']:<10}{perte_an:>18,.0f}{perte_horizon:>22,.0f}")

    print("-" * 60)
    print(f"Total estime, {HORIZON_ANNEES} ans : {total:,.0f} FCFA")


if __name__ == "__main__":
    main()