from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_sequence_summarizer import (  # noqa: E402
    export_json,
    export_markdown,
    group_events,
    load_events,
    load_json,
    normalize_event,
    normalize_events,
    render_markdown,
    summarize_events,
)


def ev(
    ts: str,
    center: float,
    *,
    event_type: str = "T009_ABSORPTION_CLUSTER",
    absorption: float = 0.8,
    compression: float = 0.8,
    dwell: float = 0.8,
    failed: float = 0.7,
    pressure: float = 0.6,
    source_mode: str = "M1_BAR_PROXY",
    data_visibility: str = "RECONSTRUCTED",
    confidence_cap: float = 0.35,
):
    return {
        "ts_utc": ts,
        "event_type": event_type,
        "zone": {"low": center - 0.0001, "high": center + 0.0001, "center": center},
        "scores": {
            "battle_score": 0.55,
            "absorption_score": absorption,
            "components": {
                "activity_score": 0.5,
                "compression_score": compression,
                "dwell_score": dwell,
                "failed_displacement_score": failed,
                "pressure_score": pressure,
            },
        },
        "features": {"signed_delta": 0.1, "delta_imbalance": 0.2, "flip_rate": 0.1, "price_range_pips": 2.0},
        "source_mode": source_mode,
        "data_visibility": data_visibility,
        "confidence_cap": confidence_cap,
    }


def state():
    return {"source": {"source_mode": "M1_BAR_PROXY", "data_visibility": "RECONSTRUCTED", "confidence_cap": 0.35}}


def test_load_empty_events(tmp_path):
    path = tmp_path / "events.json"
    path.write_text("[]", encoding="utf-8")
    assert load_events(path) == []




def test_load_json_utf8_bom(tmp_path):
    path = tmp_path / "bom.json"
    path.write_text('{"ok": true}', encoding="utf-8-sig")
    assert load_json(path)["ok"] is True

def test_normalize_event_structure():
    normalized = normalize_event(ev("2026-05-11T10:00:00Z", 1.3600), state_defaults=state())
    assert normalized.timestamp == "2026-05-11T10:00:00Z"
    assert normalized.zone_center == 1.3600
    assert normalized.compression_score == 0.8
    assert normalized.source_mode == "M1_BAR_PROXY"


def test_group_events_by_time_price():
    events = normalize_events([
        ev("2026-05-11T10:00:00Z", 1.3600),
        ev("2026-05-11T10:01:00Z", 1.3602),
        ev("2026-05-11T10:08:00Z", 1.3603),
    ], state=state())
    groups = group_events(events, max_gap_sec=300, price_merge_pips=5)
    assert len(groups) == 2
    assert [len(g) for g in groups] == [2, 1]


def test_detect_absorption_shelf():
    events = [ev(f"2026-05-11T10:0{i}:00Z", 1.3600 + i * 0.00002, absorption=0.6, failed=0.4, dwell=0.86, compression=0.88) for i in range(5)]
    summary = summarize_events(state(), events)
    assert summary["moments"][0]["moment_type"] == "T009_MOMENT_ABSORPTION_SHELF"
    assert "Palier" in summary["moments"][0]["label_fr"]


def test_detect_center_migration_up():
    events = [ev(f"2026-05-11T10:0{i}:00Z", 1.3600 + i * 0.00012, absorption=0.5, failed=0.3, dwell=0.4, compression=0.4, pressure=0.7) for i in range(5)]
    summary = summarize_events(state(), events, price_merge_pips=20)
    assert summary["moments"][0]["moment_type"] == "T009_MOMENT_PROGRESSIVE_WAVE"
    assert summary["moments"][0]["migration_direction"] == "UP"


def test_detect_center_migration_down():
    events = [ev(f"2026-05-11T10:0{i}:00Z", 1.3608 - i * 0.00012, absorption=0.5, failed=0.3, dwell=0.4, compression=0.4) for i in range(5)]
    summary = summarize_events(state(), events, price_merge_pips=20)
    assert summary["moments"][0]["moment_type"] == "T009_MOMENT_CENTER_MIGRATION_DOWN"
    assert summary["moments"][0]["migration_direction"] == "DOWN"


def test_detect_effort_without_result():
    events = [ev(f"2026-05-11T10:0{i}:00Z", 1.3600 + i * 0.00001, absorption=0.84, failed=0.81, dwell=0.5, compression=0.5) for i in range(4)]
    summary = summarize_events(state(), events)
    assert summary["moments"][0]["moment_type"] == "T009_MOMENT_EFFORT_WITHOUT_RESULT"
    assert "Effort" in summary["moments"][0]["label_fr"]


def test_export_json(tmp_path):
    summary = summarize_events(state(), [ev("2026-05-11T10:00:00Z", 1.3600)])
    out = export_json(summary, tmp_path / "summary.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["module"] == "pf_t009_sequence_summarizer"


def test_export_markdown(tmp_path):
    summary = summarize_events(state(), [ev("2026-05-11T10:00:00Z", 1.3600)])
    out = export_markdown(summary, tmp_path / "summary.md")
    text = out.read_text(encoding="utf-8")
    assert "# T009 Sequence Summary V0" in text
    assert "Ce qui se passe" in text


def test_source_quality_preserved():
    summary = summarize_events(state(), [ev("2026-05-11T10:00:00Z", 1.3600)])
    moment = summary["moments"][0]
    assert moment["source_mode"] == "M1_BAR_PROXY"
    assert moment["data_visibility"] == "RECONSTRUCTED"
    assert moment["confidence_cap"] == 0.35
    assert any("M1_BAR_PROXY" in item for item in moment["limits_fr"])


def test_french_labels_present():
    summary = summarize_events(state(), [ev("2026-05-11T10:00:00Z", 1.3600)])
    moment = summary["moments"][0]
    assert moment["label_fr"]
    assert moment["reading_fr"]
    assert moment["why_it_matters_fr"]
    assert moment["how_detected_fr"]
    assert isinstance(moment["evidence_fr"], list)
    assert isinstance(moment["limits_fr"], list)


def test_no_buy_sell_words():
    summary = summarize_events(state(), [ev("2026-05-11T10:00:00Z", 1.3600)])
    combined = json.dumps(summary, ensure_ascii=False) + render_markdown(summary)
    assert "BUY" not in combined
    assert "SELL" not in combined
