#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V6 - run_coalition_relations_once.py
Version: V0.1

Mission:
    Read latest zone_diagnostics from powerflow.db, build currency vectors,
    detect synchronized currency coalitions, then qualify coalition-vs-antagonist
    relations.

Doctrine:
    - Read-only runner.
    - Does not write DB.
    - Does not compute force snapshots.
    - Does not alert Telegram.
    - Gives a cockpit-like battlefield sentence from already logged zone context.

Requires:
    pf_coalitions.py
    pf_coalition_relations.py
    zone_diagnostics table from pf_zone_context_logger.py
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from pf_coalitions import detect_currency_coalitions, summarize_coalitions, coalitions_to_dict
from pf_coalition_relations import (
    qualify_coalition_relations,
    summarize_relations,
    relations_to_dict,
)


DEFAULT_CURRENCIES = ["USD", "GBP", "EUR", "JPY", "CAD", "CHF", "AUD"]
DEFAULT_LOOKBACK_ROWS = 200


def parse_csv(value: Optional[str]) -> Optional[List[str]]:
    if not value:
        return None
    return [x.strip().upper() for x in value.split(",") if x.strip()]


def parse_timeframes(value: Optional[str]) -> Optional[List[int]]:
    if not value:
        return None
    return [int(x.strip()) for x in value.split(",") if x.strip()]


def _json_loads(value: Any, default: Any) -> Any:
    if value in (None, ""):
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def fetch_latest_zone_rows(
    conn: sqlite3.Connection,
    *,
    timeframe: Optional[int] = None,
    symbol: Optional[str] = None,
    currencies: Optional[Sequence[str]] = None,
    lookback_rows: int = DEFAULT_LOOKBACK_ROWS,
) -> List[sqlite3.Row]:
    where: List[str] = []
    params: List[Any] = []

    if timeframe is not None:
        where.append("timeframe = ?")
        params.append(int(timeframe))

    if symbol:
        where.append("symbol = ?")
        params.append(symbol)

    if currencies:
        placeholders = ",".join("?" for _ in currencies)
        where.append(f"currency IN ({placeholders})")
        params.extend([c.upper() for c in currencies])

    sql = "SELECT * FROM zone_diagnostics"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY COALESCE(source_created_at, logged_at) DESC, id DESC LIMIT ?"
    params.append(int(lookback_rows))

    return conn.execute(sql, params).fetchall()


def latest_by_currency(rows: Sequence[sqlite3.Row]) -> Dict[str, sqlite3.Row]:
    """
    Keep the most recent row per currency.
    Rows are expected DESC by source/logged time.
    """
    out: Dict[str, sqlite3.Row] = {}
    for row in rows:
        cur = str(row["currency"]).upper()
        if cur not in out:
            out[cur] = row
    return out


def build_vector_from_zone_row(row: sqlite3.Row) -> Dict[str, Any]:
    tags = _json_loads(row["context_tags_json"], [])
    raw = _json_loads(row["raw_diagnosis_json"], {})

    # Zone diagnostics may not contain a direct slope from Personality.
    # For coalition timing, use depth_slope as a fallback respiratory slope.
    # If raw diagnosis later carries slope, that wins.
    slope = raw.get("slope", row["depth_slope"] or 0.0)
    curvature = raw.get("curvature", row["depth_acceleration"] or 0.0)

    # z_basket is represented by z_current in zone_diagnostics.
    return {
        "currency": str(row["currency"]).upper(),
        "z_basket": row["z_current"] or 0.0,
        "slope": slope or 0.0,
        "curvature": curvature or 0.0,
        "phase": raw.get("phase", row["state"]),
        "quality": raw.get("quality", "FROM_ZONE_DIAGNOSTIC"),
        "zone_state": row["state"],
        "zone_level": row["zone_level"],
        "context_score": row["context_score"] or 0.0,
        "context_tags": tags,
        "timeframe": row["timeframe"],
        "symbol": row["symbol"],
        "source_created_at": row["source_created_at"],
    }


def build_vectors_from_db(
    db_path: str,
    *,
    timeframe: Optional[int] = None,
    symbol: Optional[str] = None,
    currencies: Optional[Sequence[str]] = None,
    lookback_rows: int = DEFAULT_LOOKBACK_ROWS,
) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        if not table_exists(conn, "zone_diagnostics"):
            raise RuntimeError(
                "zone_diagnostics table not found. Run run_zone_context_logger_once.py first."
            )
        rows = fetch_latest_zone_rows(
            conn,
            timeframe=timeframe,
            symbol=symbol,
            currencies=currencies,
            lookback_rows=lookback_rows,
        )
        latest = latest_by_currency(rows)
        return [build_vector_from_zone_row(row) for _, row in sorted(latest.items())]
    finally:
        conn.close()


def cockpit_sentence(relations: Sequence[Any], coalitions: Sequence[Any]) -> str:
    if relations:
        best = relations[0]
        members = "+".join(best.coalition_members)
        return (
            f"{members} vs {best.antagonist} — {best.field_state} "
            f"({best.relation_type}), phase={best.phase}, score={best.field_score:.2f}"
        )

    if coalitions:
        best = coalitions[0]
        members = "+".join(best.members)
        return (
            f"{members} — {best.state}, phase={best.phase}, "
            f"cohesion={best.cohesion:.2f}, antagonists="
            f"{'+'.join(best.antagonist_candidates) if best.antagonist_candidates else '-'}"
        )

    return "Aucune coalition active lisible sur les derniers diagnostics."


def print_vectors(vectors: Sequence[Mapping[str, Any]]) -> None:
    print("\nVectors:")
    for v in sorted(vectors, key=lambda x: x["currency"]):
        print(
            f"  {v['currency']:<3} z={float(v['z_basket']):+6.3f} "
            f"slope={float(v['slope']):+7.4f} curv={float(v['curvature']):+7.4f} "
            f"state={v.get('zone_state') or '-':<15} level={v.get('zone_level') or '-'}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Read zone_diagnostics and detect coalition relations once.")
    parser.add_argument("--db", default="powerflow.db", help="Path to powerflow.db")
    parser.add_argument("--timeframe", type=int, default=None, help="Optional timeframe filter, e.g. 1,5,15")
    parser.add_argument("--symbol", default=None, help="Optional symbol filter, e.g. GBPUSD")
    parser.add_argument("--currencies", default=",".join(DEFAULT_CURRENCIES), help="Comma-separated currencies")
    parser.add_argument("--lookback-rows", type=int, default=DEFAULT_LOOKBACK_ROWS)
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    parser.add_argument("--vectors", action="store_true", help="Print currency vectors")
    args = parser.parse_args()

    currencies = parse_csv(args.currencies)

    vectors = build_vectors_from_db(
        args.db,
        timeframe=args.timeframe,
        symbol=args.symbol,
        currencies=currencies,
        lookback_rows=args.lookback_rows,
    )

    coalitions = detect_currency_coalitions(vectors)
    relations = qualify_coalition_relations(coalitions, vectors)

    payload = {
        "module": "run_coalition_relations_once",
        "version": "V0.1",
        "db": args.db,
        "timeframe": args.timeframe,
        "symbol": args.symbol,
        "currency_count": len(vectors),
        "coalition_count": len(coalitions),
        "relation_count": len(relations),
        "vectors": vectors,
        "coalitions": coalitions_to_dict(coalitions),
        "relations": relations_to_dict(relations),
        "cockpit_sentence": cockpit_sentence(relations, coalitions),
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("PowerFlow Coalition Relations — one-shot")
    print("=" * 72)
    print(payload["cockpit_sentence"])

    if args.vectors:
        print_vectors(vectors)

    print("\nCoalitions:")
    print(summarize_coalitions(coalitions))

    print("\nRelations:")
    print(summarize_relations(relations))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
