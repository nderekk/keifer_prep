# HellenicInsight

> Real-time Greek news bias analysis — powered by a fine-tuned Qwen model with LoRA adapters, streaming through Kafka and Spark into a live React dashboard.

---

## Overview

HellenicInsight is an end-to-end platform that continuously scrapes Greek news articles, classifies their political bias using a fine-tuned Qwen LLM, and surfaces the results on a live frontend dashboard.

Each article is classified with:

| Field | Description |
|---|---|
| **bias** | Float 0–1 (mapped to Left / Center / Right) |
| **reasoning** | The model's plain-language explanation of its bias assessment |
| **primary_entities** | Key political entities mentioned in the article |

---

## Architecture

```
  Live Scraping                Streaming              Inference & Storage
  ─────────────────────────────────────────────────────────────────────────

       Site1.gr ──┐
                  │
                  │
       ........   ├──▶  Scrapy Spider  ──▶  Cleaner  ──▶  Kafka
                  │     (live_scraper/)               (raw-articles)
                  │                                          │
       SiteN.gr ──┘                                         ▼
                                                    Spark Structured
                                                      Streaming
                                                            │
                                                            ▼
                                                    Qwen + LoRA
                                                    (bias inference)
                                                            │
                                                            ▼
                                                        MongoDB
                                                            │
                                                            ▼
                                                  Express REST API
                                                    (backend/)
                                                            │
                                                            ▼
                                                  React Dashboard
                                                    (frontend/)
```

The backend also orchestrates the scraping pipeline automatically via a cron job that runs every hour.

---

## Project Structure

```
keifer_prep/
│
├── live_scraper/
│   ├── live_news_spider.py     # Scrapy SitemapSpider — Protothema & Iefimerida
│   ├── live_cleaner.py         # Cleans and filters scraped articles
│   ├── kafka_feed.jsonl        # Cleaned output, ready for Kafka producer
│   └── last_scraped_time.txt   # State file — tracks last successful scrape
│
├── backend/
│   ├── server.js               # Express API + hourly cron pipeline orchestrator
│   ├── producer.py             # Kafka producer — publishes kafka_feed.jsonl to raw-articles
│   ├── spark_processor.py      # Spark Structured Streaming — Kafka → inference → MongoDB
│   ├── controllers/            # Article controller
│   ├── models/                 # Mongoose article model
│   ├── routes/                 # API routes
│   └── config/db.js            # MongoDB connection
│
├── frontend/
│   ├── src/App.tsx             # Main dashboard — live feed, bias meter, reasoning log
│   └── ...                     # React + Vite + Tailwind + shadcn/ui
│
├── 1st_training_dump/
│   ├── nemo_sft_train.jsonl    # NeMo SFT training split (2700 examples)
│   ├── nemo_sft_val.jsonl      # NeMo SFT validation split (300 examples)
│   ├── convert_to_nemo.ipynb   # Conversion notebook
│   └── qwen_greek_lora_final.tar.gz  # Trained LoRA adapter weights
│
├── datasets/
│   ├── final_unlabeled_dataset.json
│   ├── labeled_dataset.json / .jsonl
│   └── training/               # Training data variants
│
├── scraper/                    # Historical bulk scraper (used for dataset collection)
├── api_label.py                # Gemini 2.5 Flash labeling service (training phase)
├── docker-compose.yml          # Kafka + Kafka UI
└── requirements.txt
```

---

## Prerequisites

- Python 3.12+
- Node.js 18+
- Docker & Docker Compose
- Java 11+ (for Spark)
- MongoDB instance (local or Atlas)

---

## Steps of Execution

### Step 1 — Configure Environment Variables

Create a `.env` file in `backend/`:

```
MONGO_URI=mongodb://localhost:27017
DB_NAME=hellenic_insight
COLLECTION_NAME=articles
PORT=5000
```

---

### Step 2 — Start Kafka

```bash
docker-compose up -d
```

- Kafka broker: `localhost:9092`
- Kafka UI: `http://localhost:8080`

---

### Step 3 — Start the Spark Processor

The Spark job reads from Kafka and writes classified articles to MongoDB.

```bash
cd backend

spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.13:4.1.1,org.mongodb.spark:mongo-spark-connector_2.13:11.0.1 \
  spark_processor.py
```

---

### Step 4 — Start the Backend

```bash
cd backend
npm install
node server.js
```

The backend:
- Serves the REST API at `http://localhost:5000/api/articles`
- Runs the scrape → clean → produce pipeline automatically every hour at :45

---

### Step 5 — Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard available at `http://localhost:5173`.

---

### Manual Pipeline Run (optional)

To trigger the scraping pipeline manually without waiting for the cron:

```bash
# 1. Scrape
cd live_scraper
scrapy runspider live_news_spider.py -O raw_news.json

# 2. Clean
python live_cleaner.py

# 3. Produce to Kafka
cd ../backend
python producer.py
```

---

## Frontend Dashboard

The React dashboard:
- **Live feed** — polls `/api/articles` every 10 seconds
- **Political lean meter** — visual Left / Center / Right indicator per article
- **Reasoning log** — the model's plain-language bias explanation
- **Entity tags** — key political figures and parties detected
- **URL analysis** — paste any article URL for on-demand inference

---

## Tech Stack

| Layer | Technology |
|---|---|
| Scraping | Scrapy (SitemapSpider, incremental state) |
| Streaming | Apache Kafka |
| Processing | Apache Spark Structured Streaming |
| LLM | Qwen + LoRA fine-tuned on Greek media (NeMo SFT) |
| Labeling (training) | Google Gemini 2.5 Flash via Vertex AI |
| Storage | MongoDB |
| Backend | Node.js + Express |
| Frontend | React + Vite + Tailwind CSS + shadcn/ui |
| Infrastructure | Docker Compose |

