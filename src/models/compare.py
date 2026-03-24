"""
Phase 4 — Model Comparison Runner.

Trains all 6 models, collects metrics, writes export CSVs.

Exports written:
  data/exports/model_comparison.csv  — RMSE / MAE / R² for all models
  data/exports/prices.csv            — actual vs predicted per card/week/model
  data/exports/features.csv          — dashboard-ready feature table
  data/exports/top_movers.csv        — weekly biggest price movers
  data/exports/feature_importances.csv — per-feature importance for RF and XGBoost
"""
from __future__ import annotations

import pandas as pd
import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import EXPORTS_DIR, PROCESSED_DIR, TARGET_COL
from src.models.utils import load_features, time_split
from src.models.linear import train_lasso, train_ridge
from src.models.tree import train_random_forest, train_xgboost
from src.models.timeseries import train_arima, train_prophet


# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------

def _save_model_comparison(metrics_list: list[dict]) -> None:
    df = pd.DataFrame(metrics_list)[["model_name", "RMSE", "MAE", "R2"]]
    df = df.sort_values("RMSE").reset_index(drop=True)
    out = EXPORTS_DIR / "model_comparison.csv"
    df.to_csv(out, index=False)
    print(f"\n[compare] model_comparison.csv saved ({len(df)} models)")
    print(df.to_string(index=False))
    return df


def _save_prices(pred_dfs: list[pd.DataFrame]) -> None:
    df = pd.concat(pred_dfs, ignore_index=True)
    df = df.sort_values(["card_display", "week", "model"]).reset_index(drop=True)
    df[["actual_price", "predicted_price"]] = df[["actual_price", "predicted_price"]].round(4)
    out = EXPORTS_DIR / "prices.csv"
    df.to_csv(out, index=False)
    print(f"[compare] prices.csv saved — {len(df)} rows, {df['card_display'].nunique()} cards, {df['model'].nunique()} models")


def _save_features_export(df: pd.DataFrame) -> None:
    """Subset of features.csv for the dashboard — drop one-hot dummies, keep key cols."""
    keep = [
        "product_id", "card_display", "week", "market_price",
        "rarity_tier", "days_since_first_sale", "set_release_flag",
        "tournament_play_rate", "tournament_top8_rate",
        "price_lag_1w", "price_pct_change_1w", TARGET_COL,
    ]
    # Also include original categorical labels from master for display
    master = pd.read_csv(PROCESSED_DIR / "master.csv")[
        ["product_id", "card_name", "rarity", "type", "domain", "set"]
    ].drop_duplicates("product_id")

    export = df[keep].merge(master, on="product_id", how="left")
    export = export.sort_values(["card_display", "week"]).reset_index(drop=True)

    float_cols = export.select_dtypes("float64").columns
    export[float_cols] = export[float_cols].round(4)

    out = EXPORTS_DIR / "features.csv"
    export.to_csv(out, index=False)
    print(f"[compare] features.csv saved — {export.shape}")


def _save_feature_importances(models_map: dict) -> None:
    """Save feature importances for RF and XGBoost to a tidy CSV."""
    from src.models.utils import FEATURE_COLS
    rows = []
    for model_name, model in models_map.items():
        for feat, imp in zip(FEATURE_COLS, model.feature_importances_):
            rows.append({"model": model_name, "feature": feat, "importance": round(float(imp), 6)})
    df = pd.DataFrame(rows).sort_values(["model", "importance"], ascending=[True, False])
    out = EXPORTS_DIR / "feature_importances.csv"
    df.to_csv(out, index=False)
    print(f"[compare] feature_importances.csv saved — {len(df)} rows")


def _save_top_movers(df: pd.DataFrame) -> None:
    """Weekly price movers derived from features.csv price_pct_change_1w."""
    movers = df[["card_display", "week", "market_price", "price_pct_change_1w"]].copy()
    movers = movers.rename(columns={"market_price": "price", "price_pct_change_1w": "pct_change_1w"})
    movers["direction"] = np.where(movers["pct_change_1w"] > 0, "Up",
                          np.where(movers["pct_change_1w"] < 0, "Down", "Flat"))
    movers = movers.dropna(subset=["pct_change_1w"])
    movers[["price", "pct_change_1w"]] = movers[["price", "pct_change_1w"]].round(4)
    movers = movers.sort_values(["week", "pct_change_1w"], ascending=[True, False]).reset_index(drop=True)
    out = EXPORTS_DIR / "top_movers.csv"
    movers.to_csv(out, index=False)
    print(f"[compare] top_movers.csv saved — {len(movers)} rows")


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def run_all() -> None:
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_features()
    print(f"\n[compare] Loaded features.csv — {df.shape[0]} rows, {df['product_id'].nunique()} products\n")

    results: list[dict]      = []
    pred_dfs: list[pd.DataFrame] = []

    # ---- Linear ----
    print("=" * 50)
    print("  Ridge Regression")
    print("=" * 50)
    _, ridge_metrics, ridge_preds = train_ridge(df)
    results.append(ridge_metrics)
    pred_dfs.append(ridge_preds)

    print("\n" + "=" * 50)
    print("  Lasso Regression")
    print("=" * 50)
    _, lasso_metrics, lasso_preds = train_lasso(df)
    results.append(lasso_metrics)
    pred_dfs.append(lasso_preds)

    # ---- Tree ----
    print("\n" + "=" * 50)
    print("  Random Forest")
    print("=" * 50)
    rf_model, rf_metrics, rf_preds = train_random_forest(df)
    results.append(rf_metrics)
    pred_dfs.append(rf_preds)

    print("\n" + "=" * 50)
    print("  XGBoost")
    print("=" * 50)
    xgb_model, xgb_metrics, xgb_preds = train_xgboost(df)
    results.append(xgb_metrics)
    pred_dfs.append(xgb_preds)

    # ---- Time Series ----
    print("\n" + "=" * 50)
    print("  ARIMA (per product)")
    print("=" * 50)
    _, arima_metrics, arima_preds = train_arima(df)
    results.append(arima_metrics)
    pred_dfs.append(arima_preds)

    print("\n" + "=" * 50)
    print("  Prophet (per product)")
    print("=" * 50)
    _, prophet_metrics, prophet_preds = train_prophet(df)
    results.append(prophet_metrics)
    pred_dfs.append(prophet_preds)

    # ---- Save exports ----
    print("\n" + "=" * 50)
    print("  Saving exports")
    print("=" * 50)
    _save_model_comparison(results)
    _save_prices(pred_dfs)
    _save_features_export(df)
    _save_top_movers(df)
    _save_feature_importances({"RandomForest": rf_model, "XGBoost": xgb_model})

    print(f"\n[compare] All exports written to {EXPORTS_DIR}")


if __name__ == "__main__":
    run_all()
