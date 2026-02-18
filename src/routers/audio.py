from fastapi import APIRouter, File, UploadFile

from src.schemas.envelope import Envelope, envelope
from src.schemas.transcript import Transcript
from src.services.transcription import transcribe_upload

router = APIRouter(tags=["audio"])


@router.post("/audio/transcribe", response_model=Envelope[Transcript])
async def transcribe(file: UploadFile = File(...)) -> Envelope[Transcript]:
    transcript = transcribe_upload(file)
    return envelope(transcript)
