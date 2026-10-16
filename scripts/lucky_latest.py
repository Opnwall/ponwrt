#!/usr/bin/env python3
"""Resolve one stable Lucky ARM64 release and pin its exact archive hash."""
import hashlib
import json
import os
import pathlib
import re
import sys
import time
import urllib.request

source = pathlib.Path(sys.argv[1]).resolve()
headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'Opnwall-ponwrt-builder'}
if os.environ.get('GH_TOKEN'):
    headers['Authorization'] = 'Bearer '+os.environ['GH_TOKEN']

def fetch(url, authenticated=False):
    for attempt in range(4):
        try:
            request = urllib.request.Request(url, headers=headers if authenticated else {'User-Agent': headers['User-Agent']})
            with urllib.request.urlopen(request, timeout=120) as response:
                data = response.read()
                length = response.headers.get('Content-Length')
                if length and len(data) != int(length):
                    raise OSError('Incomplete download')
                return data
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2**attempt)

release = json.loads(fetch('https://api.github.com/repos/gdy666/lucky/releases/latest', True))
version = release['tag_name'].removeprefix('v')
if not re.fullmatch(r'\d+\.\d+\.\d+(?:[.-][A-Za-z0-9]+)*', version):
    raise SystemExit('Unexpected Lucky version: '+version)
filename = f'lucky_{version}_Linux_arm64.tar.gz'
asset = next(a for a in release['assets'] if a['name'] == filename)
data = fetch(asset['browser_download_url'])
digest = hashlib.sha256(data).hexdigest()
expected = asset.get('digest')
if expected and expected != 'sha256:'+digest:
    raise SystemExit('Lucky archive does not match GitHub release asset digest')
(source/'dl').mkdir(exist_ok=True)
(source/'dl'/filename).write_bytes(data)
makefile = source/'feeds/lucky/lucky/Makefile'
s = makefile.read_text()
for field, value in [('PKG_VERSION', version), ('PKG_HASH', digest)]:
    s, count = re.subn(r'^'+field+r':=.*$', field+':='+value, s, flags=re.M)
    if count != 1:
        raise SystemExit('Lucky package format changed: '+field)
makefile.write_text(s)
pathlib.Path('lucky-build.json').write_text(json.dumps({
    'version': version, 'asset': filename, 'sha256': digest,
    'github_digest': expected, 'release_url': release['html_url'],
    'asset_url': asset['browser_download_url']}, indent=2)+'\n')
print(f'Lucky {version}: {digest}')
