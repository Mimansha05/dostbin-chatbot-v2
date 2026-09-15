from backend.llm import format_faq_context
from backend.rate_limit import InMemoryRateLimiter


def test_format_faq_context():
    context = format_faq_context(
        [
            {
                "id": "pricing_01",
                "category": "Pricing & Purchase",
                "question": "What models are available?",
                "answer": "Popular, Premium, and Twin Composter.",
                "keywords": ["pricing", "models"],
            }
        ]
    )
    assert "pricing_01" in context
    assert "Popular, Premium, and Twin Composter." in context


def test_rate_limiter_blocks_after_limit():
    limiter = InMemoryRateLimiter(max_requests=2, window_seconds=60)
    assert limiter.allow("127.0.0.1")[0] is True
    assert limiter.allow("127.0.0.1")[0] is True
    allowed, retry_after = limiter.allow("127.0.0.1")
    assert allowed is False
    assert retry_after >= 1
