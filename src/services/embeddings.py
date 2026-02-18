import hashlib
import math
import re
from dataclasses import dataclass
from typing import Protocol

from src.core.request_context import add_warning
from src.core.settings import get_settings
from src.core.llm.tracker import track_llm_call


@dataclass
class EmbeddingResult:
    vector: list[float]
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    usd: float


class EmbeddingProvider(Protocol):
    name: str

    def embed(self, *, text: str, model: str) -> EmbeddingResult:
        """Generate embedding vector for text."""


class LocalHashEmbeddingProvider:
    name = "local-hash-embedding"

    def __init__(self, dimension: int = 64) -> None:
        self.dimension = dimension

    def embed(self, *, text: str, model: str) -> EmbeddingResult:
        vector = [0.0] * self.dimension
        tokens = re.findall(r"[a-zA-Z0-9']+", text.lower())
        if not tokens:
            return EmbeddingResult(
                vector=vector,
                provider=self.name,
                model=model,
                prompt_tokens=0,
                completion_tokens=0,
                usd=0.0,
            )

        for token in tokens:
            hashed = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
            index = hashed % self.dimension
            sign = 1.0 if ((hashed >> 8) & 1) else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(component * component for component in vector))
        normalized = [component / norm for component in vector] if norm else vector
        prompt_tokens = max(1, int(len(text) / 4))
        return EmbeddingResult(
            vector=normalized,
            provider=self.name,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=0,
            usd=round(prompt_tokens * 0.00000002, 8),
        )


class OpenAIEmbeddingProvider:
    name = "openai-embedding"

    def __init__(self, *, api_key: str, base_url: str | None, cost_per_1k: float) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.cost_per_1k = cost_per_1k

    def embed(self, *, text: str, model: str) -> EmbeddingResult:
        try:
            from openai import OpenAI
        except ModuleNotFoundError as exc:
            raise RuntimeError("openai package is not installed") from exc

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        result = client.embeddings.create(model=model, input=text)
        vector = [float(value) for value in result.data[0].embedding]
        usage = result.usage
        prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or max(1, int(len(text) / 4)))
        usd = round((prompt_tokens * self.cost_per_1k) / 1000, 8)
        return EmbeddingResult(
            vector=vector,
            provider=self.name,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=0,
            usd=usd,
        )


def generate_embedding(text: str) -> list[float]:
    provider, model = _resolve_embedding_provider()
    try:
        result = provider.embed(text=text, model=model)
    except Exception:
        add_warning("External embedding call failed; local embedding fallback was used.")
        fallback = LocalHashEmbeddingProvider()
        result = fallback.embed(text=text, model="hash-emb-v1")

    track_llm_call(
        provider=result.provider,
        model=result.model,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        usd=result.usd,
    )
    return result.vector


def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    if not vector_a or not vector_b or len(vector_a) != len(vector_b):
        return 0.0

    numerator = sum(a * b for a, b in zip(vector_a, vector_b, strict=False))
    norm_a = math.sqrt(sum(value * value for value in vector_a))
    norm_b = math.sqrt(sum(value * value for value in vector_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return numerator / (norm_a * norm_b)


def _resolve_embedding_provider() -> tuple[EmbeddingProvider, str]:
    settings = get_settings()
    requested = settings.embedding_provider.lower()
    local_provider = LocalHashEmbeddingProvider()

    if requested in {"openai", "auto"}:
        if settings.openai_api_key:
            try:
                import openai  # noqa: F401
            except ModuleNotFoundError:
                if requested == "openai":
                    add_warning(
                        "Configured OpenAI embedding provider is unavailable; local fallback was used."
                    )
            else:
                return (
                    OpenAIEmbeddingProvider(
                        api_key=settings.openai_api_key,
                        base_url=settings.openai_base_url,
                        cost_per_1k=settings.embedding_cost_per_1k,
                    ),
                    settings.embedding_model,
                )
        elif requested == "openai":
            add_warning("Configured OpenAI embedding provider is missing API key.")

    if requested not in {"local", "openai", "auto"}:
        add_warning(
            f"Unknown embedding provider '{settings.embedding_provider}'; local fallback was used."
        )

    return local_provider, "hash-emb-v1"
