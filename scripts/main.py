import logging
import sys

from chronos_core import (
    ShorelineDetector,
    ErosionPredictor,
    GlobalLinkAnalyzer,
    FinancialRiskEvaluator,
    RiskRegister,
    DashboardBuilder,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("output/chronos.log"), logging.StreamHandler()],
)
logger = logging.getLogger("chronos")

LAT_CENTER, LON_CENTER = 6.154, 1.303
TRANSECTS_INFO = {
    "T1": (1.294799, 6.152089),
    "T2": (1.311280, 6.155743),
}


def main():
    if len(sys.argv) != 3:
        print("Usage : python main.py B03.tiff B08.tiff")
        sys.exit(1)

    logger.info("=== Debut du pipeline Chronos ===")

    detector = ShorelineDetector(sys.argv[1], sys.argv[2]).run()
    detector.save_map("output/chronos_shoreline_output.png")

    predictor = ErosionPredictor("output/chronos_timeseries.csv")
    rates = predictor.fit_all()

    linker = GlobalLinkAnalyzer()
    linker.decompose(rates)

    evaluator = FinancialRiskEvaluator()
    finances = {}
    for tid, info in rates.items():
        finances[tid] = evaluator.estimate(info["slope"], info["se"])

    try:
        RiskRegister("data/port_risk_register.csv").score_all()
    except FileNotFoundError:
        logger.warning("Registre de risque non trouve, etape ignoree")

    dashboard = DashboardBuilder(LAT_CENTER, LON_CENTER)
    dashboard.add_coastline(detector.main_contour_lonlat())
    for tid, (lon, lat) in TRANSECTS_INFO.items():
        rate = rates.get(tid, {}).get("slope", 0.0)
        perte = finances.get(tid, (0, 0, 0))[1]
        dashboard.add_transect(tid, lon, lat, rate, perte)
    dashboard.save("output/chronos_dashboard.html")

    logger.info("=== Pipeline termine avec succes ===")


if __name__ == "__main__":
    main()