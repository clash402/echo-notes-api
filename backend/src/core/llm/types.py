from dataclasses import dataclass
from typing import Protocol


@dataclass
class LLMUsage:
    prompt_tokens: int
    completion_tokens: int
    usd: float


@dataclass
class LLMResponse:
    content: str
    usage: LLMUsage
    provider: str
    model: str


class LLMProvider(Protocol):
    name: str

    def generate(self, *, model: str, prompt: str, transcript: str) -> LLMResponse:
        """Return model output and normalized usage."""
