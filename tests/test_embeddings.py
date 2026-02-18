from backend.src.services.embeddings import cosine_similarity, generate_embedding


def test_embedding_similarity_prefers_related_text() -> None:
    text_a = "Database migration failed during deployment and caused API downtime."
    text_b = "API downtime happened after a failed database migration in production."
    text_c = "I cooked pasta for dinner and listened to a jazz album."

    emb_a = generate_embedding(text_a)
    emb_b = generate_embedding(text_b)
    emb_c = generate_embedding(text_c)

    sim_related = cosine_similarity(emb_a, emb_b)
    sim_unrelated = cosine_similarity(emb_a, emb_c)
    assert sim_related > sim_unrelated
