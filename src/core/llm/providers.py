import json
import re
from collections import Counter
from dataclasses import dataclass

from src.core.settings import get_settings
from src.core.llm.types import LLMResponse, LLMUsage

_AMBIGUITY_MARKERS = (
    "maybe",
    "not sure",
    "kind of",
    "sort of",
    "i guess",
    "unclear",
    "probably",
)

_STOPWORDS = {
    "about",
    "after",
    "again",
    "also",
    "because",
    "been",
    "being",
    "could",
    "from",
    "have",
    "into",
    "just",
    "like",
    "really",
    "that",
    "their",
    "them",
    "then",
    "there",
    "they",
    "this",
    "with",
    "would",
}


@dataclass
class ProviderResolution:
    provider: "LocalHeuristicLLMProvider | OpenAILLMProvider"
    warning: str | None = None


class LocalHeuristicLLMProvider:
    """Local fallback provider used for deterministic development behavior."""

    name = "local-heuristic"

    def generate(self, *, model: str, prompt: str, transcript: str) -> LLMResponse:
        payload = self._build_reflection_payload(transcript)
        prompt_tokens = max(1, int((len(prompt) + len(transcript)) / 4))
        completion_tokens = max(1, int(len(json.dumps(payload)) / 4))
        usage = LLMUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            usd=round(prompt_tokens * 0.0000002 + completion_tokens * 0.0000008, 8),
        )
        return LLMResponse(
            content=json.dumps(payload),
            usage=usage,
            provider=self.name,
            model=model,
        )

    def _build_reflection_payload(self, transcript: str) -> dict:
        cleaned = " ".join(transcript.split())
        sentences = [
            piece.strip() for piece in re.split(r"(?<=[.?!])\s+", cleaned) if piece.strip()
        ]
        themes = self._extract_themes(cleaned)
        confidence = self._confidence(cleaned)

        explicit_questions = [item.rstrip("?") + "?" for item in sentences if item.endswith("?")]
        if explicit_questions:
            questions = explicit_questions[:3]
        else:
            focus = themes[0] if themes else "what you shared"
            questions = [f"What feels least resolved about {focus}?"]

        next_thoughts = [f"Possible area to expand: {theme}." for theme in themes[:3]]
        if not next_thoughts:
            next_thoughts = ["Possible area to expand: the central idea you described."]

        summary = " ".join(sentences[:2]).strip() if sentences else ""
        if not summary:
            summary = "The transcript is brief, and the core intent is not fully explicit."

        title_words = cleaned.split()[:8]
        title = " ".join(title_words).strip().capitalize() if title_words else "Untitled reflection"

        return {
            "title": title,
            "summary": summary,
            "themes": themes or ["general context"],
            "questions": questions,
            "next_thoughts": next_thoughts,
            "confidence": confidence,
        }

    def _extract_themes(self, transcript: str) -> list[str]:
        words = re.findall(r"[a-zA-Z][a-zA-Z0-9'-]+", transcript.lower())
        filtered = [word for word in words if word not in _STOPWORDS and len(word) > 3]
        frequencies = Counter(filtered)
        return [theme for theme, _ in frequencies.most_common(4)]

    def _confidence(self, transcript: str) -> str:
        lowered = transcript.lower()
        ambiguity_hits = sum(1 for marker in _AMBIGUITY_MARKERS if marker in lowered)
        word_count = len(transcript.split())
        if word_count < 15 or ambiguity_hits >= 2:
            return "low"
        if word_count < 40 or ambiguity_hits == 1:
            return "medium"
        return "high"


class OpenAILLMProvider:
    name = "openai-chat"

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str | None,
        prompt_cost_per_1k: float,
        completion_cost_per_1k: float,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.prompt_cost_per_1k = prompt_cost_per_1k
        self.completion_cost_per_1k = completion_cost_per_1k

    def generate(self, *, model: str, prompt: str, transcript: str) -> LLMResponse:
        try:
            from openai import OpenAI
        except ModuleNotFoundError as exc:
            raise RuntimeError("openai package is not installed") from exc

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = completion.choices[0].message.content or ""
        usage = completion.usage
        prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
        if prompt_tokens == 0 and completion_tokens == 0:
            prompt_tokens = max(1, int((len(prompt) + len(transcript)) / 4))
            completion_tokens = max(1, int(len(content) / 4))

        usd = round(
            (
                prompt_tokens * self.prompt_cost_per_1k
                + completion_tokens * self.completion_cost_per_1k
            )
            / 1000,
            8,
        )
        return LLMResponse(
            content=content,
            usage=LLMUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                usd=usd,
            ),
            provider=self.name,
            model=model,
        )


def resolve_llm_provider() -> ProviderResolution:
    settings = get_settings()
    requested = settings.llm_provider.lower()
    local_provider = LocalHeuristicLLMProvider()

    if requested in {"openai", "auto"}:
        provider = _build_openai_provider()
        if provider is not None:
            return ProviderResolution(provider=provider)
        if requested == "openai":
            return ProviderResolution(
                provider=local_provider,
                warning="Configured OpenAI provider is unavailable; falling back to local reflection.",
            )

    if requested not in {"local", "auto", "openai"}:
        return ProviderResolution(
            provider=local_provider,
            warning=f"Unknown LLM provider '{settings.llm_provider}'. Falling back to local reflection.",
        )

    return ProviderResolution(provider=local_provider)


def _build_openai_provider() -> OpenAILLMProvider | None:
    settings = get_settings()
    if not settings.openai_api_key:
        return None

    try:
        import openai  # noqa: F401
    except ModuleNotFoundError:
        return None

    return OpenAILLMProvider(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        prompt_cost_per_1k=settings.llm_prompt_cost_per_1k,
        completion_cost_per_1k=settings.llm_completion_cost_per_1k,
    )
