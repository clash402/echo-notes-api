def test_root(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["message"] == "Echo Notes API"
    assert "request_id" in payload["meta"]
    assert payload["meta"]["cost"] == {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "usd": 0.0,
    }
    assert payload["meta"]["warnings"] == []
    assert response.headers.get("X-Request-Id") == payload["meta"]["request_id"]


def test_health(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["status"] == "healthy"
    assert "request_id" in payload["meta"]
    assert response.headers.get("X-Request-Id") == payload["meta"]["request_id"]
