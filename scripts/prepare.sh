#!/usr/bin/env bash
set -euo pipefail
git clone --depth 1 --branch master https://github.com/pbs05/ponwrt.git source
cd source
cat >> feeds.conf.default <<'FEEDS'
src-git istore https://github.com/linkease/istore.git
src-git ssr https://github.com/fw876/helloworld.git
src-git lucky https://github.com/gdy666/luci-app-lucky.git
src-git easytier https://github.com/EasyTier/luci-app-easytier.git
FEEDS
./scripts/feeds update -a
python3 ../scripts/install_selected_feeds.py
# Explicitly prefer these maintainers when another feed has the same package.
./scripts/feeds install -f -p istore luci-app-store luci-lib-taskd luci-lib-xterm taskd
./scripts/feeds install -f -p ssr luci-app-ssr-plus xray-core mihomo
./scripts/feeds install -f -p lucky lucky luci-app-lucky
./scripts/feeds install -f -p easytier easytier luci-app-easytier
# The upstream NPU project is a single-package repository, not a feed root.
if [ ! -e package/feeds/luci/luci-app-airoha-npu ] && [ ! -e package/feeds/pon_userspace/luci-app-airoha-npu ]; then
  git clone --depth 1 https://github.com/rchen14b/luci-app-airoha-npu.git package/custom/luci-app-airoha-npu
fi

# The UI repository may target a core version that has not been released yet.
ET_VERSION=$(gh api repos/EasyTier/EasyTier/releases/latest --jq '.tag_name | ltrimstr("v")')
[[ "$ET_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]
printf 'EASYTIER_VERSION=%s\n' "$ET_VERSION" > feeds/easytier/version.mk
printf '%s\n' "$ET_VERSION" > ../easytier-version.txt
# Upstream also carries an old nested copy; keep only the canonical package.
if [ -d package/custom/luci-app-airoha-npu ]; then
  rm -rf package/custom/luci-app-airoha-npu/luci-app-airoha-npu
  mkdir -p package/custom/luci-app-airoha-npu/po/zh_Hans
  cp ../config/airoha-npu.zh_Hans.po package/custom/luci-app-airoha-npu/po/zh_Hans/airoha-npu.po
fi
