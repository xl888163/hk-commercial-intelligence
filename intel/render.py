"""Inject the collected data into a dashboard template."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _js(obj):
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def write(payload, path, template="dashboard.html", config=None):
    with open(os.path.join(ROOT, "templates", template), encoding="utf-8") as f:
        tpl = f.read()
    html = tpl.replace("/*__DATA__*/null", _js(payload)).replace("/*__CONFIG__*/{}", _js(config or {}))
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return os.path.abspath(path)
