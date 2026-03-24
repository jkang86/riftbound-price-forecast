"""
Phase 4 — Time-Series Models: ARIMA + Prophet.

Both models operate per product_id on the price_next_week target series.
This aligns naturally with the features.csv target: predict price_next_week
from the history of price_next_week values.

ARIMA:
  - Grid search over p in {0,1,2}, d in {0,1}, q in {0,1,2} via AIC (statsmodels)
  - Skip products with fewer than MIN_SERIES_LEN rows

Prophet:
  - Uses raw price_next_week (no log transform — Prophet handles scale internally)
  - Adds set_release_flag as an additional regressor
  - Skip products with fewer than MIN_SERIES_LEN rows
"""
from __future__ import annotations

import itertools
import warnings

import numpy as np
import pandas as pd

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import MODEL_PARAMS, TARGET_COL
from src.models.utils import compute_metrics, load_features, make_pred_df, time_split

warnings.filterwarnings("ignore")

MIN_SERIES_LEN = 6   # minimum rows per product_id to attempt time-series fit


# ---------------------------------------------------------------------------
# ARIMA
# ---------------------------------------------------------------------------

def _best_arima_order(series: np.ndarray) -> tuple[int, int, int]:
    """Grid search over (p,d,q) — return order with lowest AIC."""
    from statsmodels.tsa.arima.model import ARIMA

    best_aic   = np.inf
    best_order = (1, 1, 0)

    for p, d, q in itertools.product([0, 1, 2], [0, 1], [0, 1, 2]):
        if p == 0 and q == 0:
            continue  # trivial model
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                res = ARIMA(series, order=(p, d, q)).fit()
            if res.aic < best_aic:
                best_aic   = res.aic
                best_order = (p, d, q)
        except Exception:
            pass

    return best_order


def train_arima(
    df: pd.DataFrame | None = None,
) -> tuple[None, dict, pd.DataFrame]:
    from statsmodels.tsa.arima.model import ARIMA

    if df is None:
        df = load_features()

    train_df, test_df = time_split(df)
    test_weeks = set(test_df["week"].unique())

    all_preds: list[pd.DataFrame] = []
    card_metrics: list[dict] = []
    skipped = 0

    for pid, grp in df.groupby("product_id"):
        grp = grp.sort_values("week").reset_index(drop=True)
        if len(grp) < MIN_SERIES_LEN:
            skipped += 1
            continue

        train_grp = grp[~grp["week"].isin(test_weeks)]
        test_grp  = grp[ grp["week"].isin(test_weeks)]

        if len(train_grp) < 3 or len(test_grp) == 0:
            skipped += 1
            continue

        series = train_grp[TARGET_COL].clip(lower=0).values

        order = _best_arima_order(series)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model = ARIMA(series, order=order).fit()

            # In-sample train predictions
            fitted = np.clip(model.fittedvalues, 0, None)

            # Forecast n_test steps (directly predicts price_next_week values)
            n_test   = len(test_grp)
            forecast = np.clip(model.forecast(steps=n_test), 0, None)

            # Train pred df (align fitted to train rows)
            train_pred = make_pred_df(train_grp, fitted, "ARIMA")
            test_pred  = make_pred_df(test_grp, forecast, "ARIMA")
            all_preds.extend([train_pred, test_pred])

            # Card-level test metrics
            y_true = test_grp[TARGET_COL].clip(lower=0).values
            rmse = float(np.sqrt(np.mean((y_true - forecast) ** 2)))
            mae  = float(np.mean(np.abs(y_true - forecast)))
            card_metrics.append({"rmse": rmse, "mae": mae})

        except Exception as exc:
            skipped += 1
            continue

    print(f"[ARIMA] Fitted {len(card_metrics)} products | Skipped {skipped}")

    if not card_metrics:
        raise RuntimeError("[ARIMA] No products could be fitted.")

    avg_rmse = float(np.mean([m["rmse"] for m in card_metrics]))
    avg_mae  = float(np.mean([m["mae"]  for m in card_metrics]))

    # R² computed globally across all test predictions
    pred_df = pd.concat(all_preds, ignore_index=True)
    test_preds = pred_df[pred_df["week"].isin(test_weeks)]
    r2 = float(1 - np.sum((test_preds["actual_price"] - test_preds["predicted_price"]) ** 2)
                  / np.sum((test_preds["actual_price"] - test_preds["actual_price"].mean()) ** 2))

    metrics = {
        "model_name": "ARIMA",
        "RMSE": round(avg_rmse, 4),
        "MAE":  round(avg_mae,  4),
        "R2":   round(r2, 4),
    }
    print(f"[ARIMA] RMSE: {avg_rmse:.4f} | MAE: {avg_mae:.4f} | R\u00b2: {r2:.4f}")
    return None, metrics, pred_df


# ---------------------------------------------------------------------------
# Prophet
# ---------------------------------------------------------------------------

def train_prophet(
    df: pd.DataFrame | None = None,
) -> tuple[None, dict, pd.DataFrame]:
    from prophet import Prophet

    if df is None:
        df = load_features()

    train_df, test_df = time_split(df)
    test_weeks = set(test_df["week"].unique())

    all_preds: list[pd.DataFrame] = []
    card_metrics: list[dict] = []
    skipped = 0

    for pid, grp in df.groupby("product_id"):
        grp = grp.sort_values("week").reset_index(drop=True)
        if len(grp) < MIN_SERIES_LEN:
            skipped += 1
            continue

        train_grp = grp[~grp["week"].isin(test_weeks)]
        test_grp  = grp[ grp["week"].isin(test_weeks)]

        if len(train_grp) < 3 or len(test_grp) == 0:
            skipped += 1
            continue

        prophet_train = pd.DataFrame({
            "ds": pd.to_datetime(train_grp["week"]),
            "y":  train_grp[TARGET_COL].clip(lower=0).values,
            "set_release_flag": train_grp["set_release_flag"].values,
        })
        prophet_future_rows = pd.DataFrame({
            "ds": pd.to_datetime(test_grp["week"]),
            "set_release_flag": test_grp["set_release_flag"].values,
        })
        prophet_all_rows = pd.concat([
            prophet_train[["ds", "set_release_flag"]],
            prophet_future_rows,
        ], ignore_index=True)

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                m = Prophet(
                    weekly_seasonality=False,
                    daily_seasonality=False,
                    yearly_seasonality=False,
                    seasonality_mode="additive",
                    interval_width=0.95,
                )
                m.add_regressor("set_release_flag")
                m.fit(prophet_train, iter=300)

            forecast = m.predict(prophet_all_rows)

            fitted   = np.clip(forecast["yhat"].values[:len(train_grp)], 0, None)
            test_hat = np.clip(forecast["yhat"].values[len(train_grp):], 0, None)

            train_pred = make_pred_df(train_grp, fitted,   "Prophet")
            test_pred  = make_pred_df(test_grp,  test_hat, "Prophet")
            all_preds.extend([train_pred, test_pred])

            y_true = test_grp[TARGET_COL].clip(lower=0).values
            rmse = float(np.sqrt(np.mean((y_true - test_hat) ** 2)))
            mae  = float(np.mean(np.abs(y_true - test_hat)))
            card_metrics.append({"rmse": rmse, "mae": mae})

        except Exception:
            skipped += 1
            continue

    print(f"[Prophet] Fitted {len(card_metrics)} products | Skipped {skipped}")

    if not card_metrics:
        raise RuntimeError("[Prophet] No products could be fitted.")

    avg_rmse = float(np.mean([m["rmse"] for m in card_metrics]))
    avg_mae  = float(np.mean([m["mae"]  for m in card_metrics]))

    pred_df = pd.concat(all_preds, ignore_index=True)
    test_preds = pred_df[pred_df["week"].isin(test_weeks)]
    r2 = float(1 - np.sum((test_preds["actual_price"] - test_preds["predicted_price"]) ** 2)
                  / np.sum((test_preds["actual_price"] - test_preds["actual_price"].mean()) ** 2))

    metrics = {
        "model_name": "Prophet",
        "RMSE": round(avg_rmse, 4),
        "MAE":  round(avg_mae,  4),
        "R2":   round(r2, 4),
    }
    print(f"[Prophet] RMSE: {avg_rmse:.4f} | MAE: {avg_mae:.4f} | R\u00b2: {r2:.4f}")
    return None, metrics, pred_df


if __name__ == "__main__":
    df = load_features()
    train_arima(df)
    train_prophet(df)
