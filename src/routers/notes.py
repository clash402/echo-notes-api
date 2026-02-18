from fastapi import APIRouter, HTTPException, Query

from src.schemas.envelope import Envelope, envelope
from src.schemas.notes import CreateNoteRequest, ListNotesResponse, Note
from src.services.notes import create_note, get_note, list_notes

router = APIRouter(tags=["notes"])


@router.post("/notes", response_model=Envelope[Note])
async def create_note_endpoint(payload: CreateNoteRequest) -> Envelope[Note]:
    try:
        note = create_note(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return envelope(note)


@router.get("/notes", response_model=Envelope[ListNotesResponse])
async def list_notes_endpoint(
    limit: int = Query(default=50, ge=1, le=200)
) -> Envelope[ListNotesResponse]:
    notes = list_notes(limit=limit)
    return envelope(ListNotesResponse(notes=notes))


@router.get("/notes/{note_id}", response_model=Envelope[Note])
async def get_note_endpoint(note_id: int) -> Envelope[Note]:
    try:
        note = get_note(note_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return envelope(note)
