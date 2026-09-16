import json
import os
import re
from functools import lru_cache

from joblib import load
from sklearn.metrics.pairwise import cosine_similarity


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTORSTORE_DIR = os.path.join(BASE_DIR, "vectorstore")
INDEX_FILE = os.path.join(VECTORSTORE_DIR, "tfidf_index.joblib")
METADATA_FILE = os.path.join(VECTORSTORE_DIR, "metadata.json")

DEFAULT_TOP_K = 3
MIN_SIMILARITY_SCORE = 0.08
LEXICAL_WEIGHT = 0.6
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
    "inside",
    "is",
    "it",
    "its",
    "much",
    "my",
    "of",
    "on",
    "or",
    "the",
    "things",
    "to",
    "what",
    "which",
    "with",
    "dostbin",
}


@lru_cache(maxsize=1)
def get_index():
    if not os.path.exists(INDEX_FILE):
        raise FileNotFoundError(
            f"TF-IDF index not found at {INDEX_FILE}. Run backend/build_index.py first."
        )

    payload = load(INDEX_FILE)
    if not isinstance(payload, dict) or "vectorizer" not in payload or "matrix" not in payload:
        raise ValueError("TF-IDF index is invalid. Rebuild it with backend/build_index.py.")

    return payload


@lru_cache(maxsize=1)
def get_metadata():
    if not os.path.exists(METADATA_FILE):
        raise FileNotFoundError(
            f"Metadata not found at {METADATA_FILE}. Run backend/build_index.py first."
        )

    with open(METADATA_FILE, "r", encoding="utf-8") as file:
        metadata = json.load(file)

    if isinstance(metadata, list):
        return {
            "faqs": metadata,
            "index_records": [
                {
                    "faq_index": index,
                    "faq_id": faq.get("id"),
                    "representation": "legacy",
                }
                for index, faq in enumerate(metadata)
            ],
        }

    if not isinstance(metadata, dict):
        raise ValueError("Vectorstore metadata must be an object.")

    if not isinstance(metadata.get("faqs"), list):
        raise ValueError("Vectorstore metadata field 'faqs' must be a list.")

    return metadata


def tokenize(text):
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if token not in STOPWORDS and len(token) > 1
    }


def lexical_score(query, faq):
    query_tokens = tokenize(query)
    if not query_tokens:
        return 0.0

    question_tokens = tokenize(faq.get("question", ""))
    keyword_text = " ".join(faq.get("keywords", []))
    keyword_tokens = tokenize(keyword_text)
    category_tokens = tokenize(faq.get("category", ""))

    question_overlap = len(query_tokens & question_tokens) / len(query_tokens)
    keyword_overlap = len(query_tokens & keyword_tokens) / len(query_tokens)
    category_overlap = len(query_tokens & category_tokens) / len(query_tokens)

    query_lower = query.lower()
    phrase_hits = sum(
        1
        for keyword in faq.get("keywords", [])
        if len(keyword) > 2 and keyword.lower() in query_lower
    )
    phrase_bonus = min(phrase_hits * 0.25, 0.5)

    return min(
        (question_overlap * 0.35)
        + (keyword_overlap * 0.5)
        + (category_overlap * 0.05)
        + phrase_bonus,
        1.0,
    )


def search_faqs(query, top_k=DEFAULT_TOP_K):
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query must be a non-empty string.")

    index = get_index()
    metadata = get_metadata()
    faqs = metadata["faqs"]
    vectorizer = index["vectorizer"]
    matrix = index["matrix"]

    if matrix.shape[0] != len(faqs):
        raise ValueError("TF-IDF index does not match FAQ metadata. Rebuild the index.")

    query_vector = vectorizer.transform([query.strip()])
    similarities = cosine_similarity(query_vector, matrix).ravel()

    requested_top_k = max(int(top_k), 1)
    ranked_matches = []

    for faq_index, faq in enumerate(faqs):
        similarity = float(similarities[faq_index])
        lexical = lexical_score(query, faq)

        if similarity < MIN_SIMILARITY_SCORE and lexical <= 0:
            continue

        ranked_matches.append(
            {
                "faq": faq,
                "similarity_score": similarity,
                "lexical_score": lexical,
                "ranking_score": similarity + (lexical * LEXICAL_WEIGHT),
            }
        )

    ranked_matches.sort(key=lambda item: item["ranking_score"], reverse=True)

    results = []
    for match in ranked_matches[:requested_top_k]:
        ranked_faq = dict(match["faq"])
        ranked_faq["similarity_score"] = match["similarity_score"]
        ranked_faq["lexical_score"] = match["lexical_score"]
        ranked_faq["ranking_score"] = match["ranking_score"]
        ranked_faq["matched_representation"] = "tfidf"
        results.append(ranked_faq)

    return results
