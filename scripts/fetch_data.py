"""Pull News, Research Papers, and Knowledge Base into three separate CSVs.

Each dataset has its own trusted, source-controlled origin and its own file, so
they can be fetched, refreshed, and reasoned about independently:

    data/news.csv            -- vetted mainstream/official RSS feeds
    data/research_papers.csv -- arXiv (cs.AI), classified by field
    data/knowledge_base.csv  -- a single curated GitHub "awesome list"

Run daily (see .github/workflows/refresh-news.yml) or manually:

    python scripts/fetch_data.py
"""

import re
import urllib.request
from datetime import datetime, date
from pathlib import Path

import feedparser
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# --- News: mainstream, editorially-staffed, or official primary sources only ---
NEWS_FEEDS = {
    "Tech": [
        ("TechCrunch", "https://techcrunch.com/feed/"),
        ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index"),
    ],
    "AI": [
        ("MIT Tech Review", "https://www.technologyreview.com/topic/artificial-intelligence/feed"),
        ("AI News", "https://www.artificialintelligence-news.com/feed/"),
    ],
    "Software Engineering": [
        ("InfoQ", "https://feed.infoq.com/"),
        ("Hacker News", "https://hnrss.org/frontpage"),
    ],
    "Cloud": [
        ("AWS Blog", "https://aws.amazon.com/blogs/aws/feed/"),
        ("Google Cloud Blog", "https://cloudblog.withgoogle.com/rss/"),
        ("Azure Blog", "https://azure.microsoft.com/en-us/blog/feed/"),
    ],
    "Cybersecurity": [
        ("Krebs on Security", "https://krebsonsecurity.com/feed/"),
        ("The Hacker News", "https://feeds.feedburner.com/TheHackersNews"),
        ("BleepingComputer", "https://www.bleepingcomputer.com/feed/"),
    ],
    "World": [
        ("BBC World", "http://feeds.bbci.co.uk/news/world/rss.xml"),
        ("NPR World", "https://feeds.npr.org/1004/rss.xml"),
    ],
    "Sports": [
        ("ESPN", "https://www.espn.com/espn/rss/news"),
    ],
    "Finance": [
        ("CNBC", "https://www.cnbc.com/id/10000664/device/rss/rss.html"),
    ],
    "Science": [
        ("NASA", "https://www.nasa.gov/news-release/feed/"),
    ],
}

# --- Research papers: arXiv's per-category feeds are frequently empty, so we
# fetch the reliable cs.AI feed and classify each paper from its own tags. ---
RESEARCH_FEED_URL = "https://export.arxiv.org/rss/cs.AI"
RESEARCH_FIELD_PRIORITY = [
    ("cs.CV", "Computer Vision"),
    ("cs.CL", "NLP"),
    ("cs.RO", "Robotics"),
    ("cs.LG", "Machine Learning"),
    ("cs.NE", "Neural / Evolutionary"),
    ("cs.CY", "AI & Society"),
]

# --- Knowledge base: one controlled, actively-maintained curated list -------
KNOWLEDGE_BASE_SOURCE = "GitHub: owainlewis/awesome-artificial-intelligence"
KNOWLEDGE_BASE_README_URL = (
    "https://raw.githubusercontent.com/owainlewis/awesome-artificial-intelligence/master/README.md"
)


def clean_summary(raw: str) -> str:
    text = re.sub("<[^<]+?>", "", raw or "")
    text = re.sub(r"^arXiv:\S+\s+Announce Type:\s*\S+\s+Abstract:\s*", "", text.strip())
    return " ".join(text.split())[:300]


def classify_research_field(tags: list) -> str:
    for code, label in RESEARCH_FIELD_PRIORITY:
        if code in tags:
            return label
    return "General AI"


def fetch_news() -> pd.DataFrame:
    rows = []
    for topic, sources in NEWS_FEEDS.items():
        for source_name, url in sources:
            parsed = feedparser.parse(url)
            for entry in parsed.entries:
                published = entry.get("published_parsed") or entry.get("updated_parsed")
                published_dt = datetime(*published[:6]) if published else datetime.utcnow()
                rows.append(
                    {
                        "title": entry.get("title", "").strip(),
                        "source": source_name,
                        "topic": topic,
                        "published": published_dt.strftime("%Y-%m-%d %H:%M"),
                        "summary": clean_summary(entry.get("summary", "")),
                        "url": entry.get("link", ""),
                    }
                )
    df = pd.DataFrame(rows).drop_duplicates(subset=["title", "url"])
    return df.sort_values("published", ascending=False).reset_index(drop=True)


def fetch_research_papers() -> pd.DataFrame:
    rows = []
    parsed = feedparser.parse(RESEARCH_FEED_URL)
    for entry in parsed.entries:
        published = entry.get("published_parsed") or entry.get("updated_parsed")
        published_dt = datetime(*published[:6]) if published else datetime.utcnow()
        tags = [t.get("term") for t in entry.get("tags", []) if t.get("term")]
        rows.append(
            {
                "title": entry.get("title", "").strip(),
                "source": "arXiv",
                "field": classify_research_field(tags),
                "published": published_dt.strftime("%Y-%m-%d %H:%M"),
                "summary": clean_summary(entry.get("summary", "")),
                "url": entry.get("link", ""),
            }
        )
    df = pd.DataFrame(rows).drop_duplicates(subset=["title", "url"])
    return df.sort_values("published", ascending=False).reset_index(drop=True)


def fetch_knowledge_base() -> pd.DataFrame:
    req = urllib.request.Request(KNOWLEDGE_BASE_README_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        text = resp.read().decode("utf-8", errors="ignore")

    today = date.today().strftime("%Y-%m-%d %H:%M")
    section = "General"
    rows = []
    for line in text.splitlines():
        heading = re.match(r"^###\s+(.+)$", line)
        if heading:
            section = heading.group(1).strip()
            continue
        item = re.match(r"^-\s+\[(.+?)\]\((https?://[^)]+)\)(?::\s*(.*))?$", line)
        if item:
            title, url, desc = item.groups()
            rows.append(
                {
                    "title": title.strip(),
                    "source": KNOWLEDGE_BASE_SOURCE,
                    "section": section,
                    "published": today,
                    "summary": clean_summary(desc or ""),
                    "url": url.strip(),
                }
            )
    df = pd.DataFrame(rows).drop_duplicates(subset=["title", "url"])
    return df.reset_index(drop=True)


if __name__ == "__main__":
    DATA_DIR.mkdir(exist_ok=True)

    news_df = fetch_news()
    news_df.to_csv(DATA_DIR / "news.csv", index=False)
    print(f"news.csv:            {len(news_df)} articles from {news_df['source'].nunique()} sources")

    research_df = fetch_research_papers()
    research_df.to_csv(DATA_DIR / "research_papers.csv", index=False)
    print(f"research_papers.csv: {len(research_df)} papers across {research_df['field'].nunique()} fields")

    kb_df = fetch_knowledge_base()
    kb_df.to_csv(DATA_DIR / "knowledge_base.csv", index=False)
    print(f"knowledge_base.csv:  {len(kb_df)} resources across {kb_df['section'].nunique()} sections")
