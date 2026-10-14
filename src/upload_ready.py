"""Publica um vídeo JÁ MONTADO (ex.: vídeo longo aprovado pelo Ronny).

Uso: python src/upload_ready.py <pasta>   — a pasta tem video.mp4, capa.jpg e meta.json
meta.json: {"youtube_title": ..., "youtube_description": ..., "tags": [...]}
"""
import json
import os
import sys

from youtube_uploader import set_thumbnail, upload_video


def main():
    folder = sys.argv[1]
    with open(os.path.join(folder, "meta.json"), encoding="utf-8") as f:
        meta = json.load(f)
    result = upload_video(os.path.join(folder, "video.mp4"), meta)
    cover = os.path.join(folder, "capa.jpg")
    if os.path.exists(cover):
        set_thumbnail(result["id"], cover)
    print(f"🎉 Publicado: {result['url']}")


if __name__ == "__main__":
    main()
