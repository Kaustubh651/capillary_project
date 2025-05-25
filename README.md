# Promo Sensei

Smart Slack-based assistant for real-time e-commerce promotion discovery, built with dynamic web scraping, a vector database, and an LLM/RAG pipeline.

## 🔍 Overview

Promo Sensei scrapes promotional offers from major e-commerce sites, ingests them into a Chroma/FAISS vector store, and answers user queries in Slack via retrieval-augmented generation.

## 🛠️ Components

1. **Web Scraper** (`new_scrapper.py`)  
   - Targets: Nykaa, Flipkart, Puma, Myntra  
   - Extracts title, description, expiry, brand, link, discount, image, category, channel

2. **Ingestion** (`ingest_offers_chroma3.py`)  
   - Reads `master_offers.json` (output of scraper)  
   - Computes SBERT embeddings (`all-MiniLM-L6-v2`)  
   - Stores IDs, docs, metadata, embeddings in `./chroma_db`

3. **RAG + LLM Query** (`rag2.py`)  
   - Retrieves top-K via ChromaDB  
   - Builds a prompt template  
   - Generates natural replies with Flan-T5 (`google/flan-t5-small`)

4. **Slack Bot** (`slack.py`)  
   - Slash commands:  
     - `/promosensei search [query]`  
     - `/promosensei summary`  
     - `/promosensei brand [brand_name]`  
     - `/promosensei refresh`  
   - Orchestrates scraper → ingestion → query pipeline

## 📁 Repository Structure
   .
   ├── README.md
   ├── docs/
   │ └── screenshots/
   │ ├── search-example.png ← place your demo screenshots here
   │ └── summary-example.png
   ├── master_offers.json ← combined JSON of scraped offers
   ├── chroma_db/ ← your persistent vector store
   ├── new_scrapper.py
   ├── ingest_offers_chroma3.py
   ├── rag2.py
   └── slack.py



