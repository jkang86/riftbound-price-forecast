"""
Phase 4 — Tree-Based Models: Random Forest + XGBoost.

Both models use log1p-transformed target. No feature scaling needed.
Feature importance charts saved to outputs/figures/.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit
import xgboost as xgb

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import FIGURES_DIR, MODEL_PARAMS, TARGET_COL
from src.models.utils import (
    FEATURE_COLS, compute_metrics, get_xy, load_features,
    make_pred_df, pred_to_price, time_split,
)

TOP_N_FEATURES = 10


def _save_importance_plot(importances: np.ndarray, model_name: str) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    idx = np.argsort(importances)[-TOP_N_FEATURES:]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(
        [FEATURE_COLS[i] for i in idx],
        importances[idx],
        color="#C89B3C",
    )
    ax.set_title(f"{model_name} — Top {TOP_N_FEATURES} Feature Importances")
    ax.set_xlabel("Importance")
    ax.invert_yaxis()
    fig.tight_layout()
    out = FIGURES_DIR / f"feature_importance_{model_name.lower()}.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"[{model_name}] Feature importance chart saved to {out.name}")
    print(f"[{model_name}] Top 5 features:")
    for i in reversed(idx[-5:]):
        print(f"  {FEATURE_COLS[i]}: {importances[i]:.4f}")


def train_random_forest(
    df: pd.DataFrame | None = None,
) -> tuple[RandomForestRegressor, dict, pd.DataFrame]:
    if df is None:
        df = load_features()
    train, test = time_split(df)

    X_train, y_train = get_xy(train)
    X_test,  _       = get_xy(test)
    y_test_orig = test[TARGET_COL].clip(lower=0).values

    model = RandomForestRegressor(
        n_estimators=MODEL_PARAMS["rf_n_estimators"],
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    y_pred_train = pred_to_price(model.predict(X_train))
    y_pred_test  = pred_to_price(model.predict(X_test))

    metrics = compute_metrics(y_test_orig, y_pred_test, "RandomForest")
    _save_importance_plot(model.feature_importances_, "RandomForest")

    pred_df = pd.concat([
        make_pred_df(train, y_pred_train, "RandomForest"),
        make_pred_df(test,  y_pred_test,  "RandomForest"),
    ], ignore_index=True)

    return model, metrics, pred_df


def train_xgboost(
    df: pd.DataFrame | None = None,
) -> tuple[xgb.XGBRegressor, dict, pd.DataFrame]:
    if df is None:
        df = load_features()
    train, test = time_split(df)

    X_train, y_train = get_xy(train)
    X_test,  _       = get_xy(test)
    y_test_orig = test[TARGET_COL].clip(lower=0).values

    tscv   = TimeSeriesSplit(n_splits=MODEL_PARAMS["ts_cv_splits"])
    n_boost = MODEL_PARAMS["xgb_n_estimators"]
    lr      = MODEL_PARAMS["xgb_learning_rate"]

    # Sort train by week for TimeSeriesSplit
    order = train["week"].argsort().values
    X_sorted, y_sorted = X_train[order], y_train[order]

    # Use early stopping on last CV fold to find optimal n_estimators
    best_n = n_boost
    best_score = np.inf
    for tr_idx, val_idx in tscv.split(X_sorted):
        sub_model = xgb.XGBRegressor(
            n_estimators=n_boost,
            learning_rate=lr,
            max_depth=4,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbosity=0,
            early_stopping_rounds=20,
            eval_metric="rmse",
        )
        sub_model.fit(
            X_sorted[tr_idx], y_sorted[tr_idx],
            eval_set=[(X_sorted[val_idx], y_sorted[val_idx])],
            verbose=False,
        )
        val_pred = pred_to_price(sub_model.predict(X_sorted[val_idx]))
        val_true = np.expm1(y_sorted[val_idx])
        score = float(np.sqrt(np.mean((val_true - val_pred) ** 2)))
        if score < best_score:
            best_score = score
            best_n = sub_model.best_iteration + 1

    model = xgb.XGBRegressor(
        n_estimators=best_n,
        learning_rate=lr,
        max_depth=4,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=0,
    )
    model.fit(X_train, y_train)
    print(f"[XGBoost] best n_estimators={best_n}")

    y_pred_train = pred_to_price(model.predict(X_train))
    y_pred_test  = pred_to_price(model.predict(X_test))

    metrics = compute_metrics(y_test_orig, y_pred_test, "XGBoost")
    _save_importance_plot(model.feature_importances_, "XGBoost")

    pred_df = pd.concat([
        make_pred_df(train, y_pred_train, "XGBoost"),
        make_pred_df(test,  y_pred_test,  "XGBoost"),
    ], ignore_index=True)

    return model, metrics, pred_df


if __name__ == "__main__":
    df = load_features()
    train_random_forest(df)
    train_xgboost(df)
