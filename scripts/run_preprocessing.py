"""Build processed datasets from the latest raw files.

Usage (from project root):
    python -m scripts.run_preprocessing

Outputs in data/processed/:
    wfp_market_monthly.csv     market-level panel (with outlier flag)
    wfp_national_monthly.csv   national median series per commodity
    worldbank_monthly.csv      world prices in USD/kg
    analysis_monthly.csv       wide table: local + world prices by month
    wfp_market_premiums.csv    permanent price premium per market (median = 100)
    coverage_report.csv        data completeness per commodity
    manifest.json              which raw files were used, and when
"""

import json

import pandas as pd

from src.collection.utils import PROJECT_ROOT, load_config, relpath, sha256_bytes, utc_iso
from src.preprocessing import clean_wfp, clean_worldbank


def main() -> None:
    cfg = load_config()
    out = PROJECT_ROOT / cfg["paths"]["processed_dir"]
    out.mkdir(parents=True, exist_ok=True)

    wfp = clean_wfp.run(cfg)
    wb = clean_worldbank.run(cfg)

    wfp["panel"].to_csv(out / "wfp_market_monthly.csv", index=False)
    wfp["national"].to_csv(out / "wfp_national_monthly.csv", index=False)
    wfp["coverage"].to_csv(out / "coverage_report.csv", index=False)
    wfp["premiums"].to_csv(out / "wfp_market_premiums.csv", index=False)
    wb["tidy"].to_csv(out / "worldbank_monthly.csv", index=False)

    # Wide analysis table, restricted to the WFP period
    local = wfp["national"].pivot(index="date", columns="commodity", values="price_usd_kg")
    world = wb["tidy"].pivot(index="date", columns="commodity", values="price_usd_kg")
    analysis = local.join(world, how="left")
    analysis.index.name = "date"
    analysis.reset_index().to_csv(out / "analysis_monthly.csv", index=False)

    manifest = {
        "processed_at_utc": utc_iso(),
        "inputs": {
            name: {"file": relpath(r["raw_file"]),
                   "sha256": sha256_bytes(r["raw_file"].read_bytes())}
            for name, r in [("wfp", wfp), ("worldbank", wb)]
        },
        "wfp_cleaning_stats": wfp["stats"],
        "worldbank_not_found": wb["not_found"],
        "settings": cfg["preprocessing"],
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str))

    print("WFP cleaning:", wfp["stats"])
    if wb["not_found"]:
        print("WARNING - World Bank names not found (fix config):", wb["not_found"])
    print("\nCoverage report:")
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(wfp["coverage"].to_string(index=False))
    print(f"\nanalysis_monthly.csv: {analysis.shape[0]} months x {analysis.shape[1]} series")


if __name__ == "__main__":
    main()
