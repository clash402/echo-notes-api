def test_record_reflect_save_fetch_flow(client) -> None:
    transcript = (
        "I need to stabilize release deployments. The rollback process is slow and unclear."
    )

    transcribe_response = client.post(
        "/audio/transcribe",
        files={
            "file": (
                "voice-note.txt",
                transcript.encode("utf-8"),
                "text/plain",
            )
        },
    )
    assert transcribe_response.status_code == 200
    transcribed_text = transcribe_response.json()["data"]["text"]

    echo_response = client.post("/echo", json={"transcript": transcribed_text})
    assert echo_response.status_code == 200
    echo_payload = echo_response.json()
    assert echo_payload["data"]["summary"]
    assert echo_payload["data"]["confidence"] in {"high", "medium", "low"}
    assert echo_payload["meta"]["cost"]["prompt_tokens"] > 0

    note1_response = client.post(
        "/notes",
        json={
            "transcript": "Release deployment was unstable and rollback took too long.",
            "audio_reference": "s3://notes/audio-1.wav",
        },
    )
    assert note1_response.status_code == 200
    note1_payload = note1_response.json()
    note1_id = note1_payload["data"]["id"]

    note2_response = client.post(
        "/notes",
        json={
            "transcript": "Deployments are still unstable and rollback remains a bottleneck.",
            "audio_reference": "s3://notes/audio-2.wav",
        },
    )
    assert note2_response.status_code == 200
    note2_payload = note2_response.json()
    note2_id = note2_payload["data"]["id"]
    assert note2_payload["meta"]["cost"]["prompt_tokens"] > 0

    fetch_response = client.get(f"/notes/{note2_id}")
    assert fetch_response.status_code == 200
    fetched_note = fetch_response.json()["data"]
    related_note_ids = [item["related_note_id"] for item in fetched_note["related_notes"]]
    assert note1_id in related_note_ids

    list_response = client.get("/notes")
    assert list_response.status_code == 200
    notes = list_response.json()["data"]["notes"]
    ids = [note["id"] for note in notes]
    assert note1_id in ids
    assert note2_id in ids
