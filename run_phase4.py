"""
Phase 4 runner — Model Training & Comparison.

Usage:
  python run_phase4.py            # train all 6 models + write exports
  python run_phase4.py --linear   # Ridge + Lasso only
  python run_phase4.py --tree     # Random Forest + XGBoost only
  python run_phase4.py --ts       # ARIMA + Prophet only
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 4 — Model Training")
    parser.add_argument("--linear", action="store_true")
    parser.add_argument("--tree",   action="store_true")
    parser.add_argument("--ts",     action="store_true")
    args = parser.parse_args()

    from src.models.utils import load_features
    df = load_features()

    run_all = not (args.linear or args.tree or args.ts)

    if run_all:
        from src.models.compare import run_all as _run
        _run()
        return

    from config import EXPORTS_DIR
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    import pandas as pd
    results, pred_dfs = [], []

    if args.linear or run_all:
        from src.models.linear import train_ridge, train_lasso
        _, m, p = train_ridge(df);  results.append(m); pred_dfs.append(p)
        _, m, p = train_lasso(df);  results.append(m); pred_dfs.append(p)

    if args.tree or run_all:
        from src.models.tree import train_random_forest, train_xgboost
        _, m, p = train_random_forest(df); results.append(m); pred_dfs.append(p)
        _, m, p = train_xgboost(df);       results.append(m); pred_dfs.append(p)

    if args.ts or run_all:
        from src.models.timeseries import train_arima, train_prophet
        _, m, p = train_arima(df);   results.append(m); pred_dfs.append(p)
        _, m, p = train_prophet(df); results.append(m); pred_dfs.append(p)

    if results:
        comp = pd.DataFrame(results)[["model_name", "RMSE", "MAE", "R2"]]
        print("\n=== Leaderboard ===")
        print(comp.sort_values("RMSE").to_string(index=False))


if __name__ == "__main__":
    main()
