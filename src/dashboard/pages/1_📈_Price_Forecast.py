"""Page 1 — Price Forecast: actual vs predicted per card, model selector."""
from __future__ import annotations

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import streamlit as st
from src.dashboard.utils import load_model_comparison, load_prices
from src.dashboard.components.price_chart import render as render_chart

st.set_page_config(page_title="Price Forecast", layout="wide", page_icon="📈")
st.title("📈 Price Forecast")

prices = load_prices()
mc     = load_model_comparison()

ALL_MODELS = sorted(prices["model"].unique().tolist())
ALL_CARDS  = sorted(prices["card_display"].unique().tolist())
ALL_WEEKS  = sorted(prices["week"].unique().tolist())

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")
    _default = next((c for c in ["Acceptable Losses", "Adaptatron"] if c in ALL_CARDS), ALL_CARDS[0])
    card = st.selectbox("Card", ALL_CARDS, index=ALL_CARDS.index(_default))
    models = st.multiselect("Models", ALL_MODELS, default=["Ridge", "XGBoost", "Prophet"])
    week_range = st.select_slider(
        "Week range",
        options=ALL_WEEKS,
        value=(ALL_WEEKS[0], ALL_WEEKS[-1]),
    )

if not models:
    st.warning("Select at least one model.")
    st.stop()

# ── Filter ─────────────────────────────────────────────────────────────────
df = prices[
    (prices["card_display"] == card) &
    (prices["model"].isin(models)) &
    (prices["week"] >= week_range[0]) &
    (prices["week"] <= week_range[1])
]

if df.empty:
    st.warning("No data for this selection.")
    st.stop()

# ── Chart ──────────────────────────────────────────────────────────────────
render_chart(df, models)

# ── Metrics row ────────────────────────────────────────────────────────────
st.subheader("Test-set metrics")
test_weeks = sorted(prices["week"].unique())[-3:]
test_df = df[df["week"].isin(test_weeks)]

if test_df.empty:
    st.caption("No test-period predictions for this card / model combination.")
else:
    cols = st.columns(len(models))
    for col, model_name in zip(cols, models):
        m_df = test_df[test_df["model"] == model_name]
        if m_df.empty:
            col.caption(f"{model_name}: no data")
            continue
        import numpy as np
        y_true = m_df["actual_price"].values
        y_pred = m_df["predicted_price"].values
        rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
        mae  = float(np.mean(np.abs(y_true - y_pred)))
        mc_row = mc[mc["model_name"] == model_name]
        r2 = float(mc_row["R2"].values[0]) if not mc_row.empty else float("nan")
        col.metric(f"{model_name} — RMSE", f"${rmse:.2f}")
        col.metric("MAE",  f"${mae:.2f}")
        col.metric("R²",   f"{r2:.4f}")
