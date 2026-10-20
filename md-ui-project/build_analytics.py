"""Advanced analytics for the Maryland UI project: rolling peer comparison, seasonality heatmap,
workload-vs-timeliness relationship, and a 13-week initial-claims forecast with a backtest.
Output: data/analytics.json (consumed by build_analytics_dashboard.py) + CSVs for Power BI."""
import pandas as pd, numpy as np, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, '..', 'raw')
D = os.path.join(HERE, 'data')

# ---------- 1. rolling 12-month 21-day rate: MD vs neighbors vs all-jurisdiction pool ----------
t = pd.read_csv(f'{RAW}/ar9050.csv')
t['month'] = pd.to_datetime(t.rptdate).dt.to_period('M').dt.to_timestamp()
g = lambda i: t[f'c{4*i+1}']
t['total'] = sum(g(i) for i in range(24))
t['w21'] = sum(g(i) for i in range(6))
t = t[t.month >= '2013-01-01'][['st', 'month', 'total', 'w21']]
peers = {'MD': ['MD'], 'VA': ['VA'], 'PA': ['PA'], 'DC': ['DC'], 'US pool': None}
roll = {}
for name, sts in peers.items():
    x = t if sts is None else t[t.st.isin(sts)]
    m = x.groupby('month')[['total', 'w21']].sum()
    r = m.rolling(12).sum()
    roll[name] = (r.w21 / r.total * 100).round(2)
roll = pd.DataFrame(roll).dropna().loc['2015-01-01':]
roll.index = roll.index.strftime('%Y-%m')
roll.reset_index(names='month').to_csv(f'{D}/rolling12m_21day_peers.csv', index=False)

# ---------- 2. heatmap year x month (MD) ----------
md = pd.read_csv(f'{D}/md_first_payment_timeliness_monthly.csv', parse_dates=['month'])
md = md[md.month >= '2015-01-01']
heat = md.assign(y=md.month.dt.year, m=md.month.dt.month).pivot(index='y', columns='m', values='pct21')
heat_out = {int(y): [None if pd.isna(v) else float(v) for v in row] for y, row in heat.iterrows()}

# ---------- 3. workload vs timeliness ----------
j = pd.read_csv(f'{D}/md_workload_vs_timeliness.csv', parse_dates=['month'])
j = j[j.month >= '2015-01-01']
covid = (j.month >= '2020-03-01') & (j.month <= '2021-06-01')
pts = [{'x': int(r.initial_claims), 'y': float(r.pct21), 'p': 'covid' if c else ('pre' if r.month < pd.Timestamp('2020-03-01') else 'post'), 'm': r.month.strftime('%Y-%m')}
       for r, c in zip(j.itertuples(), covid)]
norm = j[~covid]
corr = round(float(norm.initial_claims.corr(norm.pct21)), 2)
post = j[j.month >= '2022-01-01']
corr_post = round(float(post.initial_claims.corr(post.pct21)), 2)

# ---------- 4. weekly initial-claims forecast (seasonal profile x recent level) ----------
w = pd.read_csv(f'{D}/md_weekly_claims.csv', parse_dates=['week_ending']).set_index('week_ending').initial_claims
w = w[w.index >= '2022-06-01']  # post-COVID regime only
iso = w.index.isocalendar().week.astype(int)

def forecast(series, horizon=13, base_weeks=8):
    s = series.copy(); wk = s.index.isocalendar().week.astype(int)
    prof = s.groupby(wk.values).mean()              # average claims by ISO week
    prof = prof.reindex(range(1, 54)).interpolate().bfill().ffill()
    recent = s.iloc[-base_weeks:]
    level = recent.sum() / prof.reindex(recent.index.isocalendar().week.astype(int).values).sum()
    fut_idx = pd.date_range(s.index[-1] + pd.Timedelta(days=7), periods=horizon, freq='7D')
    fw = fut_idx.isocalendar().week.astype(int)
    f = pd.Series(prof.reindex(fw.values).values * level, index=fut_idx)
    resid = (s - prof.reindex(wk.values).values * level).std()
    return f, resid

# backtest: forecast last 13 observed weeks from data ending 13 weeks earlier
f_bt, _ = forecast(w.iloc[:-13])
act = w.iloc[-13:]
mape = float((abs(f_bt.values - act.values) / act.values).mean() * 100)
f, resid = forecast(w)
band = 1.28 * resid
fc = pd.DataFrame({'week_ending': f.index.strftime('%Y-%m-%d'), 'forecast': f.round(0).astype(int).values,
                   'low80': (f - band).clip(lower=0).round(0).astype(int).values, 'high80': (f + band).round(0).astype(int).values})
fc.to_csv(f'{D}/forecast_initial_claims_13wk.csv', index=False)
hist = [{'d': d.strftime('%Y-%m-%d'), 'ic': int(v)} for d, v in w.iloc[-52:].items()]

# ---------- 5. insured unemployment rate / continued weeks ----------
wk2 = pd.read_csv(f'{D}/md_weekly_claims.csv', parse_dates=['week_ending'])
wk2 = wk2[wk2.week_ending >= '2015-01-01'].copy()
wk2['m'] = wk2.week_ending.dt.to_period('M').dt.to_timestamp()
mm = wk2.groupby('m').agg(cw=('continued_weeks_claimed', 'mean'), iur=('insured_unemp_rate', 'mean')).round(2)
mm.index = mm.index.strftime('%Y-%m')

out = {
    'roll': {'months': list(roll.index), **{k: [float(v) for v in roll[k]] for k in roll.columns}},
    'heat': heat_out,
    'scatter': pts, 'corr': corr, 'corr_post': corr_post,
    'hist': hist, 'fc': fc.to_dict('records'), 'mape': round(mape, 1), 'resid': round(float(resid), 0),
    'iur': {'months': list(mm.index), 'cw': [float(v) for v in mm.cw], 'iur': [float(v) for v in mm.iur]},
    'last12': {'total': int(md.tail(12).total.sum()), 'w21': int(md.tail(12).w21.sum())},
}
json.dump(out, open(f'{D}/analytics.json', 'w'))
print('corr (ex-COVID) =', corr, '| corr 2022+ =', corr_post, '| forecast backtest MAPE =', round(mape, 1), '%')
print(fc.to_string())
print(roll.tail(1).to_string())
