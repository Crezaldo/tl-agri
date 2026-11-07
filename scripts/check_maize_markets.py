"""Maize price per municipality (recent period) + low-coverage months."""
import pandas as pd

pd.set_option("display.width", 250)
m = pd.read_csv("data/processed/wfp_market_monthly.csv", parse_dates=["date"])
n = pd.read_csv("data/processed/wfp_national_monthly.csv", parse_dates=["date"])

mz = m[(m.commodity == "maize") & (m.date >= "2024-07-01")]
print(mz.pivot_table(index="date", columns="admin1", values="price_usd_kg").round(2).to_string())

print("\nLow-coverage months in modeling window:")
print(n[n.date >= "2020-05-01"].groupby("commodity")["low_coverage"].sum())
