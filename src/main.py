import os
import sys
import traceback

from concept_generator import generate_concept
from music_generator import generate_music
from video_creator import create_video
from youtube_uploader import upload_video

LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")


def main():
    print("🇧🇷 Ritmos do Brasil Bot — Iniciando...\n")

    try:
        print("📝 Gerando conceito da música...")
        concept = generate_concept()
        print(f"✅ {concept['genre'].upper()} — \"{concept['title']}\"")
        print(f"   Tema: {concept['story']}\n")

        print("🎵 Gerando música no Suno...")
        audio_info = generate_music(concept, output_path="/tmp/ritmos_audio.mp3")
        print(f"✅ Áudio pronto ({audio_info['duration']:.0f}s)\n")

        print("🎬 Criando lyric video...")
        logo = LOGO_PATH if os.path.exists(LOGO_PATH) else None
        video_path = create_video(concept, audio_info, "/tmp/ritmos_video.mp4", logo_path=logo)

        print("\n📤 Publicando no YouTube...")
        result = upload_video(video_path, concept)

        print(f"\n🎉 Publicado com sucesso!")
        print(f"   Título : {concept['youtube_title']}")
        print(f"   URL    : {result['url']}")

    except Exception as e:
        print(f"\n❌ Erro: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
