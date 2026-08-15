"""Pull articles from public RSS feeds and save them to data/news.csv.

Run this once (or whenever you want fresh data) to regenerate the CSV
that app.py reads from:

    python scripts/fetch_news.py
"""

import re
from datetime import datetime
from pathlib import Path

import feedparser
import pandas as pd

FEEDS = {
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
    "World": [
        ("BBC World", "http://feeds.bbci.co.uk/news/world/rss.xml"),
        ("Reuters World", "https://www.reutersagency.com/feed/?best-topics=world&post_type=best"),
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

# arXiv's per-category RSS feeds (cs.LG, cs.CL, cs.CV, ...) are frequently empty;
# the cs.AI feed reliably carries new + cross-listed papers, so we fetch it once
# and derive a sub-topic per paper from its own category tags.
RESEARCH_FEED_URL = "https://export.arxiv.org/rss/cs.AI"
RESEARCH_SUBTOPIC_PRIORITY = [
    ("cs.CV", "Computer Vision"),
    ("cs.CL", "NLP"),
    ("cs.RO", "Robotics"),
    ("cs.LG", "Machine Learning"),
    ("cs.NE", "Neural / Evolutionary"),
    ("cs.CY", "AI & Society"),
]


def clean_summary(raw: str) -> str:
    text = re.sub("<[^<]+?>", "", raw or "")
    return " ".join(text.split())[:300]


def classify_research_subtopic(tags: list[str]) -> str:
    for code, label in RESEARCH_SUBTOPIC_PRIORITY:
        if code in tags:
            return label
    return "General AI"


def fetch_news_rows() -> list[dict]:
    rows = []
    for topic, sources in FEEDS.items():
        for source_name, url in sources:
            parsed = feedparser.parse(url)
            for entry in parsed.entries:
                published = entry.get("published_parsed") or entry.get("updated_parsed")
                published_dt = (
                    datetime(*published[:6]) if published else datetime.utcnow()
                )
                rows.append(
                    {
                        "title": entry.get("title", "").strip(),
                        "source": source_name,
                        "topic": topic,
                        "subtopic": "",
                        "published": published_dt.strftime("%Y-%m-%d %H:%M"),
                        "summary": clean_summary(entry.get("summary", "")),
                        "url": entry.get("link", ""),
                    }
                )
    return rows


def fetch_research_paper_rows() -> list[dict]:
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
                "topic": "Research Papers",
                "subtopic": classify_research_subtopic(tags),
                "published": published_dt.strftime("%Y-%m-%d %H:%M"),
                "summary": clean_summary(entry.get("summary", "")),
                "url": entry.get("link", ""),
            }
        )
    return rows


def fetch_all() -> pd.DataFrame:
    rows = fetch_news_rows() + fetch_research_paper_rows()
    df = pd.DataFrame(rows).drop_duplicates(subset=["title", "url"])
    df = df.sort_values("published", ascending=False).reset_index(drop=True)
    return df


if __name__ == "__main__":
    out_path = Path(__file__).resolve().parent.parent / "data" / "news.csv"
    df = fetch_all()
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} articles to {out_path}")
