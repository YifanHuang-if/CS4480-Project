"""Scaling experiment for rolling-correlation workloads.

The real-data benchmark (benchmark_pool_reuse.py) fixes the workload at 28
pairs x 4,096 observations. This script varies (a) the number of series and
therefore the number of pairs, and (b) the number of observations, then
measures serial, process-pool and thread-pool runtimes for 2, 4 and 8 workers.

Synthetic factor-model series are used so that the workload can grow without
changing the real-data findings. The synthetic data are a benchmark device,
not an empirical result. Worker-local data is broadcast once per process; each
task is a pair index, so the measurement is not dominated by re-pickling the
whole series for every pair.

Outputs
-------
scaling_benchmark_runs.csv
scaling_benchmark_summary.csv
scaling_benchmark_environment.csv
figures/parallel_scaling_runtime.png
figures/parallel_scaling_speedup.png
figures/parallel_thread_vs_process.png
note/parallel_scaling_analysis.md
"""
from __future__ import annotations

import math
import multiprocessing as mp
import os
import platform
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from itertools import combinations
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = DATA_DIR / "analysis_output"
FIGURE_DIR = OUTPUT_DIR / "figures"
NOTE_DIR = DATA_DIR.parent / "note"

WINDOW = 60
REPEATS = 5
WORKERS = (2, 4, 8)
SEED = 20261122

# (number of series, observations)
SERIES_WORKLOADS = [(8, 4096), (16, 4096), (32, 4096), (64, 4096)]
OBSERVATION_WORKLOADS = [(8, 1024), (8, 2048), (8, 4096)]
WORKLOADS = list(dict.fromkeys(SERIES_WORKLOADS + OBSERVATION_WORKLOADS))

_DATA: np.ndarray | None = None
_WEIGHTS: np.ndarray | None = None


def _pyplot():
    """Import matplotlib lazily so spawned workers do not pay for it."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

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
    return plt


def make_factor_series(n_series: int, observations: int, seed: int) -> np.ndarray:
    """Create correlated series with a fixed-seed factor model.

    Three common factors plus idiosyncratic t(5) noise produce a realistic
    mixture of strong and weak pairwise correlations. The scale is close to
    daily FX log changes (a few tenths of a percent).
    """
    rng = np.random.default_rng(seed)
    n_factors = min(3, n_series)
    factors = rng.standard_t(df=5, size=(observations, n_factors)) * 0.006
    loadings = rng.normal(size=(n_series, n_factors)) / math.sqrt(n_factors)
    idiosyncratic = rng.standard_t(df=5, size=(observations, n_series)) * 0.004
    data = factors @ loadings.T + idiosyncratic
    if not np.isfinite(data).all():
        raise ValueError("Synthetic data contain non-finite values.")
    if (np.std(data, axis=0) == 0).any():
        raise ValueError("A synthetic series is constant.")
    return np.ascontiguousarray(data, dtype=np.float64)


def pair_tasks(n_series: int) -> list[tuple[int, int]]:
    return list(combinations(range(n_series), 2))


def set_shared_data(data: np.ndarray, weights: np.ndarray) -> None:
    global _DATA, _WEIGHTS
    _DATA = data
    _WEIGHTS = weights


def init_process_worker(
    data: np.ndarray, weights: np.ndarray, barrier
) -> None:
    set_shared_data(data, weights)
    # All workers must be alive before any measured run; otherwise the lazy
    # executor start-up leaks into the timing.
    barrier.wait(timeout=120)


def _digest_pair(task: tuple[int, int]) -> tuple[float, ...]:
    if _DATA is None or _WEIGHTS is None:
        raise RuntimeError("Worker data were not initialised.")
    first, second = task
    series = (
        pd.Series(_DATA[:, first])
        .rolling(WINDOW, min_periods=WINDOW)
        .corr(pd.Series(_DATA[:, second]))
        .to_numpy()[WINDOW - 1:]
    )
    if len(series) != len(_WEIGHTS):
        raise ValueError("Rolling series length does not match the checksum weights.")
    if not np.isfinite(series).all():
        raise ValueError(f"Undefined rolling correlation for pair {task}.")
    checksum = float(np.dot(series, _WEIGHTS))
    return (
        float(task[0]),
        float(task[1]),
        checksum,
        float(series.mean()),
        float(series.std(ddof=1)),
        float(series.min()),
        float(series.max()),
    )


def chunk_digest(chunk: list[tuple[int, int]]) -> list[tuple[float, ...]]:
    return [_digest_pair(task) for task in chunk]


def digest_map(items: list[tuple[float, ...]]) -> dict[tuple[int, int], tuple[float, ...]]:
    return {(int(row[0]), int(row[1])): row[2:] for row in items}


def check_results(
    items: list[tuple[float, ...]],
    reference: dict[tuple[int, int], tuple[float, ...]],
) -> float:
    if len(items) != len(reference):
        raise ValueError("The parallel result does not contain every pair.")
    maximum_difference = 0.0
    for row in items:
        key = (int(row[0]), int(row[1]))
        if key not in reference:
            raise ValueError(f"Unexpected pair in the result: {key}.")
        expected = reference[key]
        difference = abs(row[2] - expected[0])
        maximum_difference = max(maximum_difference, difference)
        tolerances = [(1e-9, 1e-9)] + [(1e-10, 1e-12)] * 4
        for observed, target, (rtol, atol) in zip(row[2:], expected, tolerances):
            if not np.isclose(observed, target, rtol=rtol, atol=atol):
                raise ValueError(
                    f"Result mismatch for pair {key}: {observed} vs {target}."
                )
    return maximum_difference


def split_chunks(tasks: list[tuple[int, int]], workers: int) -> list[list[tuple[int, int]]]:
    chunk_size = max(1, math.ceil(len(tasks) / workers))
    return [tasks[start:start + chunk_size] for start in range(0, len(tasks), chunk_size)]


def flatten(blocks: list[list[tuple[float, ...]]]) -> list[tuple[float, ...]]:
    return [row for block in blocks for row in block]


def timed(callable_) -> tuple[list[tuple[float, ...]], float]:
    start = perf_counter()
    result = callable_()
    return result, perf_counter() - start


def build_workload(n_series: int, observations: int) -> dict:
    data = make_factor_series(n_series, observations, seed=SEED + n_series * 1000 + observations)
    tasks = pair_tasks(n_series)
    weights = np.random.default_rng(SEED + 7).normal(size=observations - WINDOW + 1)
    weights = np.ascontiguousarray(weights, dtype=np.float64)
    set_shared_data(data, weights)
    reference_items = [_digest_pair(task) for task in tasks]
    return {
        "data": data,
        "tasks": tasks,
        "weights": weights,
        "reference": digest_map(reference_items),
        "label": f"n{n_series}_T{observations}",
        "n_series": n_series,
        "observations": observations,
    }


def main() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    NOTE_DIR.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []
    setup_records: list[dict] = []

    for n_series, observations in WORKLOADS:
        workload = build_workload(n_series, observations)
        label = workload["label"]
        tasks = workload["tasks"]
        data = workload["data"]
        weights = workload["weights"]
        reference = workload["reference"]
        print(
            f"Workload {label}: {n_series} series, {len(tasks)} pairs, "
            f"{observations} observations",
            flush=True,
        )

        # Serial baseline, repeated so its median is comparable with the pools.
        for repeat in range(1, REPEATS + 1):
            result, elapsed = timed(lambda: [_digest_pair(task) for task in tasks])
            difference = check_results(result, reference)
            records.append(
                {
                    "workload": label,
                    "n_series": n_series,
                    "pairs": len(tasks),
                    "observations": observations,
                    "window": WINDOW,
                    "method": "serial",
                    "workers": 1,
                    "chunksize": 1,
                    "repeat": repeat,
                    "seconds": elapsed,
                    "results_match": True,
                    "max_absolute_difference": difference,
                }
            )

        for workers in WORKERS:
            chunks = split_chunks(tasks, workers)
            chunk_size = len(chunks[0]) if chunks else 0

            context = mp.get_context("spawn")
            barrier = context.Barrier(workers)
            process_pool = ProcessPoolExecutor(
                max_workers=workers,
                mp_context=context,
                initializer=init_process_worker,
                initargs=(data, weights, barrier),
            )
            # One single-pair task per worker forces every worker to start and
            # release the barrier before the first measured run.
            warm_tasks = [[task] for task in tasks[:workers]]
            try:
                start = perf_counter()
                warm = flatten(list(process_pool.map(chunk_digest, warm_tasks)))
                process_setup = perf_counter() - start
                if len(process_pool._processes) != workers:
                    raise RuntimeError(
                        f"Expected {workers} workers, "
                        f"found {len(process_pool._processes)}."
                    )
            except BaseException:
                process_pool.shutdown(wait=True, cancel_futures=True)
                raise

            thread_pool = ThreadPoolExecutor(max_workers=workers)
            set_shared_data(data, weights)
            try:
                start = perf_counter()
                warm_thread = flatten(list(thread_pool.map(chunk_digest, warm_tasks)))
                thread_setup = perf_counter() - start
            except BaseException:
                process_pool.shutdown(wait=True, cancel_futures=True)
                thread_pool.shutdown(wait=True, cancel_futures=True)
                raise

            methods = ["process_shared", "thread_shared"]
            for repeat in range(1, REPEATS + 1):
                offset = (repeat - 1) % len(methods)
                for method in methods[offset:] + methods[:offset]:
                    if method == "process_shared":
                        result, elapsed = timed(
                            lambda: flatten(list(process_pool.map(chunk_digest, chunks)))
                        )
                    else:
                        result, elapsed = timed(
                            lambda: flatten(list(thread_pool.map(chunk_digest, chunks)))
                        )
                    difference = check_results(result, reference)
                    records.append(
                        {
                            "workload": label,
                            "n_series": n_series,
                            "pairs": len(tasks),
                            "observations": observations,
                            "window": WINDOW,
                            "method": method,
                            "workers": workers,
                            "chunksize": chunk_size,
                            "repeat": repeat,
                            "seconds": elapsed,
                            "results_match": True,
                            "max_absolute_difference": difference,
                        }
                    )

            start = perf_counter()
            process_pool.shutdown(wait=True)
            process_shutdown = perf_counter() - start
            start = perf_counter()
            thread_pool.shutdown(wait=True)
            thread_shutdown = perf_counter() - start
            setup_records.append(
                {
                    "workload": label,
                    "workers": workers,
                    "process_setup_seconds": process_setup,
                    "process_shutdown_seconds": process_shutdown,
                    "thread_setup_seconds": thread_setup,
                    "thread_shutdown_seconds": thread_shutdown,
                    "chunksize": chunk_size,
                }
            )
            print(
                f"  workers={workers}: process setup {process_setup:.3f} s, "
                f"shutdown {process_shutdown:.3f} s",
                flush=True,
            )

    runs = pd.DataFrame(records)
    if not runs["results_match"].all():
        raise RuntimeError("At least one configuration failed correctness validation.")

    summary = runs.groupby(
        ["workload", "n_series", "pairs", "observations", "window", "method", "workers"],
        as_index=False,
    ).agg(
        runs=("seconds", "count"),
        median_seconds=("seconds", "median"),
        min_seconds=("seconds", "min"),
        max_seconds=("seconds", "max"),
        all_results_match=("results_match", "all"),
        max_absolute_difference=("max_absolute_difference", "max"),
    )
    serial = summary[summary.method == "serial"].set_index("workload").median_seconds
    summary["speedup"] = summary.workload.map(serial) / summary.median_seconds
    summary["efficiency"] = summary.speedup / summary.workers
    summary = summary.sort_values(["observations", "n_series", "method", "workers"]).reset_index(drop=True)

    runs.to_csv(OUTPUT_DIR / "scaling_benchmark_runs.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "scaling_benchmark_summary.csv", index=False, float_format="%.9f")
    pd.DataFrame(setup_records).to_csv(OUTPUT_DIR / "scaling_benchmark_setup.csv", index=False)

    environment = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "logical_cpus": os.cpu_count(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "window": WINDOW,
        "repeats": REPEATS,
        "workers": ", ".join(str(value) for value in WORKERS),
        "seed": SEED,
        "synthetic_model": "Three-factor t(5) model plus idiosyncratic t(5) noise",
        "workloads": ", ".join(f"{n}x{observations}" for n, observations in WORKLOADS),
        "timing_scope": "Map/loop call only; validation and CSV I/O excluded",
        "process_pool_data": "Worker-local copy broadcast once via initializer; tasks are pair indices",
        "thread_pool_data": "Shared in-process arrays; no serialisation",
        "baseline": "Serial median of five repetitions in the same workload",
    }
    pd.DataFrame(environment.items(), columns=["key", "value"]).to_csv(
        OUTPUT_DIR / "scaling_benchmark_environment.csv", index=False
    )

    plot_runtime(summary)
    plot_speedup(summary)
    plot_thread_vs_process(summary)
    write_note(summary, setup_records)
    print("\nScaling summary:")
    print(summary.to_string(index=False))


def plot_runtime(summary: pd.DataFrame) -> None:
    plt = _pyplot()
    series = summary[summary.observations == 4096]
    observations = summary[summary.n_series == 8]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.6))

    ax = axes[0]
    for method, workers, label, color, marker in [
        ("serial", 1, "Serial", "#475569", "o"),
        ("process_shared", 4, "Process pool, 4 workers", "#2563eb", "s"),
        ("process_shared", 8, "Process pool, 8 workers", "#0d9488", "^"),
    ]:
        frame = series[(series.method == method) & (series.workers == workers)]
        ax.plot(frame.pairs, frame.median_seconds, marker=marker, color=color, label=label)
    serial_series = series[(series.method == "serial")].set_index("pairs").median_seconds.sort_index()
    ax.plot(
        serial_series.index,
        serial_series.to_numpy() / 8,
        linestyle="--",
        color="#9ca3af",
        label="Ideal 8x (serial / 8)",
    )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Currency pairs in the workload")
    ax.set_ylabel("Median runtime (seconds, log scale)")
    ax.set_title("Workload size: number of pairs (4,096 observations)")
    ax.legend(fontsize=8.5, frameon=False)

    ax = axes[1]
    for method, workers, label, color, marker in [
        ("serial", 1, "Serial", "#475569", "o"),
        ("process_shared", 8, "Process pool, 8 workers", "#2563eb", "s"),
        ("thread_shared", 8, "Thread pool, 8 workers", "#b45309", "^"),
    ]:
        frame = observations[(observations.method == method) & (observations.workers == workers)]
        ax.plot(frame.observations, frame.median_seconds, marker=marker, color=color, label=label)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Observations per series")
    ax.set_ylabel("Median runtime (seconds, log scale)")
    ax.set_title("Workload size: observations (8 series)")
    ax.legend(fontsize=8.5, frameon=False)

    fig.suptitle(
        "Rolling-Correlation Runtime vs Workload Size\n"
        "60-observation windows; synthetic factor-model series; medians of five repetitions",
        fontsize=14,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(FIGURE_DIR / "parallel_scaling_runtime.png", bbox_inches="tight")
    plt.close(fig)


def plot_speedup(summary: pd.DataFrame) -> None:
    plt = _pyplot()
    series = summary[(summary.method == "process_shared") & (summary.observations == 4096)]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.4))

    ax = axes[0]
    for workers, color, marker in [(2, "#64748b", "o"), (4, "#2563eb", "s"), (8, "#0d9488", "^")]:
        frame = series[series.workers == workers].sort_values("pairs")
        ax.plot(frame.pairs, frame.speedup, marker=marker, color=color, label=f"{workers} workers")
    reference = series[series.workers == 8].set_index("pairs").sort_index()
    ax.plot(reference.index, np.full(len(reference), 8.0), linestyle="--", color="#9ca3af", label="Ideal 8x")
    ax.set_xscale("log")
    ax.set_xlabel("Currency pairs in the workload")
    ax.set_ylabel("Speedup vs serial median")
    ax.set_title("Speedup vs workload size")
    ax.legend(fontsize=9, frameon=False)

    ax = axes[1]
    for workers, color, marker in [(2, "#64748b", "o"), (4, "#2563eb", "s"), (8, "#0d9488", "^")]:
        frame = series[series.workers == workers].sort_values("pairs")
        ax.plot(frame.pairs, frame.efficiency, marker=marker, color=color, label=f"{workers} workers")
    ax.axhline(1.0, linestyle="--", color="#9ca3af", label="100% efficiency")
    ax.set_xscale("log")
    ax.set_ylim(0, 1.1)
    ax.set_xlabel("Currency pairs in the workload")
    ax.set_ylabel("Parallel efficiency (speedup / workers)")
    ax.set_title("Efficiency vs workload size")
    ax.legend(fontsize=9, frameon=False)

    fig.suptitle("Process-Pool Scaling, 4,096 Observations per Series", fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(FIGURE_DIR / "parallel_scaling_speedup.png", bbox_inches="tight")
    plt.close(fig)


def plot_thread_vs_process(summary: pd.DataFrame) -> None:
    plt = _pyplot()
    frame = summary[(summary.workload == "n64_T4096") & (summary.method.isin(["process_shared", "thread_shared"]))]
    fig, ax = plt.subplots(figsize=(9, 5.4))
    for method, label, color, marker in [
        ("process_shared", "Process pool", "#2563eb", "s"),
        ("thread_shared", "Thread pool", "#b45309", "^"),
    ]:
        rows = frame[frame.method == method].sort_values("workers")
        ax.plot(rows.workers, rows.speedup, marker=marker, color=color, label=label)
    ax.plot([2, 4, 8], [2, 4, 8], linestyle="--", color="#9ca3af", label="Ideal linear speedup")
    ax.set_xticks([2, 4, 8])
    ax.set_xlabel("Workers")
    ax.set_ylabel("Speedup vs serial median")
    ax.set_title(
        "Process vs Thread Pool: 2,016 Pairs x 4,096 Observations\n"
        "Medians of five repetitions; 60-observation windows"
    )
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "parallel_thread_vs_process.png", bbox_inches="tight")
    plt.close(fig)


def write_note(summary: pd.DataFrame, setup_records: list[dict]) -> None:
    def median(workload: str, method: str, workers: int) -> float:
        rows = summary[
            (summary.workload == workload)
            & (summary.method == method)
            & (summary.workers == workers)
        ]
        return float(rows.median_seconds.iloc[0])

    def speedup(workload: str, method: str, workers: int) -> float:
        rows = summary[
            (summary.workload == workload)
            & (summary.method == method)
            & (summary.workers == workers)
        ]
        return float(rows.speedup.iloc[0])

    lines = [
        "# Parallel Scaling Analysis",
        "",
        "## What was varied",
        "",
        "The real-data benchmark fixes the workload at 28 pairs and 4,096 observations. "
        "This experiment varies the number of synthetic factor-model series (8, 16, 32 and 64, "
        "giving 28, 120, 496 and 2,016 pairs) and the number of observations (1,024, 2,048 and "
        "4,096), then measures serial, process-pool and thread-pool runtimes for 2, 4 and 8 workers. "
        "Each configuration is measured five times; the median is reported.",
        "",
        "Worker-local data is broadcast once per process, so tasks are pair indices rather than "
        "copies of the series. This isolates computation and scheduling from repeated pickling. "
        "The per-task-array design remains measured at 28 pairs in `parallel_performance_analysis.md`.",
        "",
        "## Results",
        "",
        "| Workload | Pairs | Serial (ms) | Process 4w (ms) | Process 8w (ms) | Speedup 8w | Efficiency 8w |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    order = [
        ("n8_T1024", 8, 1024),
        ("n8_T2048", 8, 2048),
        ("n8_T4096", 8, 4096),
        ("n16_T4096", 16, 4096),
        ("n32_T4096", 32, 4096),
        ("n64_T4096", 64, 4096),
    ]
    for label, n_series, observations in order:
        pairs = int(summary[summary.workload == label].pairs.iloc[0])
        serial_ms = median(label, "serial", 1) * 1000
        process4 = median(label, "process_shared", 4) * 1000
        process8 = median(label, "process_shared", 8) * 1000
        speedup8 = speedup(label, "process_shared", 8)
        efficiency8 = float(
            summary[
                (summary.workload == label)
                & (summary.method == "process_shared")
                & (summary.workers == 8)
            ].efficiency.iloc[0]
        )
        lines.append(
            f"| {n_series} series, {observations} obs | {pairs} | {serial_ms:.2f} | "
            f"{process4:.2f} | {process8:.2f} | {speedup8:.2f}x | {efficiency8:.2f} |"
        )

    serial_small = median("n8_T4096", "serial", 1) * 1000
    serial_large = median("n64_T4096", "serial", 1) * 1000
    process8_small = median("n8_T4096", "process_shared", 8) * 1000
    process8_large = median("n64_T4096", "process_shared", 8) * 1000
    best_large = speedup("n64_T4096", "process_shared", 8)
    thread8_large = speedup("n64_T4096", "thread_shared", 8)

    lines += [
        "",
        "## Interpretation",
        "",
        f"As the workload grows from 28 pairs to 2,016 pairs, the serial median rises from "
        f"{serial_small:.2f} ms to {serial_large:.2f} ms, while the eight-worker process-pool "
        f"median rises from {process8_small:.2f} ms to {process8_large:.2f} ms. The eight-worker "
        f"speedup at 2,016 pairs is {best_large:.2f}x.",
        "",
        f"The thread-pool speedup at 2,016 pairs and eight workers is {thread8_large:.2f}x. "
        "Threads avoid serialisation but share the interpreter; processes pay serialisation and "
        "startup costs but are not limited by one Python interpreter. The comparison shows which "
        "constraint dominates at this workload size.",
        "",
        "The small-workload result is dominated by per-message and scheduling overhead. Speedup "
        "only approaches the worker count once the per-task computation is large enough to amortise "
        "that overhead. This is consistent with Amdahl's law and with the fixed-cost measurements in "
        "`parallel_performance_analysis.md`.",
        "",
        "## Caveats",
        "",
        "- The series are synthetic factor-model data used only to vary workload size. They do not "
        "replace the real-data findings in the exploratory and parallel notes.",
        "- The environment is one machine, one Python build and one execution session. The numbers "
        "are medians of five repetitions, not confidence intervals.",
        "- Process-pool timing includes map/scheduling and result collection but excludes pool "
        "startup and shutdown; startup and shutdown are recorded in `scaling_benchmark_setup.csv`.",
        "- The workload is CPU-bound rolling correlation; no I/O is included.",
        "",
        "## Files",
        "",
        "- `../data/analysis_output/scaling_benchmark_runs.csv`",
        "- `../data/analysis_output/scaling_benchmark_summary.csv`",
        "- `../data/analysis_output/scaling_benchmark_setup.csv`",
        "- `../data/analysis_output/scaling_benchmark_environment.csv`",
        "- `../data/analysis_output/figures/parallel_scaling_runtime.png`",
        "- `../data/analysis_output/figures/parallel_scaling_speedup.png`",
        "- `../data/analysis_output/figures/parallel_thread_vs_process.png`",
        "",
    ]
    (NOTE_DIR / "parallel_scaling_analysis.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
