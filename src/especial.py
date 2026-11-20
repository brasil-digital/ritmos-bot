"""Vídeo LONGO "especial" do Ritmos: narração do Ronny (VoiceStudio, já gerada) + várias imagens por capítulo.

Diferente do longform.py (1 imagem por bloco, voz OpenAI), aqui:
  - a narração vem pronta da pasta do gerar_frases.py (<fala>.wav + tempos.json + falas.json com _exibir);
  - cada capítulo tem 4–8 imagens com zoom/pan e transição suave;
  - legenda sincronizada frase a frase pelos tempos reais da narração;
  - cartão de abertura de cada história ("HISTÓRIA 1 • LAMBADA");
  - trilha instrumental PRÓPRIA (músicas do Suno do canal, voz removida) baixinha por baixo.

Uso:
  python src/especial.py longos/<roteiro>.json            → monta em longos/out/<nome>/
  python src/especial.py longos/<roteiro>.json --imagens  → só gera as imagens (pra conferir antes)
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
from longform import scene_image  # noqa: E402
from longform_video import (ENC, FONT_ANTON, FPS, GREEN, H, RED, W, WHITE, YELLOW, _caption_png,  # noqa: E402
                            _frame_png, _mont, _run, _title_png, _wrap, audio_duration, concat, make_cover,
                            render_end_card)

PAUSE = 0.9      # respiro entre capítulos
FADE = 0.7       # transição entre imagens
CARD_SECS = 4.5  # cartão "HISTÓRIA N"
MUSIC_VOL = 0.11  # trilha por baixo da voz
MUSIC_VOL_END = 0.45

MOTIONS = [
    ("1+0.12*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    ("1.12-0.12*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
    ("1.1", "(iw-iw/zoom)*on/{n}", "ih/2-(ih/zoom/2)"),
    ("1.1", "(iw-iw/zoom)*(1-on/{n})", "ih/2-(ih/zoom/2)"),
    ("1.1", "iw/2-(iw/zoom/2)", "(ih-ih/zoom)*on/{n}"),
]


def exibir(texto, mapa):
    for k in sorted(mapa, key=len, reverse=True):
        texto = texto.replace(k, mapa[k])
    return texto


def story_card_png(card, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([(0, 330), (W, 800)], fill=(0, 0, 0, 170))
    d.rectangle([(0, 330), (W, 338)], fill=YELLOW)
    d.rectangle([(0, 792), (W, 800)], fill=GREEN)
    badge = f"HISTÓRIA {card['num']}"
    bf = _mont(48, b"Black")
    bw = d.textlength(badge, font=bf)
    d.rounded_rectangle([(W / 2 - bw / 2 - 34, 375), (W / 2 + bw / 2 + 34, 447)], radius=36, fill=RED)
    d.text((W / 2, 411), badge, font=bf, fill=WHITE, anchor="mm")
    size = 200
    while size > 90:
        font = ImageFont.truetype(FONT_ANTON, size)
        if d.textlength(card["nome"], font=font) <= 1700:
            break
        size -= 10
    d.text((W / 2, 585), card["nome"], font=font, fill=YELLOW, anchor="mm", stroke_width=9, stroke_fill=(0, 0, 0))
    d.text((W / 2, 735), card["info"], font=_mont(50, b"Black"), fill=WHITE, anchor="mm",
           stroke_width=4, stroke_fill=(0, 0, 0))
    img.save(path)


def captions(fala_texto, marcas, mapa, max_chars=84):
    """[(t0, t1, texto)] a partir dos tempos reais de cada frase (pedaço longo vira 2–3 legendas)."""
    out = []
    for m in marcas:
        txt = exibir(fala_texto[m["c0"]:m["c1"]].strip(), mapa)
        words = txt.split()
        k = max(1, -(-len(txt) // max_chars))
        per = -(-len(words) // k)
        parts = [" ".join(words[i:i + per]) for i in range(0, len(words), per)]
        span = (m["t1"] - m["t0"]) / len(parts)
        for j, p in enumerate(parts):
            out.append((m["t0"] + j * span, m["t0"] + (j + 1) * span + (0.25 if j == len(parts) - 1 else 0), p))
    return out


def render_section(idx, sec, imgs, voice_wav, caps, out_path, tmp, label):
    speech = audio_duration(voice_wav)
    dur = speech + PAUSE
    n_img = len(imgs)
    seg = dur / n_img
    frames = int((seg + FADE) * FPS) + 2

    cmd = ["ffmpeg", "-y"]
    for p in imgs:
        cmd += ["-i", p]
    filt = []
    for i in range(n_img):
        z, x, y = (m.format(n=frames) for m in MOTIONS[(idx + i) % len(MOTIONS)])
        filt.append(f"[{i}:v]scale=3840:-2,crop=3840:2160,zoompan=z='{z}':x='{x}':y='{y}':d={frames}:"
                    f"s={W}x{H}:fps={FPS},setsar=1,format=yuv420p[s{i}]")
    last = "s0"
    for i in range(1, n_img):
        filt.append(f"[{last}][s{i}]xfade=transition=fade:duration={FADE}:offset={i * seg:.3f}[x{i}]")
        last = f"x{i}"

    overlays = []
    frame = os.path.join(tmp, f"frame_{idx}.png")
    _frame_png(sec.get("heading", ""), label, frame)
    overlays.append((frame, None))
    card = sec.get("card")
    if card:
        cp = os.path.join(tmp, f"card_{idx}.png")
        if card["tipo"] == "titulo":
            _title_png(card["linha1"], card["linha2"], cp)
        else:
            story_card_png(card, cp)
        overlays.append((cp, (0.0, CARD_SECS)))
    for j, (t0, t1, txt) in enumerate(caps):
        p = os.path.join(tmp, f"cap_{idx}_{j}.png")
        _caption_png(txt, p)
        overlays.append((p, (t0, t1)))

    base = len(imgs)
    for p, _ in overlays:
        cmd += ["-i", p]
    cmd += ["-i", voice_wav]
    for k, (_, win) in enumerate(overlays):
        en = f":enable='between(t,{win[0]:.2f},{win[1]:.2f})'" if win else ""
        filt.append(f"[{last}][{base + k}:v]overlay=0:0{en}[o{k}]")
        last = f"o{k}"
    filt.append(f"[{base + len(overlays)}:a]aresample=44100,apad[a]")
    cmd += ["-filter_complex", ";".join(filt), "-map", f"[{last}]", "-map", "[a]", "-t", f"{dur:.3f}"] + ENC + [out_path]
    _run(cmd)
    return dur


def music_bed(sections, durations, trilhas, end_secs, out_path, tmp):
    """Uma faixa instrumental por capítulo (com fade), mais alta no cartão final."""
    parts = []
    offsets = {}
    for i, (sec, dur) in enumerate(zip(sections, durations)):
        src = trilhas[sec["trilha"]]
        start = offsets.get(src, 15.0)
        offsets[src] = start + dur
        p = os.path.join(tmp, f"trilha_{i}.wav")
        _run(["ffmpeg", "-y", "-stream_loop", "-1", "-ss", f"{start:.2f}", "-i", src, "-t", f"{dur:.3f}", "-af",
              f"volume={MUSIC_VOL},afade=t=in:d=1.2,afade=t=out:st={max(0, dur - 1.2):.2f}:d=1.2",
              "-ar", "44100", "-ac", "2", p])
        parts.append(p)
    p = os.path.join(tmp, "trilha_fim.wav")
    _run(["ffmpeg", "-y", "-ss", "40", "-i", trilhas[sections[-1]["trilha"]], "-t", str(end_secs), "-af",
          f"volume={MUSIC_VOL_END},afade=t=in:d=0.8,afade=t=out:st={end_secs - 2}:d=2", "-ar", "44100", "-ac", "2", p])
    parts.append(p)
    lst = os.path.join(tmp, "trilha.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for q in parts:
            f.write(f"file '{os.path.abspath(q).replace(os.sep, '/')}'\n")
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "pcm_s16le", out_path])


def main():
    path = sys.argv[1]
    script = json.load(open(path, encoding="utf-8"))
    name = os.path.splitext(os.path.basename(path))[0]
    wd = os.environ.get("OUT_DIR") or os.path.join(os.path.dirname(path), "out", name)
    os.makedirs(wd, exist_ok=True)
    sections = script["sections"]

    jobs = [(p, os.path.join(wd, f"img_{i:02d}_{j:02d}.png")) for i, s in enumerate(sections)
            for j, p in enumerate(s["images"])]
    jobs.append((script["thumb_image_prompt"], os.path.join(wd, "capa_bg.png")))
    print(f"🖼️  {len(jobs)} imagens...", flush=True)
    with ThreadPoolExecutor(max_workers=5) as pool:
        list(pool.map(lambda j: scene_image(*j), jobs))
    cover = make_cover(script, os.path.join(wd, "capa_bg.png"), os.path.join(wd, "capa.jpg"))
    if "--imagens" in sys.argv:
        print(f"ok, imagens em {wd}")
        return

    nd = script["narracao_dir"]
    falas_doc = json.load(open(os.path.join(nd, "falas.json"), encoding="utf-8"))
    falas = {f["id"]: f["texto"] for f in falas_doc["falas"]}
    mapa = falas_doc.get("_exibir", {})
    tempos = json.load(open(os.path.join(nd, "tempos.json"), encoding="utf-8"))

    parts, durations = [], []
    for i, sec in enumerate(sections):
        fid = sec["fala"]
        imgs = [os.path.join(wd, f"img_{i:02d}_{j:02d}.png") for j in range(len(sec["images"]))]
        caps = captions(falas[fid], tempos[fid], mapa)
        out = os.path.join(wd, f"bloco_{i:02d}.mp4")
        durations.append(render_section(i, sec, imgs, os.path.join(nd, fid + ".wav"), caps, out, wd,
                                        script.get("category_label", "ESPECIAL")))
        parts.append(out)
        print(f"   🎬 {i + 1}/{len(sections)} {sec['heading']} ({durations[-1]:.0f}s)", flush=True)
    end = os.path.join(wd, "final.mp4")
    end_secs = 10
    render_end_card(end, wd, seconds=end_secs, thanks="OBRIGADO POR ASSISTIR")
    parts.append(end)
    voz = os.path.join(wd, "video_voz.mp4")
    concat(parts, voz, wd)

    bed = os.path.join(wd, "trilha.wav")
    music_bed(sections, durations, script["trilhas"], end_secs, bed, wd)
    video = os.path.join(wd, "video_longo.mp4")
    _run(["ffmpeg", "-y", "-i", voz, "-i", bed, "-filter_complex",
          "[0:a]asplit=2[v][sc];[1:a][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=600[m];"
          "[v][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
          "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
          "-movflags", "+faststart", video])

    # capítulos p/ a descrição
    chapters, t = [], 0.0
    for sec, dur in zip(sections, durations):
        s = int(t)
        chapters.append(f"{s // 60:02d}:{s % 60:02d} {sec['heading']}")
        t += dur
    with open(os.path.join(wd, "capitulos.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(chapters))
    print(f"✅ {sum(durations) + end_secs:.0f}s → {video}\n   capa: {cover}")


if __name__ == "__main__":
    main()
