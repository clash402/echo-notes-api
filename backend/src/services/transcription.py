from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import tempfile
from typing import Protocol

from fastapi import UploadFile

from backend.src.core.request_context import add_warning
from backend.src.core.settings import get_settings
from backend.src.schemas.transcript import Transcript, TranscriptMetadata


class TranscriptionProvider(Protocol):
    name: str

    def transcribe(self, *, audio_path: Path, filename: str, content_type: str) -> Transcript:
        """Transcribe an audio file into text."""


@dataclass
class TranscriptionProviderResolution:
    provider: TranscriptionProvider | None
    warning: str | None = None


class LocalWhisperTranscriptionProvider:
    name = "whisper-local"

    def __init__(self, *, model_name: str) -> None:
        self.model_name = model_name

    def transcribe(self, *, audio_path: Path, filename: str, content_type: str) -> Transcript:
        model = _load_whisper_model(self.model_name)
        result = model.transcribe(str(audio_path))  # type: ignore[attr-defined]
        transcript_text = (result.get("text") or "").strip()
        language = result.get("language")
        return Transcript(
            text=transcript_text,
            metadata=TranscriptMetadata(
                model=f"whisper-{self.model_name}",
                language=language,
                duration_seconds=None,
                source="whisper_local",
            ),
        )


class OpenAIWhisperTranscriptionProvider:
    name = "whisper-openai-api"

    def __init__(self, *, api_key: str, base_url: str | None, model: str) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    def transcribe(self, *, audio_path: Path, filename: str, content_type: str) -> Transcript:
        try:
            from openai import OpenAI
        except ModuleNotFoundError as exc:
            raise RuntimeError("openai package is not installed") from exc

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        with audio_path.open("rb") as handle:
            result = client.audio.transcriptions.create(
                model=self.model,
                file=handle,
                response_format="verbose_json",
            )

        language = getattr(result, "language", None)
        duration = getattr(result, "duration", None)
        transcript_text = str(getattr(result, "text", "")).strip()
        return Transcript(
            text=transcript_text,
            metadata=TranscriptMetadata(
                model=self.model,
                language=language,
                duration_seconds=float(duration) if duration is not None else None,
                source="whisper_openai_api",
            ),
        )


def transcribe_upload(file: UploadFile) -> Transcript:
    content = file.file.read()
    content_type = file.content_type or ""
    filename = file.filename or "upload.wav"
    lowercase_name = filename.lower()

    if content_type.startswith("text/") or lowercase_name.endswith(".txt"):
        text = content.decode("utf-8", errors="ignore").strip()
        return Transcript(
            text=text,
            metadata=TranscriptMetadata(
                model="text-passthrough-v1",
                language="en",
                duration_seconds=None,
                source="text",
            ),
        )

    suffix = Path(lowercase_name).suffix if "." in lowercase_name else ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as temp_file:
        temp_file.write(content)
        temp_file.flush()
        audio_path = Path(temp_file.name)
        resolution = _resolve_transcription_provider()
        if resolution.warning:
            add_warning(resolution.warning)
        if resolution.provider is None:
            return _unavailable_transcript()

        try:
            return resolution.provider.transcribe(
                audio_path=audio_path,
                filename=filename,
                content_type=content_type,
            )
        except Exception:
            add_warning("Primary transcription provider failed; attempting local Whisper fallback.")
            fallback = _resolve_local_provider()
            if fallback is not None:
                try:
                    return fallback.transcribe(
                        audio_path=audio_path,
                        filename=filename,
                        content_type=content_type,
                    )
                except Exception:
                    add_warning("Local Whisper fallback failed.")

    return _unavailable_transcript()


def _unavailable_transcript() -> Transcript:
    add_warning("Transcription provider unavailable; transcription was not performed.")
    return Transcript(
        text="",
        metadata=TranscriptMetadata(
            model="whisper-unavailable",
            language=None,
            duration_seconds=None,
            source="audio_unprocessed",
        ),
    )


def _resolve_transcription_provider() -> TranscriptionProviderResolution:
    settings = get_settings()
    requested = settings.transcription_provider.lower()

    if requested in {"local", "auto"}:
        local_provider = _resolve_local_provider()
        if local_provider is not None:
            return TranscriptionProviderResolution(provider=local_provider)
        if requested == "local":
            return TranscriptionProviderResolution(
                provider=None,
                warning="Configured local Whisper provider is unavailable.",
            )

    if requested in {"openai", "auto"}:
        openai_provider = _resolve_openai_provider()
        if openai_provider is not None:
            return TranscriptionProviderResolution(provider=openai_provider)
        if requested == "openai":
            return TranscriptionProviderResolution(
                provider=None,
                warning="Configured OpenAI Whisper provider is unavailable.",
            )

    if requested not in {"local", "openai", "auto"}:
        return TranscriptionProviderResolution(
            provider=None,
            warning=f"Unknown transcription provider '{settings.transcription_provider}'.",
        )

    return TranscriptionProviderResolution(provider=None)


def _resolve_local_provider() -> LocalWhisperTranscriptionProvider | None:
    settings = get_settings()
    try:
        import whisper  # noqa: F401
    except ModuleNotFoundError:
        return None
    return LocalWhisperTranscriptionProvider(model_name=settings.whisper_local_model)


def _resolve_openai_provider() -> OpenAIWhisperTranscriptionProvider | None:
    settings = get_settings()
    if not settings.openai_api_key:
        return None
    try:
        import openai  # noqa: F401
    except ModuleNotFoundError:
        return None
    return OpenAIWhisperTranscriptionProvider(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        model=settings.whisper_openai_model,
    )


@lru_cache(maxsize=2)
def _load_whisper_model(model_name: str):
    import whisper  # type: ignore

    return whisper.load_model(model_name)
