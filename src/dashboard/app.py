"""
Riftbound Price Forecast — Landing Page.
Run: streamlit run src/dashboard/app.py
"""
from __future__ import annotations

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from src.dashboard.utils import load_features, load_model_comparison, load_prices, load_top_movers

st.set_page_config(
    page_title="Riftbound Price Forecast",
    layout="wide",
    page_icon="⚔️",
)

# ── Load data ──────────────────────────────────────────────────────────────
prices  = load_prices()
mc      = load_model_comparison()
features = load_features()
movers  = load_top_movers()

# ── Header ─────────────────────────────────────────────────────────────────
st.title("⚔️ Riftbound Card Price Forecasting")
st.markdown(
    """
    A data science portfolio project that scrapes card price and tournament data
    for the **Riftbound TCG**, engineers features, and trains six forecasting models
    to predict weekly card price movement.

    > **Stack:** Python · TCGPlayer API · SQLite · scikit-learn · XGBoost · Prophet · Streamlit · Plotly
    """
)

# ── KPI row ────────────────────────────────────────────────────────────────
best_model   = mc.loc[mc["RMSE"].idxmin()]
last_week    = sorted(movers["week"].unique())[-1]
top_mover_row = movers[movers["week"] == last_week].nlargest(1, "pct_change_1w").iloc[0]
avg_pred_chg = (
    prices[prices["model"] == "Ridge"]["predicted_price"].mean()
    - prices[prices["model"] == "Ridge"]["actual_price"].mean()
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Cards Tracked",     f"{features['card_display'].nunique()}")
c2.metric("Best Model RMSE",   f"${best_model['RMSE']:.2f}",  delta=best_model["model_name"])
c3.metric("Top Mover (latest week)", top_mover_row["card_display"],
          delta=f"{top_mover_row['pct_change_1w']:+.1%}")
c4.metric("Avg Predicted Δ (Ridge)", f"${avg_pred_chg:+.2f}")

st.divider()

# ── Data freshness ─────────────────────────────────────────────────────────
last_data = sorted(features["week"].unique())[-1]
st.caption(f"Last updated: {last_data}   ·   Data source: TCGPlayer Infinite + RiftboundStats API")

# ── Navigation hint ────────────────────────────────────────────────────────
st.info("Use the sidebar to navigate between pages.", icon="👈")
