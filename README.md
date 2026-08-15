# Daily News Digest

A news-outlet-style dashboard built with **vibe coding** (Claude Code + Streamlit) for the
Mastering Agentic AI Bootcamp — Week 1 Project (Path B).

**Live app:** https://daily-news-digest-aug2026.streamlit.app

## Idea

Pull recent articles from free public RSS feeds plus arXiv, and surface them as an interactive,
news-outlet-styled dashboard: topic filters, keyword/source/timeline charts, a market snapshot,
and a browsable article feed — split into two clearly separate areas, **News** and
**Research Papers**, so day-to-day headlines never get mixed in with academic papers.

## Layout

- **📊 Overview** — cross-cutting stats across everything (most active topic/source, articles
  by area, top sources, keyword chart, activity timeline, latest headlines).
- **📰 News** — sub-tabs for **Technology** (grouping Tech / AI / Software Engineering / Cloud,
  each browsable individually or combined), **World**, **Sports**, **Finance** (includes a
  live **Market Snapshot** — S&P 500, Nasdaq, Bitcoin), and **Science**.
- **📄 Research Papers** — a fully separate top-level area. Papers pulled from arXiv (cs.AI),
  broken down by field (NLP, Machine Learning, Computer Vision, Robotics, ...) derived from
  each paper's own category tags, each field browsable on its own tab.

## Data sources

- **News**: free public RSS feeds (no API key), fetched with `feedparser` and cached to
  `data/news.csv`. Sources: TechCrunch, Ars Technica, MIT Tech Review, AI News, InfoQ,
  Hacker News, AWS/GCP/Azure blogs, BBC, Reuters, ESPN, CNBC, NASA — see `scripts/fetch_news.py`.
- **Research papers**: arXiv's `cs.AI` RSS feed (per-category feeds like `cs.LG`/`cs.CL` are
  frequently empty on arXiv's side, so we fetch the reliable `cs.AI` feed and classify each
  paper's field from its own category tags instead).
- **Market snapshot**: live via `yfinance` (Yahoo Finance), cached in-app for 1 hour — not part
  of the daily CSV refresh, since prices move faster than daily news.

## Color theme

Charts use a validated, colorblind-safe categorical palette (checked with the `dataviz` skill's
`validate_palette.js` — CVD ΔE and contrast gates, adjacency order kept fixed per chart via
`category_orders`):

| Area | Slot 1 (blue) | Slot 2 (orange) | Slot 3 (aqua) | Slot 4 (yellow) | Slot 5 (magenta) | Slot 6 (green) | Slot 7 (violet) |
|---|---|---|---|---|---|---|---|
| **Top-level** | Technology | World | Sports | Finance | Science | Research Papers | — |
| **Tech sub-topics** | Tech | AI | Software Engineering | Cloud | — | — | — |
| **Research fields** | General AI | NLP | Machine Learning | Computer Vision | AI & Society | Robotics | Neural/Evolutionary |
| **Market snapshot** | S&P 500 | Nasdaq | Bitcoin | — | — | — | — |

Single-hue charts (top sources, keyword frequency, activity timeline) use slot 1 (blue) as a
magnitude ramp rather than a categorical palette, per the "one hue for ranking" rule.

## Stack

- **Streamlit** — UI
- **pandas** — data wrangling
- **feedparser** — RSS/arXiv ingestion
- **plotly** — charts
- **yfinance** — market snapshot
- Claude (via Claude Code) — AI-assisted build

## Project structure

```
daily-news-digest/
├── app.py                          # Streamlit app
├── scripts/
│   └── fetch_news.py               # pulls RSS + arXiv feeds -> data/news.csv
├── data/
│   └── news.csv                    # cached article dataset
├── .github/workflows/
│   └── refresh-news.yml            # daily scheduled refresh (GitHub Actions)
├── requirements.txt
├── LICENSE
└── README.md
```

## Running it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# (optional) refresh data/news.csv with the latest RSS + arXiv articles
python scripts/fetch_news.py

streamlit run app.py
```

The app loads `data/news.csv` by default. You can also upload your own CSV
(same columns: `title, source, topic, subtopic, published, summary, url`) from the
sidebar to explore a different dataset without touching the code.

## Keeping data fresh

`.github/workflows/refresh-news.yml` runs `scripts/fetch_news.py` daily (07:00 UTC) and
commits `data/news.csv` back to the repo if it changed — no manual step needed. Trigger it
manually anytime with `gh workflow run refresh-news.yml` or from the Actions tab.

## Updating the deployed Streamlit app

The live app at https://daily-news-digest-aug2026.streamlit.app is connected to this GitHub
repo. Streamlit Community Cloud watches the `master` branch and **auto-redeploys within a
minute or two of any push** — including the daily auto-refresh commit from the GitHub Actions
workflow above. To update it yourself:

1. Make your changes locally, commit, and `git push`.
2. That's it — Streamlit Cloud picks up the new commit and redeploys automatically.

If it ever gets stuck: go to [share.streamlit.io](https://share.streamlit.io) → open the app →
the **⋮** menu → **Reboot app** to force a fresh redeploy.

## License & citation

MIT licensed — see [LICENSE](LICENSE). You're free to use, modify, and redistribute this
project (including commercially), as long as the copyright notice and license text are kept
with any copy. If you build on this project or reference it, a credit/link back is appreciated:

> Daily News Digest — Cibaca Khandelwal ([@cibaca](https://github.com/cibaca)) —
> https://github.com/cibaca/daily-news-digest

## Status

- [x] Idea locked, repo scaffolded
- [x] RSS + arXiv fetch script, daily auto-refresh via GitHub Actions
- [x] Streamlit UI: News / Research Papers split, topic filters, search, CSV upload
- [x] Market snapshot (S&P 500 / Nasdaq / Bitcoin)
- [x] Validated color theme, news-outlet visual style
- [x] Deployed to Streamlit Community Cloud
- [x] MIT license
- [ ] Screenshots + video demo
- [ ] Project documentation (Google Doc)

## Course deliverables

Built for the Mastering Agentic AI Bootcamp, Week 1 Project — deadline Aug 16, 2026, 11:59pm PT.
