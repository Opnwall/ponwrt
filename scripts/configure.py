#!/usr/bin/env python3
"""Preserve upstream platform defaults, restrict profiles, then select applications."""
import pathlib
import re
import sys

source = pathlib.Path(sys.argv[1]).resolve()
repo = pathlib.Path(__file__).resolve().parents[1]
base = (source / 'configs/an7581.config').read_text()
# Remove both old and new per-device Kconfig forms, including -usb-sfp variants.
base = '\n'.join(line for line in base.splitlines() if not re.match(
    r'(?:# )?CONFIG_TARGET_(?:DEVICE_)?airoha_an7581_DEVICE_', line)) + '\n'
base = re.sub(r'(?:# )?CONFIG_TARGET_ALL_PROFILES(?:=.*| is not set)',
              '# CONFIG_TARGET_ALL_PROFILES is not set', base)
extra = (repo / 'config/packages.config').read_text()
# Drop preexisting assignments to avoid relying on Kconfig duplicate precedence.
keys = set(re.findall(r'^(?:# )?(CONFIG_[A-Za-z0-9_-]+)(?:=| is not set)', extra, re.M))
base = '\n'.join(line for line in base.splitlines()
                 if not any(line.startswith(k+'=') or line == '# '+k+' is not set' for k in keys)) + '\n'
profiles = '\n'.join(
    f'CONFIG_TARGET_DEVICE_airoha_an7581_DEVICE_{device}=y\n'
    f'CONFIG_TARGET_DEVICE_PACKAGES_airoha_an7581_DEVICE_{device}=""'
    for device in ('nokia_xg-040g-md-ubi', 'znxt_zn515xg-d'))
(source / '.config').write_text(base + '\n' + profiles + '\n' + extra)
defaults = source / 'files/etc/uci-defaults'
defaults.mkdir(parents=True, exist_ok=True)
(defaults / '99-opnwall-defaults').write_text('''#!/bin/sh
# Fresh-image defaults; no operator identity or optical calibration is embedded.
uci set network.lan.ipaddr='192.168.1.1'
uci set network.lan.netmask='255.255.255.0'
uci set luci.main.mediaurlbase='/luci-static/argon'
uci set luci.main.lang='zh_cn'
uci commit network
uci commit luci
passwd -d root
exit 0
''')
(defaults / '99-opnwall-defaults').chmod(0o755)
# Fix the empty-argument/getopts bug previously verified on these devices.
init = source / 'feeds/ssr/luci-app-ssr-plus/root/etc/init.d/shadowsocksr'
if not init.exists():
    raise SystemExit('SSR init script path changed; inspect the upstream package before building')
s = init.read_text()
old = '"$(get_arg_out)" "$(gfwmode)" "$ARG_UDP" "$ARG_UDP_RULES" "$ARG_A"'
if old in s:
    s = s.replace(old, '$(get_arg_out) $(gfwmode) $ARG_UDP $ARG_UDP_RULES $ARG_A')
    init.write_text(s)
else:
    print('SSR optional-argument expression changed upstream; no legacy patch required')

# Package-host tools are staged in hostpkg, not the tools/ host directory.
# Both SSR core recipes use upx/host but older recipes reference the tools path.
for package in ('mihomo', 'xray-core'):
    recipe = source / 'feeds/ssr' / package / 'Makefile'
    content = recipe.read_text()
    if 'upx/host' not in content:
        raise SystemExit(f'{package}: UPX host dependency changed; inspect upstream recipe')
    old_tool = '$(STAGING_DIR_HOST)/bin/upx'
    new_tool = '$(STAGING_DIR_HOSTPKG)/bin/upx'
    if old_tool in content:
        recipe.write_text(content.replace(old_tool, new_tool))
        print(f'{package}: corrected UPX path to STAGING_DIR_HOSTPKG')
    elif new_tool not in content:
        raise SystemExit(f'{package}: UPX install command changed; inspect upstream recipe')

# miniupnpd 2.3.11 already contains the permission-parser and private-WAN fixes.
# The feed still carries its old backport and logging hunks for older sources.
miniupnpd = source / 'feeds/packages/net/miniupnpd'
if re.search(r'^PKG_VERSION:=2\.3\.11$', (miniupnpd / 'Makefile').read_text(), re.M):
    (miniupnpd / 'patches/020-descr-filter-fix.patch').unlink(missing_ok=True)
    (miniupnpd / 'patches/030-allow-private-fix.patch').unlink(missing_ok=True)
    (miniupnpd / 'patches/040-improve-logging.patch').write_text(
        (repo / 'config/miniupnpd-2.3.11-logging.patch').read_text())
    print('miniupnpd 2.3.11: removed integrated parser/private-WAN backports and rebased logging patch')
