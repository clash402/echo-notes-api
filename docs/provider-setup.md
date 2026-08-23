# Echo Notes Provider Setup

Reflection, embeddings, and transcription can be routed independently. Copy the example configuration before changing providers:

```bash
cp .env.local.example .env.local
```

## Routing Modes

- `auto` prefers an available external provider and otherwise uses a supported local fallback.
- `local` uses deterministic reflection and embeddings plus optional local Whisper.
- `openai` uses the configured OpenAI-compatible endpoint and falls back with response warnings when the current service supports a local path.

Core settings:

```dotenv
ECHO_NOTES_LLM_PROVIDER=auto
ECHO_NOTES_EMBEDDING_PROVIDER=auto
ECHO_NOTES_TRANSCRIPTION_PROVIDER=auto
OPENAI_API_KEY=
OPENAI_BASE_URL=
```

Model names and cost rates live in `.env.local.example`. Rates are configuration inputs used for estimates; update them when provider pricing changes.

## Local Whisper

Install Whisper and ffmpeg:

```bash
pip install openai-whisper
brew install ffmpeg
```

Then configure:

```dotenv
ECHO_NOTES_TRANSCRIPTION_PROVIDER=local
ECHO_NOTES_WHISPER_LOCAL_MODEL=base
```

Local Whisper is optional. Without a usable transcription provider, audio requests return explicit unprocessed metadata and warnings rather than fabricated text.

## Fly.io

Configure provider credentials and routing as Fly secrets:

```bash
fly secrets set \
  OPENAI_API_KEY="your-key" \
  ECHO_NOTES_LLM_PROVIDER="auto" \
  ECHO_NOTES_EMBEDDING_PROVIDER="auto" \
  ECHO_NOTES_TRANSCRIPTION_PROVIDER="auto" \
  -a echo-notes-api
```

Non-secret model and cost configuration may also be set as secrets or deployment environment variables.

## Verification

1. Start the API and call `GET /health`.
2. Call `POST /echo` and inspect `meta.cost` and `meta.warnings`.
3. Create a note and confirm its reflection, embedding, and related links persist.
4. Call `POST /audio/transcribe` and verify the returned metadata identifies the actual provider or explicit fallback.
