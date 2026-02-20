def test_notes_preflight_allows_local_frontend_origin(client) -> None:
    response = client.options(
        "/notes",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "GET" in response.headers["access-control-allow-methods"]


def test_notes_response_sets_cors_header_for_local_frontend(client) -> None:
    response = client.get("/notes", headers={"Origin": "http://localhost:3000"})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_notes_response_sets_cors_header_for_vercel_frontend(client) -> None:
    response = client.get(
        "/notes",
        headers={"Origin": "https://echo-notes-web-eta.vercel.app"},
    )

    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "https://echo-notes-web-eta.vercel.app"
    )
