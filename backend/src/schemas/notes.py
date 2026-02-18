from pydantic import BaseModel, Field

from backend.src.schemas.reflection import Reflection
from backend.src.schemas.transcript import Transcript, TranscriptMetadata


class RelatedNoteLink(BaseModel):
    note_id: int
    related_note_id: int
    similarity: float


class Note(BaseModel):
    id: int
    audio_reference: str | None = None
    transcript: Transcript
    reflection: Reflection
    related_notes: list[RelatedNoteLink] = Field(default_factory=list)
    created_at: str
    updated_at: str


class CreateNoteRequest(BaseModel):
    transcript: str
    audio_reference: str | None = None
    transcript_metadata: TranscriptMetadata | None = None


class ListNotesResponse(BaseModel):
    notes: list[Note]
