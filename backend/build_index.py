import json
import os

import faiss
from sentence_transformers import SentenceTransformer


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FAQ_FILE = os.path.join(BASE_DIR, "data", "dostbin_faq.json")
VECTORSTORE_DIR = os.path.join(BASE_DIR, "vectorstore")
INDEX_FILE = os.path.join(VECTORSTORE_DIR, "dostbin_faq.index")
METADATA_FILE = os.path.join(VECTORSTORE_DIR, "metadata.json")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
REQUIRED_FIELDS = ("category", "question", "answer", "keywords")
INDEX_SCHEMA_VERSION = 2


def load_embedding_model():
    try:
        return SentenceTransformer(EMBEDDING_MODEL, local_files_only=True)
    except OSError:
        return SentenceTransformer(EMBEDDING_MODEL)


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


def create_search_records(faqs):
    records = []

    for faq_index, faq in enumerate(faqs):
        keywords = ", ".join(faq.get("keywords", []))

        intent_text = f"""
Category: {faq['category']}

Question: {faq['question']}
Question: {faq['question']}
Question: {faq['question']}

Keywords: {keywords}
Keywords: {keywords}
Keywords: {keywords}
"""

        keyword_text = f"""
Category: {faq['category']}

Keywords: {keywords}
Keywords: {keywords}
Keywords: {keywords}
Keywords: {keywords}

Question: {faq['question']}
"""

        full_text = f"""
Category: {faq['category']}

Question: {faq['question']}
Question: {faq['question']}

Keywords: {keywords}
Keywords: {keywords}

Answer: {faq['answer']}
"""

        for representation, text in (
            ("intent", intent_text),
            ("keywords", keyword_text),
            ("full", full_text),
        ):
            records.append(
                {
                    "faq_index": faq_index,
                    "faq_id": faq.get("id"),
                    "representation": representation,
                    "text": text.strip(),
                }
            )

    return records


def build_index():
    faqs = load_faqs()
    search_records = create_search_records(faqs)
    documents = [record["text"] for record in search_records]

    print("\nLoading embedding model...")
    model = load_embedding_model()
    print("Embedding model loaded.")

    print("\nCreating embeddings...")
    embeddings = model.encode(
        documents,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    )
    print(f"Created embeddings with shape: {embeddings.shape}")

    os.makedirs(VECTORSTORE_DIR, exist_ok=True)

    print("\nBuilding FAISS index...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    print(f"FAISS index contains {index.ntotal} documents.")

    faiss.write_index(index, INDEX_FILE)

    metadata = {
        "schema_version": INDEX_SCHEMA_VERSION,
        "faqs": faqs,
        "index_records": [
            {
                "faq_index": record["faq_index"],
                "faq_id": record["faq_id"],
                "representation": record["representation"],
            }
            for record in search_records
        ],
    }

    with open(METADATA_FILE, "w", encoding="utf-8") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=2)

    print("\n----------------------------------------")
    print("DOSTBin vector database created!")
    print("----------------------------------------")
    print(f"Index:    {INDEX_FILE}")
    print(f"Metadata: {METADATA_FILE}")
    print(f"FAQs:     {len(faqs)}")
    print(f"Vectors:  {len(search_records)}")


if __name__ == "__main__":
    build_index()
