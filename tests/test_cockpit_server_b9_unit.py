"""Unit tests for cockpit_server_b9 without binding port 8880."""
from __future__ import annotations

import importlib.util
import json
import sqlite3
from pathlib import Path


def load_module():
    module_path = Path(__file__).resolve().parents[1] / "Core" / "cockpit_server_b9.py"
    spec = importlib.util.spec_from_file_location("cockpit_server_b9", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_health_endpoint():
    mod = load_module()
    client = mod.app.test_client()
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["service"] == "cockpit_b9_server"
    assert data["port"] == 8880


def test_b9_nodes_live_endpoint_reads_recent_nodes(tmp_path, monkeypatch):
    nodes_dir = tmp_path / "output" / "b9_nodes_live"
    nodes_dir.mkdir(parents=True)
    (nodes_dir / "GBPUSD_20260519T100000.json").write_text(
        json.dumps({"symbol": "GBPUSD", "timestamp": "2026-05-19T10:00:00Z", "node_type": "A"}),
        encoding="utf-8",
    )
    (nodes_dir / "GBPUSD_20260519T101000.json").write_text(
        json.dumps({"symbol": "GBPUSD", "timestamp": "2026-05-19T10:10:00Z", "node_type": "B"}),
        encoding="utf-8",
    )
    (nodes_dir / "EURUSD_20260519T101000.json").write_text(
        json.dumps({"symbol": "EURUSD", "timestamp": "2026-05-19T10:10:00Z"}),
        encoding="utf-8",
    )

    mod = load_module()
    monkeypatch.setenv("B9_NODES_DIR", str(nodes_dir))
    client = mod.app.test_client()
    response = client.get("/api/b9-nodes-live?symbol=GBPUSD&limit=1")
    assert response.status_code == 200
    data = response.get_json()
    assert data["count"] == 1
    assert data["nodes"][0]["node_type"] == "B"
    assert data["data_visibility"] == "TACTICAL_OK"


def test_b9_nodes_live_missing_dir_is_degraded(tmp_path, monkeypatch):
    mod = load_module()
    monkeypatch.setenv("B9_NODES_DIR", str(tmp_path / "missing"))
    client = mod.app.test_client()
    response = client.get("/api/b9-nodes-live?symbol=GBPUSD&limit=5")
    assert response.status_code == 200
    data = response.get_json()
    assert data["nodes"] == []
    assert data["data_visibility"] == "READING_PARTIAL"
    assert "B9_NODES_DIR_MISSING" in data["technical_risks"]


def test_b8_coalition_context_endpoint_with_db(tmp_path, monkeypatch):
    db_path = tmp_path / "powerflow.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE bars_h1 (symbol TEXT, open REAL, high REAL, low REAL, close REAL, created_at TEXT)"
    )
    rows = [
        ("GBPUSD", 1.2500, 1.2520, 1.2490, 1.2510, "2026-05-19T10:00:00Z"),
        ("EURUSD", 1.1000, 1.1020, 1.0990, 1.1010, "2026-05-19T10:00:00Z"),
        ("AUDUSD", 0.6600, 0.6620, 0.6590, 0.6610, "2026-05-19T10:00:00Z"),
        ("NZDUSD", 0.6100, 0.6120, 0.6090, 0.6110, "2026-05-19T10:00:00Z"),
        ("USDJPY", 155.0, 155.5, 154.9, 155.2, "2026-05-19T10:00:00Z"),
        ("USDCAD", 1.3600, 1.3620, 1.3590, 1.3610, "2026-05-19T10:00:00Z"),
        ("USDCHF", 0.9100, 0.9120, 0.9090, 0.9110, "2026-05-19T10:00:00Z"),
        ("EURGBP", 0.8600, 0.8620, 0.8590, 0.8610, "2026-05-19T10:00:00Z"),
        ("GBPJPY", 194.0, 194.5, 193.9, 194.2, "2026-05-19T10:00:00Z"),
    ]
    conn.executemany("INSERT INTO bars_h1 VALUES (?, ?, ?, ?, ?, ?)", rows)
    conn.commit()
    conn.close()

    mod = load_module()
    monkeypatch.setenv("POWERFLOW_DB_PATH", str(db_path))
    client = mod.app.test_client()
    response = client.get("/api/b8-coalition-context?symbol=GBPUSD")
    assert response.status_code == 200
    data = response.get_json()
    assert "usd_quote" in data
    assert "usd_base" in data
    assert "gbp_cross" in data
    assert "coalitions" in data
    assert data["data_visibility"] in {"TACTICAL_OK", "DEGRADED"}
    assert data["coalitions"]["usd_quote"]["available_count"] == 4


def test_b8_coalition_context_missing_db_is_structured(tmp_path, monkeypatch):
    mod = load_module()
    monkeypatch.setenv("POWERFLOW_DB_PATH", str(tmp_path / "missing.db"))
    client = mod.app.test_client()
    response = client.get("/api/b8-coalition-context")
    assert response.status_code == 200
    data = response.get_json()
    assert data["usd_quote"] == []
    assert data["usd_base"] == []
    assert data["gbp_cross"] == []
    assert data["data_visibility"] == "READING_PARTIAL"
    assert "DB_NOT_FOUND" in data["technical_risks"]
