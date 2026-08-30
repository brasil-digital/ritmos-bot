"""Script local para preview do slide com watermark."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Substitui fontes Linux por fontes Windows
import video_creator
video_creator.FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"
video_creator.FONT_REG  = "C:/Windows/Fonts/arial.ttf"

from video_creator import _make_slide

RADIO_LOGO = os.path.join(os.path.dirname(__file__), "assets", "radio_logo.png")
LOGO       = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
OUT        = os.path.join(os.path.dirname(__file__), "preview_slide.png")

slide = _make_slide(
    slide_text="O afrobeat de Fela Kuti virou arma política contra a ditadura na Nigéria. 🎶",
    slide_num=2,
    total_slides=5,
    content_type="historia",
    subject="Fela Kuti",
    logo_path=LOGO,
    radio_logo_path=RADIO_LOGO,
)
slide.save(OUT)
print(f"Preview salvo em: {OUT}")
