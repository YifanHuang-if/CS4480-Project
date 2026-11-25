# Research Findings and Report Outline

Working title: Exploring EUR-Based Exchange Rates: Correlation, Volatility, Clustering and Parallel Computing

This is an evidence-based writing plan, not the final report. Values refer to the current saved CSV outputs.

## 1. Research questions

1. How do daily exchange-rate changes and volatility differ across the eight currencies?
2. Which currencies move together, and how stable are these relationships over time?
3. What groups emerge from correlation-based hierarchical clustering?
4. How do process-pool reuse and task batching affect rolling-correlation runtime?

## 2. Dataset facts

- Eight quote currencies: CNY, USD, JPY, GBP, HKD, CHF, AUD and CAD; EUR is the common base.
- Requested period: 2010-01-01 to 2025-12-31. Actual retained observations: 2010-01-04 to 2025-12-31.
- The cleaning summary records 7,141 original rows, 3,044 outside the requested period, 4,097 retained rows, zero exact duplicates removed and zero retained rows with missing rates.
- Differencing yields 4,096 log-return observations per currency. A 60-observation window yields 4,037 valid windows per pair.
- Quotes are foreign currency units per EUR. A positive log change means EUR appreciation against that quote currency. These are exchange-rate log changes, not total investment returns.
- Evidence: `data/cleaning_output/cleaning_summary.csv` and `data/analysis_output/daily_returns_summary.csv`.

## 3. Findings and evidence

| Finding | Numerical evidence | Source under data/analysis_output | Interpretation boundary |
|---|---|---|---|
| JPY has the highest full-period daily volatility; CHF has the lowest | JPY: 0.642004%; CHF: 0.463204% | daily_returns_summary.csv | Standard deviation of daily log changes; not annualized volatility |
| Low full-period volatility does not rule out extreme local volatility | CHF has the highest maximum 60-observation daily volatility among the eight currencies: 2.107576%, window 2015-01-15 to 2015-04-10 | rolling_volatility_summary_60d.csv | A window statistic, not a single-day return or a causal explanation |
| USD and HKD move almost identically relative to EUR | Full-period correlation: 0.996567; rolling correlation: 0.916335 to 0.999986 | currency_pair_correlations.csv; rolling_correlation_summary_all_pairs_60d.csv | Common EUR base affects the interpretation |
| CHF and AUD have the weakest full-period absolute correlation among the 28 pairs | 0.106444; all 28 full-period correlations are positive | currency_pair_correlations.csv | Weak linear correlation does not establish independence |
| Full-period correlations hide changes in sign and strength | JPY-AUD: full-period 0.146437; rolling minimum -0.600930 and maximum 0.807684 | rolling_correlation_summary_all_pairs_60d.csv | Rolling dates mark window endpoints; overlapping windows are dependent |
| USD-HKD is the most stable pair by rolling-correlation standard deviation; USD-JPY is the least stable by that metric | Standard deviations: 0.009220 and 0.272307, respectively | rolling_correlation_summary_all_pairs_60d.csv | Stability is defined by this metric, not by range alone |
| Clustering summarizes the correlation structure | USD-HKD merges first at distance 0.082864, CNY joins next; AUD-CAD also forms a pair; CHF joins last | currency_cluster_linkage.csv; figures/currency_clustering_dendrogram.png | Average linkage with distance sqrt(2*(1-r)); exploratory, not independent confirmation of correlation |
| One-shot parallel is dominated by process setup | 28 pairs: serial 17.915/18.551 ms; fresh pool 980.875/1,066.978 ms; reused pool 20.016/19.272 ms; reused+batched 18.667/11.313 ms; best 1.640x at 4 workers | pool_reuse_benchmark_summary.csv | Fresh-pool timing includes startup, transfer and shutdown; the warm-pool speedup excludes setup; one-shot execution remains slower than serial |
| Parallel benefit grows with workload size | 28 pairs: 2.76x at 8 workers; 2,016 pairs: serial 1,532.60 ms, 8 workers 261.68 ms, 5.86x, efficiency 0.73 | scaling_benchmark_summary.csv | Synthetic factor-model data; medians of five repetitions; one machine |
| Threads do not scale on this workload | 2,016 pairs / 8 threads: 1.08x; process pool: 5.86x | scaling_benchmark_summary.csv | GIL and Python-level overhead; process pools pay serialisation and startup |
| Chunksize has an interior optimum | 4 workers: chunksize 4 → 9.557 ms (1.835x); chunksize 28 (one chunk) → 27.838 ms (0.630x); 2 workers best 7 → 13.617 ms (1.288x) | chunksize_sweep.csv | 28-pair workload; the optimum depends on pair count and worker count |
| Correlations are rank-stable after extreme sessions | Dropping 2015-01-15 and 2016-06-24: Spearman 0.996; largest Δr +0.054067 (JPY-CHF); CHF volatility −0.068826 pp | outlier_sensitivity_correlations.csv; outlier_sensitivity_volatility.csv | Sensitivity check, not causal attribution |
| Bootstrap intervals separate strong from weak pairs | USD-HKD [0.994850, 0.997732]; JPY-GBP [0.0552, 0.2965] | correlation_bootstrap_ci.csv | Moving-block bootstrap, block 60, 1,000 replicates; approximate interval |
| Window choice changes variability, not pair ordering | Rolling-correlation SD at 30/60/120: USD-HKD 0.0124/0.0092/0.0068; AUD-JPY 0.3009/0.2597/0.2228 | window_sensitivity_summary.csv | 60 observations is a reporting choice, not an optimum |

## 4. Suggested report structure

The supplied slides provide a project example and assessment criteria, but do not specify a mandatory report template or page limit. The structure below is a proposed organization.

| Section | Main content | Suggested evidence |
|---|---|---|
| 1. Introduction and objectives | Motivate studying co-movement, changing volatility and computational overhead; state the four research questions | Brief project scope |
| 2. Data source and preprocessing | Source provenance, date and currency selection, missing-value checks, quote direction and log-change calculation | Cleaning summary; preprocessing code |
| 3. Exploratory analysis | Indexed exchange-rate trends, daily changes, descriptive statistics and full-period correlation | Indexed trends, daily-change plots, correlation heatmap |
| 4. Time-varying relationships and clustering | Annual and rolling volatility; all-pair rolling correlations; hierarchical clustering | Volatility figures, rolling summary and dendrogram |
| 5. Parallel implementation and performance | Independent pair tasks; serial baseline; 2/4/8 workers; fresh vs reused pool; batching; chunksize; process vs thread; scaling to 2,016 pairs; correctness checks; timing definitions | Three benchmark figures, three scaling figures, chunksize figure and benchmark tables |
| 6. Discussion and limitations | Answer research questions; distinguish observed patterns from explanations; common-base effects, window choice, outliers, small workload and single-machine limits | Findings table above |
| 7. Conclusion and future work | Summarize supported findings; propose window sensitivity, outlier sensitivity and meaningful workload scaling as future work | No unperformed experiment presented as completed |
| References and reproducibility | Verified data citation, method sources, software versions, execution instructions and relevant acknowledgements | Environment CSV and source files |

## 5. Assessment alignment

Transcribed from `sources/d4b30603b8ba1cec4b015d642585c9b2.png`:

| Criterion | Points | Planned evidence |
|---|---:|---|
| Real World Impact / Creativity | 5 | Explain what changes in co-movement and volatility reveal; avoid unsupported investment claims |
| Solid Works and Output Amount | 20 | Reproducible cleaning, analyses, figures and benchmark outputs |
| Technical Depth and Correctness | 20 | Formulas, quote direction, clustering method, rolling-window definition, validation and limitations |
| Parallel Computing Elements | 20 | Explain implementation choices and both one-shot and warm-pool results |
| Use of Written English | 5 | Consistent terms, clear figure captions and evidence-based claims |
| Technical Presentation Amount | 20 | A later presentation covering methods, findings and performance |
| Technical Presentation Skills | 5 | A later rehearsal and clear allocation of speaking roles |
| Question and Answer (Q&A) | 5 | A later question bank addressing design choices and limitations |

This mapping identifies relevant evidence; it does not predict a grade. The provided slides do not state a minimum speedup requirement.

## 6. Remaining work before a final report

- Write the report, cover sheet and presentation; record the actual contributions of the 3–4 group members. These are the deliverables the rubric actually scores.
- Check Canvas for the cover-sheet template, any page limit, the submission format and the presentation length; the lecture slides do not state them.
- Use `docs/figure_index.md` to map each of the 22 figures to a report section and `docs/assessment_mapping.md` to check rubric coverage.
- Data source, fields and cleaning rules are now documented in `docs/data_source.md`; cite the ECB and record the snapshot date.
- Formulas, timing scopes and validation conventions are now documented in `docs/methods.md`; reuse them in the report.
- Execution order, dependencies and environment are documented in `README.md` and `requirements.txt`; re-run the benchmark stage on an idle machine before freezing the final numbers.
- Policy-event interpretations are drafted in `docs/interpretations.md` with official sources; keep them labelled as conjectures and do not claim causality.
- Future work should now focus on what was not done: higher-frequency data, more currencies, formal common-factor decomposition, event studies, and a Spark/Hadoop comparison at larger scale.
- Review the text, record assistance accurately, run the VeriGuide check, and submit before the Week 13 deadline.

## 7. Suggested central argument

The eight EUR-based exchange-rate series exhibit heterogeneous volatility and correlation patterns. Strong full-period co-movement can remain stable, as for USD-HKD, while weaker aggregate correlations can conceal substantial time variation, as for JPY-AUD. Clustering summarizes these relationships but does not establish their causes. For the computational component, process setup dominates one-shot execution of this small workload: a fresh pool is roughly 55 times slower than serial at 28 pairs. Reusing a pool and batching tasks recovers a 1.64x task-stage speedup at 28 pairs, and the benefit grows with workload size to 5.86x at 2,016 pairs and 8 workers. Threads do not scale on this workload (1.08x), so the process pool is the appropriate choice at this scale; a distributed framework would only become attractive at a much larger scale.


## 8. Extended Analyses (Completed)

| Analysis | Script under data/ | Evidence under data/analysis_output/ | Report use |
|---|---|---|---|
| Monthly changes and calendar heatmaps | analyze_monthly_changes.py | monthly_exchange_rate_changes.csv; monthly_change_summary.csv; figures/monthly_exchange_rate_heatmaps.png | Exploratory analysis: direction and timing across months, without claiming seasonality |
| Empirical tails and extreme dates | analyze_extreme_changes.py | extreme_daily_change_summary.csv; top10_absolute_daily_changes.csv; figures/daily_change_distributions.png | Discussion: typical volatility, frequency of large changes and severity of extremes |
| Boxplots, scatterplots and volatility comparison | plot_distributions.py | figures/daily_change_boxplots.png; figures/correlation_scatter_examples.png; figures/volatility_comparison.png | Exploratory analysis: distribution shape, strong/weak pair scatter, full-period vs rolling volatility |
| Rolling-window sensitivity | analyze_window_sensitivity.py | window_sensitivity_summary.csv; figures/window_sensitivity.png | Discussion: justify the 60-observation choice with 30/60/120 comparisons |
| Outlier sensitivity | analyze_outlier_sensitivity.py | outlier_sensitivity_correlations.csv; outlier_sensitivity_volatility.csv; figures/outlier_sensitivity.png | Discussion: show that the correlation ranking is not driven by two extreme sessions |
| Moving-block bootstrap | bootstrap_correlations.py | correlation_bootstrap_ci.csv; figures/correlation_bootstrap_ci.png | Exploratory analysis: attach approximate uncertainty to the 28 correlations |
| Scaling across data sizes and workers | scaling_parallel_correlations.py | scaling_benchmark_runs.csv; scaling_benchmark_summary.csv; scaling_benchmark_setup.csv; figures/parallel_scaling_runtime.png; figures/parallel_scaling_speedup.png; figures/parallel_thread_vs_process.png | Parallel section: 28–2,016 pairs, 2/4/8 workers, process vs thread |
| Chunksize sweep | benchmark_chunksize.py | chunksize_sweep.csv; figures/parallel_chunksize_sweep.png | Parallel section: why batching helps and why one chunk per workload is too coarse |

Additional evidence:

- Monthly changes use simple month-end percentages; January 2010 is unavailable because the preceding month is outside the cleaned sample. Each currency has 191 valid changes.
- CHF's January 2015 monthly change is -12.940785%. JPY has the highest monthly standard deviation (2.894551%).
- CHF's worst daily log change is -15.553938% on 2015-01-15, despite having the lowest full-period daily standard deviation. Its absolute-log-change >= 1% frequency is 2.465820%, versus JPY's 10.156250%.
- Window sensitivity: rolling-correlation standard deviations for USD-HKD are 0.012422/0.009220/0.006790 at 30/60/120 observations; for AUD-JPY they are 0.300936/0.259658/0.222780. The ordering of pair variability is stable, while shorter windows are noisier.
- Outlier sensitivity: dropping 2015-01-15 and 2016-06-24 changes the largest pair correlation by +0.054067 (JPY-CHF); the Spearman rank correlation between baseline and outlier-excluded vectors is 0.995621. CHF's daily volatility falls by 0.068826 percentage points.
- Bootstrap: 1,000 moving-block replicates, block length 60. USD-HKD interval [0.994850, 0.997732]; JPY-GBP [0.0552, 0.2965]; the weakest pairs have the widest intervals.
- Scaling: at 2,016 pairs and 4,096 observations, serial 1,532.60 ms; 8-worker process pool 261.68 ms (5.86x, 73.2% efficiency); 8-thread pool 1.08x. At 28 pairs, process-pool speedup is 2.76x at 8 workers.
- Chunksize: at 4 workers the best chunksize is 4 (9.557 ms, 1.835x); one chunk per workload is slower than serial (27.838 ms, 0.630x). The optimum depends on pair count and worker count.

Documentation for these analyses is in `docs/methods.md`, `docs/figure_index.md` and `note/parallel_scaling_analysis.md`. The archived 5-repetition benchmark is not a current result; see `data/archive/README.md`.

## 9. Documentation Map

| Document | Contents |
|---|---|
| `docs/data_source.md` | ECB provenance, fields, period, cleaning rules, citation |
| `docs/methods.md` | Formulas, validation, benchmark scope, bootstrap and sensitivity definitions |
| `docs/figure_index.md` | All 22 figures, scripts, suggested report sections and messages |
| `docs/figure_generation.md` | Figure-to-code map and one-command rebuild |
| `docs/project_workflow.md` | Five-step workflow: what each step implements and produces (Chinese) |
| `docs/assessment_mapping.md` | Rubric-to-evidence map and remaining deliverables |
| `docs/interpretations.md` | Three labelled conjectures with official sources |
| `docs/qa_bank.md` | 21 Q&A entries for the presentation |
| `docs/run_log.md` | Date, environment, commands, checks and caveats for the frozen run |
| `README.md` | Quick start, run order, key results, environment and limitations |
