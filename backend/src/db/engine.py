import sqlite3
from pathlib import Path

from backend.src.core.settings import get_settings
from backend.src.db.models import SCHEMA_STATEMENTS


def get_connection() -> sqlite3.Connection:
    settings = get_settings()
    db_path = settings.database_path
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(db_path), check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def init_db() -> None:
    connection = get_connection()
    try:
        for statement in SCHEMA_STATEMENTS:
            connection.execute(statement)
        _apply_lightweight_migrations(connection)
        connection.commit()
    finally:
        connection.close()


def _apply_lightweight_migrations(connection: sqlite3.Connection) -> None:
    note_columns = _table_columns(connection, "notes")
    if note_columns:
        if "transcript_metadata_json" not in note_columns:
            connection.execute("ALTER TABLE notes ADD COLUMN transcript_metadata_json TEXT")
        if "reflection_internal_json" not in note_columns:
            connection.execute("ALTER TABLE notes ADD COLUMN reflection_internal_json TEXT")


def _table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row["name"]) for row in rows}


def insert_cost_ledger_row(
    *,
    app: str,
    request_id: str,
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    usd: float,
) -> None:
    connection = get_connection()
    try:
        connection.execute(
            """
            INSERT INTO cost_ledger (
              app, request_id, provider, model, prompt_tokens, completion_tokens, usd
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (app, request_id, provider, model, prompt_tokens, completion_tokens, usd),
        )
        connection.commit()
    finally:
        connection.close()


def insert_reflection_event_row(
    *, transcript_text: str, reflection_json: str, reflection_internal_json: str
) -> None:
    connection = get_connection()
    try:
        connection.execute(
            """
            INSERT INTO reflection_events (
              transcript_text, reflection_json, reflection_internal_json
            ) VALUES (?, ?, ?)
            """,
            (transcript_text, reflection_json, reflection_internal_json),
        )
        connection.commit()
    finally:
        connection.close()
