"""Translate Chinese text on dashboard records into English.

Provider:
  * Claude (when ANTHROPIC_API_KEY is set, e.g. as a GitHub secret) - best with
    Hong Kong company and building names;
  * otherwise MyMemory's free public API (anonymous limit about 5,000 characters/day).
Every translation is cached in data/translations.json, so each line is
translated once. The original Chinese is kept on the record (`*_zh` fields)
and shown next to the English, so nothing is lost if a translation is imperfect.
"""
import json
import os
import re
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "translations.json")
CJK = re.compile(r"[一-鿿]")
LATIN = re.compile(r"[A-Za-z]")
MODEL = "claude-opus-5-5"

PROMPT = """Translate each item from Chinese (Hong Kong) into concise, natural English.
Items are property and business news headlines, company names, building names or event names.
Rules:
- Use a well-known official English name only when you are sure of it (e.g. 太古坊 -> Taikoo Place, 新地 -> SHKP, 渣打 -> Standard Chartered).
- If you are not sure of a company or building's official English name, translate its meaning and keep the Chinese in brackets, e.g. "Sun Wah Hong (瑞華行)".
- Keep numbers exact: 萬 = 10,000, 億 = 100,000,000 (write HK$ amounts like HK$340 million; 呎 = sq ft).
- Do not add facts that are not in the item.
Return only a JSON array of strings, one translation per input item, in the same order and the same length."""


def needs(text):
    return bool(text) and len(CJK.findall(text)) >= 2


def _mostly_english(text):
    letters = len(LATIN.findall(text))
    return letters >= 12 and letters >= 1.5 * len(CJK.findall(text))


def _strip_cjk(text):
    """'HKTDC Jewellery Show (香港貿發局珠寶展)' -> 'HKTDC Jewellery Show'."""
    t = re.sub(r"\s*[(（][^()（）]*[一-鿿][^()（）]*[)）]", "", text)
    return re.sub(r"\s{2,}", " ", t).strip(" -|")


def _claude(items):
    import anthropic
    client = anthropic.Anthropic()
    out = []
    for i in range(0, len(items), 60):
        chunk = items[i:i + 60]
        resp = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            output_config={"effort": "low"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=PROMPT,
            messages=[{"role": "user", "content": json.dumps(chunk, ensure_ascii=False)}],
        )
        if resp.stop_reason == "refusal":
            raise RuntimeError("translation request declined")
        text = "".join(b.text for b in resp.content if b.type == "text").strip()
        text = text[text.find("["): text.rfind("]") + 1]
        got = json.loads(text)
        if not isinstance(got, list) or len(got) != len(chunk):
            raise RuntimeError("translation count mismatch")
        out += [str(g).strip() for g in got]
    return out


def _mymemory(items):
    out = []
    for t in items:
        url = "https://api.mymemory.translated.net/get?" + urllib.parse.urlencode({"q": t[:480], "langpair": "zh-TW|en"})
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "hk-commercial-intelligence"}), timeout=20) as r:
            d = json.loads(r.read().decode("utf-8"))
        tr = (d.get("responseData") or {}).get("translatedText") or ""
        if d.get("responseStatus") != 200 or not tr or "MYMEMORY WARNING" in tr.upper():
            break          # daily quota reached: the rest are translated on a later refresh
        out.append(tr.strip())
    return out


def translate_all(texts):
    """Return {chinese: english}. Untranslated items (quota / errors) are simply missing."""
    try:
        with open(CACHE, encoding="utf-8") as f:
            cache = json.load(f)
    except (OSError, ValueError):
        cache = {}
    todo = sorted({t for t in texts if needs(t) and t not in cache})
    provider = "cache only"
    if todo:
        try:
            if os.environ.get("ANTHROPIC_API_KEY"):
                provider = "Claude"
                done = _claude(todo)
            else:
                provider = "MyMemory"
                done = _mymemory(todo)
        except Exception as e:
            print(f"Translation ({provider}) stopped: {e}")
            done = []
        cache.update(dict(zip(todo, done)))
        with open(CACHE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=0)
    missing = sum(1 for t in todo if t not in cache)
    print(f"Translation: {len(todo)} new lines via {provider}; {missing} left for the next refresh")
    return cache


def apply(ev, pr, tx):
    """Translate Chinese fields in place, keeping the original as <field>_zh."""
    texts = []
    for e in ev:
        texts += [e["name"], e.get("venue", ""), e.get("organiser", "")]
    for p in pr:
        texts += [p["headline"], p["company"]] + [s.get("title", "") for s in p["sources"]]
    for t in tx:
        texts += [t["party"], t["premises"], t["line"]] + [s.get("title", "") for s in t["sources"]]
    texts = [x for x in texts if x and not _mostly_english(x)]
    tr = translate_all(texts)

    def en(text):
        if not text or not CJK.search(text):
            return text
        if _mostly_english(text):
            return _strip_cjk(text)
        return tr.get(text, text)

    def swap(rec, field):
        orig = rec.get(field) or ""
        new = en(orig)
        if new != orig:
            rec[field + "_zh"] = orig
            rec[field] = new
            rec["actions"] = [a.replace(orig, new) for a in rec.get("actions", [])]
            for l in rec.get("links", []):
                if orig in l.get("url", ""):
                    l["url"] = l["url"].replace(urllib.parse.quote(orig), urllib.parse.quote(new))

    for e in ev:
        for f in ("name", "venue", "organiser"):
            swap(e, f)
    for p in pr:
        swap(p, "company")
        swap(p, "headline")
        for s in p["sources"]:
            if s.get("title") and CJK.search(s["title"]):
                s["title"] = en(s["title"])
    for t in tx:
        swap(t, "party")
        swap(t, "premises")
        if t.get("record_source") == "News":
            t["line_zh"] = t["line"]
            headline = t["sources"][0]["title"] if t["sources"] else ""
            t["line"] = f"{t['party']} - {en(headline)}"
        for s in t["sources"]:
            if s.get("title") and CJK.search(s["title"]):
                s["title"] = en(s["title"])
