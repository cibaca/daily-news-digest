from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA_DIR = Path(__file__).parent / "data"
NEWS_PATH = DATA_DIR / "news.csv"
RESEARCH_PATH = DATA_DIR / "research_papers.csv"
KNOWLEDGE_PATH = DATA_DIR / "knowledge_base.csv"

STOPWORDS = {
    "the", "a", "an", "to", "of", "in", "on", "for", "and", "is", "are",
    "at", "with", "as", "by", "from", "it", "its", "this", "that", "be",
    "how", "why", "what", "after", "over", "into", "new", "says", "will",
    "than", "his", "her", "their", "up", "out", "not", "vs", "amid",
}

# --- Color theme -------------------------------------------------------------
# Validated categorical palette (dataviz skill: scripts/validate_palette.js).
# Slot order is the CVD-safety mechanism -- kept fixed via category_orders=
# on every chart so adjacency never drifts with the data.
SLOT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7"]
# Pastel tints + darkened text of each SLOT hue -- for "newspaper section tag" UI chrome
# (kickers, card backgrounds). Decorative use only; charts keep the full-saturation SLOT
# colors above, since those are what the CVD/contrast validator gates apply to.
PASTEL_MAP = dict(zip(SLOT, ["#d4e4f7", "#fbe1d6", "#d1efe4", "#fbeccc", "#fae5ed", "#cce6cc", "#dbd8ed"]))
TEXT_MAP = dict(zip(SLOT, ["#1e569a", "#a94b25", "#137e58", "#ab7400", "#a75976", "#005e00", "#352a78"]))

TECH_TOPICS = ["Tech", "AI", "Software Engineering", "Cloud", "Cybersecurity"]
NEWS_ORDER = ["Technology", "World", "Sports", "Finance", "Science"]
TECH_ORDER = ["Tech", "AI", "Software Engineering", "Cloud", "Cybersecurity"]
RESEARCH_FIELD_ORDER = [
    "General AI", "NLP", "Machine Learning", "Computer Vision",
    "AI & Society", "Robotics", "Neural / Evolutionary",
]
STOCK_TICKERS = {"S&P 500": "^GSPC", "Nasdaq": "^IXIC", "Bitcoin": "BTC-USD"}
STOCK_ORDER = list(STOCK_TICKERS.keys())
AREA_ORDER = ["News", "Research Papers", "Knowledge Base"]

TOPIC_EMOJI = {
    "Technology": "💻", "Tech": "💻", "AI": "🤖", "Software Engineering": "🛠️",
    "Cloud": "☁️", "Cybersecurity": "🛡️", "World": "🌍", "Sports": "🏅", "Finance": "💰", "Science": "🔬",
}
TOPIC_COLOR = {
    "Technology": SLOT[0], "Tech": SLOT[0], "AI": SLOT[1], "Software Engineering": SLOT[2],
    "Cloud": SLOT[3], "Cybersecurity": SLOT[4], "World": SLOT[1], "Sports": SLOT[2],
    "Finance": SLOT[3], "Science": SLOT[4],
}
RESEARCH_FIELD_COLOR = dict(zip(RESEARCH_FIELD_ORDER, SLOT))
STOCK_COLOR = dict(zip(STOCK_ORDER, SLOT))
AREA_COLOR = {"News": SLOT[0], "Research Papers": SLOT[1], "Knowledge Base": SLOT[2]}
AREA_EMOJI = {"News": "📰", "Research Papers": "📄", "Knowledge Base": "📚"}
KB_CARD_COLOR = SLOT[2]

NEWS_SOURCES_NOTE = (
    "All News sources are mainstream, editorially-staffed outlets or official vendor/agency "
    "blogs (BBC, NPR, ESPN, CNBC, NASA, TechCrunch, Ars Technica, MIT Tech Review, InfoQ, "
    "AWS/Google Cloud/Azure, Krebs on Security, The Hacker News, BleepingComputer) -- no "
    "content farms or unverified aggregators. Hacker News (the aggregator, not Krebs) is "
    "community-curated tech discussion, included for signal, not as a newsroom."
)
NEWS_SOURCES_NOTE_SIMPLE = (
    "Every story here comes from a well-known, trustworthy publisher or an official company "
    "blog -- no random blogs, no unverified sites."
)

# --- Simple mode: plain-language labels for non-technical readers -------------
# Display-only -- the underlying category names (used for filtering/data) never change.
SIMPLE_LABELS = {
    "AI": "Artificial Intelligence (AI)",
    "Software Engineering": "Coding & App Development",
    "Cloud": "Cloud Computing",
    "Cybersecurity": "Online Safety & Security",
    "World": "World News",
    "Finance": "Money & Markets",
    "Knowledge Base": "Learning Resources",
    "General AI": "General AI",
    "NLP": "Language AI (understands text)",
    "Machine Learning": "Machine Learning (AI that learns from data)",
    "Computer Vision": "Image AI (understands pictures)",
    "AI & Society": "AI & Society",
    "Robotics": "Robots",
    "Neural / Evolutionary": "Brain-Inspired AI",
    "Foundational papers": "Key Research Papers",
    "Guides and playbooks": "How-To Guides",
    "LLM application engineering": "Building AI Apps",
    "Protocols and interoperability": "AI Systems Working Together",
    "Agent frameworks": "AI Agent Tools",
    "Durable and asynchronous agents": "Reliable AI Agents",
    "Retrieval and data": "AI + Your Data",
    "Evals and reliability": "Testing AI Quality",
    "Deployment and observability": "Running AI Live",
    "Coding agents": "AI Coding Assistants",
    "Agent skills and workflows": "AI Agent Skills",
    "Software factories and agent orchestration": "Multi-Agent Systems",
}


def disp(name: str) -> str:
    """Plain-language label when Simple mode is on; the raw name otherwise."""
    if st.session_state.get("simple_mode") and name in SIMPLE_LABELS:
        return SIMPLE_LABELS[name]
    return name


def disp_order(names: list) -> list:
    return [disp(n) for n in names]


def disp_color_map(base_map: dict) -> dict:
    if not st.session_state.get("simple_mode"):
        return base_map
    merged = dict(base_map)
    merged.update({disp(k): v for k, v in base_map.items()})
    return merged

st.set_page_config(page_title="Daily News Digest", page_icon="📰", layout="wide")


@st.cache_data
def load_data() -> pd.DataFrame:
    """Load News, Research Papers, and Knowledge Base CSVs and normalize into one schema."""
    frames = []

    if NEWS_PATH.exists():
        news = pd.read_csv(NEWS_PATH)
        news["published"] = pd.to_datetime(news["published"])
        news["area"] = "News"
        news["category"] = news["topic"]
        news["color"] = news["category"].map(TOPIC_COLOR).fillna("#64748b")
        news["emoji"] = news["category"].map(TOPIC_EMOJI).fillna("📰")
        frames.append(news[["title", "source", "area", "category", "color", "emoji", "published", "summary", "url"]])

    if RESEARCH_PATH.exists():
        research = pd.read_csv(RESEARCH_PATH)
        research["published"] = pd.to_datetime(research["published"])
        research["area"] = "Research Papers"
        research["category"] = research["field"]
        research["color"] = research["category"].map(RESEARCH_FIELD_COLOR).fillna("#64748b")
        research["emoji"] = "📄"
        frames.append(research[["title", "source", "area", "category", "color", "emoji", "published", "summary", "url"]])

    if KNOWLEDGE_PATH.exists():
        kb = pd.read_csv(KNOWLEDGE_PATH)
        kb["published"] = pd.to_datetime(kb["published"])
        kb["area"] = "Knowledge Base"
        kb["category"] = kb["section"]
        kb["color"] = KB_CARD_COLOR
        kb["emoji"] = "📚"
        frames.append(kb[["title", "source", "area", "category", "color", "emoji", "published", "summary", "url"]])

    if not frames:
        return pd.DataFrame(columns=["title", "source", "area", "category", "color", "emoji", "published", "summary", "url"])
    return pd.concat(frames, ignore_index=True)


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


def keyword_chart(titles: pd.Series, height: int = 300, key: str = None):
    kw_df = top_keywords(titles)
    if kw_df.empty:
        return
    fig = px.bar(kw_df, x="count", y="keyword", orientation="h", color_discrete_sequence=[SLOT[0]])
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=height, showlegend=False)
    st.plotly_chart(fig, use_container_width=True, key=key)


def kicker(label: str, color: str, emoji: str):
    bg = PASTEL_MAP.get(color, "#eeeeec")
    text = TEXT_MAP.get(color, "#3a3a38")
    st.markdown(
        f"<div style='display:inline-block;background:{bg};color:{text};"
        f"border:1px solid {color};padding:3px 12px;border-radius:4px;font-size:0.75rem;font-weight:700;"
        f"letter-spacing:0.06em;text-transform:uppercase;margin-bottom:0.7rem;'>"
        f"{emoji} {disp(label)}</div>",
        unsafe_allow_html=True,
    )


def overview_line(text: str):
    st.markdown(
        f"<div style='background:#f2f1ee;border-radius:8px;padding:0.7rem 1rem;"
        f"margin-bottom:1rem;font-size:0.92rem;'>{text}</div>",
        unsafe_allow_html=True,
    )


def render_market_snapshot(key_prefix: str):
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
    fig = px.line(indexed, x=indexed.index, y=STOCK_ORDER, color_discrete_map=STOCK_COLOR)
    fig.update_layout(yaxis_title="Indexed performance (start = 100)", xaxis_title=None, legend_title=None)
    st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_chart")
    st.caption("Source: Yahoo Finance, cached hourly.")


def render_card(row: pd.Series, latest_ts: pd.Timestamp, show_fresh_badge: bool = True):
    is_fresh = show_fresh_badge and (latest_ts - row["published"]) <= pd.Timedelta(hours=3)
    badge = " &nbsp;🔥 <span style='color:#ef4444;font-size:0.75em;'>NEW</span>" if is_fresh else ""
    summary = row["summary"] if pd.notna(row["summary"]) and row["summary"] else ""
    pastel_bg = PASTEL_MAP.get(row["color"], "#f5f5f4")
    text_color = TEXT_MAP.get(row["color"], "#33332f")
    st.markdown(
        f"""
<div style="background:{pastel_bg};border:1px solid rgba(0,0,0,0.06);border-left:4px solid {row['color']};
            border-radius:8px;padding:0.75rem 1rem;margin-bottom:0.75rem;height:100%;">
  <div class="headline-title" style="font-weight:600;margin-bottom:0.25rem;">
    <a href="{row['url']}" target="_blank" style="text-decoration:none;color:{text_color};">{row['title']}</a>{badge}
  </div>
  <div style="font-size:0.8em;opacity:0.75;margin-bottom:0.4rem;color:{text_color};">
    {row['emoji']} {disp(row['area'])} · {disp(row['category'])} · {row['source']} · {row['published']:%b %d, %H:%M}
  </div>
  <div style="font-size:0.9em;opacity:0.9;color:#1a1a1a;">{summary}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_feed(feed: pd.DataFrame, latest_ts: pd.Timestamp, key_prefix: str, show_fresh_badge: bool = True):
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

    if page.empty:
        st.info("No items match the current filters.")
        return

    if view == "Card grid":
        cols = st.columns(2)
        for i, (_, row) in enumerate(page.iterrows()):
            with cols[i % 2]:
                render_card(row, latest_ts, show_fresh_badge)
    else:
        for _, row in page.iterrows():
            is_fresh = show_fresh_badge and (latest_ts - row["published"]) <= pd.Timedelta(hours=3)
            badge = " 🔥" if is_fresh else ""
            st.markdown(
                f"{row['emoji']} **[{row['title']}]({row['url']})**{badge}  "
                f"<span style='opacity:0.6;font-size:0.85em;'>· {disp(row['category'])} · {row['source']} · "
                f"{row['published']:%b %d, %H:%M}</span>",
                unsafe_allow_html=True,
            )

    if len(feed) > show_n:
        if st.button(f"Show more ({len(feed) - show_n} remaining)", key=f"{key_prefix}_more"):
            st.session_state[f"{key_prefix}_show"] = show_n + 10
            st.rerun()


def render_category_section(cat_df: pd.DataFrame, category: str, color: str, emoji: str, latest_ts: pd.Timestamp, key_prefix: str, show_fresh_badge: bool = True):
    kicker(category, color, emoji)
    st.subheader(f"Top keywords — {disp(category)}")
    keyword_chart(cat_df["title"], height=300, key=f"{key_prefix}_kw")
    st.subheader(f"{len(cat_df)} items")
    render_feed(cat_df, latest_ts, key_prefix=key_prefix, show_fresh_badge=show_fresh_badge)


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

items = load_data()
if items.empty:
    st.error("No data available. Run `python scripts/fetch_data.py` to generate the CSVs first.")
    st.stop()

news_all = items[items["area"] == "News"]
research_all = items[items["area"] == "Research Papers"]
kb_all = items[items["area"] == "Knowledge Base"]

# --- Sidebar: reading mode + per-area filters -----------------------------------
st.sidebar.toggle(
    "👋 Simple mode (plain-language labels)", key="simple_mode",
    help="Swaps technical labels (e.g. 'NLP', 'Software Engineering') for plain-language "
         "descriptions. Same data and charts underneath -- just friendlier wording.",
)

st.sidebar.title("Filters")

with st.sidebar.expander("📰 News", expanded=True):
    news_categories = sorted(news_all["category"].unique())
    sel_news_cat = st.multiselect(
        "Topics", news_categories, default=news_categories,
        format_func=lambda t: f"{TOPIC_EMOJI.get(t, '')} {disp(t)}", key="news_cat",
    )
    news_sources = sorted(news_all["source"].unique())
    sel_news_src = st.multiselect("Sources", news_sources, default=news_sources, key="news_src")
    if not news_all.empty:
        min_d, max_d = news_all["published"].min().date(), news_all["published"].max().date()
        news_date_range = (min_d, max_d) if min_d == max_d else st.slider(
            "Date range", min_value=min_d, max_value=max_d, value=(min_d, max_d), key="news_date"
        )
    else:
        news_date_range = None

with st.sidebar.expander("📄 Research Papers"):
    research_fields = sorted(research_all["category"].unique())
    sel_research_cat = st.multiselect(
        "Fields", research_fields, default=research_fields,
        format_func=disp, key="research_cat",
    )

with st.sidebar.expander("📚 Knowledge Base"):
    kb_sections = sorted(kb_all["category"].unique())
    sel_kb_cat = st.multiselect(
        "Sections", kb_sections, default=kb_sections,
        format_func=disp, key="kb_cat",
    )

search = st.sidebar.text_input("🔎 Search everything")

# --- Apply filters --------------------------------------------------------------
news_mask = items["area"].eq("News") & items["category"].isin(sel_news_cat) & items["source"].isin(sel_news_src)
if news_date_range:
    news_mask &= items["published"].dt.date.between(news_date_range[0], news_date_range[1])
research_mask = items["area"].eq("Research Papers") & items["category"].isin(sel_research_cat)
kb_mask = items["area"].eq("Knowledge Base") & items["category"].isin(sel_kb_cat)

filtered = items[news_mask | research_mask | kb_mask]
if search:
    m = filtered["title"].str.contains(search, case=False, na=False) | filtered["summary"].str.contains(search, case=False, na=False)
    filtered = filtered[m]

data_freshness = items["published"].max()
st.caption(
    f"🕒 News/Research as of **{news_all['published'].max():%b %d, %Y %H:%M}** · "
    f"{disp('Knowledge Base')} last synced **{kb_all['published'].max():%b %d, %Y}** · refreshes daily via GitHub Actions"
)

if filtered.empty:
    st.warning("No items match the current filters.")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Items", len(filtered))
c2.metric("Areas", filtered["area"].nunique())
c3.metric("Sources", filtered["source"].nunique())

news_f = filtered[filtered["area"] == "News"]
research_f = filtered[filtered["area"] == "Research Papers"]
kb_f = filtered[filtered["area"] == "Knowledge Base"]

if st.session_state.get("simple_mode"):
    overview_line(
        "👋 <b>Simple mode is on.</b> Here's what the three tabs below mean: "
        "📰 <b>News</b> = today's headlines. &nbsp; 📄 <b>Research Papers</b> = new AI research "
        "(more technical, written by scientists). &nbsp; 📚 <b>Learning Resources</b> = a "
        "hand-picked list of books, courses, and tools for learning AI."
    )

tabs = st.tabs(["📊 Overview", f"📰 News ({len(news_f)})", f"📄 Research Papers ({len(research_f)})", f"📚 {disp('Knowledge Base')} ({len(kb_f)})"])

# ============================= OVERVIEW ==========================================
with tabs[0]:
    simple = st.session_state.get("simple_mode")
    overview_bits = []
    if not news_f.empty:
        top_news_cat = news_f["category"].value_counts().idxmax()
        overview_bits.append(
            f"📰 <b>News</b>: {len(news_f)} articles from {news_f['source'].nunique()} trusted sources "
            f"across {news_f['category'].nunique()} topics -- most covered: {TOPIC_EMOJI.get(top_news_cat,'')} {disp(top_news_cat)}."
        )
    if not research_f.empty:
        top_field = research_f["category"].value_counts().idxmax()
        label = "research papers" if simple else "arXiv papers"
        unit = "topics" if simple else "fields"
        overview_bits.append(
            f"📄 <b>Research Papers</b>: {len(research_f)} {label} across {research_f['category'].nunique()} {unit} "
            f"-- most covered: {disp(top_field)}."
        )
    if not kb_f.empty:
        top_section = kb_f["category"].value_counts().idxmax()
        source_desc = "one hand-picked, trustworthy list" if simple else "a single controlled source"
        overview_bits.append(
            f"📚 <b>{disp('Knowledge Base')}</b>: {len(kb_f)} curated resources across {kb_f['category'].nunique()} sections "
            f"from {source_desc} -- largest: {disp(top_section)}."
        )
    overview_line("&nbsp;&nbsp;|&nbsp;&nbsp;".join(overview_bits))

    chart1, chart2 = st.columns(2)
    with chart1:
        st.subheader("Items by area")
        area_counts = filtered["area"].value_counts().reindex(AREA_ORDER).dropna().reset_index()
        area_counts.columns = ["area", "count"]
        if simple:
            area_counts["area"] = area_counts["area"].apply(disp)
        fig = px.bar(
            area_counts, x="area", y="count", color="area",
            color_discrete_map=disp_color_map(AREA_COLOR), category_orders={"area": disp_order(AREA_ORDER)},
        )
        fig.update_layout(showlegend=False, xaxis_title=None)
        st.plotly_chart(fig, use_container_width=True, key="overview_area_chart")

    with chart2:
        st.subheader("Top sources by volume")
        source_counts = filtered["source"].value_counts().head(10).reset_index()
        source_counts.columns = ["source", "count"]
        fig_src = px.bar(source_counts, x="count", y="source", orientation="h", color_discrete_sequence=[SLOT[0]])
        fig_src.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
        st.plotly_chart(fig_src, use_container_width=True, key="overview_sources_chart")

    st.subheader("Top keywords (News + Research headlines)")
    keyword_chart(pd.concat([news_f["title"], research_f["title"]]), height=320, key="overview_kw")

    if not news_f.empty:
        st.subheader("News activity over time")
        timeline = news_f.set_index("published").resample("h").size().reset_index(name="count")
        fig3 = px.line(timeline, x="published", y="count", color_discrete_sequence=[SLOT[0]])
        fig3.update_layout(xaxis_title=None)
        st.plotly_chart(fig3, use_container_width=True, key="overview_timeline_chart")

    render_market_snapshot(key_prefix="overview_market")

    st.subheader("Latest across everything")
    render_feed(filtered, data_freshness, key_prefix="overview")

# ============================= NEWS ==============================================
with tabs[1]:
    if news_f.empty:
        st.info("No News items match the current filters.")
    else:
        kicker("News", AREA_COLOR["News"], "📰")
        with st.expander("ℹ️ About these sources"):
            st.write(NEWS_SOURCES_NOTE_SIMPLE if simple else NEWS_SOURCES_NOTE)

        tech_selected = [t for t in TECH_TOPICS if t in sel_news_cat]
        other_news_selected = [t for t in ["World", "Sports", "Finance", "Science"] if t in sel_news_cat]

        news_sub_labels = []
        if tech_selected:
            news_sub_labels.append("💻 Technology")
        news_sub_labels += [f"{TOPIC_EMOJI.get(t,'')} {disp(t)}" for t in other_news_selected]
        news_tabs = st.tabs(news_sub_labels) if news_sub_labels else []
        n_idx = 0

        if tech_selected:
            with news_tabs[n_idx]:
                kicker("Technology", TOPIC_COLOR["Technology"], TOPIC_EMOJI["Technology"])
                tech_df = news_f[news_f["category"].isin(tech_selected)]

                st.subheader("Articles by tech sub-topic")
                sub_counts = tech_df["category"].value_counts().reindex(tech_selected).dropna().reset_index()
                sub_counts.columns = ["category", "count"]
                if simple:
                    sub_counts["category"] = sub_counts["category"].apply(disp)
                fig_tech = px.bar(
                    sub_counts, x="category", y="count", color="category",
                    color_discrete_map=disp_color_map(TOPIC_COLOR), category_orders={"category": disp_order(TECH_ORDER)},
                )
                fig_tech.update_layout(showlegend=False, xaxis_title=None)
                st.plotly_chart(fig_tech, use_container_width=True, key="tech_subtopic_chart")

                sub_tab_labels = ["All Tech"] + [f"{TOPIC_EMOJI.get(t,'')} {disp(t)}" for t in tech_selected]
                sub_tabs = st.tabs(sub_tab_labels)
                with sub_tabs[0]:
                    st.subheader(f"{len(tech_df)} technology articles")
                    render_feed(tech_df, data_freshness, key_prefix="tech_all")
                for s_tab, t in zip(sub_tabs[1:], tech_selected):
                    with s_tab:
                        render_category_section(
                            news_f[news_f["category"] == t], t, TOPIC_COLOR.get(t, "#64748b"),
                            TOPIC_EMOJI.get(t, ""), data_freshness, key_prefix=f"tech_{t}",
                        )
            n_idx += 1

        for topic in other_news_selected:
            with news_tabs[n_idx]:
                render_category_section(
                    news_f[news_f["category"] == topic], topic, TOPIC_COLOR.get(topic, "#64748b"),
                    TOPIC_EMOJI.get(topic, ""), data_freshness, key_prefix=topic,
                )
                if topic == "Finance":
                    render_market_snapshot(key_prefix="finance_market")
            n_idx += 1

# ============================= RESEARCH PAPERS ====================================
with tabs[2]:
    if research_f.empty:
        st.info("No Research Papers match the current filters.")
    else:
        kicker("Research Papers", AREA_COLOR["Research Papers"], AREA_EMOJI["Research Papers"])
        if simple:
            st.caption(
                "The newest research papers about AI, sorted into simple topics. These are "
                "written by scientists, so they're more technical than News -- that's why they "
                "get their own tab."
            )
        else:
            st.caption(
                "Latest papers from arXiv (cs.AI), classified by field from each paper's own "
                "category tags. Kept fully separate from the News area by design."
            )

        rc1, rc2 = st.columns(2)
        rc1.metric("Papers", len(research_f))
        rc2.metric("Topics" if simple else "Fields covered", research_f["category"].nunique())

        st.subheader("Papers by topic" if simple else "Papers by field")
        field_counts = research_f["category"].value_counts().reindex(RESEARCH_FIELD_ORDER).dropna().reset_index()
        field_counts.columns = ["field", "count"]
        if simple:
            field_counts["field"] = field_counts["field"].apply(disp)
        fig_field = px.bar(
            field_counts, x="count", y="field", orientation="h", color="field",
            color_discrete_map=disp_color_map(RESEARCH_FIELD_COLOR), category_orders={"field": disp_order(RESEARCH_FIELD_ORDER)},
        )
        fig_field.update_layout(yaxis={"categoryorder": "total ascending"}, height=320, showlegend=False)
        st.plotly_chart(fig_field, use_container_width=True, key="research_field_chart")

        st.subheader("Top keywords in paper titles")
        keyword_chart(research_f["title"], height=320, key="research_kw")

        raw_fields = [f for f in RESEARCH_FIELD_ORDER if f in research_f["category"].unique()]
        field_tab_labels = ["All fields"] + [disp(f) for f in raw_fields]
        field_tabs = st.tabs(field_tab_labels)
        with field_tabs[0]:
            st.subheader(f"{len(research_f)} papers")
            render_feed(research_f, data_freshness, key_prefix="rp_all")
        for f_tab, field in zip(field_tabs[1:], raw_fields):
            with f_tab:
                field_df = research_f[research_f["category"] == field]
                st.subheader(f"{disp(field)} — {len(field_df)} papers")
                render_feed(field_df, data_freshness, key_prefix=f"rp_{field}")

# ============================= KNOWLEDGE BASE =====================================
with tabs[3]:
    if kb_f.empty:
        st.info("No Knowledge Base resources match the current filters.")
    else:
        kicker("Knowledge Base", AREA_COLOR["Knowledge Base"], AREA_EMOJI["Knowledge Base"])
        source_name = kb_f["source"].iloc[0]
        if simple:
            st.caption(
                "A hand-picked list of learning resources about AI -- books, courses, and "
                "tools -- from one trusted, regularly-updated list. Not news, just reference "
                "material to learn from."
            )
        else:
            st.caption(
                f"A single, actively-maintained, source-controlled reference list ({source_name}) -- "
                "not a news feed. Re-synced daily; kept fully separate from News and Research Papers."
            )

        kc1, kc2 = st.columns(2)
        kc1.metric("Resources", len(kb_f))
        kc2.metric("Sections", kb_f["category"].nunique())

        st.subheader("Resources by section")
        section_counts = kb_f["category"].value_counts().reset_index()
        section_counts.columns = ["section", "count"]
        if simple:
            section_counts["section"] = section_counts["section"].apply(disp)
        fig_kb = px.bar(section_counts, x="count", y="section", orientation="h", color_discrete_sequence=[SLOT[2]])
        fig_kb.update_layout(yaxis={"categoryorder": "total ascending"}, height=400, showlegend=False)
        st.plotly_chart(fig_kb, use_container_width=True, key="kb_section_chart")

        st.subheader(f"{len(kb_f)} resources")
        render_feed(kb_f, data_freshness, key_prefix="kb", show_fresh_badge=False)
