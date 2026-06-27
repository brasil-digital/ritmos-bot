import os
import sys
import traceback

from content_generator import generate_content
from narration import generate_narration
from video_creator import create_video
from youtube_uploader import upload_video

LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")


def main():
    print("🇧🇷 Ritmos do Brasil Bot — Iniciando...\n")

    try:
        print("📝 Gerando conteúdo sobre música brasileira...")
        content = generate_content()
        print(f"✅ Tema: {content['type']} — {content['subject']}")
        print(f"   Título: {content['youtube_title']}\n")

        print("🎙️  Gerando narração feminina...")
        audio_path = generate_narration(content["narration_script"], "/tmp/ritmos_narration.mp3")

        print("\n🎬 Criando YouTube Short com narração...")
        logo = LOGO_PATH if os.path.exists(LOGO_PATH) else None
        video_path = create_video(content, "/tmp/ritmos_video.mp4", logo_path=logo, audio_path=audio_path)

        print("\n📤 Publicando no YouTube...")
        result = upload_video(video_path, content)

        print(f"\n🎉 Short publicado com narração!")
        print(f"   Título: {content['youtube_title']}")
        print(f"   URL   : {result['url']}")

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
