#!/bin/bash
# Move to the live_scraper directory regardless of where you call it from
cd "$(dirname "$0")"

echo "=== Starting Greek News Live Scraper ==="

# 1. Clean the old raw JSON container so it doesn't inflate forever
rm -f raw_news.jsonl

# 2. Run the Scrapy spider (appends output to raw_news.jsonl)
# -O overwrites the file cleanly
echo "Scraping new articles..."
../venv/bin/scrapy runspider live_news_spider.py -O raw_news.jsonl

# 3. Clean the HTML out and append to kafka_feed.jsonl
echo "Cleaning HTML and extracting valid rows..."
../venv/bin/python3 live_cleaner.py

echo "=== Pipeline finished! ==="
