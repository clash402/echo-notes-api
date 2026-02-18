from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from backend.src.core.request_context import get_request_meta

T = TypeVar("T")


class CostPayload(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    usd: float = 0.0


class MetaPayload(BaseModel):
    request_id: str
    cost: CostPayload = Field(default_factory=CostPayload)
    warnings: list[str] = Field(default_factory=list)


class Envelope(BaseModel, Generic[T]):
    data: T
    meta: MetaPayload


def build_meta() -> MetaPayload:
    request_meta = get_request_meta()
    return MetaPayload(
        request_id=request_meta.request_id,
        cost=CostPayload(
            prompt_tokens=request_meta.cost.prompt_tokens,
            completion_tokens=request_meta.cost.completion_tokens,
            usd=request_meta.cost.usd,
        ),
        warnings=request_meta.warnings,
    )


def envelope(data: T) -> Envelope[T]:
    return Envelope[T](data=data, meta=build_meta())
