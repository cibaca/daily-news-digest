# Daily News Digest — Project Documentation

---

## Project overview

**Daily News Digest** is a news-outlet-style Streamlit dashboard with three independently
sourced, independently refreshed areas, plus a plain-language mode for non-technical readers:

- **📰 News** — RSS from vetted mainstream/official outlets, split into Technology (Tech, AI,
  Software Engineering, Cloud, Cybersecurity), World, Sports, Finance (with a live stock market
  snapshot), and Science.
- **📄 Research Papers** — recent arXiv (cs.AI) papers, auto-classified by field (NLP, Machine
  Learning, Computer Vision, Robotics, ...).
- **📚 Knowledge Base** — curated reference resources (books, courses, frameworks, tools) pulled
  from a single actively-maintained GitHub "awesome list."
- **👋 Simple mode** — a sidebar toggle that swaps every technical label for a plain-language
  equivalent app-wide, for readers unfamiliar with the jargon.

The three data areas are deliberately kept separate — different sourcing models, different
trust levels, different browsing needs — rather than dumped into one undifferentiated feed.

Live app: https://daily-news-digest-aug2026.streamlit.app
Code: https://github.com/cibaca/daily-news-digest

For a diagram of how the pieces fit together, see [`docs/architecture.md`](architecture.md).

## Datasets used

| Dataset | Source | Size | Refresh |
|---|---|---|---|
| News | 17 RSS feeds: BBC, NPR, ESPN, CNBC, NASA, TechCrunch, Ars Technica, MIT Tech Review, AI News, InfoQ, Hacker News, AWS/GCP/Azure blogs, Krebs on Security, The Hacker News, BleepingComputer | 333 articles | Daily, automated |
| Research Papers | arXiv `cs.AI` RSS, classified into 7 fields from each paper's own category tags | 299 papers | Daily, automated |
| Knowledge Base | GitHub repo `owainlewis/awesome-artificial-intelligence` (README parsed into 14 sections) | 77 resources | Daily, automated |
| Market Snapshot | Yahoo Finance via `yfinance` (S&P 500, Nasdaq, Bitcoin) | 3 tickers | Live, cached 1 hour |

No paid APIs or API keys were needed — every data source is free and publicly accessible.

## AI coding tool used

**Claude Code** (Anthropic's CLI coding agent) was used for the entire build, end to end —
scaffolding the repo, writing the RSS/arXiv/GitHub fetch pipeline, building the Streamlit UI,
setting up GitHub Actions for daily refresh, deploying to Streamlit Community Cloud, and
iterating on UI/UX, data visualization design, plain-language accessibility, and a licensing
audit.

## Prompts used during vibe coding (condensed to the essential ones)

1. *"Lock down an idea and create a GitHub repo — give me a list of project ideas, maybe a news
   compilation and interest topics."* → Brainstormed options, picked **Personal Interest News
   Digest**, created the GitHub repo, chose RSS (no API key) as the data source.
2. *"Project should be from CSV, with options in Streamlit to make changes. Auto-refresh once
   daily."* → Built the RSS → CSV fetch script, the first Streamlit app (filters, charts, feed),
   deployed to Streamlit Community Cloud, and added a GitHub Actions cron workflow for daily
   auto-refresh.
3. *"Improve the dashboard, sort by topic, make it more useful. Add AI, Software Engineering,
   and Cloud topics."* → Reorganized navigation into topic tabs with pagination and per-topic
   keyword charts, then expanded the RSS feed set and added a card-grid layout with richer
   stats.
4. *"Add Research Papers with sub-topic stats, group Tech together, give it a news-site theme —
   but keep Research Papers separate from News. Add colors, an overview tab, a stocks section,
   an open-source license, and Streamlit update docs."* → Integrated arXiv (working around
   arXiv's broken per-category feeds), grouped Tech/AI/Software Engineering/Cloud under one
   Technology tab, added a masthead theme, a live Market Snapshot, an MIT license, and split
   Research Papers into its own top-level area.
5. *"Create separate CSVs for News, Research Papers, and a Knowledge Base — ensure news sources
   are trustworthy, use a professional color palette, clean up the data."* → Split into three
   independent CSVs, audited every news source (dropped a dead Reuters feed, added NPR),
   sourced the Knowledge Base from a single curated GitHub list, ran the color palette through
   an actual colorblind-safety validator, and added a matching Streamlit theme.
6. *"Add Cybersecurity as a topic, and a pastel color theme for a newspaper feel."* → Added a
   Cybersecurity topic with vetted security-journalism sources, and a pastel tint/dark-text
   treatment for section badges and article cards.
7. *"Add a Tech / Non-Tech toggle — same information, simpler language."* → Built a Simple mode
   toggle that swaps every technical label app-wide via a plain-language dictionary, without
   touching the underlying data or filtering.
8. *"Check the whole app is consistent — `.gitignore`, README, credit given, license accuracy."*
   → Audited third-party content licensing (verified the Knowledge Base source is MIT-licensed),
   clarified in the README that the MIT license covers the code only (not the news excerpts,
   abstracts, or KB entries displayed), and added arXiv's requested acknowledgment plus a
   `yfinance`/Yahoo Finance disclaimer.

## Iterations & what changed along the way

- **Data architecture**: started as one combined CSV → split into three fully independent CSVs
  (News / Research Papers / Knowledge Base) once the project grew, so each dataset could have
  its own trust model, refresh cadence, and schema.
- **Source reliability discovered mid-build**: arXiv's per-category RSS feeds (`cs.LG`, `cs.CL`,
  `cs.CV`) turned out to be empty on arXiv's own infrastructure — worked around by fetching the
  reliable `cs.AI` feed and classifying each paper's field from its own tags instead. Reuters'
  public RSS also turned out to be dead and was replaced with NPR.
- **Navigation**: flat list of topic tabs → grouped Technology sub-topics under one tab → fully
  separate top-level areas (News / Research Papers / Knowledge Base) once the project had three
  genuinely different kinds of content that shouldn't be filtered or charted together.
- **Color design**: moved from ad hoc chart colors to a palette run through an actual
  colorblind-safety validator (CVD ΔE, contrast gates), then layered a pastel/newspaper variant
  on top for UI chrome (cards, section badges) while keeping full-saturation colors in charts.
- **Accessibility for non-technical readers**: added a Simple mode toggle late in the build,
  once it became clear the dashboard had accumulated real jargon (NLP, arXiv, cs.AI, KB section
  names like "Durable and asynchronous agents") that wasn't approachable for a general reader.
- **Testing approach**: initially verified the Streamlit app with `curl`, which only fetches the
  static HTML shell and doesn't actually execute the Python script. Switched to Streamlit's
  official `AppTest` harness, which runs the real script — this caught several genuine bugs
  (duplicate chart element IDs from repeated renders, a markdown-inside-raw-HTML bug that broke
  bold text in the Overview summary) that `curl` had missed entirely.
- **Licensing/ethics pass**: near the end, did a dedicated audit — confirmed the Knowledge Base
  source repo's own license permits reuse, clarified that the project's MIT license covers only
  the code (not the third-party news/research/reference content flowing through it), and added
  the acknowledgment arXiv explicitly requests from API consumers.

## Learnings / observations

- **The biggest surprise was how quickly an idea became a working product.** Instead of
  spending days setting up project structure, deployment, CI/CD, and data pipelines, I was able
  to get a usable application running very early and spend most of my time evaluating features
  and improving the user experience.
- **Prompt quality mattered more than writing detailed technical specifications.** The most
  productive workflow was not creating a massive requirements document upfront. Instead, I
  continuously reviewed the application, identified the next improvement, and gave focused
  instructions. Each iteration made the product noticeably better and helped discover
  requirements that were not obvious at the beginning.
- **Building the app exposed product decisions faster than planning alone.** Once the dashboard
  was live, it became immediately clear which features were useful, which navigation patterns
  were confusing, and which data sources needed improvement. Rapid implementation shortened the
  feedback loop between idea, execution, and evaluation.
- **AI significantly reduced development friction but still required direction.** Claude Code
  handled most implementation tasks quickly, including data ingestion, UI development,
  deployment, testing updates, and project organization. My role shifted from writing every line
  of code to defining goals, reviewing outputs, validating decisions, and deciding what should
  be built next.
- **Data source reliability became a larger challenge than coding.** More time was spent
  validating feeds, replacing broken sources, checking licensing, and improving content
  organization than writing application logic. The quality of the final product depended
  heavily on the quality of the underlying data.
- **Testing and verification remain essential.** A running application does not guarantee a
  correct application. Several issues were only discovered after testing the actual Streamlit
  execution path, reinforcing the importance of validating outputs rather than assuming
  generated code is correct.
- **The project changed how I think about software development.** With modern AI coding agents,
  implementation is no longer the primary bottleneck for many small applications. The greater
  challenge is defining the right problem, selecting trustworthy data, evaluating results, and
  continuously refining the product through iteration.

## Tech stack

Streamlit, pandas, feedparser, plotly, yfinance, GitHub Actions (scheduled fetch), Streamlit
Community Cloud (hosting). MIT licensed (code only — see README for third-party content terms).
