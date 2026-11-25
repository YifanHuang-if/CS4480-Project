# Data Source and Provenance

## 1. Provider and citation

- **Provider:** European Central Bank (ECB), *euro foreign exchange reference rates*.
- **Dataset:** `eurofxref-hist.csv` (daily historical reference rates).
- **Landing page:** <https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html>
- **Direct download:** <https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip>
- **Local copy:** `Project/data/eurofxref-hist.csv` (1,926,581 bytes; 7,141 data rows; 42 columns).
- **Snapshot:** observations from 1999-01-04 to 2026-11-20. The local file was last written on 2026-11-22 15:54 (Asia/Shanghai). This timestamp is recorded as a local fact, not as proof of the original download time.
- **Suggested citation:** European Central Bank (2026), *Euro foreign exchange reference rates*, historical series, accessed 2026-11-22. Check the ECB terms of use before redistributing the file.

## 2. Fields used

| Field | Meaning |
|---|---|
| `Date` | Reference date of the ECB publication. |
| `CNY`, `USD`, `JPY`, `GBP`, `HKD`, `CHF`, `AUD`, `CAD` | Foreign currency units per 1 EUR. |

- **Base currency:** EUR.
- **Quote convention:** foreign currency units per 1 EUR. For example, `USD = 1.099` means 1.099 USD per EUR.
- **Direction:** a positive daily log change means the euro appreciated against that quote currency (it bought more of it).
- **Missing marker:** the raw file uses `N/A`. In the retained 2010–2025 window, the eight used columns have no missing values.
- The raw file contains 41 quote currencies. The project uses eight of them; the other 33 are not read by the pipeline.

## 3. Period and sample

| Item | Value |
|---|---:|
| Requested period | 2010-01-01 to 2025-12-31 |
| Retained first observation | 2010-01-04 |
| Retained last observation | 2025-12-31 |
| Retained daily observations | 4,097 |
| Daily log changes | 4,096 |
| Rows outside the requested period | 3,044 |
| Exact duplicates removed | 0 |
| Retained rows with missing rates | 0 |

The ECB publishes reference rates on TARGET business days, so successive observations can span weekends and holidays. Daily changes are therefore changes between available observations, not uniformly spaced 24-hour returns.

## 4. Cleaning rules

The implementation is `Project/data/clean_exchange_rates.py`; the machine-readable summary is `Project/data/cleaning_output/cleaning_summary.csv`.

1. Parse `Date` from either `YYYY/MM/DD` (the ECB download in this repository) or `YYYY-MM-DD`; reject invalid dates.
2. Keep the requested period, sort ascending, and require unique dates.
3. Remove exact duplicate rows; reject a repeated date whose rates conflict.
4. Convert the eight quotes to numeric values; reject non-numeric text, non-positive rates and infinite values.
5. Report missing counts and rows with missing rates. No imputation is performed.
6. Save the cleaned file plus the missing-value report and the cleaning summary.

Rows are not dropped for being extreme. The 2015-01-15 and 2016-06-24 sessions are retained in the main analysis and examined separately in `outlier_sensitivity_*.csv`.

## 5. Why these eight currencies

The selection covers a mix of exchange-rate regimes — HKD is pegged to USD, CNY is managed, and USD, JPY, GBP, CHF, AUD and CAD are floating — while all eight are quoted against EUR in the same ECB file and have complete coverage over the period. This is a purposive selection for interpretability, not a random sample.

## 6. Reproducing the data

```powershell
# 1. Download the ZIP from the direct URL above and extract eurofxref-hist.csv
#    into Project/data/.
# 2. Run the pipeline from Project/.
python data/clean_exchange_rates.py
python data/calculate_returns.py
```

The ECB file is updated on each publication day. Re-downloading later will add observations, so record the snapshot date whenever the pipeline is re-run. The project period ends on 2025-12-31, so later observations are filtered out by the cleaning script.
