from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "groq_configured" in payload


def test_chat_rejects_empty_message():
    response = client.post("/api/chat", json={"message": "   "})
    assert response.status_code == 400
    payload = response.json()
    assert payload["success"] is False


def test_chat_rejects_oversized_message():
    response = client.post("/api/chat", json={"message": "x" * 501})
    assert response.status_code == 422


def test_ask_rejects_empty_question():
    response = client.post("/ask", json={"question": "   "})
    assert response.status_code == 400


@patch("backend.main.find_faq_answer", return_value=None)
@patch("backend.main.search_faqs")
def test_chat_returns_fallback_without_llm_when_unrelated(mock_search, _mock_faq):
    mock_search.return_value = [
        {
            "id": "unrelated",
            "question": "Unrelated",
            "similarity_score": 0.1,
            "lexical_score": 0.0,
            "ranking_score": 0.1,
        }
    ]

    with patch("backend.main.generate_answer") as mock_generate:
        response = client.post("/api/chat", json={"message": "What is the capital of Mars?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert "knowledge base" in payload["response"].lower()
    mock_generate.assert_not_called()


@patch("backend.main.find_faq_answer", return_value=None)
@patch("backend.main.search_faqs")
@patch("backend.main.generate_answer", return_value="The Premium model is automatic.")
def test_chat_success(mock_generate, mock_search, _mock_faq):
    mock_search.return_value = [
        {
            "id": "product_01",
            "question": "What is the difference between the Popular and Premium models?",
            "similarity_score": 0.8,
            "lexical_score": 0.6,
            "ranking_score": 1.0,
        }
    ]

    response = client.post("/api/chat", json={"message": "Which model is automatic?"})
    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "success": True,
        "response": "The Premium model is automatic.",
        "sources": [
            {
                "id": "product_01",
                "question": "What is the difference between the Popular and Premium models?",
                "score": 0.8,
            }
        ],
    }
    mock_generate.assert_called_once()


@patch("backend.main.find_faq_answer", return_value=None)
@patch("backend.main.search_faqs")
@patch("backend.main.generate_answer", return_value="The Premium model is automatic.")
def test_ask_success(mock_generate, mock_search, _mock_faq):
    mock_search.return_value = [
        {
            "id": "product_01",
            "question": "What is the difference between the Popular and Premium models?",
            "similarity_score": 0.8,
            "lexical_score": 0.6,
            "ranking_score": 1.0,
        }
    ]

    response = client.post("/ask", json={"question": "Which model is automatic?"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "The Premium model is automatic."
    assert payload["question"] == "Which model is automatic?"
    mock_generate.assert_called_once()
