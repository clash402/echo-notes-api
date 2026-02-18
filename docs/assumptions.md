# Echo Notes API Assumptions

## 2026-02-18

- This first increment establishes API contracts and middleware first, then adds
  transcription/reflection/note workflows in later steps.
- All responses are returned in the required envelope format from day one.
- `cost_ledger` records are only written when token usage is greater than zero,
  which will be populated once LLM providers are integrated.
- SQLite is initialized at startup and schema is managed with direct SQL for v1
  simplicity.
- Reflection and embedding generation use local deterministic providers in v1 to
  keep development/test behavior stable without external credentials.
- `/audio/transcribe` supports text uploads as a deterministic passthrough path;
  if `whisper` is not installed for audio formats, the API returns an empty
  transcript with explicit warning metadata.
- Internal reflection metadata is persisted on both `/echo` calls
  (`reflection_events`) and `/notes` persistence (`notes.reflection_internal_json`).
- Provider routing is environment-driven (`auto|local|openai`) for reflection,
  embeddings, and transcription. If OpenAI credentials/package are missing, the
  system falls back to local providers and emits warnings in API metadata.
