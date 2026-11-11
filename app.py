"""YCSEP | Podcast Content Intelligence — redesigned research dashboard.

Run from the project folder:
    python -m streamlit run app.py

Reads only the five aggregated Assignment II CSV files in ./data.
Optional episode-level graph visualizations require original uploaded graph CSVs.
Tables are rendered as HTML rather than st.dataframe to avoid pyarrow imports
that are blocked on some enterprise-managed Windows computers.
"""

from __future__ import annotations

from html import escape
from pathlib import Path
import io

import networkx as nx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import plotly.io as pio
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

# ==========================================
# MIDNIGHT BLOOM COLOR PALETTE
# ==========================================

PRIMARY = "#192B59"       # Midnight Blue
ACCENT = "#5274B8"        # Royal Blue
RED = "#D93650"           # Crimson Red
PINK = "#E879A5"          # Rose Pink
BLUSH = "#F2A0BB"         # Blush Pink

INK = "#293348"           # Main Text
MUTED = "#8791A5"         # Secondary Text
BACKGROUND = "#F7F8FC"    # App Background
SURFACE = "#FFFFFF"       # Cards
BORDER = "#E5E8F0"        # Borders

# Channel colors
CHANNEL_COLORS = {
    "The Daily Ketchup Podcast": "#192B59",
    "Yah Lah BUT": "#D93650",
    "YouGotWatch": "#E879A5",
}

# Cluster colors
CLUSTER_COLORS = {
    "0": "#192B59",
    "1": "#D93650",
    "2": "#E879A5",
}

# Expected CSV schemas
EXPECTED = {
    "cluster_composition.csv": {
        "cluster", "channel", "episodes",
        "median_words", "topic_hypothesis"
    },
    "channel_profile.csv": {
        "channel", "episodes", "speaker_turns",
        "median_words", "median_speakers"
    },
    "model_evaluation.csv": {
        "model", "k", "silhouette", "ari"
    },
    "channel_edges.csv": {
        "channel_a", "channel_b", "edges"
    },
    "graph_sensitivity.csv": {
        "threshold", "edges", "components",
        "isolates", "largest_component"
    },
}

st.set_page_config(
    page_title="YCSEP | Podcast Intelligence",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
:root {--ink:#17243C; --muted:#718098; --border:#E5EAF2; --accent:#526CE1; --bg:#F4F7FC;}
html, body, [class*='css'], .stApp {font-family:'DM Sans', sans-serif;}
.stApp {background:#F4F7FC; color:var(--ink);}
.block-container {max-width:1450px; padding:2.0rem 2.4rem 3.2rem;}
#MainMenu {visibility:hidden;}
footer {visibility:hidden;}
h1,h2,h3,h4 {font-family:'Plus Jakarta Sans',sans-serif!important; color:var(--ink)!important; letter-spacing:-.035em;}
[data-testid='stSidebar'] {background:#FFFFFF; border-right:1px solid var(--border);}
[data-testid='stSidebar'] .block-container {padding-top:1.6rem;}
[data-testid='stSidebar'] h3 {font-size:1.03rem!important;}
[data-testid='stSidebar'] label {color:#40516C!important; font-weight:600;}
.hero {position:relative; overflow:hidden; border-radius:24px; padding:34px 36px 28px;
 background:linear-gradient(115deg,#172D54 0%,#294B7F 58%,#376B9B 100%); color:white;
 box-shadow:0 18px 44px rgba(33,61,106,.16); margin-bottom:22px;}
.hero:after {content:'';position:absolute;width:300px;height:300px;border:1px solid rgba(255,255,255,.18);border-radius:50%;right:-70px;top:-165px;box-shadow:0 0 0 45px rgba(255,255,255,.035),0 0 0 95px rgba(255,255,255,.025);}
.hero-label {font-size:11px; letter-spacing:.17em; font-weight:800; color:#BBD4FF; text-transform:uppercase; margin-bottom:14px;}
.hero-title {font-family:'Plus Jakarta Sans',sans-serif;font-size:clamp(27px,2.6vw,39px);font-weight:800;letter-spacing:-.05em;line-height:1.2;margin-bottom:9px;position:relative;z-index:1;}
.hero-desc {color:#DBE7F9;font-size:14px;max-width:750px;line-height:1.7;position:relative;z-index:1;}
.hero-chips {display:flex;gap:9px;flex-wrap:wrap;margin-top:19px;position:relative;z-index:1;}
.hero-chip {border:1px solid rgba(255,255,255,.23);border-radius:50px;background:rgba(255,255,255,.1);padding:6px 12px;color:#F2F7FF;font-size:11px;font-weight:700;}
.section-kicker {color:#526CE1;font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.12em;margin-bottom:6px;}
.section-title {font-family:'Plus Jakarta Sans',sans-serif;font-size:23px;font-weight:800;letter-spacing:-.04em;color:#17243C;margin:8px 0 5px;}
.section-desc {font-size:13px;color:#74819A;margin:0 0 20px;line-height:1.6;}
.metric-card {background:#FFF;border:1px solid #E5EAF2;border-radius:17px;padding:20px 19px 17px;min-height:138px;
 box-shadow:0 6px 19px rgba(25,51,94,.035);margin-bottom:9px;}
.metric-top {display:flex;justify-content:space-between;align-items:center;gap:12px;}
.metric-label {color:#6C7B94;font-size:12px;font-weight:700;line-height:1.4;}
.metric-icon {display:inline-flex;width:32px;height:32px;border-radius:10px;background:#EDF1FF;align-items:center;justify-content:center;font-size:16px;}
.metric-value {font-family:'Plus Jakarta Sans',sans-serif;font-size:32px;letter-spacing:-.06em;line-height:1.25;font-weight:800;color:#1B2C4B;margin-top:12px;}
.metric-note {font-size:11px;color:#8B97AA;margin-top:5px;}
.insight-bar {padding:15px 18px;border:1px solid #D8E5F5;background:#EDF5FF;border-radius:13px;color:#355276;font-size:12px;line-height:1.65;margin:16px 0 22px;}
.chart-title {font-family:'Plus Jakarta Sans',sans-serif;font-size:14px;font-weight:800;color:#22334F;margin:2px 0 0;}
.chart-subtitle {font-size:11px;color:#8C98A9;margin:3px 0 6px;}
.card-heading {font-family:'Plus Jakarta Sans',sans-serif;color:#1F3253;font-size:16px;font-weight:800;letter-spacing:-.025em;}
.card-body {font-size:12px;color:#64758F;line-height:1.7;margin-top:7px;}
.insight-card {background:white;border:1px solid #E5EAF2;border-radius:17px;padding:22px 24px;margin:3px 0 14px;
 box-shadow:0 6px 20px rgba(25,51,94,.035);}
.insight-num {display:inline-flex;background:#E9EEFF;border-radius:8px;color:#5066CE;font-size:11px;font-weight:800;padding:6px 9px;margin-bottom:11px;}
.insight-action {background:#F6F8FC;border-left:3px solid #526CE1;padding:12px 14px;border-radius:7px;margin-top:14px;font-size:12px;color:#3D4E6A;line-height:1.65;}
.clean-table-wrap {overflow:auto;border-radius:14px;border:1px solid #E4EAF3;background:white;margin:8px 0 18px;}
.clean-table {border-collapse:collapse;width:100%;font-size:12px;color:#3D4D69;}
.clean-table th {text-align:left;background:#F2F5FB;color:#62718A;padding:12px 14px;font-size:11px;font-weight:800;white-space:nowrap;}
.clean-table td {padding:11px 14px;border-top:1px solid #EDF1F6;vertical-align:top;}
.clean-table tr:nth-child(even) td {background:#FBFCFE;}
.sidebar-brand {font-family:'Plus Jakarta Sans',sans-serif;font-size:21px;font-weight:800;color:#1B3155;line-height:1.3;letter-spacing:-.05em;}
.sidebar-caption {font-size:11px;color:#8794A8;line-height:1.65;margin-top:6px;margin-bottom:18px;}
.sidebar-chip {padding:10px 12px;border-radius:10px;background:#F1F5FB;color:#53657F;font-size:11px;line-height:1.6;}
.caption-strip {color:#91A0B3;font-size:11px;margin-top:13px;line-height:1.65;}
[data-testid='stTabs'] [data-baseweb='tab-list'] {background:#FFF;padding:7px;border:1px solid #E6EBF3;border-radius:14px;gap:4px;margin-bottom:19px;overflow:auto;}
[data-testid='stTabs'] button[data-baseweb='tab'] {height:42px;border-radius:9px;color:#61718A;font-size:12px;font-weight:700;padding:0 18px;border-bottom:0;}
[data-testid='stTabs'] button[aria-selected='true'] {background:#EAF0FF;color:#314E99!important;}
[data-testid='stTabs'] [data-baseweb='tab-highlight'],[data-testid='stTabs'] [data-baseweb='tab-border'] {display:none;}
[data-testid='stVerticalBlockBorderWrapper']>div {border-radius:16px!important;border-color:#E5EAF2!important;background:white;}
[data-testid='stPlotlyChart'] {border-radius:12px;overflow:hidden;}
[data-testid='stFileUploader'] {border-radius:15px;}
hr {border-color:#E5EAF2!important;}
@media(max-width:800px){.block-container{padding:1rem .9rem 2rem;}.hero{padding:24px 20px;border-radius:16px;}.metric-card{min-height:120px;padding:15px;}.metric-value{font-size:27px;}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA / name)


def metric(label: str, value: str, note: str, icon: str = "◈") -> None:
    st.markdown(
        f'<div class="metric-card"><div class="metric-top"><span class="metric-label">{escape(label)}</span>'
        f'<span class="metric-icon">{escape(icon)}</span></div>'
        f'<div class="metric-value">{escape(str(value))}</div>'
        f'<div class="metric-note">{escape(note)}</div></div>',
        unsafe_allow_html=True,
    )


def table(df: pd.DataFrame, max_rows: int = 20) -> None:
    """HTML table avoids st.dataframe -> pyarrow native DLL import."""
    if df.empty:
        st.info("Belum ada data untuk pilihan ini.")
        return
    safe_df = df.head(max_rows).copy().fillna("—")
    markup = safe_df.to_html(index=False, escape=True, classes="clean-table", border=0)
    st.markdown(f'<div class="clean-table-wrap">{markup}</div>', unsafe_allow_html=True)
    if len(df) > max_rows:
        st.caption(f"Menampilkan {max_rows} dari {len(df)} baris.")


def section(title: str, subtitle: str, kicker: str = "RESEARCH DASHBOARD") -> None:
    st.markdown(
        f'<div class="section-kicker">{escape(kicker)}</div>'
        f'<div class="section-title">{escape(title)}</div>'
        f'<div class="section-desc">{escape(subtitle)}</div>',
        unsafe_allow_html=True,
    )


def plot_style(fig: go.Figure, height: int = 340, *, legend: bool = True) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=12, t=17, b=28),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(family="Arial, sans-serif", color="#61718B", size=12),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="top", y=-0.22, x=0, title_text="", font=dict(size=10)),
        hoverlabel=dict(bgcolor="#1F3559", font_color="white"),
    )
    fig.update_xaxes(showline=False, zeroline=False, gridcolor="#EEF2F7", tickfont=dict(size=11))
    fig.update_yaxes(showline=False, zeroline=False, gridcolor="#EEF2F7", tickfont=dict(size=11))
    return fig


def chart_title(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="chart-title">{escape(title)}</div><div class="chart-subtitle">{escape(subtitle)}</div>', unsafe_allow_html=True)


def plot(fig: go.Figure) -> None:
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False, "responsive": True})


def insight(number: str, title: str, explanation: str, action: str) -> None:
    st.markdown(
        f'<div class="insight-card"><div class="insight-num">{escape(number)}</div>'
        f'<div class="card-heading">{escape(title)}</div><div class="card-body">{escape(explanation)}</div>'
        f'<div class="insight-action"><strong>Business opportunity</strong><br>{escape(action)}</div></div>',
        unsafe_allow_html=True,
    )


# Load and validate the real aggregated research CSVs.
try:
    datasets = {name: read_csv(name) for name in EXPECTED}
except (FileNotFoundError, pd.errors.ParserError, UnicodeError) as exc:
    st.error(f"Data penelitian tidak dapat dibaca: {exc}")
    st.info("Pastikan kelima CSV asli berada dalam folder `data` di samping `app.py`.")
    st.stop()

for fname, needed in EXPECTED.items():
    absent = needed - set(datasets[fname].columns)
    if absent:
        st.error(f"File {fname} membutuhkan kolom: {', '.join(sorted(absent))}")
        st.stop()

composition = datasets["cluster_composition.csv"]
profile = datasets["channel_profile.csv"]
models = datasets["model_evaluation.csv"]
sensitivity = datasets["graph_sensitivity.csv"]
channel_edges = datasets["channel_edges.csv"]

# Values derived from the actual CSVs, not fabricated episode-level records.
all_channels = profile["channel"].astype(str).tolist()
total_episodes = int(profile["episodes"].sum())
total_turns = int(profile["speaker_turns"].sum())
total_clusters = int(composition["cluster"].nunique())
reported_cross_edges = int(channel_edges["edges"].sum())
selected_sensitivity = sensitivity.loc[(sensitivity["threshold"].astype(float) - 0.55).abs().idxmin()]
threshold_matches = abs(float(selected_sensitivity["threshold"]) - 0.55) < 1e-8
edges_at_threshold = int(selected_sensitivity["edges"]) if threshold_matches else None
cross_percent = 100 * reported_cross_edges / edges_at_threshold if edges_at_threshold else None

with st.sidebar:
    st.markdown('<div class="sidebar-brand">◈ YCSEP Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-caption">PODCAST RESEARCH CONSOLE<br>Assignment II · Analytics workspace</div>', unsafe_allow_html=True)
    st.markdown("### Explore channels")
    selected_channels = st.multiselect("Podcast channels", all_channels, default=all_channels)
    st.markdown('<div class="sidebar-chip">Channel filter applies to composition charts and channel profiles only. It does not retrain clustering or change graph metrics.</div>', unsafe_allow_html=True)
    st.divider()
    st.markdown("### Research source")
    st.caption("YCSEP Assignment II · 90-episode research sample across three podcast channels.")
    st.caption("Semantic-MiniLM · K-Means (k=3) · graph cosine threshold 0.55, five candidate neighbors.")
    st.divider()
    st.markdown("### Dataset status")
    for name in EXPECTED:
        st.caption("✓ " + name)
    st.markdown('<div class="caption-strip">Research findings are exploratory. Topic labels and recommendations require human validation.</div>', unsafe_allow_html=True)

filtered = composition[composition["channel"].isin(selected_channels)].copy()
filtered_profile = profile[profile["channel"].isin(selected_channels)].copy()

st.markdown(
    '<div class="hero"><div class="hero-label">BIG DATA ANALYTICS · FINAL PROJECT</div>'
    '<div class="hero-title">🎙️ Podcast Content Intelligence</div>'
    '<div class="hero-desc">From research results to practical content discovery insights. Explore semantic segments, compare model quality, and evaluate relationships across podcast channels.</div>'
    '<div class="hero-chips"><span class="hero-chip">YCSEP Research</span><span class="hero-chip">Semantic-MiniLM + K-Means</span><span class="hero-chip">Graph-based discovery</span><span class="hero-chip">Assignment II sample</span></div></div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="insight-bar"><strong>Reading guide:</strong> All reported results describe the Assignment II research sample, not the full YCSEP corpus. Clusters are not independently validated topic classes. Episode-level recommendations are only available with original graph exports.</div>',
    unsafe_allow_html=True,
)

tab_overview, tab_ml, tab_graph, tab_business = st.tabs(
    ["◉ Executive Overview", "◇ Machine Learning", "◎ Graph Analytics", "▣ Business Insights"]
)

with tab_overview:
    section("Research at a glance", "An executive summary of the experimental dataset and cross-channel content landscape.", "EXECUTIVE OVERVIEW")
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric("Sampled episodes", f"{total_episodes:,}", "Across three research channels", "🎧")
    with c2: metric("Speaker turns", f"{total_turns:,}", "After research filtering", "☷")
    with c3: metric("Selected clusters", str(total_clusters), "Semantic-MiniLM · K-Means", "◈")
    with c4: metric("Cross-channel links", f"{reported_cross_edges} / {edges_at_threshold or '—'}", "Exploratory semantic graph", "↗")
    st.markdown('<div class="caption-strip">Summary metrics cover the entire research sample and do not change with the channel filter.</div>', unsafe_allow_html=True)
    st.write("")

    l, r = st.columns([1.18, 1], gap="large")
    with l:
        with st.container(border=True):
            chart_title("Episode distribution by cluster", "Stacked channel contributions · selected channels")
            if filtered.empty:
                st.info("Select at least one channel in the sidebar.")
            else:
                grouped = filtered.groupby(["cluster", "channel"], as_index=False)["episodes"].sum()
                grouped["cluster"] = grouped["cluster"].astype(str)
                fig = px.bar(grouped, x="cluster", y="episodes", color="channel", barmode="stack",
                             color_discrete_map=CHANNEL_COLORS, text="episodes", labels={"cluster":"Cluster", "episodes":"Episodes"})
                fig.update_traces(textposition="inside", textfont=dict(color="white", size=11))
                plot(plot_style(fig, 354))
    with r:
        with st.container(border=True):
            chart_title("Podcast channel mix", "Number of sampled episodes per channel")
            if filtered_profile.empty:
                st.info("Select at least one channel in the sidebar.")
            else:
                fig = px.bar(filtered_profile, x="channel", y="episodes", color="channel",
                             color_discrete_map=CHANNEL_COLORS, text="episodes", labels={"channel":"", "episodes":"Episodes"})
                fig.update_traces(textposition="outside")
                fig.update_layout(xaxis_tickangle=-12)
                plot(plot_style(fig, 354, legend=False))

    st.write("")
    l, r = st.columns([1.2, 1], gap="large")
    with l:
        with st.container(border=True):
            chart_title("Channel profile", "Research sample metadata · filterable by channel")
            display = filtered_profile.rename(columns={"channel":"Channel", "episodes":"Episodes", "speaker_turns":"Speaker turns", "median_words":"Median words", "median_speakers":"Median speakers"})
            table(display)
    with r:
        insight("01 · KEY FINDING", "Clusters reveal a mixed content structure",
                "Cluster membership differs across podcast channels, but this alone does not establish reliable topic labels.",
                "Use clusters to prioritize manual content taxonomy review before applying any automated category labels.")

with tab_ml:
    section("Model performance & segmentation", "Compare text representations and clustering stability across the 27 research configurations.", "MACHINE LEARNING")
    mini = models[(models["model"].astype(str).str.contains("MiniLM", case=False)) & (models["k"].astype(int) == 3)]
    mini_sil = float(mini.iloc[0]["silhouette"]) if not mini.empty else None
    mini_ari = float(mini.iloc[0]["ari"]) if not mini.empty else None
    c1,c2,c3 = st.columns(3)
    with c1: metric("MiniLM silhouette · k=3", f"{mini_sil:.4f}" if mini_sil is not None else "—", "Cosine silhouette score", "◈")
    with c2: metric("MiniLM stability · ARI", f"{mini_ari:.4f}" if mini_ari is not None else "—", "Stability across initialization", "↗")
    with c3: metric("Channel–cluster NMI", "0.3543", "Reported association in Assignment II", "◎")
    st.write("")

    metric_choice = st.radio("Compare evaluation metric", ["silhouette", "ari"], horizontal=True,
                             format_func=lambda x: "Silhouette (cosine)" if x == "silhouette" else "Stability (ARI)")
    l, r = st.columns([1.22, 1], gap="large")
    with l:
        with st.container(border=True):
            chart_title("Model comparison across k", "Scores vary with the chosen number of clusters")
            fig = px.line(models, x="k", y=metric_choice, color="model", markers=True,
                          color_discrete_sequence=["#526CE1", "#16A994", "#F1A64A"],
                          labels={"k":"Cluster count (k)",metric_choice:metric_choice.upper(),"model":"Representation"})
            fig.update_xaxes(dtick=1)
            plot(plot_style(fig, 350))
    with r:
        with st.container(border=True):
            chart_title("Silhouette at k = 3", "All representations on a comparable baseline")
            three = models[models["k"].astype(int) == 3].copy()
            fig = px.bar(three, x="model", y="silhouette", color="model", text="silhouette",
                         color_discrete_sequence=["#526CE1", "#16A994", "#F1A64A"],
                         labels={"model":"", "silhouette":"Silhouette score"})
            fig.update_traces(texttemplate="%{text:.4f}", textposition="outside")
            plot(plot_style(fig, 350, legend=False))

    l, r = st.columns([1.1, 1], gap="large")
    with l:
        with st.container(border=True):
            chart_title("Cluster profile", "Values transcribed from the Assignment II results")
            cluster_summary = composition.groupby("cluster", as_index=False).agg(
                Episodes=("episodes", "sum"),
                **{"Median words": ("median_words", "first"), "Theme hypothesis": ("topic_hypothesis", "first")},
            ).rename(columns={"cluster":"Cluster"})
            table(cluster_summary)
    with r:
        with st.container(border=True):
            chart_title("Transcript-length differences", "Median word counts per cluster (descriptive)")
            fig = px.bar(cluster_summary, x="Cluster", y="Median words", text="Median words",
                         color=cluster_summary["Cluster"].astype(str), color_discrete_map=CLUSTER_COLORS)
            fig.update_traces(textposition="outside")
            plot(plot_style(fig, 290, legend=False))
    st.warning("Research limitation: channel–cluster association (NMI 0.3543) and transcript-length effects (ε²≈0.41) may influence segmentation. Stability is not the same as topic-label accuracy. Use manual validation before deployment.")
    with st.expander("View all model results"):
        table(models.sort_values(["model", "k"]), max_rows=30)

with tab_graph:
    section("Semantic relationships across channels", "Inspect graph structure and sensitivity. Episode-level maps require your actual exported nodes and edges.", "GRAPH ANALYTICS")
    c1,c2,c3,c4 = st.columns(4)
    with c1: metric("Graph nodes", str(total_episodes), "Research sample", "◉")
    with c2: metric("Edges · cosine ≥ 0.55", str(edges_at_threshold or "—"), "From graph sensitivity CSV", "↗")
    with c3: metric("Cross-channel", f"{reported_cross_edges} ({cross_percent:.1f}%)" if cross_percent is not None else str(reported_cross_edges), "Linked across different channels", "↔")
    with c4: metric("Largest component", str(int(selected_sensitivity["largest_component"])) if threshold_matches else "—", "At research graph threshold", "◎")
    st.write("")

    l, r = st.columns([1,1.13], gap="large")
    with l:
        with st.container(border=True):
            chart_title("Cross-channel links", "Research graph edge counts by channel pair")
            edge_view = channel_edges.copy()
            edge_view["Pair"] = edge_view["channel_a"].str.replace("The Daily Ketchup Podcast", "Daily Ketchup", regex=False) + " · " + edge_view["channel_b"].str.replace("The Daily Ketchup Podcast", "Daily Ketchup", regex=False)
            fig = px.bar(edge_view.sort_values("edges"), x="edges", y="Pair", orientation="h", text="edges", labels={"edges":"Edges", "Pair":""})
            fig.update_traces(marker_color="#526CE1", textposition="outside")
            plot(plot_style(fig, 334, legend=False))
    with r:
        with st.container(border=True):
            chart_title("Threshold sensitivity", "Edge count and isolated nodes under alternative thresholds")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=sensitivity["threshold"], y=sensitivity["edges"], name="Edges", mode="lines+markers",
                                     line=dict(color="#526CE1",width=3),marker=dict(size=7)))
            fig.add_trace(go.Scatter(x=sensitivity["threshold"], y=sensitivity["isolates"], name="Isolates",mode="lines+markers",yaxis="y2",
                                     line=dict(color="#F1A64A",width=3),marker=dict(size=7)))
            fig.update_layout(yaxis=dict(title="Edges"), yaxis2=dict(title="Isolated nodes",overlaying="y",side="right",showgrid=False))
            plot(plot_style(fig, 334))

    st.write("")
    with st.container(border=True):
        chart_title("Episode-level relationship explorer", "Upload original node and edge exports for a non-synthetic graph preview")
        st.caption("The default aggregated CSVs do not contain episode-level identities. This panel will not invent individual episode relationships.")
        left, right = st.columns(2)
        with left:
            nodes_file = st.file_uploader("Upload episode nodes CSV", type=["csv"], key="ycsep_nodes")
        with right:
            edges_file = st.file_uploader("Upload episode edges CSV", type=["csv"], key="ycsep_edges")

        if nodes_file is not None and edges_file is not None:
            try:
                node_df = pd.read_csv(io.BytesIO(nodes_file.getvalue()))
                edge_df = pd.read_csv(io.BytesIO(edges_file.getvalue()))
            except Exception as exc:
                st.error(f"CSV tidak bisa dibaca: {exc}")
            else:
                st.caption(f"Uploaded: {len(node_df)} nodes · {len(edge_df)} edges. Choose the identifier/source/target columns below.")
                if len(node_df) == 0 or len(edge_df) == 0:
                    st.info("CSV masih kosong.")
                else:
                    n_id = st.selectbox("Node ID column", node_df.columns.tolist(), index=0)
                    e1, e2 = st.columns(2)
                    with e1:
                        src = st.selectbox("Edge source column", edge_df.columns.tolist(), index=0)
                    with e2:
                        dst = st.selectbox("Edge target column", edge_df.columns.tolist(), index=min(1,len(edge_df.columns)-1))
                    label_options = ["(use node ID)"] + [str(v) for v in node_df.columns if v != n_id]
                    chosen_label = st.selectbox("Node display label", label_options)
                    if st.button("Render uploaded graph", type="primary"):
                        node_keys = node_df[n_id].dropna().astype(str).tolist()
                        valid_keys = set(node_keys)
                        g = nx.Graph()
                        g.add_nodes_from(node_keys)
                        valid = edge_df[[src,dst]].dropna().astype(str)
                        for s,t in valid.itertuples(index=False,name=None):
                            if s in valid_keys and t in valid_keys and s != t:
                                g.add_edge(s,t)
                        if len(g) > 250 or g.number_of_edges() > 2500:
                            st.warning("Graph too large for this preview. Filter source exports to at most 250 nodes and 2,500 edges.")
                        else:
                            positions = nx.spring_layout(g, seed=42)
                            ex,ey = [],[]
                            for a,b in g.edges():
                                ex.extend([positions[a][0], positions[b][0], None])
                                ey.extend([positions[a][1], positions[b][1], None])
                            labels = {str(k): str(v) for k,v in zip(node_df[n_id], node_df[chosen_label])} if chosen_label != "(use node ID)" else {}
                            n_names = list(g.nodes())
                            fig = go.Figure()
                            fig.add_trace(go.Scatter(x=ex, y=ey, mode="lines", line=dict(width=.7,color="#B8C5D9"), hoverinfo="skip",showlegend=False))
                            fig.add_trace(go.Scatter(x=[positions[n][0] for n in n_names],y=[positions[n][1] for n in n_names],
                                                     mode="markers",marker=dict(size=10,color="#526CE1",line=dict(color="white",width=1.5)),
                                                     text=[labels.get(n,n) for n in n_names],hovertemplate="%{text}<extra></extra>",showlegend=False))
                            fig.update_layout(xaxis=dict(visible=False),yaxis=dict(visible=False,scaleanchor="x",scaleratio=1))
                            plot(plot_style(fig, 470,legend=False))
                            st.caption(f"Showing {g.number_of_nodes()} uploaded nodes and {g.number_of_edges()} validated uploaded edges. Layout is a visualization, not a newly computed recommendation model.")
        else:
            st.markdown('<div class="sidebar-chip">Upload both original CSV exports to activate the graph view. No demo nodes or generated edges will be substituted.</div>', unsafe_allow_html=True)

with tab_business:
    section("Turn analytical results into decisions", "Potential operational uses to evaluate, not established commercial outcomes.", "BUSINESS INSIGHTS")
    insight("01 · CONTENT TAXONOMY", "Organize the podcast catalog with evidence",
            "K-Means divides the research sample into three exploratory groups. The channel mix shows meaningful differences but may reflect the source channel and transcript length.",
            "Ask editors to review a set of episodes from each cluster and assign human-validated content tags before applying a catalog-wide taxonomy.")
    insight("02 · CONTENT DISCOVERY", "Surface possible related episodes across channels",
            f"The research graph contains {reported_cross_edges} cross-channel semantic links" + (f" out of {edges_at_threshold} links." if edges_at_threshold else "."),
            "Treat linked episodes as recommendation candidates and test them with relevance judgments, precision@5, and user studies before launch.")
    insight("03 · MODEL GOVERNANCE", "Separate format effects from subject matter",
            "Episode length differs by cluster, and channel is associated with cluster assignment; semantic closeness is not proof of the same topic or audience preference.",
            "Evaluate normalized episode summaries and topic annotations to reduce format effects. Document uncertainty in any production classification workflow.")
    with st.container(border=True):
        chart_title("Suggested validation roadmap", "Practical steps for research-to-product development")
        roadmap = pd.DataFrame([
            {"Phase":"1 · Review", "Purpose":"Human-check cluster themes", "Evidence needed":"Expert topic annotations"},
            {"Phase":"2 · Validate", "Purpose":"Measure recommendation relevance", "Evidence needed":"Ground-truth pairs / precision@5"},
            {"Phase":"3 · Pilot", "Purpose":"Test user experience", "Evidence needed":"Opt-in user feedback / usability tests"},
            {"Phase":"4 · Monitor", "Purpose":"Check drift and quality", "Evidence needed":"Repeated evaluations on new episodes"},
        ])
        table(roadmap)
    st.info("Not established by this research: increases in revenue, watch time, click-through rate, satisfaction, or production recommendation accuracy.")

st.markdown('<div class="caption-strip">YCSEP · Podcast Content Intelligence &nbsp;|&nbsp; Source: Assignment II, Chapters 4–6 &nbsp;|&nbsp; Aggregated research CSVs, not fabricated episode-level data.</div>', unsafe_allow_html=True)
