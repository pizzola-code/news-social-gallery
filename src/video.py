# -*- coding: utf-8 -*-
"""Crea uno YouTube Short 9:16 (1080x1920) dalle 5 card: ciascuna card a fuoco al
centro su sfondo sfocato della card stessa, slideshow con dissolvenze + musica.
ffmpeg: usa quello di sistema (CI) o il binario di imageio-ffmpeg (locale)."""
import os, subprocess, tempfile
from PIL import Image, ImageFilter, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
MUSIC = os.path.join(ASSETS, "music", "inspired-kevinmacleod.mp3")
LX = os.path.join(ASSETS, "fonts", "LexendDeca.ttf")
W, H = 1080, 1920
INK = "#0E2A4D"; CYAN = "#6fc2e7"
SEC_PER = 3.0   # secondi per card
FADE = 0.4

def _ffmpeg():
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

def _vertical_frame(card_path):
    card = Image.open(card_path).convert("RGB")  # 1080x1080
    s = card.resize((W, W))                          # card a fuoco (full width)
    big = card.resize((H, H))                       # 1920x1920
    bg = big.crop(((H-W)//2, 0, (H-W)//2 + W, H))   # 1080x1920 centro
    bg = bg.filter(ImageFilter.GaussianBlur(45))
    bg = Image.blend(bg, Image.new("RGB", (W, H), INK), 0.55)
    frame = bg.copy()
    frame.paste(s, (0, (H - W)//2))                 # card a fuoco centrata
    d = ImageDraw.Draw(frame)
    d.rectangle([0, 0, W, 6], fill=CYAN)            # filetto ciano top
    # bordino ciano sopra/sotto la card
    y0 = (H - W)//2
    d.line([(0, y0-2), (W, y0-2)], fill=CYAN, width=2)
    d.line([(0, y0+W+2), (W, y0+W+2)], fill=CYAN, width=2)
    return frame

def build_short(card_paths, out_path, music=MUSIC):
    ff = _ffmpeg()
    n = len(card_paths); total = SEC_PER * n
    with tempfile.TemporaryDirectory() as tmp:
        clips = []
        for i, cp in enumerate(card_paths):
            fp = os.path.join(tmp, f"f{i}.png"); _vertical_frame(cp).save(fp)
            cl = os.path.join(tmp, f"c{i}.mp4")
            vf = (f"fade=t=in:st=0:d={FADE},fade=t=out:st={SEC_PER-FADE}:d={FADE},format=yuv420p")
            subprocess.run([ff, "-y", "-loop", "1", "-t", str(SEC_PER), "-i", fp,
                            "-vf", vf, "-r", "30", "-c:v", "libx264", "-pix_fmt", "yuv420p", cl],
                           check=True, capture_output=True)
            clips.append(cl)
        lst = os.path.join(tmp, "list.txt")
        with open(lst, "w") as f:
            for cl in clips: f.write(f"file '{cl}'\n")
        slide = os.path.join(tmp, "slide.mp4")
        subprocess.run([ff, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", slide],
                       check=True, capture_output=True)
        if music and os.path.exists(music):
            subprocess.run([ff, "-y", "-i", slide, "-i", music,
                            "-filter_complex", f"[1:a]afade=t=out:st={total-2}:d=2[a]",
                            "-map", "0:v", "-map", "[a]", "-t", str(total),
                            "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", out_path],
                           check=True, capture_output=True)
        else:
            subprocess.run([ff, "-y", "-i", slide, "-c", "copy", out_path], check=True, capture_output=True)
    return out_path

# crediti musica (CC-BY) da aggiungere alla descrizione YouTube
MUSIC_CREDIT = 'Musica: "Inspired" di Kevin MacLeod (incompetech.com) - Licenza Creative Commons BY 4.0'

if __name__ == "__main__":
    import glob, sys
    cards = sorted(glob.glob(os.path.join(ROOT, "out", "card_*_*.png")))
    print("card:", len(cards))
    out = os.path.join(ROOT, "out", "short_test.mp4")
    build_short(cards, out); print("OK", out, os.path.getsize(out), "bytes")
