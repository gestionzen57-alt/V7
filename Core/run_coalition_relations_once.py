#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V6 - run_coalition_relations_once.py
Version: V0.3

Mission:
    Finalize the coalition/relation readout layer.

    Read zone_diagnostics, reconstruct z_current slope/curvature from history,
    detect currency coalitions, qualify coalition-vs-antagonist relations, and
    split output into:
        1) ACTIVE RELATIONS
        2) STRONG COALITIONS WITHOUT ACTIVE ANTAGONIST
        3) WEAK / HIDDEN FIELD NOISE

Doctrine:
    - Read-only runner.
    - Does not write DB.
    - Does not compute force_snapshots.
    - Does not alert Telegram.
    - Does not detect temporal nodes.
    - Active temporal window remains a future module.
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

DEFAULT_MIN_FIELD_SCORE = 0.45
DEFAULT_STRONG_COALITION_COHESION = 0.75


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


def split_field_readout(
    coalitions: Sequence[Any],
    relations: Sequence[Any],
    *,
    min_field_score: float = DEFAULT_MIN_FIELD_SCORE,
    strong_cohesion: float = DEFAULT_STRONG_COALITION_COHESION,
) -> Dict[str, Any]:
    active_relations = [r for r in relations if r.field_score >= min_field_score]
    weak_relations = [r for r in relations if r.field_score < min_field_score]

    active_relation_coalitions = {r.coalition_id for r in active_relations}

    strong_coalitions = [
        c for c in coalitions
        if c.cohesion >= strong_cohesion and c.coalition_id not in active_relation_coalitions
    ]

    return {
        "active_relations": active_relations,
        "strong_coalitions": strong_coalitions,
        "weak_relations": weak_relations,
    }


def cockpit_sentence_from_split(split: Mapping[str, Any], time_key: Optional[str] = None) -> str:
    prefix = f"{time_key} — " if time_key else ""

    active = split["active_relations"]
    if active:
        best = active[0]
        members = "+".join(best.coalition_members)
        return (
            f"{prefix}RELATION ACTIVE: {members} vs {best.antagonist} — "
            f"{best.field_state} ({best.relation_type}), phase={best.phase}, score={best.field_score:.2f}"
        )

    strong = split["strong_coalitions"]
    if strong:
        best = strong[0]
        members = "+".join(best.members)
        ants = "+".join(best.antagonist_candidates) if best.antagonist_candidates else "-"
        return (
            f"{prefix}COALITION FORTE: {members} — {best.state}, "
            f"phase={best.phase}, cohesion={best.cohesion:.2f}, antagonists={ants}"
        )

    return f"{prefix}Aucun champ coalition utile au seuil courant."


def compact_coalition_line(c: Any) -> str:
    ant = "+".join(c.antagonist_candidates) if c.antagonist_candidates else "-"
    return (
        f"{'+'.join(c.members)}: {c.state} | phase={c.phase} | "
        f"cohesion={c.cohesion:.2f} | z={c.z_mean:+.2f} | "
        f"slope={c.slope_mean:+.2f} | leader={c.leader} | antagonist={ant}"
    )


def compact_relation_line(r: Any) -> str:
    return (
        f"{'+'.join(r.coalition_members)} vs {r.antagonist}: "
        f"{r.relation_type} | field={r.field_state} | "
        f"score={r.field_score:.2f} | phase={r.phase}"
    )


def run_latest(
    db_path: str,
    *,
    timeframe: Optional[int],
    symbol: Optional[str],
    currencies: Optional[Sequence[str]],
    lookback_rows: int,
    slope_lag: int,
    min_field_score: float = DEFAULT_MIN_FIELD_SCORE,
    strong_cohesion: float = DEFAULT_STRONG_COALITION_COHESION,
) -> Dict[str, Any]:
    rows = load_rows(db_path, timeframe=timeframe, symbol=symbol, currencies=currencies, lookback_rows=lookback_rows)
    time_key = latest_time(rows)

    vectors: List[Dict[str, Any]] = []
    coalitions: List[Any] = []
    relations: List[Any] = []
    split = {"active_relations": [], "strong_coalitions": [], "weak_relations": []}

    if time_key:
        vectors = build_vectors_for_time(rows, time_key=time_key, slope_lag=slope_lag)
        coalitions, relations = analyze_vectors(vectors)
        split = split_field_readout(
            coalitions,
            relations,
            min_field_score=min_field_score,
            strong_cohesion=strong_cohesion,
        )

    active_relations = split["active_relations"]
    strong_coalitions = split["strong_coalitions"]
    weak_relations = split["weak_relations"]

    return {
        "module": "run_coalition_relations_once",
        "version": "V0.3",
        "mode": "latest",
        "db": db_path,
        "timeframe": timeframe,
        "symbol": symbol,
        "time_key": time_key,
        "thresholds": {
            "min_field_score": min_field_score,
            "strong_cohesion": strong_cohesion,
        },
        "currency_count": len(vectors),
        "coalition_count": len(coalitions),
        "relation_count": len(relations),
        "active_relation_count": len(active_relations),
        "strong_coalition_count": len(strong_coalitions),
        "weak_relation_count": len(weak_relations),
        "vectors": vectors,
        "coalitions": coalitions_to_dict(coalitions),
        "relations": relations_to_dict(relations),
        "active_relations": relations_to_dict(active_relations),
        "strong_coalitions": coalitions_to_dict(strong_coalitions),
        "weak_relations": relations_to_dict(weak_relations),
        "cockpit_sentence": cockpit_sentence_from_split(split, time_key),
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
    strong_cohesion: float,
) -> Dict[str, Any]:
    rows = load_rows(db_path, timeframe=timeframe, symbol=symbol, currencies=currencies, lookback_rows=lookback_rows)
    times = unique_times(rows)[-max(1, int(scan)):]

    active_windows: List[Dict[str, Any]] = []
    strong_coalition_windows: List[Dict[str, Any]] = []
    hidden_weak_relation_windows: List[Dict[str, Any]] = []

    for time_key in times:
        vectors = build_vectors_for_time(rows, time_key=time_key, slope_lag=slope_lag)
        coalitions, relations = analyze_vectors(vectors)
        split = split_field_readout(
            coalitions,
            relations,
            min_field_score=min_field_score,
            strong_cohesion=strong_cohesion,
        )

        if split["active_relations"]:
            best = split["active_relations"][0]
            active_windows.append({
                "time_key": time_key,
                "best_score": best.field_score,
                "vectors": vectors,
                "active_relations": relations_to_dict(split["active_relations"]),
                "strong_coalitions": coalitions_to_dict(split["strong_coalitions"]),
                "cockpit_sentence": cockpit_sentence_from_split(split, time_key),
            })
        elif split["strong_coalitions"]:
            best_c = split["strong_coalitions"][0]
            strong_coalition_windows.append({
                "time_key": time_key,
                "best_cohesion": best_c.cohesion,
                "vectors": vectors,
                "strong_coalitions": coalitions_to_dict(split["strong_coalitions"]),
                "cockpit_sentence": cockpit_sentence_from_split(split, time_key),
            })
        elif split["weak_relations"]:
            best_w = split["weak_relations"][0]
            hidden_weak_relation_windows.append({
                "time_key": time_key,
                "best_score": best_w.field_score,
                "weak_relations": relations_to_dict(split["weak_relations"]),
            })

    active_windows.sort(key=lambda item: item["best_score"], reverse=True)
    strong_coalition_windows.sort(key=lambda item: item["best_cohesion"], reverse=True)
    hidden_weak_relation_windows.sort(key=lambda item: item["best_score"], reverse=True)

    return {
        "module": "run_coalition_relations_once",
        "version": "V0.3",
        "mode": "scan",
        "db": db_path,
        "timeframe": timeframe,
        "symbol": symbol,
        "scan": scan,
        "thresholds": {
            "min_field_score": min_field_score,
            "strong_cohesion": strong_cohesion,
        },
        "active_window_count": len(active_windows),
        "strong_coalition_window_count": len(strong_coalition_windows),
        "hidden_weak_relation_count": len(hidden_weak_relation_windows),
        "active_windows": active_windows,
        "strong_coalition_windows": strong_coalition_windows,
        "hidden_weak_relation_windows": hidden_weak_relation_windows,
    }


def _print_vectors(vectors: Sequence[Mapping[str, Any]]) -> None:
    print("\nVectors:")
    for v in sorted(vectors, key=lambda item: item["currency"]):
        print(
            f"  {v['currency']:<3} z={float(v['z_basket']):+6.3f} "
            f"slope={float(v['slope']):+7.4f} curv={float(v['curvature']):+7.4f} "
            f"state={v.get('zone_state') or '-':<15} level={v.get('zone_level') or '-'}"
        )


def print_latest(payload: Mapping[str, Any], show_vectors: bool) -> None:
    print("PowerFlow Coalition Relations — latest V0.3")
    print("=" * 72)
    print(payload["cockpit_sentence"])

    if show_vectors:
        _print_vectors(payload["vectors"])

    print("\nRELATIONS ACTIVES")
    if payload["active_relations"]:
        for r in payload["active_relations"]:
            print(
                f"- {'+'.join(r['coalition_members'])} vs {r['antagonist']}: "
                f"{r['relation_type']} | field={r['field_state']} | "
                f"score={r['field_score']:.2f} | phase={r['phase']}"
            )
    else:
        print("- aucune")

    print("\nCOALITIONS FORTES SANS RELATION ACTIVE")
    if payload["strong_coalitions"]:
        for c in payload["strong_coalitions"]:
            ant = "+".join(c["antagonist_candidates"]) if c["antagonist_candidates"] else "-"
            print(
                f"- {'+'.join(c['members'])}: {c['state']} | phase={c['phase']} | "
                f"cohesion={c['cohesion']:.2f} | z={c['z_mean']:+.2f} | "
                f"slope={c['slope_mean']:+.2f} | antagonist={ant}"
            )
    else:
        print("- aucune")

    print("\nBRUIT / RELATIONS FAIBLES")
    if payload["weak_relations"]:
        for r in payload["weak_relations"][:5]:
            print(
                f"- {'+'.join(r['coalition_members'])} vs {r['antagonist']}: "
                f"{r['relation_type']} | score={r['field_score']:.2f}"
            )
    else:
        print("- aucun")


def print_scan(payload: Mapping[str, Any]) -> None:
    print("PowerFlow Coalition Relations — scan V0.3")
    print("=" * 72)

    print("\nRELATIONS ACTIVES")
    if payload["active_windows"]:
        for idx, window in enumerate(payload["active_windows"][:20], start=1):
            print(f"{idx:02d}. {window['cockpit_sentence']}")
    else:
        print("- aucune")

    print("\nCOALITIONS FORTES SANS RELATION ACTIVE")
    if payload["strong_coalition_windows"]:
        for idx, window in enumerate(payload["strong_coalition_windows"][:20], start=1):
            print(f"{idx:02d}. {window['cockpit_sentence']}")
    else:
        print("- aucune")

    print("\nBRUIT MASQUÉ")
    print(f"- relations faibles masquées: {payload['hidden_weak_relation_count']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Read zone_diagnostics and separate active relations from strong coalitions.")
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--timeframe", type=int, default=None)
    parser.add_argument("--symbol", default=None)
    parser.add_argument("--currencies", default=",".join(DEFAULT_CURRENCIES))
    parser.add_argument("--lookback-rows", type=int, default=DEFAULT_LOOKBACK_ROWS)
    parser.add_argument("--slope-lag", type=int, default=DEFAULT_SLOPE_LAG)
    parser.add_argument("--scan", type=int, default=0)
    parser.add_argument("--min-field-score", type=float, default=DEFAULT_MIN_FIELD_SCORE)
    parser.add_argument("--strong-cohesion", type=float, default=DEFAULT_STRONG_COALITION_COHESION)
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
            strong_cohesion=args.strong_cohesion,
        )
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print_scan(payload)
        return 0

    payload = run_latest(
        args.db,
        timeframe=args.timeframe,
        symbol=args.symbol,
        currencies=currencies,
        lookback_rows=args.lookback_rows,
        slope_lag=args.slope_lag,
        min_field_score=args.min_field_score,
        strong_cohesion=args.strong_cohesion,
    )

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_latest(payload, args.vectors)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
