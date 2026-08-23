# Echo Notes

Echo Notes is the knowledge and memory layer of Ghost Platform. The current API captures a transcript, reflects on it, creates an embedding, stores the result, and links the note to semantically similar recent notes.

The product direction is durable decision recall: preserving why something was decided, not merely what was written. The current implementation establishes the ingestion and relationship foundation; it does not yet provide natural-language recall over the knowledge store.

## Current Capabilities

- Accept text transcripts and uploaded audio
- Transcribe with local Whisper or OpenAI, with explicit fallback metadata
- Generate structured reflections with local deterministic logic or OpenAI
- Generate local deterministic or OpenAI embeddings
- Persist transcripts, provider metadata, reflections, embeddings, and cost records in SQLite
- Link each new note to the three most similar notes among the latest 50
- List notes and retrieve note details
- Return a consistent `{ data, meta }` envelope with request ID, cost, and warnings

## Boundaries

Echo Notes is not currently a general knowledge assistant or production vector-search service.

- There is no semantic query or synthesized recall endpoint.
- Embeddings are stored as JSON in SQLite and compared in process.
- Recency weighting, decay, pruning, deletion, namespaces, access control, and retention policies are not implemented.
- Audio may be transcribed, but the service does not manage durable audio-object storage.
- Provider fallback favors local availability over strict production parity.

These are explicit current limits, not hidden guarantees. See [docs/architecture.md](docs/architecture.md) for the implemented pipeline and evolution triggers.

The next product boundary is trustworthy recall: add correction and deletion before treating stored memory as durable, then evaluate semantic or hybrid retrieval against a keyword-search baseline. This keeps lifecycle governance and measurable retrieval quality ahead of secondary features such as automatic tagging.

## Note Pipeline

```text
Transcript
  -> validation
  -> structured reflection
  -> embedding
  -> SQLite persistence
  -> similarity links
```

Provider-backed steps are probabilistic. Validation, envelope construction, persistence, link selection, and API contracts remain deterministic.

## Quick Start

Requires Python 3.11 or later.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
cp .env.local.example .env.local
./start.sh
```

The API runs at `http://localhost:8000`, with interactive OpenAPI documentation at `/docs`. Local providers allow the core flow to run without external credentials.

Provider selection and optional Whisper setup are documented in [docs/provider-setup.md](docs/provider-setup.md).

## API Surface

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Service health |
| `POST /audio/transcribe` | Transcribe an uploaded file or return explicit fallback metadata |
| `POST /echo` | Generate a structured reflection for a transcript |
| `POST /notes` | Run the note pipeline and persist the result |
| `GET /notes` | List recent notes |
| `GET /notes/{note_id}` | Retrieve a note and its related-note links |

## Quality Checks

```bash
black --check .
ruff check .
pytest
```

Tests cover health, provider fallback, deterministic embeddings and reflection, and the note persistence flow.

## Deployment

The API is containerized and configured for Fly.io. The current Fly configuration does not mount persistent storage, so the deployed SQLite database is ephemeral across machine replacement. The current `main` branch also does not configure cross-origin browser access; a separately hosted web client requires a same-origin proxy or the pending CORS integration.

The web client lives in [echo-notes-web](https://github.com/clash402/echo-notes-web).
