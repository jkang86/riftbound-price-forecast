"""Page 3 — Card Explorer: per-card drill-down with price history and metadata."""
from __future__ import annotations

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import streamlit as st
from src.dashboard.utils import load_features, load_prices
from src.dashboard.components.card_explorer import render as render_explorer

st.set_page_config(page_title="Card Explorer", layout="wide", page_icon="🔍")
st.title("🔍 Card Explorer")

features = load_features()
prices   = load_prices()

ALL_CARDS = sorted(features["card_display"].unique().tolist())
TEST_WEEKS = sorted(prices["week"].unique())[-3:]

# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Select Card")
    _default = next((c for c in ["Acceptable Losses", "Adaptatron"] if c in ALL_CARDS), ALL_CARDS[0])
    card = st.selectbox("Card", ALL_CARDS, index=ALL_CARDS.index(_default))

card_df = features[features["card_display"] == card].sort_values("week")

if card_df.empty:
    st.warning("No data for this card.")
    st.stop()

meta = card_df.iloc[0]

# ── Metadata row ───────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Rarity",    meta.get("rarity", "—"))
c2.metric("Type",      meta.get("type", "—"))
c3.metric("Domain",    meta.get("domain", "—"))
c4.metric("Set",       meta.get("set", "—"))
c5.metric("Days on Market", f"{int(card_df['days_since_first_sale'].max())}")

st.divider()

# ── Price history + play rate chart ────────────────────────────────────────
st.subheader("Price history & tournament play rate")
render_explorer(card_df, TEST_WEEKS)

st.divider()

# ── Summary stats ──────────────────────────────────────────────────────────
st.subheader("Price statistics")
col_a, col_b = st.columns(2)
with col_a:
    st.dataframe(
        card_df[["week", "market_price", "price_pct_change_1w", "tournament_play_rate"]]
        .rename(columns={
            "market_price": "Price",
            "price_pct_change_1w": "WoW %",
            "tournament_play_rate": "Play Rate",
        })
        .set_index("week")
        .style.format({"Price": "${:.2f}", "WoW %": "{:+.2%}", "Play Rate": "{:.2%}"}),
        width='stretch',
    )
with col_b:
    desc = card_df["market_price"].describe().round(4)
    st.dataframe(desc.rename("Value").to_frame(), width='stretch')
