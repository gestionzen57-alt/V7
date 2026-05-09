#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V6 - run_coalition_relations_once.py
Version: V0.2

Read zone_diagnostics, reconstruct z_current slope/curvature from history,
detect coalitions, qualify coalition-vs-antagonist relations.

Read-only. No DB writes. No Telegram.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import defaultdict
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from pf_coalitions import detect_currency_coalitions, coalitions_to_dict
from pf_coalition_relations import qualify_coalition_relations, relations_to_dict


DEFAULT_CURRENCIES = ["USD", "GBP", "EUR", "JPY", "CAD", "CHF", "AUD"]
DEFAULT_LOOKBACK_ROWS = 1200
DEFAULT_SLOPE_LAG = 1


def parse_csv(value: Optional[str]) -> Optional[List[str]]:
    if not value:
        return None
    return [x.strip().upper() for x in value.split(",") if x.strip()]


def _json_loads(value: Any, default: Any) -> Any:
    if value in (None, ""):
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _row_time_key(row: sqlite3.Row) -> str:
    return str(row["source_created_at"] or row["logged_at"] or "")


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone()
    return row is not None


def fetch_zone_rows(
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
    return list(reversed(conn.execute(sql, params).fetchall()))


def load_rows(
    db_path: str,
    *,
    timeframe: Optional[int] = None,
    symbol: Optional[str] = None,
    currencies: Optional[Sequence[str]] = None,
    lookback_rows: int = DEFAULT_LOOKBACK_ROWS,
) -> List[sqlite3.Row]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        if not table_exists(conn, "zone_diagnostics"):
            raise RuntimeError("zone_diagnostics table not found. Run run_zone_context_logger_once.py first.")
        return fetch_zone_rows(
            conn,
            timeframe=timeframe,
            symbol=symbol,
            currencies=currencies,
            lookback_rows=lookback_rows,
        )
    finally:
        conn.close()


def unique_times(rows: Sequence[sqlite3.Row]) -> List[str]:
    out: List[str] = []
    seen = set()
    for row in rows:
        key = _row_time_key(row)
        if key and key not in seen:
            seen.add(key)
            out.append(key)
    return out


def latest_time(rows: Sequence[sqlite3.Row]) -> Optional[str]:
    times = unique_times(rows)
    return times[-1] if times else None


def history_by_currency(rows: Sequence[sqlite3.Row]) -> Dict[str, List[sqlite3.Row]]:
    hist: Dict[str, List[sqlite3.Row]] = defaultdict(list)
    for row in rows:
        hist[str(row["currency"]).upper()].append(row)
    return hist


def _row_before_or_at(hist: Sequence[sqlite3.Row], time_key: str) -> Optional[sqlite3.Row]:
    chosen: Optional[sqlite3.Row] = None
    for row in hist:
        key = _row_time_key(row)
        if key <= time_key:
            chosen = row
        else:
            break
    return chosen


def _last_n_before_or_at(hist: Sequence[sqlite3.Row], time_key: str, n: int) -> List[sqlite3.Row]:
    out: List[sqlite3.Row] = []
    for row in hist:
        key = _row_time_key(row)
        if key <= time_key:
            out.append(row)
        else:
            break
    return out[-n:]


def _derive_slope_curvature(hist: Sequence[sqlite3.Row], time_key: str, slope_lag: int) -> Tuple[float, float]:
    lag = max(1, int(slope_lag))
    recent = _last_n_before_or_at(hist, time_key, max(3, lag + 2))
    z = [_safe_float(row["z_current"]) for row in recent]
    if len(z) < 2:
        return 0.0, 0.0

    if len(z) > lag:
        slope_now = (z[-1] - z[-1 - lag]) / lag
    else:
        slope_now = z[-1] - z[-2]

    if len(z) <= lag + 1:
        return round(slope_now, 4), 0.0

    prev_end = len(z) - 2
    prev_start = max(0, prev_end - lag)
    denom = max(1, prev_end - prev_start)
    slope_prev = (z[prev_end] - z[prev_start]) / denom
    return round(slope_now, 4), round(slope_now - slope_prev, 4)


def build_vector_from_row(row: sqlite3.Row, *, slope: float, curvature: float) -> Dict[str, Any]:
    tags = _json_loads(row["context_tags_json"], [])
    raw = _json_loads(row["raw_diagnosis_json"], {})
    return {
        "currency": str(row["currency"]).upper(),
        "z_basket": _safe_float(row["z_current"]),
        "slope": slope,
        "curvature": curvature,
        "phase": raw.get("phase", row["state"]),
        "quality": raw.get("quality", "FROM_ZONE_DIAGNOSTIC"),
        "zone_state": row["state"],
        "zone_level": row["zone_level"],
        "context_score": _safe_float(row["context_score"]),
        "context_tags": tags,
        "timeframe": row["timeframe"],
        "symbol": row["symbol"],
        "source_created_at": row["source_created_at"],
    }


def build_vectors_for_time(rows: Sequence[sqlite3.Row], *, time_key: str, slope_lag: int = DEFAULT_SLOPE_LAG) -> List[Dict[str, Any]]:
    hist = history_by_currency(rows)
    vectors: List[Dict[str, Any]] = []
    for currency in sorted(hist.keys()):
        row = _row_before_or_at(hist[currency], time_key)
        if row is None:
            continue
        slope, curvature = _derive_slope_curvature(hist[currency], time_key, slope_lag)
        vectors.append(build_vector_from_row(row, slope=slope, curvature=curvature))
    return vectors


def analyze_vectors(vectors: Sequence[Mapping[str, Any]]) -> Tuple[List[Any], List[Any]]:
    coalitions = detect_currency_coalitions(vectors)
    relations = qualify_coalition_relations(coalitions, vectors)
    return coalitions, relations


def cockpit_sentence(relations: Sequence[Any], coalitions: Sequence[Any], time_key: Optional[str] = None) -> str:
    prefix = f"{time_key} — " if time_key else ""
    if relations:
        best = relations[0]
        members = "+".join(best.coalition_members)
        return f"{prefix}{members} vs {best.antagonist} — {best.field_state} ({best.relation_type}), phase={best.phase}, score={best.field_score:.2f}"
    if coalitions:
        best = coalitions[0]
        members = "+".join(best.members)
        ants = "+".join(best.antagonist_candidates) if best.antagonist_candidates else "-"
        return f"{prefix}{members} — {best.state}, phase={best.phase}, cohesion={best.cohesion:.2f}, antagonists={ants}"
    return f"{prefix}Aucune coalition active lisible sur les diagnostics."


def run_latest(
    db_path: str,
    *,
    timeframe: Optional[int],
    symbol: Optional[str],
    currencies: Optional[Sequence[str]],
    lookback_rows: int,
    slope_lag: int,
) -> Dict[str, Any]:
    rows = load_rows(db_path, timeframe=timeframe, symbol=symbol, currencies=currencies, lookback_rows=lookback_rows)
    time_key = latest_time(rows)
    vectors: List[Dict[str, Any]] = []
    coalitions: List[Any] = []
    relations: List[Any] = []
    if time_key:
        vectors = build_vectors_for_time(rows, time_key=time_key, slope_lag=slope_lag)
        coalitions, relations = analyze_vectors(vectors)

    return {
        "module": "run_coalition_relations_once",
        "version": "V0.2",
        "mode": "latest",
        "db": db_path,
        "timeframe": timeframe,
        "symbol": symbol,
        "time_key": time_key,
        "currency_count": len(vectors),
        "coalition_count": len(coalitions),
        "relation_count": len(relations),
        "vectors": vectors,
        "coalitions": coalitions_to_dict(coalitions),
        "relations": relations_to_dict(relations),
        "cockpit_sentence": cockpit_sentence(relations, coalitions, time_key),
    }


def run_scan(
    db_path: str,
    *,
    timeframe: Optional[int],
    symbol: Optional[str],
    currencies: Optional[Sequence[str]],
    lookback_rows: int,
    slope_lag: int,
    scan: int,
    min_field_score: float,
) -> Dict[str, Any]:
    rows = load_rows(db_path, timeframe=timeframe, symbol=symbol, currencies=currencies, lookback_rows=lookback_rows)
    times = unique_times(rows)[-max(1, int(scan)):]
    windows: List[Dict[str, Any]] = []

    for time_key in times:
        vectors = build_vectors_for_time(rows, time_key=time_key, slope_lag=slope_lag)
        coalitions, relations = analyze_vectors(vectors)
        best_score = relations[0].field_score if relations else 0.0
        if relations and best_score < min_field_score:
            continue
        if coalitions or relations:
            windows.append({
                "time_key": time_key,
                "vectors": vectors,
                "coalitions": coalitions_to_dict(coalitions),
                "relations": relations_to_dict(relations),
                "cockpit_sentence": cockpit_sentence(relations, coalitions, time_key),
                "best_field_score": best_score,
            })

    windows.sort(key=lambda item: item["best_field_score"], reverse=True)
    return {
        "module": "run_coalition_relations_once",
        "version": "V0.2",
        "mode": "scan",
        "db": db_path,
        "timeframe": timeframe,
        "symbol": symbol,
        "scan": scan,
        "window_count": len(windows),
        "windows": windows,
    }


def _print_vectors(vectors: Sequence[Mapping[str, Any]]) -> None:
    print("\nVectors:")
    for v in sorted(vectors, key=lambda item: item["currency"]):
        print(
            f"  {v['currency']:<3} z={float(v['z_basket']):+6.3f} "
            f"slope={float(v['slope']):+7.4f} curv={float(v['curvature']):+7.4f} "
            f"state={v.get('zone_state') or '-':<15} level={v.get('zone_level') or '-'}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Read zone_diagnostics and detect coalition relations.")
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--timeframe", type=int, default=None)
    parser.add_argument("--symbol", default=None)
    parser.add_argument("--currencies", default=",".join(DEFAULT_CURRENCIES))
    parser.add_argument("--lookback-rows", type=int, default=DEFAULT_LOOKBACK_ROWS)
    parser.add_argument("--slope-lag", type=int, default=DEFAULT_SLOPE_LAG)
    parser.add_argument("--scan", type=int, default=0)
    parser.add_argument("--min-field-score", type=float, default=0.0)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--vectors", action="store_true")
    args = parser.parse_args()

    currencies = parse_csv(args.currencies)

    if args.scan and args.scan > 0:
        payload = run_scan(
            args.db,
            timeframe=args.timeframe,
            symbol=args.symbol,
            currencies=currencies,
            lookback_rows=args.lookback_rows,
            slope_lag=args.slope_lag,
            scan=args.scan,
            min_field_score=args.min_field_score,
        )
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0
        print("PowerFlow Coalition Relations — scan")
        print("=" * 72)
        if not payload["windows"]:
            print("Aucune fenêtre coalition/relation trouvée dans le scan.")
            return 0
        for idx, window in enumerate(payload["windows"][:20], start=1):
            print(f"{idx:02d}. {window['cockpit_sentence']}")
        return 0

    payload = run_latest(
        args.db,
        timeframe=args.timeframe,
        symbol=args.symbol,
        currencies=currencies,
        lookback_rows=args.lookback_rows,
        slope_lag=args.slope_lag,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print("PowerFlow Coalition Relations — latest")
    print("=" * 72)
    print(payload["cockpit_sentence"])
    if args.vectors:
        _print_vectors(payload["vectors"])

    print("\nCoalitions:")
    if payload["coalitions"]:
        for c in payload["coalitions"]:
            ant = "+".join(c["antagonist_candidates"]) if c["antagonist_candidates"] else "-"
            print(
                f"{'+'.join(c['members'])}: {c['state']} | phase={c['phase']} | "
                f"cohesion={c['cohesion']:.2f} | z={c['z_mean']:+.2f} | "
                f"slope={c['slope_mean']:+.2f} | leader={c['leader']} | antagonist={ant}"
            )
    else:
        print("No active currency coalition.")

    print("\nRelations:")
    if payload["relations"]:
        for r in payload["relations"]:
            print(
                f"{'+'.join(r['coalition_members'])} vs {r['antagonist']}: "
                f"{r['relation_type']} | field={r['field_state']} | "
                f"score={r['field_score']:.2f} | phase={r['phase']}"
            )
    else:
        print("No active coalition relation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
