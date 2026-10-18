#!/usr/bin/env python3
import hashlib
import json
import pathlib
import shutil
import sys

build, output = map(pathlib.Path, sys.argv[1:3])
output.mkdir(parents=True, exist_ok=True)
profiles = json.loads((build/'profiles.json').read_text())['profiles']
for device in ('nokia_xg-040g-md-ubi', 'znxt_zn515xg-d', 'fiberhome_hg5585f-ct'):
    info = profiles[device]
    images = [image for image in info['images']
              if image.get('name', '').endswith('.itb')]
    if not any('sysupgrade' in image['name'] for image in images):
        raise SystemExit(f'Missing sysupgrade ITB for {device}')
    for image in images:
        name = image['name']
        if pathlib.Path(name).name != name:
            raise SystemExit('Invalid output path in profiles.json')
        file = build/name
        data = file.read_bytes()
        if len(data) < 1024*1024 or data[:4] != bytes.fromhex('d00dfeed'):
            raise SystemExit(f'Invalid FIT image: {name}')
        if image.get('sha256') and hashlib.sha256(data).hexdigest() != image['sha256']:
            raise SystemExit(f'Image hash mismatch: {name}')
        shutil.copy2(file, output/name)
for name in ('profiles.json', 'version.buildinfo', 'feeds.buildinfo', 'config.buildinfo'):
    if (build/name).is_file():
        shutil.copy2(build/name, output/name)
for file in build.glob('*.manifest'):
    shutil.copy2(file, output/file.name)
for name in ('build-config.diff', 'source-commit.txt', 'feeds-sources.txt', 'feeds-commits.txt', 'lucky-build.json', 'easytier-version.txt'):
    shutil.copy2(name, output/name)
files = sorted(file for file in output.iterdir() if file.is_file() and file.name != 'sha256sums')
(output/'sha256sums').write_text(''.join(hashlib.sha256(file.read_bytes()).hexdigest()+'  '+file.name+'\n' for file in files))
print('Validated images for both models; packaged '+str(len(files))+' files')
