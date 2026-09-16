from backend.retriever import search_faqs


def test_search_returns_expected_fields():
    results = search_faqs("Which model is automatic?")
    assert results
    first = results[0]
    for field in (
        "id",
        "question",
        "answer",
        "category",
        "similarity_score",
        "lexical_score",
        "ranking_score",
    ):
        assert field in first


def test_search_finds_premium_for_automatic():
    results = search_faqs("Which model is automatic?")
    ids = [result["id"] for result in results]
    assert "product_01" in ids
    assert results[0]["ranking_score"] >= 0.4
