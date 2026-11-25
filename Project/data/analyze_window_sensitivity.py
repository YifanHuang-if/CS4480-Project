"""Rolling-correlation window sensitivity.

The main analysis uses a 60-observation window. This script repeats the
rolling correlation for four representative pairs with 30, 60 and 120
observations to show whether the qualitative conclusions depend on that
choice. It does not search for an optimal window.

Outputs
-------
window_sensitivity_summary.csv
figures/window_sensitivity.png
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = DATA_DIR / "analysis_output"
FIGURE_DIR = OUTPUT_DIR / "figures"
CURRENCIES = ["CNY", "USD", "JPY", "GBP", "HKD", "CHF", "AUD", "CAD"]
PAIRS = [("USD", "HKD"), ("CNY", "USD"), ("AUD", "CAD"), ("AUD", "JPY")]
WINDOWS = [30, 60, 120]
COLORS = {30: "#b45309", 60: "#2563eb", 120: "#0d9488"}


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


def main() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    frame = load_returns().set_index("Date")
    rows = []
    series_by_window: dict[int, dict[str, pd.Series]] = {}

    for window in WINDOWS:
        series_by_window[window] = {}
        for first, second in PAIRS:
            name = f"{first}_{second}"
            rolling = (
                frame[first]
                .rolling(window, min_periods=window)
                .corr(frame[second])
                .dropna()
            )
            if rolling.empty or not np.isfinite(rolling.to_numpy()).all():
                raise ValueError(f"No valid rolling values for {name} at window {window}.")
            series_by_window[window][name] = rolling
            rows.append(
                {
                    "pair": name,
                    "window": window,
                    "valid_windows": len(rolling),
                    "mean_correlation": rolling.mean(),
                    "std_correlation": rolling.std(),
                    "min_correlation": rolling.min(),
                    "min_date": rolling.idxmin().strftime("%Y-%m-%d"),
                    "max_correlation": rolling.max(),
                    "max_date": rolling.idxmax().strftime("%Y-%m-%d"),
                }
            )

    summary = pd.DataFrame(rows)
    summary.to_csv(
        OUTPUT_DIR / "window_sensitivity_summary.csv",
        index=False,
        float_format="%.6f",
    )

    fig, axes = plt.subplots(2, 2, figsize=(14, 8), sharex=True, sharey=True)
    for ax, (first, second) in zip(axes.flat, PAIRS):
        name = f"{first}_{second}"
        full_period = float(frame[first].corr(frame[second]))
        for window in WINDOWS:
            ax.plot(
                series_by_window[window][name].index,
                series_by_window[window][name].to_numpy(),
                linewidth=0.9,
                color=COLORS[window],
                label=f"{window}-observation window",
            )
        ax.axhline(
            full_period,
            color="black",
            linestyle="--",
            linewidth=1.0,
            label=f"Full-period r = {full_period:.3f}",
        )
        ax.axhline(0, color="#9ca3af", linewidth=0.7)
        ax.set_title(name.replace("_", " and "))
        ax.set_ylim(-1.05, 1.05)
        ax.set_ylabel("Pearson correlation")
        ax.grid(alpha=0.25)
        if ax is axes[1, 0] or ax is axes[1, 1]:
            ax.set_xlabel("Date")
    axes[0, 0].legend(fontsize=8, frameon=False, loc="lower left")
    fig.suptitle(
        "Window Sensitivity of 30/60/120-Observation Rolling Correlations\n"
        "Foreign currency units per EUR, 2010-2025",
        fontsize=14,
    )
    fig.autofmt_xdate()
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(FIGURE_DIR / "window_sensitivity.png", bbox_inches="tight")
    plt.close(fig)

    print(summary.to_string(index=False))
    print("\nSaved window_sensitivity_summary.csv and figures/window_sensitivity.png")


if __name__ == "__main__":
    main()
