import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Vozes femininas do OpenAI TTS
VOICES = ["nova", "shimmer"]


def generate_narration(script: str, output_path: str = "/tmp/narration.mp3") -> str:
    import random
    voice = random.choice(VOICES)
    print(f"🎙️  Gerando narração com voz '{voice}'...")

    response = client.audio.speech.create(
        model="tts-1-hd",
        voice=voice,
        input=script,
        response_format="mp3",
        speed=0.95,  # levemente mais lento — mais natural e claro
    )

    response.stream_to_file(output_path)
    print(f"✅ Áudio gerado: {output_path}")
    return output_path
