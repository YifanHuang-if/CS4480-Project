# Reproduction Run Log

- **Date:** 2026-11-22 (Asia/Shanghai).
- **Working directory:** `Project/`.
- **Interpreter:** Python 3.11.9.
- **Libraries:** NumPy 2.4.6, pandas 3.1.1, Matplotlib 3.11.2, SciPy 1.17.1.
- **Machine:** Windows, 16 logical CPUs; process pools use the `spawn` start method.
- **Data snapshot:** `data/eurofxref-hist.csv`, observations through 2026-11-20.
- **Inputs:** the raw ECB file plus `requirements.txt`.
- **Outputs:** 22 figures, 32 analysis CSVs, 4 cleaning CSVs.

## Commands executed

```powershell
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
python data/benchmark_pool_reuse.py
python data/plot_parallel_performance.py
python data/scaling_parallel_correlations.py
python data/benchmark_chunksize.py
python data/regenerate_figures.py
```

Optional verification of the parallel main analysis:

```powershell
python data/analyze_all_rolling_correlations.py --workers 4
```

The parallel and serial paths produced identical rolling-correlation values and summaries in this run.

## Checks performed

- The cleaning summary reports 7,141 raw rows, 4,097 retained rows, 4,096 daily changes, and no missing rates in the retained window.
- Every parallel result matches its serial reference (`rtol=1e-10`, `atol=1e-12`).
- The monthly compounding identity holds against month-end quote ratios.
- The bootstrap baseline matches the saved full-period correlations within the six-decimal storage rounding.
- Scatterplot correlations are recomputed and checked against the saved table.
- All 21 analysis scripts compile under Python 3.11.9.
- `regenerate_figures.py` rebuilt all 22 figures from code without re-measuring the benchmarks; the benchmark figures were redrawn from the frozen CSVs.

## Caveats

- Benchmark medians depend on machine load, interpreter build and background processes. The environment CSVs record the run.
- The ECB file is updated on each publication day; re-downloading changes the last observation. Record the snapshot date before re-running.
- The scaling series are synthetic factor-model data used only to vary workload size. They do not replace the real-data findings.
