# PonWrt 自动编译

基于 [pbs05/ponwrt](https://github.com/pbs05/ponwrt) 最新 master 源码，自动更新所有 feeds。

## 设备与默认设置

| 设备 | Profile |
| --- | --- |
| Nokia XG-040G-MD UBI | `nokia_xg-040g-md-ubi` |
| ZNXT ZN515XG-D | `znxt_zn515xg-d` |
| FiberHome HG5585F CT | `fiberhome_hg5585f-ct` |

- 默认地址：`192.168.1.1`，用户名 `root`，密码为空。
- 默认主题：Argon，简体中文。
- 插件：iStore、SSR Plus+（Xray / Mihomo）、Lucky（每次构建获取最新正式版 ARM64 二进制）、EasyTier、UPnP、Airoha NPU、IPTV、PON 管理。
- 同时包含 OpenSSH SFTP 服务端，供 FinalShell 文件列表使用。
- 不预置宽带账号、认证 SN/LOID、ri/bosa、节点订阅、Lucky 管理配置或 EasyTier 组网密钥。
- 不自动超频；不自动配置 IPTV VLAN 或远程组网。

## 触发与下载

每周五 **北京时间 00:00** 自动构建（GitHub cron 为 UTC 周四 16:00）。GitHub 的定时队列可能延迟执行。也可在 Actions → Build PonWrt → Run workflow 手动触发。

成功后在 Releases 下载各机型自己的 `sysupgrade.itb`，以及生成的恢复镜像。附件包含 SHA256、源码与 feeds 提交、构建配置和 Lucky 版本记录。

只有两个设备的镜像均构建成功、附件完整上传并正式发布后，才删除本工作流创建的旧 Release 及对应 tag。不会删除手工发布或其他工作流生成的 Release；失败不会删除上一版。

## 实现与来源

- 主源码：https://github.com/pbs05/ponwrt
- PON/IPTV：https://github.com/pbs05/openwrt-pon-userspace
- iStore：https://github.com/linkease/istore
- SSR：https://github.com/fw876/helloworld
- Lucky 插件：https://github.com/gdy666/luci-app-lucky
- Lucky 二进制：https://github.com/gdy666/lucky/releases/latest
- EasyTier：https://github.com/EasyTier/luci-app-easytier
- NPU：https://github.com/rchen14b/luci-app-airoha-npu
- Argon、UPnP：PonWrt 的 LuCI feed。

工作流基于上游完整 AN7581 配置，只启用上述两个 Profile。feeds 全部更新，但仅安装平台已选包、指定插件及其依赖，避免无关桌面/多媒体包带来的 Kconfig 冲突。显式启用 tar 的 XZ 依赖，防止 iStore 被 Kconfig 取消选择。`make defconfig` 后检查必需插件，若上游更名或缺失，构建会失败，避免发布缺少应用的镜像。

Lucky 的版本与压缩包 SHA256 写入包定义；如果 GitHub 提供 asset digest，会额外比对。SSR 包保留之前排查确认的空参数/getopts 修补，并修正 Mihomo/Xray 的 UPX 主机工具路径为 `STAGING_DIR_HOSTPKG`。

## 注意事项

首次启动脚本会设置 LAN 地址、主题和 root 空密码。升级保留配置时也可能覆盖这些设置。刷机前保存配置与本机出厂数据。构建成功不等于已通过实机刷写验证；本仓库不自动操作任何设备。

公开仓库长期没有活动时，GitHub 可能暂停定时任务，需要手动重新启用。构建需要 Actions 的 `contents: write` 权限发布 Release；工作流已按 job 分配权限。

miniupnpd 2.3.11 构建兼容：该版源码已包含权限解析重写，因此移除 feeds 中重复的 `020-descr-filter-fix.patch`；日志补丁按 2.3.11 重新整理。修正仅针对该版本，保留 UPnP 功能和新版权限校验。
