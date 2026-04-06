"""
Analytical SQL queries against the Riftbound SQLite database.

Each function returns a list of sqlite3.Row objects and prints a formatted
result table. Demonstrates: CTEs, window functions (LAG, AVG OVER, RANK),
multi-table JOINs, conditional aggregation, and HAVING filters.

Usage:
  from src.database.queries import run_all
  run_all()
"""
import sqlite3
from pathlib import Path
from typing import Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import DB_PATH


# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

def _connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(
            f"Database not found at {db_path}. Run `python run_db.py` first."
        )
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _print_table(title: str, rows: list[sqlite3.Row], max_rows: int = 15) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")
    if not rows:
        print("  (no results)")
        return
    keys = rows[0].keys()
    col_w = {k: max(len(k), max(len(str(r[k] or "")) for r in rows[:max_rows])) for k in keys}
    header = "  " + "  ".join(k.ljust(col_w[k]) for k in keys)
    sep    = "  " + "  ".join("-" * col_w[k] for k in keys)
    print(header)
    print(sep)
    for row in rows[:max_rows]:
        print("  " + "  ".join(str(row[k] or "").ljust(col_w[k]) for k in keys))
    if len(rows) > max_rows:
        print(f"  ... ({len(rows) - max_rows} more rows)")


# ---------------------------------------------------------------------------
# Query 1 — Weekly price trend with week-over-week delta (window: LAG)
# ---------------------------------------------------------------------------

QUERY_WEEKLY_TREND = """
WITH weekly_avg AS (
    SELECT
        card_name,
        week,
        ROUND(AVG(market_price), 4)  AS avg_price,
        SUM(qty_sold)                AS total_qty
    FROM price_history
    GROUP BY card_name, week
)
SELECT
    card_name,
    week,
    avg_price,
    total_qty,
    ROUND(
        avg_price - LAG(avg_price) OVER (PARTITION BY card_name ORDER BY week),
        4
    ) AS price_delta,
    ROUND(
        100.0 * (avg_price - LAG(avg_price) OVER (PARTITION BY card_name ORDER BY week))
              / NULLIF(LAG(avg_price) OVER (PARTITION BY card_name ORDER BY week), 0),
        2
    ) AS pct_change
FROM weekly_avg
ORDER BY card_name, week;
"""


def weekly_price_trend(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    rows = conn.execute(QUERY_WEEKLY_TREND).fetchall()
    _print_table("Weekly Price Trend — LAG window (price_delta, pct_change)", rows)
    return rows


# ---------------------------------------------------------------------------
# Query 2 — Most volatile cards by price standard deviation
# ---------------------------------------------------------------------------

QUERY_VOLATILITY = """
WITH weekly_avg AS (
    SELECT
        card_name,
        week,
        AVG(market_price) AS avg_price
    FROM price_history
    GROUP BY card_name, week
),
stats AS (
    SELECT
        card_name,
        COUNT(week)                                         AS weeks_tracked,
        ROUND(AVG(avg_price), 4)                           AS mean_price,
        ROUND(MAX(avg_price) - MIN(avg_price), 4)          AS price_range,
        ROUND(
            SQRT(AVG(avg_price * avg_price) - AVG(avg_price) * AVG(avg_price)),
            4
        )                                                  AS price_stddev
    FROM weekly_avg
    GROUP BY card_name
    HAVING weeks_tracked >= 3
)
SELECT
    card_name,
    weeks_tracked,
    mean_price,
    price_range,
    price_stddev,
    RANK() OVER (ORDER BY price_stddev DESC) AS volatility_rank
FROM stats
ORDER BY volatility_rank
LIMIT 20;
"""


def most_volatile_cards(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    rows = conn.execute(QUERY_VOLATILITY).fetchall()
    _print_table("Most Volatile Cards — Stddev + RANK window", rows)
    return rows


# ---------------------------------------------------------------------------
# Query 3 — Legend meta share by week (deck play rate via CTE + JOIN)
# ---------------------------------------------------------------------------

QUERY_META_SHARE = """
WITH weekly_totals AS (
    SELECT
        STRFTIME('%Y-%m-%d', DATE(created_at, 'weekday 0', '-6 days')) AS week,
        COUNT(*) AS total_decks
    FROM decks
    GROUP BY week
),
legend_counts AS (
    SELECT
        STRFTIME('%Y-%m-%d', DATE(created_at, 'weekday 0', '-6 days')) AS week,
        legend,
        COUNT(*) AS deck_count,
        SUM(CASE WHEN best_placement IS NOT NULL AND best_placement <= 8 THEN 1 ELSE 0 END) AS top8_count
    FROM decks
    GROUP BY week, legend
),
ranked AS (
    SELECT
        lc.week,
        lc.legend,
        lc.deck_count,
        wt.total_decks,
        ROUND(100.0 * lc.deck_count / wt.total_decks, 2)            AS play_rate_pct,
        lc.top8_count,
        ROUND(100.0 * lc.top8_count / NULLIF(lc.deck_count, 0), 2)  AS top8_conversion_pct,
        RANK() OVER (PARTITION BY lc.week ORDER BY lc.deck_count DESC) AS rank_in_week
    FROM legend_counts lc
    JOIN weekly_totals wt ON lc.week = wt.week
)
SELECT * FROM ranked
WHERE rank_in_week <= 5
ORDER BY week DESC, rank_in_week;
"""


def legend_meta_share(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    rows = conn.execute(QUERY_META_SHARE).fetchall()
    _print_table("Top 5 Legends per Week — Meta Share + Top8 Conversion (CTE + RANK)", rows)
    return rows


# ---------------------------------------------------------------------------
# Query 4 — Cards rising in price AND in tournament play rate (JOIN + filter)
# ---------------------------------------------------------------------------

QUERY_BIGGEST_MOVERS = """
WITH weekly_avg AS (
    SELECT
        card_name,
        week,
        AVG(market_price) AS avg_price,
        SUM(qty_sold)     AS weekly_qty
    FROM price_history
    GROUP BY card_name, week
),
with_delta AS (
    SELECT
        card_name,
        week,
        ROUND(avg_price, 4) AS avg_price,
        weekly_qty,
        ROUND(
            avg_price - LAG(avg_price) OVER (PARTITION BY card_name ORDER BY week),
            4
        ) AS price_delta,
        ROUND(
            100.0 * (avg_price - LAG(avg_price) OVER (PARTITION BY card_name ORDER BY week))
                  / NULLIF(LAG(avg_price) OVER (PARTITION BY card_name ORDER BY week), 0),
            2
        ) AS pct_change
    FROM weekly_avg
),
ranked AS (
    SELECT
        *,
        RANK() OVER (PARTITION BY week ORDER BY ABS(price_delta) DESC) AS move_rank
    FROM with_delta
    WHERE price_delta IS NOT NULL
)
SELECT
    r.card_name,
    c.rarity,
    c.card_type,
    c.domain,
    r.week,
    r.avg_price,
    r.price_delta,
    r.pct_change,
    r.weekly_qty
FROM ranked r
JOIN cards c ON c.name = r.card_name
WHERE r.move_rank <= 3
ORDER BY r.week DESC, ABS(r.price_delta) DESC;
"""


def biggest_weekly_movers(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    rows = conn.execute(QUERY_BIGGEST_MOVERS).fetchall()
    _print_table("Biggest Weekly Price Movers — RANK per week + JOIN cards metadata", rows)
    return rows


# ---------------------------------------------------------------------------
# Query 5 — Tournament size trend over time with 4-week rolling average
# ---------------------------------------------------------------------------

QUERY_EVENT_TREND = """
WITH event_series AS (
    SELECT
        event_date,
        name,
        participant_count,
        event_type,
        AVG(participant_count) OVER (
            ORDER BY event_date
            ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
        ) AS rolling_avg_4
    FROM events
    WHERE status = 'completed'
      AND participant_count IS NOT NULL
)
SELECT
    event_date,
    name,
    participant_count,
    ROUND(rolling_avg_4, 1) AS rolling_avg_4_events,
    event_type
FROM event_series
ORDER BY event_date;
"""


def event_size_trend(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    rows = conn.execute(QUERY_EVENT_TREND).fetchall()
    _print_table("Tournament Size Trend — 4-event Rolling Average (ROWS BETWEEN window)", rows)
    return rows


# ---------------------------------------------------------------------------
# Query 6 — Rarity tier price summary (conditional aggregation)
# ---------------------------------------------------------------------------

QUERY_RARITY_SUMMARY = """
SELECT
    c.rarity,
    COUNT(DISTINCT c.name)                      AS card_count,
    ROUND(AVG(ph.market_price), 4)              AS avg_market_price,
    ROUND(MIN(ph.market_price), 4)              AS min_price,
    ROUND(MAX(ph.market_price), 4)              AS max_price,
    ROUND(SUM(ph.qty_sold), 0)                  AS total_qty_sold,
    ROUND(AVG(CASE WHEN ph.qty_sold > 0
                   THEN ph.market_price END), 4) AS avg_price_active_weeks
FROM cards c
JOIN price_history ph ON ph.product_id = c.product_id
GROUP BY c.rarity
ORDER BY avg_market_price DESC;
"""


def rarity_price_summary(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    rows = conn.execute(QUERY_RARITY_SUMMARY).fetchall()
    _print_table("Price Summary by Rarity — Conditional Aggregation + JOIN", rows)
    return rows


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_all(db_path: Path = DB_PATH) -> None:
    conn = _connect(db_path)
    try:
        weekly_price_trend(conn)
        most_volatile_cards(conn)
        legend_meta_share(conn)
        biggest_weekly_movers(conn)
        event_size_trend(conn)
        rarity_price_summary(conn)
    finally:
        conn.close()
    print(f"\n[queries] All queries complete.")


if __name__ == "__main__":
    run_all()
