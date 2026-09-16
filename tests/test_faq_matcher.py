from fastapi.testclient import TestClient

from backend.faq_matcher import (
    POPULAR_DEMO_URL,
    PREMIUM_DEMO_URL,
    TWIN_DEMO_URL,
    find_faq_answer,
)
from backend.main import app


client = TestClient(app)


def test_space_question():
    match = find_faq_answer("How much space does it need?")
    assert match is not None
    assert match["id"] == "install_space"
    assert "4" in match["answer"]


def test_smell_question():
    match = find_faq_answer("Does it smell?")
    assert match is not None
    assert match["id"] == "use_smell"


def test_bones_question():
    match = find_faq_answer("Can I put bones in it?")
    assert match is not None
    assert match["id"] == "use_avoid"
    assert "bones" in match["answer"].lower()


def test_composting_time():
    match = find_faq_answer("How long does composting take?")
    assert match is not None
    assert match["id"] == "use_time"


def test_monthly_cost():
    match = find_faq_answer("How much does it cost every month?")
    assert match is not None
    assert match["id"] == "cost_monthly"


def test_popular_premium_difference():
    match = find_faq_answer("What is the difference between Premium and Popular?")
    assert match is not None
    assert match["id"] == "feature_difference"


def test_liquid_fertilizer():
    match = find_faq_answer("Do I get liquid fertilizer?")
    assert match is not None
    assert match["id"] == "feature_fertilizer"


def test_booking():
    match = find_faq_answer("How do I book one?")
    assert match is not None
    assert match["id"] == "start_book"


def test_payment():
    match = find_faq_answer("How can I pay?")
    assert match is not None
    assert match["id"] == "start_pay"


def test_delivery_time_variants():
    for question in (
        "How long does delivery take?",
        "What is the delivery time?",
        "How long does shipping take?",
    ):
        match = find_faq_answer(question)
        assert match is not None, question
        assert match["id"] == "start_delivery"


def test_warranty():
    match = find_faq_answer("What is the warranty?")
    assert match is not None
    assert match["id"] == "warranty_lifespan"


def test_subscribe():
    match = find_faq_answer("Can I subscribe to supplies?")
    assert match is not None
    assert match["id"] == "support_subscribe"


def test_premium_demo():
    match = find_faq_answer("Show me the Premium demo.")
    assert match is not None
    assert PREMIUM_DEMO_URL in match["answer"]
    assert POPULAR_DEMO_URL not in match["answer"]


def test_popular_demo():
    match = find_faq_answer("Show me the Popular demo.")
    assert match is not None
    assert POPULAR_DEMO_URL in match["answer"]


def test_twin_demo():
    match = find_faq_answer("Show me the Twin Composter demo.")
    assert match is not None
    assert TWIN_DEMO_URL in match["answer"]


def test_generic_demo():
    match = find_faq_answer("Give me a demo video.")
    assert match is not None
    assert PREMIUM_DEMO_URL in match["answer"]
    assert POPULAR_DEMO_URL in match["answer"]
    assert TWIN_DEMO_URL in match["answer"]


def test_weather_does_not_match_faq():
    assert find_faq_answer("What is the weather today?") is None


def test_chat_endpoint_returns_faq_answer():
    response = client.post("/api/chat", json={"message": "Does the composter smell?"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert "odor" in payload["response"].lower()
    assert payload["sources"][0]["type"] == "faq"
    assert payload["sources"][0]["question"]
