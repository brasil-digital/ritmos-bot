"""Lista todos os canais YouTube disponíveis nessa conta."""
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

creds = Credentials(
    token=None,
    refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
    client_id=os.environ["YOUTUBE_CLIENT_ID"],
    client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
    token_uri="https://oauth2.googleapis.com/token",
    scopes=["https://www.googleapis.com/auth/youtube"],
)
creds.refresh(Request())
youtube = build("youtube", "v3", credentials=creds)

print("=== Canais disponíveis nessa conta ===\n")
resp = youtube.channels().list(part="snippet,id", mine=True).execute()
for ch in resp.get("items", []):
    print(f"ID   : {ch['id']}")
    print(f"Nome : {ch['snippet']['title']}")
    print(f"URL  : https://www.youtube.com/channel/{ch['id']}")
    print()

# Verifica onde foi o vídeo que acabamos de subir
print("=== Vídeo publicado há pouco ===")
vid = youtube.videos().list(part="snippet", id="CKXGdoYlt4Y").execute()
for v in vid.get("items", []):
    print(f"Título   : {v['snippet']['title']}")
    print(f"Canal ID : {v['snippet']['channelId']}")
    print(f"Canal    : {v['snippet']['channelTitle']}")
