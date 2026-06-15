# -*- coding: utf-8 -*-
"""Pubblica/schedula un carosello su Metricool (LinkedIn + Facebook) via API ufficiale.
Endpoint e payload ricavati dal pacchetto ufficiale mcp-metricool."""
import json, os, requests

BASE = "https://app.metricool.com/api"
TOKEN = os.environ.get("METRICOOL_USER_TOKEN", "")
USER_ID = os.environ.get("METRICOOL_USER_ID", "")
BLOG_ID = os.environ.get("METRICOOL_BLOG_ID", "")
TZ = os.environ.get("PUBLISH_TZ", "Europe/Rome")

def schedule(image_urls, text, when_iso, providers=None, autopublish=True, draft=False):
    """when_iso: 'YYYY-MM-DDTHH:MM:SS' (ora locale TZ). Ritorna la risposta API (dict).
    providers: lista di network (es. ['linkedin','facebook'] o ['gmb']); default da env PROVIDERS."""
    if providers is None:
        providers = [p.strip() for p in os.environ.get("PROVIDERS", "linkedin,facebook").split(",") if p.strip()]
    prov, ndata = [], {}
    for net in providers:
        prov.append({"network": net})
        if net == "linkedin":
            ndata["linkedinData"] = {"type": "post", "previewIncluded": False, "publishImagesAsPDF": False}
        elif net == "facebook":
            ndata["facebookData"] = {"type": "POST"}
        elif net == "gmb":
            ndata["gmbData"] = {"topicType": "STANDARD"}
    body = {
        "autoPublish": bool(autopublish),
        "draft": bool(draft),
        "providers": prov,
        "publicationDate": {"dateTime": when_iso, "timezone": TZ},
        "text": text,
        "media": list(image_urls),
        "mediaAltText": [],
        "descendants": [],
        "smartLinkData": {"ids": []},
        "shortener": False,
        "firstCommentText": "",
        "hasNotReadNotes": False,
        **ndata,
    }
    url = f"{BASE}/v2/scheduler/posts?blogId={BLOG_ID}&userId={USER_ID}"
    r = requests.post(url, headers={"X-Mc-Auth": TOKEN, "content-type": "application/json",
                                    "accept": "application/json"},
                      data=json.dumps(body), timeout=40)
    r.raise_for_status()
    return r.json()

def build_text(caption, link, hashtags):
    tags = " ".join(hashtags) if hashtags else ""
    return f"{caption}\n\nApprofondisci: {link}" + (f"\n\n{tags}" if tags else "")
