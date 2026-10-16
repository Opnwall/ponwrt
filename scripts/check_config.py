#!/usr/bin/env python3
import pathlib
import re
import sys
s = pathlib.Path(sys.argv[1]).read_text()
expected = {'nokia_xg-040g-md-ubi', 'znxt_zn515xg-d'}
actual = set(re.findall(r'^CONFIG_TARGET_DEVICE_airoha_an7581_DEVICE_([^=]+)=y$', s, re.M))
if actual != expected:
    raise SystemExit(f'Device selection mismatch: {actual} != {expected}')
required = ['luci-app-store', 'luci-app-ssr-plus', 'xray-core', 'mihomo',
            'lucky', 'luci-app-lucky', 'easytier', 'luci-app-easytier',
            'luci-app-upnp', 'luci-app-airoha-npu', 'luci-app-iptv',
            'luci-theme-argon', 'openssh-sftp-server', 'kmod-nft-tproxy', 'kmod-nft-socket',
            'luci-i18n-ssr-plus-zh-cn', 'luci-i18n-lucky-zh-cn',
            'luci-i18n-easytier-zh-cn', 'luci-i18n-airoha-npu-zh-cn', 'luci-i18n-iptv-zh-cn']
missing = [p for p in required if f'CONFIG_PACKAGE_{p}=y' not in s.splitlines()]
if missing:
    raise SystemExit('Required packages disappeared during make defconfig: '+', '.join(missing))
print('Both device profiles and all required packages are enabled')
