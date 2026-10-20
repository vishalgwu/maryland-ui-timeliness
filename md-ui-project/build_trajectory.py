"""Recovery-trajectory analysis: at the post-2022 pace of improvement, when would Maryland reach the 87% standard?
Fits a linear trend to the rolling 12-month 21-day rate since Jan 2023 and projects it forward with a bootstrap-style
range from the fit's slope uncertainty. Outputs data/recovery_trajectory.csv and docs/images/recovery_trajectory.png"""
import pandas as pd, numpy as np, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, 'data')
IMG = os.path.join(HERE, '..', 'docs', 'images')
os.makedirs(IMG, exist_ok=True)

r = pd.read_csv(f'{D}/rolling12m_21day_peers.csv', parse_dates=['month']).set_index('month')
fit = r.loc['2023-01-01':, 'MD']
x = np.arange(len(fit))
slope, icpt = np.polyfit(x, fit.values, 1)            # points per month
resid = fit.values - (slope * x + icpt)
se = resid.std(ddof=2) / (x.std() * np.sqrt(len(x)))  # slope standard error (ignores autocorrelation: indicative only)
TARGET = 87.0
cur = fit.iloc[-1]

def months_to(s):
    return np.inf if s <= 0 else (TARGET - cur) / s

central, fast, slow = months_to(slope), months_to(slope + 1.28 * se), months_to(max(slope - 1.28 * se, 1e-9))
print(f'slope = {slope*12:.2f} pts/yr (se {se*12:.2f}); current {cur:.1f}%; months to 87%: central {central:.0f}, '
      f'optimistic {fast:.0f}, pessimistic {slow:.0f}')

horizon = int(min(max(central * 1.3, 24), 240))
fut = pd.date_range(fit.index[-1] + pd.DateOffset(months=1), periods=horizon, freq='MS')
k = np.arange(1, horizon + 1)
proj = pd.DataFrame({'month': fut, 'central': cur + slope * k, 'optimistic': cur + (slope + 1.28 * se) * k,
                     'pessimistic': cur + (slope - 1.28 * se) * k}).round(2)
proj.to_csv(f'{D}/recovery_trajectory.csv', index=False)
reach = lambda m: (fit.index[-1] + pd.DateOffset(months=int(np.ceil(m)))).strftime('%b %Y') if np.isfinite(m) else 'never'
print('central ETA', reach(central), '| optimistic', reach(fast), '| pessimistic', reach(slow))

fig, ax = plt.subplots(figsize=(11, 5), dpi=150)
ax.plot(r.index, r.MD, color='#c8102e', lw=2.5, label='Maryland (actual, rolling 12-mo)')
ax.plot(r.index, r['US pool'], color='#6b7a89', lw=1.6, ls='--', label='National pool')
ax.plot(proj.month, proj.central.clip(upper=100), color='#1d4e89', lw=2, ls=':', label=f'Trend at +{slope*12:.1f} pts/yr')
ax.fill_between(proj.month, proj.pessimistic.clip(upper=100), proj.optimistic.clip(upper=100), color='#1d4e89', alpha=.15, label='80% slope range')
ax.axhline(TARGET, color='#2a9d6f', lw=1.5)
ax.text(r.index[2], TARGET + .8, '87% federal standard', color='#2a9d6f', fontsize=9)
ax.set_ylim(10, 100); ax.set_ylabel('% first payments within 21 days')
ax.set_title(f'Recovery trajectory: at the current pace Maryland reaches 87% around {reach(central)}', loc='left', fontweight='bold')
ax.legend(loc='lower right', frameon=False, fontsize=9)
for s in ('top', 'right'): ax.spines[s].set_visible(False)
fig.tight_layout(); fig.savefig(f'{IMG}/recovery_trajectory.png'); print('saved png')
