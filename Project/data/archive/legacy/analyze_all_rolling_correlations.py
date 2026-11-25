from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd


DATA_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = DATA_DIR / "analysis_output"
INPUT_FILE = OUTPUT_DIR / "fx_daily_log_returns_2010_2025.csv"

CURRENCIES = ["CNY", "USD", "JPY", "GBP", "HKD", "CHF", "AUD", "CAD"]
WINDOW = 60


def main():
    df = pd.read_csv(INPUT_FILE, parse_dates=["Date"]).set_index("Date")
    if not df.index.is_monotonic_increasing or not df.index.is_unique:
        raise ValueError("Dates must be unique and sorted in ascending order.")
    if len(df) < WINDOW or not np.isfinite(df[CURRENCIES].to_numpy(dtype=float)).all():
        raise ValueError("Not enough observations, or invalid currency values.")

    results = pd.DataFrame(index=df.index)
    for first, second in combinations(CURRENCIES, 2):
        results[f"{first}_{second}"] = (
            df[first].rolling(WINDOW, min_periods=WINDOW).corr(df[second])
        )

    results = results.iloc[WINDOW - 1:]
    if results.isna().any().any():
        raise ValueError("A rolling window has zero variance or missing results.")

    summary = []
    for first, second in combinations(CURRENCIES, 2):
        name = f"{first}_{second}"
        series = results[name]
        summary.append({
            "pair": name,
            "full_period_correlation": df[first].corr(df[second]),
            "valid_windows": len(series),
            "mean_correlation": series.mean(),
            "std_correlation": series.std(),
            "min_correlation": series.min(),
            "min_date": series.idxmin().strftime("%Y-%m-%d"),
            "max_correlation": series.max(),
            "max_date": series.idxmax().strftime("%Y-%m-%d"),
        })

    summary = pd.DataFrame(summary).sort_values(
        "std_correlation", ascending=False
    )
    results.to_csv(
        OUTPUT_DIR / "rolling_correlations_all_pairs_60d.csv",
        index_label="Date", float_format="%.6f"
    )
    summary.to_csv(
        OUTPUT_DIR / "rolling_correlation_summary_all_pairs_60d.csv",
        index=False, float_format="%.6f"
    )

    print(f"Currency pairs: {len(summary)}")
    print(f"Windows per pair: {len(results)}")
    print("\nFive pairs with the largest rolling changes:")
    print(summary[["pair", "full_period_correlation", "std_correlation",
                   "min_correlation", "max_correlation"]].head().to_string(index=False))


if __name__ == "__main__":
    main()
