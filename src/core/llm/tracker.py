import sqlite3

from src.core.request_context import get_request_meta, record_cost
from src.core.settings import get_settings
from src.db.engine import insert_cost_ledger_row


def track_llm_call(
    *, provider: str, model: str, prompt_tokens: int, completion_tokens: int, usd: float
) -> None:
    record_cost(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, usd=usd)
    request_meta = get_request_meta()
    settings = get_settings()
    try:
        insert_cost_ledger_row(
            app=settings.app_name,
            request_id=request_meta.request_id,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            usd=usd,
        )
    except sqlite3.Error:
        # Unit-level service calls may occur before app startup initializes schema.
        pass
