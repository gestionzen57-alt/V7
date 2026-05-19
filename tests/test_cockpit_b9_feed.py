"""Tests for the B9 cockpit live feed.

The feed is memory-only and read-only. It does not write DB, send Telegram, or
mutate dashboard state.
"""
from __future__ import annotations

import importlib

import pytest

feed = importlib.import_module("cockpit_b9_feed")

pytestmark = pytest.mark.skipif(feed.Flask is None, reason="Flask is not installed")


@pytest.fixture(autouse=True)
def _clean_buffer():
    feed.reset_b9_node_buffer()
    yield
    feed.reset_b9_node_buffer()


@pytest.fixture()
def client():
    app = feed.create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def _node(idx: int, symbol: str = "GBPUSD", verdict: str = "ACCEPTED") -> dict:
    return {
        "node_id": f"B9N_{idx:03d}",
        "symbol": symbol,
        "price_verdict_candidate": verdict,
        "data_visibility": "TACTICAL_OK",
        "zone_bounds": [1.2700, 1.2750],
    }


def test_api_b9_nodes_live_returns_200(client):
    response = client.get("/api/b9-nodes-live")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_symbol_filter_ok(client):
    feed.push_b9_node(_node(1, "GBPUSD"))
    feed.push_b9_node(_node(2, "EURUSD"))
    payload = client.get("/api/b9-nodes-live?symbol=EURUSD").get_json()
    assert payload["symbol"] == "EURUSD"
    assert payload["count"] == 1
    assert payload["nodes"][0]["symbol"] == "EURUSD"


def test_verdict_filter_ok(client):
    feed.push_b9_node(_node(1, verdict="ACCEPTED"))
    feed.push_b9_node(_node(2, verdict="REJECTED"))
    payload = client.get("/api/b9-nodes-live?verdict=REJECTED").get_json()
    assert payload["count"] == 1
    assert payload["nodes"][0]["price_verdict_candidate"] == "REJECTED"


def test_limit_respected(client):
    for i in range(20):
        feed.push_b9_node(_node(i))
    payload = client.get("/api/b9-nodes-live?limit=5").get_json()
    assert payload["count"] == 5
    assert len(payload["nodes"]) == 5


def test_limit_capped_to_50(client):
    for i in range(80):
        feed.push_b9_node(_node(i))
    payload = client.get("/api/b9-nodes-live?limit=500").get_json()
    assert payload["count"] == 50
    assert len(payload["nodes"]) == 50


def test_count_equals_len_nodes(client):
    for i in range(3):
        feed.push_b9_node(_node(i))
    payload = client.get("/api/b9-nodes-live").get_json()
    assert payload["count"] == len(payload["nodes"])


def test_buffer_push_get_ok():
    feed.push_b9_node(_node(1, "GBPUSD"))
    nodes = feed._get_recent_b9_nodes(symbol="GBPUSD", limit=10)
    assert len(nodes) == 1
    assert nodes[0]["node_id"] == "B9N_001"


def test_buffer_max_200_elements():
    for i in range(250):
        feed.push_b9_node(_node(i))
    nodes = feed._get_recent_b9_nodes(symbol="ALL", limit=500)
    assert len(feed._B9_NODE_BUFFER) == 200
    assert len(nodes) == 50  # public read cap remains 50.
    all_internal = list(feed._B9_NODE_BUFFER)
    assert all_internal[0]["node_id"] == "B9N_050"
    assert all_internal[-1]["node_id"] == "B9N_249"


def test_newest_first_order(client):
    feed.push_b9_node(_node(1))
    feed.push_b9_node(_node(2))
    payload = client.get("/api/b9-nodes-live?limit=2").get_json()
    assert [n["node_id"] for n in payload["nodes"]] == ["B9N_002", "B9N_001"]


def test_invalid_limit_falls_back_to_default(client):
    for i in range(12):
        feed.push_b9_node(_node(i))
    payload = client.get("/api/b9-nodes-live?limit=not-an-int").get_json()
    assert payload["count"] == 10


def test_register_b9_feed_is_idempotent():
    app = feed.Flask(__name__)
    feed.register_b9_feed(app)
    feed.register_b9_feed(app)
    rules = [r.rule for r in app.url_map.iter_rules() if r.rule == "/api/b9-nodes-live"]
    assert len(rules) == 1


def test_no_decision_language_in_feed_payload(client):
    feed.push_b9_node(_node(1, verdict="ACCEPTED"))
    payload = client.get("/api/b9-nodes-live").get_json()
    text = str(payload).upper()
    assert "BUY" not in text
    assert "SELL" not in text
