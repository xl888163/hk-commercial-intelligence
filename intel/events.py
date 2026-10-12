"""Event collectors. Each returns a list of raw event dicts taken verbatim
from an official listing (venue, government agency or chamber of commerce)."""
import datetime as dt
import html
import re

from .net import fetch, fetch_json

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def clean(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def _mon(s):
    return MONTHS.get(s[:3].lower())


def parse_range(text):
    """Parse the date formats used by the listings below -> (start, end) dates."""
    t = clean(text)
    # 13/10/2026 - 16/10/2026  |  13/10/2026
    m = re.findall(r"(\d{1,2})/(\d{1,2})/(\d{4})", t)
    if m:
        d = [dt.date(int(y), int(mo), int(da)) for da, mo, y in m]
        return d[0], d[-1]
    # 23 Sep - 12 Oct, 2026 | 06 - 21 Oct, 2026 | 13 Oct 2026 | 14 October 2026
    m = re.search(r"(\d{1,2})\s*([A-Za-z]{3,9})?\s*[-–]\s*(\d{1,2})\s+([A-Za-z]{3,9}),?\s+(\d{4})", t)
    if m:
        d1, m1, d2, m2, y = m.groups()
        end = dt.date(int(y), _mon(m2), int(d2))
        start_m = _mon(m1) if m1 else _mon(m2)
        sy = int(y) - 1 if start_m > end.month else int(y)
        return dt.date(sy, start_m, int(d1)), end
    m = re.search(r"(\d{1,2})\s+([A-Za-z]{3,9}),?\s+(\d{4})", t)
    if m and _mon(m.group(2)):
        d = dt.date(int(m.group(3)), _mon(m.group(2)), int(m.group(1)))
        return d, d
    return None, None


# ---------------------------------------------------------------------------
def hkcec(max_pages=12):
    """Hong Kong Convention and Exhibition Centre event calendar (next 12 months)."""
    out, seen = [], set()
    base = "https://www.hkcec.com/en/event-calendar"
    for page in range(max_pages):
        h = fetch(base, {"filter_keyword": "", "field_event_start_date_value": "+0 day",
                         "field_event_end_date_value": "+1 year", "page": page})
        blocks = re.split(r'<div class="event-table">', h)[1:]
        new = 0
        for b in blocks:
            title_html = re.search(r'<div class="event-title">(.*?)</div>', b, re.S)
            if not title_html:
                continue
            parts = re.split(r"<br\s*/?>", title_html.group(1))
            name = clean(parts[0])
            start, end = parse_range(parts[-1] if len(parts) > 1 else "")
            key = (name, start)
            if key in seen or not start:
                continue
            seen.add(key)
            new += 1
            link = re.search(r'<a class="event_img" href="([^"]+)"', b)
            nature = clean(" ".join(re.findall(r'<div class="event-nature">(.*?)</div>', b, re.S)))
            org = re.search(r'<div class="event-organiser">(.*?)</div>', b, re.S)
            org_url = re.search(r'<div class="event-organiser">.*?href="([^"]+)"', b, re.S)
            phone = re.search(r'event-phone[^"]*">.*?<span>(.*?)</span>', b, re.S)
            email = re.search(r'event-email[^"]*">.*?<span>(.*?)</span>', b, re.S)
            out.append({
                "name": name, "start": start, "end": end,
                "venue": "Hong Kong Convention and Exhibition Centre (HKCEC), Wan Chai",
                "organiser": clean(org.group(1)) if org else "",
                "organiser_url": html.unescape(org_url.group(1)) if org_url else "",
                "contact_phone": clean(phone.group(1)) if phone else "",
                "contact_email": clean(email.group(1)) if email else "",
                "access": nature or "Not stated in listing",
                "audience": nature or "",
                "category": "Exhibition / conference",
                "url": html.unescape(link.group(1)) if link else base,
                "source": "HKCEC event calendar", "source_url": base, "official": True,
            })
        if not new:
            break
    return out


AWE_KEEP = {"exhibition", "conference", "meeting", "education", "private event"}


def asiaworld_expo():
    """AsiaWorld-Expo upcoming events (exhibitions/conferences; concerts excluded)."""
    url = "https://www.asiaworld-expo.com/en-us/whats-on/upcoming-events/"
    h = fetch(url)
    out = []
    for cat, s, e, body in re.findall(
            r'data-cat="([^"]*)" data-start="([^"]*)" data-end="([^"]*)">(.*?)event-filter-tab-tool', h, re.S):
        cats = {c for c in cat.split("|") if c}
        if not cats & AWE_KEEP:
            continue
        name = clean(re.search(r"<h3>(.*?)</h3>", body, re.S).group(1))
        if re.search(r"CANCELLED|POSTPONED", name, re.I):
            continue
        start = dt.datetime.strptime(s, "%m/%d/%Y").date()
        end = dt.datetime.strptime(e, "%m/%d/%Y").date()
        href = re.search(r'href="([^"]+)"', body)
        halls = re.findall(r'<div class="event-filter-tab-location">(.*?)</div>', re.sub(r"<!--.*?-->", "", body, flags=re.S), re.S)
        hall = clean(halls[-1]) if halls else ""
        out.append({
            "name": name, "start": start, "end": end,
            "venue": "AsiaWorld-Expo, Chek Lap Kok" + (f" ({hall})" if hall else ""),
            "organiser": "", "access": "Not stated in listing",
            "audience": ", ".join(sorted(c.title() for c in cats)),
            "category": ", ".join(sorted(c.title() for c in cats)),
            "url": "https://www.asiaworld-expo.com" + html.unescape(href.group(1)) if href else url,
            "source": "AsiaWorld-Expo upcoming events", "source_url": url, "official": True,
        })
    return out


def investhk():
    """InvestHK (HKSAR Government) business events API."""
    api = "https://www2.investhk.gov.hk/api/en/events"
    hdr = {"Origin": "https://www.investhk.gov.hk", "Referer": "https://www.investhk.gov.hk/en/events/"}
    out, page = [], 1
    while page <= 10:
        d = fetch_json(api, {"status": 1, "time": 0, "keywords": "", "parentId": 1084,
                             "page": page, "take": 50}, hdr)["data"]
        for e in d.get("results", []):
            start = dt.date.fromisoformat(e["startDate"][:10])
            end = dt.date.fromisoformat((e.get("endDate") or e["startDate"])[:10])
            out.append({
                "name": clean(e["title"]), "start": start, "end": end,
                "venue": clean(e.get("location")), "organiser": "",
                "access": "Not stated in listing", "audience": "Business / investors (InvestHK listing)",
                "category": ", ".join(e.get("industries") or []) or "Business event",
                "description": clean(e.get("description")),
                "url": "https://www.investhk.gov.hk" + e["url"],
                "source": "InvestHK events (HKSAR Gov)", "source_url": "https://www.investhk.gov.hk/en/events/",
                "official": True,
            })
        if page * 50 >= int(d.get("totalResult") or 0):
            break
        page += 1
    return out


def glueup_chamber(url, source):
    """Chamber of commerce listings hosted on Glue Up (AmCham, BritCham)."""
    h = fetch(url)
    out = []
    for row in re.split(r'<div class="event-row">', h)[1:]:
        title = re.search(r'class="link-to-eb event-listing-title" href="([^"]+)"[^>]*>(.*?)<span', row, re.S)
        date = re.search(r'<div class="event-date">(.*?)</div>', row, re.S)
        if not (title and date):
            continue
        start, end = parse_range(date.group(1))
        if not start:
            continue
        venue = re.search(r'<div class="event-venue">(.*?)</div>', row, re.S)
        desc = re.search(r'<div class="event-description">(.*?)</div>', row, re.S)
        tags = [clean(t) for t in re.findall(r'<span class="event-tag">(.*?)</span>', row, re.S)]
        out.append({
            "name": clean(title.group(2)), "start": start, "end": end,
            "venue": clean(venue.group(1)) if venue else "", "organiser": source,
            "access": "Chamber registration (member / guest)",
            "audience": "Chamber members & guests",
            "category": ", ".join(tags) or "Chamber event",
            "description": clean(desc.group(1)) if desc else "",
            "time": clean(date.group(1)),
            "url": html.unescape(title.group(1)),
            "source": source + " events", "source_url": url, "official": True,
        })
    return out


def hkgcc():
    """Hong Kong General Chamber of Commerce - upcoming events (first page)."""
    url = "https://www.chamber.org.hk/en/events/"
    h = fetch(url)
    out = []
    for li in re.split(r'<li class="event_list_li">', h)[1:]:
        t = re.search(r'lblTitle_eng"[^>]*>(.*?)</span>', li, re.S)
        link = re.search(r'href="(whatson_detail\.aspx\?e_code=[^"]+)"', li)
        d = re.search(r'fa-calendar"></i>\s*<span>(.*?)</span>', li, re.S)
        if not (t and d):
            continue
        start, end = parse_range(d.group(1))
        if not start:
            continue
        out.append({
            "name": clean(t.group(1)), "start": start, "end": end,
            "venue": "", "organiser": "Hong Kong General Chamber of Commerce",
            "access": "Chamber registration (member / guest)", "audience": "Chamber members & guests",
            "category": "Chamber event",
            "url": "https://www.chamber.org.hk/en/events/" + html.unescape(link.group(1)) if link else url,
            "source": "HKGCC events", "source_url": url, "official": True,
        })
    return out


SOURCES = [
    ("HKCEC event calendar", hkcec),
    ("AsiaWorld-Expo upcoming events", asiaworld_expo),
    ("InvestHK events (HKSAR Gov)", investhk),
    ("AmCham HK events", lambda: glueup_chamber("https://www.amcham.org.hk/events", "AmCham HK")),
    ("BritCham HK events", lambda: glueup_chamber("https://www.britcham.com/events", "BritCham HK")),
    ("HKGCC events", hkgcc),
]
