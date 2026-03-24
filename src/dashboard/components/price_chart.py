"""Actual vs predicted price line chart."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

MODEL_COLORS = {
    "Ridge":        "#C89B3C",
    "Lasso":        "#E8B86D",
    "RandomForest": "#4A90D9",
    "XGBoost":      "#7BC8A4",
    "ARIMA":        "#E05C5C",
    "Prophet":      "#B57BFF",
}


def render(df: pd.DataFrame, selected_models: list[str]) -> None:
    """
    df: filtered prices DataFrame for a single card_display.
    selected_models: list of model names to overlay.
    """
    fig = go.Figure()

    # Actual price — one trace (same across models)
    actual = df[df["model"] == selected_models[0]].sort_values("week")
    fig.add_trace(go.Scatter(
        x=actual["week"],
        y=actual["actual_price"],
        name="Actual",
        line=dict(color="#FFFFFF", width=2),
        mode="lines+markers",
        marker=dict(size=5),
    ))

    for model in selected_models:
        subset = df[df["model"] == model].sort_values("week")
        fig.add_trace(go.Scatter(
            x=subset["week"],
            y=subset["predicted_price"],
            name=model,
            line=dict(color=MODEL_COLORS.get(model, "#888888"), width=1.5, dash="dot"),
            mode="lines+markers",
            marker=dict(size=4),
        ))

    # Shade test region (last 3 weeks)
    all_weeks = sorted(df["week"].unique())
    if len(all_weeks) >= 3:
        test_start = all_weeks[-3]
        fig.add_vrect(
            x0=test_start, x1=all_weeks[-1],
            fillcolor="rgba(200,155,60,0.08)",
            layer="below", line_width=0,
            annotation_text="Test period",
            annotation_position="top left",
            annotation_font_color="#C89B3C",
        )

    fig.update_layout(
        xaxis_title="Week",
        yaxis_title="Price (USD)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        margin=dict(l=0, r=0, t=30, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, width='stretch')
