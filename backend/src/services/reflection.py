import json
import sqlite3
from dataclasses import dataclass
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import ValidationError

from backend.src.core.llm.providers import LocalHeuristicLLMProvider, resolve_llm_provider
from backend.src.core.llm.router import ModelRouter
from backend.src.core.llm.tracker import track_llm_call
from backend.src.core.request_context import add_warning
from backend.src.db.engine import insert_reflection_event_row
from backend.src.schemas.reflection import Reflection

REFLECTION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "You are Echo Notes. Reflect only what is explicitly supported by transcript evidence. "
                "Never diagnose, moralize, or provide direct advice unless the user already implied it. "
                "If uncertain, acknowledge uncertainty. Prefer under-interpretation to over-interpretation. "
                "Return strict JSON with keys: title, summary, themes, questions, next_thoughts, confidence."
            ),
        ),
        (
            "human",
            (
                "Transcript:\n{transcript}\n\n"
                "Produce concise reflection JSON. Confidence must be one of high, medium, low."
            ),
        ),
    ]
)


@dataclass
class ReflectionInternalMetadata:
    interpretation_level: Literal["low", "medium"]
    ambiguity_detected: bool


@dataclass
class ReflectionResult:
    reflection: Reflection
    internal_metadata: ReflectionInternalMetadata


def reflect_transcript(transcript: str) -> ReflectionResult:
    cleaned = transcript.strip()
    if not cleaned:
        add_warning("Transcript is empty; reflection confidence was set to low.")
        reflection = Reflection(
            title="Empty transcript",
            summary="No clear transcript content was provided.",
            themes=["unclear input"],
            questions=["Could you provide more detail in a follow-up note?"],
            next_thoughts=["Possible area to expand: the core topic you intended to capture."],
            confidence="low",
        )
        return ReflectionResult(
            reflection=reflection,
            internal_metadata=ReflectionInternalMetadata(
                interpretation_level="low", ambiguity_detected=True
            ),
        )

    router = ModelRouter()
    model = router.route(tier="default")
    resolution = resolve_llm_provider()
    provider = resolution.provider
    if resolution.warning:
        add_warning(resolution.warning)
    prompt_value = REFLECTION_PROMPT.invoke({"transcript": cleaned})
    rendered_prompt = prompt_value.to_string()

    try:
        llm_response = provider.generate(model=model, prompt=rendered_prompt, transcript=cleaned)
    except Exception:
        add_warning("External LLM call failed; local reflection fallback was used.")
        fallback_provider = LocalHeuristicLLMProvider()
        llm_response = fallback_provider.generate(
            model=model, prompt=rendered_prompt, transcript=cleaned
        )
    track_llm_call(
        provider=llm_response.provider,
        model=llm_response.model,
        prompt_tokens=llm_response.usage.prompt_tokens,
        completion_tokens=llm_response.usage.completion_tokens,
        usd=llm_response.usage.usd,
    )

    reflection = _parse_reflection(llm_response.content)
    ambiguity_detected = reflection.confidence != "high"
    interpretation_level: Literal["low", "medium"] = "medium" if ambiguity_detected else "low"
    internal_metadata = ReflectionInternalMetadata(
        interpretation_level=interpretation_level,
        ambiguity_detected=ambiguity_detected,
    )
    if ambiguity_detected:
        add_warning("Reflection contains ambiguity; confidence is below high.")

    _persist_reflection_event(
        transcript=cleaned,
        reflection=reflection,
        internal_metadata=internal_metadata,
    )

    return ReflectionResult(reflection=reflection, internal_metadata=internal_metadata)


def _parse_reflection(content: str) -> Reflection:
    try:
        payload = json.loads(content)
        return Reflection.model_validate(payload)
    except (json.JSONDecodeError, ValidationError):
        extracted_payload = _try_extract_json_object(content)
        if extracted_payload is not None:
            try:
                return Reflection.model_validate(extracted_payload)
            except ValidationError:
                pass
        add_warning("Reflection provider response was malformed; fallback reflection was used.")
        return Reflection(
            title="Fallback reflection",
            summary="The transcript was processed, but structured reflection parsing was incomplete.",
            themes=["processing fallback"],
            questions=["Which part of the transcript should be clarified first?"],
            next_thoughts=["Possible area to expand: the most specific claim in the transcript."],
            confidence="low",
        )


def _persist_reflection_event(
    *,
    transcript: str,
    reflection: Reflection,
    internal_metadata: ReflectionInternalMetadata,
) -> None:
    try:
        insert_reflection_event_row(
            transcript_text=transcript,
            reflection_json=json.dumps(reflection.model_dump()),
            reflection_internal_json=json.dumps(
                {
                    "interpretation_level": internal_metadata.interpretation_level,
                    "ambiguity_detected": internal_metadata.ambiguity_detected,
                }
            ),
        )
    except sqlite3.Error:
        add_warning("Reflection metadata persistence failed for this request.")


def _try_extract_json_object(content: str) -> dict | None:
    if "{" not in content or "}" not in content:
        return None
    start = content.find("{")
    end = content.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        payload = json.loads(content[start : end + 1])
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None
