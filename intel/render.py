"""Inject the collected data into a dashboard template."""
import hashlib
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _js(obj):
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def write(payload, path, template="dashboard.html", config=None):
    with open(os.path.join(ROOT, "templates", template), encoding="utf-8") as f:
        tpl = f.read()
    html = tpl.replace("/*__DATA__*/null", _js(payload)).replace("/*__CONFIG__*/{}", _js(config or {}))
    build = hashlib.sha1(html.encode("utf-8")).hexdigest()[:12]
    html = html.replace("/*__BUILD__*/", build)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    if "/*__BUILD__*/" in tpl:   # pages that check for a newer version
        with open(os.path.join(os.path.dirname(os.path.abspath(path)), "version.json"), "w", encoding="utf-8") as f:
            json.dump({"build": build}, f)
    return os.path.abspath(path)
