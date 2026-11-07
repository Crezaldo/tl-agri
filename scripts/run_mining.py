"""Run pattern mining and print key findings.

Usage (from project root):
    python -m scripts.run_mining
"""

import pandas as pd

from src.collection.utils import load_config
from src.mining import patterns


def main() -> None:
    cfg = load_config()
    r = patterns.run(cfg)
    start, end = r["window"]
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)

    print(f"Window: {start:%Y-%m} -> {end:%Y-%m} | figures: {len(r['figures'])} in {cfg['mining']['figures_dir']}/")
    print("\n1) Seasonality & trend strength (0 = none, 1 = strong):")
    print(r["strength"].to_string(index=False))
    print("\n   Seasonal index (% vs trend):")
    print(r["seasonal_index"].T.to_string())
    print("\n2) Stationarity (ADF p-values; suggested ARIMA d):")
    print(r["stationarity"].to_string(index=False))
    print("\n3) Co-movement of monthly changes:")
    print(r["corr"].to_string())
    print("\n4) Price transmission world -> local:")
    print(r["transmission"].to_string(index=False))
    print("\n5) Price shocks (|robust z| > threshold):")
    print(r["anomalies"].to_string(index=False) if len(r["anomalies"]) else "   none")
    print("\n6) Municipality clusters:")
    print(r["clusters"].drop(columns=["cluster"]).to_string())

    # ---- auto key findings
    s = r["strength"]
    print("\nKey findings (auto):")
    if len(s):
        top = s.iloc[0]
        print(f"- Strongest seasonality: {top['commodity']} (Fs={top['seasonal_strength']:.2f}, "
              f"amplitude {top['seasonal_amplitude_pct']:.0f}%)")
    for _, t in r["transmission"].iterrows():
        verdict = "YES" if t["world_granger_causes_local"] else "no"
        print(f"- {t['world']} -> {t['local']}: best lag {int(t['best_lag'])} m "
              f"(corr {t['best_lag_corr']:.2f}); Granger p={t['granger_p']:.3f}, "
              f"Bonferroni p={t['granger_p_bonferroni']:.3f} -> {verdict}")
    d = r["stationarity"]
    print("- Suggested ARIMA d: " + ", ".join(f"{c}={v}" for c, v in zip(d['commodity'], d['suggested_d'])))
    a = r["anomalies"]
    if len(a):
        multi = a[a["n_commodities_same_month"] >= 2]["date"].dt.strftime("%Y-%m").unique()
        print(f"- {len(a)} price shocks; months with shocks in >= 2 commodities: {', '.join(multi) or 'none'}")


if __name__ == "__main__":
    main()
