# -*- coding: utf-8 -*-
"""Render engine: da contenuto (dict di extract) + asset -> 5 card PNG 1080x1080.
Testo sovrapposto via Pillow (sempre corretto). Logo Spaggiari nel footer.
Sfondo: card1 usa la copertina dell'articolo se disponibile, le altre la libreria a tema."""
import os, io, urllib.request
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
FONTS = os.path.join(ASSETS, "fonts")
LIB = os.path.join(ASSETS, "bg-library")
LOGO = os.path.join(ASSETS, "logo-neg-orig.webp")
PF = os.path.join(FONTS, "PlayfairDisplay.ttf")
LX = os.path.join(FONTS, "LexendDeca.ttf")
SZ, PAD = 1080, 96
INK="#0E2A4D"; WHITE="#FFFFFF"; CYAN="#6fc2e7"; RED="#C8202B"; BODY="#C9D6E3"; FOOT="#8AA0B8"; LINE="#23456b"
UA = {"User-Agent": "Mozilla/5.0 (compatible; SpaggiariNewsBot/1.0)"}

_fc = {}
def font(fam, size, w):
    k=(fam,size,w)
    if k not in _fc:
        f=ImageFont.truetype(fam,size)
        try: f.set_variation_by_name(w)
        except Exception: pass
        _fc[k]=f
    return _fc[k]

def wrap(d,t,f,mw):
    out,cur=[],""
    for word in t.split():
        s=(cur+" "+word).strip()
        if d.textlength(s,font=f)<=mw: cur=s
        else: out.append(cur); cur=word
    if cur: out.append(cur)
    return out

def fit_font(d, text, fam, maxsize, minsize, w, maxw, max_lines):
    """Sceglie la dimensione max che sta in max_lines righe (niente parole orfane)."""
    for s in range(maxsize, minsize-1, -2):
        if len(wrap(d, text, font(fam,s,w), maxw)) <= max_lines: return font(fam,s,w)
    return font(fam, minsize, w)

def block(d,t,x,y,f,fill,mw,lh=1.12):
    for line in wrap(d,t,f,mw):
        d.text((x,y),line,font=f,fill=fill); a,de=f.getmetrics(); y+=int((a+de)*lh)
    return y

_logo=None
def logo_img():
    global _logo
    if _logo is None:
        im=Image.open(LOGO).convert("RGBA"); _logo=im.crop(im.getbbox())
    return _logo

def _theme_bg(theme, variant):
    p=os.path.join(LIB, f"{theme}_{variant}.png")
    if not os.path.exists(p):  # fallback
        alts=[f for f in os.listdir(LIB) if f.endswith(".png")]
        p=os.path.join(LIB, sorted(alts)[0])
    return Image.open(p).convert("RGB").resize((SZ,SZ))

def _cover_from_url(url):
    try:
        req=urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r: data=r.read()
        im=Image.open(io.BytesIO(data)).convert("RGB")
        # cover-crop quadrato
        w,h=im.size; s=min(w,h); im=im.crop(((w-s)//2,(h-s)//2,(w-s)//2+s,(h-s)//2+s)).resize((SZ,SZ))
        return im
    except Exception:
        return None

def base(bg, overlay=0.28):
    bg=Image.blend(bg, Image.new("RGB",(SZ,SZ),INK), overlay)
    g=Image.new("L",(1,SZ),0)
    for i in range(SZ): g.putpixel((0,i),int(170*max(0,(i-SZ*0.5)/(SZ*0.5))))
    return Image.composite(Image.new("RGB",(SZ,SZ),INK), bg, g.resize((SZ,SZ)))

def eyebrow(d,t,y=150):
    f=font(LX,30,"SemiBold"); cx=PAD
    for ch in t.upper():
        d.text((cx,y),ch,font=f,fill=RED); cx+=d.textlength(ch,font=f)+4
    d.line([(PAD,y+52),(PAD+70,y+52)],fill=RED,width=4)

def footer(img,d,page,total):
    d.line([(PAD,SZ-150),(SZ-PAD,SZ-150)],fill=LINE,width=2)
    lg=logo_img(); lw=300; lh=int(lg.height*lw/lg.width); lg=lg.resize((lw,lh))
    img.paste(lg,(PAD,SZ-128-(lh-34)//2),lg)
    f=font(LX,28,"Medium"); pg=f"{page} / {total}"
    d.text((SZ-PAD-d.textlength(pg,font=f),SZ-122),pg,font=f,fill=FOOT)

def _card(bg, eb, draw_body, page, total, out):
    img=base(bg); d=ImageDraw.Draw(img); eyebrow(d,eb); draw_body(img,d); footer(img,d,page,total)
    img.save(out); return out

def build_gallery(content, article, outdir, datestr):
    os.makedirs(outdir, exist_ok=True)
    theme=content["theme"]; total=5; paths=[]
    def p(n): return os.path.join(outdir, f"card_{datestr}_{n}.png")

    # CARD 1 - cover (copertina articolo se c'e, altrimenti tema_a)
    cov=_cover_from_url(article.get("image","")) if article.get("image") else None
    bg1=cov if cov is not None else _theme_bg(theme,"a")
    c=content["cover"]
    def b1(img,d):
        y=300
        f=fit_font(d,c["title"],PF,92,56,"Bold",SZ-2*PAD,3)
        y=block(d,c["title"],PAD,y,f,WHITE,SZ-2*PAD,lh=1.05); y+=30
        block(d,c.get("hi",""),PAD,y,font(LX,54,"SemiBold"),CYAN,SZ-2*PAD)
    paths.append(_card(bg1, c["eyebrow"], b1, 1, total, p(1)))

    # CARD 2-4 - testo
    for i,cc in enumerate(content["cards"], start=2):
        bg=_theme_bg(theme, "a" if i%2 else "b")
        def b(img,d,cc=cc):
            y=300
            f=fit_font(d,cc["title"],PF,78,52,"Bold",SZ-2*PAD,3)
            y=block(d,cc["title"],PAD,y,f,WHITE,SZ-2*PAD,lh=1.08); y+=26
            block(d,cc["body"],PAD,y,font(LX,38,"Regular"),BODY,SZ-2*PAD,lh=1.32)
        paths.append(_card(bg, cc["eyebrow"], b, i, total, p(i)))

    # CARD 5 - CTA
    bg5=_theme_bg(theme,"b"); cta=content["cta"]
    def b5(img,d):
        y=300
        f=fit_font(d,cta["title"],PF,76,50,"Bold",SZ-2*PAD,3)
        y=block(d,cta["title"],PAD,y,f,WHITE,SZ-2*PAD,lh=1.08); y+=24
        y=block(d,cta.get("body",""),PAD,y,font(LX,38,"Regular"),BODY,SZ-2*PAD,lh=1.32)
        fb=font(LX,34,"SemiBold"); lbl="Leggi l'articolo completo"; bb=fb.getbbox(lbl)
        tw=d.textlength(lbl,font=fb); px,py=44,26; w=tw+2*px; hh=(bb[3]-bb[1])+2*py; yy=y+30
        d.rounded_rectangle([PAD,yy,PAD+w,yy+hh],radius=12,fill=CYAN)
        d.text((PAD+px,yy+py-bb[1]),lbl,font=fb,fill=INK)
        d.text((PAD,yy+hh+18),"spaggiari.eu/news",font=font(LX,26,"Medium"),fill=CYAN)
    paths.append(_card(bg5, cta["eyebrow"], b5, 5, total, p(5)))
    return paths
