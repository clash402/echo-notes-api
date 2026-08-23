# Echo Notes Architecture

## Responsibility

Echo Notes owns capture, reflection, embedding, storage, and relationship discovery for durable notes. Its current role is an ingestion and memory-foundation service.

It does not yet provide natural-language recall, permissions-aware retrieval, knowledge decay, or organizational memory policy.

## System Context

```text
Browser or API client
  -> FastAPI envelope and request context
      -> transcription service
      -> reflection service
      -> embedding service
      -> note pipeline
      -> SQLite
      -> optional OpenAI or local Whisper providers
```

Every API response uses a `{ data, meta }` envelope. Metadata includes request ID, accumulated model cost, and provider warnings.

## Capture Paths

- `POST /audio/transcribe` converts an uploaded file into a transcript when a provider is available. Text uploads also provide a deterministic development path.
- `POST /echo` generates a reflection without persisting a note.
- `POST /notes` runs the full note pipeline and persists its output.

## Note Pipeline

The LangGraph note pipeline is a fixed sequence:

1. Validate that the transcript is non-empty.
2. Generate a structured reflection.
3. Generate an embedding.
4. Persist the note and provider metadata.
5. Compare the embedding with the latest 50 notes.
6. Persist links to the three highest-similarity notes.

This is a workflow rather than an open-ended agent. The sequence is explicit because each stage has a stable responsibility and failure boundary.

## Provider Strategy

Reflection, embeddings, and transcription are configured independently with `auto`, `local`, or `openai` routing.

- Local reflection and embeddings keep development deterministic.
- Local Whisper is optional and requires its package plus ffmpeg.
- OpenAI provides hosted reflection, embedding, and transcription.
- Missing external configuration falls back where supported and emits warnings in response metadata.

This availability-oriented fallback is appropriate for the current personal-scale product. A stricter environment could change the policy to fail closed when provider parity or data handling requirements demand it.

## Persistence

SQLite stores:

- Transcript text and transcription metadata
- Structured reflection and internal reflection metadata
- Embeddings as JSON arrays
- Directed related-note links and cosine similarity
- Reflection events
- Model cost-ledger records

The current similarity calculation is in process and linear over at most 50 candidate notes. This avoids premature vector infrastructure but does not support large-scale retrieval.

## Failure Behavior

| Failure | Behavior |
| --- | --- |
| Empty transcript | Reject note creation |
| Provider unavailable | Use supported local fallback and emit warnings |
| Audio cannot be processed | Return explicit unprocessed metadata rather than invented text |
| Reflection or embedding failure | Do not persist a partially constructed note |
| Unknown note | Return 404 |
| SQLite failure | Fail the request; no distributed retry exists |

## Evolution Triggers

Introduce additional infrastructure only when a capability requires it:

- Add semantic query and source-backed synthesis before claiming recall.
- Add vector indexing when corpus size or latency makes in-process comparison inadequate.
- Add retention, deletion, correction, and provenance policies before team use.
- Add identity and namespace isolation before multi-user data.
- Add durable object storage before retaining audio.
- Add evaluation sets for reflection and retrieval before optimizing provider quality.
