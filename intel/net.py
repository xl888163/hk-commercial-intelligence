"""HTTP helpers (standard library only)."""
import gzip
import json
import time
import urllib.error
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def fetch(url, params=None, headers=None, timeout=25, retries=2):
    """Return response text, or raise the last error after retries."""
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    hdrs = {"User-Agent": UA, "Accept-Language": "en-HK,en;q=0.9,zh-HK;q=0.8",
            "Accept-Encoding": "gzip"}
    hdrs.update(headers or {})
    last = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=hdrs)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                charset = r.headers.get_content_charset() or "utf-8"
                return raw.decode(charset, errors="replace")
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            last = e
            time.sleep(1.5 * (attempt + 1))
    raise last


def fetch_json(url, params=None, headers=None):
    return json.loads(fetch(url, params, headers))
