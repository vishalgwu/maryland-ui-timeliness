import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(HERE, 'data', 'department.json'), encoding='utf-8'))
html = open(os.path.join(HERE, 'department_template.html'), encoding='utf-8').read()
html = html.replace('/*CHARTJS*/', open(os.path.join(HERE, 'chart.umd.min.js'), encoding='utf-8').read())
html = html.replace('/*DATA*/', json.dumps(data))
open(os.path.join(HERE, 'department.html'), 'w', encoding='utf-8').write(html)
print('ok', len(html) // 1024, 'KB')
