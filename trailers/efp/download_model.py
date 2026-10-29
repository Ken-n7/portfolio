"""Download the official full-precision Kokoro release in verified ranges."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import urllib.request
import time
import hashlib

ROOT = Path(__file__).resolve().parent / 'work'
ROOT.mkdir(parents=True, exist_ok=True)
release_url = 'https://api.github.com/repos/thewh1teagle/kokoro-onnx/releases/tags/model-files-v1.1'
with urllib.request.urlopen(release_url, timeout=30) as response:
    release = json.load(response)
(ROOT / 'model-release.json').write_text(json.dumps(release, indent=2))
asset = next(a for a in release['assets'] if a['name'] == 'kokoro-v1.0.onnx')
url, size = asset['browser_download_url'], asset['size']
chunk = 4 * 1024 * 1024
parts = ROOT / 'model-parts'
parts.mkdir(exist_ok=True)
def fetch(i):
    start, end = i * chunk, min(size, (i + 1) * chunk) - 1
    dest = parts / str(i)
    if dest.exists() and dest.stat().st_size == end - start + 1:
        return
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={'Range': f'bytes={start}-{end}', 'User-Agent': 'EFP-local-video-build'})
            with urllib.request.urlopen(req, timeout=120) as r:
                assert r.status == 206, f'Range unsupported: {r.status}'
                assert r.headers.get('Content-Range', '').startswith(f'bytes {start}-{end}/')
                data = r.read()
            assert len(data) == end - start + 1
            dest.write_bytes(data)
            print(f'Part {i + 1}/{(size + chunk - 1) // chunk}', flush=True)
            return
        except Exception:
            if attempt == 3:
                raise
            time.sleep(1 + attempt)
with ThreadPoolExecutor(max_workers=16) as pool:
    list(pool.map(fetch, range((size + chunk - 1) // chunk)))
with (ROOT / 'kokoro-v1.0.onnx').open('wb') as out:
    for i in range((size + chunk - 1) // chunk):
        out.write((parts / str(i)).read_bytes())
assert (ROOT / 'kokoro-v1.0.onnx').stat().st_size == size
with (ROOT / 'kokoro-v1.0.onnx').open('rb') as model:
    assert 'sha256:' + hashlib.file_digest(model, 'sha256').hexdigest() == asset['digest']
print('Full precision model ready.', flush=True)
