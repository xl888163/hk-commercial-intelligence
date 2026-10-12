"""Property-movement collectors: news RSS feeds and HKSAR Government press releases.
Each returns raw headline items exactly as published (title, link, publisher, date)."""
import email.utils
import html
import re
import urllib.parse

from .net import fetch

# Google News searches restricted to the Hong Kong editions - office move-ins.
MOVE_EN = '(office OR offices OR headquarters OR HQ) (relocate OR relocates OR relocating OR moves OR "move to" OR leases OR "new office" OR opens OR expands OR "sq ft" OR floors)'
MOVE_ZH = '(寫字樓 OR 甲廈 OR 總部 OR 樓面) (承租 OR 租用 OR 搬遷 OR 進駐 OR 遷入 OR 預租 OR 擴充 OR 租下)'
GN_QUERIES_EN = [
    '"Hong Kong" office relocation',
    '"Hong Kong" relocates headquarters tower',
    '"Hong Kong" office lease "sq ft"',
    '"Hong Kong" leases floors tower',
    '"Hong Kong" "Grade A" office tenant',
    '"opens Hong Kong office"',
    '"new Hong Kong office"',
    '"Hong Kong" "regional headquarters" office opens OR relocates',
    '"Hong Kong" office "moves to" Central OR "Island East" OR "Kowloon East" OR "West Kowloon" OR Admiralty OR "Quarry Bay"',
    '"Nippon Express" "Hong Kong" office OR warehouse OR relocate OR opens',
]
# Outlets covering Hong Kong business - each searched for office moves.
OUTLETS_EN = ["therealdeal.com", "scmp.com", "thestandard.com.hk", "hongkongbusiness.hk", "realestateasia.com",
              "mingtiandi.com", "law.com", "bloomberg.com", "reuters.com", "finews.asia", "asianinvestor.net",
              "campaignasia.com", "tyr.hkbu.edu.hk", "yp.scmp.com", "nipponexpress-holdings.com",
              "businesswire.com", "prnewswire.com", "globenewswire.com", "news.gov.hk", "rthk.hk", "hongkongfp.com",
              "edgeprop.sg", "asiaassetmanagement.com", "insideretail.asia", "datacenterdynamics.com", "w.media"]
GN_QUERIES_EN += [f'site:{d} "Hong Kong" {MOVE_EN}' for d in OUTLETS_EN]
GN_QUERIES_ZH = [
    "香港 寫字樓 搬遷",
    "承租 寫字樓 樓面 總部",
    "租用 甲廈 平方呎",
    "預租 甲廈 總部",
    "進駐 甲廈 樓面",
]
OUTLETS_ZH = ["hk01.com", "stheadline.com", "on.cc", "hket.com", "hkej.com", "wenweipo.com", "takungpao.com",
              "am730.com.hk", "mingpao.com", "now.com", "i-cable.com", "etnet.com.hk", "hkcd.com", "thevalue.com",
              "dotdotnews.com", "orangenews.hk", "bastillepost.com"]
GN_QUERIES_ZH += [f"site:{d} {MOVE_ZH}" for d in OUTLETS_ZH]

DIRECT_FEEDS = [
    ("SCMP Property", "https://www.scmp.com/rss/96/feed"),
    ("Mingtiandi", "https://www.mingtiandi.com/feed/"),
    ("RTHK Business", "https://rthk.hk/rthk/news/rss/e_expressnews_ebusiness.xml"),
    ("Hong Kong Free Press", "https://hongkongfp.com/feed/"),
]

GOV_FEED = "https://www.info.gov.hk/gia/rss/general_en.xml"
GOV_KEEP = re.compile(r"land sale|tender|\bsite\b|data (?:centre|facility)|logistics|warehouse|"
                      r"government office|Northern Metropolis|Kai Tak|San Tin|Hung Shui Kiu|"
                      r"development|commercial", re.I)
GOV_DROP = re.compile(r"drug|seiz|arrest|weather|typhoon|road|traffic|swimming|vacancies|LCQ|"
                      r"Victoria Park|fair stalls|consultation on|exhibition|speech|appointment", re.I)


def _items(xml):
    for it in re.findall(r"<item>(.*?)</item>", xml, re.S):
        def tag(name):
            m = re.search(rf"<{name}[^>]*>(.*?)</{name}>", it, re.S)
            v = (m.group(1) if m else "").replace("<![CDATA[", "").replace("]]>", "")
            return html.unescape(v).strip()
        src = re.search(r'<source url="([^"]*)">(.*?)</source>', it, re.S)
        yield tag, src


def _date(s):
    try:
        return email.utils.parsedate_to_datetime(s).date()
    except Exception:
        return None


def google_news(query, lang, days=90):
    if lang == "en":
        params = {"hl": "en-HK", "gl": "HK", "ceid": "HK:en"}
    else:
        params = {"hl": "zh-HK", "gl": "HK", "ceid": "HK:zh-Hant"}
    url = "https://news.google.com/rss/search?q=" + urllib.parse.quote(f"{query} when:{days}d")
    xml = fetch(url, params)
    out = []
    for tag, src in _items(xml):
        title, publisher = tag("title"), html.unescape(src.group(2)).strip() if src else ""
        if publisher and title.endswith(" - " + publisher):
            title = title[: -len(publisher) - 3].strip()
        out.append({
            "title": title, "url": tag("link"), "date": _date(tag("pubDate")),
            "publisher": publisher, "publisher_url": src.group(1) if src else "",
            "lang": lang, "feed": "Google News (HK edition)", "official": False, "summary": "",
        })
    return out


def direct_feed(name, url):
    xml = fetch(url)
    out = []
    for tag, _ in _items(xml):
        desc = re.sub(r"<[^>]+>", " ", tag("description"))
        out.append({
            "title": tag("title"), "url": tag("link"), "date": _date(tag("pubDate")),
            "publisher": name, "publisher_url": url, "lang": "en", "feed": name,
            "official": False, "summary": re.sub(r"\s+", " ", desc).strip()[:600],
        })
    return out


def gov_press():
    xml = fetch(GOV_FEED)
    out = []
    for tag, _ in _items(xml):
        t = tag("title")
        if not GOV_KEEP.search(t) or GOV_DROP.search(t):
            continue
        desc = re.sub(r"<[^>]+>|&nbsp;", " ", tag("description"))
        out.append({
            "title": t, "url": tag("link"), "date": _date(tag("pubDate")),
            "publisher": "HKSAR Government press release", "publisher_url": "https://www.info.gov.hk",
            "lang": "en", "feed": "HKSAR Government press releases", "official": True,
            "summary": re.sub(r"\s+", " ", desc).strip()[:600],
        })
    return out


def _label(q, lang):
    m = re.match(r"site:(\S+)", q)
    return f"News search ({'EN' if lang == 'en' else '中文'}): " + (m.group(1) if m else q)


def sources(days=90):
    s = [(_label(q, "en"), (lambda q=q: google_news(q, "en", days))) for q in GN_QUERIES_EN]
    s += [(_label(q, "zh"), (lambda q=q: google_news(q, "zh", days))) for q in GN_QUERIES_ZH]
    s += [(name, (lambda n=name, u=url: direct_feed(n, u))) for name, url in DIRECT_FEEDS]
    return s
