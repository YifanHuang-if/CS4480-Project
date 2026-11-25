"""Regenerate every figure from code, without re-running timing benchmarks.

The descriptive analyses are recomputed from the cleaned data; the parallel
benchmark figures are redrawn from the frozen CSVs (`pool_reuse_*`,
`scaling_benchmark_summary.csv`, `chunksize_sweep.csv`). Timing numbers
therefore do not drift when only the figures are rebuilt.

Run from `Project/`:

    python data/regenerate_figures.py
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = DATA_DIR / "analysis_output"
FIGURE_DIR = OUTPUT_DIR / "figures"

EXPECTED_FIGURES = {
    "indexed_exchange_rates.png",
    "daily_log_returns.png",
    "monthly_exchange_rate_heatmaps.png",
    "daily_change_distributions.png",
    "annual_daily_volatility_pct.png",
    "rolling_daily_volatility_60d.png",
    "currency_correlation_heatmap.png",
    "currency_clustering_dendrogram.png",
    "rolling_correlations_60d.png",
    "parallel_one_shot_runtime.png",
    "parallel_reused_pool_runtime.png",
    "parallel_reused_pool_speedup.png",
    "daily_change_boxplots.png",
    "correlation_scatter_examples.png",
    "volatility_comparison.png",
    "parallel_scaling_runtime.png",
    "parallel_scaling_speedup.png",
    "parallel_thread_vs_process.png",
    "parallel_chunksize_sweep.png",
    "window_sensitivity.png",
    "outlier_sensitivity.png",
    "correlation_bootstrap_ci.png",
}

# Modules whose main() recomputes a descriptive result and writes its figure.
DESCRIPTIVE_MODULES = [
    "plot_exchange_rates",
    "analyze_correlations",
    "cluster_currencies",
    "analyze_rolling_volatility",
    "analyze_annual_volatility",
    "analyze_rolling_correlations",
    "analyze_monthly_changes",
    "analyze_extreme_changes",
    "plot_distributions",
    "analyze_window_sensitivity",
    "analyze_outlier_sensitivity",
    "bootstrap_correlations",
]

# plot_parallel_performance reads frozen benchmark CSVs and only plots.
PLOT_ONLY_MODULES = ["plot_parallel_performance"]


def run_module(name: str) -> None:
    module = importlib.import_module(name)
    if hasattr(module, "main"):
        module.main()
    else:
        # plot_exchange_rates.py and analyze_correlations.py execute at import.
        print(f"  {name}: top-level script executed on import", flush=True)


def draw_benchmark_figures_from_saved_tables() -> None:
    """Redraw scaling and chunksize figures from their frozen summaries."""
    import benchmark_chunksize
    import scaling_parallel_correlations

    scaling_summary = pd.read_csv(OUTPUT_DIR / "scaling_benchmark_summary.csv")
    scaling_parallel_correlations.plot_runtime(scaling_summary)
    scaling_parallel_correlations.plot_speedup(scaling_summary)
    scaling_parallel_correlations.plot_thread_vs_process(scaling_summary)

    chunksize_summary = pd.read_csv(OUTPUT_DIR / "chunksize_sweep.csv")
    benchmark_chunksize.plot_chunksize(chunksize_summary)


def main() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    for name in DESCRIPTIVE_MODULES + PLOT_ONLY_MODULES:
        print(f"== {name} ==", flush=True)
        run_module(name)

    print("== scaling/chunksize figures from saved tables ==", flush=True)
    draw_benchmark_figures_from_saved_tables()

    present = {path.name for path in FIGURE_DIR.glob("*.png")}
    missing = EXPECTED_FIGURES - present
    if missing:
        raise RuntimeError(f"Missing figures after regeneration: {sorted(missing)}")
    print(f"\nRegenerated {len(present)} figures in {FIGURE_DIR}")
    for name in sorted(present):
        print(f"  {name}")


if __name__ == "__main__":
    main()
