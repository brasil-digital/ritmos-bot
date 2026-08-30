import os
import math
import subprocess
import tempfile
import textwrap
from PIL import Image, ImageDraw, ImageFont

# YouTube Shorts: vertical 9:16
W, H = 1080, 1920

def _find_font(candidates):
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[0]


FONT_BOLD = _find_font([
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
])
FONT_REG = _find_font([
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "C:/Windows/Fonts/arial.ttf",
])
# Fonte de display para o cartão de título (Impact no Windows, Liberation no CI)
FONT_DISPLAY = _find_font([
    "C:/Windows/Fonts/impact.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
])

# Nome do canal (mantenha igual a CHANNEL_NAME em content_generator.py)
BRAND_NAME = "Ritmos do Brasil e do Mundo"

# Paleta da marca (verde/amarelo — herdada do logo do canal)
GREEN = (0, 168, 89)
YELLOW = (255, 210, 0)
BLUE = (0, 39, 118)
WHITE = (245, 245, 245)
LIGHT = (200, 210, 200)
BG_A = (10, 10, 20)
BG_B = (15, 30, 20)

# Gradientes por tipo de conteúdo (ângulo)
GRADIENTS = {
    "curiosidade":    ((10, 5, 30), (25, 15, 50)),
    "historia":       ((20, 10, 5), (40, 20, 10)),
    "genero":         ((25, 10, 5), (50, 20, 10)),
    "lenda":          ((5, 15, 30), (10, 30, 50)),
    "em_alta":        ((5, 25, 15), (10, 45, 25)),
    "instrumento":    ((22, 12, 5), (44, 26, 12)),
    "rivalidade":     ((20, 5, 5),  (40, 10, 10)),
    "letra":          ((5, 10, 30), (10, 20, 55)),
    "recorde":        ((25, 20, 5), (50, 40, 10)),
    "influencia":     ((8, 22, 24), (14, 40, 44)),
    # chaves antigas (compatibilidade)
    "artista_lenda":  ((5, 15, 30), (10, 30, 50)),
    "artista_atual":  ((5, 25, 15), (10, 45, 25)),
    "bossa_nova":     ((5, 10, 30), (10, 20, 55)),
    "default":        ((8, 15, 8),  (18, 30, 18)),
}

# Rótulo da tag do cartão de título por tipo de conteúdo (ângulo)
TYPE_LABELS = {
    "curiosidade": "CURIOSIDADE",
    "historia": "HISTÓRIA",
    "genero": "GÊNERO MUSICAL",
    "lenda": "LENDA DA MÚSICA",
    "em_alta": "EM ALTA",
    "instrumento": "INSTRUMENTO",
    "rivalidade": "RIVALIDADE",
    "letra": "POR TRÁS DA LETRA",
    "recorde": "RECORDE",
    "influencia": "CONEXÕES",
    # chaves antigas (compatibilidade)
    "artista_lenda": "LENDA DA MÚSICA",
    "artista_atual": "EM ALTA",
    "record": "RECORDE",
    "instrumentos": "INSTRUMENTO",
}

# Duração do cartão de título na abertura do Short (vira a miniatura padrão)
TITLE_CARD_DUR = 1.3


def _font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _gradient(draw, top, bot):
    for y in range(H):
        t = y / H
        r = int(top[0] + (bot[0] - top[0]) * t)
        g = int(top[1] + (bot[1] - top[1]) * t)
        b = int(top[2] + (bot[2] - top[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))


def _wrap_text(text, font, max_width, draw):
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current = []

    for word in words:
        test = " ".join(current + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def _make_slide(slide_text, slide_num, total_slides, content_type, subject, logo_path, radio_logo_path=None):
    img = Image.new("RGB", (W, H), BG_A)
    draw = ImageDraw.Draw(img)

    grad = GRADIENTS.get(content_type, GRADIENTS["default"])
    _gradient(draw, grad[0], grad[1])

    # Watermark: Rádio IA Fala Brasil logo (centralizado, semitransparente)
    if radio_logo_path and os.path.exists(radio_logo_path):
        try:
            wm = Image.open(radio_logo_path).convert("RGBA")
            wm_size = int(W * 0.72)
            wm = wm.resize((wm_size, wm_size), Image.LANCZOS)
            r, g, b, a = wm.split()
            a = a.point(lambda x: int(x * 0.18))
            wm.putalpha(a)
            wm_x = (W - wm_size) // 2
            wm_y = (H - wm_size) // 2 - 40
            img_rgba = img.convert("RGBA")
            img_rgba.paste(wm, (wm_x, wm_y), wm)
            img = img_rgba.convert("RGB")
            draw = ImageDraw.Draw(img)
        except Exception:
            pass

    # Top stripe
    draw.rectangle([(0, 0), (W, 10)], fill=GREEN)
    draw.rectangle([(0, 10), (W, 20)], fill=YELLOW)

    # Bottom stripe
    draw.rectangle([(0, H - 20), (W, H - 10)], fill=YELLOW)
    draw.rectangle([(0, H - 10), (W, H)], fill=GREEN)

    f_brand = _font(FONT_BOLD, 38)
    f_subject = _font(FONT_REG, 32)
    f_main = _font(FONT_BOLD, 64)
    f_cta = _font(FONT_BOLD, 52)
    f_small = _font(FONT_REG, 28)
    f_counter = _font(FONT_REG, 30)

    # Logo top-left
    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((100, 100), Image.LANCZOS)
            img.paste(logo, (40, 35), logo)
        except Exception:
            pass

    # Brand name top-right
    draw.text((W - 40, 65), BRAND_NAME, font=f_brand, fill=GREEN, anchor="rm")

    # Subject pill (centered, below brand)
    if subject and slide_num < total_slides:
        subj_text = f"♪  {subject.upper()}  ♪"
        draw.text((W // 2, 170), subj_text, font=f_subject, fill=YELLOW, anchor="mm")

    # Separator line
    sep_y = 220
    draw.rectangle([(80, sep_y), (W - 80, sep_y + 2)], fill=(60, 80, 60))

    # Main text — centered vertically in remaining space
    is_cta = slide_num == total_slides
    font_main = f_cta if is_cta else f_main
    max_w = W - 120
    lines = _wrap_text(slide_text, font_main, max_w, draw)

    line_h = 80 if not is_cta else 70
    total_text_h = len(lines) * line_h
    start_y = (H - total_text_h) // 2 + 30

    for i, line in enumerate(lines):
        y = start_y + i * line_h
        # Shadow
        draw.text((W // 2 + 2, y + 2), line, font=font_main, fill=(0, 0, 0), anchor="mm")
        color = GREEN if is_cta else WHITE
        draw.text((W // 2, y), line, font=font_main, fill=color, anchor="mm")

    # Progress dots at bottom
    dot_r = 10
    dot_gap = 35
    total_w = total_slides * (2 * dot_r) + (total_slides - 1) * (dot_gap - 2 * dot_r)
    start_x = (W - total_w) // 2 + dot_r
    for d in range(total_slides):
        cx = start_x + d * dot_gap
        cy = H - 50
        color = GREEN if d == slide_num - 1 else (60, 80, 60)
        draw.ellipse([(cx - dot_r, cy - dot_r), (cx + dot_r, cy + dot_r)], fill=color)

    return img


def _fit_display_font(draw, text, max_width, max_lines, start_size, min_size=60):
    """Encontra o maior tamanho de fonte cujo texto quebrado cabe em max_lines linhas."""
    size = start_size
    while size > min_size:
        font = _font(FONT_DISPLAY, size)
        lines = _wrap_text(text, font, max_width, draw)
        if len(lines) <= max_lines and all(
            draw.textbbox((0, 0), l, font=font)[2] <= max_width for l in lines
        ):
            return font, lines
        size -= 8
    font = _font(FONT_DISPLAY, min_size)
    return font, _wrap_text(text, font, max_width, draw)


def _make_title_card(content_type, subject, hook, logo_path, radio_logo_path=None):
    """Cartão de abertura no estilo das thumbnails do canal.

    O YouTube usa um frame do início como miniatura do Short, então este
    cartão vira a 'capa' do vídeo na página do canal e na busca.
    """
    img = Image.new("RGB", (W, H), BG_A)
    draw = ImageDraw.Draw(img)

    grad = GRADIENTS.get(content_type, GRADIENTS["default"])
    # Versão mais vibrante do gradiente do tipo
    top = tuple(min(255, int(c * 1.6)) for c in grad[0])
    bot = tuple(min(255, int(c * 2.6)) for c in grad[1])
    _gradient(draw, top, bot)

    # Watermark suave ao fundo
    if radio_logo_path and os.path.exists(radio_logo_path):
        try:
            wm = Image.open(radio_logo_path).convert("RGBA")
            wm_size = int(W * 0.9)
            wm = wm.resize((wm_size, wm_size), Image.LANCZOS)
            r, g, b, a = wm.split()
            a = a.point(lambda x: int(x * 0.12))
            wm.putalpha(a)
            img_rgba = img.convert("RGBA")
            img_rgba.paste(wm, ((W - wm_size) // 2, (H - wm_size) // 2), wm)
            img = img_rgba.convert("RGB")
            draw = ImageDraw.Draw(img)
        except Exception:
            pass

    # Faixas Brasil (mais grossas que nos slides)
    draw.rectangle([(0, 0), (W, 18)], fill=GREEN)
    draw.rectangle([(0, 18), (W, 36)], fill=YELLOW)
    draw.rectangle([(0, H - 36), (W, H - 18)], fill=YELLOW)
    draw.rectangle([(0, H - 18), (W, H)], fill=GREEN)

    # Logo grande no topo (recortado em círculo — o arquivo tem fundo preto)
    logo_bottom = 150
    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((190, 190), Image.LANCZOS)
            mask = Image.new("L", logo.size, 0)
            ImageDraw.Draw(mask).ellipse([(0, 0), logo.size], fill=255)
            img.paste(logo, ((W - logo.width) // 2, 110), mask)
            logo_bottom = 110 + logo.height
        except Exception:
            pass

    f_brand = _font(FONT_BOLD, 52)
    for i, ln in enumerate(("RITMOS DO BRASIL", "E DO MUNDO")):
        draw.text((W // 2, logo_bottom + 40 + i * 58), ln,
                  font=f_brand, fill=YELLOW, anchor="mm",
                  stroke_width=4, stroke_fill=(0, 0, 0))

    # Tag do tipo de conteúdo (pílula amarela)
    label = TYPE_LABELS.get(content_type, "RITMOS DO BRASIL E DO MUNDO")
    f_tag = _font(FONT_BOLD, 46)
    tb = draw.textbbox((0, 0), label, font=f_tag)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    tag_y = 640
    draw.rounded_rectangle(
        [(W // 2 - tw // 2 - 36, tag_y - th // 2 - 26),
         (W // 2 + tw // 2 + 36, tag_y + th // 2 + 26)],
        radius=22, fill=YELLOW)
    draw.text((W // 2, tag_y), label, font=f_tag, fill=(20, 20, 0), anchor="mm")

    # Assunto em letras GIGANTES (o "título da thumbnail")
    subject_up = (subject or "MÚSICA DO MUNDO").upper()
    font_subj, lines = _fit_display_font(draw, subject_up, W - 140, 3, 190)
    asc, desc = font_subj.getmetrics()
    line_h = int((asc + desc) * 1.02)
    total_h = line_h * len(lines)
    y0 = 1010 - total_h // 2
    for i, line in enumerate(lines):
        draw.text((W // 2, y0 + i * line_h), line, font=font_subj,
                  fill=WHITE, anchor="mm", stroke_width=10, stroke_fill=(0, 0, 0))

    # Hook como teaser abaixo do assunto
    if hook:
        f_hook = _font(FONT_BOLD, 54)
        hook_lines = _wrap_text(hook, f_hook, W - 200, draw)[:2]
        hy = y0 + total_h + 80
        for i, hl in enumerate(hook_lines):
            draw.text((W // 2, hy + i * 66), hl, font=f_hook,
                      fill=YELLOW, anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))

    # Chamada no rodapé
    f_cta = _font(FONT_BOLD, 44)
    draw.text((W // 2, H - 140), "ASSISTA ATÉ O FINAL",
              font=f_cta, fill=WHITE, anchor="mm",
              stroke_width=3, stroke_fill=(0, 0, 0))

    return img


def _audio_duration(audio_path: str) -> float:
    """Get audio duration in seconds using ffprobe."""
    result = subprocess.run([
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", audio_path
    ], capture_output=True, text=True)
    import json
    data = json.loads(result.stdout)
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "audio":
            return float(stream.get("duration", 45))
    return 45.0


def create_video(content, output_path="/tmp/ritmos_video.mp4", logo_path=None, audio_path=None, radio_logo_path=None):
    slides = content["slides"]
    content_type = content.get("type", "default")
    subject = content.get("subject", "")

    print(f"🎬 Criando Short: {content.get('youtube_title', BRAND_NAME)}")
    print(f"   Tipo: {content_type} | Assunto: {subject} | {len(slides)} slides")

    # Calcular duração de cada slide baseado no áudio
    if audio_path and os.path.exists(audio_path):
        total_duration = _audio_duration(audio_path)
        print(f"   Duração do áudio: {total_duration:.1f}s")
    else:
        total_duration = len(slides) * 9.0

    # Cartão de título abre o vídeo (vira a miniatura padrão do Short);
    # os slides dividem o tempo restante para manter o total = duração do áudio.
    card_dur = TITLE_CARD_DUR if total_duration > 8 else 0
    slide_dur = (total_duration - card_dur) / len(slides)

    with tempfile.TemporaryDirectory() as tmp:
        imgs = []
        if card_dur:
            card = _make_title_card(
                content_type, subject, content.get("hook", ""),
                logo_path, radio_logo_path=radio_logo_path
            )
            card_path = os.path.join(tmp, "slide_card.png")
            card.save(card_path)
            imgs.append((card_path, card_dur))
            print("   Cartão de título (capa do Short)")
        for i, slide in enumerate(slides):
            img = _make_slide(
                slide["text"], i + 1, len(slides),
                content_type, subject, logo_path,
                radio_logo_path=radio_logo_path
            )
            path = os.path.join(tmp, f"slide_{i:02d}.png")
            img.save(path)
            imgs.append((path, slide_dur))
            print(f"   Slide {i+1}/{len(slides)}")

        concat_file = os.path.join(tmp, "slides.txt")
        with open(concat_file, "w") as f:
            for path, dur in imgs:
                f.write(f"file '{path}'\n")
                f.write(f"duration {dur:.3f}\n")
            f.write(f"file '{imgs[-1][0]}'\n")

        slides_mp4 = os.path.join(tmp, "slides_silent.mp4")
        result = subprocess.run([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_file,
            "-vf", "fps=30,scale=1080:1920:flags=lanczos,format=yuv420p",
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            slides_mp4,
        ], capture_output=True)

        if result.returncode != 0:
            raise Exception(f"FFmpeg slides error: {result.stderr.decode()[-500:]}")

        # Combinar vídeo + narração
        if audio_path and os.path.exists(audio_path):
            result = subprocess.run([
                "ffmpeg", "-y",
                "-i", slides_mp4,
                "-i", audio_path,
                "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                "-movflags", "+faststart",
                output_path,
            ], capture_output=True)
        else:
            os.rename(slides_mp4, output_path)
            result = type("R", (), {"returncode": 0})()

        if result.returncode != 0:
            raise Exception(f"FFmpeg merge error: {result.stderr.decode()[-500:]}")

    print(f"✅ Vídeo criado: {output_path}")
    return output_path
