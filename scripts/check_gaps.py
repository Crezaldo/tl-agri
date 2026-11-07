"""Show continuous data segments per commodity (no gaps)."""
import pandas as pd

n = pd.read_csv("data/processed/wfp_national_monthly.csv", parse_dates=["date"])
for com, g in n.groupby("commodity"):
    ok = g["price_usd_kg"].notna()
    seg = (ok != ok.shift()).cumsum()
    runs = g[ok].groupby(seg[ok])["date"].agg(["min", "max", "count"])
    print(com)
    print(runs.to_string(index=False))
    print()
