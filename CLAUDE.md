# Ritmos bot — guia para o Claude

Bot do canal YouTube **Ritmos do Brasil e do Mundo** (@ritmos-do-mundo, channel `UC-Y3ELG72lJeIBdcTqmAuOA`; antes "Ritmos do Brasil"): Shorts sobre música, narrados em PT-BR. Dono: Ronny (fala português; responda em português, simples e direto).

## Onde roda
GitHub Actions, branch **`main`**.

| Workflow | Quando | O que faz |
|---|---|---|
| `upload.yml` (Ritmos do Brasil e do Mundo — Postar Short) | 9h e 21h UTC | gera e publica 1 Short |
| `alerta.yml` | quando o de cima falha | avisa o Ronny no Telegram |

**Ao criar um workflow novo, adicione o `name:` dele na lista `workflows:` do `alerta.yml`** (tem que bater exatamente, inclusive o "—").

## Pipeline (`src/main.py`)
`content_generator.py` (Claude Haiku; sorteio REGIÃO × ÂNGULO) → `narration.py` (OpenAI TTS, voz feminina sorteada `nova`/`shimmer`) → `video_creator.py` (1080×1920, 5 slides, cartão de título de 1,3 s que vira a miniatura, marca d'água do logo da Rádio IA Fala Brasil a 18%) → `youtube_uploader.py`.

## Decisões do Ronny (não mudar sem pedido)
- **Brasil ~80% do sorteio** (`REGION_WEIGHTS`, brasil = 44). Os Shorts de artistas brasileiros com conflito/virada no título têm ~1 mil views; os "do Mundo", dezenas.
- Ângulos `resistencia` e `virada` com peso maior (`ANGLE_WEIGHTS`); fórmula de título: `[emoji] Artista: frase com PALAVRA forte | Gênero`.
- Narração sempre em PT-BR. `CHANNEL_HANDLE`/`CHANNEL_NAME` no topo do `content_generator.py`; `BRAND_NAME` no `video_creator.py`.
- Anti-repetição: o prompt recebe os últimos 15 títulos do canal (RSS público, sem chave).

## Testar sem publicar
- Visual: `python test_preview.py` (gera `preview_slide.png` / `preview_titlecard.png`, gitignored; usa fontes do Windows).
- Não há modo "sem upload" no `main.py` — não rode o pipeline completo só para testar.

## Armadilhas conhecidas
- O token do YouTube tem que ser do canal Ritmos (já aconteceu de gerar para o Brasil Digital por engano): depois de trocar o token, conferir com `python check_channels.py`.
- Shorts não aceitam thumbnail por API → por isso o 1º quadro é a capa.
- O runner do GitHub às vezes tem cache apt velho → o workflow faz `apt-get update` antes de instalar.

## Segredos (GitHub → Settings → Secrets)
`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`. **Nunca** escrever valores de chaves em arquivos do repositório (ele é público). O Ronny grava segredos ele mesmo.
