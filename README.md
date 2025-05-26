# Capillary Offer Intelligence Project

This project scrapes offers from different sources, stores them in a vector database using embeddings, and enables querying via a Retrieval-Augmented Generation (RAG) system. A Slackbot interface is also included to interact with the data easily.

---

## 📁 Project Structure

- `scraper.py` – Scrapes offers from various websites and stores them in `Master_offer.json`.
- `ingest_to_vector_db.py` – Ingests the scraped data into a Chroma vector database.
- `rag_query.py` – Enables querying using RAG-based search.
- `slackbot.py` – Connects the query system with Slack to interact with users.
- `Master_offer.json` – Stores all the scraped data.
- `Chroma_db/` – Vector database created using the Chroma library.
- `Scraping demo` – Used to verify scraping from different websites.
- `Chromedriver` – Required for automated browsing (ensure it matches your Chrome version).
- `requirements.txt` – Lists all required Python packages.
- `docs/screenshots/` – Contains UI and CLI screenshots of different parts of the system.

---

## 🛠️ Setup Instructions

1. **Unzip the archive**
2. *(Optional)* Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Quickstart

Run the following in order:

```bash
python scraper.py
python ingest_to_vector_db.py
python rag_query.py
python slackbot.py
```
To run the slackbot open this link -https://drive.google.com/file/d/1Ez9SONcHAwHGdFIn0HXfwfZwwHK1ooCN/view?usp=drive_link
---

## 💬 Sample Queries & Outputs

Refer to the `docs/screenshots/` folder for:

- Slackbot interaction demo (`slack-search-demo.png`)
- Ingestion console logs (`ingestion-console.png`)
- CLI query demo (`rag-cli-demo.png`)

---

## 🔐 Notes

- All Slack API and secret keys are embedded in the respective code files. Ensure you manage them securely in production environments using `.env` files or secrets managers.

---

## 🧠 Key Design Decisions

- Used ChromaDB for efficient vector-based retrieval.
- Modular Python scripts allow separate execution and testing.
- Slackbot enables real-time, user-friendly query interface.
- JSON used for portability of scraped data.

---

## 📌 Requirements

See `requirements.txt` for full dependency list.

---

## 📸 Screenshots

Find all screenshots in the `docs`
https://docs.google.com/document/d/1Cx2yfGv_y6BQ5ohz0C4HtWHL8TaLr69d/edit?usp=drive_link&ouid=106402010391681913529&rtpof=true&sd=true

---

## 🙌 Acknowledgments

This assignment was prepared as part of Capillary’s technical evaluation process.

---
