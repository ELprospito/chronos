import sys
import csv

SEA_LEVEL_RISE_MM_PER_YEAR = 3.5
BEACH_SLOPE = 0.01


def bruun_retreat_m_per_year(slr_mm_per_year, slope):
    slr_m_per_year = slr_mm_per_year / 1000.0
    return slr_m_per_year / slope


def main():
    if len(sys.argv) != 2:
        print("Usage : python chronos_global_link.py chronos_rates.csv")
        sys.exit(1)

    global_rate = bruun_retreat_m_per_year(SEA_LEVEL_RISE_MM_PER_YEAR, BEACH_SLOPE)

    print(f"Recul attribuable a la montee mondiale des mers (regle de Bruun) : {global_rate:.2f} m/an")
    print()
    print(f"{'Transect':<10}{'Mesure (m/an)':<16}{'Part mondiale':<16}{'Part locale'}")
    print("-" * 60)

    with open(sys.argv[1]) as f:
        for row in csv.DictReader(f):
            measured = float(row["rate_m_per_year"])
            measured_retreat = -measured
            local = measured_retreat - global_rate
            print(f"{row['transect_id']:<10}{measured_retreat:<16.2f}{global_rate:<16.2f}{local:.2f}")


if __name__ == "__main__":
    main()