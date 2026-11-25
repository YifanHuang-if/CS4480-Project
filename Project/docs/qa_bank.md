# Q&A Bank

Short answers for the Week 12–13 presentation. Each answer points to the evidence file or figure that supports it. Keep the numbers approximate when speaking; quote exact values only when the slide shows them.

## Data and preprocessing

**1. Why log changes rather than simple percentage changes?**
Log changes are additive over time, symmetric for equal up/down moves, and standard for volatility and correlation. The project uses `100 * ln(P_t / P_{t-1})`; monthly changes are simple percentages and are labelled separately (`docs/methods.md`).

**2. Why 2010–2025 and these eight currencies?**
The period gives 16 years and 4,096 daily changes. The eight currencies mix pegged/managed and floating regimes and have complete coverage in the ECB file. This is a purposive selection, not a random sample (`docs/data_source.md`).

**3. How did you handle missing values and duplicates?**
The raw file uses `N/A`; after filtering, the eight used columns have no missing values. Exact duplicates removed: 0; conflicting dates are rejected. The missing-value report and cleaning summary are saved (`cleaning_output/`).

**4. Is the ECB data a transaction price?**
No. These are daily reference rates, not traded prices. Successive observations can span weekends and holidays, so daily changes are not uniformly spaced 24-hour returns (`docs/data_source.md`).

## Analysis

**5. Why is USD–HKD almost perfectly correlated?**
Hong Kong operates a linked exchange rate system against the USD, so both quotes move together relative to EUR. The full-period correlation is 0.996567 and the rolling minimum is 0.916335 (`currency_pair_correlations.csv`, `rolling_correlation_summary_all_pairs_60d.csv`).

**6. Why are all 28 full-period correlations positive?**
All quotes share EUR as the base. A common EUR movement shifts many quotes in the same direction, which induces positive co-movement even when bilateral drivers differ. This is an interpretation boundary, not proof of a common cause.

**7. CHF has the lowest full-period volatility but the largest single move. Is that contradictory?**
No. A standard deviation and a single extreme answer different questions. CHF's daily volatility is 0.463204%, but its 2015-01-15 log change is −15.553938% and its 60-day rolling volatility peaks at 2.107576% (`daily_returns_summary.csv`, `rolling_volatility_summary_60d.csv`).

**8. Why 60 observations for the rolling window?**
It is about three trading months: long enough to estimate a correlation, short enough to show regime changes. The sensitivity check with 30/60/120 observations shows the ordering of pair variability is stable, while shorter windows are noisier (`window_sensitivity_summary.csv`, `window_sensitivity.png`).

**9. Why average linkage and `sqrt(2(1-r))`?**
The distance converts a correlation into a metric; average linkage balances single and complete linkage and is a standard exploratory choice. The tree is cut into 2, 3 and 4 clusters to show sensitivity; no optimal cluster count is claimed (`docs/methods.md`).

**10. Is the clustering stable?**
It is exploratory and depends on the period, common base, distance and linkage. USD–HKD merge first at 0.083 and CHF joins last; the 2/3/4-cluster partitions are saved, but no stability claim is made (`currency_cluster_linkage.csv`).

**11. Do the extreme dates drive the correlations?**
Not the overall ranking. Dropping 2015-01-15 and 2016-06-24 changes a pair correlation by at most +0.054 (JPY–CHF), and the Spearman rank correlation between baseline and outlier-excluded vectors is 0.996. CHF's daily volatility falls by 0.069 percentage points (`outlier_sensitivity_*.csv`, `outlier_sensitivity.png`).

**12. What do the bootstrap intervals add?**
They show sampling uncertainty. With 1,000 moving-block replicates and block length 60, USD–HKD has a narrow interval [0.9948, 0.9977], while weak pairs such as JPY–GBP have wide intervals [0.0552, 0.2965] (`correlation_bootstrap_ci.csv`).

## Parallel computing

**13. Why does a fresh process pool take about 1 second when serial is 18 ms?**
On Windows, `spawn` starts new interpreters, imports NumPy/pandas, transfers data, computes, collects results and shuts down. For a 28-pair workload, that fixed cost dominates. Fresh pool median 0.98–1.07 s versus serial 17.9–18.6 ms (`pool_reuse_benchmark_summary.csv`, `parallel_one_shot_runtime.png`).

**14. Why is the reused pool not faster than serial at 28 pairs?**
Per-task messages dominate: the serial median is only 18 ms, so 28 round trips are comparable to the whole computation. Batching reduces messages and reaches 11.3 ms at 4 workers (1.64x). This is why batching is used (`parallel_reused_pool_runtime.png`).

**15. Why does 8 workers reach only 5.86x, not 8x?**
Amdahl's law, process start-up amortisation, inter-process transfer and load balance. At 2,016 pairs and 4,096 observations the 8-worker median is 261.7 ms against 1,532.6 ms serial, i.e. 5.86x and 73% efficiency (`scaling_benchmark_summary.csv`, `parallel_scaling_speedup.png`). An Amdahl check on the medians implies about a 5% serial fraction at eight workers.

**16. Why processes instead of threads?**
Threads share memory and avoid serialisation, but the rolling-correlation workload stays near 1.0x with 2/4/8 threads in this experiment, consistent with the GIL and Python-level overhead. Processes scale to 5.86x. The trade-off is start-up and transfer cost (`parallel_thread_vs_process.png`).

**17. Why not Spark or Hadoop?**
The data are 8 series × 4,096 observations. Distributed frameworks add JVM/cluster start-up, scheduling and serialisation costs that are large relative to a 20 ms serial workload. The scaling experiment shows where local processes become worthwhile; a distributed framework would be appropriate at a much larger scale or with distributed storage. The report should state this as a design choice, not a claim that Spark is never useful (`note/parallel_scaling_analysis.md`).

**18. Why synthetic data for the scaling experiment?**
The real data cannot be enlarged without changing the research question. Synthetic factor-model series keep the computation identical while varying the number of pairs and observations. They are a benchmark device; the real-data findings are unchanged (`scaling_benchmark_environment.csv`).

## Impact, limitations and future work

**19. What is the real-world relevance?**
The correlation structure is a first step for currency-risk monitoring and diversification: highly correlated pairs offer little diversification, and time-varying correlations matter for risk limits. The parallel results are relevant to choosing process pools and batching for repeated rolling-window tasks. Avoid claiming profitable trading strategies.

**20. What are the main limitations?**
Eight currencies, one 16-year sample, daily reference rates, a common EUR base, overlapping windows, one machine for the benchmarks, and no causal identification. The report should state each limitation next to the claim it constrains (`docs/methods.md`).

**21. What would you do with more time?**
Higher-frequency data, more currencies, a formal common-factor decomposition, window and cluster stability tests, a Spark/Hadoop comparison at larger scale, and a proper event study for the policy dates.
