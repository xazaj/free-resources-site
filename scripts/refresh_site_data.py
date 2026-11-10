#!/usr/bin/env python3
"""Refresh the site data from the Pi-produced JSON outputs and rebuild.

This script does NO fetching / scraping. Fetching stays where it already
is, on schedule, outside Uppcoder:
  - free-intel-refresh: Pi runs scripts/fetch_free_intel.mjs daily ~09:07
    -> <pi>/projects/free-intel-refresh/data/intel-data.json
  - forum deals: node scripts/fetch-deals.mjs daily ~09:07
    -> <pi>/projects/free-forum-deals/deals-data.json

This script only: (1) copies the latest intel snapshot, (2) filters deals
to the last 7 days by posted_at (items with no posted_at are excluded
and counted, not guessed), (3) writes data/*.json + meta.json, (4) rebuilds
public/index.html via build_site.py.

Usage (from the repo root, on the machine that holds the Pi outputs):
    python3 scripts/refresh_site_data.py [--snapshot-date YYYY-MM-DD]
    # then deploy: see DEPLOY.md (rsync public/ + data/ to Uppcoder via SSH,
    # or rsync the whole repo minus .git; no cron inside Uppcoder)

Exit code 0 on success; prints exact counts for the daily log.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

INTEL_SRC = os.environ.get(
    "INTEL_SRC",
    os.path.expanduser("~/workspace/pi-agent-env/projects/free-intel-refresh/data/intel-data.json"))
DEALS_SRC = os.environ.get(
    "DEALS_SRC",
    os.path.expanduser("~/workspace/pi-agent-env/projects/free-forum-deals/deals-data.json"))
DEALS_STATE = os.environ.get(
    "DEALS_STATE",
    os.path.expanduser("~/workspace/pi-agent-env/projects/free-forum-deals/state.json"))


def parse_dt(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except ValueError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot-date", default=datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d"),
                    help="Snapshot date (Asia/Kuala_Lumpur, default today).")
    args = ap.parse_args()

    intel = json.load(open(INTEL_SRC, encoding="utf-8"))
    deals_raw = json.load(open(DEALS_SRC, encoding="utf-8"))
    n_services = sum(len(c["services"]) for c in intel["categories"])

    # 7-day window: snapshot date minus 7 days at 00:00 (+08) up to end of
    # snapshot date. E.g. snapshot 2026-11-10 -> cutoff 2026-11-03 00:00+08.
    tz8 = timezone(timedelta(hours=8))
    end = datetime.fromisoformat(args.snapshot_date + "T23:59:59+08:00")
    cutoff = datetime.fromisoformat(args.snapshot_date + "T00:00:00+08:00") - timedelta(days=7)
    kept, no_date = [], 0
    for d in deals_raw:
        dt = parse_dt(d.get("posted_at"))
        if dt is None:
            no_date += 1
            continue
        if dt >= cutoff:
            kept.append(d)
    kept.sort(key=lambda d: d.get("posted_at", ""), reverse=True)

    deals_last_run = ""
    try:
        state = json.load(open(DEALS_STATE, encoding="utf-8"))
        runs = [v.get("last_run", "") for v in state.get("sources", {}).values() if v.get("last_run")]
        deals_last_run = max(runs) if runs else ""
    except Exception:
        pass

    meta = {
        "snapshot_date": args.snapshot_date,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "intel_generated_at": intel.get("meta", {}).get("generated_at", ""),
        "intel_run_id": intel.get("meta", {}).get("run_id", ""),
        "deals_last_run": deals_last_run,
        "counts": {
            "services": n_services,
            "deals_total_in_file": len(deals_raw),
            "deals_in_7d": len(kept),
            "deals_excluded_no_date": no_date,
            "aggregators": len(intel.get("aggregators", [])),
            "retired": len(intel.get("retired", [])),
            "unverified": len(intel.get("unverified", [])),
        },
        "window": {"cutoff": cutoff.isoformat(), "end": end.isoformat()},
        "note": ("Snapshot of Pi-produced outputs dated 2026-11-10 unless re-run. "
                 "Deals are the filtered full set from deals-data.json; the 45-item "
                 "human-checked set in the intel space is a different cut — do not mix."),
    }

    data_dir = os.path.join(ROOT, "data")
    os.makedirs(data_dir, exist_ok=True)
    json.dump(intel, open(os.path.join(data_dir, "services.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(kept, open(os.path.join(data_dir, "deals.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(meta, open(os.path.join(data_dir, "meta.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    import build_site
    result = build_site.build()
    print(f"refresh done snapshot={args.snapshot_date} "
          f"services={result['services']} deals_file={len(deals_raw)} "
          f"deals_7d={len(kept)} deals_no_date_excluded={no_date} "
          f"window_from={cutoff.date()} to={end.date()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
