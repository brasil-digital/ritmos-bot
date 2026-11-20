"""Shorts verticais do especial (narração do Ronny pronta no VoiceStudio + imagens do vídeo longo).

Uso: python src/especial_shorts.py longos/<shorts>.json   → longos/out/<nome>/<id>.mp4 + <id>.txt (título/descrição)
1º quadro = capa (Shorts não aceitam thumbnail por API).
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
from especial import FADE, MOTIONS, captions, exibir  # noqa: E402
from longform_video import (ENC, FONT_ANTON, FPS, GREEN, RED, WHITE, YELLOW, _mont, _paste_logo, _run,  # noqa: E402
                            _wrap, audio_duration)

W, H = 1080, 1920
COVER_SECS = 1.4
END_SECS = 2.5
BRAND = "RITMOS DO BRASIL E DO MUNDO"


def _bars(d):
    d.rectangle([(0, 0), (W, 10)], fill=GREEN)
    d.rectangle([(0, 10), (W, 18)], fill=YELLOW)


def cover_png(bg, hook, tag, path):
    src = Image.open(bg).convert("RGB")
    s = H / src.height
    src = src.resize((int(src.width * s) + 1, H), Image.LANCZOS)
    img = src.crop(((src.width - W) // 2, 0, (src.width - W) // 2 + W, H)).convert("RGBA")
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 120))
    img = Image.alpha_composite(img, shade)
    d = ImageDraw.Draw(img)
    _bars(d)
    tf = _mont(46, b"Black")
    tw = d.textlength(tag, font=tf)
    d.rounded_rectangle([(W / 2 - tw / 2 - 30, 330), (W / 2 + tw / 2 + 30, 400)], radius=35, fill=RED)
    d.text((W / 2, 365), tag, font=tf, fill=WHITE, anchor="mm")
    size = 150
    while size > 70:
        font = ImageFont.truetype(FONT_ANTON, size)
        lines = _wrap(d, hook.upper(), font, 960)
        if len(lines) <= 5:
            break
        size -= 8
    lh = int(size * 1.12)
    y = 900 - lh * len(lines) / 2
    for line in lines:
        d.text((W / 2, y + lh / 2), line, font=font, fill=YELLOW, anchor="mm", stroke_width=9, stroke_fill=(0, 0, 0))
        y += lh
    _paste_logo(img, 150, ((W - 150) // 2, 1560))
    d.text((W / 2, 1760), BRAND, font=_mont(38, b"Black"), fill=WHITE, anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))
    img.convert("RGB").save(path)


def frame_png(tag, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(260):
        d.line([(0, y), (W, y)], fill=(0, 0, 0, int(150 * (1 - y / 260))))
    _bars(d)
    x = 40 + _paste_logo(img, 90, (40, 50)) + 18
    d.text((x, 95), BRAND, font=_mont(30, b"Black"), fill=WHITE, anchor="lm", stroke_width=3, stroke_fill=(0, 0, 0))
    tf = _mont(36, b"Black")
    tw = d.textlength(tag, font=tf)
    d.rounded_rectangle([(40, 170), (40 + tw + 44, 228)], radius=29, fill=YELLOW)
    d.text((62 + tw / 2, 199), tag, font=tf, fill=(20, 20, 0), anchor="mm")
    img.save(path)


def caption_png(text, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    font = _mont(62, b"Black")
    lines = _wrap(d, text, font, 920)[:4]
    lh = 80
    y0 = 1330
    widest = max(d.textlength(l, font=font) for l in lines)
    d.rounded_rectangle([(W / 2 - widest / 2 - 30, y0 - 20), (W / 2 + widest / 2 + 30, y0 + lh * len(lines) + 14)],
                        radius=18, fill=(0, 0, 0, 175))
    for i, line in enumerate(lines):
        d.text((W / 2, y0 + i * lh + lh / 2), line, font=font, fill=WHITE, anchor="mm")
    img.save(path)


def end_png(path):
    img = Image.new("RGB", (W, H), (12, 10, 18))
    d = ImageDraw.Draw(img)
    _bars(d)
    _paste_logo(img, 260, ((W - 260) // 2, 420))
    for i, (t, f, c) in enumerate([("A HISTÓRIA COMPLETA", ImageFont.truetype(FONT_ANTON, 110), YELLOW),
                                   ("ESTÁ NO CANAL", ImageFont.truetype(FONT_ANTON, 110), YELLOW),
                                   ("5 músicas brasileiras que", _mont(54, b"ExtraBold"), WHITE),
                                   ("conquistaram o mundo", _mont(54, b"ExtraBold"), WHITE)]):
        d.text((W / 2, 820 + i * 125 + (40 if i >= 2 else 0)), t, font=f, fill=c, anchor="mm",
               stroke_width=5 if i < 2 else 0, stroke_fill=(0, 0, 0))
    d.text((W / 2, 1460), "@ritmos-do-mundo", font=_mont(58, b"Black"), fill=WHITE, anchor="mm")
    img.save(path)


def render_short(sh, wd_long, nd, mapa, falas, tempos, music, out_dir):
    sid = sh["fala"]
    voice = os.path.join(nd, sid + ".wav")
    speech = audio_duration(voice)
    body = speech + 0.6
    imgs = [os.path.join(wd_long, f) for f in sh["images"]]
    n_img = len(imgs)
    seg = body / n_img
    frames = int((seg + FADE) * FPS) + 2
    tmp = os.path.join(out_dir, "tmp_" + sid)
    os.makedirs(tmp, exist_ok=True)

    cover = os.path.join(tmp, "cover.png")
    cover_png(os.path.join(wd_long, sh["cover_image"]), sh["hook"], sh["tag"], cover)
    frame = os.path.join(tmp, "frame.png")
    frame_png(sh["tag"], frame)
    endp = os.path.join(tmp, "end.png")
    end_png(endp)

    cmd = ["ffmpeg", "-y"]
    for p in imgs:
        cmd += ["-i", p]
    filt = []
    for i in range(n_img):
        z, x, y = (m.format(n=frames) for m in MOTIONS[i % 2])
        filt.append(f"[{i}:v]scale=-2:3840,crop=2160:3840,zoompan=z='{z}':x='{x}':y='{y}':d={frames}:"
                    f"s={W}x{H}:fps={FPS},setsar=1,format=yuv420p[s{i}]")
    last = "s0"
    for i in range(1, n_img):
        filt.append(f"[{last}][s{i}]xfade=transition=fade:duration={FADE}:offset={i * seg:.3f}[x{i}]")
        last = f"x{i}"
    overlays = [(frame, None)]
    for j, (t0, t1, txt) in enumerate(captions(falas[sid], tempos[sid], mapa, max_chars=70)):
        p = os.path.join(tmp, f"cap_{j}.png")
        caption_png(txt, p)
        overlays.append((p, (t0, t1)))
    base = n_img
    for p, _ in overlays:
        cmd += ["-i", p]
    for k, (_, win) in enumerate(overlays):
        en = f":enable='between(t,{win[0]:.2f},{win[1]:.2f})'" if win else ""
        filt.append(f"[{last}][{base + k}:v]overlay=0:0{en}[o{k}]")
        last = f"o{k}"
    filt.append(f"[{last}]trim=duration={body:.3f},setpts=PTS-STARTPTS[body]")
    ci = base + len(overlays)
    cmd += ["-loop", "1", "-t", str(COVER_SECS), "-i", cover, "-loop", "1", "-t", str(END_SECS), "-i", endp,
            "-i", voice, "-stream_loop", "-1", "-ss", str(sh.get("music_start", 20)), "-i", music]
    filt.append(f"[{ci}:v]scale={W}:{H},fps={FPS},format=yuv420p,setsar=1[cv]")
    filt.append(f"[{ci + 1}:v]scale={W}:{H},fps={FPS},format=yuv420p,setsar=1[ev]")
    filt.append("[cv][body][ev]concat=n=3:v=1:a=0[v]")
    total = COVER_SECS + body + END_SECS
    d_ms = int(COVER_SECS * 1000)
    filt.append(f"[{ci + 2}:a]aresample=44100,aformat=channel_layouts=stereo,adelay={d_ms}|{d_ms},apad[vo]")
    filt.append(f"[{ci + 3}:a]aresample=44100,aformat=channel_layouts=stereo,volume=0.13,"
                f"afade=t=out:st={total - 1.5:.2f}:d=1.5[mu]")
    filt.append("[vo]asplit=2[vo1][sc];[mu][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=600[md];"
                "[vo1][md]amix=inputs=2:duration=longest:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    out = os.path.join(out_dir, sid + ".mp4")
    cmd += ["-filter_complex", ";".join(filt), "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}"] + ENC + [out]
    _run(cmd)
    return out, total


def main():
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    name = os.path.splitext(os.path.basename(sys.argv[1]))[0]
    out_dir = os.path.join(os.path.dirname(sys.argv[1]), "out", name)
    os.makedirs(out_dir, exist_ok=True)
    nd = cfg["narracao_dir"]
    doc = json.load(open(os.path.join(nd, "falas.json"), encoding="utf-8"))
    falas = {f["id"]: f["texto"] for f in doc["falas"]}
    tempos = json.load(open(os.path.join(nd, "tempos.json"), encoding="utf-8"))
    mapa = doc.get("_exibir", {})
    only = sys.argv[2:] or None
    for sh in cfg["shorts"]:
        if only and sh["fala"] not in only:
            continue
        out, total = render_short(sh, cfg["imagens_dir"], nd, mapa, falas, tempos, cfg["trilhas"][sh["trilha"]], out_dir)
        with open(out[:-4] + ".txt", "w", encoding="utf-8") as f:
            f.write(sh["title"] + "\n\n" + sh["description"] + "\n\nTAGS: " + ", ".join(sh["tags"]))
        print(f"✅ {sh['fala']} {total:.1f}s → {out}", flush=True)


if __name__ == "__main__":
    main()
