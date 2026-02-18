from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.core.settings import clear_settings_cache
from src.db.engine import init_db


@pytest.fixture(autouse=True)
def isolated_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    db_path = tmp_path / "echo_notes_test.db"
    monkeypatch.setenv("ECHO_NOTES_DB_PATH", str(db_path))
    monkeypatch.setenv("ECHO_NOTES_APP_NAME", "echo-notes-api-test")
    monkeypatch.setenv("ECHO_NOTES_LLM_PROVIDER", "auto")
    monkeypatch.setenv("ECHO_NOTES_EMBEDDING_PROVIDER", "auto")
    monkeypatch.setenv("ECHO_NOTES_TRANSCRIPTION_PROVIDER", "auto")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    clear_settings_cache()
    init_db()
    yield
    clear_settings_cache()


@pytest.fixture()
def client() -> Iterator[TestClient]:
    from main import app

    with TestClient(app) as test_client:
        yield test_client
