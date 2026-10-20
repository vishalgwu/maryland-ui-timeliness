/* Maryland UI Pulse: interactive analytics app. Vanilla JS + d3 (map) + Chart.js (charts). No build step. */
(() => {
const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
const fmt = n => Math.round(n).toLocaleString('en-US');
const COL = { pink: '#ff4fa3', lime: '#c6ff3d', violet: '#7c5cff', cyan: '#36e2ff', amber: '#ffb23f', mute: '#a7a6c0', line: 'rgba(255,255,255,.09)', coral: '#ff8f5a', mint: '#8affc1' };
const SHOT = /[?&]shot/.test(location.search) || !('IntersectionObserver' in window); // ?shot = no animations (for screenshots)
const FIPS = { '01': 'AL', '02': 'AK', '04': 'AZ', '05': 'AR', '06': 'CA', '08': 'CO', '09': 'CT', '10': 'DE', '11': 'DC', '12': 'FL', '13': 'GA', '15': 'HI', '16': 'ID', '17': 'IL', '18': 'IN', '19': 'IA', '20': 'KS', '21': 'KY', '22': 'LA', '23': 'ME', '24': 'MD', '25': 'MA', '26': 'MI', '27': 'MN', '28': 'MS', '29': 'MO', '30': 'MT', '31': 'NE', '32': 'NV', '33': 'NH', '34': 'NJ', '35': 'NM', '36': 'NY', '37': 'NC', '38': 'ND', '39': 'OH', '40': 'OK', '41': 'OR', '42': 'PA', '44': 'RI', '45': 'SC', '46': 'SD', '47': 'TN', '48': 'TX', '49': 'UT', '50': 'VT', '51': 'VA', '53': 'WA', '54': 'WV', '55': 'WI', '56': 'WY' };

Promise.all([fetch('data/site.json').then(r => r.json()), fetch('vendor/states-albers-10m.json').then(r => r.json())])
  .then(([S, topo]) => init(S, topo)).catch(e => { console.error(e); document.body.insertAdjacentHTML('afterbegin', '<p style="padding:20px;color:#ff4fa3">Could not load data. Serve this folder over http (not file://).</p>'); });

function init(S, topo) {
  if (SHOT) document.body.classList.add('shot');
  const K = S.kpi, byAbbr = Object.fromEntries(S.states.map(s => [s.st, s])), MD = byAbbr.MD;
  Chart.defaults.color = COL.mute; Chart.defaults.borderColor = COL.line; Chart.defaults.font.family = "'Inter',system-ui,sans-serif";
  Chart.defaults.plugins.legend.labels.usePointStyle = true; Chart.defaults.plugins.legend.labels.boxWidth = 8;
  Chart.defaults.animation.duration = SHOT ? 0 : 900;
  const charts = {};
  const mkChart = (key, canvas, cfg) => { charts[key]?.destroy(); charts[key] = new Chart(canvas, cfg); return charts[key]; };
  const monthName = m => new Date(m + '-15').toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
  const sparseTicks = { maxTicksLimit: 8, maxRotation: 0 };

  /* ---------- hero, ticker, counters ---------- */
  $('#asof').textContent = monthName(K.asof);
  $('#heroPct').textContent = K.now;
  $('#kMedian').textContent = K.median;
  const gauge = () => {
    const R = 92, c = 110, a = (87 / 100) * 2 * Math.PI - Math.PI / 2;
    const x1 = c + (R - 14) * Math.cos(a), y1 = c + (R - 14) * Math.sin(a), x2 = c + (R + 14) * Math.cos(a), y2 = c + (R + 14) * Math.sin(a);
    $('#gMark').innerHTML = `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" class="g-mark"/><text x="${c + (R + 28) * Math.cos(a)}" y="${c + (R + 28) * Math.sin(a) + 4}" class="g-lbl" text-anchor="middle">87%</text>`;
    if (SHOT) $('#gFill').style.strokeDasharray = `${K.now} 100`; else requestAnimationFrame(() => setTimeout(() => { $('#gFill').style.transition = 'stroke-dasharray 1.8s cubic-bezier(.2,.8,.2,1)'; $('#gFill').style.strokeDasharray = `${K.now} 100`; }, 250));
    animateNum($('#gNum'), K.now, 1, 1800);
  };
  gauge();
  const items = [`<b>${K.now}%</b> of first payments within 21 days`, `federal standard <b>87%</b>`, `<b>#${K.rank}</b> of ${K.n} jurisdictions`, `<b>${fmt(K.late12)}</b> late first payments in 12 months`,
    `<b>${K.meet}</b> of 51 states meet the standard`, `only <b>${K.recovered}</b> states back within 2 pts of 2019`, `<b>${K.tail70}%</b> wait 70+ days`, `late payments ≈ <b>${fmt(K.late_mean)}</b>/month whatever the volume`];
  $('#ticker').innerHTML = [...items, ...items].map(t => `<span>${t}</span>`).join('');

  function animateNum(el, to, dec = 0, dur = 1400, prefix = '') {
    if (SHOT) { el.textContent = prefix + to.toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec }); return; }
    const t0 = performance.now(); const step = t => { const p = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - p, 3); el.textContent = prefix + (to * e).toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec }); if (p < 1) requestAnimationFrame(step); }; requestAnimationFrame(step);
  }
  const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); e.target.querySelectorAll?.('[data-count]').forEach(n => { if (!n.dataset.done) { n.dataset.done = 1; animateNum(n, +n.dataset.count, +(n.dataset.dec || 0), 1500, n.dataset.prefix || ''); } }); io.unobserve(e.target); } }), { threshold: .12 });
  $$('.reveal').forEach(n => { if (SHOT) { n.classList.add('in'); n.querySelectorAll('[data-count]').forEach(c => animateNum(c, +c.dataset.count, +(c.dataset.dec || 0), 0, c.dataset.prefix || '')); } else io.observe(n); });

  /* ---------- MAP ---------- */
  const SCALES = {
    now: { fn: d3.scaleLinear().domain([45, 65, 80, 87, 97]).range(['#ff2e7e', '#ff7a3d', '#ffd23f', '#a8f04a', '#2df5c0']).clamp(true), val: s => s.now, lab: v => v.toFixed(1) + '%', lo: '45%', hi: '97%', note: 'Federal standard: 87% within 21 days' },
    change: { fn: d3.scaleLinear().domain([-25, -10, -2, 2, 10]).range(['#ff2e7e', '#ff8f5a', '#4a4964', '#58e0d0', '#36e2ff']).clamp(true), val: s => s.change, lab: v => (v > 0 ? '+' : '') + v.toFixed(1) + ' pts', lo: '-25 pts', hi: '+10 pts', note: 'Last 12 months vs calendar 2019' },
    rank: { fn: d3.scaleLinear().domain([1, 27, 53]).range(['#2df5c0', '#ffd23f', '#ff2e7e']).clamp(true), val: s => s.rank, lab: v => '#' + v, lo: '#1 best', hi: '#53', note: 'Rank by on-time rate' }
  };
  let metric = 'now', selected = 'MD';
  const svg = d3.select('#usmap'), g = svg.append('g'), path = d3.geoPath();
  const feats = topojson.feature(topo, topo.objects.states).features.map(f => ({ ...f, abbr: FIPS[String(f.id).padStart(2, '0')] })).filter(f => f.abbr);
  const colorOf = s => s ? SCALES[metric].fn(SCALES[metric].val(s)) : '#2a2a3d';
  const stPaths = g.selectAll('path.st').data(feats).join('path').attr('class', 'st').attr('d', path).style('vector-effect', 'non-scaling-stroke')
    .attr('fill', f => colorOf(byAbbr[f.abbr]));
  const mdFeat = feats.find(f => f.abbr === 'MD'), dcFeat = feats.find(f => f.abbr === 'DC');
  g.append('path').attr('class', 'md-ring').attr('d', path(mdFeat)).style('vector-effect', 'non-scaling-stroke');
  const mdC = path.centroid(mdFeat);
  g.append('text').attr('class', 'lab').attr('x', mdC[0] + 34).attr('y', mdC[1] + 26).text('MARYLAND');
  g.append('line').attr('x1', mdC[0] + 6).attr('y1', mdC[1] + 4).attr('x2', mdC[0] + 32).attr('y2', mdC[1] + 22).attr('stroke', '#fff').attr('stroke-width', 1).style('vector-effect', 'non-scaling-stroke');
  const dcC = dcFeat ? path.centroid(dcFeat) : mdC;
  const dcDot = g.append('circle').attr('class', 'dc').attr('cx', dcC[0]).attr('cy', dcC[1]).attr('r', 4.2).attr('fill', colorOf(byAbbr.DC));
  const tip = $('#tip'), wrap = $('.map-wrap');
  function tipHtml(s) { if (!s) return ''; const d = s.st === 'MD' ? null : s.now - MD.now; return `<b>${s.name}</b><div class="r"><span>On-time</span><span>${s.now}%</span></div><div class="r"><span>2019</span><span>${s.pre}%</span></div><div class="r"><span>Change</span><span>${s.change > 0 ? '+' : ''}${s.change} pts</span></div><div class="r"><span>Rank</span><span>#${s.rank}/${K.n}</span></div>${d == null ? '' : `<div class="r"><span>vs Maryland</span><span>${d > 0 ? '+' : ''}${d.toFixed(1)} pts</span></div>`}`; }
  function bindHover(sel, getAbbr) {
    sel.on('mousemove', (e, d) => { const s = byAbbr[getAbbr(d)]; if (!s) return; tip.innerHTML = tipHtml(s); tip.classList.add('on'); const r = wrap.getBoundingClientRect(); let x = e.clientX - r.left + 16, y = e.clientY - r.top + 14; if (x > r.width - 200) x -= 220; tip.style.left = x + 'px'; tip.style.top = y + 'px'; })
      .on('mouseleave', () => tip.classList.remove('on')).on('click', (e, d) => select(getAbbr(d)));
  }
  bindHover(stPaths, f => f.abbr); bindHover(dcDot, () => 'DC');
  const zoom = d3.zoom().scaleExtent([1, 10]).filter(e => e.type !== 'wheel' && !e.button).on('zoom', e => { g.attr('transform', e.transform); g.select('text.lab').style('font-size', 11 / e.transform.k + 'px').style('stroke-width', 3 / e.transform.k + 'px'); dcDot.attr('r', 4.2 / Math.sqrt(e.transform.k)); });
  svg.call(zoom);
  const home = d3.zoomIdentity;
  $('#zoomReset').onclick = () => svg.transition().duration(800).call(zoom.transform, home);
  $('#zoomMA').onclick = () => {
    const sel = feats.filter(f => ['MD', 'VA', 'WV', 'PA', 'DE', 'DC', 'NJ', 'NC'].includes(f.abbr)), bs = sel.map(f => path.bounds(f));
    const x0 = d3.min(bs, b => b[0][0]), y0 = d3.min(bs, b => b[0][1]), x1 = d3.max(bs, b => b[1][0]), y1 = d3.max(bs, b => b[1][1]);
    const k = Math.min(10, 0.86 / Math.max((x1 - x0) / 975, (y1 - y0) / 610));
    svg.transition().duration(1000).call(zoom.transform, d3.zoomIdentity.translate(975 / 2 - k * (x0 + x1) / 2, 610 / 2 - k * (y0 + y1) / 2).scale(k));
  };
  function recolor() {
    stPaths.transition().duration(600).attr('fill', f => colorOf(byAbbr[f.abbr])); dcDot.transition().duration(600).attr('fill', colorOf(byAbbr.DC));
    const sc = SCALES[metric], d = sc.fn.domain(), grad = d3.range(0, 1.01, .1).map(t => sc.fn(d[0] + t * (d[d.length - 1] - d[0]))).join(',');
    $('#legBar').style.background = `linear-gradient(90deg,${grad})`; $('#legLo').textContent = sc.lo; $('#legHi').textContent = sc.hi; $('#legNote').textContent = sc.note;
  }
  $$('#metricSeg button').forEach(b => b.onclick = () => { $$('#metricSeg button').forEach(x => x.classList.toggle('on', x === b)); metric = b.dataset.m; recolor(); renderSel(); });
  // state picker + lists
  const sorted = [...S.states].sort((a, b) => a.name.localeCompare(b.name));
  $('#stateSel').innerHTML = sorted.map(s => `<option value="${s.st}">${s.name}</option>`).join('');
  $('#stateSel').onchange = e => select(e.target.value);
  const byRank = [...S.states].sort((a, b) => a.rank - b.rank);
  const li = s => `<li data-st="${s.st}"><span>${s.st}</span><span>${s.now}%</span></li>`;
  $('#topList').innerHTML = byRank.slice(0, 5).map(li).join(''); $('#botList').innerHTML = byRank.slice(-5).reverse().map(li).join('');
  $$('.lists li').forEach(l => l.onclick = () => select(l.dataset.st));
  // selected panel + sparkline
  function renderSel() {
    const s = byAbbr[selected], sc = SCALES[metric], d = s.st === 'MD' ? null : s.now - MD.now;
    $('#stateSel').value = s.st;
    $('#selPanel').innerHTML = `<h3>${s.name}</h3><div class="big" style="color:${colorOf(s)}">${metric === 'rank' ? '#' + s.rank : metric === 'change' ? (s.change > 0 ? '+' : '') + s.change + ' pts' : s.now + '%'}</div>
      <div class="row"><span>On-time (12 mo)</span><b>${s.now}%</b></div><div class="row"><span>2019</span><b>${s.pre}%</b></div><div class="row"><span>Rank</span><b>#${s.rank} of ${K.n}</b></div><div class="row"><span>First payments</span><b>${fmt(s.payments)}</b></div>
      ${d == null ? '<div class="row"><span>vs US pool</span><b class="' + (MD.now - K.us_pool < 0 ? 'neg' : 'pos') + '">' + (MD.now - K.us_pool).toFixed(1) + ' pts</b></div>' : `<div class="row"><span>vs Maryland</span><b class="${d >= 0 ? 'pos' : 'neg'}">${d > 0 ? '+' : ''}${d.toFixed(1)} pts</b></div>`}`;
    stPaths.classed('sel', f => f.abbr === selected).classed('dim', false);
    const from = S.months.indexOf('2019-01'), labs = S.months.slice(from), other = s.st === 'MD' ? 'US' : s.st;
    const ds = [{ label: 'Maryland', data: S.series.MD.slice(from), borderColor: COL.pink, borderWidth: 2.4, pointRadius: 0, tension: .3 }, { label: s.st === 'MD' ? 'US pool' : s.name, data: S.series[other].slice(from), borderColor: COL.lime, borderWidth: 2, pointRadius: 0, tension: .3, borderDash: s.st === 'MD' ? [4, 4] : [] }];
    mkChart('spark', $('#sparkSel'), { type: 'line', data: { labels: labs, datasets: ds }, options: { maintainAspectRatio: true, aspectRatio: 2.2, plugins: { legend: { labels: { font: { size: 11 } } }, tooltip: { enabled: false } }, scales: { x: { display: false }, y: { min: 20, max: 100, ticks: { callback: v => v + '%', font: { size: 10 }, maxTicksLimit: 4 }, grid: { color: COL.line } } } } });
  }
  function select(a) { if (!byAbbr[a]) return; selected = a; renderSel(); }
  recolor(); renderSel();

  /* ---------- TRENDS ---------- */
  const PAL = { MD: COL.pink, US: '#ffffff', VA: COL.cyan, PA: COL.violet, DC: COL.amber, WV: COL.coral, DE: COL.mint };
  const extra = [COL.lime, '#ff6b6b', '#6bc5ff', '#d58bff', '#ffd86b'];
  let active = new Set(['US', 'VA', 'PA']), fromM = '2019-01'; const chipOrder = ['VA', 'PA', 'DC', 'WV', 'DE', 'US'];
  const colFor = k => PAL[k] || (PAL[k] = extra[Object.keys(PAL).length % extra.length]);
  function chips() {
    $('#trendChips').innerHTML = `<span class="chip fixed"><i style="background:${COL.pink}"></i>Maryland</span>` + [...chipOrder, ...[...active].filter(k => !chipOrder.includes(k))].map(k => `<button class="chip ${active.has(k) ? '' : 'off'}" data-k="${k}"><i style="background:${colFor(k)}"></i>${k === 'US' ? 'US pool' : byAbbr[k].name}</button>`).join('') +
      `<select id="addSt"><option value="">+ add a state</option>${sorted.filter(s => s.st !== 'MD' && !chipOrder.includes(s.st)).map(s => `<option value="${s.st}">${s.name}</option>`).join('')}</select>`;
    $$('#trendChips .chip[data-k]').forEach(b => b.onclick = () => { active.has(b.dataset.k) ? active.delete(b.dataset.k) : active.add(b.dataset.k); chips(); trend(); });
    $('#addSt').onchange = e => { if (e.target.value) { active.add(e.target.value); chips(); trend(); } };
  }
  function trend() {
    const i = S.months.indexOf(fromM), labs = S.months.slice(i);
    const ds = [{ label: 'Maryland', data: S.series.MD.slice(i), borderColor: COL.pink, borderWidth: 3.4, pointRadius: 0, tension: .3, order: 0 }];
    [...active].forEach(k => ds.push({ label: k === 'US' ? 'US pool' : byAbbr[k].name, data: S.series[k].slice(i), borderColor: colFor(k), borderWidth: 1.8, pointRadius: 0, tension: .3, borderDash: k === 'US' ? [6, 5] : [], order: 1 }));
    ds.push({ label: '87% standard', data: labs.map(() => 87), borderColor: COL.lime, borderWidth: 1.4, borderDash: [3, 5], pointRadius: 0, order: 2 });
    mkChart('trend', $('#trendChart'), { type: 'line', data: { labels: labs, datasets: ds }, options: { maintainAspectRatio: false, interaction: { mode: 'index', intersect: false }, plugins: { legend: { display: false }, tooltip: { backgroundColor: 'rgba(14,14,26,.95)', borderColor: COL.line, borderWidth: 1, padding: 12, callbacks: { title: i => monthName(i[0].label), label: c => ` ${c.dataset.label}: ${c.parsed.y}%` } } }, scales: { y: { min: 20, max: 100, ticks: { callback: v => v + '%' } }, x: { ticks: { ...sparseTicks, callback: function (v) { return this.getLabelForValue(v).slice(0, 4); } }, grid: { display: false } } } } });
  }
  $$('#rangeSeg button').forEach(b => b.onclick = () => { $$('#rangeSeg button').forEach(x => x.classList.toggle('on', x === b)); fromM = b.dataset.from; trend(); });
  chips(); trend();
  const A = S.annual;
  mkChart('annual', $('#annualChart'), { type: 'line', data: { labels: A.years, datasets: [{ label: 'Maryland', data: A.MD, borderColor: COL.pink, backgroundColor: COL.pink, borderWidth: 3.4, pointRadius: 4, tension: .25 }, { label: 'US average', data: A.US, borderColor: '#fff', backgroundColor: '#fff', borderWidth: 2, pointRadius: 3, borderDash: [5, 4], tension: .25 }, { label: '87% standard', data: A.years.map(() => 87), borderColor: COL.lime, borderDash: [3, 5], borderWidth: 1.4, pointRadius: 0 }] }, options: { maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } }, scales: { y: { min: 30, max: 100, ticks: { callback: v => v + '%' } }, x: { grid: { display: false } } } } });

  const falls = [...S.states].filter(s => !['PR', 'VI'].includes(s.st)).sort((a, b) => a.change - b.change).slice(0, 6), maxF = Math.abs(falls[0].change);
  $('#falls').innerHTML = falls.map(s => `<div class="${s.st === 'MD' ? 'md' : ''}"><span>${s.st}</span><i style="width:${Math.abs(s.change) / maxF * 100}%"></i><b>${s.change}</b></div>`).join('');

  /* ---------- DELAY ---------- */
  const bs = S.bands, head = bs.slice(0, 6), tail = bs.slice(6), bandData = [...head.map(b => ({ l: b.days, v: b.pct, n: b.payments })), { l: '43+', v: +tail.reduce((a, b) => a + b.pct, 0).toFixed(1), n: tail.reduce((a, b) => a + b.payments, 0) }];
  mkChart('bands', $('#bandChart'), { type: 'bar', data: { labels: bandData.map(b => b.l + ' d'), datasets: [{ data: bandData.map(b => b.v), borderRadius: 10, backgroundColor: bandData.map((b, i) => i < 3 ? COL.lime : i < 5 ? COL.amber : COL.pink) }] }, options: { maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => ` ${c.parsed.y}% (${fmt(bandData[c.dataIndex].n)} payments)` } } }, scales: { y: { ticks: { callback: v => v + '%' } }, x: { grid: { display: false } } } } });
  $('#corrTxt').textContent = `Correlation ${K.late_corr}: volume doesn't predict lateness.`;
  const sc = S.scatter;
  mkChart('scatter', $('#scatterChart'), { type: 'scatter', data: { datasets: [{ data: sc.map(p => ({ x: p.claims, y: p.late, m: p.m })), backgroundColor: COL.cyan + 'cc', borderColor: COL.cyan, pointRadius: 5, pointHoverRadius: 8 }, { type: 'line', data: [{ x: d3.min(sc, p => p.claims), y: K.late_mean }, { x: d3.max(sc, p => p.claims), y: K.late_mean }], borderColor: COL.pink, borderDash: [5, 4], pointRadius: 0, borderWidth: 2 }] }, options: { maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => c.raw.m ? ` ${monthName(c.raw.m)}: ${fmt(c.raw.x)} claims, ${fmt(c.raw.y)} late` : ` average ${fmt(K.late_mean)} late/month` } } }, scales: { x: { title: { display: true, text: 'initial claims in month' }, ticks: { callback: v => fmt(v / 1000) + 'k' }, grid: { color: COL.line } }, y: { title: { display: true, text: 'late payments' }, min: 0, ticks: { callback: v => fmt(v) } } } } });
  $('#mapeTxt').textContent = S.kpi.mape + '%';
  const H = S.hist, F = S.fc, labs = [...H.map(r => r.d), ...F.map(r => r.week_ending)], last = H[H.length - 1].ic, pad = a => [...Array(H.length - 1).fill(null), ...a];
  mkChart('fc', $('#fcChart'), { type: 'line', data: { labels: labs, datasets: [{ label: 'Actual', data: [...H.map(r => r.ic), ...Array(F.length).fill(null)], borderColor: COL.cyan, borderWidth: 2.2, pointRadius: 0, tension: .3 }, { label: 'Forecast', data: pad([last, ...F.map(r => r.forecast)]), borderColor: COL.pink, borderDash: [6, 4], borderWidth: 2.4, pointRadius: 0, tension: .3 }, { label: '80% band', data: pad([last, ...F.map(r => r.high80)]), borderColor: 'transparent', backgroundColor: COL.pink + '30', pointRadius: 0, fill: '+1', tension: .3 }, { label: 'low', data: pad([last, ...F.map(r => r.low80)]), borderColor: 'transparent', pointRadius: 0, tension: .3 }] }, options: { maintainAspectRatio: false, interaction: { mode: 'index', intersect: false }, plugins: { legend: { labels: { filter: i => i.text !== 'low' } } }, scales: { y: { min: 0, ticks: { callback: v => fmt(v) } }, x: { ticks: { maxTicksLimit: 6, maxRotation: 0, callback: function (v) { const l = this.getLabelForValue(v); return monthName(l.slice(0, 7)); } }, grid: { display: false } } } } });

  /* ---------- DEPARTMENT ---------- */
  const CH = [
    { t: 'ID fraud', c: 'Identity theft surged during the pandemic and keeps evolving. Before 2020 under 1% of claims were flagged; the share peaked at 35% in Q1 2023 and was 18% in Q4 2025.', r: ['TrueID and US Post Office identity verification', 'Fraud-finding tools (LexisNexis, Unified Fraud Response) check identity and IP address', 'Flags on changes to sensitive data such as bank accounts', 'A dedicated team manually reviews flagged employers'], a: 'Fraud review competes with honest claimants for the same staff. A queue dashboard (flag rate, review age, release rate) would show how much of the late tail is screening, and where false positives slow legitimate claims.' },
    { t: 'Funding', c: 'Federal administrative funding stayed flat while costs rose and no longer covers earned workload. The US Department of Labor rescinded $25 million in multi-year UI modernization grants.', r: ['FY26 budget bill allocates 0.15% of the taxable wage base to core operations, customer service, IT modernization, fraud prevention and reemployment services'], a: 'With limited money, targeting matters. Forecasting weekly claims (about 5.7% error in a backtest) lets managers match staffing to expected demand instead of staffing for the peak all year.' },
    { t: 'Customer support', c: 'During the pandemic in-person help ended and the call center was outsourced, costing nearly $300 million from FY21 to FY25.', r: ['State-staffed call center re-established in 2025 for under $9 million a year', 'In-person help reopened at Baltimore HQ and three American Job Centers, serving over 14,000 residents in 2025'], a: 'Track call-back wait, first-contact resolution and repeat-call drivers. Calls are a leading indicator of processing problems before they show up in the federal 21-day measure.' },
    { t: 'Technology', c: 'The BEACON claims system launched in 2020 with major technical problems that slowed claims, and the loss of federal funds has limited fixes.', r: ['UI website redesigned in September 2025 to help people file accurate, complete claims faster', 'Grant-funded work with Harvard and Stanford to streamline processes and find bottlenecks'], a: 'Bottleneck work needs stage timestamps (filed, identity verified, adjudicated, approved, paid). With those, process mining shows exactly where days are lost. That is the data I would ask for first.' }];
  const TL = [['2020', 'Collections paused', 'Claims jumped from about 161,000 in 2019 to 1.7 million in 2020 and $6.85 billion in benefits were paid in 2020-21. The department paused active overpayment collection and did not consistently resume until 2023.'], ['Nov 2021', 'Lawsuit', 'Maryland was sued over alleged due-process violations in its overpayment recovery process (Gorres et al. v. Robinson).'], ['Jan 2022', 'Settlement', 'The settlement required the department to stop collections and set up a process to notify claimants of appeal rights and the chance to seek a hardship waiver.'], ['Mar 2022', '$484M recovered', 'Maryland recovered $484 million from a financial institution, in previously frozen UI benefits.'], ['Sep 2023', 'Determinations restart', 'The department restarted issuing overpayment determinations for new claims.'], ['Jun 2025', '$520M recovered', 'Maryland recovered $520 million from a financial institution, in previously frozen UI benefits.'], ['Dec 2025', 'Retroactive process', 'A retroactive process began to pursue recovery of over $1 billion, with about 184,000 notices mailed and support for people who need to verify identity or report fraud. Part reflects overpayments in the January 2026 state audit, largely federal CARES Act money.']];
  let deptTab = 'ch';
  function dept() {
    const body = $('#deptBody'); ['dFraud', 'dClaims', 'dWages'].forEach(k => { charts[k]?.destroy(); delete charts[k]; });
    if (deptTab === 'ch') {
      body.innerHTML = `<div class="pills">${CH.map((c, i) => `<button class="chip" data-i="${i}">${c.t}</button>`).join('')}</div><div id="chBox"></div>`;
      const show = i => { $$('#deptBody .pills .chip').forEach((b, j) => b.style.background = i === j ? 'var(--ink)' : '', $$('#deptBody .pills .chip').forEach((b, j) => b.style.color = i === j ? '#0b0b12' : '')); const c = CH[i]; $('#chBox').innerHTML = `<div class="cols2"><div class="panel red"><h4>Challenge</h4><p>${c.c}</p></div><div class="panel green"><h4>Department response</h4><ul>${c.r.map(x => '<li>' + x + '</li>').join('')}</ul></div></div><div class="panel blue"><h4>Analyst angle</h4><p>${c.a}</p></div>`; };
      $$('#deptBody .pills .chip').forEach((b, i) => b.onclick = () => show(i)); show(0);
    } else if (deptTab === 'ov') {
      body.innerHTML = `<p class="note">Overpayments are benefits paid to people who were not eligible, including through identity theft. Click a milestone.</p><div class="tl-line">${TL.map((x, i) => `<button data-i="${i}"><b>${x[0]}</b><span>${x[1]}</span></button>`).join('')}</div><div class="panel blue" id="tlBox" style="margin-top:6px"></div>`;
      const show = i => { $$('#deptBody .tl-line button').forEach((b, j) => b.classList.toggle('on', i === j)); $('#tlBox').innerHTML = `<h4>${TL[i][0]}: ${TL[i][1]}</h4><p>${TL[i][2]}</p>`; };
      $$('#deptBody .tl-line button').forEach((b, i) => b.onclick = () => show(i)); show(0);
    } else {
      body.innerHTML = `<div class="num-grid"><div><h3>Fraud share vs on-time rate</h3><p class="note">Quarterly. Correlation ${S.fv_corr} (13 quarters): suggestive, not proof.</p><div class="box"><canvas id="cF"></canvas></div></div><div><h3>UI claims filed per quarter</h3><p class="note">Department-reported. Steady at ~35k.</p><div class="box"><canvas id="cC"></canvas></div></div><div><h3>Wages recovered for workers</h3><p class="note">Fiscal years (FY26 = first half).</p><div class="box"><canvas id="cW"></canvas></div></div></div>`;
      mkChart('dFraud', $('#cF'), { type: 'line', data: { labels: S.fv.map(r => r.q), datasets: [{ label: 'Fraud share (%)', data: S.fv.map(r => r.fraud), borderColor: COL.pink, borderWidth: 2.6, pointRadius: 3, tension: .25 }, { label: 'Paid within 21 days (%)', data: S.fv.map(r => r.timely), borderColor: COL.cyan, borderWidth: 2.6, pointRadius: 3, tension: .25 }] }, options: { maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } }, scales: { y: { min: 0, max: 100, ticks: { callback: v => v + '%' } }, x: { ticks: { maxRotation: 60, font: { size: 10 } }, grid: { display: false } } } } });
      mkChart('dClaims', $('#cC'), { type: 'bar', data: { labels: Object.keys(S.claims_q), datasets: [{ data: Object.values(S.claims_q), backgroundColor: COL.violet, borderRadius: 8 }] }, options: { maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => ' ' + fmt(c.parsed.y) + ' claims' } } }, scales: { y: { min: 0, ticks: { callback: v => fmt(v / 1000) + 'k' } }, x: { ticks: { maxRotation: 60, font: { size: 10 } }, grid: { display: false } } } } });
      mkChart('dWages', $('#cW'), { type: 'bar', data: { labels: Object.keys(S.wages), datasets: [{ data: Object.values(S.wages), backgroundColor: COL.lime, borderRadius: 8 }] }, options: { maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => ' $' + fmt(c.parsed.y) } } }, scales: { y: { ticks: { callback: v => '$' + (v / 1e6).toFixed(1) + 'M' } }, x: { ticks: { font: { size: 10 } }, grid: { display: false } } } } });
    }
  }
  $$('#deptTabs button').forEach(b => b.onclick = () => { $$('#deptTabs button').forEach(x => x.classList.toggle('on', x === b)); deptTab = b.dataset.t; dept(); });
  dept();

  /* ---------- WHAT-IF ---------- */
  const wi = () => { const t = +$('#tgt').value, extraP = Math.max(0, Math.round(t / 100 * K.total12 - K.ontime12)); $('#tgtV').textContent = t; $('#wiBig').textContent = '+' + fmt(extraP);
    $('#wiBar').style.width = Math.min(100, extraP / (0.95 * K.total12 - K.ontime12) * 100) + '%'; $('#wiMonth').textContent = `About ${fmt(extraP / 12)} more people paid within 21 days every month (${fmt(K.total12)} first payments in the last 12 months).`; };
  $('#tgt').oninput = wi; wi();

  /* ---------- chrome: nav highlight + cursor glow ---------- */
  const links = $$('.nav nav a'), secs = links.map(a => $(a.getAttribute('href')));
  const nio = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) links.forEach(a => a.classList.toggle('on', a.getAttribute('href') === '#' + e.target.id)); }), { rootMargin: '-45% 0px -50% 0px' });
  secs.forEach(s => s && nio.observe(s));
  const glow = $('#glow'); window.addEventListener('pointermove', e => { glow.style.opacity = 1; glow.style.left = e.clientX + 'px'; glow.style.top = e.clientY + 'px'; }, { passive: true });
}
})();
