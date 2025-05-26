#!/usr/bin/env python3
import json
import uuid
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings, DEFAULT_TENANT, DEFAULT_DATABASE

# ─── Configuration ─────────────────────────────────────────────────────────────
_EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
_embed_model     = SentenceTransformer(_EMBED_MODEL_NAME, device="cpu")
DB_PATH          = "./chroma_db"
COLLECTION_NAME  = "promo_offers"
OFFERS_FILE      = "scrapping\master_offers.json"


def load_offers(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def to_embed_text(o: dict) -> str:
    return f"{o.get('title','')}. {o.get('description','')}"


def get_collection():
    client = chromadb.PersistentClient(
        path=DB_PATH,
        settings=Settings(),
        tenant=DEFAULT_TENANT,
        database=DEFAULT_DATABASE,
    )
    return client.get_or_create_collection(COLLECTION_NAME)


def main():
    # 1. Load scraped offers
    offers = load_offers(OFFERS_FILE)
    print(f"Loaded {len(offers)} offers from {OFFERS_FILE}")

    # 2. No dedupe—ingest all records including duplicates
    all_offers = offers
    print(f"{len(all_offers)} offers to ingest (including duplicates)")

    # 3. Connect to ChromaDB
    col = get_collection()

    # 4. Prepare docs & metadata, assign unique IDs
    ids, docs, metas = [], [], []
    for o in all_offers:
        doc_id = str(uuid.uuid4())
        ids.append(doc_id)
        docs.append(to_embed_text(o))
        metas.append({
            "brand":    o.get("brand",""),
            "expiry":   o.get("expiry",""),
            "link":     o.get("link",""),
            "category": o.get("category",""),
            "discount": str(o.get("discount","")),
            "image":    o.get("image",""),
            "channel":  o.get("channel",""),
        })

    # 5. Batch-encode
    print(f"Computing embeddings for {len(docs)} documents...")
    embeddings = _embed_model.encode(docs, show_progress_bar=True).tolist()

    # 6. Append to ChromaDB
    col.add(
        ids=ids,
        documents=docs,
        metadatas=metas,
        embeddings=embeddings
    )
    print(f"Ingested {len(ids)} offers into ChromaDB at {DB_PATH}")

    # 7. Optional test query
    test_query = "flat 50% off deals today"
    q_emb = _embed_model.encode(test_query).tolist()
    results = col.query(query_embeddings=[q_emb], n_results=5)
    print(f"\nTop 5 results for: {test_query}")
    for i, md in enumerate(results["metadatas"][0], 1):
        print(f"{i}. {md}")


if __name__ == "__main__":
    main()
