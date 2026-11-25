# Methods and Conventions

This note records the formulas, conventions and validation rules used in the pipeline. It is the source for the methods section of the final report.

## 1. Data flow

```
ECB eurofxref-hist.csv
  -> clean_exchange_rates.py
  -> cleaning_output/fx_eur_8currencies_2010_2025.csv
  -> calculate_returns.py
  -> analysis_output/fx_daily_log_returns_2010_2025.csv
  -> descriptive, correlation, clustering, volatility, sensitivity and parallel analyses
```

## 2. Transformations

### Daily log change

For consecutive available observations \(P_{t-1}\) and \(P_t\), the daily log change is

```
100 * ln(P_t / P_{t-1})
```

It is expressed in percent. Because the quote is foreign currency units per EUR, a positive value means EUR appreciation against that currency. This is an exchange-rate log change, not a total investment return.

### Monthly change

```
100 * (P_month_end / P_previous_month_end - 1)
```

This is a simple percentage change. Daily log percentages should not be summed and labelled as a simple monthly percentage; the monthly script compounds the daily changes for its internal identity check instead.

### Standardisation

The trend chart uses base 100: the first observation of each currency is set to 100. This is a common-base index, not a z-score. The report should state that convention explicitly.

## 3. Volatility

- Daily volatility is the sample standard deviation of daily log changes, `ddof=1`, multiplied by 100.
- It is **not annualised**. No square-root-of-time scaling is applied.
- The 60-observation rolling volatility uses `rolling(60, min_periods=60).std(ddof=1) * 100`; the first 59 rows are excluded.
- Annual volatility groups daily log changes by calendar year and applies the same sample standard deviation.

## 4. Correlation

- Pearson correlation of daily log changes, computed pairwise on the 4,096 complete observations.
- All 28 pairs share the same EUR base; this common base can induce co-movement even when the bilateral economic drivers differ.
- Correlation does not establish causation. Full-period correlations can hide sign and strength changes; the 60-observation rolling correlations document that variation.
- With 28 pairs, individual coefficients are not adjusted for multiple comparisons; the bootstrap intervals and rank stability are descriptive aids, not formal family-wise tests.

## 5. Clustering

- Distance: `sqrt(2 * (1 - r))`, clipped to `[0, 4]`, applied to the Pearson correlation matrix.
- Linkage: average linkage.
- Inputs: daily log changes for the eight currencies over 2010–2025.
- The tree is cut into 2, 3 and 4 clusters to illustrate sensitivity. No optimal cluster count is claimed.
- The dendrogram and partitions are exploratory; they depend on the period, the common base, the distance definition and the linkage rule.

## 6. Robustness analyses

### Rolling-window sensitivity

`analyze_window_sensitivity.py` recomputes the rolling correlation for USD-HKD, CNY-USD, AUD-CAD and AUD-JPY with 30, 60 and 120 observations. It reports the mean, standard deviation, minimum and maximum of each series. The aim is to show whether the qualitative ordering of pair variability depends on the 60-observation choice, not to select an optimal window.

### Outlier sensitivity

`analyze_outlier_sensitivity.py` recomputes all correlations and daily volatilities after dropping:

- 2015-01-15 (SNB discontinued the EUR/CHF floor);
- 2016-06-24 (Brexit referendum result);
- both dates.

The main analysis retains these observations. The sensitivity check separates a general pattern from two influential sessions. Spearman rank correlation between the baseline and outlier-excluded correlation vectors summarises rank stability.

### Moving-block bootstrap

`bootstrap_correlations.py` uses a moving-block bootstrap:

- block length 60 (same as the rolling window);
- 1,000 replicates, fixed seed 20261122;
- blocks are drawn with replacement from all valid start positions, concatenated and truncated to 4,096 observations;
- the 2.5th and 97.5th percentiles of each pair correlation form an approximate 95% interval.

The block bootstrap keeps short-range dependence, but it is not an exact treatment of overlapping-window dependence. The intervals are approximate and descriptive.

## 7. Parallel benchmark conventions

- **Workload:** 28 pairs of eight currencies, 60-observation rolling Pearson correlations, 4,096 daily log changes.
- **Serial baseline:** the same calculation function, run in one process.
- **Fresh pool:** process startup, data transfer, computation, result collection and shutdown are included.
- **Reused pool:** transfer, computation and collection are included; startup, warm-up and shutdown are excluded.
- **Batched pool:** the same reused pool with a chunksize larger than one.
- **Correctness:** every parallel result is compared with the serial reference using `rtol=1e-10`, `atol=1e-12`; validation runs outside the timed region.
- **Speedup:** `serial median / parallel median`.
- **Efficiency:** `speedup / workers`.
- Ten repetitions with the method order rotated between repetitions; medians and min–max ranges are reported. Min–max is not a confidence interval.
- The process pool uses the `spawn` start method on Windows. Every worker is started before timing; the original benchmark uses a barrier, and the scaling script uses a barrier plus one warm-up task per worker. The recorded setup time grows with worker count because each spawned worker imports the scientific stack; it is excluded from the task-stage timing.

## 8. Scaling experiment

- `scaling_parallel_correlations.py` uses synthetic factor-model series so workload size can be varied without changing the real-data findings.
- Three common factors plus idiosyncratic noise, both t-distributed with 5 degrees of freedom; fixed seed 20261122.
- Series counts: 8, 16, 32 and 64 (28, 120, 496 and 2,016 pairs) at 4,096 observations.
- Observation counts: 1,024, 2,048 and 4,096 for eight series.
- Workers: 2, 4 and 8; methods: serial, process pool with worker-local data, thread pool with shared data.
- Worker-local data is broadcast once per process; tasks are pair indices, not copies of the series. This isolates computation and scheduling from repeated pickling.
- The per-task-array design is measured separately at 28 pairs in `benchmark_pool_reuse.py`; it is not the design used for the scaling curve.

An Amdahl check on the 2,016-pair medians gives an implied serial fraction of about 4.1% at four workers and 5.2% at eight workers (`s = (1/S - 1/p) / (1 - 1/p)`). A fixed serial section would give the same value; the increase suggests that additional overhead — process start-up amortisation, inter-process transfer and load balance — grows with the worker count. The calculation is descriptive and should not be presented as a measured serial fraction.

## 9. Chunksize sensitivity

`benchmark_chunksize.py` holds the real 28-pair workload fixed and sweeps the chunksize over 1, 2, 4, 7, 14 and 28 for 2, 4 and 8 workers. Ten repetitions per configuration. Every worker is started before timing via a barrier and a full warm-up.

## 10. Validation and rounding

- Dates must be unique and sorted; numeric inputs must be finite; exchange-rate levels must be positive.
- Rolling-window results are checked against a direct sample standard deviation on the first window.
- Monthly compounding is checked against the ratio of the final and initial month-end quotes.
- The parallel and serial paths are checked for exact equality on the rolling-correlation grid.
- CSV values are rounded to six decimals for the rolling grids and summaries, and to eight or nine decimals where the analysis needs more precision. The report should quote at most four significant decimals and state the convention.

## 11. Known limitations

- Eight currencies and one 16-year sample; the results describe this sample, not future probabilities.
- The common EUR base induces correlation; the analysis does not decompose it.
- Daily changes are not uniformly spaced and rolling windows overlap.
- Clustering is exploratory; no optimal number of clusters is claimed.
- The parallel measurements describe one machine, one Python build and one session; medians are not confidence intervals.
- Synthetic scaling data are a benchmark device, not an empirical result.
- No causal claim is made about policy events; the interpretations are labelled conjectures in `interpretations.md`.
