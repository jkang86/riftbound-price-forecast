"""Top movers horizontal bar chart + styled dataframe."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st


def render(df: pd.DataFrame, top_n: int = 10) -> None:
    """df: pre-filtered top_movers slice for one week + direction."""
    subset = df.nlargest(top_n, "pct_change_1w") if not df.empty else df

    colors = subset["direction"].map({"Up": "#7BC8A4", "Down": "#E05C5C", "Flat": "#888888"})

    fig = px.bar(
        subset.sort_values("pct_change_1w"),
        x="pct_change_1w",
        y="card_display",
        orientation="h",
        color="direction",
        color_discrete_map={"Up": "#7BC8A4", "Down": "#E05C5C", "Flat": "#888888"},
        labels={"pct_change_1w": "% Change", "card_display": ""},
        text=subset.sort_values("pct_change_1w")["pct_change_1w"].map(lambda v: f"{v:+.1%}"),
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        xaxis=dict(tickformat=".0%"),
    )
    st.plotly_chart(fig, width='stretch')
