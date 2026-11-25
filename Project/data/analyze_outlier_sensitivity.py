"""Sensitivity of correlations and volatility to two extreme sessions.

The cleaned sample contains two well-known extreme dates: 2015-01-15 (the
Swiss National Bank discontinued the EUR/CHF floor) and 2016-06-24 (the
Brexit referendum result). This script recomputes the full-period Pearson
correlations and daily volatilities after dropping those rows, one at a time
and together. It describes sensitivity; it does not attribute causality.

Outputs
-------
outlier_sensitivity_correlations.csv
outlier_sensitivity_volatility.csv
figures/outlier_sensitivity.png
"""
from pathlib import Path
from itertools import combinations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

DATA_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = DATA_DIR / "analysis_output"
FIGURE_DIR = OUTPUT_DIR / "figures"
CURRENCIES = ["CNY", "USD", "JPY", "GBP", "HKD", "CHF", "AUD", "CAD"]
EVENTS = {
    "2015-01-15": "SNB discontinues the EUR/CHF floor",
    "2016-06-24": "Brexit referendum result",
}


def load_returns() -> pd.DataFrame:
    frame = pd.read_csv(
        OUTPUT_DIR / "fx_daily_log_returns_2010_2025.csv", parse_dates=["Date"]
    )
    if frame.empty:
        raise ValueError("The daily-return file is empty.")
    if frame["Date"].isna().any() or not frame["Date"].is_unique:
        raise ValueError("Dates must be valid and unique.")
    if not frame["Date"].is_monotonic_increasing:
        raise ValueError("Dates must be sorted in ascending order.")
    if not np.isfinite(frame[CURRENCIES].to_numpy(dtype=float)).all():
        raise ValueError("The daily changes contain missing or infinite values.")
    return frame


def scenario_frame(frame: pd.DataFrame, excluded: set[str]) -> pd.DataFrame:
    dates = frame["Date"].dt.strftime("%Y-%m-%d")
    keep = ~dates.isin(excluded)
    selected = frame.loc[keep, ["Date"] + CURRENCIES].copy()
    if len(selected) < 100:
        raise ValueError("Too few observations after exclusion.")
    return selected


def correlation_table(frame: pd.DataFrame) -> pd.DataFrame:
    values = frame[CURRENCIES]
    matrix = values.corr()
    rows = []
    for first, second in combinations(CURRENCIES, 2):
        rows.append(
            {
                "pair": f"{first}_{second}",
                "correlation": float(matrix.loc[first, second]),
            }
        )
    return pd.DataFrame(rows)


def volatility_table(frame: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "currency": CURRENCIES,
            "daily_volatility_pct": frame[CURRENCIES].std(ddof=1).to_numpy() * 100,
        }
    )


def main() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    frame = load_returns()
    dates = set(frame["Date"].dt.strftime("%Y-%m-%d"))
    missing_events = [date for date in EVENTS if date not in dates]
    if missing_events:
        raise ValueError(f"Event dates are absent from the sample: {missing_events}")

    scenarios = {
        "baseline": scenario_frame(frame, set()),
        "exclude_snb": scenario_frame(frame, {"2015-01-15"}),
        "exclude_brexit": scenario_frame(frame, {"2016-06-24"}),
        "exclude_both": scenario_frame(frame, {"2015-01-15", "2016-06-24"}),
    }

    correlations = {
        name: correlation_table(selected) for name, selected in scenarios.items()
    }
    merged = correlations["baseline"].rename(columns={"correlation": "baseline_r"})
    for name in ["exclude_snb", "exclude_brexit", "exclude_both"]:
        merged = merged.merge(
            correlations[name].rename(columns={"correlation": f"{name}_r"}),
            on="pair",
            how="inner",
        )
    merged["delta_both"] = merged["exclude_both_r"] - merged["baseline_r"]
    merged["absolute_delta_both"] = merged["delta_both"].abs()
    merged = merged.sort_values("absolute_delta_both", ascending=False).reset_index(drop=True)
    merged.to_csv(
        OUTPUT_DIR / "outlier_sensitivity_correlations.csv",
        index=False,
        float_format="%.9f",
    )

    volatility = volatility_table(scenarios["baseline"]).rename(
        columns={"daily_volatility_pct": "baseline_volatility_pct"}
    )
    for name in ["exclude_snb", "exclude_brexit", "exclude_both"]:
        volatility = volatility.merge(
            volatility_table(scenarios[name]).rename(
                columns={"daily_volatility_pct": f"{name}_volatility_pct"}
            ),
            on="currency",
            how="inner",
        )
    volatility["delta_both_pct_points"] = (
        volatility["exclude_both_volatility_pct"] - volatility["baseline_volatility_pct"]
    )
    volatility = volatility.sort_values("delta_both_pct_points").reset_index(drop=True)
    volatility.to_csv(
        OUTPUT_DIR / "outlier_sensitivity_volatility.csv",
        index=False,
        float_format="%.9f",
    )

    rank_correlation = spearmanr(merged["baseline_r"], merged["exclude_both_r"]).statistic
    largest = merged.iloc[0]
    largest_volatility = volatility.loc[
        volatility["delta_both_pct_points"].abs().idxmax()
    ]
    print(
        f"Spearman rank correlation of the 28 full-period correlations "
        f"(baseline vs exclude both): {rank_correlation:.6f}"
    )
    print(
        f"Largest absolute change: {largest['pair']} "
        f"{largest['baseline_r']:.6f} -> {largest['exclude_both_r']:.6f} "
        f"(delta {largest['delta_both']:+.6f})"
    )
    print(
        f"Largest absolute volatility change: "
        f"{largest_volatility['currency']} "
        f"{largest_volatility['delta_both_pct_points']:+.6f} percentage points"
    )

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    ax = axes[0]
    ax.scatter(
        merged["baseline_r"],
        merged["exclude_both_r"],
        color="#2563eb",
        s=30,
        alpha=0.8,
    )
    limits = [
        min(merged["baseline_r"].min(), merged["exclude_both_r"].min()) - 0.03,
        1.0,
    ]
    ax.plot(limits, limits, linestyle="--", color="#9ca3af", linewidth=1)
    offsets = [(6, 6), (6, -14), (-48, 8), (-48, -16)]
    for row, offset in zip(merged.head(4).itertuples(), offsets):
        ax.annotate(
            row.pair,
            (row.baseline_r, row.exclude_both_r),
            textcoords="offset points",
            xytext=offset,
            fontsize=8,
        )
    ax.set_xlim(*limits)
    ax.set_ylim(*limits)
    ax.set_xlabel("Baseline full-period correlation")
    ax.set_ylabel("Correlation excluding both extreme dates")
    ax.set_title("All 28 pairs: baseline vs outlier-excluded")
    ax.grid(alpha=0.25)

    ax = axes[1]
    colors = ["#b91c1c" if value < 0 else "#0d9488" for value in volatility["delta_both_pct_points"]]
    ax.barh(
        volatility["currency"],
        volatility["delta_both_pct_points"],
        color=colors,
        height=0.6,
    )
    ax.axvline(0, color="#475569", linewidth=0.8)
    ax.set_xlabel("Change in daily volatility (percentage points)")
    ax.set_title("Daily volatility after excluding both dates")
    ax.grid(axis="x", alpha=0.25)

    fig.suptitle(
        "Sensitivity to 2015-01-15 (SNB) and 2016-06-24 (Brexit)\n"
        "Standard deviations of daily log changes; not annualized",
        fontsize=14,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(FIGURE_DIR / "outlier_sensitivity.png", bbox_inches="tight")
    plt.close(fig)

    print("\nSaved outlier_sensitivity_correlations.csv, "
          "outlier_sensitivity_volatility.csv and figures/outlier_sensitivity.png")


if __name__ == "__main__":
    main()
