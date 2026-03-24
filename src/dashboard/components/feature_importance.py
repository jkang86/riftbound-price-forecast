"""Feature importance horizontal bar chart."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st


def render(df: pd.DataFrame, model: str = "XGBoost", top_n: int = 10) -> None:
    """df: feature_importances DataFrame (model, feature, importance)."""
    subset = (
        df[df["model"] == model]
        .nlargest(top_n, "importance")
        .sort_values("importance")
    )
    fig = px.bar(
        subset,
        x="importance",
        y="feature",
        orientation="h",
        color="importance",
        color_continuous_scale=["#1E2A40", "#C89B3C"],
        labels={"importance": "Importance", "feature": ""},
    )
    fig.update_coloraxes(showscale=False)
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(tickfont=dict(size=11)),
    )
    st.plotly_chart(fig, width='stretch')
