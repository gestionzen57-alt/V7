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
    validate_summary_contract,
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


def london_pack_events():
    events = []
    # 08:00-08:14 effort without result.
    for i in range(4):
        events.append(ev(f"2026-05-15T08:0{i}:00Z", 1.3350 + i * 0.00001, absorption=0.86, failed=0.82, dwell=0.6, compression=0.62))
    # 09:10-09:31 retest / decision zone after extension.
    for i in range(4):
        events.append(ev(f"2026-05-15T09:1{i}:00Z", 1.3340 - i * 0.00010, absorption=0.55, failed=0.50, dwell=0.62, compression=0.62, pressure=0.6))
    # 10:00-10:23 progressive wave.
    for i in range(5):
        events.append(ev(f"2026-05-15T10:0{i}:00Z", 1.3340 + i * 0.00013, absorption=0.45, failed=0.30, dwell=0.4, compression=0.4, pressure=0.75))
    # 11:00-11:31 center migration down.
    for i in range(5):
        events.append(ev(f"2026-05-15T11:0{i}:00Z", 1.3360 - i * 0.00013, absorption=0.50, failed=0.35, dwell=0.45, compression=0.5, pressure=0.65))
    # 11:37-12:00 breathing inside previous zone.
    for i in range(2):
        events.append(ev(f"2026-05-15T11:3{7+i}:00Z", 1.3356, absorption=0.55, failed=0.40, dwell=0.45, compression=0.45, pressure=0.4))
    return events


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


def test_london_pack_summary_generates_moments():
    summary = summarize_events(state(), london_pack_events(), price_merge_pips=20)
    types = [m["moment_type"] for m in summary["moments"]]
    assert len(summary["moments"]) >= 5
    assert "T009_MOMENT_EFFORT_WITHOUT_RESULT" in types
    assert "T009_MOMENT_PROGRESSIVE_WAVE" in types
    assert "T009_MOMENT_CENTER_MIGRATION_DOWN" in types


def test_summary_md_contains_french_sections():
    summary = summarize_events(state(), london_pack_events(), price_merge_pips=20)
    text = render_markdown(summary)
    assert "Ce qui se passe" in text
    assert "Pourquoi c'est important" in text
    assert "Comment cela se produit" in text
    assert "Cause / reaction / consequence" in text
    assert "Lecture fractale" in text


def test_summary_preserves_limits():
    summary = summarize_events(state(), london_pack_events(), price_merge_pips=20)
    for moment in summary["moments"]:
        joined = " ".join(moment["limits_fr"])
        assert "M1_BAR_PROXY" in joined
        assert "RECONSTRUCTED" in joined
        assert "delta proxy" in joined


def test_why_how_fields_present():
    summary = summarize_events(state(), london_pack_events(), price_merge_pips=20)
    moment = summary["moments"][0]
    for key in ["what_happens_fr", "why_it_matters_fr", "how_it_happened_fr", "mechanism_fr", "proof_summary_fr"]:
        assert moment.get(key)


def test_mechanism_fr_for_migration_down():
    summary = summarize_events(state(), [ev(f"2026-05-11T10:0{i}:00Z", 1.3608 - i * 0.00012, absorption=0.5, failed=0.3, dwell=0.4, compression=0.4) for i in range(5)], price_merge_pips=20)
    moment = summary["moments"][0]
    assert "Centres successifs plus bas" in moment["mechanism_fr"]


def test_mechanism_fr_for_progressive_wave():
    summary = summarize_events(state(), [ev(f"2026-05-11T10:0{i}:00Z", 1.3600 + i * 0.00012, absorption=0.5, failed=0.3, dwell=0.4, compression=0.4, pressure=0.7) for i in range(5)], price_merge_pips=20)
    moment = summary["moments"][0]
    assert "deplacement net" in moment["mechanism_fr"]


def test_scene_causality_fields_present():
    summary = summarize_events(state(), london_pack_events(), price_merge_pips=20)
    for moment in summary["moments"]:
        for key in ["previous_context_fr", "cause_fr", "reaction_fr", "consequence_fr", "memory_shift_fr", "retest_role_fr"]:
            assert key in moment
            assert isinstance(moment[key], str)


def test_memory_shift_detected_after_shelf_break():
    events = []
    for i in range(5):
        events.append(ev(f"2026-05-11T10:0{i}:00Z", 1.3600 + i * 0.00002, absorption=0.6, failed=0.4, dwell=0.86, compression=0.88))
    for i in range(5):
        events.append(ev(f"2026-05-11T10:1{i}:00Z", 1.3590 - i * 0.00012, absorption=0.5, failed=0.3, dwell=0.4, compression=0.4))
    summary = summarize_events(state(), events, price_merge_pips=20)
    down = [m for m in summary["moments"] if m["moment_type"] == "T009_MOMENT_CENTER_MIGRATION_DOWN"][-1]
    assert "bas" in down["memory_shift_fr"]


def test_retest_role_fr_present():
    summary = summarize_events(state(), london_pack_events(), price_merge_pips=20)
    assert any(m["retest_role_fr"] for m in summary["moments"])


def test_scene_id_generation():
    summary = summarize_events(state(), london_pack_events(), price_merge_pips=20)
    ids = [m["scene_id"] for m in summary["moments"]]
    assert ids[0] == "B9SC-001"
    assert len(ids) == len(set(ids))


def test_session_chapter_assignment():
    summary = summarize_events(state(), london_pack_events(), price_merge_pips=20)
    chapters = {m["session_chapter"] for m in summary["moments"]}
    assert "Décision de zone" in chapters or "Migration de centre" in chapters
    assert summary["session_scene"]["scene_id"] == "B9SESSION-001"


def test_fractal_reading_fr_present():
    summary = summarize_events(state(), london_pack_events(), price_merge_pips=20)
    assert all(m["fractal_reading_fr"] for m in summary["moments"])


def test_validate_summary_contract():
    summary = summarize_events(state(), london_pack_events(), price_merge_pips=20)
    assert validate_summary_contract(summary) == []


def test_export_json(tmp_path):
    summary = summarize_events(state(), [ev("2026-05-11T10:00:00Z", 1.3600)])
    out = export_json(summary, tmp_path / "summary.json")
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["module"] == "pf_t009_sequence_summarizer"
    assert data["version"] == "V3.1"


def test_export_markdown(tmp_path):
    summary = summarize_events(state(), [ev("2026-05-11T10:00:00Z", 1.3600)])
    out = export_markdown(summary, tmp_path / "summary.md")
    text = out.read_text(encoding="utf-8")
    assert "# T009 Sequence Summary V3.1" in text
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


def test_prefers_l1_raw_first_ts_for_time_start():
    event = ev("2026-05-16T23:11:00Z", 1.3600)
    event["evidence"] = {"L1_raw": {"first_ts_utc": "2026-05-15T08:00:00Z"}}
    summary = summarize_events(state(), [event])
    assert summary["moments"][0]["time_start"] == "2026-05-15T08:00:00Z"


def test_replay_report_time_remap():
    event = ev("2026-05-16T23:11:00Z", 1.3600)
    replay_report = {
        "shifted_start_utc": "2026-05-16T23:11:00Z",
        "original_start_utc": "2026-05-15T08:00:00Z",
    }
    summary = summarize_events(state(), [event], replay_report=replay_report)
    assert summary["moments"][0]["time_start"] == "2026-05-15T08:00:00Z"


def test_progressive_wave_with_retrace_not_effort_without_result():
    centers = [1.3600, 1.3603, 1.3606, 1.3609, 1.3605, 1.3604]
    events = [
        ev(
            f"2026-05-15T10:{i:02d}:00Z",
            center,
            absorption=0.86,
            failed=0.82,
            dwell=0.45,
            compression=0.45,
            pressure=0.78,
        )
        for i, center in enumerate(centers)
    ]
    summary = summarize_events(state(), events, price_merge_pips=20)
    types = [m["moment_type"] for m in summary["moments"]]
    assert "T009_MOMENT_PROGRESSIVE_WAVE" in types
    assert types[0] != "T009_MOMENT_EFFORT_WITHOUT_RESULT"
    assert summary["moments"][0]["max_favorable_excursion_pips"] >= 4.0


def test_split_large_group_on_center_inflexion():
    centers = [1.3360, 1.3357, 1.3354, 1.3351, 1.3348, 1.3349, 1.3350, 1.3350]
    events = [
        ev(
            f"2026-05-15T11:{i:02d}:00Z",
            center,
            absorption=0.55,
            failed=0.35,
            dwell=0.5,
            compression=0.55,
            pressure=0.65,
        )
        for i, center in enumerate(centers)
    ]
    summary = summarize_events(state(), events, price_merge_pips=20)
    assert len(summary["moments"]) >= 2
    assert summary["moments"][0]["moment_type"] == "T009_MOMENT_CENTER_MIGRATION_DOWN"
    assert summary["moments"][1]["moment_type"] in {
        "T009_MOMENT_FLOW_BREATHING",
        "T009_MOMENT_CORRECTIVE_WAVE",
        "T009_MOMENT_RETRACE_DECISION_AREA",
        "T009_MOMENT_GENERIC_BATTLEFIELD",
    }


def test_french_labels_have_accents():
    summary = summarize_events(
        state(),
        [ev(f"2026-05-11T10:0{i}:00Z", 1.3608 - i * 0.00012, absorption=0.5, failed=0.3, dwell=0.4, compression=0.4) for i in range(5)],
        price_merge_pips=20,
    )
    labels = " | ".join(m["label_fr"] for m in summary["moments"])
    assert "gravité" in labels
    summary_effort = summarize_events(state(), [ev(f"2026-05-11T11:0{i}:00Z", 1.3600 + i * 0.00001, absorption=0.84, failed=0.81, dwell=0.5, compression=0.5) for i in range(4)])
    assert "résultat" in summary_effort["moments"][0]["label_fr"]


def test_source_profile_is_mandatory_and_cautious_for_m1_proxy():
    summary = summarize_events(state(), [ev("2026-05-11T10:00:00Z", 1.3600)])
    assert summary["source"]["source_profile"]["quality"] == "PROXY_CAUTION"
    moment = summary["moments"][0]
    assert moment["source_profile"]["source_mode"] == "M1_BAR_PROXY"
    assert "lecture reconstruite" in moment["source_profile"]["language_fr"].lower()


def test_zone_memory_object_minimal_fields_v31():
    summary = summarize_events(state(), [ev("2026-05-11T10:00:00Z", 1.3600)])
    zone_memory = summary["moments"][0]["zone_memory"]
    for key in ["zone_low", "zone_high", "zone_center_start", "zone_center_end", "state", "source_mode", "data_visibility", "confidence_cap"]:
        assert key in zone_memory


def test_parent_scene_base_reaction_projection_judgment_v31():
    summary = summarize_events(state(), london_pack_events(), price_merge_pips=20)
    parent = summary["moments"][0]["parent_scene"]
    assert parent["model"] == "base -> réaction -> projection -> jugement"
    for key in ["base_fr", "reaction_fr", "projection_fr", "judgment_fr", "read_only"]:
        assert key in parent
    assert parent["read_only"] is True


def test_effort_role_fuel_brake_absorption_v31():
    progressive = summarize_events(
        state(),
        [ev(f"2026-05-11T10:0{i}:00Z", 1.3600 + i * 0.00012, absorption=0.5, failed=0.3, dwell=0.4, compression=0.4, pressure=0.7) for i in range(5)],
        price_merge_pips=20,
    )["moments"][0]
    absorbed = summarize_events(
        state(),
        [ev(f"2026-05-11T11:0{i}:00Z", 1.3600 + i * 0.00001, absorption=0.84, failed=0.81, dwell=0.5, compression=0.5) for i in range(4)],
    )["moments"][0]
    shelf = summarize_events(
        state(),
        [ev(f"2026-05-11T12:0{i}:00Z", 1.3600 + i * 0.00002, absorption=0.6, failed=0.4, dwell=0.86, compression=0.88) for i in range(5)],
    )["moments"][0]
    assert progressive["effort_role"] == "FUEL"
    assert absorbed["effort_role"] == "ABSORPTION"
    assert shelf["effort_role"] == "BRAKE"


def test_retest_status_pending_failed_accepted_v31():
    pending = summarize_events(
        state(),
        [ev(f"2026-05-11T10:0{i}:00Z", 1.3600 + (0.0007 if i == 2 else i * 0.00001), absorption=0.4, failed=0.3, pressure=0.8) for i in range(4)],
        price_merge_pips=20,
    )["moments"][0]
    failed_events = [ev(f"2026-05-11T10:0{i}:00Z", 1.3600 + i * 0.0002, pressure=0.8) for i in range(4)]
    failed_events += [ev(f"2026-05-11T10:1{i}:00Z", 1.3606 - i * 0.0002, pressure=0.8) for i in range(4)]
    failed_summary = summarize_events(state(), failed_events, price_merge_pips=20)
    statuses = {m["retest_status"] for m in failed_summary["moments"]}
    assert pending["retest_status"] in {"PENDING", "ACCEPTED", "NOT_ISOLATED"}
    assert "FAILED" in statuses or "PENDING" in statuses or "ACCEPTED" in statuses


def test_cli_replay_report_remaps_exported_moment_times(tmp_path):
    import subprocess

    state_path = tmp_path / "state.json"
    events_path = tmp_path / "events.json"
    replay_path = tmp_path / "replay.json"
    out_dir = tmp_path / "out"
    state_path.write_text(json.dumps(state()), encoding="utf-8")
    events_path.write_text(json.dumps([ev("2026-05-16T23:11:00Z", 1.3600)]), encoding="utf-8")
    replay_path.write_text(json.dumps({"shifted_start_utc": "2026-05-16T23:11:00Z", "original_start_utc": "2026-05-15T08:00:00Z"}), encoding="utf-8")
    cmd = [sys.executable, str(ROOT / "run_t009_sequence_summarizer_once.py"), "--state", str(state_path), "--events", str(events_path), "--replay-report", str(replay_path), "--output", str(out_dir)]
    subprocess.check_call(cmd)
    exported = json.loads((out_dir / "t009_sequence_summary.json").read_text(encoding="utf-8"))
    assert exported["moments"][0]["time_start"] == "2026-05-15T08:00:00Z"
    md = (out_dir / "t009_sequence_summary.md").read_text(encoding="utf-8")
    assert "08:00 UTC" in md


def test_london_1000_1023_progressive_wave_preserved_v31():
    centers = [1.33506, 1.33518, 1.33574, 1.33626, 1.33676, 1.33711, 1.33742]
    events = [ev(f"2026-05-15T10:{i:02d}:00Z", c, absorption=0.55, failed=0.45, dwell=0.5, compression=0.5, pressure=0.76) for i, c in enumerate(centers)]
    summary = summarize_events(state(), events, price_merge_pips=30)
    assert summary["moments"][0]["moment_type"] == "T009_MOMENT_PROGRESSIVE_WAVE"
    assert summary["moments"][0]["effort_role"] == "FUEL"


def test_london_11_12_split_preserved_v31():
    centers = [1.33645, 1.33590, 1.33540, 1.33516, 1.33523, 1.33465, 1.33485, 1.33533, 1.33478, 1.33460]
    events = [ev(f"2026-05-15T11:{i:02d}:00Z", c, absorption=0.55, failed=0.45, dwell=0.5, compression=0.55, pressure=0.7) for i, c in enumerate(centers)]
    summary = summarize_events(state(), events, price_merge_pips=30)
    assert len(summary["moments"]) >= 2
    assert any(m["moment_type"] == "T009_MOMENT_CENTER_MIGRATION_DOWN" for m in summary["moments"])


def test_no_decision_language_in_export_v31():
    summary = summarize_events(state(), london_pack_events(), price_merge_pips=20)
    combined = (json.dumps(summary, ensure_ascii=False) + render_markdown(summary)).lower()
    for forbidden in ["achat", "vente", "entrée", "signal confirmé", "résistance confirmée", "vendeur limite confirmé", "footprint exact en m1 proxy"]:
        assert forbidden not in combined


def test_no_db_write_no_telegram_dashboard_b8_imports_v31():
    source = (ROOT / "pf_t009_sequence_summarizer.py").read_text(encoding="utf-8").lower()
    runner = (ROOT / "run_t009_sequence_summarizer_once.py").read_text(encoding="utf-8").lower()
    combined = source + runner
    assert "sqlite3" not in combined
    assert "powerflow.db" not in combined
    assert "tick_archive.db" not in combined
    assert "telegram" not in combined
    assert "dashboard" not in combined
    assert "b8" not in combined
