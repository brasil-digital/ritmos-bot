"""Monta o vídeo LONGO 16:9 (1920x1080) do Ritmos a partir do roteiro em blocos.

Base: longform_video.py do brasil-digital-bot, com a marca do Ritmos.
Cada bloco = narração própria + imagem própria com movimento (zoom/pan) +
título do bloco (capítulo) + legenda frase a frase. No fim, cartão com a
live 24h da Rádio + inscrição. Sem música de fundo: música de terceiros dá
Content ID, e a narração é o conteúdo.
"""
import json
import os
import re
import subprocess

from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
FPS = 30
PAUSE = 0.6  # respiro entre um bloco e outro

ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")
FONT_ANTON = os.path.join(ASSETS, "fonts", "Anton-Regular.ttf")
FONT_MONT = os.path.join(ASSETS, "fonts", "Montserrat.ttf")
LOGO = os.path.join(ASSETS, "logo.png")

BRAND = "RITMOS DO BRASIL E DO MUNDO"
HANDLE = "@ritmos-do-mundo"

WHITE = (255, 255, 255)
YELLOW = (255, 210, 0)
GREEN = (0, 168, 89)
RED = (230, 33, 23)
DARK = (12, 10, 18)

ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", "-r", str(FPS),
       "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2"]


def _mont(size, weight=b"ExtraBold"):
    f = ImageFont.truetype(FONT_MONT, size)
    try:
        f.set_variation_by_name(weight)
    except Exception:
        pass
    return f


def _run(cmd):
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        raise Exception(f"FFmpeg falhou: {r.stderr.decode(errors='ignore')[-800:]}")


def audio_duration(path: str) -> float:
    r = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
                       capture_output=True, text=True)
    return float(json.loads(r.stdout)["format"]["duration"])


def _wrap(draw, text, font, max_w):
    lines, cur = [], []
    for word in text.split():
        test = " ".join(cur + [word])
        if cur and draw.textlength(test, font=font) > max_w:
            lines.append(" ".join(cur))
            cur = [word]
        else:
            cur.append(word)
    if cur:
        lines.append(" ".join(cur))
    return lines


def caption_chunks(text: str, max_chars: int = 84) -> list[str]:
    """Frases da narração em pedaços de no máx ~2 linhas de legenda."""
    chunks = []
    for sent in re.split(r"(?<=[.!?…])\s+", text.strip()):
        words = sent.split()
        if not words:
            continue
        k = -(-len(sent) // max_chars)
        target = len(sent) / k
        parts, cur = [], []
        for word in words:
            cur.append(word)
            if len(parts) < k - 1 and len(" ".join(cur)) >= target:
                parts.append(" ".join(cur))
                cur = []
        if cur:
            parts.append(" ".join(cur))
        chunks += parts
    return chunks


def _paste_logo(img, size, pos):
    if not os.path.exists(LOGO):
        return 0
    logo = Image.open(LOGO).convert("RGBA")
    logo.thumbnail((size, size), Image.LANCZOS)
    mask = Image.new("L", logo.size, 0)
    ImageDraw.Draw(mask).ellipse([(0, 0), logo.size], fill=255)
    img.paste(logo, pos, mask)
    return logo.width


def _caption_png(text, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    font = _mont(46)
    lines = _wrap(d, text, font, 1500)[:3]
    lh = 60
    y0 = H - 70 - lh * len(lines)
    widest = max(d.textlength(l, font=font) for l in lines)
    d.rounded_rectangle([(W / 2 - widest / 2 - 28, y0 - 16), (W / 2 + widest / 2 + 28, H - 58)],
                        radius=14, fill=(0, 0, 0, 165))
    for i, line in enumerate(lines):
        d.text((W / 2, y0 + i * lh + lh / 2 - 6), line, font=font, fill=WHITE, anchor="mm")
    img.save(path)


def _frame_png(heading, category_label, path):
    """Moldura fixa do bloco: marca, série e título do capítulo."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(200):
        d.line([(0, y), (W, y)], fill=(0, 0, 0, int(140 * (1 - y / 200))))
    d.rectangle([(0, 0), (W, 7)], fill=GREEN)
    d.rectangle([(0, 7), (W, 13)], fill=YELLOW)
    x = 44 + _paste_logo(img, 82, (44, 32)) + 16
    d.text((x, 73), BRAND, font=_mont(32, b"Black"), fill=WHITE, anchor="lm",
           stroke_width=3, stroke_fill=(0, 0, 0))
    cf = _mont(26, b"Black")
    cw = d.textlength(category_label, font=cf)
    d.rounded_rectangle([(W - 44 - cw - 44, 50), (W - 44, 96)], radius=23, fill=YELLOW)
    d.text((W - 44 - 22 - cw / 2, 73), category_label, font=cf, fill=(20, 20, 0), anchor="mm")
    if heading:
        hf = _mont(40, b"Black")
        hw = d.textlength(heading.upper(), font=hf)
        d.rectangle([(44, 136), (54, 196)], fill=YELLOW)
        d.rectangle([(54, 136), (54 + hw + 40, 196)], fill=(0, 0, 0, 175))
        d.text((74, 166), heading.upper(), font=hf, fill=WHITE, anchor="lm")
    img.save(path)


def _title_png(text, sub, path):
    """Título gigante no começo do vídeo (primeiros segundos do gancho)."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([(0, 300), (W, 790)], fill=(0, 0, 0, 155))
    size = 190
    while size > 80:
        font = ImageFont.truetype(FONT_ANTON, size)
        lines = _wrap(d, text.upper(), font, 1700)
        if len(lines) <= 2:
            break
        size -= 10
    lh = int(size * 1.15)
    y0 = 500 - lh * len(lines) / 2
    for i, line in enumerate(lines):
        d.text((W / 2, y0 + i * lh + lh / 2), line, font=font, fill=YELLOW, anchor="mm",
               stroke_width=8, stroke_fill=(0, 0, 0))
    if sub:
        d.text((W / 2, 700), sub.upper(), font=_mont(64, b"Black"), fill=WHITE, anchor="mm",
               stroke_width=4, stroke_fill=(0, 0, 0))
    img.save(path)


def _end_card_png(path):
    img = Image.new("RGB", (W, H), DARK)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(12 + 8 * t), int(10 + 28 * t), int(18 + 10 * t)))
    d.rectangle([(0, 0), (W, 10)], fill=GREEN)
    d.rectangle([(0, 10), (W, 18)], fill=YELLOW)
    d.rectangle([(0, H - 18), (W, H - 10)], fill=YELLOW)
    d.rectangle([(0, H - 10), (W, H)], fill=GREEN)
    _paste_logo(img, 230, ((W - 230) // 2, 90))
    d.text((W / 2, 400), "OBRIGADA POR ASSISTIR", font=_mont(66, b"Black"), fill=WHITE, anchor="mm")
    d.text((W / 2, 480), f"Inscreva-se no Ritmos do Brasil e do Mundo  •  {HANDLE}", font=_mont(40, b"Bold"),
           fill=YELLOW, anchor="mm")
    # selo AO VIVO (mesmo do slide final dos Shorts)
    lf = _mont(70, b"Black")
    label = "AO VIVO 24h"
    lw = d.textlength(label, font=lf)
    dot = 44
    pw = dot + 28 + lw
    px, py = (W - pw) / 2, 660
    d.rounded_rectangle([(px - 50, py - 62), (px + pw + 50, py + 62)], radius=36, fill=RED)
    d.ellipse([(px, py - dot / 2), (px + dot, py + dot / 2)], fill=WHITE)
    d.text((px + dot + 28, py), label, font=lf, fill=WHITE, anchor="lm")
    d.text((W / 2, 820), "Ouça a Rádio aqui no canal: músicas originais o dia todo", font=_mont(48, b"ExtraBold"),
           fill=WHITE, anchor="mm")
    img.save(path)


MOTIONS = [
    ("1+0.13*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    ("1.13-0.13*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    ("1.12", "(iw-iw/zoom)*on/{n}", "ih/2-(ih/zoom/2)"),
    ("1.12", "(iw-iw/zoom)*(1-on/{n})", "ih/2-(ih/zoom/2)"),
]


def render_section(idx, section, img_path, audio_path, out_path, tmp, category_label, title=None):
    speech = audio_duration(audio_path)
    dur = speech + PAUSE
    n = int(dur * FPS) + 1
    z, x, y = (m.format(n=n) for m in MOTIONS[idx % len(MOTIONS)])

    frame = os.path.join(tmp, f"frame_{idx}.png")
    _frame_png(section.get("heading", ""), category_label, frame)
    overlays = [(frame, None)]
    if title:
        tp = os.path.join(tmp, f"title_{idx}.png")
        _title_png(title[0], title[1], tp)
        overlays.append((tp, (0.0, 4.0)))

    chunks = caption_chunks(section["narration"])
    total_chars = sum(len(c) for c in chunks) or 1
    t = 0.0
    for j, chunk in enumerate(chunks):
        span = speech * len(chunk) / total_chars
        cp = os.path.join(tmp, f"cap_{idx}_{j}.png")
        _caption_png(chunk, cp)
        overlays.append((cp, (t, t + span)))
        t += span

    cmd = ["ffmpeg", "-y", "-i", img_path]
    for p, _ in overlays:
        cmd += ["-i", p]
    cmd += ["-i", audio_path]

    filt = [f"[0:v]scale=3840:-2,crop=3840:2160,zoompan=z='{z}':x='{x}':y='{y}':d={n}:s={W}x{H}:fps={FPS}[v0]"]
    for k, (_, window) in enumerate(overlays, start=1):
        en = f":enable='between(t,{window[0]:.2f},{window[1]:.2f})'" if window else ""
        filt.append(f"[v{k-1}][{k}:v]overlay=0:0{en}[v{k}]")
    filt.append(f"[{len(overlays) + 1}:a]apad[a]")

    cmd += ["-filter_complex", ";".join(filt), "-map", f"[v{len(overlays)}]", "-map", "[a]",
            "-t", f"{dur:.3f}"] + ENC + [out_path]
    _run(cmd)
    return dur


def render_end_card(out_path, tmp, seconds=8):
    png = os.path.join(tmp, "endcard.png")
    _end_card_png(png)
    _run(["ffmpeg", "-y", "-loop", "1", "-i", png, "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
          "-t", str(seconds), "-vf", f"scale={W}:{H}"] + ENC + [out_path])


def concat(parts, out_path, tmp):
    lst = os.path.join(tmp, "parts.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for p in parts:
            f.write(f"file '{os.path.abspath(p).replace(os.sep, '/')}'\n")
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
          "-movflags", "+faststart", out_path])


def make_cover(script, bg_path, out_path, size=(1280, 720)):
    """Thumbnail 16:9: imagem de fundo escurecida à esquerda + nome gigante + frase."""
    w, h = size
    if bg_path and os.path.exists(bg_path):
        src = Image.open(bg_path).convert("RGB")
        scale = max(w / src.width, h / src.height)
        src = src.resize((int(src.width * scale) + 1, int(src.height * scale) + 1), Image.LANCZOS)
        img = src.crop(((src.width - w) // 2, (src.height - h) // 2, (src.width - w) // 2 + w,
                        (src.height - h) // 2 + h))
    else:
        img = Image.new("RGB", (w, h), DARK)
    shade = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    for x in range(w):
        sd.line([(x, 0), (x, h)], fill=(0, 0, 0, int(215 * max(0, 1 - x / (w * 0.8)))))
    img = Image.alpha_composite(img.convert("RGBA"), shade).convert("RGB")
    d = ImageDraw.Draw(img)
    d.rectangle([(0, 0), (w, 8)], fill=GREEN)
    d.rectangle([(0, 8), (w, 15)], fill=YELLOW)

    badge = script.get("badge", "").upper()
    if badge:
        bf = _mont(34, b"Black")
        bw = d.textlength(badge, font=bf)
        d.rounded_rectangle([(48, 52), (48 + bw + 52, 108)], radius=28, fill=RED)
        d.text((48 + 26 + bw / 2, 80), badge, font=bf, fill=WHITE, anchor="mm")

    # nome: no máx 2 linhas e ~330 px de altura, pra frase caber embaixo
    name = script["thumb_text"].upper()
    size_ = 200
    while size_ > 70:
        font = ImageFont.truetype(FONT_ANTON, size_)
        lines = _wrap(d, name, font, int(w * 0.66))
        asc, desc = font.getmetrics()
        lh = int((asc + desc) * 0.95)
        if len(lines) <= 2 and lh * len(lines) <= 330:
            break
        size_ -= 10
    y = 140
    for line in lines:
        d.text((48, y), line, font=font, fill=YELLOW, anchor="la", stroke_width=9, stroke_fill=(0, 0, 0))
        y += lh
    sub = script.get("thumb_sub", "").upper()
    if sub:
        sf = _mont(54, b"Black")
        for line in _wrap(d, sub, sf, int(w * 0.62)):
            d.text((48, y + 10), line, font=sf, fill=WHITE, anchor="la", stroke_width=4, stroke_fill=(0, 0, 0))
            y += 66
    d.text((48, h - 45), f"{BRAND}  •  {HANDLE}", font=_mont(26, b"ExtraBold"),
           fill=WHITE, anchor="lm", stroke_width=3, stroke_fill=(0, 0, 0))
    img.save(out_path, quality=90)
    return out_path
