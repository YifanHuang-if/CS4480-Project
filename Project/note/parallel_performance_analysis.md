# Parallel Computing Performance Experiment

## Workload and method

The experiment computes 60-observation rolling Pearson correlations for all 28 pairs of eight currencies, using 4096 daily log-return observations from the 2010-2025 dataset. Each configuration is measured 10 times, with method order rotated between repetitions. The same calculation function is used throughout. All results match the serial reference within rtol=1e-10 and atol=1e-12.

Fresh-pool timing includes process startup, data transfer, computation, result collection and shutdown. Reused-pool timing includes data transfer, computation and collection, but excludes startup, warm-up and shutdown. CSV I/O and correctness validation are excluded from every timed run. Batching uses 14 pairs per chunk with two workers and seven with four workers.

## Results

| Comparison workers | Method | Median (ms) | Speedup |
|---|---|---:|---:|
| 2 | Fresh pool | 980.875 | 0.018 |
| 2 | Reused pool | 20.016 | 0.895 |
| 2 | Reused + batched | 18.667 | 0.960 |
| 2 | Serial | 17.915 | 1.000 |
| 4 | Fresh pool | 1066.978 | 0.017 |
| 4 | Reused pool | 19.272 | 0.963 |
| 4 | Reused + batched | 11.313 | 1.640 |
| 4 | Serial | 18.551 | 1.000 |

The fastest task-stage configuration is Reused + batched with 4 workers: 11.313 ms and 1.64x speedup, corresponding to a 39.0% reduction in task-stage elapsed time relative to its serial baseline.

With 2 workers, the reused pool takes 20.02 ms and the batched pool 18.67 ms, against a serial baseline of 17.92 ms.
With 4 workers, the reused pool takes 19.27 ms and the batched pool 11.31 ms, against a serial baseline of 18.55 ms.

Fresh-pool execution remains much slower than serial execution. The results are consistent with process setup and per-task message overhead dominating this small workload; batching reduces the number of messages. The experiment does not separately isolate startup, serialization, scheduling and computation costs.

## Setup costs and interpretation

- 2 workers: startup plus one full warm-up workload = 0.918 s; shutdown = 0.083 s. These are single measurements, not repeated medians.
- 4 workers: startup plus one full warm-up workload = 1.005 s; shutdown = 0.106 s. These are single measurements, not repeated medians.

Serial execution is preferable for a single invocation of this small analysis. A prepared pool only improves the task stage when per-task overhead is amortised, as the batched configuration does here. The reported warm-pool speedup must not be described as an end-to-end application speedup; the total benefit across repeated workloads depends on how setup costs are amortized.

## Limitations

These measurements describe one machine, dataset and execution session. Ten repetitions and min-max whiskers describe observed variability, not confidence intervals or statistical significance. Millisecond timings are sensitive to system load. An idle persistent pool remains allocated during serial and fresh-pool measurements. No conclusion about large-scale or distributed scalability follows from this experiment.

## Figures

- ../data/analysis_output/figures/parallel_one_shot_runtime.png
- ../data/analysis_output/figures/parallel_reused_pool_runtime.png
- ../data/analysis_output/figures/parallel_reused_pool_speedup.png

Environment and exact timing definitions: ../data/analysis_output/pool_reuse_environment.csv
