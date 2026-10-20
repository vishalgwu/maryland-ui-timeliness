import pandas as pd, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, 'data')
md = pd.read_csv(f'{D}/md_first_payment_timeliness_monthly.csv')
st = pd.read_csv(f'{D}/state_comparison_trailing12m.csv')
wk = pd.read_csv(f'{D}/md_weekly_claims.csv', parse_dates=['week_ending'])
bd = pd.read_csv(f'{D}/md_delay_bands_trailing12m.csv')
wk = wk[wk.week_ending >= '2019-01-01']
tail = bd.iloc[6:]
bands = bd.iloc[:6].to_dict('records') + [{'days': '43+', 'payments': int(tail.payments.sum()), 'pct': round(float(tail.pct.sum()), 1)}]
data = {
    'monthly': md[md.month >= '2015-01-01'][['month', 'total', 'w21', 'pct21']].assign(month=lambda d: d.month.str[:7]).to_dict('records'),
    'states': st[['st', 'pct21', 'rank', 'total']].to_dict('records'),
    'weekly': [{'d': r.week_ending.strftime('%Y-%m-%d'), 'ic': int(r.initial_claims)} for r in wk.itertuples()],
    'bands': bands,
}
html = open(os.path.join(HERE, 'dashboard_template.html'), encoding='utf-8').read()
html = html.replace('/*CHARTJS*/', open(os.path.join(HERE, 'chart.umd.min.js'), encoding='utf-8').read())
html = html.replace('/*DATA*/', json.dumps(data))
open(os.path.join(HERE, 'dashboard.html'), 'w', encoding='utf-8').write(html)
print('ok', len(html) // 1024, 'KB')
