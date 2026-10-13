"""HKEXnews filings that name the buyer / tenant of a Hong Kong property.

Listed companies must announce notifiable and connected transactions. When the
deal is a purchase, sale, tenancy or lease of Hong Kong premises, the
announcement states the parties, the exact address and the price or rent.
Text is read from the filing itself; fields that cannot be read are left empty.
PDF reading needs the `pypdf` package (installed in the GitHub workflow); without
it this source reports itself unavailable and the rest of the refresh carries on.
"""
import concurrent.futures as cf
import datetime as dt
import html
import os
import io
import json
import logging
import re
import urllib.parse

from .net import UA

SEARCH = "https://www1.hkexnews.hk/search/titleSearchServlet.do"
CATEGORIES = [("6", "16200"), ("6", "16300"), ("1", "11200"), ("1", "11300")]   # discloseable, major, connected, continuing connected
TITLE_IN = re.compile(r"PROPERT|PREMISES|OFFICE|TENANC|LEASE AGREEMENT|LEASE OF|LEASEBACK|\bSITE\b|FLOOR|\bUNITS?\b|"
                      r"BUILDING|WAREHOUSE|SHOP|WORKSHOP", re.I)
TITLE_OUT = re.compile(r"FINANCE LEASE|AIRCRAFT|VESSEL|MACHINERY|EQUIPMENT|SHIP|\bPRC\b|SHANGHAI|BEIJING|SHENZHEN|GUANGZHOU|"
                       r"CHINA|MANILA|SINGAPORE|LAND PARCEL|LAND USE|EQUITY INTEREST|SHARES|LOAN|FUND|MANAGEMENT SERVICES|"
                       r"PROPERTY MANAGEMENT|PROPERTY SERVICES|DATA CENTER RACKS|TERMINATION|DELAY IN DESPATCH|SUPPLEMENTAL", re.I)
INCOMING = {"purchaser": "Buyer", "tenant": "Tenant", "lessee": "Tenant", "licensee": "Licensee"}
OUTGOING = {"vendor": "Seller", "landlord": "Landlord", "lessor": "Landlord", "licensor": "Licensor"}
COMPANY = r"([A-Z][A-Za-z0-9&,.()'’\- ]{2,90}?(?:Limited|Ltd\.?|Company|Corporation|Incorporated|Inc\.?|LLC|L\.P\.|Bank|Partnership))"
ADDR_RX = re.compile(r"((?:Flat|Flats|Unit|Units|Shop|Shops|Office|Offices|Suite|Suites|Room|Rooms|Workshop|Workshops|Portion|"
                     r"Whole|The whole|Car Parking|Ground Floor|G/F|\d+(?:st|nd|rd|th)\s+Floor|\d+/F)[^;:“”\"]{3,220}?Hong Kong)\b")
AREA_RX = re.compile(r"(?:gross|saleable)\s+floor\s+area\s+of\s+(?:approximately\s+)?([\d,]+)\s*(?:sq\.?\s*ft|square\s+feet)", re.I)
MONEY_RX = re.compile(r"HK\$\s?([\d,]+(?:\.\d+)?)\s*(million)?", re.I)


def _get(url, params=None, binary=False):
    import urllib.request
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://www1.hkexnews.hk/search/titlesearch.xhtml"})
    with urllib.request.urlopen(req, timeout=40) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "replace")


def _list(days):
    today = dt.date.today()
    rows = []
    for grp, code in CATEGORIES:
        res = json.loads(_get(SEARCH, {
            "sortDir": 0, "sortByOptions": "DateTime", "category": 0, "market": "SEHK", "stockId": -1,
            "documentType": -1, "fromDate": (today - dt.timedelta(days=days)).strftime("%Y%m%d"),
            "toDate": today.strftime("%Y%m%d"), "title": "", "searchType": 1, "t1code": 10000,
            "t2Gcode": grp, "t2code": code, "rowRange": 500, "lang": "E"}))
        rows += json.loads(res.get("result") or "null") or []
    seen, out = set(), []
    for r in rows:
        title = html.unescape(r.get("TITLE", "")).replace("<br/>", " ")
        if r["FILE_LINK"] in seen or not TITLE_IN.search(title) or TITLE_OUT.search(title):
            continue
        seen.add(r["FILE_LINK"])
        out.append({"date": dt.datetime.strptime(r["DATE_TIME"][:10], "%d/%m/%Y").date(), "title": title,
                    "company": html.unescape(r["STOCK_NAME"]).split("<br/>")[0],
                    "url": "https://www1.hkexnews.hk" + r["FILE_LINK"]})
    return out


def _text(url):
    raw = _get(url, binary=True)
    if url.lower().endswith(".pdf"):
        import pypdf
        logging.getLogger("pypdf").setLevel(logging.ERROR)
        pages = pypdf.PdfReader(io.BytesIO(raw)).pages[:8]
        t = " ".join((p.extract_text() or "") for p in pages)
    else:
        t = re.sub(r"<[^>]+>", " ", raw.decode("utf-8", "replace"))
    return re.sub(r"\s+", " ", html.unescape(t)).replace("’", "'")


NAME_RX = re.compile(r"((?:(?:[A-Z][A-Za-z0-9&'.\-]*|&|\([A-Z]{1,4}\))\s+){1,9}(?:Limited|Ltd\.?|Company|Corporation|Incorporated|Inc\.?|LLC|Bank|Partnership))")
GENERIC = re.compile(r"^(?:The\s+)?(?:Company|Board|Group|Purchaser|Vendor|Tenant|Landlord|Exchange)$|Stock Exchange|Listing Rules", re.I)


def _clean_name(raw, listed):
    names = [n.strip() for n in NAME_RX.findall(raw or "")]
    name = names[-1] if names else ""
    name = re.sub(r"^(?:and|The|For|On|As|Of)\s+", "", name).strip()
    if not name or GENERIC.search(name) or len(name) < 6:
        return f"{listed.title()} (listed company)" if re.search(r"\bthe company\b", raw or "", re.I) else ""
    return name


def _usage(addr):
    if re.search(r"\bshops?\b|shopping|mall|store", addr, re.I):
        return "Retail"
    if re.search(r"workshop|industrial|factory|godown|warehouse", addr, re.I):
        return "Industrial"
    return "Office / commercial"


def _parse(doc, text):
    parties = {}
    for m in re.finditer(r"\b(Purchaser|Vendor|Landlord|Tenant|Lessee|Lessor|Licensee|Licensor)s?\s*[:：]\s*" + COMPANY, text):
        parties.setdefault(m.group(1).lower(), m.group(2).strip(" ,"))
    for m in re.finditer(COMPANY + r",?[^;:“”]{0,120}?\bas (?:the )?(purchaser|vendor|landlord|tenant|lessee|lessor|licensee|licensor)\b", text, re.I):
        parties.setdefault(m.group(2).lower(), m.group(1).strip(" ,"))
    for m in re.finditer(r"“(Purchaser|Vendor|Landlord|Tenant|Lessee|Lessor)”\s+" + COMPANY, text):
        parties.setdefault(m.group(1).lower(), m.group(2).strip(" ,"))
    parties = {k: _clean_name(v, doc["company"]) for k, v in parties.items()}
    parties = {k: v for k, v in parties.items() if v}
    inc = next(((INCOMING[k], v) for k, v in parties.items() if k in INCOMING), None)
    if not inc:
        return None
    addr = None
    for m in ADDR_RX.finditer(text):
        a = re.split(r"‘‘|''|“|Stock Exchange", m.group(1))[0].strip(" ,")
        if len(a) < 220 and not re.search(r"PRC|People's Republic|registered office|principal place of business", a, re.I):
            addr = a
            break
    if not addr:
        return None
    out = next(((OUTGOING[k], v) for k, v in parties.items() if k in OUTGOING), (None, ""))
    lease = inc[0] in ("Tenant", "Licensee")
    money, per_month = None, False
    m = (re.search(r"(?:monthly\s+)?rent[^.]{0,160}?HK\$\s?[\d,\.]+(?:\s*million)?", text, re.I) if lease
         else re.search(r"consideration[^.]{0,160}?HK\$\s?[\d,\.]+(?:\s*million)?", text, re.I))
    if m:
        mm = MONEY_RX.search(m.group(0))
        if mm:
            money = float(mm.group(1).replace(",", "")) * (1e6 if mm.group(2) else 1)
            per_month = bool(re.search(r"month", m.group(0), re.I))
    area = AREA_RX.search(text)
    return {
        "date": doc["date"], "deal": "Lease" if lease else "Sale", "party": inc[1], "party_role": inc[0],
        "counterparty": out[1], "counterparty_role": out[0] or "", "listed_company": doc["company"],
        "premises": addr, "price": money, "per_month": per_month, "usage": _usage(addr), "area": int(area.group(1).replace(",", "")) if area else None,
        "url": doc["url"], "title": doc["title"],
    }


CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "hkex_cache.json")


def filings(days=120, max_docs=150):
    """Parsed filings; each document is read once and remembered in data/hkex_cache.json."""
    try:
        with open(CACHE, encoding="utf-8") as f:
            cache = json.load(f)
    except (OSError, ValueError):
        cache = {}
    docs = _list(days)[:max_docs]
    todo = [d for d in docs if d["url"] not in cache]
    try:
        import pypdf  # noqa: F401
    except ImportError:
        if todo:
            raise RuntimeError("pypdf not installed")

    def work(d):
        try:
            rec = _parse(d, _text(d["url"]))
        except Exception:
            return d["url"], "error"
        if rec:
            rec = dict(rec, date=rec["date"].isoformat())
        return d["url"], rec

    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        for url, rec in ex.map(work, todo):
            if rec != "error":
                cache[url] = rec
    keep = {d["url"] for d in docs}
    cache = {u: v for u, v in cache.items() if u in keep}
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)
    out = []
    for d in docs:
        rec = cache.get(d["url"])
        if rec:
            out.append(dict(rec, date=dt.date.fromisoformat(rec["date"])))
    return out
