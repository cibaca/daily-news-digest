from collections import Counter
from datetime import datetime
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

# --- Color theme -----------------------------------------------------------
# Validated categorical palette (dataviz skill: scripts/validate_palette.js).
# Slot order is the CVD-safety mechanism -- kept fixed via category_orders=
# on every chart so adjacency never drifts with the data.
SLOT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7"]

TECH_TOPICS = ["Tech", "AI", "Software Engineering", "Cloud"]
TOPIC_ORDER = ["Technology", "World", "Sports", "Finance", "Science", "Research Papers"]
TECH_ORDER = ["Tech", "AI", "Software Engineering", "Cloud"]
RESEARCH_FIELD_ORDER = [
    "General AI", "NLP", "Machine Learning", "Computer Vision",
    "AI & Society", "Robotics", "Neural / Evolutionary",
]
STOCK_TICKERS = {"S&P 500": "^GSPC", "Nasdaq": "^IXIC", "Bitcoin": "BTC-USD"}
STOCK_ORDER = list(STOCK_TICKERS.keys())

TOPIC_EMOJI = {
    "Technology": "💻", "Tech": "💻", "AI": "🤖", "Software Engineering": "🛠️",
    "Cloud": "☁️", "World": "🌍", "Sports": "🏅", "Finance": "💰",
    "Science": "🔬", "Research Papers": "📄", "News": "📰",
}
TOPIC_COLOR = dict(zip(TOPIC_ORDER, SLOT))
TOPIC_COLOR.update(dict(zip(TECH_ORDER, SLOT)))  # local context, own chart -- safe to reuse slots
RESEARCH_FIELD_COLOR = dict(zip(RESEARCH_FIELD_ORDER, SLOT))
STOCK_COLOR = dict(zip(STOCK_ORDER, SLOT))


def emoji_for(topic: str) -> str:
    return TOPIC_EMOJI.get(topic, "📰")


def color_for(topic: str) -> str:
    return TOPIC_COLOR.get(topic, "#64748b")


st.set_page_config(page_title="Daily News Digest", page_icon="📰", layout="wide")


@st.cache_data
def load_csv(path_or_buffer) -> pd.DataFrame:
    df = pd.read_csv(path_or_buffer)
    df["published"] = pd.to_datetime(df["published"])
    if "subtopic" not in df.columns:
        df["subtopic"] = ""
    df["subtopic"] = df["subtopic"].fillna("")
    return df


@st.cache_data(ttl=3600)
def fetch_market_snapshot() -> pd.DataFrame:
    import yfinance as yf

    data = yf.download(
        list(STOCK_TICKERS.values()), period="30d", interval="1d", progress=False
    )["Close"]
    data = data.dropna(how="all").ffill().dropna()
    return data.rename(columns={v: k for k, v in STOCK_TICKERS.items()})


def top_keywords(titles: pd.Series, n: int = 12) -> pd.DataFrame:
    words = Counter()
    for title in titles:
        for word in str(title).lower().split():
            word = "".join(c for c in word if c.isalpha())
            if len(word) > 2 and word not in STOPWORDS:
                words[word] += 1
    common = words.most_common(n)
    return pd.DataFrame(common, columns=["keyword", "count"])


def kicker(label: str, color: str, emoji: str):
    st.markdown(
        f"<div style='display:inline-block;background:{color};color:white;"
        f"padding:3px 12px;border-radius:4px;font-size:0.75rem;font-weight:700;"
        f"letter-spacing:0.06em;text-transform:uppercase;margin-bottom:0.7rem;'>"
        f"{emoji} {label}</div>",
        unsafe_allow_html=True,
    )


def render_market_snapshot():
    st.subheader("📈 Market Snapshot")
    try:
        market_data = fetch_market_snapshot()
    except Exception:
        st.info("Market data temporarily unavailable.")
        return

    cols = st.columns(len(STOCK_ORDER))
    for col, name in zip(cols, STOCK_ORDER):
        series = market_data[name]
        last, prev = series.iloc[-1], series.iloc[-2]
        pct = (last - prev) / prev * 100
        col.metric(name, f"{last:,.2f}", f"{pct:+.2f}%")

    indexed = market_data / market_data.iloc[0] * 100
    fig = px.line(
        indexed, x=indexed.index, y=STOCK_ORDER,
        color_discrete_map=STOCK_COLOR,
        category_orders={"variable": STOCK_ORDER},
    )
    fig.update_layout(
        yaxis_title="Indexed performance (start = 100)", xaxis_title=None, legend_title=None,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Source: Yahoo Finance, cached hourly.")


def render_card(row: pd.Series, latest_ts: pd.Timestamp):
    is_fresh = (latest_ts - row["published"]) <= pd.Timedelta(hours=3)
    badge = " &nbsp;🔥 <span style='color:#ef4444;font-size:0.75em;'>NEW</span>" if is_fresh else ""
    summary = row["summary"] if pd.notna(row["summary"]) and row["summary"] else ""
    st.markdown(
        f"""
<div style="border:1px solid rgba(128,128,128,0.25);border-left:4px solid {color_for(row['topic'])};
            border-radius:8px;padding:0.75rem 1rem;margin-bottom:0.75rem;height:100%;">
  <div class="headline-title" style="font-weight:600;margin-bottom:0.25rem;">
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


def render_topic_section(topic_df: pd.DataFrame, topic: str, latest_ts: pd.Timestamp, key_prefix: str, extra=None):
    kicker(topic, color_for(topic), emoji_for(topic))
    if extra:
        extra()
    st.subheader(f"Top keywords — {topic}")
    kw_df = top_keywords(topic_df["title"])
    if not kw_df.empty:
        fig = px.bar(kw_df, x="count", y="keyword", orientation="h", color_discrete_sequence=[SLOT[0]])
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    st.subheader(f"{len(topic_df)} articles")
    render_feed(topic_df, latest_ts, key_prefix=key_prefix)


# --- Masthead -----------------------------------------------------------------
today_str = datetime.now().strftime("%A, %B %d, %Y")
st.markdown(
    f"""
<style>
.headline-title a {{ font-family: Georgia, 'Times New Roman', serif; }}
</style>
<div style="text-align:center;padding:0.25rem 0 1rem 0;border-bottom:3px double rgba(128,128,128,0.4);margin-bottom:1.25rem;">
  <div style="font-family:Georgia,'Times New Roman',serif;font-size:2.4rem;font-weight:700;letter-spacing:0.02em;">📰 DAILY NEWS DIGEST</div>
  <div style="font-size:0.85rem;opacity:0.65;margin-top:0.3rem;letter-spacing:0.03em;">{today_str.upper()} · LIVE EDITION</div>
</div>
""",
    unsafe_allow_html=True,
)

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

# --- Top-level areas: Overview / News / Research Papers -------------------------
tech_selected = [t for t in TECH_TOPICS if t in selected_topics]
other_news_selected = [t for t in ["World", "Sports", "Finance", "Science"] if t in selected_topics]
news_selected = tech_selected or other_news_selected
research_selected = "Research Papers" in selected_topics

tab_labels = ["📊 Overview"]
if news_selected:
    news_count = filtered["topic"].isin(tech_selected + other_news_selected).sum()
    tab_labels.append(f"📰 News ({news_count})")
if research_selected:
    rp_count = (filtered["topic"] == "Research Papers").sum()
    tab_labels.append(f"📄 Research Papers ({rp_count})")

tabs = st.tabs(tab_labels)
tab_idx = 1

# --- Overview: compiles News + Research Papers together for a bird's-eye view --
with tabs[0]:
    top_source = filtered["source"].value_counts().idxmax()
    top_topic = filtered["topic"].value_counts().idxmax()
    m1, m2 = st.columns(2)
    m1.metric("Most active topic", f"{emoji_for(top_topic)} {top_topic}", f"{(filtered['topic'] == top_topic).sum()} articles")
    m2.metric("Most active source", top_source, f"{(filtered['source'] == top_source).sum()} articles")

    chart1, chart2 = st.columns(2)
    with chart1:
        st.subheader("Articles by area")
        display_topic = filtered["topic"].apply(lambda t: "Technology" if t in TECH_TOPICS else t)
        topic_counts = display_topic.value_counts().reindex(TOPIC_ORDER).dropna().reset_index()
        topic_counts.columns = ["topic", "count"]
        fig = px.bar(
            topic_counts, x="topic", y="count", color="topic",
            color_discrete_map=TOPIC_COLOR, category_orders={"topic": TOPIC_ORDER},
        )
        fig.update_layout(showlegend=False, xaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)

    with chart2:
        st.subheader("Top sources by volume")
        source_counts = filtered["source"].value_counts().head(10).reset_index()
        source_counts.columns = ["source", "count"]
        fig_src = px.bar(source_counts, x="count", y="source", orientation="h", color_discrete_sequence=[SLOT[0]])
        fig_src.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
        st.plotly_chart(fig_src, use_container_width=True)

    st.subheader("Top keywords in headlines")
    kw_df = top_keywords(filtered["title"])
    fig2 = px.bar(kw_df, x="count", y="keyword", orientation="h", color_discrete_sequence=[SLOT[0]])
    fig2.update_layout(yaxis={"categoryorder": "total ascending"}, height=320, showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Articles over time")
    timeline = filtered.set_index("published").resample("h").size().reset_index(name="count")
    fig3 = px.line(timeline, x="published", y="count", color_discrete_sequence=[SLOT[0]])
    fig3.update_layout(xaxis_title=None)
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Latest headlines across everything")
    render_feed(filtered, data_freshness, key_prefix="overview")

# --- News area: Technology / World / Sports / Finance / Science ----------------
if news_selected:
    with tabs[tab_idx]:
        kicker("News", "#334155", "📰")
        news_sub_labels = []
        if tech_selected:
            news_sub_labels.append(f"{emoji_for('Technology')} Technology")
        news_sub_labels += [f"{emoji_for(t)} {t}" for t in other_news_selected]
        news_tabs = st.tabs(news_sub_labels)
        n_idx = 0

        if tech_selected:
            with news_tabs[n_idx]:
                kicker("Technology", color_for("Technology"), emoji_for("Technology"))
                tech_df = filtered[filtered["topic"].isin(tech_selected)]

                st.subheader("Articles by tech sub-topic")
                sub_counts = tech_df["topic"].value_counts().reindex(tech_selected).dropna().reset_index()
                sub_counts.columns = ["topic", "count"]
                fig_tech = px.bar(
                    sub_counts, x="topic", y="count", color="topic",
                    color_discrete_map=TOPIC_COLOR, category_orders={"topic": TECH_ORDER},
                )
                fig_tech.update_layout(showlegend=False, xaxis_title=None)
                st.plotly_chart(fig_tech, use_container_width=True)

                sub_tab_labels = ["All Tech"] + [f"{emoji_for(t)} {t}" for t in tech_selected]
                sub_tabs = st.tabs(sub_tab_labels)
                with sub_tabs[0]:
                    st.subheader(f"{len(tech_df)} technology articles")
                    render_feed(tech_df, data_freshness, key_prefix="tech_all")
                for s_tab, t in zip(sub_tabs[1:], tech_selected):
                    with s_tab:
                        render_topic_section(filtered[filtered["topic"] == t], t, data_freshness, key_prefix=f"tech_{t}")
            n_idx += 1

        for topic in other_news_selected:
            with news_tabs[n_idx]:
                extra = render_market_snapshot if topic == "Finance" else None
                render_topic_section(filtered[filtered["topic"] == topic], topic, data_freshness, key_prefix=topic, extra=extra)
            n_idx += 1
    tab_idx += 1

# --- Research Papers area: kept fully separate from News ------------------------
if research_selected:
    with tabs[tab_idx]:
        kicker("Research Papers", color_for("Research Papers"), emoji_for("Research Papers"))
        rp_df = filtered[filtered["topic"] == "Research Papers"]
        st.caption("Latest papers from arXiv (cs.AI), broken down by field via each paper's own category tags. Kept separate from the News area by design.")

        rc1, rc2 = st.columns(2)
        rc1.metric("Papers", len(rp_df))
        rc2.metric("Fields covered", rp_df["subtopic"].nunique())

        st.subheader("Papers by field")
        field_counts = rp_df["subtopic"].value_counts().reindex(RESEARCH_FIELD_ORDER).dropna().reset_index()
        field_counts.columns = ["field", "count"]
        fig_field = px.bar(
            field_counts, x="count", y="field", orientation="h", color="field",
            color_discrete_map=RESEARCH_FIELD_COLOR, category_orders={"field": RESEARCH_FIELD_ORDER},
        )
        fig_field.update_layout(yaxis={"categoryorder": "total ascending"}, height=320, showlegend=False)
        st.plotly_chart(fig_field, use_container_width=True)

        st.subheader("Top keywords in paper titles")
        kw_df = top_keywords(rp_df["title"])
        fig_kw = px.bar(kw_df, x="count", y="keyword", orientation="h", color_discrete_sequence=[SLOT[0]])
        fig_kw.update_layout(yaxis={"categoryorder": "total ascending"}, height=320, showlegend=False)
        st.plotly_chart(fig_kw, use_container_width=True)

        field_tab_labels = ["All fields"] + [f for f in RESEARCH_FIELD_ORDER if f in rp_df["subtopic"].unique()]
        field_tabs = st.tabs(field_tab_labels)
        with field_tabs[0]:
            st.subheader(f"{len(rp_df)} papers")
            render_feed(rp_df, data_freshness, key_prefix="rp_all")
        for f_tab, field in zip(field_tabs[1:], field_tab_labels[1:]):
            with f_tab:
                field_df = rp_df[rp_df["subtopic"] == field]
                st.subheader(f"{field} — {len(field_df)} papers")
                render_feed(field_df, data_freshness, key_prefix=f"rp_{field}")
    tab_idx += 1
