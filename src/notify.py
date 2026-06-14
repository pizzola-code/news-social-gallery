# -*- coding: utf-8 -*-
"""Email di anteprima/veto via SMTP Office365."""
import os, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

HOST = os.environ.get("SMTP_HOST", "smtp.office365.com")
PORT = int(os.environ.get("SMTP_PORT", "587"))
USER = os.environ.get("SMTP_USER", "")
PWD = os.environ.get("SMTP_PASS", "")
TO = os.environ.get("SMTP_TO", "pizzola@spaggiari.eu")

def send_preview(subject, article, content, image_urls, publish_at, post_link=None):
    imgs = "".join(f'<img src="{u}" style="width:150px;border-radius:8px;margin:4px;border:1px solid #ddd">' for u in image_urls)
    tags = " ".join(content.get("hashtags", []))
    veto = ('<p style="background:#FFF3CD;padding:12px;border-radius:8px">'
            f'⚠️ La gallery verrà pubblicata in automatico alle <b>{publish_at}</b> su LinkedIn + Facebook.<br>'
            'Per <b>annullare</b>: apri Metricool → Planner e <b>cancella il post schedulato</b> prima di quell’ora.</p>')
    html = f"""<div style="font-family:Arial,sans-serif;max-width:680px">
<h2 style="color:#0E2A4D">Anteprima post /news</h2>
<p><b>Articolo:</b> <a href="{article['url']}">{article['title']}</a></p>
{veto}
<p><b>Caption:</b><br>{content['caption']}<br><br>Approfondisci: {article['url']}<br>{tags}</p>
<div>{imgs}</div>
{('<p><b>Post in Metricool:</b> '+post_link+'</p>') if post_link else ''}
</div>"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject; msg["From"] = USER; msg["To"] = TO
    msg.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP(HOST, PORT, timeout=40) as s:
        s.starttls(); s.login(USER, PWD); s.sendmail(USER, [a.strip() for a in TO.split(",")], msg.as_string())
    return True
