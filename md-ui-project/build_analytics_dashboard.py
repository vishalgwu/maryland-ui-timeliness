import pandas as pd, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, 'data')
a = json.load(open(f'{D}/analytics.json'))
j = pd.read_csv(f'{D}/md_workload_vs_timeliness.csv', parse_dates=['month'])
r = j[j.month >= '2023-01-01']
a['late_mean'] = float(r.late_payments.mean())
a['late_corr'] = round(float(r.late_payments.corr(r.initial_claims)), 2)
a['late_series'] = [{'m': m.strftime('%Y-%m'), 'v': int(v)} for m, v in zip(j[j.month >= '2021-07-01'].month, j[j.month >= '2021-07-01'].late_payments)]
html = open(os.path.join(HERE, 'analytics_template.html'), encoding='utf-8').read()
html = html.replace('/*CHARTJS*/', open(os.path.join(HERE, 'chart.umd.min.js'), encoding='utf-8').read())
html = html.replace('/*DATA*/', json.dumps(a))
open(os.path.join(HERE, 'analytics_dashboard.html'), 'w', encoding='utf-8').write(html)
print('ok', len(html) // 1024, 'KB')
