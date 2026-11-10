# DEPLOY.md — 部署到 Uppcoder free-resources Stack #1286

目标服务器：Uppcoder Spark 免费档，free-resources Stack #1286（2026-11-10 从 Git 仓库新建，
替代已删除的 blank-stack #1136），裸 Python，无数据库，Private（待切 Public），Active/Running。
公开地址（切 Public 后）：https://xd8ue11o-python-free-resources.apps-2.websson.cloud
Stack 页：https://portal.uppcoder.com/cust-portal/stacks/1286
代码仓库（公开）：https://github.com/xazaj/free-resources-site ，分支 main。
SSH：`xd8ue11o@xd8ue11o-python-free-resources.apps-2.websson.cloud`，端口 2222。

**入口说明（重要）：Uppcoder Python 默认跑 `python3 -u app.py`，门户里没有任何地方
能改启动命令。** 所以仓库根目录有 `app.py`，它只做一件事：交给 `server.main()`；
真正的服务器是 `server.py`（标准库 `http.server`，读 `$PORT`、默认 8000、监听 `0.0.0.0`）。
改启动行为只改这两个文件，不要在门户里找启动命令设置——没有。

**前置条件：SSH key（仅当需要 SSH 时）。** Git 部署不需要 SSH key。
如需 SSH，在 Stack 页点 Connect with SSH → Create a key for me（公钥存账号，私钥下载到本机，
妥善保存，**不要发进聊天、不要写进仓库**）；或在 Settings → SSH Keys 粘贴一个已有的公钥。

## 1. 首次部署（Git 仓库 → Uppcoder 门户）

新建 Stack 时在部署流程的 Build 步骤填 SOURCE CODE：仓库
`https://github.com/xazaj/free-resources-site`，分支 `main`，FOLDER IN THE REPO 留空
（仓库根目录），ACCESS 选 Public repository。其他：裸 Python、无数据库、
VS Code / Terminal / Files / SSH 默认勾选、TIER 默认 Frontend。点 Deploy，
约 5 分钟显示 Deployment Complete（旧 blank-stack 首次部署约 11 分钟）。

注意：已部署的 Stack 在门户里**没有**接仓库的入口（2026-11-10 实测：主应用卡片无
Repository/Source 行，"Add or remove components" 里也无源码设置；官方指南写的
"No repository → Connect" 在实际界面不存在）。所以改代码要走第 3 节的重新部署，
不要指望在旧 Stack 上直接连仓库。

## 2. 切成公开访问（必须做，否则外人打不开）

Stack 目前是 **Private**（Stack 页显示 Private，“Requires uppcoder login”）。
在 Stack 页把 **Private → Public**（“Allow public access without login” 开关打开），
再打开 https://xd8ue11o-python-free-resources.apps-2.websson.cloud 确认不登录也能看到首页。
VS Code、终端与文件始终只在登录后可见，公开的只是网站本身。

## 3. 每日刷新（外部触发，不在 Uppcoder 里设 cron）

Uppcoder 免费档**没有定时任务**，站内不设 cron、不做抓取。SSH 也连不上
（2026-11-10 实测：网关认 key 但认证循环 partial success，见第 5 节），
所以刷新改走 **Git 推送 + 门户重新部署**，每天的流程全部在外面：

```
09:07  Pi 跑 free-intel-refresh（已有） + node 跑 fetch-deals.mjs（已有）
  ↓
本机（或跑 Pi 的那台机器）跑：
  python3 ~/workspace/uppcoder-free-resources/scripts/refresh_site_data.py
  git push 到 xazaj/free-resources-site 的 main 分支（Muse 经 GitHub App 推送）
  ↓
在 Uppcoder 门户对 free-resources Stack 点重新部署（Redeploy / Pull），
等它变 Active 再打开公开地址核对。
```

把上面几步加到已有每日任务的收尾步骤里即可（Pi 任务或本机 cron，二选一，
不要两边都加，避免重复推送）。注意：门户重新部署约 5–10 分钟；静态文件
是现读的，但只有重新部署（或重启 Python 组件）后新文件才会生效。

## 4. 自定义域名（后续步骤，本次不做）

用户域名托管在 Cloudflare。**不要现在配。** Uppcoder 文档说自定义域名是
plan 功能，Deploy €15 档列出 6 个域名；**Spark 免费档是否包含自定义域名未核实**。
部署并切 Public 后，先去 Stack 的域名设置里看免费档能不能加域名，再决定：
能加，再按 Uppcoder 给的 CNAME / A 记录去 Cloudflare 加解析；不能加，就继续用
`https://xd8ue11o-python-free-resources.apps-2.websson.cloud`，不要假设免费包含。

## 5. 已知问题与排障

- **应用地址返回纯文本 404（2026-11-10 实测）。** blank-stack #1136 与新建的
  free-resources #1286 都出现过。#1286 已查明一个直接原因：仓库当时没有 `app.py`，
  平台 Python 默认跑 `python3 -u app.py`，进程根本没起来；门户里又没有任何地方能改
  启动命令。已补 `app.py`（仅交给 `server.main()`）并重新部署。如补了 `app.py`
  仍 404，再看是不是网关/后端转发问题（旧 Stack 的 Terminal / VS Code / Files
  也全部 404，同一平台侧症状），那时再找平台支持。
- **网页 Terminal / VS Code / Files 返回 404（2026-11-10 实测）。**
  部署完成后与重启 Python 组件后均如此。不要反复点网页终端；改走 SSH 核实
  Python / pip / git 版本（`python3 --version; pip3 --version; git --version`），
  并把版本号补记到 README / 记忆里。如 SSH 也连不上，先确认 key 已正确添加、
  再确认 Stack 是 Active/Running。
- **SSH 认证循环 partial success（2026-11-10 实测）。** 服务器认 key 但只给
  "partial success"，随后循环要求再次 publickey，始终不完成登录；单把、双把、
  平台自生成三把 key 都如此；整栈重启无效。疑似网关认了账号 key 后接不到容器内
  sshd（与网页工具 404 同源）。不要反复试 key；部署与刷新改走 Git + 门户。
- **部署约 5–11 分钟才完成，期间一直显示 Queued。** 首次部署慢是正常的，等它变
  Deployment Complete 再操作，不要中途重复提交。
- **额度。** 2GB 磁盘：本站全部文件约 530KB，最大单文件是首页 `public/index.html` 约 150KB，
  即使每天加数据也够用很久；500 CPU 秒/天：纯静态文件读取几乎不耗 CPU，
  不要在站里加服务端渲染、搜索索引或定时任务。
- **备份。** 本仓库（`~/workspace/uppcoder-free-resources/`）已纳入每日复活包的
  备份范围；Uppcoder 端每晚也有备份。改数据只改本地源文件再重新生成，不要直接
  在服务器上改 `public/index.html`（下次刷新会被覆盖）。

## 6. 部署后核对清单

- [ ] 应用地址能打开（`app.py` 在运行），首页统计数字与 `data/meta.json` 一致
- [ ] Stack 已切 Public，公开地址不登录能打开
- [ ] 首页搜索、类别/绑卡/核实筛选、羊毛筛选在手机与桌面都正常
- [ ] 第二天 09:07 刷新后，Git 推送 + 门户重新部署一次，确认数字有更新（或无变化时不推送也行，但要留日志）
- [ ] （如 SSH 恢复）SSH 能连入，`python3 --version` 已记录
