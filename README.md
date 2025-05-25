Below is a comprehensive **README.md** you can drop into the root of your project. It’s tailored to your files and leaves placeholders for demo screenshots under `docs/screenshots/`. Right after that, you’ll find a step-by-step on how to turn your local folder into a GitHub repo and push your code up.

---

```markdown
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

```

.
├── README.md
├── docs/
│   └── screenshots/
│       ├── search-example.png   ← place your demo screenshots here
│       └── summary-example.png
├── master\_offers.json          ← combined JSON of scraped offers
├── chroma\_db/                  ← your persistent vector store
├── new\_scrapper.py
├── ingest\_offers\_chroma3.py
├── rag2.py
└── slack.py

````

## 🚀 Quickstart

### 1. Prerequisites

- Python 3.8+  
- ChromeDriver in `PATH` (for Selenium/uc)  
- A Slack workspace and a registered Slack App with bot scopes (`commands`, `chat:write`)  
- (Optional) Virtual environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
````

### 2. Scrape & Ingest

```bash
python new_scrapper.py
python ingest_offers_chroma3.py
```

### 3. Run & Test RAG CLI

```bash
python rag2.py
> Any flat 50% off deals today?
```

### 4. Launch Slack Bot

1. In `slack.py`, set your `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `SLACK_SIGNING_SECRET`.

2. Run:

   ```bash
   python slack.py
   ```

3. In your workspace, type:

   ```
   /promosensei search flat 30% off Puma
   ```

## 🎥 Demo

<div align="center">
  <img src="docs/screenshots/search-example.png" alt="Search example" width="400"/>
  <img src="docs/screenshots/summary-example.png" alt="Summary example" width="400"/>
</div>

> **Tip:** Replace the above with your actual screenshots.

## 🔑 Key Design Decisions

* **ChromaDB** with SBERT embeddings for sub-second retrieval and lower token usage
* **Flan-T5** deployed locally for privacy & cost control
* **Modular pipeline**: scraper → ingest → query → Slack interface

## ✍️ Contributing

1. Fork this repo
2. Create a feature branch: `git checkout -b feature/awesome`
3. Commit your changes: `git commit -m "Add awesome feature"`
4. Push to your branch: `git push origin feature/awesome`
5. Open a Pull Request

## 📄 License

MIT © Your Name

````

---

## 🚩 Turning your folder into a GitHub repo

1. **Initialize** (in your project root):
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Promo Sensei end-to-end pipeline"
````

2. **Create a GitHub repo**

   * Go to [https://github.com/new](https://github.com/new)
   * Give it a name (e.g. `promo-sensei`) and optional description
   * Leave it **empty** (no README/LICENSE)

3. **Add remote & push**:

   ```bash
   git remote add origin git@github.com:<your-username>/promo-sensei.git
   git branch -M main
   git push -u origin main
   ```

Now your code, README, and project structure will live on GitHub. Feel free to ask if you need help with GitHub Actions, CI/CD, or any other tweaks!
