"""Commercial building transactions.

Two sources:
  * Centaline Commercial's public transaction register (oir.centanet.com):
    date, building, floor, unit, area, price/rent, and whether the record came
    from a Land Registry search or market news. The register does not name the
    buyer or tenant.
  * News headlines that name the buyer/tenant of an office, commercial or
    industrial deal (Google News HK editions, collected in property.py).
Records are copied as published; nothing is inferred about the parties.
"""
import datetime as dt
import html
import re
import concurrent.futures as cf
import time

from .net import fetch

BASE = "https://oir.centanet.com"
CATEGORIES = [("sale", "office"), ("lease", "office"), ("sale", "industrial"), ("lease", "industrial")]
MAX_PAGES = 40
REGION = {"hk-island": "HK Island", "kowloon": "Kowloon", "new-territories": "New Territories"}


def _clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def _rows(page_html):
    out = []
    for tr in re.findall(r'<tr class="list"[^>]*>(.*?)</tr>', page_html, re.S):
        tds = [_clean(t) for t in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        href = re.search(r'href="(/(?:en/)?transaction/[^"]+/detail/(\d+)/)', tr)
        if len(tds) >= 10 and href:
            out.append((tds, href.group(1), href.group(2)))
    return out


def _money(txt):
    """'Sold $105.87M' -> 105870000 ; 'Leased $50,000' -> 50000."""
    m = re.search(r"\$([\d,\.]+)\s*([MB]?)", txt)
    if not m:
        return None
    v = float(m.group(1).replace(",", ""))
    return v * (1e6 if m.group(2) == "M" else 1e9 if m.group(2) == "B" else 1)


def _area(txt):
    m = re.search(r"([\d,]+)", txt or "")
    return int(m.group(1).replace(",", "")) if m else None


def _category(deal, usage, cutoff):
    out = []
    with cf.ThreadPoolExecutor(max_workers=2) as ex:
        for page in range(1, MAX_PAGES + 1):
            f_en = ex.submit(fetch, f"{BASE}/en/transaction/{deal}/{usage}/", {"pageindex": page})
            f_zh = ex.submit(fetch, f"{BASE}/transaction/{deal}/{usage}/", {"pageindex": page})
            en, zh = _rows(f_en.result()), _rows(f_zh.result())
            zh_name = {r[2]: r[0][3] for r in zh}
            if not en:
                break
            oldest = None
            for tds, href, bid in en:
                date = dt.datetime.strptime(tds[0], "%d/%m/%Y").date()
                oldest = date if oldest is None or date < oldest else oldest
                if date < cutoff:
                    continue
                slug = href.split("/")[-4] if "/detail/" in href else ""
                region = next((v for k, v in REGION.items() if slug.startswith(k)), "")
                out.append({
                    "date": date, "deal": "Sale" if deal == "sale" else "Lease", "usage": tds[1],
                    "district": tds[2], "building": tds[3], "building_zh": zh_name.get(bid, ""),
                    "building_id": bid, "floor": "" if tds[4] == "--" else tds[4],
                    "unit": "" if tds[5] == "--" else tds[5], "area": _area(tds[6]), "area_txt": tds[6],
                    "price": _money(tds[7]), "price_txt": tds[7], "psf": tds[8], "record_source": tds[9],
                    "region": region, "url": BASE + href.split("?")[0],
                })
            if oldest and oldest < cutoff:
                break
            time.sleep(0.3)   # be polite to the site
    return out


def centaline(days=60):
    cutoff = dt.date.today() - dt.timedelta(days=days)
    with cf.ThreadPoolExecutor(max_workers=len(CATEGORIES)) as ex:
        parts = ex.map(lambda c: _category(c[0], c[1], cutoff), CATEGORIES)
    return [r for part in parts for r in part]


SOURCES = [("Centaline Commercial transaction register", centaline)]
