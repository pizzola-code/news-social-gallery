# -*- coding: utf-8 -*-
"""Estrae da un articolo /news il contenuto della gallery (intro social + 5 card)
usando Anthropic. Restituisce un dict strutturato e VALIDATO.

Regola d'oro brand: NIENTE numeri/fatti inventati, solo ci� che � nell'articolo.
Niente claim di conformit�. 'Gruppo Spaggiari' senza articolo. Sigla FSL (mai PCTO)."""
import json, os, re
import anthropic

MODEL = os.environ.get("EXTRACT_MODEL", "claude-sonnet-4-6")
THEMES = ["maturita", "normativa", "scadenze", "iscrizioni", "didattica", "orientamento"]

SCHEMA_HINT = """Rispondi SOLO con un oggetto JSON valido (nessun testo fuori dal JSON) con questa forma:
{
  "theme": "uno tra: maturita | normativa | scadenze | iscrizioni | didattica | orientamento",
  "caption": "intro per il post social, 2-3 frasi, tono istituzionale ma chiaro, SENZA hashtag finali qui",
  "hashtags": ["#...", "#..."],
  "cover":  {"eyebrow": "OCCHIELLO BREVE", "title": "titolo forte (max ~6 parole)", "hi": "frase gancio breve con il dato chiave"},
  "cards": [
     {"eyebrow": "...", "title": "titolo card (max ~7 parole)", "body": "1-2 frasi, max ~210 caratteri"},
     {"eyebrow": "...", "title": "...", "body": "..."},
     {"eyebrow": "...", "title": "...", "body": "..."}
  ],
  "cta": {"eyebrow": "IN SINTESI", "title": "frase di chiusura forte", "body": "1 frase"}
}
Vincoli: italiano corretto con accenti; usa SOLO numeri/fatti presenti nell'articolo (non inventarli);
i titoli possono contenere i numeri chiave; niente claim di conformit� normativa; 'Gruppo Spaggiari' senza articolo."""

def _coerce(d):
    assert d.get("theme") in THEMES, f"theme non valido: {d.get('theme')}"
    for k in ("caption", "cover", "cta"): assert k in d, f"manca {k}"
    assert isinstance(d.get("cards"), list) and len(d["cards"]) == 3, "servono esattamente 3 card centrali"
    d.setdefault("hashtags", [])
    return d

def extract(article: dict) -> dict:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    user = (f"TITOLO: {article['title']}\nDESCRIZIONE: {article['description']}\n"
            f"URL: {article['url']}\n\nTESTO ARTICOLO:\n{article['content_text']}\n\n{SCHEMA_HINT}")
    msg = client.messages.create(
        model=MODEL, max_tokens=1500, temperature=0.3,
        system="Sei l'editor social di Gruppo Spaggiari (editoria scolastica). Sintetizzi articoli /news in caroselli precisi e on-brand.",
        messages=[{"role": "user", "content": user}],
    )
    txt = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    m = re.search(r"\{.*\}", txt, re.S)
    if not m: raise RuntimeError("Nessun JSON nella risposta del modello")
    return _coerce(json.loads(m.group(0)))

if __name__ == "__main__":
    import fetch_latest
    print(json.dumps(extract(fetch_latest.latest_article()), ensure_ascii=False, indent=2))
