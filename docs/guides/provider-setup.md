# Provider Setup

This guide configures reflection, embeddings, and transcription providers for
local dev and Fly.io deploys.

## Local environment

1. Copy example env:

```bash
cp .env.example .env
```

2. Choose routing strategy:

- `auto`: prefers external provider when available, otherwise local fallback.
- `openai`: requires OpenAI credentials; falls back with warnings if unavailable.
- `local`: local-only behavior where supported.

3. Set required values in `.env`:

```bash
ECHO_NOTES_LLM_PROVIDER=auto
ECHO_NOTES_EMBEDDING_PROVIDER=auto
ECHO_NOTES_TRANSCRIPTION_PROVIDER=auto
OPENAI_API_KEY=your-key
OPENAI_BASE_URL=
```

## Local Whisper setup (optional)

Use this if you want local audio transcription without external APIs.

```bash
pip install openai-whisper
```

Install `ffmpeg` on your machine so Whisper can decode audio input.

Then set:

```bash
ECHO_NOTES_TRANSCRIPTION_PROVIDER=local
ECHO_NOTES_WHISPER_LOCAL_MODEL=base
```

## Fly.io secrets

Set secrets on the deployed Fly app:

```bash
fly secrets set \
  OPENAI_API_KEY="your-key" \
  OPENAI_BASE_URL="" \
  ECHO_NOTES_LLM_PROVIDER="auto" \
  ECHO_NOTES_EMBEDDING_PROVIDER="auto" \
  ECHO_NOTES_TRANSCRIPTION_PROVIDER="auto" \
  ECHO_NOTES_LLM_DEFAULT_MODEL="gpt-4o-mini" \
  ECHO_NOTES_LLM_CHEAP_MODEL="gpt-4o-mini" \
  ECHO_NOTES_EMBEDDING_MODEL="text-embedding-3-small" \
  ECHO_NOTES_WHISPER_OPENAI_MODEL="whisper-1" \
  ECHO_NOTES_LLM_PROMPT_COST_PER_1K="0.00015" \
  ECHO_NOTES_LLM_COMPLETION_COST_PER_1K="0.0006" \
  ECHO_NOTES_EMBEDDING_COST_PER_1K="0.00002" \
  -a echo-notes-api
```

## Verify configuration

1. Start API and call `GET /health`.
2. Call `POST /echo` with a transcript and confirm `meta.cost` is populated.
3. Call `POST /audio/transcribe` with audio and confirm metadata `source`:
- `whisper_openai_api` for API transcription
- `whisper_local` for local Whisper
- `audio_unprocessed` when no provider is available
