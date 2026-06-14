# -*- coding: utf-8 -*-
"""Test render con contenuto d'esempio (articolo crediti). Nessun segreto."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
import render

article = {
    "url": "https://www.spaggiari.eu/news/crediti-scolastici-maturita-2026-calcolo-tabella",
    "title": "Crediti scolastici Maturità 2026",
    "image": "https://www.spaggiari.eu/hubfs/blog-images/cover_crediti_scolastici_maturita_20260614.png",
}
content = {
    "theme": "maturita",
    "caption": "Maturità 2026: quanto pesa il credito scolastico?",
    "hashtags": ["#Maturità2026", "#CreditoScolastico"],
    "cover": {"eyebrow": "Maturità 2026", "title": "Crediti scolastici: come si calcolano", "hi": "Fino a 40 punti su 100"},
    "cards": [
        {"eyebrow": "Quanto pesa ogni anno", "title": "12 + 13 + 15 = 40 punti",
         "body": "Il credito vale fino a 40 punti: massimo 12 in terza, 13 in quarta e 15 in quinta."},
        {"eyebrow": "Come si calcola", "title": "La media dei voti decide la fascia",
         "body": "La media di tutti i voti, compreso il comportamento, individua la banda della tabella Allegato A."},
        {"eyebrow": "Il comportamento conta", "title": "Condotta almeno 9 per il massimo",
         "body": "Il punteggio più alto della fascia spetta solo con voto di comportamento almeno 9/10."},
    ],
    "cta": {"eyebrow": "In sintesi", "title": "40 crediti + 60 prove = 100",
            "body": "Ai 40 crediti scolastici si sommano fino a 60 punti dalle prove d'esame (20 + 20 + 20)."},
}
paths = render.build_gallery(content, article, os.path.join(os.path.dirname(__file__), "out"), "20260614")
print("OK:", *[os.path.basename(p) for p in paths])
