import anthropic
import json
import os
import random

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

CONTENT_TYPES = [
    ("curiosidade", "Uma curiosidade incrível e pouco conhecida"),
    ("historia", "A história emocionante por trás de uma música ou momento icônico"),
    ("artista_lenda", "Homenagem a um grande nome da música brasileira do passado"),
    ("artista_atual", "Destaque de um artista brasileiro atual que está bombando"),
    ("genero", "Tudo sobre um gênero musical brasileiro — origem, características, ícones"),
    ("rivalidade", "Uma rivalidade ou parceria histórica entre artistas brasileiros"),
    ("letra", "O significado profundo por trás de uma letra de música famosa"),
    ("record", "Um recorde ou feito histórico da música brasileira"),
    ("tendencia", "Uma tendência atual que está mudando a música brasileira"),
    ("comparacao", "Comparação entre dois estilos ou épocas da música brasileira"),
    ("compositores", "Os maiores compositores brasileiros de todos os tempos"),
    ("instrumentos", "Instrumentos típicos da música brasileira e suas histórias"),
    ("carnaval", "Histórias e curiosidades do carnaval e suas músicas"),
    ("sertanejo", "O universo do sertanejo — raízes, evolução e grandes nomes"),
    ("funk", "A história e impacto cultural do funk brasileiro"),
    ("mpb", "Os pilares da MPB e artistas que definiram o gênero"),
    ("bossa_nova", "A Bossa Nova — o gênero que colocou o Brasil no mapa mundial"),
    ("samba", "O samba — alma da música brasileira"),
    ("forro", "O forró — da origem nordestina ao sucesso nacional"),
    ("axe", "O axé baiano — energia, dança e cultura"),
]

HOOKS = [
    "Você sabia que...",
    "A história que poucos conhecem:",
    "Isso vai te surpreender:",
    "O Brasil que poucos conhecem:",
    "Fato incrível:",
    "Você não vai acreditar:",
    "A verdade por trás de:",
    "Descubra agora:",
    "O segredo que ninguém conta:",
    "Incrível mas verdadeiro:",
]


def generate_content():
    content_type, content_desc = random.choice(CONTENT_TYPES)
    hook = random.choice(HOOKS)

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": f"""Você é um especialista apaixonado em música brasileira criando conteúdo viral para YouTube Shorts.

Tipo de conteúdo: {content_desc}
Hook inicial: "{hook}"

Crie um roteiro para um Short do YouTube sobre música brasileira. O vídeo terá 5 slides de texto de ~9 segundos cada (total ~45 segundos).

Responda APENAS com JSON válido, sem markdown:
{{
  "type": "{content_type}",
  "hook": "{hook}",
  "subject": "assunto específico escolhido (ex: 'Roberto Carlos', 'Bossa Nova', 'Garota de Ipanema')",
  "slides": [
    {{
      "text": "Texto do slide 1 — o HOOK que prende a atenção (máx 80 chars)",
      "duration": 9
    }},
    {{
      "text": "Texto do slide 2 — primeira revelação/fato (máx 100 chars)",
      "duration": 9
    }},
    {{
      "text": "Texto do slide 3 — aprofundamento/contexto (máx 100 chars)",
      "duration": 9
    }},
    {{
      "text": "Texto do slide 4 — clímax ou curiosidade surpreendente (máx 100 chars)",
      "duration": 9
    }},
    {{
      "text": "🎵 Ritmos do Brasil\\nInscreva-se para mais conteúdo!",
      "duration": 9
    }}
  ],
  "youtube_title": "Título YouTube otimizado para Shorts (máx 80 chars, inclui emoji)",
  "youtube_description": "Descrição completa para YouTube (2 parágrafos + hashtags). Mencionar @ritmos-do-brasil",
  "tags": ["musica brasileira", "shorts", "...mais 8 tags relevantes..."]
}}"""
        }]
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())
