"""Data for the 'Inside MD Labor' page.
Part A (hand-transcribed): figures shown in the Maryland Department of Labor briefing to the House Government, Labor and
Elections Committee, Feb 10, 2026 (https://mgaleg.maryland.gov/meeting_material/2026/gvc%20-%20134152049604952590%20-%20MD%20Labor%20GLE%20Committee%20Briefing%202.9.26%20FINAL.pdf).
Chart values were read from slide labels; they are the department's numbers, not mine.
Part B (computed): annual and quarterly 21-day timeliness from the public ETA 9050 file, used to cross-check the
department's chart and to compare against its fraud-flag share."""
import pandas as pd, numpy as np, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, '..', 'raw'); D = os.path.join(HERE, 'data')

# ---------- Part A: department-reported figures ----------
claims_q = {'Q1 2024': 37656, 'Q2 2024': 37188, 'Q3 2024': 34173, 'Q4 2024': 32543,
            'Q1 2025': 37066, 'Q2 2025': 37383, 'Q3 2025': 33203, 'Q4 2025': 36519}      # ETA 5159, regular UI + UCFE + UCX
fraud_share = {'Q4 2022': 28, 'Q1 2023': 35, 'Q2 2023': 32, 'Q3 2023': 29, 'Q4 2023': 25, 'Q1 2024': 21, 'Q2 2024': 22,
               'Q3 2024': 25, 'Q4 2024': 22, 'Q1 2025': 20, 'Q2 2025': 15, 'Q3 2025': 18, 'Q4 2025': 18}  # % new suspected ID fraud
wages_recovered = {'FY2021': 988188, 'FY2022': 752118, 'FY2023': 706551, 'FY2024': 1801503, 'FY2025': 2034876, 'FY2026 (Q1/Q2)': 1325420}
wage_fraud = {'cols': ['FY2024', 'FY2025', 'FY2026 (Q1/Q2)'], 'Site visits': [102, 433, 217], 'Workers interviewed': [1687, 3074, 1430],
              'Misclassified workers found': [199, 558, 113], 'Citations / settlements in lieu': [18, 37, 11], 'Referrals to sister agencies': [130, 375, 239]}

# ---------- Part B: computed from ETA 9050 ----------
t = pd.read_csv(f'{RAW}/ar9050.csv')
t['date'] = pd.to_datetime(t.rptdate)
g = lambda i: t[f'c{4*i+1}']
t['total'] = g(0) + g(1)
t['w21'] = sum(g(i) for i in range(2, 8))
t['y'] = t.date.dt.year
annual = {}
for name, sel in (('MD', t.st == 'MD'), ('US', t.st != '')):
    a = t[sel].groupby('y')[['w21', 'total']].sum()
    annual[name] = (a.w21 / a.total * 100).round(1)
annual = pd.DataFrame(annual).loc[2018:2025]
annual.to_csv(f'{D}/annual_timeliness_md_vs_us.csv')

md = t[t.st == 'MD'].copy(); md['q'] = md.date.dt.to_period('Q')
qa = md.groupby('q')[['w21', 'total']].sum(); qa['pct'] = (qa.w21 / qa.total * 100).round(1)
qa.index = [f'Q{p.quarter} {p.year}' for p in qa.index]
rows = [{'q': k, 'fraud': v, 'timely': float(qa.pct[k])} for k, v in fraud_share.items() if k in qa.index]
fv = pd.DataFrame(rows); fv.to_csv(f'{D}/fraud_share_vs_timeliness_quarterly.csv', index=False)
corr = round(float(fv.fraud.corr(fv.timely)), 2)
print('quarterly corr (fraud share vs % within 21 days), n =', len(fv), ':', corr)
print(annual.T.to_string())

json.dump({'claims_q': claims_q, 'fraud_share': fraud_share, 'wages': wages_recovered, 'wage_fraud': wage_fraud,
           'annual': {'years': [int(y) for y in annual.index], 'MD': annual.MD.tolist(), 'US': annual.US.tolist()},
           'fv': rows, 'fv_corr': corr}, open(f'{D}/department.json', 'w'))
