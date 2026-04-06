"""
Phase 4 — Linear Models: Ridge + Lasso.

Both models use:
  - Log1p transform on price-scale features and target
  - StandardScaler on all features
  - GridSearchCV(alpha) with TimeSeriesSplit(n_splits=5) on training data
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import Lasso, Ridge
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.preprocessing import StandardScaler

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import MODEL_PARAMS
from src.models.utils import (
    compute_metrics_per_card, get_xy, load_features, make_pred_df,
    pred_to_price, time_split,
)


def _fit_linear(
    name: str,
    estimator,
    param_grid: dict,
    train: pd.DataFrame,
    test: pd.DataFrame,
) -> tuple[object, dict, pd.DataFrame]:
    X_train, y_train = get_xy(train)
    X_test,  y_test  = get_xy(test)

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    tscv = TimeSeriesSplit(n_splits=MODEL_PARAMS["ts_cv_splits"])
    # Sort train by week so TimeSeriesSplit respects temporal order
    train_order = train["week"].argsort().values
    X_train_sorted = X_train_s[train_order]
    y_train_sorted = y_train[train_order]

    cv = GridSearchCV(
        estimator, param_grid,
        cv=tscv,
        scoring="neg_root_mean_squared_error",
        n_jobs=-1,
    )
    cv.fit(X_train_sorted, y_train_sorted)
    best = cv.best_estimator_
    print(f"[{name}] best params: {cv.best_params_}")

    y_pred_train_log = best.predict(X_train_s)
    y_pred_test_log  = best.predict(X_test_s)

    y_pred_train = pred_to_price(y_pred_train_log)
    y_pred_test  = pred_to_price(y_pred_test_log)
    y_test_orig  = test[__import__('config').TARGET_COL].clip(lower=0).values

    metrics  = compute_metrics_per_card(test, y_pred_test, name)
    pred_df  = pd.concat([
        make_pred_df(train, y_pred_train, name),
        make_pred_df(test,  y_pred_test,  name),
    ], ignore_index=True)

    return best, metrics, pred_df


def train_ridge(
    df: pd.DataFrame | None = None,
) -> tuple[Ridge, dict, pd.DataFrame]:
    if df is None:
        df = load_features()
    train, test = time_split(df)
    return _fit_linear(
        "Ridge",
        Ridge(),
        {"alpha": MODEL_PARAMS["ridge_alphas"]},
        train, test,
    )


def train_lasso(
    df: pd.DataFrame | None = None,
) -> tuple[Lasso, dict, pd.DataFrame]:
    if df is None:
        df = load_features()
    train, test = time_split(df)
    return _fit_linear(
        "Lasso",
        Lasso(max_iter=5000),
        {"alpha": MODEL_PARAMS["lasso_alphas"]},
        train, test,
    )


if __name__ == "__main__":
    df = load_features()
    train_ridge(df)
    train_lasso(df)
