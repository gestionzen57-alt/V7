"""B9 cockpit feed for PowerFlow V7.6.7.

Read-only in-memory feed exposing B9 nodes to a Flask cockpit endpoint.
No DB write, no Telegram send, no dashboard mutation.

Usage in an existing Flask server:

    from cockpit_b9_feed import register_b9_feed, push_b9_node
    register_b9_feed(app)

Then the endpoint is available at:

    GET /api/b9-nodes-live?symbol=GBPUSD&limit=10&verdict=ACCEPTED
"""
from __future__ import annotations

from datetime import datetime
from threading import RLock
from typing import Any, Callable

try:  # Flask is optional for import/py_compile and required for API tests.
    from flask import Flask, jsonify, request
except Exception:  # pragma: no cover - exercised only when Flask is absent.
    Flask = None  # type: ignore[assignment]
    jsonify = None  # type: ignore[assignment]
    request = None  # type: ignore[assignment]

MAX_B9_NODE_BUFFER = 200
_B9_NODE_BUFFER: list[dict[str, Any]] = []
_B9_LOCK = RLock()


def reset_b9_node_buffer() -> None:
    """Clear the in-memory buffer. Intended for tests and controlled restarts."""
    with _B9_LOCK:
        _B9_NODE_BUFFER.clear()


def push_b9_node(node: dict[str, Any]) -> dict[str, Any]:
    """Add one B9 node to the read-only cockpit buffer.

    The function copies the input node to avoid later caller-side mutation leaking
    into the cockpit feed. It never writes to DB and never sends Telegram.
    """
    if not isinstance(node, dict):
        raise TypeError("node must be a dict")

    stored = dict(node)
    stored.setdefault("symbol", "UNKNOWN")
    stored.setdefault("buffer_received_at", datetime.utcnow().isoformat())

    with _B9_LOCK:
        _B9_NODE_BUFFER.append(stored)
        if len(_B9_NODE_BUFFER) > MAX_B9_NODE_BUFFER:
            del _B9_NODE_BUFFER[:-MAX_B9_NODE_BUFFER]
    return stored


def _coerce_limit(limit: Any, default: int = 10, max_limit: int = 50) -> int:
    try:
        value = int(limit)
    except (TypeError, ValueError):
        value = default
    if value < 1:
        value = default
    return min(value, max_limit)


def _get_recent_b9_nodes(symbol: str = "ALL", limit: int = 10, verdict: str | None = None) -> list[dict[str, Any]]:
    """Return recent nodes newest-first, optionally filtered by symbol/verdict."""
    safe_limit = _coerce_limit(limit)
    with _B9_LOCK:
        nodes = list(reversed(_B9_NODE_BUFFER))

    if symbol and symbol != "ALL":
        nodes = [n for n in nodes if n.get("symbol") == symbol]
    if verdict:
        nodes = [n for n in nodes if n.get("price_verdict_candidate") == verdict]
    return nodes[:safe_limit]


def _make_payload(symbol: str, limit: int, verdict_filter: str | None) -> dict[str, Any]:
    nodes = _get_recent_b9_nodes(symbol=symbol, limit=limit, verdict=verdict_filter)
    return {
        "status": "ok",
        "symbol": symbol,
        "count": len(nodes),
        "timestamp": datetime.utcnow().isoformat(),
        "nodes": nodes,
    }


def register_b9_feed(app: Any) -> Any:
    """Register GET /api/b9-nodes-live on an existing Flask app.

    Idempotent: calling it twice does not duplicate the route.
    """
    if Flask is None or request is None or jsonify is None:
        raise RuntimeError("Flask is required to register /api/b9-nodes-live")

    if "b9_nodes_live" in getattr(app, "view_functions", {}):
        return app

    @app.route("/api/b9-nodes-live", methods=["GET"], endpoint="b9_nodes_live")
    def b9_nodes_live():  # type: ignore[no-untyped-def]
        symbol = request.args.get("symbol", "ALL")
        limit = _coerce_limit(request.args.get("limit", 10))
        verdict_filter = request.args.get("verdict", None)
        return jsonify(_make_payload(symbol=symbol, limit=limit, verdict_filter=verdict_filter))

    return app


def create_app() -> Any:
    """Create a minimal Flask app exposing the B9 feed endpoint."""
    if Flask is None:
        raise RuntimeError("Flask is required to create the B9 feed app")
    app = Flask(__name__)
    register_b9_feed(app)
    return app


__all__ = [
    "MAX_B9_NODE_BUFFER",
    "push_b9_node",
    "reset_b9_node_buffer",
    "_get_recent_b9_nodes",
    "register_b9_feed",
    "create_app",
]
