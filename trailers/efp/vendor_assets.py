"""Cache the app's public CDN dependencies for repeatable offline capture."""
from pathlib import Path
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
ROOT = Path(__file__).resolve().parent / 'work'
templates = ROOT / 'app/inventory/templates/inventory'
vendor = ROOT / 'app/inventory/static/capture'
vendor.mkdir(parents=True, exist_ok=True)
urls = set()
for f in templates.glob('*.html'):
    urls.update(re.findall(r'(?:src|href)="(https://[^\"]+)"', f.read_text()))
urls = {u for u in urls if not any(host in u for host in ['fonts.googleapis.com', 'fonts.gstatic.com'])}
urls.add('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/webfonts/fa-solid-900.woff2')
def fetch(url):
    name = url.split('/')[-1]
    if not (vendor / name).exists():
        mirror = url.replace('https://cdn.datatables.net/1.13.7/css/dataTables.bootstrap5.min.css', 'https://cdn.jsdelivr.net/npm/datatables.net-bs5@1.13.7/css/dataTables.bootstrap5.min.css').replace('https://cdn.datatables.net/1.13.7/js/dataTables.bootstrap5.min.js', 'https://cdn.jsdelivr.net/npm/datatables.net-bs5@1.13.7/js/dataTables.bootstrap5.min.js').replace('https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js', 'https://cdn.jsdelivr.net/npm/datatables.net@1.13.7/js/jquery.dataTables.min.js')
        with urllib.request.urlopen(mirror, timeout=60) as r:
            data = r.read()
        if name.endswith('.css'):
            data = data.replace(b'../webfonts/', b'')
        (vendor / name).write_bytes(data)
    return url, '/static/capture/' + name
mapping = dict(ThreadPoolExecutor(max_workers=8).map(fetch, sorted(urls)))
for f in templates.glob('*.html'):
    s = f.read_text()
    s = re.sub(r'<link[^>]+https://fonts\.(?:googleapis|gstatic)[^>]+>', '', s)
    for url, local in mapping.items():
        s = s.replace(url, local)
    f.write_text(s)
print('Cached', len(mapping), 'public assets.')
