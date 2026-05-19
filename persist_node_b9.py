"""Persistence layer for PowerFlow V7.6.7 B9 terrain nodes.

This module is intentionally small and dependency-free. It owns only the
`nodes_b9` table and exposes read/write helpers for B9 node persistence.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

SCHEMA_NODES_B9 = """
CREATE TABLE IF NOT EXISTS nodes_b9 (
    node_id TEXT PRIMARY KEY,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    symbol TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    node_status TEXT,
    node_role TEXT,
    node_role_fr TEXT,
    zone_low REAL,
    zone_high REAL,
    center REAL,
    width_pips REAL,
    price_verdict TEXT,
    zone_role TEXT,
    data_visibility TEXT,
    confidence REAL,
    source_stack TEXT,
    requalified_event TEXT,
    b6_match_score INTEGER DEFAULT 0,
    b6_film_id TEXT,
    alert_sent INTEGER DEFAULT 0,
    node_json TEXT
);
"""

INDEXES_NODES_B9 = (
    "CREATE INDEX IF NOT EXISTS idx_nodes_b9_symbol_ts ON nodes_b9(symbol, timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_nodes_b9_verdict ON nodes_b9(price_verdict);",
)


def _json_dumps(value: Any) -> str | None:
    """Serialize any JSON-compatible value while preserving accents."""
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _as_text(value: Any) -> str | None:
    """Persist scalars as text and dict/list payloads as JSON text."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list, tuple)):
        return _json_dumps(value)
    return str(value)


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _connect(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True) if Path(db_path).parent != Path(".") else None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_nodes_b9_table(db_path: str = "powerflow.db") -> None:
    """Create the nodes_b9 table and indexes if they do not exist."""
    with _connect(db_path) as conn:
        conn.execute(SCHEMA_NODES_B9)
        for index_sql in INDEXES_NODES_B9:
            conn.execute(index_sql)
        conn.commit()


def persist_node_b9(
    node: dict,
    requalified: dict | None = None,
    b6_match: dict | None = None,
    alert_sent: bool = False,
    db_path: str = "powerflow.db",
) -> bool:
    """Insert or update a B9 node in SQLite.

    Args:
        node: Terrain node snapshot. Must include `node_id`, `symbol`, and `timestamp`.
        requalified: Optional packet requalification payload.
        b6_match: Optional B6 field-memory match payload.
        alert_sent: Whether a downstream alert was sent for this node.
        db_path: SQLite database path.

    Returns:
        True on success.

    Raises:
        ValueError: When required node fields are missing.
        sqlite3.Error: If SQLite cannot persist the row.
    """
    if not isinstance(node, dict):
        raise ValueError("node must be a dict")

    required = ("node_id", "symbol", "timestamp")
    missing = [key for key in required if not node.get(key)]
    if missing:
        raise ValueError(f"missing required node field(s): {', '.join(missing)}")

    init_nodes_b9_table(db_path)

    requalified_event = None
    if requalified:
        requalified_event = requalified.get("event") or requalified.get("requalified_event") or requalified.get("label")

    b6_match_score = 0
    b6_film_id = None
    if b6_match:
        b6_match_score = _as_int(b6_match.get("score", b6_match.get("match_score", 0)))
        b6_film_id = b6_match.get("film_id") or b6_match.get("b6_film_id")

    source_stack = node.get("source_stack")
    if source_stack is None and requalified:
        source_stack = requalified.get("source_stack")

    row = {
        "node_id": node["node_id"],
        "symbol": node["symbol"],
        "timestamp": node["timestamp"],
        "node_status": node.get("node_status") or node.get("status"),
        "node_role": node.get("node_role") or node.get("role"),
        "node_role_fr": node.get("node_role_fr") or node.get("role_fr"),
        "zone_low": _as_float(node.get("zone_low")),
        "zone_high": _as_float(node.get("zone_high")),
        "center": _as_float(node.get("center")),
        "width_pips": _as_float(node.get("width_pips")),
        "price_verdict": node.get("price_verdict"),
        "zone_role": node.get("zone_role"),
        "data_visibility": _as_text(node.get("data_visibility")),
        "confidence": _as_float(node.get("confidence")),
        "source_stack": _as_text(source_stack),
        "requalified_event": _as_text(requalified_event),
        "b6_match_score": b6_match_score,
        "b6_film_id": _as_text(b6_film_id),
        "alert_sent": 1 if alert_sent else 0,
        "node_json": _json_dumps({"node": node, "requalified": requalified, "b6_match": b6_match}),
    }

    sql = """
    INSERT INTO nodes_b9 (
        node_id, symbol, timestamp, node_status, node_role, node_role_fr,
        zone_low, zone_high, center, width_pips, price_verdict, zone_role,
        data_visibility, confidence, source_stack, requalified_event,
        b6_match_score, b6_film_id, alert_sent, node_json
    ) VALUES (
        :node_id, :symbol, :timestamp, :node_status, :node_role, :node_role_fr,
        :zone_low, :zone_high, :center, :width_pips, :price_verdict, :zone_role,
        :data_visibility, :confidence, :source_stack, :requalified_event,
        :b6_match_score, :b6_film_id, :alert_sent, :node_json
    )
    ON CONFLICT(node_id) DO UPDATE SET
        symbol = excluded.symbol,
        timestamp = excluded.timestamp,
        node_status = excluded.node_status,
        node_role = excluded.node_role,
        node_role_fr = excluded.node_role_fr,
        zone_low = excluded.zone_low,
        zone_high = excluded.zone_high,
        center = excluded.center,
        width_pips = excluded.width_pips,
        price_verdict = excluded.price_verdict,
        zone_role = excluded.zone_role,
        data_visibility = excluded.data_visibility,
        confidence = excluded.confidence,
        source_stack = excluded.source_stack,
        requalified_event = excluded.requalified_event,
        b6_match_score = excluded.b6_match_score,
        b6_film_id = excluded.b6_film_id,
        alert_sent = excluded.alert_sent,
        node_json = excluded.node_json;
    """

    with _connect(db_path) as conn:
        conn.execute(sql, row)
        conn.commit()
    return True


def get_recent_nodes_b9(
    symbol: str | None = None,
    verdict: str | None = None,
    limit: int = 20,
    db_path: str = "powerflow.db",
) -> list[dict]:
    """Read recent B9 nodes from the database."""
    init_nodes_b9_table(db_path)
    safe_limit = max(1, min(_as_int(limit, 20), 500))

    where: list[str] = []
    params: dict[str, Any] = {"limit": safe_limit}
    if symbol:
        where.append("symbol = :symbol")
        params["symbol"] = symbol
    if verdict:
        where.append("price_verdict = :verdict")
        params["verdict"] = verdict

    where_sql = " WHERE " + " AND ".join(where) if where else ""
    sql = f"""
        SELECT *
        FROM nodes_b9
        {where_sql}
        ORDER BY timestamp DESC, created_at DESC
        LIMIT :limit
    """

    with _connect(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()

    results: list[dict] = []
    for row in rows:
        item = dict(row)
        if item.get("node_json"):
            try:
                item["node_json"] = json.loads(item["node_json"])
            except json.JSONDecodeError:
                pass
        results.append(item)
    return results


__all__ = ["init_nodes_b9_table", "persist_node_b9", "get_recent_nodes_b9"]
