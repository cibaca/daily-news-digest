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
TOPIC_EMOJI = {
    "Tech": "💻",
    "AI": "🤖",
    "Software Engineering": "🛠️",
    "Cloud": "☁️",
    "World": "🌍",
    "Sports": "🏅",
    "Finance": "💰",
    "Science": "🔬",
}


TOPIC_COLOR = {
    "Tech": "#6366f1",
    "AI": "#ec4899",
    "Software Engineering": "#14b8a6",
    "Cloud": "#0ea5e9",
    "World": "#f59e0b",
    "Sports": "#22c55e",
    "Finance": "#eab308",
    "Science": "#8b5cf6",
}


def emoji_for(topic: str) -> str:
    return TOPIC_EMOJI.get(topic, "📰")


def color_for(topic: str) -> str:
    return TOPIC_COLOR.get(topic, "#64748b")


st.set_page_config(page_title="Daily News Digest", page_icon="📰", layout="wide")


@st.cache_data
def load_csv(path_or_buffer) -> pd.DataFrame:
    df = pd.read_csv(path_or_buffer)
    df["published"] = pd.to_datetime(df["published"])
    return df


def top_keywords(titles: pd.Series, n: int = 12) -> pd.DataFrame:
    words = Counter()
    for title in titles:
        for word in str(title).lower().split():
            word = "".join(c for c in word if c.isalpha())
            if len(word) > 2 and word not in STOPWORDS:
                words[word] += 1
    common = words.most_common(n)
    return pd.DataFrame(common, columns=["keyword", "count"])


def render_card(row: pd.Series, latest_ts: pd.Timestamp):
    is_fresh = (latest_ts - row["published"]) <= pd.Timedelta(hours=3)
    badge = " &nbsp;🔥 <span style='color:#ef4444;font-size:0.75em;'>NEW</span>" if is_fresh else ""
    summary = row["summary"] if pd.notna(row["summary"]) and row["summary"] else ""
    st.markdown(
        f"""
<div style="border-left:4px solid {color_for(row['topic'])};border:1px solid rgba(128,128,128,0.25);
            border-left:4px solid {color_for(row['topic'])};border-radius:8px;padding:0.75rem 1rem;
            margin-bottom:0.75rem;height:100%;">
  <div style="font-weight:600;margin-bottom:0.25rem;">
    <a href="{row['url']}" target="_blank" style="text-decoration:none;">{row['title']}</a>{badge}
  </div>
  <div style="font-size:0.8em;opacity:0.65;margin-bottom:0.4rem;">
    {emoji_for(row['topic'])} {row['topic']} · {row['source']} · {row['published']:%b %d, %H:%M}
  </div>
  <div style="font-size:0.9em;opacity:0.85;">{summary}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_feed(feed: pd.DataFrame, latest_ts: pd.Timestamp, key_prefix: str):
    col_a, col_b = st.columns([2, 1])
    with col_a:
        sort_choice = st.radio(
            "Sort by",
            ["Newest first", "Oldest first", "Source A-Z"],
            horizontal=True,
            key=f"{key_prefix}_sort",
        )
    with col_b:
        view = st.radio(
            "View", ["Card grid", "Compact list"], horizontal=True, key=f"{key_prefix}_view"
        )

    if sort_choice == "Source A-Z":
        feed = feed.sort_values(["source", "published"], ascending=[True, False])
    else:
        feed = feed.sort_values("published", ascending=(sort_choice == "Oldest first"))

    show_n = st.session_state.get(f"{key_prefix}_show", 10)
    page = feed.head(show_n)

    if view == "Card grid":
        cols = st.columns(2)
        for i, (_, row) in enumerate(page.iterrows()):
            with cols[i % 2]:
                render_card(row, latest_ts)
    else:
        for _, row in page.iterrows():
            is_fresh = (latest_ts - row["published"]) <= pd.Timedelta(hours=3)
            badge = " 🔥" if is_fresh else ""
            st.markdown(
                f"{emoji_for(row['topic'])} **[{row['title']}]({row['url']})**{badge}  "
                f"<span style='opacity:0.6;font-size:0.85em;'>· {row['source']} · "
                f"{row['published']:%b %d, %H:%M}</span>",
                unsafe_allow_html=True,
            )

    if len(feed) > show_n:
        if st.button(f"Show more ({len(feed) - show_n} remaining)", key=f"{key_prefix}_more"):
            st.session_state[f"{key_prefix}_show"] = show_n + 10
            st.rerun()


st.title("📰 Daily News Digest")

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
selected_topics = st.sidebar.multiselect(
    "Topics", topics, default=topics, format_func=lambda t: f"{emoji_for(t)} {t}"
)

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

data_freshness = df["published"].max()
st.caption(
    f"🕒 Data as of **{data_freshness:%b %d, %Y %H:%M}** · "
    f"{df['source'].nunique()} sources · refreshes daily via GitHub Actions"
)

if filtered.empty:
    st.warning("No articles match the current filters.")
    st.stop()

# --- Metrics -----------------------------------------------------------------
c1, c2, c3 = st.columns(3)
c1.metric("Articles", len(filtered))
c2.metric("Topics", filtered["topic"].nunique())
c3.metric("Sources", filtered["source"].nunique())

# --- Topic-organized navigation ----------------------------------------------
tab_labels = ["📊 Overview"] + [f"{emoji_for(t)} {t} ({(filtered['topic'] == t).sum()})" for t in selected_topics]
tabs = st.tabs(tab_labels)

with tabs[0]:
    top_source = filtered["source"].value_counts().idxmax()
    top_topic = filtered["topic"].value_counts().idxmax()
    m1, m2 = st.columns(2)
    m1.metric("Most active topic", f"{emoji_for(top_topic)} {top_topic}", f"{(filtered['topic'] == top_topic).sum()} articles")
    m2.metric("Most active source", top_source, f"{(filtered['source'] == top_source).sum()} articles")

    chart1, chart2 = st.columns(2)
    with chart1:
        st.subheader("Articles by topic")
        topic_counts = filtered["topic"].value_counts().reset_index()
        topic_counts.columns = ["topic", "count"]
        fig = px.bar(
            topic_counts, x="topic", y="count", color="topic",
            color_discrete_map={t: color_for(t) for t in topic_counts["topic"]},
        )
        st.plotly_chart(fig, use_container_width=True)

    with chart2:
        st.subheader("Source diversity")
        source_counts = filtered["source"].value_counts().reset_index()
        source_counts.columns = ["source", "count"]
        fig_src = px.pie(source_counts, names="source", values="count", hole=0.45)
        st.plotly_chart(fig_src, use_container_width=True)

    st.subheader("Top keywords in headlines")
    kw_df = top_keywords(filtered["title"])
    fig2 = px.bar(kw_df, x="count", y="keyword", orientation="h")
    fig2.update_layout(yaxis={"categoryorder": "total ascending"}, height=320)
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Articles over time")
    timeline = filtered.set_index("published").resample("h").size().reset_index(name="count")
    fig3 = px.line(timeline, x="published", y="count")
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Latest headlines across all topics")
    render_feed(filtered, data_freshness, key_prefix="overview")

for tab, topic in zip(tabs[1:], selected_topics):
    with tab:
        topic_df = filtered[filtered["topic"] == topic]
        st.subheader(f"Top keywords — {topic}")
        kw_df = top_keywords(topic_df["title"])
        if not kw_df.empty:
            fig = px.bar(kw_df, x="count", y="keyword", orientation="h")
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=300)
            st.plotly_chart(fig, use_container_width=True)
        st.subheader(f"{emoji_for(topic)} {topic} articles ({len(topic_df)})")
        render_feed(topic_df, data_freshness, key_prefix=topic)
