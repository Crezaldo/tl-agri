"""Inspect suspicious price jumps: raw median vs market-adjusted series."""
import pandas as pd

n = pd.read_csv("data/processed/wfp_national_monthly.csv", parse_dates=["date"])
for com, start in [("maize", "2025-10-01"), ("beans_kidney", "2026-02-01")]:
    print(com)
    print(n[(n.commodity == com) & (n.date >= start)].to_string(index=False))
    print()
