# -*- coding: utf-8 -*-
"""Render engine: da contenuto (dict di extract) + asset -> 5 card PNG 1080x1080.
Testo sovrapposto via Pillow (sempre corretto). Logo Spaggiari nel footer.
Sfondo: card1 usa la copertina dell'articolo se disponibile, le altre la libreria a tema.
Estetica: occhiello a chip rosso, indicatore a pallini, cover editoriale con scrim."""
import os, io, urllib.request
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
FONTS = os.path.join(ASSETS, "fonts")
LIB = os.path.join(ASSETS, "bg-library")
LOGO = os.path.join(ASSETS, "logo-spaggiari-neg.png")
PF = os.path.join(FONTS, "PlayfairDisplay.ttf")
LX = os.path.join(FONTS, "LexendDeca.ttf")
SZ, PAD = 1080, 96
INK="#0E2A4D"; WHITE="#FFFFFF"; CYAN="#6fc2e7"; RED="#C8202B"; BODY="#D2DEEA"; FOOT="#8AA0B8"; LINE="#23456b"; DOT_OFF="#37597C"
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
    for s in range(maxsize, minsize-1, -2):
        if len(wrap(d, text, font(fam,s,w), maxw)) <= max_lines: return font(fam,s,w)
    return font(fam, minsize, w)

def block(d,t,x,y,f,fill,mw,lh=1.12):
    for line in wrap(d,t,f,mw):
        d.text((x,y),line,font=f,fill=fill); a,de=f.getmetrics(); y+=int((a+de)*lh)
    return y

def block_h(d,t,f,mw,lh=1.12):
    a,de=f.getmetrics(); return len(wrap(d,t,f,mw))*int((a+de)*lh)

_logo=None
def logo_img():
    global _logo
    if _logo is None:
        im=Image.open(LOGO).convert("RGBA"); _logo=im.crop(im.getbbox())
    return _logo

def _theme_bg(theme, variant):
    p=os.path.join(LIB, f"{theme}_{variant}.png")
    if not os.path.exists(p):
        alts=[f for f in os.listdir(LIB) if f.endswith(".png")]; p=os.path.join(LIB, sorted(alts)[0])
    return Image.open(p).convert("RGB").resize((SZ,SZ))

def _cover_from_url(url):
    try:
        req=urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r: data=r.read()
        im=Image.open(io.BytesIO(data)).convert("RGB")
        w,h=im.size; s=min(w,h); im=im.crop(((w-s)//2,(h-s)//2,(w-s)//2+s,(h-s)//2+s)).resize((SZ,SZ))
        return im
    except Exception:
        return None

def base(bg, cover=False):
    """Scrim navy. Per la cover: foto visibile in alto, scrim forte in basso per il testo."""
    bg=Image.blend(bg.convert("RGB"), Image.new("RGB",(SZ,SZ),INK), 0.16 if cover else 0.30)
    grad=Image.new("L",(1,SZ),0)
    for i in range(SZ):
        t=i/SZ
        if cover:
            a=int(245*max(0,(t-0.32)/0.68)); a=max(a, int(70*(1-t)))  # forte sotto + leggero sopra
        else:
            a=int(150*max(0,(t-0.52)/0.48))
        grad.putpixel((0,i), min(255,a))
    out=Image.composite(Image.new("RGB",(SZ,SZ),INK), bg, grad.resize((SZ,SZ)))
    # filetto ciano sottile sul bordo superiore: firma di brand coerente su tutte le card
    ImageDraw.Draw(out).rectangle([0,0,SZ,6], fill=CYAN)
    return out

def eyebrow_chip(d, t, y=120):
    f=font(LX,28,"SemiBold"); txt=t.upper(); ls=3
    tw=sum(d.textlength(c,font=f)+ls for c in txt)-ls
    px,py=26,16; bb=f.getbbox("Ag"); th=bb[3]-bb[1]
    d.rounded_rectangle([PAD,y,PAD+tw+2*px,y+th+2*py], radius=8, fill=RED)
    cx=PAD+px
    for c in txt:
        d.text((cx,y+py-bb[1]),c,font=f,fill=WHITE); cx+=d.textlength(c,font=f)+ls
    return y+th+2*py

def footer(img,d,page,total):
    d.line([(PAD,SZ-150),(SZ-PAD,SZ-150)],fill=LINE,width=2)
    lg=logo_img(); lw=300; lh=int(lg.height*lw/lg.width); lg=lg.resize((lw,lh))
    img.paste(lg,(PAD,SZ-128-(lh-34)//2),lg)
    # pallini indicatore
    r=8; gap=30; cy=SZ-114
    total_w=(total-1)*gap
    x0=SZ-PAD-total_w
    for i in range(total):
        cur = (i==page-1)
        col = CYAN if cur else DOT_OFF
        rr = r if cur else r-2
        d.ellipse([x0+i*gap-rr, cy-rr, x0+i*gap+rr, cy+rr], fill=col)

def build_gallery(content, article, outdir, datestr):
    os.makedirs(outdir, exist_ok=True)
    theme=content["theme"]; total=5; paths=[]
    def p(n): return os.path.join(outdir, f"card_{datestr}_{n}.png")

    # CARD 1 - cover editoriale (copertina articolo se c'e)
    cov=_cover_from_url(article.get("image","")) if article.get("image") else None
    img=base(cov if cov is not None else _theme_bg(theme,"a"), cover=True)
    d=ImageDraw.Draw(img); c=content["cover"]
    eyebrow_chip(d, c["eyebrow"])
    ft=fit_font(d,c["title"],PF,96,58,"Bold",SZ-2*PAD,3)
    hh=block_h(d,c.get("hi",""),font(LX,52,"SemiBold"),SZ-2*PAD)
    th=block_h(d,c["title"],ft,SZ-2*PAD,1.05)
    ystart=SZ-210-hh-30-th   # ancora il blocco testo appena sopra il footer
    y=block(d,c["title"],PAD,ystart,ft,WHITE,SZ-2*PAD,lh=1.05); y+=30
    block(d,c.get("hi",""),PAD,y,font(LX,52,"SemiBold"),CYAN,SZ-2*PAD)
    d.text((PAD,SZ-196),"Scorri →",font=font(LX,26,"SemiBold"),fill=CYAN)
    footer(img,d,1,total); img.save(p(1)); paths.append(p(1))

    # CARD 2-4 - testo
    for i,cc in enumerate(content["cards"], start=2):
        img=base(_theme_bg(theme, "a" if i%2 else "b")); d=ImageDraw.Draw(img)
        yb=eyebrow_chip(d, cc["eyebrow"])+44
        ft=fit_font(d,cc["title"],PF,78,52,"Bold",SZ-2*PAD,3)
        y=block(d,cc["title"],PAD,yb,ft,WHITE,SZ-2*PAD,lh=1.08); y+=28
        block(d,cc["body"],PAD,y,font(LX,38,"Regular"),BODY,SZ-2*PAD,lh=1.34)
        footer(img,d,i,total); img.save(p(i)); paths.append(p(i))

    # CARD 5 - CTA
    img=base(_theme_bg(theme,"b")); d=ImageDraw.Draw(img); cta=content["cta"]
    yb=eyebrow_chip(d, cta["eyebrow"])+44
    ft=fit_font(d,cta["title"],PF,76,50,"Bold",SZ-2*PAD,3)
    y=block(d,cta["title"],PAD,yb,ft,WHITE,SZ-2*PAD,lh=1.08); y+=24
    y=block(d,cta.get("body",""),PAD,y,font(LX,38,"Regular"),BODY,SZ-2*PAD,lh=1.34)
    fb=font(LX,34,"SemiBold"); lbl="Leggi l'articolo completo"; bb=fb.getbbox(lbl)
    tw=d.textlength(lbl,font=fb); px,py=44,26; w=tw+2*px; hh=(bb[3]-bb[1])+2*py; yy=y+34
    d.rounded_rectangle([PAD,yy,PAD+w,yy+hh],radius=12,fill=CYAN)
    d.text((PAD+px,yy+py-bb[1]),lbl,font=fb,fill=INK)
    d.text((PAD,yy+hh+18),"spaggiari.eu/news",font=font(LX,26,"Medium"),fill=CYAN)
    footer(img,d,5,total); img.save(p(5)); paths.append(p(5))
    return paths
