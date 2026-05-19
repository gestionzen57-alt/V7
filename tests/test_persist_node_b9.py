import json
import sqlite3
from pathlib import Path

import pytest

from persist_node_b9 import get_recent_nodes_b9, init_nodes_b9_table, persist_node_b9


def sample_node(node_id="node-1", symbol="EURUSD", timestamp="2026-05-19T08:00:00Z", verdict="EFFORT_WITHOUT_RESULT"):
    return {
        "node_id": node_id,
        "symbol": symbol,
        "timestamp": timestamp,
        "node_status": "ACTIVE",
        "node_role": "pullback_after_release",
        "node_role_fr": "pullback après release",
        "zone_low": 1.0801,
        "zone_high": 1.0812,
        "center": 1.08065,
        "width_pips": 11.0,
        "price_verdict": verdict,
        "zone_role": "retest_zone",
        "data_visibility": {"raw_coverage": 0.91, "confidence_cap": 0.72},
        "confidence": 0.68,
        "source_stack": ["M1_BAR_PROXY", "B6_FIELD_MEMORY", "B9_REQUALIFIER"],
    }


@pytest.fixture()
def db_path(tmp_path):
    return str(tmp_path / "powerflow_test.db")


def test_init_table_creates_table_if_absent(db_path):
    init_nodes_b9_table(db_path)
    with sqlite3.connect(db_path) as conn:
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='nodes_b9'").fetchall()
    assert tables == [("nodes_b9",)]


def test_persist_node_inserts_correctly(db_path):
    assert persist_node_b9(sample_node(), db_path=db_path) is True
    rows = get_recent_nodes_b9(db_path=db_path)
    assert len(rows) == 1
    assert rows[0]["node_id"] == "node-1"
    assert rows[0]["symbol"] == "EURUSD"


def test_get_recent_nodes_filters_symbol(db_path):
    persist_node_b9(sample_node("n1", "EURUSD", "2026-05-19T08:00:00Z"), db_path=db_path)
    persist_node_b9(sample_node("n2", "GBPUSD", "2026-05-19T08:01:00Z"), db_path=db_path)
    rows = get_recent_nodes_b9(symbol="GBPUSD", db_path=db_path)
    assert [row["symbol"] for row in rows] == ["GBPUSD"]


def test_get_recent_nodes_filters_verdict(db_path):
    persist_node_b9(sample_node("n1", verdict="CENTER_DESCENDING"), db_path=db_path)
    persist_node_b9(sample_node("n2", verdict="RETEST_FAILED"), db_path=db_path)
    rows = get_recent_nodes_b9(verdict="RETEST_FAILED", db_path=db_path)
    assert len(rows) == 1
    assert rows[0]["node_id"] == "n2"


def test_limit_is_respected(db_path):
    for i in range(5):
        persist_node_b9(sample_node(f"n{i}", timestamp=f"2026-05-19T08:0{i}:00Z"), db_path=db_path)
    rows = get_recent_nodes_b9(limit=3, db_path=db_path)
    assert len(rows) == 3


def test_node_json_contains_complete_payload(db_path):
    node = sample_node()
    requalified = {"event": "PAIR_DOWN_REQUALIFIED", "label": "pullback", "source_stack": ["B9"]}
    b6_match = {"score": 87, "film_id": "B6_FILM_03"}
    persist_node_b9(node, requalified=requalified, b6_match=b6_match, db_path=db_path)
    row = get_recent_nodes_b9(db_path=db_path)[0]
    assert row["node_json"]["node"] == node
    assert row["node_json"]["requalified"] == requalified
    assert row["node_json"]["b6_match"] == b6_match


def test_upsert_duplicate_node_id_does_not_error(db_path):
    persist_node_b9(sample_node("dup", verdict="OLD"), db_path=db_path)
    persist_node_b9(sample_node("dup", verdict="NEW"), db_path=db_path)
    rows = get_recent_nodes_b9(db_path=db_path)
    assert len(rows) == 1
    assert rows[0]["price_verdict"] == "NEW"


def test_b6_match_score_is_persisted(db_path):
    persist_node_b9(sample_node(), b6_match={"score": 93, "film_id": "B6_FILM_12"}, db_path=db_path)
    row = get_recent_nodes_b9(db_path=db_path)[0]
    assert row["b6_match_score"] == 93
    assert row["b6_film_id"] == "B6_FILM_12"


def test_missing_required_fields_raise_value_error(db_path):
    with pytest.raises(ValueError):
        persist_node_b9({"node_id": "bad", "symbol": "EURUSD"}, db_path=db_path)
