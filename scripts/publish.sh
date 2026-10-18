#!/usr/bin/env bash
set -euo pipefail
TAG="ponwrt-$(date +%Y%m%d-%H%M)-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"
export TAG
cat > release-notes.md <<NOTES
<!-- ponwrt-weekly-managed -->
PonWrt 自动构建：北京时间 $(date '+%Y-%m-%d %H:%M:%S')。

设备：nokia_xg-040g-md-ubi、znxt_zn515xg-d。请使用对应型号的文件。

包含 iStore、SSR Plus+（Xray / Mihomo）、Lucky、EasyTier、UPnP、Airoha NPU 和 IPTV；默认 Argon 中文界面、192.168.1.1、root 空密码。带 SFTP 文件服务。

源码提交：$(cat release/source-commit.txt)
Lucky 版本：$(python3 -c 'import json;print(json.load(open("release/lucky-build.json"))["version"])')
构建记录：https://github.com/${GH_REPO}/actions/runs/${GITHUB_RUN_ID}

升级保留旧配置时，首次启动默认设置可能覆盖 LAN 地址、主题及 root 密码。请先备份配置与本机出厂数据。固件仅经过构建和镜像结构检查，未自动进行实机刷写测试。
NOTES
# An incomplete upload remains a draft and cannot trigger old-release deletion.
gh release create "$TAG" release/* --draft --target "$GITHUB_SHA" --title "PonWrt $(date +%Y-%m-%d)" --notes-file release-notes.md
python3 - <<'PY'
import json, os, pathlib, subprocess
# GitHub's tag endpoint may return 404 for an unpublished draft.
pages=json.loads(subprocess.check_output(['gh','api','--paginate','--slurp',f'repos/{os.environ["GH_REPO"]}/releases?per_page=100']))
matches=[r for page in pages for r in page if r['tag_name']==os.environ['TAG'] and r['draft']]
if len(matches) != 1:
    raise SystemExit('Expected exactly one matching draft; previous release is preserved')
r=matches[0]
actual={a['name']: a['size'] for a in r['assets']}
expected={p.name: p.stat().st_size for p in pathlib.Path('release').iterdir() if p.is_file()}
if expected != actual:
    raise SystemExit('Uploaded asset list/size mismatch; previous release is preserved')
pathlib.Path('release-id.txt').write_text(str(r['id']))
PY
gh api --method PATCH "repos/${GH_REPO}/releases/$(cat release-id.txt)" -F draft=false -f make_latest=true > published-release.json
# Delete only releases created by this workflow, after publication succeeds.
python3 - <<'PY'
import json, os, subprocess
repo, current = os.environ['GH_REPO'], os.environ['TAG']
pages=json.loads(subprocess.check_output(['gh','api','--paginate','--slurp',f'repos/{repo}/releases?per_page=100']))
for page in pages:
    for release in page:
        tag=release['tag_name']
        if (tag != current and tag.startswith('ponwrt-') and not release['draft']
                and '<!-- ponwrt-weekly-managed -->' in (release.get('body') or '')):
            subprocess.run(['gh','release','delete',tag,'--cleanup-tag','--yes'],check=True)
PY
