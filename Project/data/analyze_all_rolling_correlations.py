"""All-pair rolling correlations, serial by default, process pool optional.

The serial path is the reference. ``--workers N`` sends each currency pair to
a process pool; the same calculation function is used in both paths, so the
saved values are identical.
"""
from __future__ import annotations

import argparse
import math
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = DATA_DIR / "analysis_output"
INPUT_FILE = OUTPUT_DIR / "fx_daily_log_returns_2010_2025.csv"

CURRENCIES = ["CNY", "USD", "JPY", "GBP", "HKD", "CHF", "AUD", "CAD"]
WINDOW = 60


def calculate_pair(task: tuple[str, np.ndarray, np.ndarray]) -> tuple[str, np.ndarray]:
    """Rolling correlation for one pair; used by both execution paths."""
    name, first, second = task
    result = (
        pd.Series(first)
        .rolling(WINDOW, min_periods=WINDOW)
        .corr(pd.Series(second))
        .to_numpy()[WINDOW - 1:]
    )
    return name, result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute 60-observation rolling correlations for all 28 pairs."
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Worker processes; 1 keeps the serial path (default: 1).",
    )
    parser.add_argument(
        "--chunksize",
        type=int,
        default=0,
        help="Tasks per process-pool message; 0 selects ceil(pairs / workers).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.workers < 1:
        raise ValueError("--workers must be at least 1.")
    if args.chunksize < 0:
        raise ValueError("--chunksize cannot be negative.")

    df = pd.read_csv(INPUT_FILE, parse_dates=["Date"]).set_index("Date")
    if not df.index.is_monotonic_increasing or not df.index.is_unique:
        raise ValueError("Dates must be unique and sorted in ascending order.")
    if len(df) < WINDOW or not np.isfinite(df[CURRENCIES].to_numpy(dtype=float)).all():
        raise ValueError("Not enough observations, or invalid currency values.")

    tasks = [
        (f"{first}_{second}", df[first].to_numpy(dtype=float), df[second].to_numpy(dtype=float))
        for first, second in combinations(CURRENCIES, 2)
    ]

    if args.workers == 1:
        pairs = list(map(calculate_pair, tasks))
    else:
        chunksize = (
            args.chunksize
            if args.chunksize > 0
            else max(1, math.ceil(len(tasks) / args.workers))
        )
        with ProcessPoolExecutor(
            max_workers=args.workers,
            mp_context=mp.get_context("spawn"),
        ) as executor:
            pairs = list(executor.map(calculate_pair, tasks, chunksize=chunksize))

    series_by_pair = dict(pairs)
    expected = {name for name, _, _ in tasks}
    if set(series_by_pair) != expected:
        raise ValueError("The result does not contain every currency pair.")

    results = pd.DataFrame(index=df.index[WINDOW - 1:])
    for first, second in combinations(CURRENCIES, 2):
        name = f"{first}_{second}"
        results[name] = series_by_pair[name]
        if len(series_by_pair[name]) != len(results):
            raise ValueError(f"Unexpected result length for {name}.")
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

    print(f"Execution: {'serial' if args.workers == 1 else f'{args.workers} workers'}")
    print(f"Currency pairs: {len(summary)}")
    print(f"Windows per pair: {len(results)}")
    print("\nFive pairs with the largest rolling changes:")
    print(summary[["pair", "full_period_correlation", "std_correlation",
                   "min_correlation", "max_correlation"]].head().to_string(index=False))


if __name__ == "__main__":
    main()
