# 项目流程说明（Open Project 五步）

## 概览

- **数据：** ECB `eurofxref-hist.csv`，使用 2010-01-04 至 2025-12-31，共 4,097 个日度观测、4,096 个日对数变化。
- **环境：** Python 3.11.9 + NumPy / pandas / Matplotlib / SciPy；Windows，进程池 `spawn`。
- **当前状态：** 第 1–4 步完成；第 5 步已完成 10 页报告草稿，PPT 与 Cover Sheet 待做。
- **一键重建全部图：** `python data/regenerate_figures.py`（22 张图，全部由代码生成）。

## 研究问题

1. 八个币种的日度变化和波动有什么差异？
2. 哪些货币同向变动，这种关系随时间稳定吗？
3. 相关性聚类能否概括货币结构，结论对窗口和极值是否稳健？
4. 对滚动相关这种“小规模、可重复”的任务，进程池、batching、线程和数据规模分别带来什么代价和收益？

## 五步流程总览

| 步骤 | 核心问题 | 主要方法 | 主要产出 |
|---|---|---|---|
| **1. 收集数据** | 用什么数据、取哪段、取哪些币种？ | ECB 历史参考汇率；2010–2025；8 个覆盖完整的币种；记录来源与口径 | 原始 CSV、来源说明、清洗摘要 |
| **2. 预处理与可视化** | 数据能否直接计算；趋势、分布、极值怎么呈现？ | 日期/重复/缺失/异常校验；日对数变化；月环比；首日=100；折线、直方、箱线、散点、热图 | 清洗数据、收益 CSV、基础图、清洗记录 |
| **3. 进一步分析** | 波动、相关、聚类、稳健性各说明什么？ | 全期/年度/滚动波动；28 对 Pearson；60 日滚动相关；平均连接聚类；窗口/极值/bootstrap | 波动图、相关矩阵、树状图、敏感性 CSV、研究发现 |
| **4. 并行计算与性能** | 并行在什么规模下值得；瓶颈在哪？ | 串行 vs fresh/reused/batched 进程池；2/4/8 worker；28–2,016 对 scaling；线程；chunksize | 并行代码、基准表、7 张性能图、两份并行笔记 |
| **5. 总结与展示** | 如何把证据写成可评分的报告；如何复现？ | IEEEtran 报告；图表索引；评分映射；Q&A；运行日志；一键重建图 | 10 页报告草稿；文档与支持材料；PPT/Cover Sheet 待做 |

## 分步明细

### 第 1 步：收集数据

| 子项 | 研究了什么问题 | 解决方法 | 生成什么 |
|---|---|---|---|
| 1.1 数据来源与版本 | 哪个公开来源有足够长的历史、统一口径、可引用？ | 选用 ECB *euro foreign exchange reference rates* 的 `eurofxref-hist.csv`；记录 URL、快照日期、文件规模（7,141 行 × 42 列，1999-01-04 至 2026-11-20） | 原始数据 [eurofxref-hist.csv](../data/eurofxref-hist.csv)；来源说明 [data_source.md](data_source.md) |
| 1.2 年份与币种筛选 | 哪段时间和哪些币种覆盖完整、适合比较？ | 取 2010-01-04–2025-12-31；选 CNY/USD/JPY/GBP/HKD/CHF/AUD/CAD；检查八个币种在窗口内无缺失 | 4,097 行清洗数据；[cleaning_summary.csv](../data/cleaning_output/cleaning_summary.csv) |
| 1.3 字段含义与报价基准 | 报价方向、单位、缺失标记如何定义？ | 明确“外币/1 EUR”；正的对数变化 = 欧元升值；原始 `N/A` 不插补；记录字段字典与选择理由 | 数据说明文档；README 的数据节 |

### 第 2 步：预处理与可视化

| 子项 | 研究了什么问题 | 解决方法 | 生成什么 |
|---|---|---|---|
| 2.1 日期、重复、缺失、异常 | 数据能否直接进入计算？ | 兼容 `YYYY/MM/DD` 与 `YYYY-MM-DD`；排序与唯一性检查；冲突日期检查；非正/无穷值检查；缺失报告；不插补、不缩尾 | 清洗数据 [fx_eur_8currencies_2010_2025.csv](../data/cleaning_output/fx_eur_8currencies_2010_2025.csv)；缺失报告；清洗摘要 |
| 2.2 变化率与标准化 | 如何跨币种比较，且时间上可加？ | 日对数变化 `100*ln(P_t/P_{t-1})`；月环比用简单百分比；走势用首日=100 指数化 | 4,096 条日收益 [fx_daily_log_returns_2010_2025.csv](../data/analysis_output/fx_daily_log_returns_2010_2025.csv)；月度变化表 |
| 2.3 基础可视化 | 趋势、分布、极值、相关结构怎么呈现？ | 折线图（指数走势、日变化）、直方图、箱线图、散点图、月度热图、波动对比图 | 基础图见 [figures/](../data/analysis_output/figures)；新增箱线/散点/波动对比三张图 |

### 第 3 步：进一步分析

| 子项 | 研究了什么问题 | 解决方法 | 生成什么 |
|---|---|---|---|
| 3.1 波动 | 各币种波动差异有多大，是否随时间变化？ | 全期日标准差（`ddof=1`，非年化）；年度标准差；60 日滚动标准差（4,037 个窗口） | 日/年/滚动波动 CSV 与图；JPY 全期最高 0.642%，CHF 最低 0.463% 但 60 日峰值 2.108% |
| 3.2 相关性与时间变化 | 哪些货币同向，关系稳定吗？ | 28 对全期 Pearson；60 日滚动相关及汇总；相关热图 | 相关矩阵、货币对表、滚动相关汇总与图；USD–HKD 0.9966，CHF–AUD 0.1064，JPY–AUD 滚动区间 −0.6009 至 0.8077 |
| 3.3 聚类 | 相关结构能否分成可解释的组？ | 距离 `sqrt(2(1-r))`；平均连接层次聚类；切 k=2/3/4 | 树状图、linkage 表、cluster assignments；USD–HKD 先合并（0.0829），CHF 最后加入（1.2410） |
| 3.4 稳健性与不确定性 | 结论是否依赖窗口、两个极值日或抽样？ | 30/60/120 窗口对比；剔除 2015-01-15 与 2016-06-24；1,000 次 block bootstrap（块长 60） | 窗口/极值敏感性 CSV、bootstrap 区间与图；Spearman 0.9956，JPY–CHF Δr +0.0541，CHF 波动 −0.0688 pp |
| 3.5 补充分析 | 月度节奏和尾部风险是否被全期统计掩盖？ | 月末简单百分比变化与日历热图；经验分位数、尾部均值、≥1% 阈值计数 | 月度变化表/热图；极值汇总与 top-10 表；CHF 单日 −15.55%，JPY ≥1% 占比 10.16% |

### 第 4 步：并行计算与性能

| 子项 | 研究了什么问题 | 解决方法 | 生成什么 |
|---|---|---|---|
| 4.1 工作负载与串行基线 | 并行前串行多快，结果如何校验？ | 28 对 × 60 日窗口 × 4,096 观测；同一计算函数；10 次重复；`allclose(rtol=1e-10, atol=1e-12)` | 串行中位数 17.9–18.6 ms；串行/并行逐值一致的检查代码 |
| 4.2 进程池策略 | 启动、传输、调度成本有多大？ | fresh pool / reused pool / reused+batched；barrier + warm-up 确保 worker 全部就绪；计时口径分开 | [pool_reuse_benchmark_summary.csv](../data/analysis_output/pool_reuse_benchmark_summary.csv)；3 张基准图；fresh pool 约慢 55 倍，batching 在 4 worker 达 1.640x |
| 4.3 数据规模 × 进程数 | 并行在什么规模下开始划算？ | 合成 factor-model 序列，28/120/496/2,016 对；2/4/8 worker；worker-local 数据；5 次重复 | [scaling_benchmark_summary.csv](../data/analysis_output/scaling_benchmark_summary.csv)；3 张 scaling 图；2,016 对 / 8 worker 为 5.86x、73% 效率 |
| 4.4 线程与 chunksize | 线程是否可行；batching 粒度怎么选？ | ThreadPoolExecutor 对照；chunksize 1/2/4/7/14/28 扫描（2/4/8 worker） | [chunksize_sweep.csv](../data/analysis_output/chunksize_sweep.csv)；线程 1.04–1.09x；4 worker 最佳 chunksize=4（1.835x），单 chunk 仅 0.630x |
| 4.5 主流程集成 | 并行能否进入正式分析，而不只是 benchmark？ | 给 [analyze_all_rolling_correlations.py](../data/analyze_all_rolling_correlations.py) 加 `--workers`；默认串行；并行结果与串行逐值一致 | 可选的并行分析入口；验证记录 |

### 第 5 步：总结与展示

| 子项 | 研究了什么问题 | 解决方法 | 生成什么 |
|---|---|---|---|
| 5.1 报告 | 如何把数据、方法、结果和局限组织成可评分报告？ | 按 IEEEtran 模板改写为 Open Project 结构：任务、数据、验证、基线、改进、结果、AI 声明、讨论、复现、分工 | 10 页报告 PDF 与 LaTeX 源码：[report/](../report) |
| 5.2 展示 | 如何在有限时间内讲清方法和结果？ | 计划 12–15 页 PPT：数据、EDA、相关/聚类、并行、scaling、限制、future work | **待做**（PPT 与 Cover Sheet） |
| 5.3 复现与支持材料 | 别人能否从原始数据重建所有结果？ | README 运行顺序、`requirements.txt`、环境 CSV、运行日志、一键重建图脚本 | [README.md](../../README.md)、[requirements.txt](../requirements.txt)、[run_log.md](run_log.md)、[regenerate_figures.py](../data/regenerate_figures.py) |
| 5.4 评分映射与 Q&A | 报告是否覆盖 rubric；演示会被问什么？ | 评分项到证据的映射；21 条 Q&A；可引用推测与官方来源 | [assessment_mapping.md](assessment_mapping.md)、[qa_bank.md](qa_bank.md)、[interpretations.md](interpretations.md) |

## 运行顺序

完整命令见 [README.md](../../README.md) 的 Quick start。按阶段概括：

```powershell
# 1) 清洗与收益
python data/clean_exchange_rates.py
python data/calculate_returns.py

# 2) 描述、可视化、相关、聚类、波动、月度/极值
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

# 3) 稳健性
python data/plot_distributions.py
python data/analyze_window_sensitivity.py
python data/analyze_outlier_sensitivity.py
python data/bootstrap_correlations.py

# 4) 并行与性能
python data/benchmark_pool_reuse.py
python data/plot_parallel_performance.py
python data/scaling_parallel_correlations.py
python data/benchmark_chunksize.py

# 5) 一键重建全部图（不重跑计时）
python data/regenerate_figures.py
```

## 说明

- 实际绘图使用 **Matplotlib**，未使用计划表中的 Seaborn；效果与可复现性已满足要求。
- “标准化走势”实现为**首日=100 的指数化**，不是 z-score；报告里已写明这一口径。
- 所有图由脚本生成，PNG 只是产物；`regenerate_figures.py` 会检查 22 张图是否齐全。
- 并行计时数字对机器负载和解释器版本敏感；当前数字已冻结在 CSV 和笔记中，重跑会小幅漂移。
- 第 5 步还剩 PPT 与 Cover Sheet；报告草稿已完成并填入 Group 9 信息，提交前核对 AI 声明和工时总额。
