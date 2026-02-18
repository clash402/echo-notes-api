from fastapi import APIRouter, File, UploadFile

from src.core.request_context import add_warning
from src.schemas.envelope import Envelope, envelope
from src.schemas.transcript import Transcript
from src.services.transcription import transcribe_upload

router = APIRouter(tags=["audio"])

try:
    import python_multipart  # type: ignore # noqa: F401

    _MULTIPART_AVAILABLE = True
except ModuleNotFoundError:
    try:
        import multipart  # type: ignore # noqa: F401

        _MULTIPART_AVAILABLE = True
    except ModuleNotFoundError:
        _MULTIPART_AVAILABLE = False


if _MULTIPART_AVAILABLE:

    @router.post("/audio/transcribe", response_model=Envelope[Transcript])
    async def transcribe(file: UploadFile = File(...)) -> Envelope[Transcript]:
        transcript = transcribe_upload(file)
        return envelope(transcript)

else:

    @router.post("/audio/transcribe", response_model=Envelope[Transcript])
    async def transcribe_unavailable() -> Envelope[Transcript]:
        add_warning(
            "python-multipart is not installed. Install it to enable /audio/transcribe file uploads."
        )
        return envelope(
            Transcript.model_validate(
                {
                    "text": "",
                    "metadata": {
                        "model": "multipart-unavailable",
                        "language": None,
                        "duration_seconds": None,
                        "source": "audio_unprocessed",
                    },
                }
            )
        )
