import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pf_battlefield_flux_dashboard


def test_build_dashboard_widget_structure():
    state = {"source_mode": "TIMER_1S_SAMPLE", "data_visibility": "LIVE", "tick_count": 100, "lookback_min": 30, "events": [], "context": {"symbol": "GBPUSD"}}
    widget = pf_battlefield_flux_dashboard.build_dashboard_evidence_widget(state, [])
    assert widget["title"] == "Battlefield Flux"
    assert "timestamp" in widget
    assert widget["source_mode"] == "TIMER_1S_SAMPLE"
    assert widget["data_visibility"] == "LIVE"
    assert "events" in widget
    assert "evidence_L1" in widget
    assert "evidence_L2" in widget
    assert "evidence_L3" in widget


def test_format_trader_alert_packet_battle():
    event = {"event_type": "BATTLE_LEVEL_BORN", "zone": {"level": 1.2650, "strength": 0.8, "dwell_time_sec": 120}, "battle_score": 0.78, "timestamp": "2026-05-16T10:00:00Z"}
    context = {"source_mode": "TIMER_1S_SAMPLE", "symbol": "GBPUSD"}
    packet = pf_battlefield_flux_dashboard.format_trader_alert_packet(event, context)
    assert packet["event_type"] == "T009_BATTLE_LEVEL_BORN"
    assert packet["source_mode"] == "TIMER_1S_SAMPLE"
    assert packet["data_visibility"] == "LIVE"
    assert packet["confidence"] == pytest.approx(0.78)
    assert "BATTLE_LEVEL_BORN" in packet["message_trader_fr"]
    assert "T009_BATTLE_LEVEL_BORN" not in packet["message_trader_fr"]


def test_format_trader_alert_packet_reconstructed():
    event = {"event_type": "ABSORPTION_CLUSTER", "zone": {"level": 1.2700}, "absorption_score": 0.85, "timestamp": "2026-05-16T10:00:00Z"}
    context = {"source_mode": "M1_BAR_PROXY"}
    packet = pf_battlefield_flux_dashboard.format_trader_alert_packet(event, context)
    assert packet["event_type"] == "T009_ABSORPTION_CLUSTER"
    assert packet["data_visibility"] == "RECONSTRUCTED"
    assert packet["confidence"] <= 0.35
    assert packet["confidence"] == pytest.approx(0.35)
    assert "data reconstruite" in packet["message_trader_fr"]


def test_route_telegram_dry_run_blocked(tmp_path):
    packet = {"event_type": "T009_BATTLE_LEVEL_BORN", "symbol": "GBPUSD", "message_trader_fr": "BATTLE_LEVEL_BORN 1.2650 détecté", "confidence": 0.78, "data_visibility": "LIVE", "source_mode": "TIMER_1S_SAMPLE"}
    flags = {"POWERFLOW_T009_ENABLE_TELEGRAM": 0, "POWERFLOW_T009_DRY_RUN": 1, "POWERFLOW_T009_OUTPUT_DIR": str(tmp_path)}
    result = pf_battlefield_flux_dashboard.route_to_telegram_dry_run(packet, flags)
    assert result["sent"] is False
    assert result["logged"] is True
    assert "dry-run" in result["reason"].lower()
    assert (tmp_path / "telegram_dry_run_log.json").exists()


def test_route_telegram_reconstructed_blocked(tmp_path):
    packet = {"event_type": "T009_ABSORPTION_CLUSTER", "symbol": "GBPUSD", "message_trader_fr": "ABSORPTION_CLUSTER 1.2700 possible", "confidence": 0.35, "data_visibility": "RECONSTRUCTED", "source_mode": "M1_BAR_PROXY"}
    flags = {"POWERFLOW_T009_ENABLE_TELEGRAM": 0, "POWERFLOW_T009_DRY_RUN": 1, "POWERFLOW_T009_OUTPUT_DIR": str(tmp_path)}
    result = pf_battlefield_flux_dashboard.route_to_telegram_dry_run(packet, flags)
    assert result["sent"] is False
    assert result["logged"] is True
    assert "reconstructed" in result["reason"].lower()


def test_dashboard_widget_empty_safe():
    state = {"source_mode": "UNKNOWN", "events": []}
    widget = pf_battlefield_flux_dashboard.build_dashboard_evidence_widget(state, [])
    assert widget["events"] == []
    assert widget["source_mode"] == "UNKNOWN"
    assert widget["data_visibility"] == "BLIND"


def test_log_phase1b_event_writes_file(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    pf_battlefield_flux_dashboard.log_phase1b_event("DASHBOARD_WIDGET_BUILT", {"widget_id": "test"}, str(output_dir))
    log_file = output_dir / "phase1b_events.log"
    assert log_file.exists()
    assert "DASHBOARD_WIDGET_BUILT" in log_file.read_text(encoding="utf-8")


def test_cli_safety_checks_telegram_flag(tmp_path):
    script = Path(__file__).resolve().parent.parent / "run_battlefield_flux_with_dashboard.py"
    env = os.environ.copy()
    env["POWERFLOW_T009_ENABLE_TELEGRAM"] = "1"
    env["POWERFLOW_T009_DRY_RUN"] = "1"
    result = subprocess.run([sys.executable, str(script), "--symbol", "GBPUSD", "--output", str(tmp_path)], env=env, capture_output=True, text=True)
    assert result.returncode == 1
    assert "POWERFLOW_T009_ENABLE_TELEGRAM=0" in result.stdout


def test_cli_creates_dashboard_and_dry_run_files(tmp_path):
    script = Path(__file__).resolve().parent.parent / "run_battlefield_flux_with_dashboard.py"
    env = os.environ.copy()
    env["POWERFLOW_T009_ENABLE_TELEGRAM"] = "0"
    env["POWERFLOW_T009_DRY_RUN"] = "1"
    result = subprocess.run([sys.executable, str(script), "--symbol", "GBPUSD", "--lookback-min", "1", "--output", str(tmp_path), "--enable-dashboard", "--dry-run-telegram"], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / "battlefield_flux_state.json").exists()
    assert (tmp_path / "battlefield_flux_events.json").exists()
    assert (tmp_path / "battlefield_flux_dashboard_widget.json").exists()
    assert (tmp_path / "telegram_dry_run_log.json").exists()
    assert (tmp_path / "phase1b_events.log").exists()
