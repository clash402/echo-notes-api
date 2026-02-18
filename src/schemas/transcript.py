from pydantic import BaseModel


class TranscriptMetadata(BaseModel):
    model: str
    language: str | None = None
    duration_seconds: float | None = None
    source: str


class Transcript(BaseModel):
    text: str
    metadata: TranscriptMetadata
