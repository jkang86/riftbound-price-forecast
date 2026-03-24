"""Page 4 — Top Movers: biggest weekly price movers."""
from __future__ import annotations

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import streamlit as st
from src.dashboard.utils import load_top_movers
from src.dashboard.components.top_movers import render as render_movers

st.set_page_config(page_title="Top Movers", layout="wide", page_icon="🔥")
st.title("🔥 Top Movers")

movers = load_top_movers()
ALL_WEEKS = sorted(movers["week"].unique(), reverse=True)

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters")
    week      = st.selectbox("Week", ALL_WEEKS)
    direction = st.radio("Direction", ["Both", "Up", "Down"], horizontal=True)
    top_n     = st.slider("Top N", min_value=5, max_value=20, value=10)

df = movers[movers["week"] == week].copy()

if direction != "Both":
    df = df[df["direction"] == direction]

if df.empty:
    st.info("No movers for this selection.")
    st.stop()

# Largest absolute movers
df_top = df.reindex(df["pct_change_1w"].abs().nlargest(top_n).index)

# ── Chart ──────────────────────────────────────────────────────────────────
render_movers(df_top, top_n=top_n)

st.divider()

# ── Styled table ───────────────────────────────────────────────────────────
st.subheader(f"Top {top_n} movers — {week}")

def _color_direction(val):
    if val == "Up":
        return "color: #7BC8A4; font-weight: bold"
    if val == "Down":
        return "color: #E05C5C; font-weight: bold"
    return ""

display_df = df_top[["card_display", "price", "pct_change_1w", "direction"]].rename(
    columns={"card_display": "Card", "price": "Price", "pct_change_1w": "% Change", "direction": "Direction"}
).reset_index(drop=True)

styled = (
    display_df.style
    .applymap(_color_direction, subset=["Direction"])
    .format({"Price": "${:.2f}", "% Change": "{:+.2%}"})
)
st.dataframe(styled, width='stretch', hide_index=True)
