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
CHANNEL_HANDLE = "@ritmos-do-mundo"
CHANNEL_NAME = "Ritmos do Brasil e do Mundo"

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

# Peso de cada região no sorteio. Brasil = 4x a soma das outras 11 => ~80%.
# Analytics set/2026: os Shorts de artistas BR fazem ~1 mil views cada; os
# "do Mundo" (qawwali, Masekela...) ficaram em 17–67. O público é brasileiro.
REGION_WEIGHTS = {"brasil": 44}
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
    ("resistencia", "Um artista que enfrentou censura, ditadura, preconceito ou o poder — e o preço que pagou"),
    ("virada", "Uma decisão surpreendente de um artista (recusou fama, dinheiro ou um contrato; mudou tudo de repente)"),
]

# Peso de cada ângulo. Os campeões de views são histórias de conflito/virada
# com um artista no centro ("a voz que a DITADURA tentou silenciar",
# "REJEITOU ser popstar americana"); gênero/instrumento/recorde rendem menos.
ANGLE_WEIGHTS = {
    "resistencia": 4,
    "virada": 3,
    "historia": 3,
    "lenda": 3,
    "letra": 2,
    "rivalidade": 2,
}
DEFAULT_ANGLE_WEIGHT = 1

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


def _pick_angle():
    weights = [ANGLE_WEIGHTS.get(key, DEFAULT_ANGLE_WEIGHT) for key, _ in ANGLES]
    return random.choices(ANGLES, weights=weights, k=1)[0]


def generate_content():
    region_key, region_desc = _pick_region()
    angle_key, angle_desc = _pick_angle()
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
- Escolha UM assunto específico e concreto. De preferência uma PESSOA (artista) no centro da história, com um conflito, um obstáculo ou uma virada.
- Conteúdo factualmente correto. Nada de invenção — o conflito tem que ser real e verificável.

Título do YouTube — siga EXATAMENTE esta fórmula, que é a que mais funciona no canal:
"[emoji] [Nome do artista]: [frase curta com UMA palavra forte em MAIÚSCULAS] | [Gênero]"
A palavra forte é um verbo ou substantivo de conflito/virada: SALVOU, REJEITOU, DESAFIOU, CENSURADA, DITADURA, ESQUECEU, PROIBIDA, VENCEU, INVENTOR, REVOLUCIONÁRIO...
Exemplos reais do canal que passaram de 1 mil views:
- 🎺 Luiz Gonzaga: A Sanfona que SALVOU o Nordeste | Forró
- 🎤 Clara Nunes: A Voz que a DITADURA Tentou SILENCIAR | Samba
- 🎵 Marisa Monte REJEITOU Ser Popstar Americana | Shorts
- 🎸 Alceu Valença: O Trovador que a Indústria ESQUECEU | Shorts
Sem clickbait falso: a palavra forte tem que ser verdade na história contada.
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
  "youtube_title": "Título seguindo a fórmula acima (máx 80 chars)",
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
