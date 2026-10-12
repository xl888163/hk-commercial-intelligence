"""Official-website watchlist for recurring events that venue calendars list late
or not at all (data-centre, art, high-net-worth). Each refresh fetches the
organiser's own page and uses the date printed there, near the named anchor
text. If no date can be read from the page, the event is left out - dates are
never assumed from previous years.

Add an entry: name, url, anchor (text next to the date on the page), venue,
category, organiser.
"""
import datetime as dt
import html
import re

from .net import fetch

WATCHLIST = [
    {"name": "Data Center Asia Hong Kong (powered by Data Center World)", "url": "https://www.datacenter-asia.com/hongkong/",
     "anchor": "July", "venue": "Hong Kong Convention and Exhibition Centre (HKCEC), Wan Chai",
     "category": "Data centre exhibition & conference", "organiser": "Informa Markets"},
    {"name": "Build4Asia", "url": "https://www.build4asia.com/",
     "anchor": "July", "venue": "Hong Kong Convention and Exhibition Centre (HKCEC), Wan Chai",
     "category": "Construction, building services & smart building exhibition", "organiser": "Messe Frankfurt"},
    {"name": "Art Basel Hong Kong", "url": "https://www.artbasel.com/hong-kong",
     "anchor": "", "venue": "Hong Kong Convention and Exhibition Centre (HKCEC), Wan Chai",
     "category": "International art fair (galleries, collectors, private banks)", "organiser": "Art Basel"},
    {"name": "Affordable Art Fair Hong Kong", "url": "https://affordableartfair.com/fairs/hong-kong/",
     "anchor": "May 2027|May 2026|Hong Kong Convention", "venue": "Hong Kong Convention and Exhibition Centre (HKCEC), Wan Chai",
     "category": "Art fair (galleries, collectors)", "organiser": "Affordable Art Fair"},
]

MON = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
DATE_RX = re.compile(
    r"(?P<d1>\d{1,2})\s*[-–]\s*(?P<d2>\d{1,2})\s+(?P<m>[A-Za-z]{3,9})\.?,?\s+(?P<y>20\d\d)"          # 7 – 8 July 2027
    r"|(?P<m2>[A-Za-z]{3,9})\.?\s+(?P<e1>\d{1,2})\s*[-–]\s*(?P<e2>\d{1,2}),?\s+(?P<y2>20\d\d)")       # March 25 – 27, 2027


def _text(page):
    t = re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", page, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(t))


def _dates(text, today):
    out = []
    for m in DATE_RX.finditer(text):
        if m.group("d1"):
            d1, d2, mon, y = m.group("d1"), m.group("d2"), m.group("m"), m.group("y")
        else:
            d1, d2, mon, y = m.group("e1"), m.group("e2"), m.group("m2"), m.group("y2")
        mi = MON.get(mon[:3].lower())
        if not mi:
            continue
        try:
            start, end = dt.date(int(y), mi, int(d1)), dt.date(int(y), mi, int(d2))
        except ValueError:
            continue
        if end >= today:
            out.append((m.start(), start, end))
    return out


def official_pages():
    today = dt.date.today()
    out = []
    for w in WATCHLIST:
        try:
            text = _text(fetch(w["url"]))
        except Exception:
            continue
        found = _dates(text, today)
        if w["anchor"]:
            anchors = [m.start() for m in re.finditer(w["anchor"], text)]
            found = [f for f in found if any(abs(f[0] - a) < 200 for a in anchors)] or []
        if not found:
            continue          # no date printed on the official page: leave it out
        _, start, end = min(found, key=lambda f: f[1])
        out.append({
            "name": w["name"], "start": start, "end": end, "venue": w["venue"], "organiser": w["organiser"],
            "access": "Not stated in listing", "audience": w["category"], "category": w["category"],
            "url": w["url"], "source": "Official event website (date read from page)", "source_url": w["url"],
            "official": True,
        })
    return out
