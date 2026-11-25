# Assessment Mapping

This table maps the **CS4880 Open Project (40%)** rubric to the artefacts in this repository. It is a preparation aid: the rubric scores the **report** and the **presentation**, not the repository itself. The report and slides are prepared separately.

| Rubric item | Points | Where the evidence lives | Current status | What still has to happen |
|---|---:|---|---|---|
| Real World Impact / Creativity | 5 | `docs/interpretations.md`; `note/research_findings_and_report_outline.md`; findings table | Topic is on the suggested list; candidate interpretations with official sources are written | Turn the notes into 1–2 report pages: why co-movement, volatility and pipeline performance matter; keep conjectures labelled |
| Solid Works and Output Amount | 20 | 21 scripts, 22 figures, 32 analysis CSVs, 4 cleaning CSVs, 4 notes, 6 docs | Strong volume and reproducibility | Write the report; include the figure index and the reproduction appendix |
| Technical Depth and Correctness | 20 | `docs/methods.md`; `window_sensitivity_summary.csv`; `outlier_sensitivity_*.csv`; `correlation_bootstrap_ci.csv`; validation checks in every script | Strong: formulas, ddof=1, window definition, clustering distance, bootstrap, sensitivity, correctness checks | Put the formulas and the sensitivity discussion into the report; do not overclaim causality |
| Parallel Computing Elements | 20 | `benchmark_pool_reuse.py`; `scaling_parallel_correlations.py`; `benchmark_chunksize.py`; `analyze_all_rolling_correlations.py --workers`; three benchmark figures + three scaling figures | Strong: serial/fresh/reused/batched, 2/4/8 workers, 28–2,016 pairs, process vs thread, chunksize sweep, correctness, setup costs | Explain why this scale uses processes rather than Spark/Hadoop; connect to Amdahl, IPC and memory hierarchy |
| Use of Written English | 5 | All notes, `README.md`, `docs/*.md` | Clear and precise in the notes | Maintain the same style in the report; proofread |
| Technical Presentation Amount | 20 | `docs/figure_index.md`; `docs/qa_bank.md` | Not started | Build 12–15 slides covering data, EDA, correlation/clustering, parallel design, scaling, limitations, future work |
| Technical Presentation Skills | 5 | — | Not started | Rehearse with a timer; assign speaking roles |
| Question and Answer (Q&A) | 5 | `docs/qa_bank.md`; `docs/methods.md` | Draft question bank available | Rehearse short answers; keep evidence numbers at hand |

## Hard requirements from the course outline

- **Group size:** 3–4 members; confirm on Canvas and record names and contributions on the cover sheet.
- **Deadline:** Saturday of Week 13; late submissions receive 0. Confirm the exact date on Canvas.
- **Deliverables:** Project Cover Sheet, Project Report, Supporting Materials — all submitted on Canvas.
- **Presentation:** Weeks 12–13 during lecture time; the schedule is randomly assigned.
- **Academic honesty:** CityU rules and VeriGuide. Cite the ECB data, software libraries and any external source; record contributions accurately.

## Repository status at a glance

| Item | Count / status |
|---|---|
| Analysis and benchmark scripts | 21 |
| Figures | 22 |
| Analysis CSVs | 32 |
| Cleaning CSVs | 4 |
| Notes (findings, exploratory, parallel, scaling) | 4 |
| Documentation (source, methods, figures, generation, workflow, assessment, interpretations, Q&A, run log) | 9 |
| Report (LaTeX/PDF draft) | 10-page draft in `report/`; Group 9 details filled in; verify AI statement and total hours |
| Presentation (.pptx) | **not yet written** |
| Cover sheet | **not yet written** |

The analysis workflow is ready for a high-scoring report. The remaining work is writing and packaging, not new analysis.
