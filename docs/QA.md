# Questions and Answers: Findings, Method and Next Steps

Short answers to the questions this analysis most often raises. Numbers are for the 12 months to September 2026 unless stated. See the [README](../README.md) for the full method.

## Findings

**1. What is the headline result?**
Maryland paid **72.5%** of first unemployment payments within 21 days, against the 87% federal standard. That is 48th of 53 jurisdictions (median 86.3%). About 17,100 of 62,300 first payments were late, and about 9,000 more on-time payments a year would reach 87%.

**2. Why is Maryland low?**
Public data cannot prove a single cause, but it narrows the field. The problem is persistent (below the national pool every month since January 2021), concentrated in a long tail (about 1 in 13 payments takes over 70 days), and not driven by claim volume. The department itself points to ID-fraud screening, flat federal funding, the loss of in-house call-center capacity and problems with its 2020 claims system. Claim-level timestamps would let us rank those causes.

**3. Is it a staffing or volume problem?**
Probably not mainly. Since 2023, late payments average about 1,600 a month whether weekly claims are low or high (correlation 0.01). Months with more claims have not had worse on-time rates. That points to process bottlenecks (identity checks, adjudication of disputed claims) rather than raw intake capacity. This is a correlation, not proof.

**4. What is the biggest surprise in the data?**
The shape of the delay. 34% of payments go out within a week and 72.5% within three, but 7.6% take over 70 days. The average hides that tail, and the tail is where targeted fixes would pay off.

**5. Is there a link between ID fraud and late payments?**
Weakly. The department reports that suspected-fraud claims fell from 35% of new claims (Q1 2023) to 18% (Q4 2025), and quarterly on-time rates tend to be higher when that share is lower (correlation -0.32). With only 13 quarters this is suggestive, not conclusive.

**6. When would Maryland reach 87%?**
Around 2030 if the rolling rate keeps rising about 4 points a year, as it has since 2023. That is indicative only: part of the rise is recovery from the 2022 trough, the uncertainty range is understated because rolling windows overlap, and a new surge or policy change would move it.

## Method and trust

**7. How do you know the numbers are right?**
Two checks. The delay bands add up to the file's total, and my annual rates match the department's own published chart (Maryland 2025: 69.3%; US 2025: 83.4%) and the reported June 2020 low of 14.1%. An early version of the calculation had a column error, which these checks caught and which is fixed and documented in the commit history.

**8. How is the on-time rate calculated?**
First payments made within 21 days of the first compensable week (the 0-7, 8-14 and 15-21 day bands, intrastate plus interstate) divided by all first payments, from the federal ETA 9050 file. The 12-month rate sums payments before dividing, so busy months carry proper weight.

**9. The state says backdating makes the metric look worse. How do you handle that?**
It is a fair point and this data cannot settle it. The federal clock starts at the claim's effective date, so a claim backdated three weeks looks late even if paid at once. I would measure two clocks: filing date to payment (what the agency controls) and effective date to payment (what the federal metric reports). That needs claim-level dates.

**10. How reliable is the claims forecast?**
It is a simple seasonal model (average weekly pattern since mid-2022, scaled to the last eight weeks). On a held-out 13-week backtest the average error was 5.7%. It cannot anticipate shocks such as a federal shutdown or a mass layoff, so it is for staffing plans, with the 80% band shown.

**11. What are the main limitations?**
Aggregate monthly data only, so no causes at claim level. Backdating cannot be separated from agency delay. Department figures on the third dashboard were read from slides. Correlations are descriptive. The forecast and trajectory are illustrative.

## Recommendations

**12. What would you do first?**
Get claim-level timestamps and issue codes (filed, identity verified, adjudicated, approved, paid). With those I would split agency delay from claimant delay, find which queues create the 70-day tail, and build one weekly dashboard with the 87% target on every chart.

**13. What would the operational dashboard track?**
Weekly intake against the forecast, age of pending claims by stage, percent paid within 14 and 21 days, share of claims in fraud or identity review and how long they wait there, call-back wait times, and a regional split, each with the 87% line.

**14. How do you balance fraud prevention against speed?**
It is a trade-off, not a contradiction. Stronger identity checks protect public money but can hold honest claimants. I would measure the share of flagged claims later released as legitimate and how long they waited. That shows whether screening is well targeted or just slow.

**15. How would you explain this to non-technical leaders or legislators?**
Lead with one number and one picture: "72.5% paid on time against an 87% standard, with about 9,000 more people a year needing to be paid faster." Then show the long-tail chart, name the two or three bottlenecks the data supports, and say plainly what the data cannot tell us yet.

**16. What data would you ask for next?**
Claim-level lifecycle timestamps, issue and adjudication codes, identity-verification outcomes and timing, call-center volumes and wait times, and local-office or region. Together these allow stage-level process mining.

## Tools

**17. What tools were used?**
Python (pandas, NumPy, Matplotlib) for the pipeline, Chart.js for the self-contained dashboards, and clean CSVs that load directly into Power BI Desktop. All of it rebuilds from two public federal files with the scripts in the repo.
