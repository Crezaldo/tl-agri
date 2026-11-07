# Data Dictionary & Collection Documentation

Part 1 covers **raw data** (Step 2: Data Collection).
Part 2 (processed data) will be added in Step 3: Preprocessing.

## 1. Sources and polling intervals

| Source | Access method | Source updates | Our polling | Schedule (Dili time, UTC+9) | Raw location |
|---|---|---|---|---|---|
| WFP Food Prices – Timor-Leste (HDX) | CKAN API `package_show` → CSV | Monthly | Weekly | Monday 10:00 | `data/raw/wfp/` |
| World Bank Pink Sheet (monthly) | Web page scrape → XLSX | Monthly (early month) | Monthly | Day 5, 10:00 | `data/raw/worldbank/` |

**Why poll more often than the source updates?** WFP does not publish a
fixed release date. Weekly polling means a new month is captured within at
most 7 days, while the SHA-256 check prevents duplicate raw files when
nothing changed. The World Bank releases the Pink Sheet in the first
working days of each month, so day 5 is enough.

## 2. File naming convention

```
data/raw/<source>/<source>_<YYYYMMDDTHHMMSSZ>.<ext>
e.g. data/raw/wfp/wfp_20260928T010000Z.csv
```
Timestamp = UTC download time. Raw files are **never edited**.
WFP downloads also get a `.metadata.json` with the HDX resource info.

## 3. Collection log – `data/metadata/collection_log.csv`

| Column | Type | Description |
|---|---|---|
| run_timestamp_utc | ISO 8601 datetime | When the collector ran |
| source | string | `wfp` or `worldbank` |
| status | string | `saved` (new file), `unchanged` (same content), `error` |
| file_path | string | Relative path of saved file (empty if unchanged/error) |
| size_bytes | int | Size of downloaded content |
| sha256 | string | Content hash, used to detect changes |
| source_url | string | Exact URL downloaded |
| message | string | Row count or error details |

## 4. Raw schema – WFP CSV

Row 2 of the file is an HXL tag row (e.g. `#date`) and is removed in preprocessing.
*Verify against the actual downloaded file; columns may change.*

| Column | Type | Description | Example |
|---|---|---|---|
| date | date (YYYY-MM-15) | Month of observation (WFP uses the 15th) | 2024-06-15 |
| admin1 | string | Municipality | Dili |
| admin2 | string | Administrative post | Dom Aleixo |
| market | string | Market name | Dili |
| market_id | int | WFP market ID | |
| latitude, longitude | float | Market location | |
| category | string | Commodity group | cereals and tubers |
| commodity | string | Product name | Rice (imported) |
| commodity_id | int | WFP commodity ID | |
| unit | string | Unit of the price | KG |
| priceflag | string | Data quality flag, e.g. `actual` or `aggregate` (verify values) | actual |
| pricetype | string | `Retail` or `Wholesale` | Retail |
| currency | string | Currency code (TL uses USD) | USD |
| price | float | Price in local currency per unit | 0.76 |
| usdprice | float | Price in USD per unit | 0.76 |

## 5. Raw schema – World Bank Pink Sheet XLSX

Sheet `Monthly Prices`: first rows are titles/notes, then a row of
commodity names, a row of units, then data. Column A holds the period
as text `YYYYMmm` (e.g. `2024M06`). Missing values appear as `..`.
Prices are nominal USD (units vary: $/mt, $/kg).

---

# Part 2 – Processed Data (Step 3)

Produced by `python -m scripts.run_preprocessing` from the **latest** raw files.
`data/processed/manifest.json` records which raw files (name + SHA-256) were used,
the processing time (UTC), cleaning statistics and all settings.

## Cleaning rules (summary)

| Rule | Decision | Reason |
|---|---|---|
| Commodities | Keep only those in `wfp_commodity_map` | Project scope |
| Price type | Retail only | All TL rows are Retail |
| Date | Converted to month start (`YYYY-MM-01`) | WFP uses day 15; monthly frequency |
| Units | Converted to USD/kg (`KG`, `500 G`, `25 KG` …); other units dropped | Comparable prices |
| Duplicates | Same month + market + commodity → median | One value per cell |
| Outliers | Flagged (not deleted) when the residual of the two-way model (month level + market premium) exceeds 5 × MAD | Market premiums and changing reporting markets do not create false outliers; nationwide spikes are kept |
| National series | **Market-adjusted**: robust two-way model `log p[m,t] = a[t] + b[m]` fitted by alternating medians; national price = `exp(a[t])` (typical market). Raw median kept for comparison | Different markets report in different months (e.g. 2026: 2–4 markets); a raw median jumps when expensive markets (Dili, Ermera, Oecussi) enter/leave — composition bias |
| Low coverage | `low_coverage = True` if 1–2 markets reported | Warn about less reliable months |
| Spike correction | On the national series, a month that jumps away from **both** neighbours by more than max(4 × MAD, 25%) and reverts is replaced by interpolation (`spike_corrected = True`). Sustained changes are kept | Thin months (2–4 markets) with an unusual market (e.g. maize 2026-03, SAR-Oecusse 3.61 vs ~1.0 normally) |
| Segments | The two-way model is fitted separately per continuous segment (new segment after ≥ 6 missing months) | Market premiums change over time (e.g. Ermera maize: cheap in 2014–2018, ~2× typical market after 2020) |
| Missing months | Linear interpolation only for gaps ≤ 2 months (`is_imputed = True`); longer gaps stay empty | Avoid inventing long periods |

## `wfp_market_monthly.csv`

| Column | Type | Description |
|---|---|---|
| date | date | Month start |
| admin1 | string | Municipality |
| market | string | Market name |
| commodity | string | Short key, e.g. `rice_imported` |
| price_usd_kg | float | Retail price, USD per kg |
| unit_original | string | Unit in the raw file |
| is_outlier | bool | Flagged by the MAD rule |

## `wfp_national_monthly.csv`

| Column | Type | Description |
|---|---|---|
| date | date | Month start (continuous monthly range per commodity) |
| commodity | string | Short key |
| price_usd_kg | float | Market-adjusted national price (NaN = long gap) — **use for modeling** |
| price_market_adjusted | float | Two-way model level before spike correction |
| price_median_raw | float | Simple median of reporting markets (comparison only) |
| n_markets | int | Markets reporting that month (0 = no data) |
| low_coverage | bool | True if only 1–2 markets reported |
| spike_corrected | bool | True if an isolated spike was replaced by interpolation |
| is_imputed | bool | True if filled by interpolation (short gap or corrected spike) |

## `wfp_market_premiums.csv`

| Column | Type | Description |
|---|---|---|
| commodity | string | Short key |
| segment_start, segment_end | date | Continuous data segment the premium was estimated in |
| admin1 | string | Municipality |
| market | string | Market name |
| n_obs | int | Observations of this market in the segment |
| premium_index | float | Permanent price level of the market, median market = 100 (e.g. 145 = 45% more expensive) |

## `worldbank_monthly.csv`

| Column | Type | Description |
|---|---|---|
| date | date | Month start |
| commodity | string | Short key with `world_` prefix |
| price_usd_kg | float | Nominal world price, USD/kg (converted from $/mt where needed) |
| unit_original | string | Unit in the Pink Sheet |

## `analysis_monthly.csv`

Wide table, one row per month in the WFP period: one column per local
national series (e.g. `rice_imported`) and per world series (e.g.
`world_rice_thai5`), all in USD/kg. Used for EDA and pattern mining.

## `coverage_report.csv`

Per commodity: first/last month, months observed, imputed and missing,
coverage %, longest gap (months), average markets per month.

---

# Part 3 – Forecasting outputs (Step 6)

## `forecasts.csv`

| Column | Type | Description |
|---|---|---|
| commodity | string | Short key |
| date | date | Forecast month |
| model / model_spec | string | Chosen model (e.g. `ARIMA(1,1,2)`) |
| forecast_usd_kg | float | Point forecast, USD/kg |
| lower_95, upper_95 | float | Approximate 95% interval from backtest errors, widening with √horizon |
| last_observed_date, last_observed_usd_kg | date, float | Last actual value used |

## `backtest_predictions.csv`

One row per commodity × model × test month: `actual_usd_kg`, `pred_usd_kg`
(one-step-ahead, model fitted only on earlier months).

## `forecast_metrics.csv`

Per commodity × model: `MAE`, `RMSE`, `R2`, `MAPE_pct`, `rel_MAE_vs_naive`,
`rel_RMSE_vs_naive` (< 1 = better than Naive), `beats_naive`,
`DM_p_vs_naive` (Diebold-Mariano p-value; < 0.05 = significantly different from Naive),
`model_spec`.
