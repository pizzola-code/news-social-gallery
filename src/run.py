# -*- coding: utf-8 -*-
"""Orchestratore. Due fasi (il workflow committa le immagini tra l'una e l'altra):
  render  : fetch ultimo articolo -> (skip se gia fatto) -> estrai -> render 5 card -> out/manifest.json
  publish : schedula su Metricool per le 12:00 + email anteprima -> aggiorna state.json
ENV: ANTHROPIC_API_KEY, METRICOOL_USER_TOKEN/USER_ID/BLOG_ID, SMTP_*, RAW_BASE, PUBLISH_HOUR, FORCE"""
import json, os, sys, datetime
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")
STATE = os.path.join(ROOT, "state.json")
MANIFEST = os.path.join(OUT, "manifest.json")
SKIP = os.path.join(OUT, "SKIP")
TZ = ZoneInfo(os.environ.get("PUBLISH_TZ", "Europe/Rome"))

def _load(p, d): return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else d
def _save(p, o): json.dump(o, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def do_render():
    sys.path.insert(0, os.path.join(ROOT, "src"))
    import fetch_latest, extract, render
    os.makedirs(OUT, exist_ok=True)
    for f in (SKIP, MANIFEST):
        if os.path.exists(f): os.remove(f)
    art = fetch_latest.latest_article()
    last = _load(STATE, {}).get("last_url")
    if art["url"] == last and os.environ.get("FORCE") != "1":
        open(SKIP, "w").write(art["url"]); print("SKIP: nessun nuovo articolo:", art["url"]); return
    content = extract.extract(art)
    datestr = datetime.datetime.now(TZ).strftime("%Y%m%d")
    paths = render.build_gallery(content, art, OUT, datestr)
    _save(MANIFEST, {"url": art["url"], "title": art["title"], "image": art.get("image",""),
                     "caption": content["caption"], "hashtags": content.get("hashtags", []),
                     "theme": content["theme"], "files": [os.path.basename(p) for p in paths],
                     "date": datestr})
    print("RENDER ok:", len(paths), "card, tema", content["theme"])

def do_publish():
    if os.path.exists(SKIP): print("SKIP attivo, nessuna pubblicazione."); return
    import publish, notify
    m = _load(MANIFEST, None)
    if not m: raise RuntimeError("manifest.json mancante: eseguire prima 'render'")
    raw = os.environ["RAW_BASE"].rstrip("/")
    urls = [f"{raw}/{f}" for f in m["files"]]
    hour = os.environ.get("PUBLISH_HOUR", "12:00:00")
    today = datetime.datetime.now(TZ).strftime("%Y-%m-%d")
    when_iso = f"{today}T{hour}"
    art = {"url": m["url"], "title": m["title"], "image": m.get("image","")}
    text = publish.build_text(m["caption"], m["url"], m.get("hashtags", []))
    mode = os.environ.get("PUBLISH_MODE", "draft")  # dry | draft | auto
    if mode == "dry":
        print("DRY: nessuna chiamata. URLs:"); [print(" ", u) for u in urls]; resp = {"dry": True}
    elif mode == "auto":
        resp = publish.schedule(urls, text, when_iso, autopublish=True, draft=False)
        print("Metricool AUTO (pubblica alle", when_iso, "):", json.dumps(resp)[:200])
    else:  # draft
        resp = publish.schedule(urls, text, when_iso, autopublish=False, draft=True)
        print("Metricool BOZZA creata:", json.dumps(resp)[:200])
    try:
        notify.send_preview(f"[/news] Pubblicazione {today} alle {hour[:5]} — anteprima",
                            art, m, urls, f"{today} {hour[:5]}")
        print("Email anteprima inviata.")
    except Exception as e:
        print("ATTENZIONE: email non inviata:", e)
    _save(STATE, {"last_url": m["url"], "last_date": today})
    print("PUBLISH ok.")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "render"
    {"render": do_render, "publish": do_publish}[cmd]()
