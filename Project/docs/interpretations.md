# Candidate Interpretations (Conjectures, Not Causal Estimates)

The course example asks for conjectures about the findings. The analysis itself is descriptive: it does not identify causal effects. This note separates the **observed statistic** from a **candidate explanation**, and records an external source for each event. In the report, label these as conjectures and keep the causal language conditional.

## 1. CHF, 2015-01-15: the largest single daily change

- **Observation:** CHF's daily log change on 2015-01-15 is −15.553938%; its 60-observation rolling volatility peaks at 2.107576% in the window ending 2015-04-10.
- **Candidate explanation:** the Swiss National Bank discontinued the minimum exchange rate of CHF 1.20 per EUR with immediate effect on 15 January 2015. A policy regime change of this kind can produce a large, abrupt re-pricing.
- **Source:** Swiss National Bank, press conference introductory remarks, 15 January 2015, reproduced by the BIS: <https://www.bis.org/speeches/20150116-rationale-discontinuing-minimum-exchange-rate-and-lowering-interest-rates>
- **What would test it:** intraday data around the announcement, a narrow event window, and a comparison with other CHF episodes; none of these are in the current daily sample.
- **Do not claim:** that the SNB decision *caused* the exact −15.55% magnitude, or that the same move would recur.

## 2. GBP and JPY, 2016-06-24: opposite signs on the same day

- **Observation:** GBP's daily log change is +5.282616% and JPY's is −6.123226% on 2016-06-24. Both are among the largest moves in their series.
- **Candidate explanation:** the UK EU referendum result was declared on 24 June 2016. A large GBP depreciation and a JPY appreciation would be consistent with a re-pricing of political risk and safe-haven demand, but the current data cannot separate these channels.
- **Source:** Electoral Commission, official result of the EU referendum, 24 June 2016: <https://www.electoralcommission.org.uk/media-centre/official-result-eu-referendum-declared-electoral-commission-manchester>
- **What would test it:** event-window regressions with a market factor, intraday timing, and a comparison with other political-risk events.
- **Do not claim:** that the referendum *caused* the move, or that the sign pattern is a general law.

## 3. March 2020: a cross-currency volatility cluster

- **Observation:** the monthly heatmaps show large changes for several currencies in March 2020, and the daily-change panels show a volatility cluster around that period.
- **Candidate explanation:** the World Health Organization characterised COVID-19 as a pandemic on 11 March 2020, and global financial markets experienced a broad risk-off episode. A common global shock is consistent with a cross-currency volatility cluster.
- **Source:** WHO Director-General's opening remarks, 11 March 2020: <https://www.who.int/news-room/speeches/item/who-director-general-s-opening-remarks-at-the-media-briefing-on-covid-19---11-march-2020>
- **What would test it:** a common-factor decomposition and high-frequency data; the current sample is daily and only eight currencies.
- **Do not claim:** that the pandemic declaration *caused* the observed volatility, or that the pattern is specific to COVID-19.

## 4. How to phrase a conjecture in the report

Use four sentences:

1. **Observation:** the statistic and its date (with the CSV or figure reference).
2. **Candidate explanation:** the event or mechanism, stated as a possibility.
3. **Source:** an official or peer-reviewed reference.
4. **Test / limitation:** what evidence would be needed, and what the current data cannot establish.

Example:

> CHF recorded its largest daily log change (−15.55%) on 15 January 2015, the day the SNB discontinued the EUR/CHF floor (SNB, 2015). This is consistent with an abrupt policy re-pricing, but the daily data cannot identify the intraday mechanism or the counterfactual path.

## 5. Interpretation boundaries

- All quotes share EUR as the base; a common EUR movement can induce positive correlation.
- The data are daily reference rates, not transaction prices; successive observations may span weekends and holidays.
- Full-period correlations and single-day extremes answer different questions; do not use one to support the other.
- The parallel results are about computational cost, not about market behaviour.
