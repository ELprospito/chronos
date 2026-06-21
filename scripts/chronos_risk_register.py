import sys
import csv

def main():
    if len(sys.argv) != 2:
        print("Usage : python chronos_risk_register.py port_risk_register.csv")
        sys.exit(1)

    rows = []
    with open(sys.argv[1]) as f:
        for row in csv.DictReader(f):
            criticite = int(row["criticite"])
            probabilite = int(row["probabilite"])
            mitigation = int(row["mitigation_existante"])
            score = criticite * probabilite * (6 - mitigation)
            rows.append((row["asset"], row["categorie_menace"], score))

    rows.sort(key=lambda x: x[2], reverse=True)

    print(f"{'Actif':<40}{'Menace':<30}{'Score de risque'}")
    print("-" * 90)
    for asset, menace, score in rows:
        niveau = "ELEVE" if score >= 40 else "MOYEN" if score >= 20 else "FAIBLE"
        print(f"{asset:<40}{menace:<30}{score:<10} ({niveau})")

    print()
    print("Recommandation generale : prioriser la segmentation reseau et les plans")
    print("de continuite sur les actifs a risque ELEVE avant tout le reste.")


if __name__ == "__main__":
    main()