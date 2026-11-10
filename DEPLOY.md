# DEPLOY.md — 部署到 Uppcoder blank-stack #1136

目标服务器：Uppcoder Spark 免费档，blank-stack #1136，裸 Python，无数据库，
Private（待切 Public），Active/Running。
公开地址（切 Public 后）：https://w0vgf700-python-blank-stack.apps-2.websson.cloud
Stack 页：https://portal.uppcoder.com/cust-portal/stacks/1136
SSH：`w0vgf700@w0vgf700-python-blank-stack.apps-2.websson.cloud`，端口 2222。

**前置条件：SSH key。** 本次构建没有创建任何 key，也没有联系 Uppcoder。
部署前必须先有 key，二选一：
1. 在 Stack 页点 Connect with SSH → Create a key for me（公钥存账号，私钥下载到本机，妥善保存，**不要发进聊天、不要写进仓库**）；或
2. 在 Settings → SSH Keys 粘贴一个已有的公钥。

## 1. 首次部署（本机 → Uppcoder，经 SSH）

```bash
# 0. 先在本机生成最新页面（用 Pi 当天 09:07 跑完后的最新数据）
cd ~/workspace/uppcoder-free-resources
python3 scripts/refresh_site_data.py

# 1. 同步到服务器（示例路径以 Stack 内实际工作目录为准，SSH 连入后先 pwd 确认）
rsync -avz -e "ssh -p 2222" --exclude ".git" ./ w0vgf700@w0vgf700-python-blank-stack.apps-2.websson.cloud:~/free-resources/

# 2. SSH 连入，启动（标准库，无需 pip install）
ssh -p 2222 w0vgf700@w0vgf700-python-blank-stack.apps-2.websson.cloud
cd ~/free-resources
python3 --version   # 核实 Python 版本，记录下来（2026-11-10 网页终端 404，未能核实）
PORT=8000 python3 server.py
```

启动命令以 Stack 的进程配置为准：如果 Uppcoder 要求应用监听特定端口或用特定启动命令，
把 `PORT` 换成平台给的端口环境变量；`server.py` 读 `$PORT`，默认 8000，监听 `0.0.0.0`。
如需后台常驻，用 `nohup python3 server.py > server.log 2>&1 &` 或 Stack 自带的进程管理，
不要指望 `systemd`（容器内没有）。

## 2. 切成公开访问（必须做，否则外人打不开）

Stack 目前是 **Private**（Stack 页显示 Private，“Requires uppcoder login”）。
在 Stack 页把 **Private → Public**（“Allow public access without login” 开关打开），
再打开 https://w0vgf700-python-blank-stack.apps-2.websson.cloud 确认不登录也能看到首页。
VS Code、终端与文件始终只在登录后可见，公开的只是网站本身。

## 3. 每日刷新（外部触发，不在 Uppcoder 里设 cron）

Uppcoder 免费档**没有定时任务**，站内不设 cron、不做抓取。每天的流程全部在外面：

```
09:07  Pi 跑 free-intel-refresh（已有） + node 跑 fetch-deals.mjs（已有）
  ↓
本机（或跑 Pi 的那台机器）跑：
  python3 ~/workspace/uppcoder-free-resources/scripts/refresh_site_data.py
  rsync -avz -e "ssh -p 2222" ~/workspace/uppcoder-free-resources/public/ \
    w0vgf700@w0vgf700-python-blank-stack.apps-2.websson.cloud:~/free-resources/public/
  ↓
静态文件是现读的，rsync 完即生效，一般不用重启 server.py。
如改了 server.py 本身，才需要 SSH 进去重启一次。
```

把上面两行加到已有每日任务的收尾步骤里即可（Pi 任务或本机 cron，二选一，
不要两边都加，避免重复推送）。

## 4. 自定义域名（后续步骤，本次不做）

用户域名托管在 Cloudflare。**不要现在配。** Uppcoder 文档说自定义域名是
plan 功能，Deploy €15 档列出 6 个域名；**Spark 免费档是否包含自定义域名未核实**。
部署并切 Public 后，先去 Stack 的域名设置里看免费档能不能加域名，再决定：
能加，再按 Uppcoder 给的 CNAME / A 记录去 Cloudflare 加解析；不能加，就继续用
`https://w0vgf700-python-blank-stack.apps-2.websson.cloud`，不要假设免费包含。

## 5. 已知问题与排障

- **网页 Terminal / VS Code / Files 返回 404（2026-11-10 实测）。**
  部署完成后与重启 Python 组件后均如此。不要反复点网页终端；改走 SSH 核实
  Python / pip / git 版本（`python3 --version; pip3 --version; git --version`），
  并把版本号补记到 README / 记忆里。如 SSH 也连不上，先确认 key 已正确添加、
  再确认 Stack 是 Active/Running。
- **部署约 11 分钟才完成，期间一直显示 Queued。** 首次部署慢是正常的，等它变
  Deployment Complete 再操作，不要中途重复提交。
- **额度。** 2GB 磁盘：本站全部文件约 530KB，最大单文件是首页 `public/index.html` 约 150KB，
  即使每天加数据也够用很久；500 CPU 秒/天：纯静态文件读取几乎不耗 CPU，
  不要在站里加服务端渲染、搜索索引或定时任务。
- **备份。** 本仓库（`~/workspace/uppcoder-free-resources/`）已纳入每日复活包的
  备份范围；Uppcoder 端每晚也有备份。改数据只改本地源文件再重新生成，不要直接
  在服务器上改 `public/index.html`（下次刷新会被覆盖）。

## 6. 部署后核对清单

- [ ] SSH 能连入，`python3 --version` 已记录
- [ ] `server.py` 在运行，`curl -I http://127.0.0.1:8000/`（站内）返回 200
- [ ] Stack 已切 Public，公开地址不登录能打开，首页统计数字与 `data/meta.json` 一致
- [ ] 首页搜索、类别/绑卡/核实筛选、羊毛筛选在手机与桌面都正常
- [ ] 第二天 09:07 刷新后，rsync 推送一次，确认数字有更新（或无变化时不推送也行，但要留日志）
