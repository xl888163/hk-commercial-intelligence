"""Learn from the team's priority changes.

Each time someone changes an item's priority on the page, the Google Sheet
keeps the system level at that moment, the level they chose and the item's
features (sector, move type, access, deal size...). At every refresh we work
out, for each feature, how far the team moves items with that feature on
average, shrunk towards zero when there are few examples, and nudge the
default priority of similar items by that amount. The reason is shown on
every adjusted item.
"""
import json
import urllib.request

LEVELS = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
POINTS_PER_LEVEL = {"event": 2, "property": 3, "transaction": 2}
PRIOR = 3          # pseudo-examples of "no change" per feature
MIN_EXAMPLES = 2   # ignore features seen fewer times


def fetch_overrides(url, passcode):
    body = json.dumps({"action": "read", "passcode": passcode}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "text/plain;charset=utf-8"})
    with urllib.request.urlopen(req, timeout=60) as r:
        res = json.loads(r.read().decode())
    if not res.get("ok"):
        raise RuntimeError(res.get("error", "read failed"))
    tracker = res.get("tracker") or {}
    sample = next(iter(tracker.values()), {})
    print(f"Sheet check: {len(tracker)} tracked items; script returns priority field: {'priority' in sample}; "
          f"items with a saved priority: {sum(1 for t in tracker.values() if t.get('priority'))}; "
          f"with system level + features: {sum(1 for t in tracker.values() if t.get('systemLevel') and t.get('features'))}")
    rows = []
    for t in tracker.values():
        if t.get("priority") in LEVELS and t.get("systemLevel") in LEVELS and t.get("features"):
            rows.append({"user": t["priority"], "system": t["systemLevel"], "features": t["features"].split("|")})
    return rows


def fit(rows):
    stats = {}
    for r in rows:
        d = LEVELS[r["user"]] - LEVELS[r["system"]]
        for f in r["features"]:
            n, s = stats.get(f, (0, 0))
            stats[f] = (n + 1, s + d)
    return {f: v for f, v in stats.items() if v[0] >= MIN_EXAMPLES}


def apply(records, stats):
    for r in records:
        num = den = 0.0
        used = 0
        for f in r.get("features", []):
            if f in stats:
                n, s = stats[f]
                num += s
                den += n + PRIOR
                used += n
        if not den:
            continue
        shift = num / den
        pts = round(shift * POINTS_PER_LEVEL.get(r["kind"], 2))
        if pts:
            r["score"] += pts
            r["reasons"].append(f"Team feedback on similar items: {shift:+.1f} level on average across {used} re-ratings ({pts:+d})")
            high, med = r["thresholds"]
            r["level"] = "HIGH" if r["score"] >= high else "MEDIUM" if r["score"] >= med else "LOW"
    return records


def summary(stats, n_rows):
    top = sorted(((f, n, s / n) for f, (n, s) in stats.items()), key=lambda x: -abs(x[2]) * x[1])[:15]
    return {"overrides": n_rows, "features": [{"feature": f, "n": n, "avg": round(a, 2)} for f, n, a in top]}
