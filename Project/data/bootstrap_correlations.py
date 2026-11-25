"""Moving-block bootstrap confidence intervals for full-period correlations.

Daily changes are not independent: volatility clusters and successive
observations are dependent. A 60-observation moving-block bootstrap keeps
short-range dependence while resampling the series, and gives an approximate
95% percentile interval for each of the 28 pairwise correlations.

Outputs
-------
correlation_bootstrap_ci.csv
figures/correlation_bootstrap_ci.png
"""
from itertools import combinations
from pathlib import Path
from time import perf_counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = DATA_DIR / "analysis_output"
FIGURE_DIR = OUTPUT_DIR / "figures"
CURRENCIES = ["CNY", "USD", "JPY", "GBP", "HKD", "CHF", "AUD", "CAD"]
PAIRS = list(combinations(CURRENCIES, 2))
BLOCK_LENGTH = 60
N_BOOTSTRAP = 1000
SEED = 20261122
LOWER, UPPER = 2.5, 97.5


def load_returns() -> np.ndarray:
    frame = pd.read_csv(OUTPUT_DIR / "fx_daily_log_returns_2010_2025.csv")
    if frame.empty:
        raise ValueError("The daily-return file is empty.")
    values = frame[CURRENCIES].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("The daily changes contain missing or infinite values.")
    return values


def pair_values(matrix: np.ndarray) -> np.ndarray:
    return np.array([matrix[i, j] for i, j in combinations(range(len(CURRENCIES)), 2)])


def main() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    values = load_returns()
    observations = len(values)
    if observations <= BLOCK_LENGTH * 2:
        raise ValueError("Not enough observations for the block bootstrap.")

    baseline = np.corrcoef(values, rowvar=False)
    baseline_pairs = pair_values(baseline)

    published = pd.read_csv(OUTPUT_DIR / "currency_pair_correlations.csv")
    published = (
        published.set_index(["currency_1", "currency_2"])
        .loc[PAIRS]
        .reset_index()
    )
    if not np.allclose(
        baseline_pairs,
        published["correlation"].to_numpy(),
        rtol=1e-10,
        atol=1e-6,
    ):
        raise ValueError("Bootstrap baseline does not match the saved correlations.")

    rng = np.random.default_rng(SEED)
    n_blocks = int(np.ceil(observations / BLOCK_LENGTH))
    starts_max = observations - BLOCK_LENGTH
    boot = np.empty((N_BOOTSTRAP, len(PAIRS)))
    start = perf_counter()
    for replicate in range(N_BOOTSTRAP):
        starts = rng.integers(0, starts_max + 1, size=n_blocks)
        indices = np.concatenate(
            [np.arange(block_start, block_start + BLOCK_LENGTH) for block_start in starts]
        )[:observations]
        sample = values[indices]
        boot[replicate] = pair_values(np.corrcoef(sample, rowvar=False))
    elapsed = perf_counter() - start

    low = np.percentile(boot, LOWER, axis=0)
    high = np.percentile(boot, UPPER, axis=0)
    result = pd.DataFrame(
        {
            "pair": [f"{first}_{second}" for first, second in PAIRS],
            "correlation": baseline_pairs,
            "ci_low": low,
            "ci_high": high,
            "ci_width": high - low,
            "n_bootstrap": N_BOOTSTRAP,
            "block_length": BLOCK_LENGTH,
        }
    ).sort_values("correlation", ascending=False)
    result.to_csv(
        OUTPUT_DIR / "correlation_bootstrap_ci.csv",
        index=False,
        float_format="%.6f",
    )

    # Forest plot, strongest correlation at the top.
    ordered = result.reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9, 9))
    positions = np.arange(len(ordered))[::-1]
    ax.errorbar(
        ordered["correlation"],
        positions,
        xerr=[
            ordered["correlation"] - ordered["ci_low"],
            ordered["ci_high"] - ordered["correlation"],
        ],
        fmt="o",
        color="#1e3a8a",
        ecolor="#64748b",
        elinewidth=1.1,
        capsize=3,
        markersize=4,
    )
    ax.set_yticks(positions, ordered["pair"])
    ax.set_xlabel("Pearson correlation (95% moving-block bootstrap interval)")
    ax.set_title(
        "Full-Period Correlations with Bootstrap Intervals\n"
        f"{N_BOOTSTRAP} moving-block replicates; block length {BLOCK_LENGTH}"
    )
    ax.set_xlim(0, 1.02)
    ax.grid(axis="x", alpha=0.25)
    ax.axvline(0, color="#9ca3af", linewidth=0.8)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "correlation_bootstrap_ci.png", bbox_inches="tight")
    plt.close(fig)

    narrowest = ordered.loc[ordered["ci_width"].idxmin()]
    widest = ordered.loc[ordered["ci_width"].idxmax()]
    print(f"Bootstrap replicates: {N_BOOTSTRAP}; block length: {BLOCK_LENGTH}")
    print(f"Elapsed: {elapsed:.3f} s")
    print(
        f"Narrowest interval: {narrowest['pair']} "
        f"[{narrowest['ci_low']:.4f}, {narrowest['ci_high']:.4f}]"
    )
    print(
        f"Widest interval: {widest['pair']} "
        f"[{widest['ci_low']:.4f}, {widest['ci_high']:.4f}]"
    )
    print("\nSaved correlation_bootstrap_ci.csv and figures/correlation_bootstrap_ci.png")


if __name__ == "__main__":
    main()
