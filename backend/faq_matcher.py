import re
from difflib import SequenceMatcher


PREMIUM_DEMO_URL = "https://www.youtube.com/watch?v=UubAcD1v45s"
POPULAR_DEMO_URL = "https://www.youtube.com/watch?v=bKdL6QUqdgA&t=1s"
TWIN_DEMO_URL = "https://www.youtube.com/watch?v=7_gRB-VfLmo"

MIN_FAQ_CONFIDENCE = 0.5
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "can",
    "do",
    "does",
    "for",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "where",
    "which",
    "with",
    "you",
    "your",
    "dostbin",
    "bin",
    "composter",
}

APPROVED_FAQS = [
    {
        "id": "start_book",
        "category": "Getting Started & Purchase",
        "question": "How do I book one?",
        "answer": "You can pre-book any model on our website for ₹2,000. Our team will then contact you for the rest of the process.",
        "keywords": [
            "book",
            "booking",
            "pre-book",
            "prebook",
            "reserve",
            "order",
            "deposit",
            "2000",
        ],
    },
    {
        "id": "start_pay",
        "category": "Getting Started & Purchase",
        "question": "How do I pay?",
        "answer": "We accept Bank Transfer or QR Code. Cash on Delivery is only available if you pick up the bin from our Bangalore office.",
        "keywords": [
            "pay",
            "payment",
            "bank transfer",
            "qr",
            "qr code",
            "cash on delivery",
            "cod",
        ],
    },
    {
        "id": "start_delivery",
        "category": "Getting Started & Purchase",
        "question": "How soon will I get it after booking?",
        "answer": "Once you pre-book, your bin is usually dispatched within one week.",
        "keywords": [
            "delivery",
            "dispatch",
            "shipping time",
            "how soon",
            "how long",
            "arrive",
            "get it",
            "one week",
        ],
    },
    {
        "id": "start_shipping_cost",
        "category": "Getting Started & Purchase",
        "question": "Shipping costs",
        "answer": "Our prices usually include GST and delivery, so you typically don't have to pay anything extra when it arrives.",
        "keywords": [
            "shipping cost",
            "shipping costs",
            "delivery cost",
            "gst",
            "extra charge",
            "include delivery",
        ],
    },
    {
        "id": "start_demo",
        "category": "Getting Started & Purchase",
        "question": "Where can I see it in action?",
        "answer": (
            "You can watch demo videos for our models here:\n"
            f"DOSTBin Premium Demo: {PREMIUM_DEMO_URL}\n"
            f"DOSTBin Popular Demo: {POPULAR_DEMO_URL}\n"
            f"DOSTBin Twin Composter Demo: {TWIN_DEMO_URL}"
        ),
        "keywords": [
            "in action",
            "see it",
            "watch",
            "youtube",
            "demo videos",
        ],
    },
    {
        "id": "install_space",
        "category": "Installation & Space Requirements",
        "question": "How much space do I need?",
        "answer": "The Premium and Popular models fit easily in a balcony or utility area. They need about 4 × 2 ft of floor space and 3 ft of height.",
        "keywords": [
            "space",
            "room",
            "size",
            "balcony",
            "floor space",
            "dimensions",
            "how much space",
        ],
    },
    {
        "id": "install_professional",
        "category": "Installation & Space Requirements",
        "question": "Do I need a professional to install it?",
        "answer": "Not at all! It is a plug-and-play device. We provide support over video calls if you need help with your first harvest.",
        "keywords": [
            "install",
            "installation",
            "professional",
            "plug and play",
            "setup",
            "technician",
        ],
    },
    {
        "id": "use_avoid",
        "category": "Using the Composter",
        "question": "What waste should I avoid?",
        "answer": "It's best to skip bones and mango seeds to keep the blades sharp.",
        "keywords": [
            "bones",
            "mango seeds",
            "avoid",
            "cannot put",
            "don't put",
            "skip",
            "waste should i avoid",
        ],
    },
    {
        "id": "use_time",
        "category": "Using the Composter",
        "question": "How long does composting take?",
        "answer": "The composting cycle usually takes 14–20 days.",
        "keywords": [
            "composting take",
            "how long does composting",
            "cycle",
            "14",
            "20 days",
            "compost time",
        ],
    },
    {
        "id": "use_smell",
        "category": "Using the Composter",
        "question": "Does it smell or attract pests?",
        "answer": "Not at all! Our Remix Powder and Activated Charcoal keep the process hygienic and 100% odor-free, making it perfect for indoor or balcony use.",
        "keywords": [
            "smell",
            "odor",
            "odour",
            "pests",
            "flies",
            "stink",
            "odor-free",
            "hygienic",
        ],
    },
    {
        "id": "feature_difference",
        "category": "Product Features",
        "question": "How exactly do the manual and automatic models differ?",
        "answer": "The Manual (Popular) model requires you to turn a handle for 2 minutes once a day. The Automatic (Premium) model is fully sensor-based and handles all the mixing and shredding for you.",
        "keywords": [
            "difference",
            "differ",
            "popular",
            "premium",
            "manual",
            "automatic",
            "sensor",
            "handle",
        ],
    },
    {
        "id": "feature_fertilizer",
        "category": "Product Features",
        "question": "Do I get liquid fertilizer?",
        "answer": "Yes. Along with solid compost, you get a natural liquid fertilizer from your waste that is great for watering your garden.",
        "keywords": [
            "liquid fertilizer",
            "fertilizer",
            "fertiliser",
            "liquid",
            "garden",
        ],
    },
    {
        "id": "feature_bulk",
        "category": "Product Features",
        "question": "Do you offer a solution for bulk waste?",
        "answer": "Yes. For apartments or communities, we offer a Twin Composter that handles much larger amounts of waste.",
        "keywords": [
            "bulk",
            "twin",
            "twin composter",
            "apartment",
            "community",
            "larger",
        ],
    },
    {
        "id": "feature_materials",
        "category": "Product Features",
        "question": "What materials are used to make the bins?",
        "answer": "The bins are made with strong polymer and stainless steel parts to ensure they last for over 10 years.",
        "keywords": [
            "materials",
            "made of",
            "polymer",
            "stainless steel",
            "steel",
        ],
    },
    {
        "id": "cost_monthly",
        "category": "Costs & Value",
        "question": "What are the monthly costs?",
        "answer": "Electricity and powder accessories typically cost under ₹300 per month.",
        "keywords": [
            "monthly",
            "every month",
            "per month",
            "running cost",
            "electricity",
            "300",
        ],
    },
    {
        "id": "cost_roi",
        "category": "Costs & Value",
        "question": "What is the return on investment (ROI)?",
        "answer": "The machine pays for itself in about 2–3 years through the high-quality compost and liquid fertilizer you produce.",
        "keywords": [
            "roi",
            "return on investment",
            "pays for itself",
            "2-3 years",
            "investment",
        ],
    },
    {
        "id": "warranty_lifespan",
        "category": "Warranty & Durability",
        "question": "What is the warranty and lifespan?",
        "answer": "Our bins are built to last over 10 years. The Premium model comes with a 1-year warranty on electrical parts.",
        "keywords": [
            "warranty",
            "lifespan",
            "guarantee",
            "10 years",
            "electrical parts",
        ],
    },
    {
        "id": "warranty_sturdy",
        "category": "Warranty & Durability",
        "question": "How sturdy is the composter?",
        "answer": "The strong polymer body and stainless steel components are designed for long-term durability.",
        "keywords": [
            "sturdy",
            "durable",
            "durability",
            "strong",
            "build quality",
        ],
    },
    {
        "id": "support_help",
        "category": "Support & Services",
        "question": "What support do you provide?",
        "answer": "We provide video call support and phone assistance to guide you until you successfully harvest your very first batch of compost.",
        "keywords": [
            "support",
            "video call",
            "phone",
            "assistance",
            "help",
            "first harvest",
        ],
    },
    {
        "id": "support_subscribe",
        "category": "Support & Services",
        "question": "Can I subscribe to supplies?",
        "answer": "Yes! We offer a yearly subscription for accessories like cocopeat and compost enhancers so you always have what you need.",
        "keywords": [
            "subscribe",
            "subscription",
            "supplies",
            "cocopeat",
            "accessories",
            "enhancers",
        ],
    },
]


def normalize_text(text):
    lowered = str(text).lower()
    lowered = lowered.replace("&", " and ")
    cleaned = re.sub(r"[^a-z0-9]+", " ", lowered)
    return re.sub(r"\s+", " ", cleaned).strip()


def tokenize(text):
    return {
        token
        for token in normalize_text(text).split()
        if token not in STOPWORDS and len(token) > 1
    }


def _keyword_hits(message_norm, keywords):
    hits = 0
    for keyword in keywords:
        keyword_norm = normalize_text(keyword)
        if len(keyword_norm) < 2:
            continue
        if " " in keyword_norm:
            if keyword_norm in message_norm:
                hits += 2
        elif keyword_norm in message_norm.split() or f" {keyword_norm} " in f" {message_norm} ":
            hits += 1
    return hits


def _faq_confidence(message, faq):
    message_norm = normalize_text(message)
    question_norm = normalize_text(faq["question"])
    category_norm = normalize_text(faq.get("category", ""))

    question_ratio = SequenceMatcher(None, message_norm, question_norm).ratio()
    category_ratio = SequenceMatcher(None, message_norm, category_norm).ratio()
    message_tokens = tokenize(message)
    faq_tokens = tokenize(faq["question"]) | tokenize(" ".join(faq.get("keywords", [])))
    overlap = (
        len(message_tokens & faq_tokens) / len(message_tokens) if message_tokens else 0.0
    )
    hits = _keyword_hits(message_norm, faq.get("keywords", []))
    keyword_score = min(hits * 0.18, 0.72)

    score = (
        (question_ratio * 0.38)
        + (overlap * 0.28)
        + keyword_score
        + (category_ratio * 0.04)
    )

    if hits == 0 and question_ratio < 0.62:
        return 0.0

    return min(score, 1.0)


def _demo_match(message):
    message_norm = normalize_text(message)
    demo_intent = any(
        phrase in message_norm
        for phrase in (
            "demo",
            "video",
            "youtube",
            "in action",
            "watch",
        )
    )
    if not demo_intent:
        return None

    wants_premium = any(
        phrase in message_norm for phrase in ("premium", "automatic")
    )
    wants_popular = any(
        phrase in message_norm for phrase in ("popular", "manual")
    )
    wants_twin = any(
        phrase in message_norm for phrase in ("twin", "bulk", "community", "apartment")
    )

    if wants_premium and not wants_popular and not wants_twin:
        return {
            "id": "demo_premium",
            "question": "Show me the Premium demo",
            "answer": f"Here is the DOSTBin Premium demo:\n{PREMIUM_DEMO_URL}",
            "category": "Getting Started & Purchase",
            "score": 1.0,
        }
    if wants_popular and not wants_premium and not wants_twin:
        return {
            "id": "demo_popular",
            "question": "Show me the Popular demo",
            "answer": f"Here is the DOSTBin Popular demo:\n{POPULAR_DEMO_URL}",
            "category": "Getting Started & Purchase",
            "score": 1.0,
        }
    if wants_twin and not wants_premium and not wants_popular:
        return {
            "id": "demo_twin",
            "question": "Show me the Twin Composter demo",
            "answer": f"Here is the DOSTBin Twin Composter demo:\n{TWIN_DEMO_URL}",
            "category": "Getting Started & Purchase",
            "score": 1.0,
        }

    return {
        "id": "demo_all",
        "question": "Where can I see it in action?",
        "answer": (
            "Here are the DOSTBin demo videos:\n"
            f"DOSTBin Premium Demo: {PREMIUM_DEMO_URL}\n"
            f"DOSTBin Popular Demo: {POPULAR_DEMO_URL}\n"
            f"DOSTBin Twin Composter Demo: {TWIN_DEMO_URL}"
        ),
        "category": "Getting Started & Purchase",
        "score": 0.95,
    }


def find_faq_answer(message):
    if not isinstance(message, str) or not message.strip():
        return None

    demo = _demo_match(message)
    if demo:
        return demo

    best = None
    best_score = 0.0
    for faq in APPROVED_FAQS:
        score = _faq_confidence(message, faq)
        if score > best_score:
            best_score = score
            best = faq

    if not best or best_score < MIN_FAQ_CONFIDENCE:
        return None

    return {
        "id": best["id"],
        "question": best["question"],
        "answer": best["answer"],
        "category": best["category"],
        "score": round(best_score, 4),
    }
