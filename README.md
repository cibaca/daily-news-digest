# Daily News Digest

A personal-interest news dashboard built with **vibe coding** (Claude Code + Streamlit) for the
Mastering Agentic AI Bootcamp — Week 1 Project (Path B).

## Idea

Pull recent articles from free public RSS feeds across a few topic categories (Tech, World,
Sports, Finance, ...), let the user pick which topics they care about, and surface an
interactive dashboard: filtered article feed, trending-keyword charts, articles-per-topic
breakdown, and an AI-generated daily summary blurb per selected topic.

## Data source

RSS feeds (no API key required), fetched with `feedparser` and cached to `data/news.csv`.
Example sources: BBC World, TechCrunch, ESPN, CNBC — swappable in `scripts/fetch_news.py`.

## Stack

- **Streamlit** — UI
- **pandas** — data wrangling
- **feedparser** — RSS ingestion
- **plotly** — charts
- Claude (via Claude Code) — AI-assisted build + AI-generated topic summaries in-app

## Project structure

```
daily-news-digest/
├── app.py                  # Streamlit app
├── scripts/
│   └── fetch_news.py       # pulls RSS feeds -> data/news.csv
├── data/
│   └── news.csv            # cached article dataset
├── requirements.txt
└── README.md
```

## Running it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# (optional) refresh data/news.csv with the latest RSS articles
python scripts/fetch_news.py

streamlit run app.py
```

The app loads `data/news.csv` by default. You can also upload your own CSV
(same columns: `title, source, topic, published, summary, url`) from the
sidebar to explore a different dataset without touching the code.

## Status

- [x] Idea locked, repo scaffolded
- [x] RSS fetch script
- [x] Streamlit UI (topic/source/date filters, search, CSV upload, charts, feed)
- [ ] AI-generated topic summaries
- [ ] Screenshots + video demo
- [ ] Project documentation (Google Doc)

## Course deliverables

Built for the Mastering Agentic AI Bootcamp, Week 1 Project — deadline Aug 16, 2026, 11:59pm PT.
