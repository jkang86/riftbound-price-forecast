"""Page 5 — Feature Analysis: correlation heatmap, importances, scatter."""
from __future__ import annotations

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.utils import load_feature_importances, load_features
from src.dashboard.components.feature_importance import render as render_importance

st.set_page_config(page_title="Feature Analysis", layout="wide", page_icon="📊")
st.title("📊 Feature Analysis")

features    = load_features()
importances = load_feature_importances()

# ── Section 1: Correlation heatmap ─────────────────────────────────────────
st.subheader("Feature correlation matrix")

NUM_COLS = [
    "market_price", "rarity_tier", "days_since_first_sale",
    "set_release_flag", "tournament_play_rate", "tournament_top8_rate",
    "price_lag_1w", "price_pct_change_1w", "price_next_week",
]
corr = features[NUM_COLS].corr().round(3)

fig_heat = go.Figure(go.Heatmap(
    z=corr.values,
    x=corr.columns.tolist(),
    y=corr.index.tolist(),
    colorscale=[
        [0.0,  "#E05C5C"],
        [0.5,  "#1E2A40"],
        [1.0,  "#7BC8A4"],
    ],
    zmin=-1, zmax=1,
    text=corr.values.round(2),
    texttemplate="%{text}",
    textfont=dict(size=9),
    hoverongaps=False,
))
fig_heat.update_layout(
    margin=dict(l=0, r=0, t=10, b=0),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    xaxis=dict(tickangle=-35),
)
st.plotly_chart(fig_heat, width='stretch')

st.divider()

# ── Section 2: Feature importances ─────────────────────────────────────────
st.subheader("Feature importances")
col_left, col_right = st.columns(2)

with col_left:
    st.caption("XGBoost")
    render_importance(importances, model="XGBoost", top_n=10)

with col_right:
    st.caption("Random Forest")
    render_importance(importances, model="RandomForest", top_n=10)

st.divider()

# ── Section 3: Tournament play rate vs price scatter ───────────────────────
st.subheader("Tournament play rate vs price")
st.caption("Sized by top8 rate · Colored by rarity tier")

RARITY_LABELS = {1: "Common", 2: "Uncommon", 3: "Rare/Promo", 4: "Epic", 5: "Showcase"}
scatter_df = features.copy()
scatter_df["rarity_label"] = scatter_df["rarity_tier"].map(RARITY_LABELS)
scatter_df["top8_size"]    = (scatter_df["tournament_top8_rate"] * 40 + 4).clip(upper=30)

fig_scatter = px.scatter(
    scatter_df,
    x="tournament_play_rate",
    y="market_price",
    color="rarity_label",
    size="top8_size",
    hover_name="card_display",
    hover_data={"tournament_top8_rate": ":.2%", "market_price": ":$.2f", "top8_size": False},
    color_discrete_sequence=px.colors.qualitative.Bold,
    labels={
        "tournament_play_rate": "Tournament Play Rate",
        "market_price": "Market Price (USD)",
        "rarity_label": "Rarity",
    },
    log_y=True,
)
fig_scatter.update_layout(
    margin=dict(l=0, r=0, t=10, b=0),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(fig_scatter, width='stretch')
