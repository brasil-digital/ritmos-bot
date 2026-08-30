import anthropic
import json
import os
import random
import re
import urllib.request

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

CHANNEL_ID = "UC-Y3ELG72lJeIBdcTqmAuOA"
FEED_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"

# @handle do canal (atualize aqui se reservar outro no YouTube)
CHANNEL_HANDLE = "@ritmosdomundo"
CHANNEL_NAME = "Ritmos do Mundo"

# ---------------------------------------------------------------------------
# Regiões / cenas musicais. O Brasil tem peso maior (~1/3 das publicações);
# as demais regiões dividem o resto.
# ---------------------------------------------------------------------------
REGIONS = [
    ("brasil", "os ritmos do Brasil (samba, forró, bossa nova, MPB, frevo, maracatu, sertanejo, funk carioca, axé, choro...)"),
    ("africa_ocidental", "a música da África Ocidental e Central (afrobeat, highlife, juju, soukous, mbalax, Fela Kuti, griots...)"),
    ("africa_austral", "a música da África Austral e Oriental (amapiano, kwaito, mbaqanga, taarab, mbira...)"),
    ("caribe", "os ritmos do Caribe (reggae, dancehall, ska, rocksteady, soca, calypso, zouk, dub...)"),
    ("america_latina", "a música latino-americana hispânica (salsa, cumbia, reggaeton, tango, bolero, mariachi, son cubano, bachata...)"),
    ("estados_unidos", "a música dos Estados Unidos (jazz, blues, soul, hip hop, gospel, country, rock and roll, R&B...)"),
    ("europa_ocidental", "a música da Europa Ocidental (flamenco, fado, chanson francesa, folk celta, música tradicional italiana...)"),
    ("europa_oriental", "a música da Europa Oriental e dos Bálcãs (música cigana/romani, brass band balcânico, polca, música klezmer...)"),
    ("oriente_medio", "a música do Oriente Médio e Norte da África (raï, dabke, música árabe clássica, maqam, música persa...)"),
    ("sul_asia", "a música do Sul da Ásia (bhangra, filmi/Bollywood, ragas indianas, qawwali, tabla...)"),
    ("leste_asia", "a música do Leste Asiático (K-pop, J-pop, city pop, ópera de Pequim, enka, gamelão...)"),
    ("eletronica", "a música eletrônica no mundo (house de Chicago, techno de Detroit, a cena de Berlim, drum and bass, dub techno...)"),
]

# Peso de cada região no sorteio (Brasil ~1/3)
REGION_WEIGHTS = {"brasil": 6}
DEFAULT_REGION_WEIGHT = 1

# ---------------------------------------------------------------------------
# Ângulos de conteúdo (atemporais). O modo "notícias" com RSS entra numa
# segunda fase.
# ---------------------------------------------------------------------------
ANGLES = [
    ("curiosidade", "Uma curiosidade incrível e pouco conhecida"),
    ("historia", "A história emocionante por trás de uma música, artista ou movimento"),
    ("genero", "Tudo sobre um gênero musical — origem, características e ícones"),
    ("lenda", "Homenagem a um grande nome do passado, já falecido ou histórico"),
    ("em_alta", "Um artista ou cena que está explodindo agora"),
    ("instrumento", "Um instrumento típico e a história por trás dele"),
    ("rivalidade", "Uma rivalidade ou parceria histórica entre artistas"),
    ("letra", "O significado profundo por trás de uma letra de música famosa"),
    ("recorde", "Um recorde ou feito histórico da música"),
    ("influencia", "Como um ritmo influenciou (ou foi influenciado por) a música de outro continente"),
]

HOOKS = [
    "Você sabia que...",
    "A história que poucos conhecem:",
    "Isso vai te surpreender:",
    "O mundo que a música esconde:",
    "Fato incrível:",
    "Você não vai acreditar:",
    "A verdade por trás de:",
    "Descubra agora:",
    "O segredo que ninguém conta:",
    "Incrível mas verdadeiro:",
]


def _recent_video_titles(limit=15):
    """Busca os títulos dos últimos vídeos do canal via RSS (sem API key)."""
    try:
        with urllib.request.urlopen(FEED_URL, timeout=10) as resp:
            xml = resp.read().decode("utf-8")
        titles = re.findall(r"<media:title>(.*?)</media:title>", xml)
        return titles[:limit]
    except Exception as e:
        print(f"⚠️  Não consegui ler o feed do canal (seguindo sem histórico): {e}")
        return []


def _pick_region():
    weights = [REGION_WEIGHTS.get(key, DEFAULT_REGION_WEIGHT) for key, _ in REGIONS]
    return random.choices(REGIONS, weights=weights, k=1)[0]


def generate_content():
    region_key, region_desc = _pick_region()
    angle_key, angle_desc = random.choice(ANGLES)
    hook = random.choice(HOOKS)

    recent = _recent_video_titles()
    avoid_block = ""
    if recent:
        lista = "\n".join(f"- {t}" for t in recent)
        avoid_block = f"""
IMPORTANTE — o canal JÁ publicou vídeos sobre os assuntos abaixo. É PROIBIDO repetir esses assuntos, músicas, artistas ou ângulos (nem variações do mesmo tema):
{lista}

Escolha um assunto específico DIFERENTE de todos os listados acima.
"""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": f"""Você é um jornalista musical apaixonado por ritmos do mundo inteiro, criando conteúdo viral para YouTube Shorts do canal "{CHANNEL_NAME}".

Região/cena musical deste vídeo: {region_desc}
Ângulo do conteúdo: {angle_desc}
Hook inicial: "{hook}"
{avoid_block}

Crie um roteiro para um Short do YouTube sobre música/ritmos, dentro da região e do ângulo indicados acima. O vídeo terá 5 slides de texto de ~9 segundos cada (total ~45 segundos).

Regras:
- Escolha UM assunto específico e concreto (um artista, uma música, um gênero, um instrumento, um episódio).
- Conteúdo factualmente correto. Nada de invenção.
- Público brasileiro: a narração é SEMPRE em português do Brasil, mesmo quando o assunto é de outro país. Explique referências estrangeiras para quem nunca ouviu falar.

Responda APENAS com JSON válido, sem markdown:
{{
  "type": "{angle_key}",
  "region": "{region_key}",
  "hook": "{hook}",
  "subject": "assunto específico escolhido (ex: 'Fela Kuti', 'Amapiano', 'Cumbia', 'Bob Marley', 'Bossa Nova')",
  "slides": [
    {{ "text": "Texto do slide 1 — o HOOK que prende a atenção (máx 80 chars)" }},
    {{ "text": "Texto do slide 2 — primeira revelação/fato (máx 100 chars)" }},
    {{ "text": "Texto do slide 3 — aprofundamento/contexto (máx 100 chars)" }},
    {{ "text": "Texto do slide 4 — clímax ou curiosidade surpreendente (máx 100 chars)" }},
    {{ "text": "🎵 {CHANNEL_NAME}\\nInscreva-se para mais!" }}
  ],
  "narration_script": "Script COMPLETO para narração em voz feminina, em português brasileiro natural e empolgante. Deve cobrir todos os slides do vídeo. Entre 80 e 110 palavras (≈45 segundos falados). Tom animado, apaixonado por música. NÃO inclua indicações de cena ou colchetes — apenas o texto que será narrado.",
  "youtube_title": "Título YouTube otimizado para Shorts (máx 80 chars, inclui emoji)",
  "youtube_description": "Descrição completa para YouTube (2 parágrafos + hashtags). Mencionar {CHANNEL_HANDLE}",
  "tags": ["musica do mundo", "ritmos", "shorts", "...mais 7 tags relevantes ao assunto..."]
}}"""
        }]
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())
