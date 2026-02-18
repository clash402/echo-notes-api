from src.services.reflection import reflect_transcript


def test_reflection_output_structure() -> None:
    transcript = (
        "I keep coming back to the API latency issue in the dashboard. "
        "I'm not sure whether the bottleneck is the query layer or the cache misses."
    )
    result = reflect_transcript(transcript)
    reflection = result.reflection

    assert reflection.title
    assert reflection.summary
    assert isinstance(reflection.themes, list) and reflection.themes
    assert isinstance(reflection.questions, list) and reflection.questions
    assert isinstance(reflection.next_thoughts, list) and reflection.next_thoughts
    assert reflection.confidence in {"high", "medium", "low"}
    assert result.internal_metadata.interpretation_level in {"low", "medium"}
