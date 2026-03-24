"""Model leaderboard — grouped bar chart + styled dataframe."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def render(df: pd.DataFrame) -> None:
    """df: model_comparison DataFrame (model_name, RMSE, MAE, R2)."""
    ordered = df.sort_values("RMSE")

    fig = go.Figure()
    metrics = {"RMSE": "#E05C5C", "MAE": "#C89B3C", "R2": "#7BC8A4"}

    for metric, color in metrics.items():
        fig.add_trace(go.Bar(
            name=metric,
            x=ordered["model_name"],
            y=ordered[metric],
            marker_color=color,
            text=ordered[metric].round(4),
            textposition="outside",
        ))

    fig.update_layout(
        barmode="group",
        xaxis_title="Model",
        yaxis_title="Score",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=0, r=0, t=30, b=0),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, width='stretch')
