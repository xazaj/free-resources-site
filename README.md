# 免费资源站

每天刷新的免费资源目录：免费 VPS、容器 / PaaS、代码沙箱、LLM API、笔记本算力（80 条服务），加上近 7 天论坛羊毛（免费白嫖 / 限免 / 低价优惠）。设计灵感来自 openbot.run（深色、干净、大字标题、卡片网格、留白大），文案与品牌是本站自己的，没有复制对方的文字或标识。

- 公开地址（部署后）：https://w0vgf700-python-blank-stack.apps-2.websson.cloud
  （Stack 目前还是 Private，部署时按 DEPLOY.md 先切成 Public 才能公开访问。）
- 托管：Uppcoder Spark 免费档，blank-stack #1136，裸 Python，无数据库
- 数据快照：2026-11-10（`data/meta.json` 有准确时间；每次刷新会更新）

## 技术栈选择：纯静态站 + Python 标准库服务器

**选了纯静态，没有选 Flask。** 理由：

| 方案 | 结论 |
|---|---|
| 纯静态 HTML + JSON，`python3 server.py`（`http.server` 标准库） | ✅ 选中。零依赖，不用 `pip install`；每次请求只是读文件，CPU 消耗最小，最适合每天只有 500 CPU 秒的 Spark 免费档；没有数据库、没有模板渲染、没有冷启动。 |
| Python + Flask | ❌ 不选。Flask 每请求都要经过路由与模板渲染，多一层依赖与进程开销；本站不需要登录、表单或动态接口，Flask 带来的全是成本，没有收益。 |
| Node / Next.js 等 | ❌ 不选。构建重、内存占用大，2GB 内存 / 2GB 磁盘的免费 Stack 没必要。 |

- 字体：系统字体栈，无外部字体、无 CDN、无统计脚本，首屏不依赖任何外网请求。
- 渲染：构建时（`scripts/refresh_site_data.py`）把全部卡片预渲染进 `public/index.html`，关掉 JS 也能看；`public/assets/app.js`（约 1.9KB）只做本地搜索与筛选，不发任何网络请求。
- 数据：`data/services.json`（情报快照全文）、`data/deals.json`（近 7 天羊毛）、`data/meta.json`（快照时间与计数），同时也发布在 `/data/*.json` 供核对。

## 数据与刷新（重要：抓取不在 Uppcoder 里做）

抓取**继续留在本地、按原有定时任务跑**，Uppcoder 只做部署与公开托管：

- 免费服务：Pi 每天约 09:07 跑 `free-intel-refresh`（`scripts/fetch_free_intel.mjs`）→ `~/workspace/pi-agent-env/projects/free-intel-refresh/data/intel-data.json`
- 论坛羊毛：Node 脚本每天约 09:07 跑 `scripts/fetch-deals.mjs` → `~/workspace/pi-agent-env/projects/free-forum-deals/deals-data.json`
- 本站刷新：`scripts/refresh_site_data.py` 只做三件事——复制最新情报快照、把羊毛按 `posted_at` 过滤到近 7 天（无发布时间的 8 条 NodeSeek 帖子不猜日期，直接排除并计数）、重建 `public/index.html`。不抓取、不登录、不写源数据文件。

每日流程（外部触发，见 DEPLOY.md）：Pi 定时任务跑完 → 在本机跑 `python3 scripts/refresh_site_data.py` → `rsync` 到 Uppcoder → 重启 `server.py`（或让它直接读新文件——静态文件是现读的，不重启也生效）。Uppcoder 免费档没有定时任务，站内不设 cron。

## 本地运行

```bash
cd ~/workspace/uppcoder-free-resources
python3 scripts/refresh_site_data.py --snapshot-date 2026-11-10
python3 server.py            # 默认 http://127.0.0.1:8000
# 指定端口：PORT=8080 python3 server.py
```

## 数据口径（不要混报）

- 服务目录：80 条（免费 VPS 12、容器/PaaS 25、代码沙箱 15、LLM API 24、笔记本 4），另有聚合源 19 个、已关闭/需留意 5 条、未核实清单 21 条。
- 羊毛面板：源文件共 141 条；按 2026-11-03 至 2026-11-10 的 7 天窗口过滤后 133 条（免费白嫖 81、未分类 35、限免 12、低价优惠 5；LINUX DO 68、小众软件 59、V2EX 6）。8 条 NodeSeek 因发布时间无法核实而排除。
- 羊毛面板是论坛抓取的**过滤后全量集合**，与情报空间里 45 条人工核对版羊毛**口径不同**，不要混报。
- 卡片上的额度、绑卡、限制文字来自源数据原文；“未核实”表示还没找到官网或多源佐证，领之前请点进官网确认。

## 已知问题

- 2026-11-10：Uppcoder 网页 Terminal / VS Code / Files 与应用根地址多次返回纯文本 `404 page not found`，重启后仍如此；Python / pip / git 版本未通过网页终端核实。部署后请先通过 SSH 核实（见 DEPLOY.md），不要默认网页工具可用。
- 自定义域名是**后续步骤**，本次不配。用户域名托管在 Cloudflare；Uppcoder 文档说自定义域名是 plan 功能，Deploy €15 档列出 6 个域名，**Spark 免费档是否包含自定义域名未核实**，部署后先在 Stack 的域名设置里确认，再决定。

## 文件结构

```
uppcoder-free-resources/
├── README.md                     本文件
├── DEPLOY.md                     部署、公开、刷新、排障步骤
├── requirements.txt              无第三方依赖（标准库 only，仅作声明）
├── server.py                     标准库静态服务器，$PORT，默认 8000
├── data/                         本次快照（2026-11-10）：services.json / deals.json / meta.json
├── public/                       构建产物（部署时同步这部分）：index.html / data/*.json / assets/
├── public/assets/style.css       唯一 CSS，系统字体，无外部资源
├── public/assets/app.js          唯一 JS，只做本地筛选，不联网
└── scripts/
    ├── refresh_site_data.py      刷新入口：复制快照 → 过滤 7 天羊毛 → 重建页面
    └── build_site.py             预渲染 public/index.html
```
