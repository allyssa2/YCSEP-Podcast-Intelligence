# YCSEP Content Intelligence — Streamlit Final Project

This is a **Python source-code project**, not merely a static HTML mockup. It visualizes the documented outcomes of Assignment II using Streamlit, pandas and Plotly.

## 1. Install Python

Use Python 3.10+ (3.11 or 3.12 recommended).

## 2. Setup and run

Open terminal / PowerShell inside this folder:

```bash
python -m venv .venv
```

Activate the virtual environment:

- Windows PowerShell: `.venv\\Scripts\\Activate.ps1`
- Windows CMD: `.venv\\Scripts\\activate.bat`
- macOS/Linux: `source .venv/bin/activate`

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run dashboard:

```bash
python -m streamlit run app.py
```

Open the localhost URL printed by Streamlit, commonly `http://localhost:8501`.

## 3. Contents

- `app.py` — dashboard source code, including 4 pages/tabs and interactive filters
- `data/cluster_composition.csv` — Table 5.8 from Assignment II
- `data/model_evaluation.csv` — Table 5.6 from Assignment II
- `data/graph_sensitivity.csv` — Table 6.2 from Assignment II
- `data/channel_edges.csv` — cross-channel totals from Chapter 6
- `data/channel_profile.csv` — Table 4.9 from Assignment II
- `.streamlit/config.toml` — UI theme

## 4. Optional full graph data

The original per-episode `episode_semantic_graph_nodes.csv` and `episode_semantic_graph_edges.csv` were not provided in this turn. You can upload these files on the Graph Analytics tab to inspect actual records. Aggregate graph metrics are already plotted from the report.

**No invented episode graph nodes or links are presented as real research output.**

## 5. Research limitations

- 90 episodes / 3 channels represent a buffered-streaming sample, not the full YCSEP corpus.
- ML clusters are unvalidated thematic hypotheses.
- Silhouette of 0.1668 remains low in absolute terms; ARI of 0.8470 reflects stability, not topical accuracy.
- Cross-channel graph edges are potential recommendations, not validated listener relevance.
- Channel sidebar filters only affect composition plots, not fixed research-wide model or graph KPIs.
- No actual HDFS cluster or multi-node Spark execution is implied.
