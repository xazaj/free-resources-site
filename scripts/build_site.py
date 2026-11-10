#!/usr/bin/env python3
"""Build public/index.html (pre-rendered) from data/*.json.

Reads data/services.json (full intel-data.json snapshot), data/deals.json
(7-day filtered deals), writes public/index.html + copies the JSON files
to public/data/ so the page is usable even with JS disabled: all cards
are in the HTML; the small JS in public/assets/app.js only hides/shows
cards for search/filters. No external fonts, no CDN, no tracking.
"""
import html
import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
PUBLIC = os.path.join(ROOT, "public")


def esc(s):
    return html.escape(str(s or ""), quote=True)


def card_class(verify):
    v = (verify or "")
    if v.startswith("官网已核实"):
        return "verified"
    if "多源一致" in v:
        return "multi"
    if "未核实" in v or "冲突" in v:
        return "unverified"
    return "third"


def needs_card(credit):
    c = (credit or "").strip()
    if c.startswith("是") or c.startswith("须") or "须绑卡" in c or "须订阅" in c:
        return "yes"
    if c.startswith("否") or "无需绑卡" in c or "无需" in c[:6]:
        return "no"
    return "unknown"


def card_label(credit):
    c = (credit or "").strip()
    return {"yes": "需绑卡", "no": "无需绑卡", "unknown": "绑卡未明"}.get(needs_card(c), "绑卡未明")


def service_card(s):
    return f"""<article class="card svc" data-cat="{esc(s.get('category',''))}" data-card="{needs_card(s.get('credit_card'))}" data-verify="{card_class(s.get('verify_status'))}" data-name="{esc(s.get('name',''))}">
  <div class="card-top"><span class="pill {card_class(s.get('verify_status'))}">{esc(s.get('verify_status',''))}</span><span class="pill cardneed">{card_label(s.get('credit_card'))}</span></div>
  <h3><a href="{esc(s.get('url','#'))}" target="_blank" rel="noopener">{esc(s.get('name',''))}</a></h3>
  <p class="tier">{esc(s.get('free_tier',''))}</p>
  <p class="limits"><span>限制</span>{esc(s.get('limits',''))}</p>
  <p class="meta-line">绑卡：{esc(s.get('credit_card','—'))} · 核对：{esc(s.get('checked_date','—'))}</p>
</article>"""


def deal_card(d):
    posted = (d.get("posted_at") or "")[:10]
    req = d.get("requires_card")
    req_txt = "需绑卡" if req is True else ("无需绑卡" if req is False else "绑卡未明")
    notes = f"<p class=\"notes\">{esc(d.get('notes',''))}</p>" if d.get("notes") else ""
    exp = f" · 截止 {esc(d.get('expires_at',''))[:10]}" if d.get("expires_at") else ""
    return f"""<article class="card deal" data-cat="{esc(d.get('category',''))}" data-src="{esc(d.get('source',''))}" data-name="{esc(d.get('title',''))}">
  <div class="card-top"><span class="pill dealcat">{esc(d.get('category',''))}</span><span class="pill src">{esc(d.get('source',''))}</span><span class="pill cardneed">{req_txt}</span></div>
  <h3><a href="{esc(d.get('url','#'))}" target="_blank" rel="noopener">{esc(d.get('title',''))}</a></h3>
  <p class="tier">{esc(d.get('summary',''))}</p>
  {notes}
  <p class="meta-line">{posted}{exp}</p>
</article>"""


def build():
    intel = json.load(open(os.path.join(DATA, "services.json"), encoding="utf-8"))
    deals = json.load(open(os.path.join(DATA, "deals.json"), encoding="utf-8"))
    meta = json.load(open(os.path.join(DATA, "meta.json"), encoding="utf-8"))

    cats = intel["categories"]
    total_services = sum(len(c["services"]) for c in cats)
    no_card = sum(1 for c in cats for s in c["services"] if needs_card(s.get("credit_card")) == "no")
    verified = sum(1 for c in cats for s in c["services"] if card_class(s.get("verify_status")) in ("verified", "multi"))

    # ---- services sections ----
    svc_html = []
    for c in cats:
        cards = "".join(service_card(s) for s in c["services"])
        svc_html.append(f"""<section class="cat-block" id="cat-{esc(c['id'])}">
  <div class="cat-head"><h3>{esc(c['name'])}</h3><span class="count">{len(c['services'])} 条</span></div>
  <div class="grid">{cards}</div>
</section>""")

    # ---- deals ----
    deal_html = "".join(deal_card(d) for d in deals)
    from collections import Counter
    dcat = Counter(d.get("category") for d in deals)
    dsrc = Counter(d.get("source") for d in deals)

    # ---- aggregators / retired / unverified ----
    agg = "".join(
        f"<li><a href=\"{esc(a.get('url','#'))}\" target=\"_blank\" rel=\"noopener\">{esc(a.get('name',''))}</a> <span>{esc(a.get('content',''))[:90]}</span></li>"
        for a in intel.get("aggregators", []))
    ret = "".join(
        f"<li><strong>{esc(r.get('name',''))}</strong> — {esc(r.get('status',''))}：{esc(r.get('note',''))}</li>"
        for r in intel.get("retired", []))
    unv = "".join(f"<li>{esc(u.get('name',''))} <span>（{esc(u.get('category',''))}）</span></li>"
                  for u in intel.get("unverified", []))

    cat_opts = "".join(f"<option value=\"{esc(c['id'])}\">{esc(c['name'])}</option>" for c in cats)
    dcat_opts = "".join(f"<option value=\"{esc(k)}\">{esc(k)}（{v}）</option>" for k, v in sorted(dcat.items()))
    dsrc_opts = "".join(f"<option value=\"{esc(k)}\">{esc(k)}（{v}）</option>" for k, v in sorted(dsrc.items()))

    html_out = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>免费资源站 — 免费 VPS / PaaS / 沙箱 / LLM / 笔记本 + 论坛羊毛</title>
<meta name="description" content="每天刷新的免费资源目录：80 条免费服务与近 7 天论坛羊毛，只收录免费档，绑卡与核实状态写清楚。">
<link rel="stylesheet" href="/assets/style.css">
</head>
<body>
<header class="top"><div class="wrap top-in">
  <a class="logo" href="/">免费资源站 <span>Free Resources</span></a>
  <nav><a href="#services">免费服务目录</a><a href="#deals">论坛羊毛</a><a href="#notes">说明与来源</a></nav>
</div></header>

<main>
<section class="hero"><div class="wrap">
  <p class="eyebrow">每天刷新 · 只收录免费档 · 绑卡与核实状态写清楚</p>
  <h1>免费的云服务与羊毛，<br>先看清楚，再去领。</h1>
  <p class="lede">80 条免费 VPS、容器 / PaaS、代码沙箱、LLM API 与笔记本算力，加上近 7 天论坛里的免费白嫖、限免与低价优惠。额度、绑卡要求、限制与核实状态都写在卡片上，不确定的就标“未核实”，不替你做决定。</p>
  <div class="hero-cta"><a class="btn primary" href="#services">浏览免费服务</a><a class="btn" href="#deals">看看今天的羊毛</a></div>
  <div class="stats">
    <div><strong>{total_services}</strong><span>免费服务</span></div>
    <div><strong>{len(deals)}</strong><span>近 7 天羊毛</span></div>
    <div><strong>{no_card}</strong><span>明确无需绑卡</span></div>
    <div><strong>{verified}</strong><span>官网 / 多源已核实</span></div>
  </div>
  <p class="updated">数据快照：{esc(meta.get('snapshot_date',''))} · 服务数据更新 {esc(meta.get('intel_generated_at',''))} · 羊毛抓取 {esc(meta.get('deals_last_run',''))} · 下次刷新约每天 09:07（+08）</p>
</div></section>

<section id="services" class="wrap section">
  <div class="sec-head"><h2>免费服务目录</h2><p>按类别浏览。下面所有条目都来自每日核对的情报数据，卡片上写的是原文额度与限制，改动以官网为准。</p></div>
  <div class="toolbar">
    <input id="q" type="search" placeholder="搜索服务名、额度、限制…" aria-label="搜索服务">
    <select id="f-cat" aria-label="按类别筛选"><option value="">全部类别</option>{cat_opts}</select>
    <select id="f-card" aria-label="按绑卡筛选"><option value="">绑卡：全部</option><option value="no">无需绑卡</option><option value="yes">需绑卡</option><option value="unknown">绑卡未明</option></select>
    <select id="f-verify" aria-label="按核实筛选"><option value="">核实：全部</option><option value="verified">官网已核实</option><option value="multi">多源一致</option><option value="third">仅见第三方</option><option value="unverified">未核实 / 冲突</option></select>
    <span id="svc-count" class="result-count"></span>
  </div>
  {''.join(svc_html)}
</section>

<section id="deals" class="wrap section">
  <div class="sec-head"><h2>论坛羊毛 · 近 7 天</h2><p>来自 LINUX DO、小众软件、V2EX 与 NodeSeek 的帖子。羊毛面板是过滤后的全量集合，与人工核对版口径不同（见下方说明）。抽奖类已注明“非必得”，过期、领完的会剔除。</p></div>
  <div class="toolbar">
    <input id="q2" type="search" placeholder="搜索羊毛标题…" aria-label="搜索羊毛">
    <select id="f-dcat" aria-label="按羊毛类别筛选"><option value="">全部类别</option>{dcat_opts}</select>
    <select id="f-dsrc" aria-label="按来源筛选"><option value="">全部来源</option>{dsrc_opts}</select>
    <span id="deal-count" class="result-count"></span>
  </div>
  <div class="grid">{deal_html}</div>
  <p class="fineprint">近 7 天共 {len(deals)} 条：{', '.join(f'{esc(k)} {v}' for k, v in sorted(dcat.items()))}。来源：{', '.join(f'{esc(k)} {v}' for k, v in sorted(dsrc.items()))}。8 条 NodeSeek 帖子因发布时间无法核实（只有 Wayback 快照日期），未计入这 7 天列表。</p>
</section>

<section id="notes" class="wrap section">
  <div class="sec-head"><h2>说明与来源</h2></div>
  <div class="notes-grid">
    <div class="note-card"><h3>口径说明</h3>
      <p>服务目录 80 条来自每日情报核对；羊毛面板是论坛抓取的过滤后全量集合（本次快照 141 条入库，133 条落在近 7 天），与情报空间里 45 条人工核对版羊毛口径不同，不要混报。</p>
      <p>“未核实”不是“假”，是还没找到官网或多源佐证；领之前请自己点进官网确认一次额度与绑卡要求。</p></div>
    <div class="note-card"><h3>信息聚合源（{len(intel.get('aggregators', []))} 个）</h3><ul class="plain">{agg}</ul></div>
    <div class="note-card"><h3>已关闭 / 需留意（{len(intel.get('retired', []))} 条）</h3><ul class="plain">{ret}</ul></div>
    <div class="note-card"><h3>未核实清单（{len(intel.get('unverified', []))} 条）</h3><ul class="plain">{unv}</ul></div>
  </div>
  <p class="fineprint">数据来源：Pi 每日抓取与核对（free-intel-refresh，约 09:07）与论坛抓取脚本（fetch-deals.mjs，约 09:07），本站只做展示与筛选，不重新抓取。原始数据见站内 <a href="/data/services.json">services.json</a>、<a href="/data/deals.json">deals.json</a>。本站托管在 Uppcoder 免费 Spark Stack 上（2GB 内存 / 2GB 磁盘 / 每天 500 CPU 秒），纯静态页面，无数据库、无外部字体与 CDN。</p>
</section>
</main>

<footer><div class="wrap"><p>免费资源站 · 数据每日刷新，额度以各服务官网为准 · 领之前请确认绑卡与条款</p></div></footer>
<script src="/assets/app.js" defer></script>
</body>
</html>
"""
    os.makedirs(PUBLIC, exist_ok=True)
    with open(os.path.join(PUBLIC, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_out)
    os.makedirs(os.path.join(PUBLIC, "data"), exist_ok=True)
    for name in ("services.json", "deals.json", "meta.json"):
        shutil.copyfile(os.path.join(DATA, name), os.path.join(PUBLIC, "data", name))
    print(f"built public/index.html: services={total_services} deals={len(deals)} "
          f"aggregators={len(intel.get('aggregators', []))} retired={len(intel.get('retired', []))} "
          f"unverified={len(intel.get('unverified', []))}")
    return {"services": total_services, "deals": len(deals)}


if __name__ == "__main__":
    build()
