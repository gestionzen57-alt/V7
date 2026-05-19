#!/usr/bin/env python3
"""
PowerFlow B9 — Flask Server
Endpoints: B9 live nodes + B8 coalition context
Port: 8880

Doctrine:
- Cockpit surface only: reads files/DB, does not decide.
- No BUY/SELL language.
- Fail-soft: missing DB/table/node directory returns structured degraded payload.
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    from flask import Flask, jsonify, request
except ImportError as exc:  # pragma: no cover - explicit operator feedback
    raise SystemExit(
        "Flask is required. Install with: python -m pip install flask"
    ) from exc

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

DEFAULT_DB_PATH = "powerflow.db"
DEFAULT_NODES_DIR = Path("output") / "b9_nodes_live"
SERVER_VERSION = "1.0.0"

USD_QUOTE_SYMBOLS = ("EURUSD", "GBPUSD", "AUDUSD", "NZDUSD")
USD_BASE_SYMBOLS = ("USDJPY", "USDCAD", "USDCHF")
GBP_CROSS_SYMBOLS = ("EURGBP", "GBPJPY", "GBPAUD", "GBPCAD", "GBPCHF", "GBPNZD")


def utc_now_iso() -> str:
    """Return a UTC ISO timestamp with a Z suffix."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_int(value: Any, default: int = 10, minimum: int = 1, maximum: int = 250) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, parsed))


def _repo_root_from_current() -> Path:
    """Return a sensible repo/core working root for relative file lookups."""
    return Path.cwd()


def _nodes_dir() -> Path:
    override = os.getenv("B9_NODES_DIR", "").strip()
    if override:
        return Path(override)
    return _repo_root_from_current() / DEFAULT_NODES_DIR


def _db_path() -> Path:
    override = os.getenv("POWERFLOW_DB_PATH", "").strip()
    if override:
        return Path(override)
    return _repo_root_from_current() / DEFAULT_DB_PATH


def _read_json_file(path: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def get_recent_b9_nodes(symbol: str = "GBPUSD", limit: int = 10, nodes_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Read recent B9 nodes from output/b9_nodes_live.

    Expected filename shape is usually SYMBOL_*.json, but the function also accepts
    JSON files whose internal 'symbol' field matches the requested symbol.
    """
    symbol = (symbol or "GBPUSD").upper().strip()
    limit = _safe_int(limit)
    directory = nodes_dir or _nodes_dir()
    if not directory.exists() or not directory.is_dir():
        return []

    nodes: List[Dict[str, Any]] = []
    seen_files: set[str] = set()

    candidate_patterns = [f"{symbol}_*.json", "*.json"]
    for pattern in candidate_patterns:
        for path in directory.glob(pattern):
            if str(path) in seen_files:
                continue
            seen_files.add(str(path))
            data = _read_json_file(path)
            if not isinstance(data, dict):
                continue
            data_symbol = str(data.get("symbol", symbol)).upper()
            if data_symbol != symbol:
                continue
            data.setdefault("symbol", symbol)
            data.setdefault("source_file", path.name)
            nodes.append(data)

    def sort_key(node: Dict[str, Any]) -> Tuple[str, str]:
        return (str(node.get("timestamp", "")), str(node.get("source_file", "")))

    nodes.sort(key=sort_key, reverse=True)
    return nodes[:limit]


def _connect_readonly(db_path: Path) -> sqlite3.Connection:
    """Open SQLite DB in read-only mode to preserve cockpit read-only behavior."""
    uri = f"file:{db_path.resolve()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table_name,),
    ).fetchone()
    return row is not None


def _columns(conn: sqlite3.Connection, table_name: str) -> List[str]:
    try:
        rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    except sqlite3.Error:
        return []
    return [str(row[1]) for row in rows]


def _pick_column(cols: Iterable[str], candidates: Iterable[str]) -> Optional[str]:
    cols_set = set(cols)
    for candidate in candidates:
        if candidate in cols_set:
            return candidate
    return None


def _latest_bar(conn: sqlite3.Connection, symbol: str) -> Dict[str, Any]:
    """Return latest H1 bar-like row for a symbol, with schema fallback."""
    table = "bars_h1"
    cols = _columns(conn, table)
    if not cols:
        return {"symbol": symbol, "available": False, "reason": "bars_h1_schema_unavailable"}

    symbol_col = _pick_column(cols, ("symbol", "pair", "instrument"))
    close_col = _pick_column(cols, ("close", "close_price", "bid", "price", "last"))
    created_col = _pick_column(cols, ("created_at", "timestamp", "time", "bar_time", "datetime"))
    open_col = _pick_column(cols, ("open", "open_price"))
    high_col = _pick_column(cols, ("high", "high_price"))
    low_col = _pick_column(cols, ("low", "low_price"))

    if not symbol_col:
        return {"symbol": symbol, "available": False, "reason": "symbol_column_missing"}

    selected = [symbol_col]
    aliases = {symbol_col: "symbol"}
    for col in (close_col, created_col, open_col, high_col, low_col):
        if col and col not in selected:
            selected.append(col)
    select_sql = ", ".join(selected)
    order_sql = created_col or "rowid"

    try:
        row = conn.execute(
            f"SELECT {select_sql} FROM {table} WHERE {symbol_col} = ? ORDER BY {order_sql} DESC LIMIT 1",
            (symbol,),
        ).fetchone()
    except sqlite3.Error as exc:
        return {"symbol": symbol, "available": False, "reason": f"query_error:{exc}"}

    if row is None:
        return {"symbol": symbol, "available": False, "reason": "no_recent_bar"}

    out: Dict[str, Any] = {"symbol": symbol, "available": True}
    if close_col and close_col in row.keys():
        out["close"] = row[close_col]
    if created_col and created_col in row.keys():
        out["created_at"] = row[created_col]
    if open_col and open_col in row.keys():
        out["open"] = row[open_col]
    if high_col and high_col in row.keys():
        out["high"] = row[high_col]
    if low_col and low_col in row.keys():
        out["low"] = row[low_col]
    out["source_table"] = table
    return out


def _direction_proxy(row: Dict[str, Any]) -> str:
    """Light cockpit-only direction proxy from open/close when available."""
    try:
        open_value = float(row.get("open"))
        close_value = float(row.get("close"))
    except (TypeError, ValueError):
        return "UNKNOWN"
    if close_value > open_value:
        return "UP"
    if close_value < open_value:
        return "DOWN"
    return "FLAT"


def _decorate_group(rows: List[Dict[str, Any]], group_name: str) -> Dict[str, Any]:
    available = [row for row in rows if row.get("available")]
    return {
        "group": group_name,
        "items": [dict(row, direction_proxy=_direction_proxy(row)) for row in rows],
        "available_count": len(available),
        "total_count": len(rows),
        "data_visibility": "TACTICAL_OK" if available else "READING_PARTIAL",
    }


def get_b8_coalition_context(symbol: str = "GBPUSD", db_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Read B8 coalition context from powerflow.db.

    The endpoint is a cockpit read surface: it returns structured context and
    degraded states, not decisions.
    """
    symbol = (symbol or "GBPUSD").upper().strip()
    path = db_path or _db_path()
    base_payload: Dict[str, Any] = {
        "symbol": symbol,
        "timestamp": utc_now_iso(),
        "source": "powerflow.db/bars_h1",
        "usd_quote": [],
        "usd_base": [],
        "gbp_cross": [],
        "coalitions": {},
        "data_visibility": "READING_PARTIAL",
        "technical_risks": [],
    }

    if not path.exists():
        base_payload["technical_risks"].append("DB_NOT_FOUND")
        return base_payload

    try:
        conn = _connect_readonly(path)
    except sqlite3.Error as exc:
        base_payload["technical_risks"].append(f"DB_OPEN_FAILED:{exc}")
        return base_payload

    try:
        if not _table_exists(conn, "bars_h1"):
            base_payload["technical_risks"].append("BARS_H1_TABLE_MISSING")
            return base_payload

        usd_quote = [_latest_bar(conn, sym) for sym in USD_QUOTE_SYMBOLS]
        usd_base = [_latest_bar(conn, sym) for sym in USD_BASE_SYMBOLS]
        gbp_cross = [_latest_bar(conn, sym) for sym in GBP_CROSS_SYMBOLS]

        base_payload["usd_quote"] = usd_quote
        base_payload["usd_base"] = usd_base
        base_payload["gbp_cross"] = gbp_cross
        base_payload["coalitions"] = {
            "usd_quote": _decorate_group(usd_quote, "USD_QUOTE"),
            "usd_base": _decorate_group(usd_base, "USD_BASE"),
            "gbp_cross": _decorate_group(gbp_cross, "GBP_CROSS"),
        }

        total_available = sum(
            1 for row in [*usd_quote, *usd_base, *gbp_cross] if row.get("available")
        )
        if total_available >= 8:
            base_payload["data_visibility"] = "TACTICAL_OK"
        elif total_available >= 3:
            base_payload["data_visibility"] = "DEGRADED"
            base_payload["technical_risks"].append("PARTIAL_COALITION_COVERAGE")
        else:
            base_payload["data_visibility"] = "READING_PARTIAL"
            base_payload["technical_risks"].append("LOW_COALITION_COVERAGE")
        return base_payload
    finally:
        conn.close()


@app.route("/api/health", methods=["GET"])
def health():
    """Health check."""
    nodes_path = _nodes_dir()
    db_path = _db_path()
    return jsonify(
        {
            "status": "ok",
            "service": "cockpit_b9_server",
            "version": SERVER_VERSION,
            "port": 8880,
            "timestamp": utc_now_iso(),
            "read_surfaces": {
                "b9_nodes_dir_exists": nodes_path.exists(),
                "db_exists": db_path.exists(),
            },
        }
    ), 200


@app.route("/api/b9-nodes-live", methods=["GET"])
def b9_nodes_live():
    """GET /api/b9-nodes-live?symbol=GBPUSD&limit=10."""
    symbol = request.args.get("symbol", "GBPUSD").upper().strip()
    limit = _safe_int(request.args.get("limit", 10), default=10)
    nodes = get_recent_b9_nodes(symbol=symbol, limit=limit)
    technical_risks: List[str] = []
    if not _nodes_dir().exists():
        technical_risks.append("B9_NODES_DIR_MISSING")
    elif not nodes:
        technical_risks.append("NO_RECENT_B9_NODE_FOR_SYMBOL")

    return jsonify(
        {
            "symbol": symbol,
            "nodes": nodes,
            "count": len(nodes),
            "limit": limit,
            "data_visibility": "TACTICAL_OK" if nodes else "READING_PARTIAL",
            "technical_risks": technical_risks,
            "timestamp": utc_now_iso(),
        }
    ), 200


@app.route("/api/b8-coalition-context", methods=["GET"])
def b8_coalition_context():
    """GET /api/b8-coalition-context?symbol=GBPUSD."""
    symbol = request.args.get("symbol", "GBPUSD").upper().strip()
    return jsonify(get_b8_coalition_context(symbol=symbol)), 200


def run_server() -> None:
    """Run the Flask server on localhost:8880."""
    import logging

    logging.basicConfig(level=logging.INFO)
    print("PowerFlow B9 Flask Server")
    print("Routes:")
    print("  GET /api/health")
    print("  GET /api/b9-nodes-live?symbol=GBPUSD&limit=10")
    print("  GET /api/b8-coalition-context?symbol=GBPUSD")
    print("")
    print("http://localhost:8880")
    app.run(host="localhost", port=8880, debug=False, threaded=True)


if __name__ == "__main__":
    run_server()
