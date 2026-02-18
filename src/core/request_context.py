from contextvars import ContextVar
from dataclasses import dataclass, field


@dataclass
class CostMeta:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    usd: float = 0.0


@dataclass
class RequestMeta:
    request_id: str = ""
    warnings: list[str] = field(default_factory=list)
    cost: CostMeta = field(default_factory=CostMeta)


_REQUEST_META: ContextVar[RequestMeta | None] = ContextVar("request_meta", default=None)


def set_request_meta(meta: RequestMeta) -> None:
    _REQUEST_META.set(meta)


def get_request_meta() -> RequestMeta:
    meta = _REQUEST_META.get()
    if meta is None:
        meta = RequestMeta()
        _REQUEST_META.set(meta)
    return meta


def add_warning(warning: str) -> None:
    meta = get_request_meta()
    meta.warnings.append(warning)


def record_cost(prompt_tokens: int = 0, completion_tokens: int = 0, usd: float = 0.0) -> None:
    meta = get_request_meta()
    meta.cost.prompt_tokens += prompt_tokens
    meta.cost.completion_tokens += completion_tokens
    meta.cost.usd += usd
