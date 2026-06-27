import anthropic
import json
import os
import random

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

GENRES = [
    "samba", "forró", "pagode", "axé", "baião", "bossa nova",
    "sertanejo", "frevo", "maracatu", "xote", "mpb", "choro",
    "ciranda", "carimbó", "funk carioca", "samba de roda",
    "xaxado", "coco de roda", "ijexá", "lambada",
]


def generate_concept():
    genre = random.choice(GENRES)

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": f"""Você é um compositor brasileiro especializado em {genre}.
Crie um conceito completo para uma música nova no gênero {genre}.

Responda APENAS com um JSON válido, sem markdown, com esta estrutura exata:
{{
  "genre": "{genre}",
  "title": "título da música em português (máximo 6 palavras)",
  "mood": "clima emocional (ex: alegre, melancólico, apaixonado)",
  "story": "tema/história resumido em 1 frase",
  "lyrics": "letra completa em português (3-4 estrofes + refrão). Use [Verso 1], [Refrão], [Verso 2], [Ponte] como marcadores de seção. Cada seção com 4-6 linhas.",
  "suno_style": "tags de estilo para Suno AI separadas por vírgula (gênero, instrumentos, clima, tipo de voz)",
  "youtube_title": "título YouTube incluindo gênero e 'Ritmos do Brasil' (máx 80 chars)",
  "youtube_description": "descrição YouTube completa (3 parágrafos) terminando com hashtags relevantes",
  "tags": ["tag1", "tag2", "tag3", "..."]
}}"""
        }]
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())
