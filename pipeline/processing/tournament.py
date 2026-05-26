"""Compute legend-level tournament metrics from raw riftboundstats deck data.

Methodology (Option B):
  - Deck card compositions are not exposed by the API.
  - Instead, we compute per-legend per-week play/top8 rates from deck metadata.
  - Legends share domains with non-legend cards; domain is the join key to cards.
  - When multiple legends share a domain, we take the MAX rate (peak pressure wins).

Output: data/processed/tournament_features.csv
Columns: domain, week, legend_play_rate, legend_top8_rate
"""
import json
import re
from pathlib import Path

import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import RAW_DIR, PROCESSED_DIR

_STATS_DIR = RAW_DIR / "riftboundstats"

TOP8_THRESHOLD = 8


def _latest_file(prefix: str) -> Path:
    matches = sorted(_STATS_DIR.glob(f"*_{prefix}.json"), reverse=True)
    if not matches:
        raise FileNotFoundError(f"No raw file matching *_{prefix}.json in {_STATS_DIR}")
    return matches[0]


def _load(prefix: str) -> list[dict]:
    path = _latest_file(prefix)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _strip_champion_prefix(name: str) -> str:
    """'Draven, Glorious Executioner' → 'Glorious Executioner'; 'Battle Mistress' → 'Battle Mistress'."""
    return re.sub(r"^[^,]+,\s*", "", name).strip()


def _build_legend_domain_map(legend_cards: list[dict]) -> dict[str, str]:
    """Normalized short-name (lowercase) → domain, from legend card catalog."""
    mapping: dict[str, str] = {}
    for card in legend_cards:
        key = card["name"].lower()
        if key not in mapping:
            mapping[key] = card["domain"]
    return mapping


def build_tournament_features() -> pd.DataFrame:
    decks = _load("decks")
    legend_cards = _load("legend_cards")

    legend_domain = _build_legend_domain_map(legend_cards)

    df = pd.DataFrame(decks)

    # Derive ISO week start (Monday) from created_at
    created = pd.to_datetime(df["created_at"], utc=True)
    df["week"] = (created - pd.to_timedelta(created.dt.dayofweek, unit="D")).dt.strftime("%Y-%m-%d")

    # Normalize legend name to short form, then look up domain
    df["legend_short"] = df["legend"].apply(_strip_champion_prefix)
    df["domain"] = df["legend_short"].str.lower().map(legend_domain)

    unmapped = df[df["domain"].isna()]["legend"].unique()
    if len(unmapped):
        print(f"[tournament] WARNING: {len(unmapped)} legend name(s) not mapped to domain:")
        for name in sorted(unmapped):
            short = _strip_champion_prefix(name)
            print(f"  '{name}' → short='{short}' → not in legend catalog")

    df = df.dropna(subset=["domain"])

    df["is_top8"] = df["best_placement"].notna() & (df["best_placement"] <= TOP8_THRESHOLD)

    # Weekly totals (denominator for rates)
    weekly_totals = df.groupby("week")["id"].count().rename("total_decks")
    weekly_top8 = df[df["is_top8"]].groupby("week")["id"].count().rename("total_top8")

    # Per-legend-per-week counts
    legend_week = (
        df.groupby(["domain", "week", "legend_short"])
        .agg(appearances=("id", "count"), top8_appearances=("is_top8", "sum"))
        .reset_index()
        .join(weekly_totals, on="week")
        .join(weekly_top8, on="week")
    )

    legend_week["total_top8"] = legend_week["total_top8"].fillna(0)
    legend_week["legend_play_rate"] = legend_week["appearances"] / legend_week["total_decks"]
    legend_week["legend_top8_rate"] = legend_week["top8_appearances"] / legend_week["total_top8"].clip(lower=1)

    # Split compound legend domains (e.g. 'Fury|Chaos' -> ['Fury', 'Chaos'])
    # so that single-domain cards (from cards.json) can join on their own domain.
    # A Fury|Chaos legend contributes play pressure to BOTH Fury and Chaos cards.
    exploded = legend_week.copy()
    exploded["domain"] = exploded["domain"].str.split("|")
    exploded = exploded.explode("domain")

    # Aggregate to single-domain level — max across all legends touching that domain
    domain_week = (
        exploded.groupby(["domain", "week"])
        .agg(
            legend_play_rate=("legend_play_rate", "max"),
            legend_top8_rate=("legend_top8_rate", "max"),
        )
        .reset_index()
    )

    domain_week = domain_week.sort_values(["domain", "week"]).reset_index(drop=True)
    domain_week[["legend_play_rate", "legend_top8_rate"]] = (
        domain_week[["legend_play_rate", "legend_top8_rate"]].round(4)
    )

    return domain_week


def save_tournament_features() -> pd.DataFrame:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df = build_tournament_features()
    out = PROCESSED_DIR / "tournament_features.csv"
    df.to_csv(out, index=False)
    print(f"[tournament] Saved {out.name} — {df.shape[0]} rows, {df['domain'].nunique()} domains, {df['week'].nunique()} weeks")
    print(df.groupby("domain")[["legend_play_rate", "legend_top8_rate"]].mean().round(4).to_string())
    return df


if __name__ == "__main__":
    save_tournament_features()
