# news-social-gallery

Pipeline automatica: ogni giorno legge l'ultimo articolo di **spaggiari.eu/news**, genera una **gallery di 5 card** (brand Gruppo Spaggiari) e la **schedula su Metricool** (LinkedIn + Facebook) per le **12:00 Europe/Rome**, con **email di anteprima/veto** ~1h prima.

## Come funziona
1. `src/fetch_latest.py` — trova l'ultimo articolo (URL, titolo, descrizione, copertina).
2. `src/extract.py` — Anthropic estrae intro social + 5 card + tema (solo fatti dell'articolo).
3. `src/render.py` — compone 5 PNG 1080x1080: testo esatto via Pillow (font Playfair/Lexend), **logo nel footer**, sfondo dalla **libreria a tema** (`assets/bg-library/`), la cover usa l'immagine dell'articolo se presente.
4. `src/publish.py` — schedula il carosello su Metricool (API ufficiale).
5. `src/notify.py` — email di anteprima (SMTP Office365). **Veto = cancellare il post in Metricool prima delle 12:00.**

Orchestratore: `src/run.py render` poi `src/run.py publish`. Anti-duplicati via `state.json`.

## GitHub Action
`.github/workflows/daily.yml` gira alle **09:00 UTC** (~11:00 Rome). Manuale: *Run workflow* con `force`/`dry_run`.

## Secrets richiesti (Settings → Secrets → Actions)
| Secret | Valore |
|---|---|
| `ANTHROPIC_API_KEY` | chiave Anthropic |
| `METRICOOL_USER_TOKEN` | token API Metricool |
| `METRICOOL_USER_ID` | `4929668` |
| `METRICOOL_BLOG_ID` | `6398616` (brand Gruppo Spaggiari Parma) |
| `SMTP_USER` | utente Office365 (es. pizzola@spaggiari.eu) |
| `SMTP_PASS` | app password Office365 |
| `SMTP_TO` | destinatari anteprima (csv) |

## Libreria sfondi (bouquet)
Generata UNA volta con Higgsfield (navy+ciano, icona a tema, senza testo). Temi: `maturita, normativa, scadenze, iscrizioni, didattica, orientamento` (2 varianti `_a`/`_b`). Per rinfrescare il look basta rigenerarli; il giro quotidiano NON usa Higgsfield.

## Test locale
```
pip install -r requirements.txt
DRY_RUN=1 python src/run.py render
DRY_RUN=1 RAW_BASE=https://example.com python src/run.py publish
```
