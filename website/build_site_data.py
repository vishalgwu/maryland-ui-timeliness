"""Builds website/data/site.json: every number the web app shows, computed from the public ETA 9050 / ETA 539 files
(plus the department-reported series in md-ui-project/data/department.json). Run after md-ui-project/build_*.py."""
import pandas as pd, numpy as np, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
RAW = os.path.join(ROOT, 'raw'); D = os.path.join(ROOT, 'md-ui-project', 'data')

NAMES = {'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut',
         'DE': 'Delaware', 'DC': 'District of Columbia', 'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois',
         'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
         'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri', 'MT': 'Montana',
         'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
         'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania',
         'RI': 'Rhode Island', 'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
         'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming',
         'PR': 'Puerto Rico', 'VI': 'Virgin Islands'}

t = pd.read_csv(f'{RAW}/ar9050.csv')
t['date'] = pd.to_datetime(t.rptdate); t['month'] = t.date.dt.to_period('M').dt.to_timestamp()
g = lambda i: t[f'c{4*i+1}']
t['total'] = g(0) + g(1)                   # pair 0 = all first payments
t['w21'] = sum(g(i) for i in range(2, 8))  # pairs 1-3 = 0-7, 8-14, 15-21 days
last = t.month.max()

# ---- states: trailing 12 months and 2019
cur = t[t.month > last - pd.DateOffset(months=12)].groupby('st')[['w21', 'total']].sum()
pre = t[t.date.dt.year == 2019].groupby('st')[['w21', 'total']].sum()
st = pd.DataFrame({'now': cur.w21 / cur.total * 100, 'pre': pre.w21 / pre.total * 100, 'payments': cur.total})
st['change'] = st.now - st.pre
st['rank'] = st.now.rank(ascending=False, method='min').astype(int)
states = [dict(st=k, name=NAMES.get(k, k), now=round(r.now, 1), pre=round(r.pre, 1), change=round(r.change, 1), rank=int(r['rank']), payments=int(r.payments))
          for k, r in st.iterrows()]

# ---- rolling 12-month series per state (and the national pool), 2015+
months = pd.date_range('2015-01-01', last, freq='MS')
def roll(df):
    m = df.groupby('month')[['w21', 'total']].sum().reindex(pd.date_range('2013-01-01', last, freq='MS')).fillna(0)
    r = m.rolling(12).sum(); return (r.w21 / r.total * 100).reindex(months)
series = {k: [None if pd.isna(v) else round(float(v), 1) for v in roll(t[t.st == k])] for k in st.index}
series['US'] = [round(float(v), 1) for v in roll(t)]

# ---- Maryland monthly detail
md = t[t.st == 'MD'].set_index('month').loc['2015-01-01':]
mdm = [dict(m=i.strftime('%Y-%m'), total=int(r.total), w21=int(r.w21), pct=round(r.w21 / r.total * 100, 1)) for i, r in md.iterrows()]

# ---- delay bands (Maryland, 12 months)
bd = pd.read_csv(f'{D}/md_delay_bands_trailing12m.csv')
bands = bd.to_dict('records')

# ---- weekly claims, forecast, scatter
wk = pd.read_csv(f'{D}/md_weekly_claims.csv', parse_dates=['week_ending'])
wk = wk[wk.week_ending >= '2019-01-01']
weekly = [dict(d=r.week_ending.strftime('%Y-%m-%d'), ic=int(r.initial_claims)) for r in wk.itertuples()]
an = json.load(open(f'{D}/analytics.json'))
sc = pd.read_csv(f'{D}/md_workload_vs_timeliness.csv', parse_dates=['month'])
sc = sc[sc.month >= '2023-01-01']
scatter = [dict(m=r.month.strftime('%Y-%m'), claims=int(r.initial_claims), late=int(r.late_payments), pct=r.pct21) for r in sc.itertuples()]
late_corr = round(float(sc.late_payments.corr(sc.initial_claims)), 2)

dep = json.load(open(f'{D}/department.json'))
mdrow = next(s for s in states if s['st'] == 'MD')
l12 = md.loc[md.index > last - pd.DateOffset(months=12)]
w21_12, tot_12 = int(l12.w21.sum()), int(l12.total.sum())
us12 = t[t.month > last - pd.DateOffset(months=12)]
kpi = dict(now=mdrow['now'], latest=mdm[-1]['pct'], latest_month=mdm[-1]['m'], rank=mdrow['rank'], n=len(states),
           total12=tot_12, ontime12=w21_12, late12=tot_12 - w21_12, short=int(round(0.87 * tot_12 - w21_12)),
           us_pool=round(float(us12.w21.sum() / us12.total.sum() * 100), 1), median=round(float(np.median([s['now'] for s in states])), 1),
           meet=int(sum(s['now'] >= 87 for s in states if s['st'] not in ('PR', 'VI'))), recovered=int(sum(s['change'] > -2 for s in states if s['st'] not in ('PR', 'VI'))),
           tail70=bands[-1]['pct'], late_mean=round(float(sc.late_payments.mean())), late_corr=late_corr, mape=an['mape'], asof=last.strftime('%Y-%m'))

site = dict(kpi=kpi, states=states, months=[m.strftime('%Y-%m') for m in months], series=series, md=mdm, bands=bands, weekly=weekly,
            hist=an['hist'], fc=an['fc'], scatter=scatter, annual=dep['annual'], fv=dep['fv'], fv_corr=dep['fv_corr'],
            claims_q=dep['claims_q'], fraud_share=dep['fraud_share'], wages=dep['wages'], wage_fraud=dep['wage_fraud'])
os.makedirs(os.path.join(HERE, 'data'), exist_ok=True)
json.dump(site, open(os.path.join(HERE, 'data', 'site.json'), 'w'), separators=(',', ':'))
print('site.json', os.path.getsize(os.path.join(HERE, 'data', 'site.json')) // 1024, 'KB'); print(kpi)
