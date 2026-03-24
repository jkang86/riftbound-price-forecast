"""
Dashboard data loaders — all file I/O lives here.
Every loader is wrapped with @st.cache_data.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import EXPORTS_DIR


@st.cache_data
def load_prices() -> pd.DataFrame:
    return pd.read_csv(EXPORTS_DIR / "prices.csv")


@st.cache_data
def load_features() -> pd.DataFrame:
    return pd.read_csv(EXPORTS_DIR / "features.csv")


@st.cache_data
def load_model_comparison() -> pd.DataFrame:
    return pd.read_csv(EXPORTS_DIR / "model_comparison.csv")


@st.cache_data
def load_top_movers() -> pd.DataFrame:
    return pd.read_csv(EXPORTS_DIR / "top_movers.csv")


@st.cache_data
def load_feature_importances() -> pd.DataFrame:
    return pd.read_csv(EXPORTS_DIR / "feature_importances.csv")
