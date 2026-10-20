"""State maps of first-payment timeliness (US DOL ETA 9050): where does Maryland stand, and who has recovered?
Map 1: on-time rate (paid within 21 days), last 12 months, by state.
Map 2: change vs 2019 (pre-pandemic) in percentage points.
Outputs: data/state_map_data.csv and maps.html (interactive, Plotly). Static PNGs are screenshots of maps.html
(see README); the base map shapes load from Plotly's CDN, so open maps.html with an internet connection."""
import pandas as pd, numpy as np, os
import plotly.graph_objects as go

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, '..', 'raw'); D = os.path.join(HERE, 'data')

t = pd.read_csv(f'{RAW}/ar9050.csv')
t['date'] = pd.to_datetime(t.rptdate)
g = lambda i: t[f'c{4*i+1}']
t['total'] = g(0) + g(1)                     # pair 0 = all first payments
t['w21'] = sum(g(i) for i in range(2, 8))    # pairs 1-3 = 0-7, 8-14, 15-21 days
last = t.date.max()
cur = t[t.date > last - pd.DateOffset(months=12)].groupby('st')[['w21', 'total']].sum()
pre = t[t.date.dt.year == 2019].groupby('st')[['w21', 'total']].sum()
df = pd.DataFrame({'now': cur.w21 / cur.total * 100, 'pre2019': pre.w21 / pre.total * 100, 'payments': cur.total})
df['change'] = df.now - df.pre2019
df['rank'] = df.now.rank(ascending=False, method='min').astype(int)
df = df.round(1).reset_index().rename(columns={'st': 'state'})
df.to_csv(f'{D}/state_map_data.csv', index=False)
m = df[~df.state.isin(['PR', 'VI'])].copy()          # plotly's US map has the 50 states + DC
print(m[m.state.isin(['MD', 'VA', 'PA', 'DE', 'WV', 'DC'])].to_string(index=False))
print('recovered to within 2 pts of 2019:', int((m.change > -2).sum()), 'of', len(m))

def hover(r):
    return (f"<b>{r.state}</b><br>On-time (last 12 mo): {r.now}%<br>2019: {r.pre2019}%<br>Change: {r.change:+.1f} pts"
            f"<br>Rank: {r['rank']} of {len(df)}<br>First payments: {int(r.payments):,}")
m['hover'] = m.apply(hover, axis=1)
FONT = dict(family='Segoe UI, Arial, sans-serif', color='#14213d')

def outline(fig, locs, color='#14213d'):
    fig.add_trace(go.Choropleth(locations=locs, z=[1] * len(locs), locationmode='USA-states', showscale=False,
                                colorscale=[[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']], marker=dict(line=dict(color=color, width=3)),
                                hoverinfo='skip'))

def base(fig, title, sub):
    fig.update_layout(title=dict(text=f'<b>{title}</b><br><span style="font-size:13px;color:#5c6b7a">{sub}</span>', x=0.01, y=0.96),
                      geo=dict(scope='usa', projection=dict(type='albers usa'), showlakes=False, bgcolor='rgba(0,0,0,0)'),
                      margin=dict(l=10, r=10, t=80, b=10), font=FONT, paper_bgcolor='white', height=560, width=980)

# ---- Map 1: current on-time rate
f1 = go.Figure(go.Choropleth(locations=m.state, z=m.now, locationmode='USA-states', text=m.hover, hoverinfo='text',
                             colorscale=[[0, '#b2182b'], [0.35, '#ef8a62'], [0.6, '#fddbc7'], [0.8, '#92c5de'], [1, '#2166ac']],
                             zmin=50, zmax=100, marker=dict(line=dict(color='white', width=0.8)),
                             colorbar=dict(title='% paid<br>within 21 days', ticksuffix='%', len=0.7)))
outline(f1, ['MD'])
base(f1, 'Where does Maryland stand? On-time first payments by state',
     f'Share of first UI payments made within 21 days, 12 months to {last:%b %Y}. Maryland outlined. Federal standard: 87%.')
md = m[m.state == 'MD'].iloc[0]
f1.add_annotation(x=0.99, y=0.97, xref='paper', yref='paper', showarrow=False, align='right', font=dict(size=13), xanchor='right', yanchor='top',
                  text=f"<b>Maryland: {md.now}%</b>, rank {md['rank']} of {len(df)}<br>{int((m.now >= 87).sum())} of {len(m)} states meet the 87% standard")

# ---- Map 2: change since 2019
lim = float(np.ceil(m.change.abs().quantile(0.95) / 5) * 5)
f2 = go.Figure(go.Choropleth(locations=m.state, z=m.change, locationmode='USA-states', text=m.hover, hoverinfo='text',
                             colorscale='RdBu', zmin=-lim, zmax=lim, zmid=0, marker=dict(line=dict(color='white', width=0.8)),
                             colorbar=dict(title='Change vs 2019<br>(pts)', len=0.7)))
outline(f2, ['MD'])
base(f2, 'Who has recovered? Change in on-time rate since 2019',
     f'Percentage-point change: last 12 months to {last:%b %Y} vs calendar 2019. Blue = better than 2019, red = still behind. Maryland outlined.')
f2.add_annotation(x=0.99, y=0.97, xref='paper', yref='paper', showarrow=False, align='right', font=dict(size=13), xanchor='right', yanchor='top',
                  text=f"<b>Maryland: {md.change:+.1f} pts</b> vs 2019<br>{int((m.change > -2).sum())} of {len(m)} states are within 2 pts of 2019")


# ---- Map 3: Maryland and neighbors (zoom)
nb = m[m.state.isin(['MD', 'VA', 'WV', 'PA', 'DE', 'DC'])].copy()
cent = {'MD': (37.75, -74.6), 'VA': (37.5, -78.9), 'WV': (38.65, -80.6), 'PA': (40.95, -77.8), 'DE': (39.35, -74.4), 'DC': (37.8, -77.0)}
anchor = {'DE': (39.3, -75.5), 'DC': (38.9, -77.02), 'MD': (38.3, -75.75)}       # label connector start points (state too small to hold its label)
nb['lat'] = nb.state.map(lambda x: cent[x][0]); nb['lon'] = nb.state.map(lambda x: cent[x][1])
f3 = go.Figure(go.Choropleth(locations=nb.state, z=nb.now, locationmode='USA-states', text=nb.hover, hoverinfo='text',
                             colorscale=f1.data[0].colorscale, zmin=50, zmax=100, marker=dict(line=dict(color='white', width=1.5)),
                             colorbar=dict(title='% paid<br>within 21 days', ticksuffix='%', len=0.7)))
f3.add_trace(go.Scattergeo(lat=nb.lat, lon=nb.lon, mode='text', hoverinfo='skip', showlegend=False, textfont=dict(size=13, color='#14213d'),
                           textposition=['middle right' if x in anchor else 'middle center' for x in nb.state],
                           text=[f"<b>{r.state}</b><br>{r.now}%<br>({r.change:+.1f} vs 2019)" for r in nb.itertuples()]))
for st_, (alat, alon) in anchor.items():
    f3.add_trace(go.Scattergeo(lat=[alat, cent[st_][0]], lon=[alon, cent[st_][1]], mode='lines', line=dict(color='#14213d', width=1), hoverinfo='skip', showlegend=False))
outline(f3, ['MD'])
f3.update_layout(title=dict(text='<b>Maryland and its neighbors</b><br><span style="font-size:13px;color:#5c6b7a">On-time rate, last 12 months (change vs 2019 in brackets). '
                            'Maryland outlined; MD, DC and DE labels are offset with a line.</span>', x=0.01, y=0.96),
                 margin=dict(l=10, r=10, t=80, b=10), font=FONT, paper_bgcolor='white', height=520, width=980)
f3.update_geos(scope='world', projection_type='mercator', lonaxis_range=[-83.4, -71.6], lataxis_range=[36.2, 42.2], visible=False, showlakes=False, bgcolor='rgba(0,0,0,0)')

cfg = dict(displayModeBar=False, responsive=True)
page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Maryland UI Maps</title><style>body{margin:0;background:#f6f7f9;font:15px/1.5 system-ui,Segoe UI,sans-serif;color:#14213d}'
        '.wrap{max-width:1040px;margin:0 auto;padding:20px 16px 40px}h1{font-size:24px;margin:0 0 4px}p.sub{color:#5c6b7a;margin:0 0 14px}'
        '.card{background:#fff;border:1px solid #e3e7ec;border-radius:12px;padding:6px;margin-bottom:14px}.foot{color:#5c6b7a;font-size:12px}</style></head><body><div class="wrap">'
        '<h1>Maryland vs. the Nation: State Maps of UI Payment Timeliness</h1>'
        '<p class="sub">Hover a state for its numbers. Source: US DOL ETA 9050 (public), my calculation.</p>'
        f'<div class="card">{f1.to_html(full_html=False, include_plotlyjs="cdn", config=cfg, div_id="m1")}</div>'
        f'<div class="card">{f2.to_html(full_html=False, include_plotlyjs=False, config=cfg, div_id="m2")}</div>'
        f'<div class="card">{f3.to_html(full_html=False, include_plotlyjs=False, config=cfg, div_id="m3")}</div>'
        '<p class="foot">Timeliness = first payments within 21 days of the first compensable week / all first payments (intrastate + interstate). '
        'Puerto Rico and the Virgin Islands are in the data but not drawn. The base map loads from Plotly\'s CDN, so open this page online.</p></div></body></html>')
open(os.path.join(HERE, 'maps.html'), 'w', encoding='utf-8').write(page)
print('wrote maps.html', len(page) // 1024, 'KB')
