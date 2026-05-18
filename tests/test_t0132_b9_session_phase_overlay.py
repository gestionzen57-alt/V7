from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("tool", ROOT / "tools" / "build_t0132_b9_session_phase_overlay.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)  # type: ignore[union-attr]


def test_t0132_sample_passes(tmp_path: Path) -> None:
    sample = ROOT / "samples" / "b9_session_phase_overlay_v0" / "sample_t009_sequence_summary_session_overlay.json"
    manifest = mod.run(sample, tmp_path)
    assert manifest["session_overlay_state"] == "PASS"
    assert manifest["moments"] == 5
    assert manifest["missing_required_field_counts"] == {}
    assert manifest["forbidden_language_hits"] == []
    assert manifest["session_counts"]["LONDON"] == 1
    assert manifest["session_counts"]["OVERLAP"] == 1
    assert manifest["session_counts"]["DEAD_ZONE"] == 1
    assert manifest["session_counts"]["ASIAN"] == 2
    assert (tmp_path / "B9_SESSION_PHASE_OVERLAY_V0.zip").exists()


def test_t0132_enriched_fields_present(tmp_path: Path) -> None:
    sample = ROOT / "samples" / "b9_session_phase_overlay_v0" / "sample_t009_sequence_summary_session_overlay.json"
    mod.run(sample, tmp_path)
    enriched = mod.load_json(tmp_path / "B9_SESSION_PHASE_OVERLAY_ENRICHED_SUMMARY_V0.json")
    moments = enriched["moments"]
    required = [
        "b9_session_overlay_version", "b9_session", "b9_session_phase", "b9_minutes_since_session_open",
        "b9_session_bias", "b9_session_context_source", "b9_session_reading_fr", "b9_session_limits",
    ]
    for moment in moments:
        for field in required:
            assert field in moment
    overlap = [m for m in moments if m["b9_session"] == "OVERLAP"][0]
    assert overlap["b9_session_bias"] == "MAX_VELOCITY_BATTLEFIELD"
