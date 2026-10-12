#!/usr/bin/env python3
"""Hong Kong Commercial Intelligence - fetch, verify, score and build the dashboard.

Usage:
    python3 run.py              # refresh everything and open the dashboard
    python3 run.py --no-open    # refresh without opening a browser
    python3 run.py --days 60    # property-news look-back window (default 90)
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import json
import os
import sys
import time
import webbrowser

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from intel import analyze, events, property as prop, render  # noqa: E402
from intel.taxonomy import AREA_NAMES, SECTOR_NAMES  # noqa: E402

DATA = os.path.join(ROOT, "data")
HKT = dt.timezone(dt.timedelta(hours=8))


def collect(sources, label):
    results, health = [], []
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(fn): name for name, fn in sources}
        for f in cf.as_completed(futs):
            name = futs[f]
            try:
                items = f.result()
                results.extend(items)
                health.append({"group": label, "name": name, "ok": True, "count": len(items)})
                print(f"  ✓ {name}: {len(items)}")
            except Exception as e:  # keep going if one source is down
                health.append({"group": label, "name": name, "ok": False, "count": 0, "error": repr(e)[:200]})
                print(f"  ✗ {name}: {e!r}")
    return results, sorted(health, key=lambda h: h["name"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-open", action="store_true")
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--public", action="store_true", help="also build the public site in docs/index.html")
    ap.add_argument("--no-snapshot", action="store_true", help="skip saving a dated snapshot")
    args = ap.parse_args()

    os.makedirs(os.path.join(DATA, "snapshots"), exist_ok=True)
    now = dt.datetime.now(HKT)
    today = now.date()
    t0 = time.time()

    print("Fetching industry events…")
    raw_ev, h1 = collect(events.SOURCES, "Events")
    print("Fetching property movements…")
    raw_pr, h2 = collect(prop.sources(args.days), "Property")

    ev = analyze.build_events(raw_ev, today)
    pr = analyze.build_property(raw_pr, today, args.days)

    # keep a deal's id stable when new articles join its group (PIC records key on it)
    map_path = os.path.join(DATA, "id_map.json")
    try:
        with open(map_path, encoding="utf-8") as f:
            id_map = json.load(f)
    except (OSError, ValueError):
        id_map = {}
    for rec in pr:
        prev = next((id_map[s["url"]] for s in rec["sources"] if s["url"] in id_map), None)
        if prev:
            rec["id"] = prev
        for s in rec["sources"]:
            id_map[s["url"]] = rec["id"]
    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(id_map, f)

    # flag items not seen on previous runs
    hist_path = os.path.join(DATA, "history.json")
    try:
        with open(hist_path, encoding="utf-8") as f:
            history = json.load(f)
    except (OSError, ValueError):
        history = {}
    first_run = not history
    stamp = now.isoformat(timespec="seconds")
    for rec in ev + pr:
        rec["first_seen"] = history.setdefault(rec["id"], stamp)
        rec["is_new"] = (not first_run) and rec["first_seen"] == stamp
    with open(hist_path, "w", encoding="utf-8") as f:
        json.dump(history, f)

    payload = {
        "generated": stamp, "property_days": args.days,
        "events": sorted(ev, key=lambda e: (e["start"], -e["score"])),
        "property": sorted(pr, key=lambda p: p["date"], reverse=True),
        "health": h1 + h2, "sectors": SECTOR_NAMES, "areas": AREA_NAMES,
    }
    with open(os.path.join(DATA, "latest.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    if not args.no_snapshot:
        with open(os.path.join(DATA, "snapshots", now.strftime("%Y-%m-%d_%H%M") + ".json"), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)

    out = render.write(payload, os.path.join(ROOT, "dashboard.html"))
    if args.public:
        try:
            with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as f:
                config = json.load(f)
        except (OSError, ValueError):
            config = {}
        out = render.write(payload, os.path.join(ROOT, "docs", "index.html"), "public.html", config)
    hi = sum(1 for r in ev + pr if r["level"] == "HIGH")
    bad = [h["name"] for h in h1 + h2 if not h["ok"]]
    print(f"\nDone in {time.time() - t0:.0f}s: {len(ev)} events, {len(pr)} property movements, {hi} HIGH opportunities.")
    if bad:
        print("Sources unavailable this run: " + "; ".join(bad))
    print("Dashboard: " + out)
    if not args.no_open:
        webbrowser.open("file://" + out)


if __name__ == "__main__":
    main()
