# Maryland Unemployment Insurance: Are Claimants Paid Within 21 Days?

An end-to-end analytics project on how quickly Maryland pays first unemployment insurance (UI) benefits, built from public US Department of Labor data. It includes two interactive dashboards, a peer benchmark of all 53 UI jurisdictions, a claims forecast, and a recovery-trajectory analysis.

The federal timeliness standard is that **87% of first payments should go out within 21 days** of the first compensable week.

## Key findings

| Metric | Value |
|---|---|
| Maryland, last 12 months, paid within 21 days | **78.5%** (standard: 87%) |
| Latest month (Sep 2026) | 74.6% |
| Rank among 53 jurisdictions (50 states, DC, PR, VI) | **50th**; median is 89.3% |
| Gap to the national pool (rolling 12 months) | 9.4 points |
| Late first payments, last 12 months | about 26,700 |
| On-time payments needed to reach 87% | about 10,500 more per year |
| Pace since 2023 | about +1.8 points per year, which reaches 87% around **mid-2031** at that rate |

Other findings:
- **Not a volume problem.** Since 2023, late payments average about 2,440 a month whatever the claim volume (correlation 0.09). That points to process bottlenecks such as issue resolution and identity verification, not intake capacity.
- **Structural, not seasonal.** Maryland has been below Virginia, Pennsylvania, DC and the national pool in 65 of the 69 months since January 2021.
- **Surges are predictable.** A seasonal model forecasts weekly initial claims with a 5.7% average error on a 13-week backtest.

## Dashboards

Open the HTML files directly in a browser. They are self-contained and work offline.

**Executive overview** ([`md-ui-project/dashboard.html`](md-ui-project/dashboard.html)): KPIs, the 21-day trend against the 87% standard, a 53-jurisdiction ranking, the delay distribution and weekly claims demand.

![Executive overview dashboard](docs/images/dashboard_overview.png)

**Analytics deep dive** ([`md-ui-project/analytics_dashboard.html`](md-ui-project/analytics_dashboard.html)): peer trends, a seasonality heatmap, claims versus timeliness, a 13-week claims forecast, caseload trends and a what-if slider.

![Analytics deep dive dashboard](docs/images/dashboard_analytics.png)

## Recovery trajectory

A linear trend fitted to the rolling 12-month rate since January 2023 shows how long Maryland would take to reach 87% at its current pace.

![Recovery trajectory](docs/images/recovery_trajectory.png)

The range shown comes from the slope's standard error. Rolling windows overlap, so it understates the real uncertainty. Treat the date as indicative, not a forecast.

## Project structure

```
md-ui-project/
  download_raw.py                  # fetch the two public DOL files into raw/
  build_data.py                    # clean datasets from ETA 9050 + ETA 539
  build_analytics.py               # peers, heatmap, workload, claims forecast
  build_trajectory.py              # recovery-trajectory analysis + chart
  build_dashboard.py               # builds dashboard.html
  build_analytics_dashboard.py     # builds analytics_dashboard.html
  data/                            # clean CSVs (load straight into Power BI)
docs/images/                       # README images
```

## Run it

Requires Python 3.9+ with `pandas`, `numpy` and `matplotlib`.

```bash
python md-ui-project/download_raw.py
python md-ui-project/build_data.py
python md-ui-project/build_analytics.py
python md-ui-project/build_trajectory.py
python md-ui-project/build_dashboard.py
python md-ui-project/build_analytics_dashboard.py
```

The CSVs in `md-ui-project/data/` can be loaded directly into Power BI Desktop (free) for further visuals.

## Data and method

- **Sources:** US Department of Labor, Employment and Training Administration, public files [ETA 9050 First Payments Time Lapse](https://catalog.data.gov/dataset/first-payments-time-lapse-eta-9050) (monthly) and [ETA 539 Weekly Claims](https://catalog.data.gov/dataset/unemployment-insurance-weekly-claims-extended-benefits-trigger-data-eta-539). Both come from [oui.doleta.gov](https://oui.doleta.gov/unemploy/DataDownloads.asp).
- **Timeliness** = first payments made within 21 days of the first compensable week divided by all first payments (intrastate and interstate, all programs).
- **Column layout of ETA 9050:** the file ships without a column dictionary. I worked out the layout (24 groups of 4 columns, alternating intrastate and interstate, in 7-day bands) and checked it against published reports: March 2020 comes out at 96.7%, in line with the roughly 97% reported at the time. Treat the figures as my own calculation, which may differ slightly from the Department's published reports.
- **Backdating caveat:** the Maryland Department of Labor has said the federal metric counts from the claim's effective date, so backdated claims can look late even when paid promptly. This dataset cannot separate that effect from agency delay. Claim-level timestamps would.
- **Forecast:** average weekly pattern since mid-2022 scaled to the last 8 weeks' level, with an 80% band from the residual spread and a 13-week backtest. It is a simple illustrative model.
- Correlations are descriptive, not causal.

## Possible next steps

- Claim-level timestamps (filed, adjudicated, approved, paid) and issue codes, to split agency-caused from claimant-caused delay.
- Regional or local-office breakdowns.
- A Power BI version of the dashboards on the same CSVs.
