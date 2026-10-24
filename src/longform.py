"""Vídeo LONGO do Ritmos (aba Vídeos, 16:9) a partir de um roteiro pronto.

Série "Lendas da MPB": versões completas (8–10 min) dos temas que mais
seguram o público nos Shorts. Vídeo longo soma horas qualificadas p/ o YPP;
Short não soma.

Uso:
  python src/longform.py longos/x.json             → monta em OUT_DIR (padrão: longos/out/<nome>/), não publica
  python src/longform.py longos/x.json --publicar  → monta e publica (+ capa via thumbnails.set)

Roteiro JSON: category_label, subject, youtube_title, thumb_text, thumb_sub, badge,
thumb_image_prompt, youtube_description, tags, hashtags, sections[{heading, image_prompt, narration}].
"""
import base64
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

from openai import OpenAI

from longform_video import HANDLE, concat, make_cover, render_end_card, render_section

LIVE_URL = f"https://www.youtube.com/{HANDLE}/live"  # mesmo link dos Shorts (content_generator.LIVE_URL)
APP_LINE = "📱 Baixe o app Fala Brasil (iPhone e Android): https://www.falabrasil.digital/baixar/?src=youtube_ritmos"  # idem content_generator.APP_LINE

VOICE = "nova"  # fixa no vídeo inteiro (nos Shorts ela é sorteada)
SCENE_STYLE = (
    "Horizontal 16:9 cinematic documentary b-roll photograph, rich detail, dramatic natural light. "
    "Absolutely no text, letters, numbers, logos or watermarks. "
    "Do not depict any real, identifiable person or celebrity; people only as distant silhouettes or from behind. Scene: "
)

_client = None


def client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


def scene_image(prompt: str, out_path: str) -> str:
    if os.path.exists(out_path):  # reaproveita se já gerou (refazer só o que mudou)
        return out_path
    r = client().images.generate(model="gpt-image-1", size="1536x1024", quality="medium",
                                 prompt=SCENE_STYLE + prompt)
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(r.data[0].b64_json))
    return out_path


def narrate(text: str, out_path: str) -> str:
    if os.path.exists(out_path):
        return out_path
    r = client().audio.speech.create(model="tts-1-hd", voice=VOICE, input=text,
                                     response_format="mp3", speed=0.95)
    with open(out_path, "wb") as f:
        f.write(r.content)
    return out_path


def _ts(seconds: float) -> str:
    s = int(seconds)
    return f"{s // 60:02d}:{s % 60:02d}"


def build_description(script: dict, durations: list[float]) -> str:
    """Descrição + capítulos (YouTube exige 00:00, 3+ capítulos, cada um ≥10s)."""
    chapters, t = [], 0.0
    for sec, dur in zip(script["sections"], durations):
        if not chapters or (t - chapters[-1][0] >= 10 and dur >= 10):
            chapters.append((t, sec["heading"]))
        t += dur
    parts = [
        f"🔴 Rádio Ritmos do Brasil e do Mundo AO VIVO 24h: {LIVE_URL}",
        script["youtube_description"].strip(),
    ]
    if len(chapters) >= 3:
        parts.append("Capítulos:\n" + "\n".join(f"{_ts(s)} {h}" for s, h in chapters))
    parts.append(APP_LINE)
    parts.append(" ".join(script.get("hashtags") or ["#MPB"]))
    return "\n\n".join(parts)


def produce(script: dict, workdir: str):
    sections = script["sections"]
    os.makedirs(workdir, exist_ok=True)
    print(f"🎙️  Narração ({len(sections)} blocos, voz {VOICE}) + 🖼️  imagens...")
    with ThreadPoolExecutor(max_workers=4) as pool:
        imgs = list(pool.map(lambda p: scene_image(p[1]["image_prompt"], os.path.join(workdir, f"img_{p[0]:02d}.png")),
                             enumerate(sections)))
        audios = list(pool.map(lambda p: narrate(p[1]["narration"], os.path.join(workdir, f"voz_{p[0]:02d}.mp3")),
                               enumerate(sections)))
        cover_bg = scene_image(script["thumb_image_prompt"], os.path.join(workdir, "capa_bg.png"))

    cover = make_cover(script, cover_bg, os.path.join(workdir, "capa.jpg"))

    print("🎬 Montando os blocos...")
    parts, durations = [], []
    for i, sec in enumerate(sections):
        out = os.path.join(workdir, f"bloco_{i:02d}.mp4")
        title = (script["thumb_text"], script.get("thumb_sub", "")) if i == 0 else None
        durations.append(render_section(i, sec, imgs[i], audios[i], out, workdir,
                                        script.get("category_label", "LENDAS DA MPB"), title=title))
        parts.append(out)
        print(f"   Bloco {i + 1}/{len(sections)}: {sec['heading']} ({durations[-1]:.0f}s)")
    end = os.path.join(workdir, "final.mp4")
    render_end_card(end, workdir)
    parts.append(end)

    video = os.path.join(workdir, "video_longo.mp4")
    concat(parts, video, workdir)
    print(f"✅ Vídeo: {sum(durations) + 8:.0f}s → {video}")
    return video, cover, durations


def main():
    path = sys.argv[1]
    publish = "--publicar" in sys.argv
    with open(path, encoding="utf-8") as f:
        script = json.load(f)
    name = os.path.splitext(os.path.basename(path))[0]
    workdir = os.environ.get("OUT_DIR") or os.path.join(os.path.dirname(path), "out", name)

    video, cover, durations = produce(script, workdir)
    description = build_description(script, durations)
    with open(os.path.join(workdir, "descricao.txt"), "w", encoding="utf-8") as f:
        f.write(script["youtube_title"] + "\n\n" + description)

    if not publish:
        print(f"🧪 Não publicado. Confira: {workdir}")
        return

    from youtube_uploader import upload_video, set_thumbnail
    result = upload_video(video, {"youtube_title": script["youtube_title"],
                                  "youtube_description": description, "tags": script.get("tags", [])})
    set_thumbnail(result["id"], cover)
    print(f"🎉 Publicado: {result['url']}")


if __name__ == "__main__":
    main()
