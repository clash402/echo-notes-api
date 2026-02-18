import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from src.core.request_context import RequestMeta, set_request_meta


async def request_context_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    set_request_meta(RequestMeta(request_id=request_id))

    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response
