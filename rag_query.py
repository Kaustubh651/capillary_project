#!/usr/bin/env python3
import json
from pathlib import Path

from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings, DEFAULT_TENANT, DEFAULT_DATABASE
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

# ─── Configuration ─────────────────────────────────────────────────────────────
OFFERS_PATH     = Path("master_offers2.json")
EMBED_MODEL     = "all-MiniLM-L6-v2"
GEN_MODEL       = "google/flan-t5-small"
CHROMA_DB_DIR   = "./chroma_db"

# ─── LiveRAG Class ─────────────────────────────────────────────────────────────
class LiveRAG:
    def __init__(self):
        # 1. Semantic embedder
        self.embedder = SentenceTransformer(EMBED_MODEL, device="cpu")

        # 2. Local generator (Flan-T5) with beam + repetition penalty
        tokenizer = AutoTokenizer.from_pretrained(GEN_MODEL)
        model     = AutoModelForSeq2SeqLM.from_pretrained(GEN_MODEL)
        self.generator = pipeline(
            "text2text-generation",
            model=model,
            tokenizer=tokenizer,
            device=-1,
            max_length=256,
            num_beams=4,
            repetition_penalty=1.2,
            early_stopping=True,
        )

        # 3. ChromaDB
        client = chromadb.PersistentClient(
            path=CHROMA_DB_DIR,
            settings=Settings(),
            tenant=DEFAULT_TENANT,
            database=DEFAULT_DATABASE,
        )
        self.col = client.get_or_create_collection("promo_offers")

        # 4. Track ingested IDs
        self.seen_ids = set()

        # 5. How many to include in prompt
        self.TOP_K = 3

        # 6. One-time ingest at startup
        self._update_index()

    def _update_index(self):
        if not OFFERS_PATH.exists():
            return

        offers = json.loads(OFFERS_PATH.read_text(encoding="utf-8"))
        new_ids, docs, metas = [], [], []

        for o in offers:
            link = o.get("link")
            if not link or link in self.seen_ids:
                continue
            self.seen_ids.add(link)
            new_ids.append(link)
            docs.append(f"{o.get('title','')}. {o.get('description','')}")
            metas.append({
                "brand":    o.get("brand",""),
                "expiry":   o.get("expiry",""),
                "link":     link,
                "category": o.get("category",""),
                "discount": str(o.get("discount","")),
                "image":    o.get("image",""),
                "channel":  o.get("channel",""),
            })

        if not new_ids:
            return  # nothing new

        print(f"[LiveRAG] Embedding {len(docs)} new offers…")
        embs = self.embedder.encode(docs, show_progress_bar=False).tolist()
        self.col.add(
            ids=new_ids,
            documents=docs,
            metadatas=metas,
            embeddings=embs
        )
        print(f"[LiveRAG] Added {len(new_ids)} offers.")

    def _retrieve(self, query: str):
        q_emb = self.embedder.encode(query).tolist()
        res   = self.col.query(query_embeddings=[q_emb], n_results=self.TOP_K)
        return list(zip(res["documents"][0], res["metadatas"][0]))

    def _build_prompt(self, retrieved, question: str) -> str:
        lines = [
            "You are PromoSensei, a smart assistant that finds and summarizes e-commerce promotions.",
            "Here are some relevant offers (truncated to 100 chars each):"
        ]
        for i, (doc, md) in enumerate(retrieved, 1):
            snippet = doc.replace("\n"," ")[:100].rstrip()
            if len(doc) > 100:
                snippet += "…"
            lines.append(f"{i}. {snippet}")
            lines.append(
                f"   • Brand: {md['brand']}; Discount: {md.get('discount','N/A')}; Expiry: {md.get('expiry','N/A')}"
            )
        lines.append(f"\nUser asked: {question[:200]}")
        lines.append("Please answer concisely and in a friendly tone, referencing the offers above.")
        return "\n".join(lines)

    def answer(self, question: str) -> str:
        retrieved = self._retrieve(question)
        if not retrieved:
            return "Sorry, I couldn't find any relevant offers right now."
        prompt = self._build_prompt(retrieved, question)
        out    = self.generator(prompt)[0]["generated_text"]
        return out.strip()


# ─── Singleton & module‐level helper ────────────────────────────────────────────
# Instantiate once and reuse for Slack
_rag = LiveRAG()

def answer_query(question: str) -> str:
    """
    Thin wrapper around our singleton LiveRAG.  
    Slack app does: `from rag2 import answer_query`
    """
    return _rag.answer(question)


# ─── CLI Test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("LiveRAG ready. Type a query or 'exit'.")
    while True:
        q = input("> ").strip()
        if not q or q.lower() in ("exit", "quit"):
            break
        print("\n" + answer_query(q) + "\n")
