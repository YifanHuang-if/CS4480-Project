# Archived artefacts

These files are kept for provenance. They are **not** used by the current pipeline and should not be cited as current results.

| File | Why archived |
|---|---|
| `legacy/analyze_all_rolling_correlations.py` | Duplicate copy found inside `analysis_output/`. Running it there would have written to `analysis_output/analysis_output/`. The maintained version is `Project/data/analyze_all_rolling_correlations.py`. |
| `legacy/rolling_benchmark_runs.csv` | Earlier 5-repetition benchmark of the naive one-shot process pool. Superseded by `pool_reuse_benchmark_runs.csv` (10 repetitions, fresh/reused/batched) and by `scaling_benchmark_runs.csv`. Keeping it explains the earlier numbers if they appear in old notes. |
| `legacy/rolling_benchmark_summary.csv` | Summary of the same superseded benchmark. Its parallel medians (~1.0 s) are not comparable with the current `pool_reuse` fresh-pool medians because the measurement scope and interpreter build differ. |

The current results are in `Project/data/analysis_output/` and are described in `note/` and `docs/`.
