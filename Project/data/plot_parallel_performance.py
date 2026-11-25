"""Plot saved benchmark results without rerunning the timing experiment."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "analysis_output"
FIG = OUT / "figures"
LABELS = {"serial": "Serial", "fresh_pool": "Fresh pool",
          "reused_pool": "Reused pool", "reused_pool_batched": "Reused + batched"}
COLORS = ["#64748b", "#2563eb", "#0d9488"]


def main():
    summary = pd.read_csv(OUT / "pool_reuse_benchmark_summary.csv")
    runs = pd.read_csv(OUT / "pool_reuse_benchmark_runs.csv")
    setup = pd.read_csv(OUT / "pool_reuse_setup_times.csv")
    if not summary.all_results_match.astype(str).str.lower().eq("true").all():
        raise ValueError("Correctness checks did not all pass.")
    groups = sorted(summary.comparison_workers.unique())
    FIG.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 11, "axes.spines.top": False,
                         "axes.spines.right": False})
    for filename, methods, title, footnote in [
        ("parallel_one_shot_runtime.png", ["serial", "fresh_pool"],
         "One-shot runtime: process startup dominates",
         "Fresh pool includes startup, transfer, computation, collection and shutdown."),
        ("parallel_reused_pool_runtime.png", ["serial", "reused_pool", "reused_pool_batched"],
         "Task runtime with an already prepared process pool",
         "Reused pools include transfer, computation and collection; exclude setup and shutdown.")]:
        fig, axes = plt.subplots(1, len(groups), figsize=(12, 5.4), sharey=True, squeeze=False)
        for ax, workers in zip(axes.flat, groups):
            frame = summary[summary.comparison_workers == workers].set_index("method").loc[methods]
            values = frame.median_seconds.to_numpy() * 1000
            errors = np.array([values-frame.min_seconds.to_numpy()*1000,
                               frame.max_seconds.to_numpy()*1000-values])
            bars = ax.bar([LABELS[m] for m in methods], values, color=COLORS[:len(methods)],
                          yerr=errors, capsize=5, width=0.6)
            ax.bar_label(bars, labels=[f"{v:.2f}" for v in values], padding=7)
            ax.set_title(f"{workers}-worker comparison")
            ax.set_ylim(0, frame.max_seconds.max()*1000*1.25)
            ax.grid(axis="y", alpha=0.18)
            ax.set_axisbelow(True)
        axes[0, 0].set_ylabel("Runtime (milliseconds; lower is better)")
        fig.suptitle(title, fontsize=16)
        fig.text(0.5, 0.045, footnote + "\nBars: medians of 10 runs. Whiskers: min-max range, not confidence intervals. CSV I/O and validation excluded.",
                 ha="center", fontsize=9)
        fig.tight_layout(rect=(0, 0.13, 1, 0.93))
        fig.savefig(FIG / filename, dpi=200)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5.5))
    x = np.arange(len(groups))
    for offset, method, color in [(-0.18, "reused_pool", COLORS[1]),
                                   (0.18, "reused_pool_batched", COLORS[2])]:
        values = [summary[(summary.comparison_workers == w) & (summary.method == method)].speedup.iloc[0] for w in groups]
        bars = ax.bar(x+offset, values, width=0.34, label=LABELS[method], color=color)
        ax.bar_label(bars, fmt="%.2fx", padding=4)
    ax.axhline(1, color="#475569", linestyle="--", label="Serial baseline (1x)")
    ax.set_xticks(x, [f"{w} workers" for w in groups])
    ax.set_ylabel("Speedup (serial median / parallel median)")
    ax.set_ylim(0, max(2.5, summary.speedup.max()*1.3))
    ax.set_title("Reused-pool task speedup", fontsize=16)
    ax.legend(loc="upper left")
    ax.grid(axis="y", alpha=0.18)
    ax.set_axisbelow(True)
    fig.text(0.5, 0.035, "Excludes pool setup and shutdown. Each worker group uses its own measured serial baseline.", ha="center", fontsize=9)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(FIG / "parallel_reused_pool_speedup.png", dpi=200)
    plt.close(fig)

    lines = ["# Parallel Computing Performance Experiment", "",
        "## Workload and method", "",
        f"The experiment computes 60-observation rolling Pearson correlations for all 28 pairs of eight currencies, using {int(runs.observations.iloc[0])} daily log-return observations from the 2010-2025 dataset. Each configuration is measured 10 times, with method order rotated between repetitions. The same calculation function is used throughout. All results match the serial reference within rtol=1e-10 and atol=1e-12.", "",
        "Fresh-pool timing includes process startup, data transfer, computation, result collection and shutdown. Reused-pool timing includes data transfer, computation and collection, but excludes startup, warm-up and shutdown. CSV I/O and correctness validation are excluded from every timed run. Batching uses 14 pairs per chunk with two workers and seven with four workers.", "",
        "## Results", "",
        "| Comparison workers | Method | Median (ms) | Speedup |",
        "|---|---|---:|---:|"]
    for row in summary.itertuples():
        lines.append(f"| {row.comparison_workers} | {LABELS[row.method]} | {row.median_seconds*1000:.3f} | {row.speedup:.3f} |")
    best = summary.loc[summary.speedup.idxmax()]

    def median_ms(method, workers):
        rows = summary[(summary.method == method) & (summary.comparison_workers == workers)]
        return float(rows.median_seconds.iloc[0]) * 1000

    group_sentences = []
    for workers in groups:
        group_sentences.append(
            f"With {workers} workers, the reused pool takes "
            f"{median_ms('reused_pool', workers):.2f} ms and the batched pool "
            f"{median_ms('reused_pool_batched', workers):.2f} ms, against a "
            f"serial baseline of {median_ms('serial', workers):.2f} ms."
        )

    if best.speedup > 1:
        best_sentence = (
            f"The fastest task-stage configuration is {LABELS[best.method]} with "
            f"{best.workers} workers: {best.median_seconds*1000:.3f} ms and "
            f"{best.speedup:.2f}x speedup, corresponding to a "
            f"{(1-1/best.speedup)*100:.1f}% reduction in task-stage elapsed time "
            f"relative to its serial baseline."
        )
    else:
        best_sentence = (
            "No parallel configuration beats the serial baseline in this run; "
            "the best median is "
            f"{best.median_seconds*1000:.3f} ms ({best.speedup:.2f}x)."
        )

    lines += ["", best_sentence, ""]
    lines += group_sentences + ["",
        "Fresh-pool execution remains much slower than serial execution. The results are consistent with process setup and per-task message overhead dominating this small workload; batching reduces the number of messages. The experiment does not separately isolate startup, serialization, scheduling and computation costs.", "",
        "## Setup costs and interpretation", ""]
    for row in setup.itertuples():
        lines.append(f"- {row.workers} workers: startup plus one full warm-up workload = {row.startup_and_warmup_seconds:.3f} s; shutdown = {row.shutdown_seconds:.3f} s. These are single measurements, not repeated medians.")
    lines += ["", "Serial execution is preferable for a single invocation of this small analysis. A prepared pool only improves the task stage when per-task overhead is amortised, as the batched configuration does here. The reported warm-pool speedup must not be described as an end-to-end application speedup; the total benefit across repeated workloads depends on how setup costs are amortized.", "",
        "## Limitations", "",
        "These measurements describe one machine, dataset and execution session. Ten repetitions and min-max whiskers describe observed variability, not confidence intervals or statistical significance. Millisecond timings are sensitive to system load. An idle persistent pool remains allocated during serial and fresh-pool measurements. No conclusion about large-scale or distributed scalability follows from this experiment.", "",
        "## Figures", "",
        "- ../data/analysis_output/figures/parallel_one_shot_runtime.png",
        "- ../data/analysis_output/figures/parallel_reused_pool_runtime.png",
        "- ../data/analysis_output/figures/parallel_reused_pool_speedup.png", "",
        "Environment and exact timing definitions: ../data/analysis_output/pool_reuse_environment.csv", ""]
    (ROOT / "note").mkdir(exist_ok=True)
    (ROOT / "note" / "parallel_performance_analysis.md").write_text("\n".join(lines), encoding="utf-8")
    print("Saved three performance figures and note/parallel_performance_analysis.md")


if __name__ == "__main__":
    main()
