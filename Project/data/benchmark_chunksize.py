"""Chunksize sensitivity for the 28-pair rolling-correlation workload.

Batching changes how many tasks travel in one process-pool message. This
script holds the workload fixed (28 pairs, 4,096 observations, 60-observation
window) and sweeps the chunksize for 2, 4 and 8 workers. It uses a barrier so
that every worker is alive before timing starts.

Outputs
-------
chunksize_sweep.csv
figures/parallel_chunksize_sweep.png
"""
from __future__ import annotations

import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
from itertools import combinations
from pathlib import Path
from time import perf_counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from benchmark_rolling_correlations import (
    CURRENCIES,
    OUTPUT_DIR,
    WINDOW,
    calculate_pair,
)

WORKERS = (2, 4, 8)
CHUNKSIZES = (1, 2, 4, 7, 14, 28)
REPEATS = 10
FIGURE_DIR = OUTPUT_DIR / "figures"


def ready(barrier) -> None:
    barrier.wait(timeout=120)


def plot_chunksize(summary: pd.DataFrame) -> None:
    """Draw the chunksize figure from a saved sweep table."""
    serial_ms = float(summary["serial_median_ms"].iloc[0])
    fig, ax = plt.subplots(figsize=(10, 5.8))
    for workers, color, marker in [(2, "#64748b", "o"), (4, "#2563eb", "s"), (8, "#0d9488", "^")]:
        frame = summary[summary.workers == workers].sort_values("chunksize")
        ax.plot(frame["chunksize"], frame["median_ms"], marker=marker, color=color, label=f"{workers} workers")
    ax.axhline(serial_ms, color="black", linestyle="--", linewidth=1.0, label="Serial median")
    ax.set_xscale("log", base=2)
    ax.set_xticks(CHUNKSIZES)
    ax.set_xticklabels([str(value) for value in CHUNKSIZES])
    ax.set_xlabel("Chunksize (tasks per message)")
    ax.set_ylabel("Median runtime (milliseconds)")
    ax.set_title(
        "Chunksize Sensitivity, 28 Pairs x 4,096 Observations\n"
        "Medians of ten repetitions; every worker started before timing"
    )
    ax.legend(frameon=False)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "parallel_chunksize_sweep.png", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(OUTPUT_DIR / "fx_daily_log_returns_2010_2025.csv")
    if not np.isfinite(df[CURRENCIES].to_numpy(dtype=float)).all():
        raise ValueError("The input contains missing or infinite values.")
    tasks = [
        (f"{first}_{second}", df[first].to_numpy(), df[second].to_numpy())
        for first, second in combinations(CURRENCIES, 2)
    ]
    reference = dict(map(calculate_pair, tasks))
    if not all(np.isfinite(values).all() for values in reference.values()):
        raise ValueError("Undefined reference correlations.")

    records = []
    serial_times = []
    for repeat in range(1, REPEATS + 1):
        start = perf_counter()
        serial_result = list(map(calculate_pair, tasks))
        serial_times.append(perf_counter() - start)
        for name, values in serial_result:
            np.testing.assert_allclose(values, reference[name], rtol=1e-10, atol=1e-12)
    serial_median = float(np.median(serial_times))

    for workers in WORKERS:
        context = mp.get_context("spawn")
        barrier = context.Barrier(workers)
        with ProcessPoolExecutor(
            max_workers=workers,
            mp_context=context,
            initializer=ready,
            initargs=(barrier,),
        ) as executor:
            warmup = list(executor.map(calculate_pair, tasks))
            for name, values in warmup:
                np.testing.assert_allclose(values, reference[name], rtol=1e-10, atol=1e-12)
            for chunksize in CHUNKSIZES:
                times = []
                for repeat in range(1, REPEATS + 1):
                    start = perf_counter()
                    result = list(executor.map(calculate_pair, tasks, chunksize=chunksize))
                    times.append(perf_counter() - start)
                    for name, values in result:
                        np.testing.assert_allclose(
                            values, reference[name], rtol=1e-10, atol=1e-12
                        )
                records.append(
                    {
                        "workers": workers,
                        "chunksize": chunksize,
                        "runs": REPEATS,
                        "median_ms": float(np.median(times)) * 1000,
                        "min_ms": float(np.min(times)) * 1000,
                        "max_ms": float(np.max(times)) * 1000,
                        "serial_median_ms": serial_median * 1000,
                        "speedup": serial_median / float(np.median(times)),
                        "results_match": True,
                    }
                )
            print(f"Worker group {workers} complete", flush=True)

    summary = pd.DataFrame(records)
    summary.to_csv(OUTPUT_DIR / "chunksize_sweep.csv", index=False, float_format="%.6f")
    plot_chunksize(summary)

    print(summary.to_string(index=False))
    print("\nSaved chunksize_sweep.csv and figures/parallel_chunksize_sweep.png")


if __name__ == "__main__":
    main()
