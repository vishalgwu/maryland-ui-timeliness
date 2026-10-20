"""Downloads the two public US DOL files used by the project into ../raw/ (about 18 MB)."""
import os, urllib.request

RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'raw')
FILES = {
    'ar9050.csv': 'https://oui.doleta.gov/unemploy/csv/ar9050.csv',  # ETA 9050 first-payment time lapse
    'ar539.csv': 'https://oui.doleta.gov/unemploy/csv/ar539.csv',    # ETA 539 weekly claims
}
os.makedirs(RAW, exist_ok=True)
for name, url in FILES.items():
    path = os.path.join(RAW, name)
    print('downloading', url)
    with urllib.request.urlopen(url, timeout=120) as r, open(path, 'wb') as f:
        f.write(r.read())
    print('  saved', path, os.path.getsize(path) // 1024, 'KB')
