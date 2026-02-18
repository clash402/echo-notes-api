import json
from dataclasses import asdict
from datetime import UTC, datetime
from typing import TypedDict

from langgraph.graph import END, StateGraph

from backend.src.db.engine import get_connection
from backend.src.schemas.notes import CreateNoteRequest, Note, RelatedNoteLink
from backend.src.schemas.reflection import Reflection
from backend.src.schemas.transcript import Transcript, TranscriptMetadata
from backend.src.services.embeddings import cosine_similarity, generate_embedding
from backend.src.services.reflection import reflect_transcript


class NotePipelineState(TypedDict, total=False):
    transcript: str
    audio_reference: str | None
    transcript_metadata: TranscriptMetadata
    reflection: Reflection
    reflection_internal_metadata: dict
    embedding: list[float]
    note_id: int


def create_note(payload: CreateNoteRequest) -> Note:
    state: NotePipelineState = {
        "transcript": payload.transcript.strip(),
        "audio_reference": payload.audio_reference,
        "transcript_metadata": payload.transcript_metadata
        or TranscriptMetadata(
            model="external-transcript",
            language=None,
            duration_seconds=None,
            source="manual",
        ),
    }
    graph = _build_note_graph()
    result = graph.invoke(state)
    return get_note(result["note_id"])


def list_notes(limit: int = 50) -> list[Note]:
    connection = get_connection()
    try:
        rows = connection.execute(
            """
            SELECT id
            FROM notes
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        connection.close()
    return [get_note(int(row["id"])) for row in rows]


def get_note(note_id: int) -> Note:
    connection = get_connection()
    try:
        row = connection.execute(
            """
            SELECT id, audio_reference, transcript_text, transcript_metadata_json, reflection_json,
                   created_at, updated_at
            FROM notes
            WHERE id = ?
            """,
            (note_id,),
        ).fetchone()
        if row is None:
            raise KeyError(f"Note {note_id} not found")

        links = connection.execute(
            """
            SELECT note_id, related_note_id, similarity
            FROM related_note_links
            WHERE note_id = ?
            ORDER BY similarity DESC
            """,
            (note_id,),
        ).fetchall()
    finally:
        connection.close()

    transcript_metadata = TranscriptMetadata.model_validate(
        json.loads(row["transcript_metadata_json"])
    )
    transcript = Transcript(text=row["transcript_text"], metadata=transcript_metadata)
    reflection = Reflection.model_validate(json.loads(row["reflection_json"]))
    related_notes = [
        RelatedNoteLink(
            note_id=int(link["note_id"]),
            related_note_id=int(link["related_note_id"]),
            similarity=float(link["similarity"]),
        )
        for link in links
    ]
    return Note(
        id=int(row["id"]),
        audio_reference=row["audio_reference"],
        transcript=transcript,
        reflection=reflection,
        related_notes=related_notes,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _build_note_graph():
    graph_builder = StateGraph(NotePipelineState)
    graph_builder.add_node("validate_transcript", _validate_transcript)
    graph_builder.add_node("reflect", _reflect)
    graph_builder.add_node("embed", _embed)
    graph_builder.add_node("persist", _persist)
    graph_builder.set_entry_point("validate_transcript")
    graph_builder.add_edge("validate_transcript", "reflect")
    graph_builder.add_edge("reflect", "embed")
    graph_builder.add_edge("embed", "persist")
    graph_builder.add_edge("persist", END)
    return graph_builder.compile()


def _validate_transcript(state: NotePipelineState) -> NotePipelineState:
    transcript = (state.get("transcript") or "").strip()
    if not transcript:
        raise ValueError("Transcript is required.")
    state["transcript"] = transcript
    return state


def _reflect(state: NotePipelineState) -> NotePipelineState:
    reflection_result = reflect_transcript(state["transcript"])
    state["reflection"] = reflection_result.reflection
    state["reflection_internal_metadata"] = asdict(reflection_result.internal_metadata)
    return state


def _embed(state: NotePipelineState) -> NotePipelineState:
    state["embedding"] = generate_embedding(state["transcript"])
    return state


def _persist(state: NotePipelineState) -> NotePipelineState:
    connection = get_connection()
    now = datetime.now(tz=UTC).isoformat()
    try:
        existing_rows = connection.execute(
            """
            SELECT id, embedding_json
            FROM notes
            ORDER BY created_at DESC, id DESC
            LIMIT 50
            """
        ).fetchall()

        cursor = connection.execute(
            """
            INSERT INTO notes (
              audio_reference,
              transcript_text,
              transcript_metadata_json,
              reflection_json,
              reflection_internal_json,
              embedding_json,
              created_at,
              updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                state.get("audio_reference"),
                state["transcript"],
                json.dumps(state["transcript_metadata"].model_dump()),
                json.dumps(state["reflection"].model_dump()),
                json.dumps(state["reflection_internal_metadata"]),
                json.dumps(state["embedding"]),
                now,
                now,
            ),
        )
        note_id = int(cursor.lastrowid)

        related_links: list[tuple[int, float]] = []
        for row in existing_rows:
            existing_embedding = json.loads(row["embedding_json"])
            similarity = cosine_similarity(state["embedding"], existing_embedding)
            related_links.append((int(row["id"]), similarity))

        related_links.sort(key=lambda item: item[1], reverse=True)
        for related_note_id, similarity in related_links[:3]:
            connection.execute(
                """
                INSERT OR REPLACE INTO related_note_links (note_id, related_note_id, similarity)
                VALUES (?, ?, ?)
                """,
                (note_id, related_note_id, similarity),
            )

        connection.commit()
    finally:
        connection.close()

    state["note_id"] = note_id
    return state
