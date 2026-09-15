import json
import os
import re
from functools import lru_cache

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTORSTORE_DIR = os.path.join(BASE_DIR, "vectorstore")
INDEX_FILE = os.path.join(VECTORSTORE_DIR, "dostbin_faq.index")
METADATA_FILE = os.path.join(VECTORSTORE_DIR, "metadata.json")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

DEFAULT_TOP_K = 3
MIN_SIMILARITY_SCORE = 0.15
LEXICAL_WEIGHT = 0.45
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
def get_embedding_model():
    try:
        return SentenceTransformer(EMBEDDING_MODEL, local_files_only=True)
    except OSError:
        return SentenceTransformer(EMBEDDING_MODEL)


@lru_cache(maxsize=1)
def get_index():
    if not os.path.exists(INDEX_FILE):
        raise FileNotFoundError(
            f"FAISS index not found at {INDEX_FILE}. Run backend/build_index.py first."
        )

    return faiss.read_index(INDEX_FILE)


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

    if not isinstance(metadata.get("index_records"), list):
        raise ValueError("Vectorstore metadata field 'index_records' must be a list.")

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
    index_records = metadata["index_records"]
    model = get_embedding_model()

    query_embedding = model.encode(
        [query.strip()],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    query_embedding = np.asarray(query_embedding, dtype="float32")

    requested_top_k = max(int(top_k), 1)
    search_k = min(index.ntotal, max(requested_top_k * 8, requested_top_k))
    scores, indices = index.search(query_embedding, search_k)

    matches_by_faq = {}
    for score, record_index in zip(scores[0], indices[0]):
        if record_index < 0 or record_index >= len(index_records):
            continue

        index_record = index_records[record_index]
        faq_index = index_record["faq_index"]
        if faq_index < 0 or faq_index >= len(faqs):
            continue

        current_match = matches_by_faq.get(faq_index)
        if current_match is None or score > current_match["similarity_score"]:
            faq = faqs[faq_index]
            lexical = lexical_score(query, faq)
            matches_by_faq[faq_index] = {
                "similarity_score": float(score),
                "lexical_score": lexical,
                "ranking_score": float(score) + (lexical * LEXICAL_WEIGHT),
                "matched_representation": index_record.get("representation"),
            }

    ranked_matches = sorted(
        matches_by_faq.items(),
        key=lambda item: item[1]["ranking_score"],
        reverse=True,
    )

    results = []
    for faq_index, match in ranked_matches:
        if match["similarity_score"] < MIN_SIMILARITY_SCORE and match["lexical_score"] <= 0:
            continue

        faq = dict(faqs[faq_index])
        faq["similarity_score"] = match["similarity_score"]
        faq["lexical_score"] = match["lexical_score"]
        faq["ranking_score"] = match["ranking_score"]
        faq["matched_representation"] = match["matched_representation"]
        results.append(faq)

        if len(results) >= requested_top_k:
            break

    return results
