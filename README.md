# Daily News Digest

A news-outlet-style dashboard built with **vibe coding** (Claude Code + Streamlit) for the
Mastering Agentic AI Bootcamp — Week 1 Project (Path B).

**Live app:** https://daily-news-digest-aug2026.streamlit.app

## Idea

Three independently-sourced, independently-refreshed datasets, each with its own CSV and its
own top-level area in the dashboard — **News**, **Research Papers**, and **Knowledge Base** —
so day-to-day headlines, academic papers, and curated reference material never get mixed
together, filtered together, or charted together.

## Layout

- **📊 Overview** — a compiled summary across all three areas: an auto-generated stats blurb,
  items-by-area chart, top sources, keyword chart, News activity timeline, the live Market
  Snapshot, and a combined "latest across everything" feed.
- **📰 News** — sub-tabs for **Technology** (grouping Tech / AI / Software Engineering / Cloud,
  each browsable individually or combined), **World**, **Sports**, **Finance** (includes a live
  **Market Snapshot** — S&P 500, Nasdaq, Bitcoin), and **Science**. An "About these sources"
  note documents why each source is trusted.
- **📄 Research Papers** — fully separate from News. Papers from arXiv (cs.AI), classified by
  field (NLP, Machine Learning, Computer Vision, Robotics, ...) from each paper's own category
  tags, browsable per field.
- **📚 Knowledge Base** — also fully separate. Curated reference resources (books, courses,
  papers, frameworks, tools) pulled from a single controlled GitHub list, browsable by section.

## Data sources — three separate CSVs, three separate fetches

| File | Area | Source | Trust rationale |
|---|---|---|---|
| `data/news.csv` | News | Free public RSS feeds | Mainstream, editorially-staffed outlets and official vendor/agency blogs only — see below |
| `data/research_papers.csv` | Research Papers | arXiv `cs.AI` RSS | Primary source (arXiv itself); fields derived from the paper's own category tags |
| `data/knowledge_base.csv` | Knowledge Base | One curated GitHub repo | Single controlled, actively-maintained list — not an open aggregator |

**News sources**: TechCrunch, Ars Technica, MIT Tech Review, AI News, InfoQ, Hacker News,
AWS/Google Cloud/Azure blogs, BBC World, NPR World, ESPN, CNBC, NASA. All are either mainstream
editorially-staffed newsrooms or official primary-source blogs — no content farms, no
unverified aggregators. Hacker News is the one exception worth naming: it's community-curated
tech discussion, included for signal, not treated as a newsroom. (Reuters was tried and dropped
— its public RSS endpoint no longer resolves.)

**Research papers**: arXiv's per-category feeds (`cs.LG`, `cs.CL`, `cs.CV`, ...) are frequently
empty on arXiv's own infrastructure, so `scripts/fetch_data.py` fetches the reliable `cs.AI`
feed (which carries cross-listed papers too) and classifies each paper's field from its own
tags instead of relying on the broken per-category feeds.

**Knowledge base**: [`owainlewis/awesome-artificial-intelligence`](https://github.com/owainlewis/awesome-artificial-intelligence)
— an actively-maintained, quality-gated "awesome list." Chosen specifically because the source
is controlled (one maintainer, one weekly-reviewed list) rather than open/crowdsourced content.

**Market snapshot**: live via `yfinance` (Yahoo Finance), cached in-app for 1 hour — not part
of the daily CSV refresh, since prices move faster than daily news.

## Color theme

Charts use a validated, colorblind-safe categorical palette (checked with the `dataviz` skill's
`validate_palette.js` — CVD ΔE and contrast gates, adjacency order kept fixed per chart via
`category_orders`). A matching `.streamlit/config.toml` theme carries the same blue accent and
warm off-white surface into the rest of the UI (buttons, tabs, sliders) for a consistent,
professional look.

| Area | Slot 1 (blue) | Slot 2 (orange) | Slot 3 (aqua) | Slot 4 (yellow) | Slot 5 (magenta) |
|---|---|---|---|---|---|
| **News topics** | Technology | World | Sports | Finance | Science |
| **Tech sub-topics** | Tech | AI | Software Engineering | Cloud | — |
| **Research fields** | General AI | NLP | Machine Learning | Computer Vision | AI & Society (+ Robotics, Neural/Evolutionary in slots 6–7) |
| **Areas (Overview)** | News | Research Papers | Knowledge Base | — | — |
| **Market snapshot** | S&P 500 | Nasdaq | Bitcoin | — | — |

Single-hue charts (top sources, keyword frequency, Knowledge Base sections, activity timeline)
use slot 1 (blue) as a magnitude ramp rather than a categorical palette, per the "one hue for
ranking" rule — a pie chart was deliberately avoided for anything with more than a few slices.

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
├── app.py                          # Streamlit app (loads & normalizes all 3 CSVs)
├── scripts/
│   └── fetch_data.py               # fetches News, Research Papers, Knowledge Base -> 3 CSVs
├── data/
│   ├── news.csv
│   ├── research_papers.csv
│   └── knowledge_base.csv
├── .streamlit/
│   └── config.toml                 # theme
├── .github/workflows/
│   └── refresh-news.yml            # daily scheduled refresh of all 3 CSVs
├── requirements.txt
├── LICENSE
└── README.md
```

## Running it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# (optional) refresh all three CSVs: News, Research Papers, Knowledge Base
python scripts/fetch_data.py

streamlit run app.py
```

## Keeping data fresh

`.github/workflows/refresh-news.yml` runs `scripts/fetch_data.py` daily (07:00 UTC) and commits
all three CSVs back to the repo if anything changed — no manual step needed. Trigger it
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
- [x] Three separate, independently-refreshed CSVs (News / Research Papers / Knowledge Base)
- [x] Daily auto-refresh via GitHub Actions
- [x] Streamlit UI: News / Research Papers / Knowledge Base kept fully separate, per-area filters
- [x] Market snapshot (S&P 500 / Nasdaq / Bitcoin)
- [x] Validated color theme + professional Streamlit theme config
- [x] Data-driven overview summary per area
- [x] Deployed to Streamlit Community Cloud
- [x] MIT license
- [ ] Screenshots + video demo
- [ ] Project documentation (Google Doc)

## Course deliverables

Built for the Mastering Agentic AI Bootcamp, Week 1 Project — deadline Aug 16, 2026, 11:59pm PT.
