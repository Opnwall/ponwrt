#!/usr/bin/env python3
"""Install only packages selected by platform defaults and our application list."""
import pathlib
import re
import subprocess

source = pathlib.Path.cwd()
repo = pathlib.Path(__file__).resolve().parents[1]
text = (source/'configs/an7581.config').read_text()+'\n'+(repo/'config/packages.config').read_text()
selected = set(re.findall(r'^CONFIG_PACKAGE_([^=]+)=[ym]$', text, re.M))
available = set()
for index in (source/'feeds').glob('*.index'):
    available.update(re.findall(r'^Package: (\S+)$', index.read_text(), re.M))
# Config symbols for package features are not independent packages.
packages = sorted(selected & available)
print('Installing '+str(len(packages))+' selected feed packages and their dependencies', flush=True)
subprocess.run(['./scripts/feeds','install',*packages],check=True)
