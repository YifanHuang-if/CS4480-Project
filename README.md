# CS4880 Open Project: EUR-Based Exchange-Rate Analysis with Parallel Rolling Correlations

Course: **CS4880 Open Project (40%)**, City University of Hong Kong.
Group: `<add the 3–4 member names and student IDs here>`.

This repository contains the data pipeline, exploratory analyses, robustness checks, parallel benchmarks and reproduction notes. A 10-page LaTeX report draft is in [`Project/report/`](Project/report); Group 9 details are filled in, and the AI statement and contribution hours should be verified before submission. The cover sheet and presentation are prepared separately for the Week 13 submission.

> The local folder is named `CS4480-Project`, while the 2025 course outline is CS4880. Confirm the course code on the cover sheet and in the report header.

## Research questions

1. How do daily exchange-rate changes and volatility differ across the eight currencies?
2. Which currencies move together, and how stable are those relationships over time?
3. What groups emerge from correlation-based hierarchical clustering?
4. How do data size and worker count affect rolling-correlation runtime, and why?

## Data

- **Source:** European Central Bank, *euro foreign exchange reference rates*, `eurofxref-hist.csv`.
- **Coverage used:** 2010-01-04 to 2025-12-31; 4,097 daily observations; 4,096 daily log changes.
- **Currencies:** CNY, USD, JPY, GBP, HKD, CHF, AUD, CAD; base EUR; quote = foreign currency units per 1 EUR.
- **Provenance, fields and cleaning rules:** [`docs/data_source.md`](Project/docs/data_source.md).

## Repository layout

```
Project/
├── data/
│   ├── eurofxref-hist.csv                 # raw ECB snapshot (read-only input)
│   ├── clean_exchange_rates.py            # validation, period filter, cleaning summary
│   ├── calculate_returns.py               # daily log changes
│   ├── describe_returns.py                # descriptive statistics
│   ├── plot_exchange_rates.py             # indexed trends, daily-change panels
│   ├── analyze_correlations.py            # full-period Pearson matrix, heatmap
│   ├── cluster_currencies.py              # average-linkage clustering, dendrogram
│   ├── analyze_rolling_volatility.py      # 60-observation rolling volatility
│   ├── analyze_annual_volatility.py       # annual daily volatility
│   ├── analyze_rolling_correlations.py    # four illustrative pairs
│   ├── analyze_all_rolling_correlations.py# all 28 pairs; optional --workers
│   ├── analyze_monthly_changes.py         # month-end changes, calendar heatmaps
│   ├── analyze_extreme_changes.py         # empirical tails, top-10 absolute changes
│   ├── plot_distributions.py              # boxplots, scatterplots, volatility comparison
│   ├── analyze_window_sensitivity.py      # 30/60/120-observation windows
│   ├── analyze_outlier_sensitivity.py     # drop 2015-01-15 and 2016-06-24
│   ├── bootstrap_correlations.py          # moving-block bootstrap intervals
│   ├── benchmark_rolling_correlations.py  # shared task function and initial benchmark
│   ├── benchmark_pool_reuse.py            # 28-pair serial/fresh/reused/batched benchmark
│   ├── plot_parallel_performance.py       # performance figures and parallel note
│   ├── scaling_parallel_correlations.py   # 28-2,016 pairs x 2/4/8 workers, process vs thread
│   ├── benchmark_chunksize.py             # chunksize sweep
│   ├── regenerate_figures.py              # rebuild all 22 figures from code (no benchmark rerun)
│   ├── cleaning_output/                   # cleaned data, missing report, cleaning summary
│   ├── analysis_output/                   # CSVs and figures/
│   └── archive/legacy/                    # superseded artefacts, kept for provenance
├── docs/                                  # source, methods, figure index, assessment map, Q&A
└── note/                                  # findings outline, exploratory notes, parallel notes
```

## Quick start

Tested with Python 3.11.9 on Windows. Run from `Project/`:

```powershell
python -m pip install -r requirements.txt

python data/clean_exchange_rates.py
python data/calculate_returns.py
python data/describe_returns.py
python data/plot_exchange_rates.py
python data/analyze_correlations.py
python data/cluster_currencies.py
python data/analyze_rolling_volatility.py
python data/analyze_annual_volatility.py
python data/analyze_rolling_correlations.py
python data/analyze_all_rolling_correlations.py
python data/analyze_monthly_changes.py
python data/analyze_extreme_changes.py
python data/plot_distributions.py
python data/analyze_window_sensitivity.py
python data/analyze_outlier_sensitivity.py
python data/bootstrap_correlations.py
```

Parallel and benchmark stage (run on an idle machine; timings are sensitive to load):

```powershell
python data/benchmark_pool_reuse.py
python data/plot_parallel_performance.py
python data/scaling_parallel_correlations.py
python data/benchmark_chunksize.py

# Rebuild every figure from the saved results without re-measuring timings.
python data/regenerate_figures.py

# Optional: run the all-pairs analysis through the process pool.
python data/analyze_all_rolling_correlations.py --workers 4
```

All scripts resolve paths relative to their own location, so the working directory does not change the inputs or outputs. Every script uses a non-interactive Matplotlib backend.

## Key results

| Finding | Value | Evidence |
|---|---:|---|
| Retained daily observations / changes | 4,097 / 4,096 | `cleaning_output/cleaning_summary.csv` |
| Highest / lowest daily volatility | JPY 0.642004% / CHF 0.463204% | `daily_returns_summary.csv` |
| Strongest / weakest full-period correlation | USD-HKD 0.996567 / CHF-AUD 0.106444 | `currency_pair_correlations.csv` |
| Most / least stable pair by rolling-correlation SD | USD-HKD 0.009220 / USD-JPY 0.272307 | `rolling_correlation_summary_all_pairs_60d.csv` |
| JPY-AUD rolling range | -0.600930 to 0.807684 | same file |
| CHF 60-observation volatility peak | 2.107576% (2015-01-15 to 2015-04-10) | `rolling_volatility_summary_60d.csv` |
| Bootstrap interval for USD-HKD | 0.9948 to 0.9977 | `correlation_bootstrap_ci.csv` |
| Outlier-excluded correlation rank stability | Spearman 0.996 | `outlier_sensitivity_correlations.csv` |
| Best 28-pair task-stage speedup | 1.64x at 4 workers with batching | `pool_reuse_benchmark_summary.csv` |
| Scaling speedup at 2,016 pairs / 8 workers | 5.86x; 73% efficiency | `scaling_benchmark_summary.csv` |
| Thread-pool speedup at 2,016 pairs / 8 threads | 1.08x | `scaling_benchmark_summary.csv` |
| Best chunksize at 4 workers | 4 (9.557 ms; 1.835x) | `chunksize_sweep.csv` |

Interpretations: [`docs/interpretations.md`](Project/docs/interpretations.md). Methods and formulas: [`docs/methods.md`](Project/docs/methods.md). Figure index: [`docs/figure_index.md`](Project/docs/figure_index.md).

## Report draft

- [Report PDF](Project/report/fx_open_project_report_final3.pdf) (10 pages; use this build if the canonical file is locked by a viewer).
- [LaTeX source](Project/report/fx_open_project_report.tex).
- [Build notes](Project/report/README.md).

The draft follows the IEEEtran structure of the supplied template, with the Kaggle-specific sections rewritten for the Open Project. It includes nine figures and five tables. Group 9 details are filled in; check the AI statement and contribution hours before submission.

## Reproducibility

- Environment: Python 3.11.9, NumPy 2.4.6, pandas 3.1.1, Matplotlib 3.11.2, SciPy 1.17.1, Windows, 16 logical CPUs.
- The parallel benchmarks use the `spawn` start method. A barrier and warm-up start every worker before timing; otherwise lazy process start-up would leak into the measurements.
- Every parallel result is checked against the serial reference with `rtol=1e-10`, `atol=1e-12`; validation is outside the timed region.
- The bootstrap uses seed 20261122; the scaling experiment uses fixed synthetic seeds.
- Benchmark medians depend on machine load and interpreter build. The saved environment CSVs record the exact run.
- The ECB file is updated daily; re-downloading later changes the last observation. Record the snapshot date when re-running.

## Documentation

| Document | Purpose |
|---|---|
| [`docs/data_source.md`](Project/docs/data_source.md) | ECB provenance, fields, period, cleaning rules, citation |
| [`docs/methods.md`](Project/docs/methods.md) | formulas, validation, benchmark and bootstrap conventions |
| [`docs/figure_index.md`](Project/docs/figure_index.md) | all 22 figures, scripts, suggested report sections |
| [`docs/figure_generation.md`](Project/docs/figure_generation.md) | figure-to-code map and one-command rebuild |
| [`docs/project_workflow.md`](Project/docs/project_workflow.md) | 五步流程：每步实现了什么、产出是什么（中文） |
| [`docs/assessment_mapping.md`](Project/docs/assessment_mapping.md) | rubric-to-evidence map and remaining deliverables |
| [`docs/interpretations.md`](Project/docs/interpretations.md) | three labelled conjectures with official sources |
| [`docs/qa_bank.md`](Project/docs/qa_bank.md) | 21 Q&A entries for the presentation |
| [`docs/run_log.md`](Project/docs/run_log.md) | date, environment, commands, checks and caveats for the frozen run |
| [`note/research_findings_and_report_outline.md`](Project/note/research_findings_and_report_outline.md) | findings table and report outline |
| [`note/exploratory_analysis_notes.md`](Project/note/exploratory_analysis_notes.md) | exploratory results and methods |
| [`note/parallel_performance_analysis.md`](Project/note/parallel_performance_analysis.md) | 28-pair benchmark |
| [`note/parallel_scaling_analysis.md`](Project/note/parallel_scaling_analysis.md) | scaling experiment |

## Limitations

Eight currencies, one 16-year sample, daily reference rates rather than transaction prices, a common EUR base, overlapping rolling windows, one machine for the benchmarks, and no causal identification. The report states each limitation next to the claim it constrains.

## Academic integrity and contributions

- Cite the ECB data and the software libraries used.
- Record the actual contribution of each group member on the cover sheet and in the report.
- Follow CityU academic-honesty rules and the VeriGuide check.
- Do not present a conjecture as a causal finding; `docs/interpretations.md` provides the phrasing.

## What remains before submission

- [ ] Project cover sheet (Canvas template; 3–4 member names and contributions).
- [ ] Verify the report's AI statement and contribution hours; proofread.
- [ ] Presentation slides and rehearsal.
- [ ] Supporting-material package: this repository, `requirements.txt`, and a short run log.
