"""
Shared utilities for all model modules.

Split logic, feature/log-transform helpers, metric computation,
and prediction DataFrame construction.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import PROCESSED_DIR, TARGET_COL, MODEL_PARAMS

# ---------------------------------------------------------------------------
# Feature columns used by cross-sectional models (Ridge/Lasso/RF/XGB)
# ---------------------------------------------------------------------------

# Base features always expected in features.csv
_BASE_FEATURE_COLS: list[str] = [
    "rarity_tier",
    "days_since_first_sale",
    "set_release_flag",
    "tournament_play_rate",
    "tournament_top8_rate",
    "price_lag_1w",
    "price_lag_2w",
    "price_rolling_mean_4w",
    "price_pct_change_1w",
]


def get_feature_cols(df: pd.DataFrame) -> list[str]:
    """Return base features + all type/domain dummies present in df."""
    type_cols   = sorted(c for c in df.columns if c.startswith("type_"))
    domain_cols = sorted(c for c in df.columns if c.startswith("domain_primary_"))
    return _BASE_FEATURE_COLS + type_cols + domain_cols


# Legacy alias — populated after first load
FEATURE_COLS: list[str] = _BASE_FEATURE_COLS

# Price-scale features that benefit from log1p transformation
LOG_PRICE_COLS: list[str] = [
    "price_lag_1w",
    "price_lag_2w",
    "price_rolling_mean_4w",
]


# ---------------------------------------------------------------------------
# Train / test split
# ---------------------------------------------------------------------------

def load_features() -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / "features.csv")


def time_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Global time-based split — last ts_test_weeks weeks held out as test."""
    weeks = sorted(df["week"].unique())
    n_test = MODEL_PARAMS["ts_test_weeks"]
    test_weeks = set(weeks[-n_test:])
    train = df[~df["week"].isin(test_weeks)].copy()
    test  = df[ df["week"].isin(test_weeks)].copy()
    print(f"[split] train weeks: {sorted(train['week'].unique())}")
    print(f"[split] test  weeks: {sorted(test['week'].unique())}")
    print(f"[split] train rows: {len(train)} | test rows: {len(test)}")
    return train, test


# ---------------------------------------------------------------------------
# Feature matrix + log transform
# ---------------------------------------------------------------------------

def get_xy(df: pd.DataFrame, log_transform: bool = True) -> tuple[np.ndarray, np.ndarray]:
    X = df[get_feature_cols(df)].copy().astype(float)
    if log_transform:
        for col in LOG_PRICE_COLS:
            X[col] = np.log1p(X[col].clip(lower=0))
    y_raw = df[TARGET_COL].clip(lower=0).values
    y = np.log1p(y_raw) if log_transform else y_raw
    return X.values, y


# ---------------------------------------------------------------------------
# Metrics (always in original price space)
# ---------------------------------------------------------------------------

def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    model_name: str,
) -> dict[str, float]:
    y_pred = np.clip(y_pred, 0, None)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    mae  = float(mean_absolute_error(y_true, y_pred))
    r2   = float(r2_score(y_true, y_pred))
    print(f"[{model_name}] RMSE: {rmse:.4f} | MAE: {mae:.4f} | R\u00b2: {r2:.4f}")
    return {"model_name": model_name, "RMSE": round(rmse, 4), "MAE": round(mae, 4), "R2": round(r2, 4)}


def compute_metrics_per_card(
    test_df: pd.DataFrame,
    y_pred: np.ndarray,
    model_name: str,
) -> dict[str, float]:
    """Per-card averaged RMSE/MAE — matches ARIMA/Prophet methodology.

    Global compute_metrics inflates RMSE for cross-sectional models because
    a single high-value Showcase card prediction error dominates the squared sum.
    Averaging per-card metrics gives a fair apples-to-apples comparison.
    R² is still computed globally (same denominator as time-series models).
    """
    df = test_df.reset_index(drop=True).copy()
    df["_pred"] = np.clip(y_pred, 0, None)
    df["_true"] = df[TARGET_COL].clip(lower=0)

    card_stats = df.groupby("product_id").apply(
        lambda g: pd.Series({
            "rmse": float(np.sqrt(np.mean((g["_true"] - g["_pred"]) ** 2))),
            "mae":  float(np.mean(np.abs(g["_true"] - g["_pred"]))),
        })
    )
    avg_rmse = float(card_stats["rmse"].median())
    avg_mae  = float(card_stats["mae"].median())
    r2       = float(r2_score(df["_true"], df["_pred"]))

    print(f"[{model_name}] RMSE: {avg_rmse:.4f} | MAE: {avg_mae:.4f} | R\u00b2: {r2:.4f}")
    return {"model_name": model_name, "RMSE": round(avg_rmse, 4), "MAE": round(avg_mae, 4), "R2": round(r2, 4)}


def pred_to_price(y_pred_log: np.ndarray, log_transform: bool = True) -> np.ndarray:
    if log_transform:
        return np.clip(np.expm1(y_pred_log), 0, None)
    return np.clip(y_pred_log, 0, None)


# ---------------------------------------------------------------------------
# Prediction DataFrame builder
# ---------------------------------------------------------------------------

def make_pred_df(
    df: pd.DataFrame,
    predicted: np.ndarray,
    model_name: str,
) -> pd.DataFrame:
    return pd.DataFrame({
        "card_display": df["card_display"].values,
        "week":         df["week"].values,
        "actual_price": df[TARGET_COL].round(4).values,
        "predicted_price": np.round(np.clip(predicted, 0, None), 4),
        "model":        model_name,
    })
