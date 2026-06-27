import os
import math
import subprocess
import tempfile
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
FONT_PATH_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_PATH = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

# Brand colors — Brasil
GREEN = (0, 168, 89)
YELLOW = (255, 220, 0)
WHITE = (240, 240, 240)
LIGHT_GRAY = (180, 180, 200)
BG_TOP = (8, 8, 18)
BG_BOT = (18, 28, 22)


def _load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _draw_gradient(draw):
    for y in range(H):
        ratio = y / H
        r = int(BG_TOP[0] + (BG_BOT[0] - BG_TOP[0]) * ratio)
        g = int(BG_TOP[1] + (BG_BOT[1] - BG_TOP[1]) * ratio)
        b = int(BG_TOP[2] + (BG_BOT[2] - BG_TOP[2]) * ratio)
        draw.line([(0, y), (W, y)], fill=(r, g, b))


def _split_lyrics(lyrics, num_slides):
    # Keep section headers with their content
    lines = [l.strip() for l in lyrics.split("\n")]
    chunks, current = [], []
    lines_per_chunk = max(1, math.ceil(len(lines) / num_slides))

    for line in lines:
        current.append(line)
        if len(current) >= lines_per_chunk:
            chunks.append("\n".join(current))
            current = []

    if current:
        chunks.append("\n".join(current))

    return chunks[:num_slides]


def _make_slide(text, title, genre, slide_num, total, logo_path):
    img = Image.new("RGB", (W, H), BG_TOP)
    draw = ImageDraw.Draw(img)
    _draw_gradient(draw)

    # Top stripe — Brasil flag colors
    draw.rectangle([(0, 0), (W, 7)], fill=GREEN)
    draw.rectangle([(0, 7), (W, 14)], fill=YELLOW)

    # Bottom stripe
    draw.rectangle([(0, H - 14), (W, H - 7)], fill=YELLOW)
    draw.rectangle([(0, H - 7), (W, H)], fill=GREEN)

    f_title = _load_font(FONT_PATH_BOLD, 56)
    f_genre = _load_font(FONT_PATH, 34)
    f_lyrics = _load_font(FONT_PATH, 46)
    f_small = _load_font(FONT_PATH, 26)

    # Song title
    draw.text((W // 2, 60), title, font=f_title, fill=WHITE, anchor="mm")

    # Genre badge
    draw.text((W // 2, 125), f"♪  {genre.upper()}  ♪", font=f_genre, fill=GREEN, anchor="mm")

    # Separator
    draw.rectangle([(W // 4, 155), (3 * W // 4, 157)], fill=(50, 60, 60))

    # Lyrics
    y = H // 2 - 80
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            y += 22
            continue
        if line.startswith("[") and line.endswith("]"):
            draw.text((W // 2, y), line, font=f_genre, fill=(140, 160, 200), anchor="mm")
            y += 48
        else:
            draw.text((W // 2, y), line, font=f_lyrics, fill=WHITE, anchor="mm")
            y += 58

    # Branding
    draw.text((W // 2, H - 40), "Ritmos do Brasil", font=f_genre, fill=GREEN, anchor="mm")
    draw.text((W - 50, H - 40), f"{slide_num}/{total}", font=f_small, fill=(90, 90, 110), anchor="rm")

    # Logo
    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((90, 90), Image.LANCZOS)
            img.paste(logo, (40, 40), logo)
        except Exception as e:
            print(f"Aviso logo: {e}")

    return img


def create_video(concept, audio_info, output_path="/tmp/video.mp4", logo_path=None):
    title = concept["title"]
    genre = concept["genre"]
    lyrics = concept["lyrics"]
    audio_path = audio_info["path"]
    duration = float(audio_info.get("duration", 180))

    print(f"🎬 Montando vídeo: {title}")

    num_slides = 6
    slides = _split_lyrics(lyrics, num_slides)
    slide_dur = duration / len(slides)

    with tempfile.TemporaryDirectory() as tmp:
        slide_imgs = []
        for i, text in enumerate(slides):
            img = _make_slide(text, title, genre, i + 1, len(slides), logo_path)
            path = os.path.join(tmp, f"slide_{i:02d}.png")
            img.save(path)
            slide_imgs.append(path)
            print(f"   Slide {i+1}/{len(slides)}")

        concat_file = os.path.join(tmp, "slides.txt")
        with open(concat_file, "w") as f:
            for p in slide_imgs:
                f.write(f"file '{p}'\n")
                f.write(f"duration {slide_dur:.3f}\n")
            f.write(f"file '{slide_imgs[-1]}'\n")

        slides_mp4 = os.path.join(tmp, "slides.mp4")
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_file,
            "-vf", "fps=24,scale=1920:1080:flags=lanczos,format=yuv420p",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            slides_mp4,
        ], check=True, capture_output=True)

        subprocess.run([
            "ffmpeg", "-y",
            "-i", slides_mp4, "-i", audio_path,
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            output_path,
        ], check=True, capture_output=True)

    print(f"✅ Vídeo pronto: {output_path}")
    return output_path
