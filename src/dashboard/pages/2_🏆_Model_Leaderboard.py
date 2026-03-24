"""Page 2 — Model Leaderboard: RMSE/MAE/R² comparison across all models."""
from __future__ import annotations

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import streamlit as st
from src.dashboard.utils import load_model_comparison
from src.dashboard.components.model_leaderboard import render as render_chart

st.set_page_config(page_title="Model Leaderboard", layout="wide", page_icon="🏆")
st.title("🏆 Model Leaderboard")

mc = load_model_comparison()

# ── Chart ──────────────────────────────────────────────────────────────────
render_chart(mc)

st.divider()

# ── Styled table ───────────────────────────────────────────────────────────
st.subheader("Full comparison table")

best_rmse  = mc["RMSE"].min()
worst_rmse = mc["RMSE"].max()

def _row_style(row):
    if row["RMSE"] == best_rmse:
        return ["background-color: rgba(123,200,164,0.25)"] * len(row)
    if row["RMSE"] == worst_rmse:
        return ["background-color: rgba(224,92,92,0.15)"] * len(row)
    return [""] * len(row)

styled = mc.sort_values("RMSE").style.apply(_row_style, axis=1).format(
    {"RMSE": "${:.4f}", "MAE": "${:.4f}", "R2": "{:.4f}"}
)
st.dataframe(styled, width='stretch', hide_index=True)

st.download_button(
    label="⬇ Download comparison CSV",
    data=mc.to_csv(index=False),
    file_name="model_comparison.csv",
    mime="text/csv",
)

st.caption(
    "Test period: last 3 weeks of available data. "
    "ARIMA and Prophet operate on the 52 products with ≥ 6 weeks of history. "
    "Ridge/Lasso/RF/XGBoost are evaluated across all 100 products."
)
