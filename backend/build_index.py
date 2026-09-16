import json
import os

from joblib import dump
from sklearn.feature_extraction.text import TfidfVectorizer


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FAQ_FILE = os.path.join(BASE_DIR, "data", "dostbin_faq.json")
VECTORSTORE_DIR = os.path.join(BASE_DIR, "vectorstore")
INDEX_FILE = os.path.join(VECTORSTORE_DIR, "tfidf_index.joblib")
METADATA_FILE = os.path.join(VECTORSTORE_DIR, "metadata.json")
REQUIRED_FIELDS = ("category", "question", "answer", "keywords")
INDEX_SCHEMA_VERSION = 3


def load_faqs():
    print("Loading DOSTBin FAQ data...")

    with open(FAQ_FILE, "r", encoding="utf-8") as file:
        faqs = json.load(file)

    validate_faqs(faqs)
    print(f"Loaded {len(faqs)} FAQ entries.")
    return faqs


def validate_faqs(faqs):
    if not isinstance(faqs, list):
        raise ValueError("FAQ data must be a list of entries.")

    for index, faq in enumerate(faqs):
        if not isinstance(faq, dict):
            raise ValueError(f"FAQ entry {index} must be an object.")

        missing_fields = [field for field in REQUIRED_FIELDS if field not in faq]
        if missing_fields:
            raise ValueError(
                f"FAQ entry {index} is missing required fields: "
                f"{', '.join(missing_fields)}"
            )

        if not isinstance(faq["keywords"], list):
            raise ValueError(f"FAQ entry {index} field 'keywords' must be a list.")


def faq_search_text(faq):
    keywords = " ".join(faq.get("keywords", []))
    question = faq.get("question", "")
    answer = faq.get("answer", "")
    category = faq.get("category", "")

    return "\n".join(
        [
            f"Question: {question}",
            f"Question: {question}",
            f"Keywords: {keywords}",
            f"Keywords: {keywords}",
            f"Category: {category}",
            f"Answer: {answer}",
        ]
    ).strip()


def build_index():
    faqs = load_faqs()
    documents = [faq_search_text(faq) for faq in faqs]

    print("\nBuilding TF-IDF index...")
    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=1,
        token_pattern=r"(?u)\b[a-zA-Z0-9]+\b",
    )
    matrix = vectorizer.fit_transform(documents)
    print(f"TF-IDF matrix shape: {matrix.shape}")

    os.makedirs(VECTORSTORE_DIR, exist_ok=True)

    dump(
        {
            "schema_version": INDEX_SCHEMA_VERSION,
            "vectorizer": vectorizer,
            "matrix": matrix,
        },
        INDEX_FILE,
    )

    metadata = {
        "schema_version": INDEX_SCHEMA_VERSION,
        "retrieval": "tfidf",
        "faqs": faqs,
        "index_records": [
            {
                "faq_index": index,
                "faq_id": faq.get("id"),
                "representation": "tfidf",
            }
            for index, faq in enumerate(faqs)
        ],
    }

    with open(METADATA_FILE, "w", encoding="utf-8") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=2)

    print("\n----------------------------------------")
    print("DOSTBin TF-IDF index created!")
    print("----------------------------------------")
    print(f"Index:    {INDEX_FILE}")
    print(f"Metadata: {METADATA_FILE}")
    print(f"FAQs:     {len(faqs)}")


if __name__ == "__main__":
    build_index()
