"""Backtest all models, choose the best per commodity, forecast ahead.

Usage (from project root):
    python -m scripts.run_forecasting
"""

import pandas as pd

from src.collection.utils import load_config
from src.forecasting import backtest


def main() -> None:
    cfg = load_config()
    r = backtest.run(cfg)
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 20)
    m = r["metrics"]

    print(f"Walk-forward backtest: last {cfg['modeling']['test_months']} months, "
          f"horizon {cfg['forecasting']['horizon']} month\n")
    for com, g in m.groupby("commodity"):
        print(f"== {com}")
        print(g.sort_values("RMSE")[["model", "model_spec", "MAE", "RMSE", "R2", "MAPE_pct",
                                     "rel_RMSE_vs_naive", "DM_p_vs_naive"]].round(4).to_string(index=False))
        print()

    print("Model choice (best by RMSE; Naive kept if nothing beats it):")
    print(r["best"].round(4).to_string(index=False))

    print("\nAblation - does adding world prices help? (RMSE)")
    for base in ("LinearRegression", "RandomForest"):
        a = m[m["model"] == base].set_index("commodity")["RMSE"]
        b = m[m["model"] == f"{base}+world"].set_index("commodity")["RMSE"]
        for com in b.index:
            ch = 100 * (b[com] / a[com] - 1)
            print(f"  {base:16s} {com:14s} without {a[com]:.4f} | with {b[com]:.4f} ({ch:+.1f}%)")

    print("\nFuture forecast:")
    f = r["forecast"]
    print(f[["commodity", "date", "model_spec", "forecast_usd_kg", "lower_95", "upper_95"]]
          .to_string(index=False))

    main3 = m[m["model"].isin(["LinearRegression", "RandomForest", "ARIMA"])]
    wins = main3.loc[main3.groupby("commodity")["RMSE"].idxmin(), "model"].value_counts()
    print("\nKey findings (auto):")
    print(f"- Best of the 3 required models, by commodity count: {wins.to_dict()}")
    sig = m[(~m["model"].isin(["Naive", "SeasonalNaive"])) & (m["DM_p_vs_naive"] < 0.05)
            & m["beats_naive"]]
    print(f"- Significantly better than Naive (DM p < 0.05): "
          f"{', '.join(sig['commodity'] + ':' + sig['model']) or 'none'}")
    print(f"- Commodities where the chosen model beats Naive: "
          f"{int((r['best']['chosen_model'] != 'Naive').sum())} of {len(r['best'])}")


if __name__ == "__main__":
    main()
