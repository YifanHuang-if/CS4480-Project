"""Boxplots, scatterplots and a volatility comparison for the EUR-based FX data.

Outputs
-------
figures/daily_change_boxplots.png
figures/correlation_scatter_examples.png
figures/volatility_comparison.png

The boxplots use the 4,096 daily log changes per currency. The scatter panels
contrast the strongest and weakest full-period correlations. The volatility
panel compares the full-period daily standard deviation with the largest
60-observation rolling standard deviation.
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
SCATTER_PAIRS = [("USD", "HKD"), ("CNY", "USD"), ("CHF", "AUD")]

plt.rcParams.update(
    {
        "figure.dpi": 120,
        "savefig.dpi": 220,
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
    }
)


def load_returns() -> pd.DataFrame:
    """Load daily log changes and run structural checks."""
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


def draw_boxplots(values: pd.DataFrame) -> None:
    """Boxplots on the full range and on a zoomed range."""
    data = [values[currency].to_numpy(dtype=float) * 100 for currency in CURRENCIES]
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    for ax, zoom in zip(axes, [False, True]):
        boxes = ax.boxplot(
            data,
            tick_labels=CURRENCIES,
            whis=1.5,
            showmeans=True,
            patch_artist=True,
            widths=0.55,
            medianprops={"color": "#08306b", "linewidth": 1.8},
            meanprops={
                "marker": "D",
                "markerfacecolor": "white",
                "markeredgecolor": "#08306b",
                "markersize": 4,
            },
            flierprops={
                "marker": "o",
                "markerfacecolor": "none",
                "markeredgecolor": "#6b7280",
                "markersize": 2.5,
                "alpha": 0.55,
            },
        )
        for patch in boxes["boxes"]:
            patch.set_facecolor("#9ecae1")
            patch.set_edgecolor("#1f4e79")
            patch.set_alpha(0.85)

        ax.set_title("Full observed range" if not zoom else "Zoom on the interquartile range")
        ax.set_ylabel("Daily log change (%)")
        ax.axhline(0, color="#475569", linewidth=0.8)
        ax.grid(axis="y", alpha=0.25)

        if zoom:
            ax.set_ylim(-3.5, 3.5)
            ax.annotate(
                "CHF minimum -15.55%\n(below the axis)",
                xy=(5.62, -3.25),
                fontsize=8.5,
                color="#7f1d1d",
                ha="left",
                va="bottom",
            )
            ax.annotate(
                "CHF maximum +8.00%\n(above the axis)",
                xy=(5.62, 3.18),
                fontsize=8.5,
                color="#7f1d1d",
                ha="left",
                va="top",
            )

    fig.suptitle(
        "Daily Log Changes by Currency, 2010-2025\n"
        "Boxes: interquartile range; whiskers: 1.5 x IQR; diamonds: means; dots: outliers",
        fontsize=14,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(FIGURE_DIR / "daily_change_boxplots.png", bbox_inches="tight")
    plt.close(fig)


def draw_scatter(values: pd.DataFrame) -> None:
    """Scatterplots for strong and weak full-period correlations."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for ax, (first, second) in zip(axes, SCATTER_PAIRS):
        x = values[first].to_numpy(dtype=float) * 100
        y = values[second].to_numpy(dtype=float) * 100
        coefficient = float(np.corrcoef(x, y)[0, 1])
        expected = float(values[first].corr(values[second]))
        if not np.isclose(coefficient, expected, rtol=1e-10, atol=1e-12):
            raise ValueError(f"Correlation mismatch for {first}-{second}.")

        ax.scatter(
            x,
            y,
            s=9,
            alpha=0.22,
            color="#2563eb",
            edgecolors="none",
            rasterized=True,
        )
        slope, intercept = np.polyfit(x, y, 1)
        line_x = np.linspace(x.min(), x.max(), 100)
        ax.plot(line_x, slope * line_x + intercept, color="#b91c1c", linewidth=1.8)
        ax.set_title(f"{first} vs {second}\nr = {coefficient:.3f}")
        ax.set_xlabel(f"{first} daily log change (%)")
        ax.set_ylabel(f"{second} daily log change (%)")
        ax.grid(alpha=0.25)

    fig.suptitle(
        "Daily Log Changes: Strongest and Weakest Full-Period Correlations\n"
        "Foreign currency units per EUR, 2010-2025; red line: ordinary least squares",
        fontsize=14,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(FIGURE_DIR / "correlation_scatter_examples.png", bbox_inches="tight")
    plt.close(fig)


def draw_volatility_comparison() -> None:
    """Compare full-period and maximum rolling daily volatility."""
    summary = pd.read_csv(OUTPUT_DIR / "daily_returns_summary.csv")
    rolling = pd.read_csv(OUTPUT_DIR / "rolling_volatility_summary_60d.csv")
    merged = summary.merge(
        rolling[["currency", "max_daily_volatility_pct"]], on="currency", how="inner"
    )
    if len(merged) != len(CURRENCIES):
        raise ValueError("Volatility summaries do not cover all eight currencies.")

    merged = merged.sort_values("daily_volatility_pct").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(11, 5.8))
    positions = np.arange(len(merged))
    bars = ax.barh(
        positions,
        merged["daily_volatility_pct"],
        color="#60a5fa",
        height=0.55,
        label="Full-period daily volatility",
    )
    ax.scatter(
        merged["max_daily_volatility_pct"],
        positions,
        marker="D",
        color="#b91c1c",
        zorder=3,
        label="Maximum 60-observation rolling volatility",
    )
    ax.set_yticks(positions, merged["currency"])
    ax.set_xlabel("Daily volatility (%)")
    ax.set_title(
        "Full-Period vs Maximum Rolling Daily Volatility\n"
        "Standard deviations of daily log changes; not annualized"
    )
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.13),
        ncol=2,
        frameon=False,
    )
    ax.grid(axis="x", alpha=0.25)

    for bar, value in zip(bars, merged["daily_volatility_pct"]):
        ax.text(
            value + 0.015,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.3f}",
            va="center",
            fontsize=8.5,
            color="#1e3a8a",
        )
    chf = merged.loc[merged["currency"] == "CHF"]
    if not chf.empty:
        ax.annotate(
            f"CHF 60-day peak {chf['max_daily_volatility_pct'].iloc[0]:.3f}%",
            xy=(chf["max_daily_volatility_pct"].iloc[0], chf.index[0]),
            xytext=(1.42, chf.index[0] + 0.75),
            fontsize=8.5,
            color="#7f1d1d",
            arrowprops={"arrowstyle": "->", "color": "#7f1d1d", "lw": 0.9},
        )

    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "volatility_comparison.png", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    frame = load_returns()
    values = frame.set_index("Date")[CURRENCIES]
    draw_boxplots(values)
    draw_scatter(values)
    draw_volatility_comparison()
    print("Saved:")
    print("  figures/daily_change_boxplots.png")
    print("  figures/correlation_scatter_examples.png")
    print("  figures/volatility_comparison.png")


if __name__ == "__main__":
    main()
