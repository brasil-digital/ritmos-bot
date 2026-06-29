import os
import math
import subprocess
import tempfile
import textwrap
from PIL import Image, ImageDraw, ImageFont

# YouTube Shorts: vertical 9:16
W, H = 1080, 1920

FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

# Paleta Brasil
GREEN = (0, 168, 89)
YELLOW = (255, 210, 0)
BLUE = (0, 39, 118)
WHITE = (245, 245, 245)
LIGHT = (200, 210, 200)
BG_A = (10, 10, 20)
BG_B = (15, 30, 20)

# Gradientes por tipo de conteúdo
GRADIENTS = {
    "curiosidade":    ((10, 5, 30), (25, 15, 50)),
    "historia":       ((20, 10, 5), (40, 20, 10)),
    "artista_lenda":  ((5, 15, 30), (10, 30, 50)),
    "artista_atual":  ((5, 25, 15), (10, 45, 25)),
    "genero":         ((25, 10, 5), (50, 20, 10)),
    "samba":          ((20, 5, 5),  (40, 10, 10)),
    "forro":          ((25, 15, 5), (50, 30, 10)),
    "bossa_nova":     ((5, 10, 30), (10, 20, 55)),
    "default":        ((8, 15, 8),  (18, 30, 18)),
}


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

    # Decorative background circles (subtle)
    for cx, cy, r, alpha in [(W // 2, H // 3, 350, 15), (W // 4, 2 * H // 3, 200, 10)]:
        for dr in range(r, r - 40, -5):
            draw.ellipse([(cx - dr, cy - dr), (cx + dr, cy + dr)],
                         outline=(255, 255, 255, alpha), width=1)

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
    draw.text((W - 40, 65), "Ritmos do Brasil", font=f_brand, fill=GREEN, anchor="rm")

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

    print(f"🎬 Criando Short: {content.get('youtube_title', 'Ritmos do Brasil')}")
    print(f"   Tipo: {content_type} | Assunto: {subject} | {len(slides)} slides")

    # Calcular duração de cada slide baseado no áudio
    if audio_path and os.path.exists(audio_path):
        total_duration = _audio_duration(audio_path)
        print(f"   Duração do áudio: {total_duration:.1f}s")
    else:
        total_duration = len(slides) * 9.0

    slide_dur = total_duration / len(slides)

    with tempfile.TemporaryDirectory() as tmp:
        imgs = []
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
