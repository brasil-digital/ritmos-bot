import os
import time
import requests

SUNO_BASE = "https://studio-api.suno.ai"
POLL_INTERVAL = 10
MAX_POLLS = 72  # 12 minutos


def _headers():
    return {
        "Cookie": os.environ["SUNO_COOKIE"],
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Origin": "https://suno.com",
        "Referer": "https://suno.com/",
    }


def generate_music(concept, output_path="/tmp/audio.mp3"):
    print(f"🎵 Enviando para Suno: {concept['title']} ({concept['genre']})")

    payload = {
        "prompt": concept["lyrics"],
        "tags": concept["suno_style"],
        "title": concept["title"],
        "make_instrumental": False,
        "wait_audio": False,
    }

    resp = requests.post(
        f"{SUNO_BASE}/api/generate/v2/",
        headers=_headers(),
        json=payload,
        timeout=30,
    )

    if resp.status_code == 401:
        raise Exception("SUNO_COOKIE expirou. Atualize o secret no GitHub com um novo cookie do Suno.")
    if resp.status_code != 200:
        raise Exception(f"Suno API error {resp.status_code}: {resp.text[:300]}")

    clips = resp.json().get("clips", [])
    if not clips:
        raise Exception(f"Suno não retornou clips: {resp.text[:300]}")

    ids = [c["id"] for c in clips]
    print(f"⏳ Aguardando geração... IDs: {ids}")

    for attempt in range(MAX_POLLS):
        time.sleep(POLL_INTERVAL)

        feed = requests.get(
            f"{SUNO_BASE}/api/feed/?ids={','.join(ids)}",
            headers=_headers(),
            timeout=30,
        ).json()

        ready = [c for c in feed if c.get("status") in ("streaming", "complete") and c.get("audio_url")]
        if ready:
            clip = ready[0]
            audio_url = clip["audio_url"]
            duration = clip.get("metadata", {}).get("duration", 180)
            print(f"✅ Música pronta ({duration:.0f}s) — baixando...")

            audio = requests.get(audio_url, timeout=120)
            with open(output_path, "wb") as f:
                f.write(audio.content)

            return {"path": output_path, "duration": duration, "suno_id": clip["id"]}

        if attempt % 6 == 0:
            print(f"   Aguardando Suno... {(attempt * POLL_INTERVAL) // 60}min")

    raise Exception("Timeout: Suno não completou em 12 minutos")
