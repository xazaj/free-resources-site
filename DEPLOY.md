# DEPLOY.md — 部署到 Uppcoder free-resources Stack（Flask）

目标服务器：Uppcoder Spark 免费档，free-resources Stack（2026-11-10 用 Flask 重建，
替代已删除的裸 Python #1286 与 #1136），无数据库，Private（待切 Public），Active/Running。
公开地址（切 Public 后）：见 Stack 页给出的新地址（每次重建都会换）。
Stack 页：见门户 Stacks 列表中的 free-resources。
代码仓库（公开）：https://github.com/xazaj/free-resources-site ，分支 main。
SSH：见 Stack 页 Connect with SSH 给出的新用户与地址，端口 2222。

**入口说明（按官方 Flask 指南，2026-11-10 精读确认）：**
- 必须用**框架 Stack（Flask）**，不要用裸 Python：只有框架卡片才有仓库连接行
  （"No repository → Connect"，之后 Pull 拉新提交）；裸 Python 卡片没有这一行，
  已部署的裸 Python Stack 在门户里也接不上仓库、没有重新拉取入口。
- 应用以 **`python app.py`** 启动，**必须监听 127.0.0.1:8000**（平台代理只往这个
  地址转发；Flask 官方示例就是 `app.run(host="127.0.0.1", port=8000)`）。
  不要绑 0.0.0.0、不要读 `$PORT`——代理不认 `$PORT`。
- 所以仓库根目录有 `app.py`（仅交给 `server.main()`），`server.py` 固定绑
  127.0.0.1:8000。门户里没有任何地方能改启动命令，不要找。
- 之前两个裸 Python Stack 全部 404 的原因就是上面三条全违反：进程从未起来，
  入口网关对所有路径（包括 Terminal / VS Code / Files）都回纯文本 404。

## 1. 首次部署（Git 仓库 → Uppcoder 门户）

新建 Stack：Stacks → Create → Blank stack，在搜索框输入 `flask` 选 Flask
（不要选裸 Python，见上），起名字 free-resources；不加数据库（本站不需要）。
在 Build 步骤填 SOURCE CODE：仓库 `https://github.com/xazaj/free-resources-site`，
分支 `main`，FOLDER IN THE REPO 留空（仓库根目录），ACCESS 选 Public repository。
VS Code / Terminal / Files / SSH 默认勾选、TIER 默认 Frontend。点 Deploy，
约 5 分钟显示 Deployment Complete（旧 blank-stack 首次部署约 11 分钟）。

部署完先打开应用地址核对：应直接显示首页（Flask 官方示例 42 秒上线）。
如仍 404，先确认仓库根目录有 `app.py` 且 `server.py` 绑 127.0.0.1:8000，
再重启 Python 组件一次。

已部署 Stack 的代码更新：Flask 卡片上有 "No repository → Connect" 与 Pull，
新提交用 Pull 拉取（裸 Python 卡片没有，见上）。

## 2. 切成公开访问（必须做，否则外人打不开）

Stack 目前是 **Private**（Stack 页显示 Private，“Requires uppcoder login”）。
在 Stack 页把 **Private → Public**（“Allow public access without login” 开关打开），
再打开 Stack 页给出的新应用地址确认不登录也能看到首页。
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
在 Uppcoder 门户对 free-resources Stack 的 Flask 卡片点 Pull 拉取新提交，
等它变 Active 再打开公开地址核对（按官方指南：Pull brings in new commits later）。
```

把上面几步加到已有每日任务的收尾步骤里即可（Pi 任务或本机 cron，二选一，
不要两边都加，避免重复推送）。注意：门户 Pull 约几分钟；静态文件
是现读的，Pull 后应用会自动重启生效。

## 4. 自定义域名（后续步骤，本次不做）

用户域名托管在 Cloudflare。**不要现在配。** Uppcoder 文档说自定义域名是
plan 功能，Deploy €15 档列出 6 个域名；**Spark 免费档是否包含自定义域名未核实**。
部署并切 Public 后，先去 Stack 的域名设置里看免费档能不能加域名，再决定：
能加，再按 Uppcoder 给的 CNAME / A 记录去 Cloudflare 加解析；不能加，就继续用
Stack 页给出的应用地址，不要假设免费包含。

## 5. 已知问题与排障

- **应用地址返回纯文本 404（2026-11-10 实测，已查明并修复）。** blank-stack #1136
  与 free-resources #1286（均为裸 Python）都出现过。2026-11-10 精读官方 Flask
  指南后确认真正原因有三条，全违反：① 用了裸 Python Stack——只有框架卡片才有
  仓库连接行，裸 Python 卡片没有，部署后也接不上仓库、拉不到新代码；② 仓库当时
  没有 `app.py`，而应用以 `python app.py` 启动；③ `server.py` 绑的是
  0.0.0.0:$PORT，而平台代理只往 127.0.0.1:8000 转发。进程从未起来，入口网关对
  所有路径（包括 Terminal / VS Code / Files）都回纯文本 404。修复：`app.py`
  交给 `server.main()`、`server.py` 改绑 127.0.0.1:8000、用 Flask 重建 Stack。
  如 Flask 重建后仍 404，再找平台支持（当时支持对话已开，John Bannister 未回）。
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
- [ ] 第二天 09:07 刷新后，Git 推送 + 门户 Pull 一次，确认数字有更新（或无变化时不推送也行，但要留日志）
- [ ] （如 SSH 恢复）SSH 能连入，`python3 --version` 已记录
