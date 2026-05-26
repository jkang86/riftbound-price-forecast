"""Card Explorer — full price history + tournament play rate."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render(df: pd.DataFrame, test_weeks: list[str]) -> None:
    """
    df: features export filtered to a single card_display.
    test_weeks: list of week strings in the test period.
    """
    df = df.sort_values("week")

    fig = go.Figure()

    # Price history line
    fig.add_trace(go.Scatter(
        x=df["week"],
        y=df["market_price"],
        name="Market Price",
        line=dict(color="#C89B3C", width=2),
        mode="lines+markers",
        marker=dict(size=5),
        yaxis="y1",
    ))

    # Tournament play rate bars (secondary y)
    fig.add_trace(go.Bar(
        x=df["week"],
        y=df["tournament_play_rate"],
        name="Play Rate",
        marker_color="rgba(75, 144, 217, 0.4)",
        yaxis="y2",
    ))

    # Shade test region
    if test_weeks:
        fig.add_vrect(
            x0=min(test_weeks), x1=max(test_weeks),
            fillcolor="rgba(200,155,60,0.08)",
            layer="below", line_width=0,
            annotation_text="Test period",
            annotation_position="top left",
            annotation_font_color="#C89B3C",
        )

    fig.update_layout(
        xaxis_title="Week",
        yaxis=dict(title="Price (USD)", side="left"),
        yaxis2=dict(title="Play Rate", side="right", overlaying="y", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        margin=dict(l=0, r=0, t=30, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, width='stretch')
