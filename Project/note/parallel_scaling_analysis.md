# Parallel Scaling Analysis

## What was varied

The real-data benchmark fixes the workload at 28 pairs and 4,096 observations. This experiment varies the number of synthetic factor-model series (8, 16, 32 and 64, giving 28, 120, 496 and 2,016 pairs) and the number of observations (1,024, 2,048 and 4,096), then measures serial, process-pool and thread-pool runtimes for 2, 4 and 8 workers. Each configuration is measured five times; the median is reported.

Worker-local data is broadcast once per process, so tasks are pair indices rather than copies of the series. This isolates computation and scheduling from repeated pickling. The per-task-array design remains measured at 28 pairs in `parallel_performance_analysis.md`.

## Results

| Workload | Pairs | Serial (ms) | Process 4w (ms) | Process 8w (ms) | Speedup 8w | Efficiency 8w |
|---|---:|---:|---:|---:|---:|---:|
| 8 series, 1024 obs | 28 | 12.47 | 6.53 | 6.87 | 1.82x | 0.23 |
| 8 series, 2048 obs | 28 | 14.26 | 7.50 | 7.34 | 1.94x | 0.24 |
| 8 series, 4096 obs | 28 | 21.67 | 8.32 | 7.85 | 2.76x | 0.35 |
| 16 series, 4096 obs | 120 | 83.81 | 31.13 | 23.36 | 3.59x | 0.45 |
| 32 series, 4096 obs | 496 | 381.09 | 123.27 | 74.17 | 5.14x | 0.64 |
| 64 series, 4096 obs | 2016 | 1532.60 | 430.12 | 261.68 | 5.86x | 0.73 |

## Interpretation

As the workload grows from 28 pairs to 2,016 pairs, the serial median rises from 21.67 ms to 1532.60 ms, while the eight-worker process-pool median rises from 7.85 ms to 261.68 ms. The eight-worker speedup at 2,016 pairs is 5.86x.

The thread-pool speedup at 2,016 pairs and eight workers is 1.08x. Threads avoid serialisation but share the interpreter; processes pay serialisation and startup costs but are not limited by one Python interpreter. The comparison shows which constraint dominates at this workload size.

The small-workload result is dominated by per-message and scheduling overhead. Speedup only approaches the worker count once the per-task computation is large enough to amortise that overhead. This is consistent with Amdahl's law and with the fixed-cost measurements in `parallel_performance_analysis.md`.

## Caveats

- The series are synthetic factor-model data used only to vary workload size. They do not replace the real-data findings in the exploratory and parallel notes.
- The environment is one machine, one Python build and one execution session. The numbers are medians of five repetitions, not confidence intervals.
- Process-pool timing includes map/scheduling and result collection but excludes pool startup and shutdown; startup and shutdown are recorded in `scaling_benchmark_setup.csv`.
- The workload is CPU-bound rolling correlation; no I/O is included.

## Files

- `../data/analysis_output/scaling_benchmark_runs.csv`
- `../data/analysis_output/scaling_benchmark_summary.csv`
- `../data/analysis_output/scaling_benchmark_setup.csv`
- `../data/analysis_output/scaling_benchmark_environment.csv`
- `../data/analysis_output/figures/parallel_scaling_runtime.png`
- `../data/analysis_output/figures/parallel_scaling_speedup.png`
- `../data/analysis_output/figures/parallel_thread_vs_process.png`
