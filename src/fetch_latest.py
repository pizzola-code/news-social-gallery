# -*- coding: utf-8 -*-
"""Trova l'ultimo articolo pubblicato su spaggiari.eu/news. Solo stdlib.
Espone latest_article() -> dict(url,title,description,image,content_text)."""
import re, urllib.request, html

LISTING = "https://www.spaggiari.eu/news"
UA = {"User-Agent": "Mozilla/5.0 (compatible; SpaggiariNewsBot/1.0)"}
BAD = ("/news/tag", "/news/author", "/news/topic", "/news/page")

def _get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

def _meta(t, prop):
    for pat in (rf'<meta[^>]+property=["\']{prop}["\'][^>]+content=["\']([^"\']+)["\']',
                rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']{prop}["\']',
                rf'<meta[^>]+name=["\']{prop}["\'][^>]+content=["\']([^"\']+)["\']'):
        m = re.search(pat, t, re.I)
        if m: return html.unescape(m.group(1).strip())
    return ""

def _strip_html(t):
    t = re.sub(r"(?is)<(script|style|nav|header|footer)[^>]*>.*?</\1>", " ", t)
    body = re.search(r"(?is)<article.*?</article>", t)
    t = body.group(0) if body else t
    t = re.sub(r"(?is)<[^>]+>", " ", t)
    t = html.unescape(t)
    return re.sub(r"\s+", " ", t).strip()

def latest_article():
    page = _get(LISTING)
    cand = re.findall(r'href=["\'](https?://(?:www\.)?spaggiari\.eu/news/[a-z0-9][a-z0-9\-]+)["\']', page, re.I)
    seen, ordered = set(), []
    for u in cand:
        u = u.split("?")[0].rstrip("/")
        if u in seen or any(b in u for b in BAD): continue
        seen.add(u); ordered.append(u)
    if not ordered:
        raise RuntimeError("Nessun articolo trovato nel listing /news")
    url = ordered[0]
    art = _get(url)
    return {
        "url": url,
        "title": _meta(art, "og:title"),
        "description": _meta(art, "og:description"),
        "image": _meta(art, "og:image"),
        "content_text": _strip_html(art)[:9000],
    }

if __name__ == "__main__":
    import json
    print(json.dumps(latest_article(), ensure_ascii=False, indent=2)[:1500])
