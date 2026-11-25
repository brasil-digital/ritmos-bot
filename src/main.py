import os
import sys
import traceback

from content_generator import generate_content
from narration import generate_narration
from video_creator import create_video
from youtube_uploader import upload_video

LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")
RADIO_LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "radio_logo.png")


def main():
    print("🎵 Ritmos do Brasil e do Mundo — Bot iniciando...\n")

    try:
        print("📝 Gerando conteúdo sobre ritmos e música do mundo...")
        content = generate_content()
        print(f"✅ Tema: {content['type']} — {content['subject']}")
        print(f"   Título: {content['youtube_title']}\n")

        print("🎙️  Gerando narração feminina...")
        audio_path = generate_narration(content["narration_script"], "/tmp/ritmos_narration.mp3")

        print("\n🎬 Criando YouTube Short com narração...")
        logo = LOGO_PATH if os.path.exists(LOGO_PATH) else None
        radio_logo = RADIO_LOGO_PATH if os.path.exists(RADIO_LOGO_PATH) else None
        video_path = create_video(content, "/tmp/ritmos_video.mp4", logo_path=logo, audio_path=audio_path, radio_logo_path=radio_logo)

        if os.environ.get("SKIP_UPLOAD") == "1":
            # Modo teste: não publica; guarda vídeo + roteiro para aprovação.
            import json, shutil
            os.makedirs("teste", exist_ok=True)
            shutil.copy(video_path, "teste/short_teste.mp4")
            with open("teste/conteudo.json", "w", encoding="utf-8") as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
            print("\n🧪 SKIP_UPLOAD=1 — NÃO publicado. Saída em teste/")
            return

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
