"""Generates a Power BI Project (PBIP: TMDL semantic model + PBIR report) from the CSVs in md-ui-project/data.
Run:  python powerbi/build_powerbi.py   -> writes powerbi/MD-UI-Timeliness.pbip (+ .SemanticModel, .Report folders)
Open the .pbip in Power BI Desktop (free). If the data folder moved, edit the DataFolder parameter (Transform data)."""
import json, os, uuid, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..'))
DATA = os.path.join(ROOT, 'md-ui-project', 'data') + os.sep
NAME = 'MD-UI-Timeliness'
SM = os.path.join(HERE, f'{NAME}.SemanticModel')
RP = os.path.join(HERE, f'{NAME}.Report')
for d in (SM, RP):
    shutil.rmtree(d, ignore_errors=True)
guid = lambda: str(uuid.uuid4())

def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)

# ======================= semantic model =======================
CSV = 'Csv.Document(File.Contents(DataFolder & "{f}"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv])'

def m_simple(f, types, extra=''):
    ty = ', '.join('{"%s", %s}' % (c, t) for c, t in types)
    return (f'let\n\tSource = {CSV.format(f=f)},\n\tHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),\n'
            f'\tTyped = Table.TransformColumnTypes(Headers, {{{ty}}}, "en-US"){extra}\nin\n\t{"Final" if extra else "Typed"}')

I, N, T, D_ = 'Int64.Type', 'type number', 'type text', 'type date'
TABLES = {}   # name -> dict(columns=[(name,dtype,fmt,sort)], m=str, measures=[(name, dax, fmt)])

TABLES['Timeliness'] = dict(
    cols=[('month', 'dateTime', 'mmm yyyy'), ('total', 'int64', '#,0'), ('w14', 'int64', '#,0'), ('w21', 'int64', '#,0'),
          ('pct14', 'double', '0.0%'), ('pct21', 'double', '0.0%'), ('benchmark_pct', 'double', '0.0%'), ('late_payments', 'int64', '#,0')],
    m=m_simple('md_first_payment_timeliness_monthly.csv',
               [('month', D_), ('total', I), ('w14', I), ('w21', I), ('pct14', N), ('pct21', N), ('benchmark_pct', N), ('late_payments', I)],
               ',\n\tScaled = Table.TransformColumns(Typed, {{"pct14", each _/100, type number}, {"pct21", each _/100, type number}, {"benchmark_pct", each _/100, type number}}),\n\tFinal = Table.SelectRows(Scaled, each [month] >= #date(2015, 1, 1))'),
    measures=[
        ('First Payments', 'SUM(Timeliness[total])', '#,0'),
        ('Paid Within 21 Days', 'SUM(Timeliness[w21])', '#,0'),
        ('On-Time %', 'DIVIDE(SUM(Timeliness[w21]), SUM(Timeliness[total]))', '0.0%'),
        ('Standard', '0.87', '0%'),
        ('Latest Month', 'CALCULATE(MAX(Timeliness[month]), ALL(Timeliness))', 'mmm yyyy'),
        ('Latest Month On-Time %', 'VAR m = [Latest Month] RETURN CALCULATE([On-Time %], ALL(Timeliness), Timeliness[month] = m)', '0.0%'),
        ('First Payments 12M', 'VAR m = [Latest Month] RETURN CALCULATE([First Payments], ALL(Timeliness), Timeliness[month] > EDATE(m, -12), Timeliness[month] <= m)', '#,0'),
        ('On-Time Payments 12M', 'VAR m = [Latest Month] RETURN CALCULATE([Paid Within 21 Days], ALL(Timeliness), Timeliness[month] > EDATE(m, -12), Timeliness[month] <= m)', '#,0'),
        ('On-Time % 12M', 'DIVIDE([On-Time Payments 12M], [First Payments 12M])', '0.0%'),
        ('Gap To Standard (pts)', '([Standard] - [On-Time % 12M]) * 100', '0.0'),
        ('Late Payments 12M', '[First Payments 12M] - [On-Time Payments 12M]', '#,0'),
        ('Payments Short Of 87%', 'ROUND([Standard] * [First Payments 12M] - [On-Time Payments 12M], 0)', '#,0'),
        ('Late Payments', 'SUM(Timeliness[late_payments])', '#,0'),
    ])

TABLES['StateComparison'] = dict(
    cols=[('st', 'string', None, 'rank'), ('w21', 'int64', '#,0'), ('total', 'int64', '#,0'), ('pct21', 'double', '0.0%'), ('rank', 'int64', '0')],
    m=m_simple('state_comparison_trailing12m.csv', [('st', T), ('w21', I), ('total', I), ('pct21', N), ('rank', I)],
               ',\n\tScaled = Table.TransformColumns(Typed, {{"pct21", each _/100, type number}}),\n\tFinal = Scaled'),
    measures=[
        ('State On-Time % (others)', 'IF(MAX(StateComparison[st]) <> "MD", SUM(StateComparison[pct21]))', '0.0%'),
        ('State On-Time % (Maryland)', 'IF(MAX(StateComparison[st]) = "MD", SUM(StateComparison[pct21]))', '0.0%'),
        ('State On-Time %', 'SUM(StateComparison[pct21])', '0.0%'),
        ('Maryland Rank', 'LOOKUPVALUE(StateComparison[rank], StateComparison[st], "MD")', '0'),
        ('Jurisdictions', 'COUNTROWS(ALL(StateComparison))', '0'),
        ('Median Jurisdiction %', 'MEDIAN(StateComparison[pct21])', '0.0%'),
    ])

TABLES['WeeklyClaims'] = dict(
    cols=[('week_ending', 'dateTime', 'd mmm yyyy'), ('initial_claims', 'int64', '#,0'), ('continued_weeks_claimed', 'int64', '#,0'), ('insured_unemp_rate', 'double', '0.00')],
    m=m_simple('md_weekly_claims.csv', [('week_ending', D_), ('initial_claims', I), ('continued_weeks_claimed', I), ('insured_unemp_rate', N)],
               ',\n\tFinal = Table.SelectRows(Typed, each [week_ending] >= #date(2019, 1, 1))'),
    measures=[('Initial Claims', 'SUM(WeeklyClaims[initial_claims])', '#,0'),
              ('Continued Weeks Claimed', 'SUM(WeeklyClaims[continued_weeks_claimed])', '#,0')])

TABLES['DelayBands'] = dict(
    cols=[('days', 'string', None, 'band_order'), ('payments', 'int64', '#,0'), ('pct', 'double', '0.0%'), ('band_order', 'int64', '0')],
    m=m_simple('md_delay_bands_trailing12m.csv', [('days', T), ('payments', I), ('pct', N)],
               ',\n\tScaled = Table.TransformColumns(Typed, {{"pct", each _/100, type number}}),\n\tIndexed = Table.AddIndexColumn(Scaled, "band_order", 1, 1, Int64.Type),\n\tFinal = Indexed'),
    measures=[('Share Of Payments', 'SUM(DelayBands[pct])', '0.0%')])

TABLES['Peers'] = dict(
    cols=[('month', 'dateTime', 'mmm yyyy'), ('Region', 'string', None), ('Rate', 'double', '0.0%')],
    m=('let\n\tSource = ' + CSV.format(f='rolling12m_21day_peers.csv') + ',\n\tHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),\n'
       '\tMonthDate = Table.TransformColumns(Headers, {{"month", each Date.FromText(_ & "-01"), type date}}),\n'
       '\tLong = Table.UnpivotOtherColumns(MonthDate, {"month"}, "Region", "Rate"),\n'
       '\tTyped = Table.TransformColumns(Long, {{"Rate", each Number.FromText(_, "en-US") / 100, type number}})\nin\n\tTyped'),
    measures=[('Rolling 12M On-Time %', 'AVERAGE(Peers[Rate])', '0.0%')])

TABLES['ClaimsForecast'] = dict(
    cols=[('week_ending', 'dateTime', 'd mmm yyyy'), ('forecast', 'int64', '#,0'), ('low80', 'int64', '#,0'), ('high80', 'int64', '#,0')],
    m=m_simple('forecast_initial_claims_13wk.csv', [('week_ending', D_), ('forecast', I), ('low80', I), ('high80', I)]),
    measures=[('Forecast Claims', 'SUM(ClaimsForecast[forecast])', '#,0'), ('Forecast Low (80%)', 'SUM(ClaimsForecast[low80])', '#,0'),
              ('Forecast High (80%)', 'SUM(ClaimsForecast[high80])', '#,0')])

TABLES['AnnualTimeliness'] = dict(
    cols=[('y', 'int64', '0'), ('MD', 'double', '0.0%'), ('US', 'double', '0.0%')],
    m=m_simple('annual_timeliness_md_vs_us.csv', [('y', I), ('MD', N), ('US', N)],
               ',\n\tScaled = Table.TransformColumns(Typed, {{"MD", each _/100, type number}, {"US", each _/100, type number}}),\n\tFinal = Scaled'),
    measures=[('Maryland Annual %', 'SUM(AnnualTimeliness[MD])', '0.0%'), ('US Annual %', 'SUM(AnnualTimeliness[US])', '0.0%')])

TABLES['FraudVsTimeliness'] = dict(
    cols=[('q', 'string', None, 'q_order'), ('fraud', 'double', '0.0'), ('timely', 'double', '0.0'), ('q_order', 'int64', '0')],
    m=m_simple('fraud_share_vs_timeliness_quarterly.csv', [('q', T), ('fraud', N), ('timely', N)],
               ',\n\tWithOrder = Table.AddColumn(Typed, "q_order", each Number.FromText(Text.End([q], 4)) * 10 + Number.FromText(Text.Middle([q], 1, 1)), Int64.Type),\n\tFinal = WithOrder'),
    measures=[('Fraud Share %', 'SUM(FraudVsTimeliness[fraud]) / 100', '0.0%'), ('Paid Within 21 Days (quarterly)', 'SUM(FraudVsTimeliness[timely]) / 100', '0.0%')])

TABLES['DeptClaims'] = dict(
    cols=[('quarter', 'string', None, 'q_order'), ('claims', 'int64', '#,0'), ('q_order', 'int64', '0')],
    m=m_simple('dept_claims_quarterly.csv', [('quarter', T), ('claims', I)],
               ',\n\tWithOrder = Table.AddColumn(Typed, "q_order", each Number.FromText(Text.End([quarter], 4)) * 10 + Number.FromText(Text.Middle([quarter], 1, 1)), Int64.Type),\n\tFinal = WithOrder'),
    measures=[('Claims Filed', 'SUM(DeptClaims[claims])', '#,0')])

TABLES['WagesRecovered'] = dict(
    cols=[('fiscal_year', 'string', None, 'fy_order'), ('wages', 'int64', '$#,0'), ('fy_order', 'int64', '0')],
    m=m_simple('dept_wages_recovered.csv', [('fiscal_year', T), ('wages', I)],
               ',\n\tIndexed = Table.AddIndexColumn(Typed, "fy_order", 1, 1, Int64.Type),\n\tFinal = Indexed'),
    measures=[('Wages Recovered', 'SUM(WagesRecovered[wages])', '$#,0')])

def tmdl_table(name, t):
    out = [f'table {name}', f'\tlineageTag: {guid()}', '']
    for m_name, dax, fmt in t['measures']:
        q = f"'{m_name}'" if not m_name.replace('_', '').isalnum() else m_name
        out += [f'\tmeasure {q} = {dax}', f'\t\tformatString: {fmt}', f'\t\tlineageTag: {guid()}', '']
    for c in t['cols']:
        cname, dtype, fmt = c[0], c[1], c[2]
        sort = c[3] if len(c) > 3 else None
        out += [f'\tcolumn {cname}', f'\t\tdataType: {dtype}']
        if fmt: out.append(f'\t\tformatString: {fmt}')
        out += [f'\t\tlineageTag: {guid()}', '\t\tsummarizeBy: none', f'\t\tsourceColumn: {cname}']
        if sort: out.append(f'\t\tsortByColumn: {sort}')
        out.append('')
    m_lines = '\n'.join('\t\t\t' + ln for ln in t['m'].split('\n'))
    out += [f'\tpartition {name} = m', '\t\tmode: import', '\t\tsource =', m_lines, '']
    return '\n'.join(out)

write(os.path.join(HERE, f'{NAME}.pbip'), json.dumps({
    '$schema': 'https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json',
    'version': '1.0', 'artifacts': [{'report': {'path': f'{NAME}.Report'}}], 'settings': {'enableAutoRecovery': True}}, indent=2))
write(os.path.join(SM, 'definition.pbism'), json.dumps({
    '$schema': 'https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json',
    'version': '4.0', 'settings': {}}, indent=2))
write(os.path.join(SM, '.platform'), json.dumps({
    '$schema': 'https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json',
    'metadata': {'type': 'SemanticModel', 'displayName': NAME}, 'config': {'version': '2.0', 'logicalId': guid()}}, indent=2))
write(os.path.join(SM, 'definition', 'database.tmdl'), 'database\n\tcompatibilityLevel: 1600\n')
model = ['model Model', '\tculture: en-US', '\tdefaultPowerBIDataSourceVersion: powerBI_V3', '\tdiscourageImplicitMeasures', '\tsourceQueryCulture: en-US', '']
model += [f'ref table {n}' for n in TABLES] + ['ref expression DataFolder', '']
write(os.path.join(SM, 'definition', 'model.tmdl'), '\n'.join(model))
write(os.path.join(SM, 'definition', 'expressions.tmdl'),
      f'expression DataFolder = "{DATA}" meta [IsParameterQuery=true, IsParameterQueryRequired=true, Type="Text"]\n\tlineageTag: {guid()}\n')
for n, t in TABLES.items():
    write(os.path.join(SM, 'definition', 'tables', f'{n}.tmdl'), tmdl_table(n, t))

# ======================= report (PBIR) =======================
def col(entity, prop):
    return {'Column': {'Expression': {'SourceRef': {'Entity': entity}}, 'Property': prop}}
def meas(entity, prop):
    return {'Measure': {'Expression': {'SourceRef': {'Entity': entity}}, 'Property': prop}}
def proj(field, entity, prop, active=None):
    kind = 'Measure' if 'Measure' in field else 'Column'
    p = {'field': field, 'queryRef': f'{entity}.{prop}', 'nativeQueryRef': prop}
    if active: p['active'] = True
    return p
def C(e, p, active=None): return proj(col(e, p), e, p, active)
def M(e, p): return proj(meas(e, p), e, p)

def lit(v): return {'expr': {'Literal': {'Value': v}}}
def container(name, x, y, w, h, vtype, query, title=None, z=0, extra_objects=None):
    v = {'visualType': vtype, 'query': {'queryState': query}, 'drillFilterOtherVisuals': True}
    if extra_objects: v['objects'] = extra_objects
    d = {'$schema': 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.0.0/schema.json',
         'name': name, 'position': {'x': x, 'y': y, 'z': z, 'height': h, 'width': w, 'tabOrder': z}, 'visual': v}
    if title:
        d['visual']['visualContainerObjects'] = {'title': [{'properties': {'show': lit('true'), 'text': lit(f"'{title}'")}}]}
    return d

def card(name, x, y, w, h, entity, measure, title):
    return container(name, x, y, w, h, 'card', {'Values': {'projections': [M(entity, measure)]}}, title)

def line(name, x, y, w, h, cat, series, title, legend=None):
    q = {'Category': {'projections': [C(cat[0], cat[1], True)]}, 'Y': {'projections': [M(e, p) for e, p in series]}}
    if legend: q['Series'] = {'projections': [C(legend[0], legend[1])]}
    return container(name, x, y, w, h, 'lineChart', q, title)

def column(name, x, y, w, h, cat, series, title, vtype='clusteredColumnChart', sort_measure=None):
    q = {'Category': {'projections': [C(cat[0], cat[1], True)]}, 'Y': {'projections': [M(e, p) for e, p in series]}}
    c = container(name, x, y, w, h, vtype, q, title)
    if sort_measure:
        c['visual']['query']['sortDefinition'] = {'sort': [{'field': meas(*sort_measure), 'direction': 'Descending'}], 'isDefaultSort': False}
    return c

PAGES = [
 ('overview', 'Executive overview', [
   card('k1', 20, 20, 240, 90, 'Timeliness', 'On-Time % 12M', 'On-time rate, last 12 months'),
   card('k2', 275, 20, 240, 90, 'Timeliness', 'Latest Month On-Time %', 'Latest month'),
   card('k3', 530, 20, 240, 90, 'StateComparison', 'Maryland Rank', 'Rank (of 53)'),
   card('k4', 785, 20, 240, 90, 'Timeliness', 'Late Payments 12M', 'Late payments, 12 months'),
   card('k5', 1040, 20, 220, 90, 'Timeliness', 'Payments Short Of 87%', 'Short of 87% goal'),
   line('l1', 20, 125, 620, 250, ('Timeliness', 'month'), [('Timeliness', 'On-Time %'), ('Timeliness', 'Standard')], 'Share of first payments within 21 days (87% standard)'),
   column('c1', 20, 385, 1240, 320, ('StateComparison', 'st'), [('StateComparison', 'State On-Time % (others)'), ('StateComparison', 'State On-Time % (Maryland)')],
          'Last 12 months by jurisdiction (Maryland highlighted)', 'columnChart'),
   column('c2', 650, 125, 610, 250, ('DelayBands', 'days'), [('DelayBands', 'Share Of Payments')], 'When payments go out (days from first compensable week)'),
 ]),
 ('analytics', 'Analytics deep dive', [
   line('p1', 20, 20, 1240, 300, ('Peers', 'month'), [('Peers', 'Rolling 12M On-Time %')], 'Maryland vs neighbors and national pool (rolling 12 months)', legend=('Peers', 'Region')),
   line('p2', 20, 335, 410, 370, ('ClaimsForecast', 'week_ending'), [('ClaimsForecast', 'Forecast Claims'), ('ClaimsForecast', 'Forecast Low (80%)'), ('ClaimsForecast', 'Forecast High (80%)')],
        '13-week forecast of initial claims (80% band)'),
   column('p3', 440, 335, 410, 370, ('Timeliness', 'month'), [('Timeliness', 'Late Payments')], 'Late first payments per month'),
   line('p4', 860, 335, 400, 370, ('WeeklyClaims', 'week_ending'), [('WeeklyClaims', 'Initial Claims')], 'Weekly initial claims'),
 ]),
 ('dept', 'Inside MD Labor', [
   line('d1', 20, 20, 620, 330, ('AnnualTimeliness', 'y'), [('AnnualTimeliness', 'Maryland Annual %'), ('AnnualTimeliness', 'US Annual %')], 'On-time rate by year: Maryland vs US'),
   line('d2', 650, 20, 610, 330, ('FraudVsTimeliness', 'q'), [('FraudVsTimeliness', 'Fraud Share %'), ('FraudVsTimeliness', 'Paid Within 21 Days (quarterly)')], 'Suspected-fraud share vs on-time rate (quarterly)'),
   column('d3', 20, 365, 620, 340, ('DeptClaims', 'quarter'), [('DeptClaims', 'Claims Filed')], 'UI claims filed per quarter (department-reported)'),
   column('d4', 650, 365, 610, 340, ('WagesRecovered', 'fiscal_year'), [('WagesRecovered', 'Wages Recovered')], 'Wages recovered for workers (department-reported)'),
 ]),
]

write(os.path.join(RP, 'definition.pbir'), json.dumps({
    '$schema': 'https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json',
    'version': '4.0', 'datasetReference': {'byPath': {'path': f'../{NAME}.SemanticModel'}}}, indent=2))
write(os.path.join(RP, '.platform'), json.dumps({
    '$schema': 'https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json',
    'metadata': {'type': 'Report', 'displayName': NAME}, 'config': {'version': '2.0', 'logicalId': guid()}}, indent=2))
write(os.path.join(RP, 'definition', 'version.json'), json.dumps({
    '$schema': 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json', 'version': '2.0.0'}, indent=2))
THEME = {'name': 'MD UI', 'dataColors': ['#1d4e89', '#c8102e', '#e0a100', '#2a9d6f', '#7b4fb0', '#5c6b7a', '#6aa9ee', '#e07a5f'],
         'background': '#FFFFFF', 'foreground': '#14213D', 'tableAccent': '#1d4e89',
         'textClasses': {'title': {'fontFace': 'Segoe UI Semibold', 'fontSize': 12, 'color': '#14213D'}}}
write(os.path.join(RP, 'StaticResources', 'RegisteredResources', 'MDUI.json'), json.dumps(THEME, indent=2))
VER = {'visual': '1.8.0', 'report': '2.0.0', 'page': '1.3.0'}
write(os.path.join(RP, 'definition', 'report.json'), json.dumps({
    '$schema': 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.0.0/schema.json',
    'themeCollection': {'baseTheme': {'name': 'CY24SU10', 'reportVersionAtImport': VER, 'type': 'SharedResources'},
                        'customTheme': {'name': 'MDUI.json', 'reportVersionAtImport': VER, 'type': 'RegisteredResources'}},
    'resourcePackages': [{'name': 'RegisteredResources', 'type': 'RegisteredResources',
                          'items': [{'name': 'MDUI.json', 'path': 'MDUI.json', 'type': 'CustomTheme'}]}]}, indent=2))
write(os.path.join(RP, 'definition', 'pages', 'pages.json'), json.dumps({
    '$schema': 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json',
    'pageOrder': [p[0] for p in PAGES], 'activePageName': PAGES[0][0]}, indent=2))
for pid, title, visuals in PAGES:
    write(os.path.join(RP, 'definition', 'pages', pid, 'page.json'), json.dumps({
        '$schema': 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/1.3.0/schema.json',
        'name': pid, 'displayName': title, 'displayOption': 'FitToPage', 'height': 720, 'width': 1280}, indent=2))
    for v in visuals:
        write(os.path.join(RP, 'definition', 'pages', pid, 'visuals', v['name'], 'visual.json'), json.dumps(v, indent=2))
print('written', HERE)
