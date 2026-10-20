"""Builds clean Maryland UI datasets from US DOL ETA-9050 (first-payment time lapse)
and ETA-539 (weekly claims). Raw files: https://oui.doleta.gov/unemploy/csv/ar9050.csv, ar539.csv"""
import pandas as pd, json, os
RAW = os.path.join(os.path.dirname(__file__), '..', 'raw')
OUT = os.path.join(os.path.dirname(__file__), 'data')

# ---- ETA 9050: 96 cols = 24 groups of 4 [Total, UI, UCFE, UCX]; groups alternate intrastate/interstate
# per 7-day band: <=7, 8-14, 15-21, 22-28, ... ; we use the Total column of each group.
t = pd.read_csv(f'{RAW}/ar9050.csv')
t['month'] = pd.to_datetime(t['rptdate']).dt.to_period('M').dt.to_timestamp()
grp = lambda i: t[f'c{4*i+1}']
t['total'] = sum(grp(i) for i in range(24))
for k, (name, gs) in {'d14': ('w14', range(0, 4)), 'd21': ('w21', range(0, 6))}.items():
    t[name] = sum(grp(i) for i in gs)
t['over_70'] = grp(22) + grp(23)
t['pct21'] = (t.w21 / t.total * 100).round(2)
t['pct14'] = (t.w14 / t.total * 100).round(2)
cols = ['st', 'month', 'total', 'w14', 'w21', 'pct14', 'pct21']
t = t[cols].dropna()
md = t[t.st == 'MD'].drop(columns='st')
md['benchmark_pct'] = 87
md['late_payments'] = md.total - md.w21
md.to_csv(f'{OUT}/md_first_payment_timeliness_monthly.csv', index=False)

# state comparison: trailing 12 months, 21-day
last = t.month.max()
tr = t[t.month > last - pd.DateOffset(months=12)]
s = tr.groupby('st')[['w21', 'total']].sum()
s['pct21'] = (s.w21 / s.total * 100).round(1)
s['rank'] = s.pct21.rank(ascending=False, method='min').astype(int)
s = s.sort_values('pct21', ascending=False).reset_index()
s.to_csv(f'{OUT}/state_comparison_trailing12m.csv', index=False)

# ---- ETA 539 weekly claims for MD: c3 = initial claims, c8 = continued weeks claimed, c19 = insured unemployment rate
w = pd.read_csv(f'{RAW}/ar539.csv')
mw = w[w.st == 'MD'].copy()
mw['week_ending'] = pd.to_datetime(mw.c2)   # c2 = reflecting week ended
mw = mw.rename(columns={'c3': 'initial_claims', 'c8': 'continued_weeks_claimed', 'c19': 'insured_unemp_rate'})
mw = mw[['week_ending', 'initial_claims', 'continued_weeks_claimed', 'insured_unemp_rate']]
mw.to_csv(f'{OUT}/md_weekly_claims.csv', index=False)

# monthly workload vs timeliness
mw['month'] = mw.week_ending.dt.to_period('M').dt.to_timestamp()
mm = mw.groupby('month').initial_claims.sum().reset_index()
j = md.merge(mm, on='month', how='inner')
j.to_csv(f'{OUT}/md_workload_vs_timeliness.csv', index=False)

print('MD months', len(md), md.month.min().date(), md.month.max().date())
print(s[s.st.isin(['MD','VA','PA','DE','WV','DC'])])
print('states', len(s), 'median', s.pct21.median())
r = j[(j.month >= '2010-01-01') & ((j.month < '2020-03-01') | (j.month >= '2022-01-01'))]
print('corr claims vs pct21 (excl. covid):', round(r.initial_claims.corr(r.pct21), 2))
print(md.tail(14).to_string())
print(j[j.month.between('2020-02-01','2021-06-01')][['month','initial_claims','pct21']].to_string())

# ---- delay bands for MD, trailing 12 months (intrastate+interstate Total column per 7-day band)
tt = pd.read_csv(f'{RAW}/ar9050.csv'); tt = tt[tt.st == 'MD'].copy()
tt['month'] = pd.to_datetime(tt.rptdate).dt.to_period('M').dt.to_timestamp()
tt = tt[tt.month > tt.month.max() - pd.DateOffset(months=12)]
labels = ['0-7', '8-14', '15-21', '22-28', '29-35', '36-42', '43-49', '50-56', '57-63', '64-70', '71-77', '78+']
bands = pd.DataFrame({'days': labels, 'payments': [int(tt[f'c{8*p+1}'].sum() + tt[f'c{8*p+5}'].sum()) for p in range(12)]})
bands['pct'] = (bands.payments / bands.payments.sum() * 100).round(1)
bands.to_csv(f'{OUT}/md_delay_bands_trailing12m.csv', index=False)
print(bands.to_string())
