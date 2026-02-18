from src.core.settings import clear_settings_cache


def test_echo_openai_provider_without_key_falls_back(client, monkeypatch) -> None:
    monkeypatch.setenv("ECHO_NOTES_LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    clear_settings_cache()

    response = client.post(
        "/echo",
        json={"transcript": "I am uncertain about the deployment plan and still deciding."},
    )
    assert response.status_code == 200
    warnings = response.json()["meta"]["warnings"]
    assert any("OpenAI provider is unavailable" in warning for warning in warnings)


def test_notes_openai_embedding_without_key_falls_back(client, monkeypatch) -> None:
    monkeypatch.setenv("ECHO_NOTES_EMBEDDING_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    clear_settings_cache()

    response = client.post(
        "/notes",
        json={
            "transcript": "The migration plan changed and we need to revisit rollout sequencing."
        },
    )
    assert response.status_code == 200
    warnings = response.json()["meta"]["warnings"]
    assert any("embedding provider is missing API key" in warning for warning in warnings)


def test_audio_openai_transcription_without_key_returns_warning(client, monkeypatch) -> None:
    monkeypatch.setenv("ECHO_NOTES_TRANSCRIPTION_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    clear_settings_cache()

    response = client.post(
        "/audio/transcribe",
        files={"file": ("voice.wav", b"fake-audio-data", "audio/wav")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["text"] == ""
    assert payload["data"]["metadata"]["model"] == "whisper-unavailable"
    warnings = payload["meta"]["warnings"]
    assert any("OpenAI Whisper provider is unavailable" in warning for warning in warnings)
