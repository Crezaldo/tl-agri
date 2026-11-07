"""Run EDA and print key findings.

Usage (from project root):
    python -m scripts.run_eda
"""

import pandas as pd

from src.collection.utils import load_config
from src.eda import eda


def main() -> None:
    cfg = load_config()
    r = eda.run(cfg)
    s = r["summary"]
    start, end = r["window"]

    print(f"Modeling window: {start:%Y-%m} -> {end:%Y-%m}")
    print(f"Figures saved ({len(r['figures'])}) in {cfg['eda']['figures_dir']}/")
    with pd.option_context("display.width", 220, "display.max_columns", 30):
        print("\nSummary statistics (USD/kg):")
        print(s[["commodity", "n_months", "mean", "min", "max", "cv_pct",
                 "change_pct", "mom_std_pct", "max_mom_rise_pct", "max_rise_month"]]
              .to_string(index=False))
        print("\nPrice premium by municipality, 2020 onward (median market = 100):")
        print(r["markets"].to_string())
        print("\nOutliers by municipality:")
        print(r["outliers"].head(8).to_string())

    print("\nKey findings (auto):")
    print(f"- Most volatile (highest CV): {s.iloc[0]['commodity']} ({s.iloc[0]['cv_pct']:.1f}%)")
    print(f"- Most stable (lowest CV): {s.iloc[-1]['commodity']} ({s.iloc[-1]['cv_pct']:.1f}%)")
    up = s.sort_values("change_pct", ascending=False).iloc[0]
    print(f"- Largest change over window: {up['commodity']} ({up['change_pct']:+.1f}%)")
    mk = r["markets"].mean(axis=1)
    print(f"- Most expensive municipality: {mk.idxmax()} ({mk.max():.0f}); "
          f"cheapest: {mk.idxmin()} ({mk.min():.0f})")


if __name__ == "__main__":
    main()
