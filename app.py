from collections import Counter
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA_PATH = Path(__file__).parent / "data" / "news.csv"
STOPWORDS = {
    "the", "a", "an", "to", "of", "in", "on", "for", "and", "is", "are",
    "at", "with", "as", "by", "from", "it", "its", "this", "that", "be",
    "how", "why", "what", "after", "over", "into", "new", "says", "will",
    "than", "his", "her", "their", "up", "out", "not", "vs", "amid",
}

st.set_page_config(page_title="Daily News Digest", page_icon="📰", layout="wide")


@st.cache_data
def load_csv(path_or_buffer) -> pd.DataFrame:
    df = pd.read_csv(path_or_buffer)
    df["published"] = pd.to_datetime(df["published"])
    return df


def top_keywords(titles: pd.Series, n: int = 15) -> pd.DataFrame:
    words = Counter()
    for title in titles:
        for word in str(title).lower().split():
            word = "".join(c for c in word if c.isalpha())
            if len(word) > 2 and word not in STOPWORDS:
                words[word] += 1
    common = words.most_common(n)
    return pd.DataFrame(common, columns=["keyword", "count"])


st.title("📰 Daily News Digest")
st.caption("A personal-interest news dashboard — vibe coded with Claude Code for the Mastering Agentic AI Bootcamp.")

# --- Sidebar: data source + filters ---------------------------------------
st.sidebar.header("Data source")
uploaded = st.sidebar.file_uploader("Upload your own news CSV", type="csv")
use_default = st.sidebar.checkbox("Use bundled sample CSV", value=uploaded is None)

if uploaded is not None and not use_default:
    df = load_csv(uploaded)
    st.sidebar.success(f"Loaded {len(df)} articles from upload")
elif DATA_PATH.exists():
    df = load_csv(DATA_PATH)
    st.sidebar.info(f"Loaded {len(df)} articles from data/news.csv")
else:
    st.error("No data available. Upload a CSV or run `python scripts/fetch_news.py` first.")
    st.stop()

st.sidebar.header("Filters")
topics = sorted(df["topic"].dropna().unique())
selected_topics = st.sidebar.multiselect("Topics", topics, default=topics)

sources = sorted(df["source"].dropna().unique())
selected_sources = st.sidebar.multiselect("Sources", sources, default=sources)

min_date, max_date = df["published"].min().date(), df["published"].max().date()
if min_date == max_date:
    date_range = (min_date, max_date)
else:
    date_range = st.sidebar.slider(
        "Date range", min_value=min_date, max_value=max_date, value=(min_date, max_date)
    )

search = st.sidebar.text_input("Search in title/summary")

# --- Apply filters ----------------------------------------------------------
filtered = df[
    df["topic"].isin(selected_topics)
    & df["source"].isin(selected_sources)
    & (df["published"].dt.date >= date_range[0])
    & (df["published"].dt.date <= date_range[1])
]
if search:
    mask = filtered["title"].str.contains(search, case=False, na=False) | filtered[
        "summary"
    ].str.contains(search, case=False, na=False)
    filtered = filtered[mask]

# --- Metrics -----------------------------------------------------------------
c1, c2, c3 = st.columns(3)
c1.metric("Articles", len(filtered))
c2.metric("Topics", filtered["topic"].nunique())
c3.metric("Sources", filtered["source"].nunique())

if filtered.empty:
    st.warning("No articles match the current filters.")
    st.stop()

# --- Charts -------------------------------------------------------------------
chart1, chart2 = st.columns(2)
with chart1:
    st.subheader("Articles by topic")
    topic_counts = filtered["topic"].value_counts().reset_index()
    topic_counts.columns = ["topic", "count"]
    fig = px.bar(topic_counts, x="topic", y="count", color="topic")
    st.plotly_chart(fig, use_container_width=True)

with chart2:
    st.subheader("Top keywords in headlines")
    kw_df = top_keywords(filtered["title"])
    fig2 = px.bar(kw_df, x="count", y="keyword", orientation="h")
    fig2.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Articles over time")
timeline = (
    filtered.set_index("published").resample("h").size().reset_index(name="count")
)
fig3 = px.line(timeline, x="published", y="count")
st.plotly_chart(fig3, use_container_width=True)

# --- Article feed --------------------------------------------------------------
st.subheader(f"Filtered feed ({len(filtered)} articles)")
sort_choice = st.radio("Sort by", ["Newest first", "Oldest first"], horizontal=True)
feed = filtered.sort_values("published", ascending=(sort_choice == "Oldest first"))

for _, row in feed.iterrows():
    with st.container(border=True):
        st.markdown(f"**[{row['title']}]({row['url']})**")
        st.caption(f"{row['topic']} · {row['source']} · {row['published']:%Y-%m-%d %H:%M}")
        if pd.notna(row["summary"]) and row["summary"]:
            st.write(row["summary"])
