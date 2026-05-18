from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_t0118_human_terrain_synthesis_contract(tmp_path: Path) -> None:
    film_cards = {
        "film_cards": [
            {
                "film_id": "F1", "date": "2026-05-01", "session": "LONDON", "source_family": "FORCE_SNAPSHOT_DERIVED",
                "summary_recovery_type": "FORCE_SNAPSHOT_DERIVED", "source_mode": "M1_BAR_PROXY",
                "data_visibility": "RECONSTRUCTED_FORCE_SNAPSHOT_DERIVED", "confidence_cap": "0.35",
                "memory_family": "DIRECTIONAL_PROGRESS_MEMORY", "raw_agreement": "CONFIRMED_BY_RAW",
                "source_quality_state": "SOURCE_QUALITY_USABLE", "b6_memory_candidate_state": "B6_KEEP_CANDIDATE",
                "raw_texture_role": "RAW_PROGRESS_CONFIRMED", "b6_memory_candidate_score": "0.88", "source_quality_score": "0.76",
                "raw_range_pips": "5.5", "raw_tick_count": "165", "label_fr": "Vague progressive", "moment_type": "FLOW_DIRECTIONAL_DISPLACEMENT",
                "base": "Base", "reaction": "Reaction", "projection": "Projection", "judgment": "Judgment", "limits": "proxy/reconstructed reading; not full footprint claim"
            },
            {
                "film_id": "F2", "date": "2026-05-02", "session": "NY", "source_family": "RECOVERED_EXISTING_B9_SUMMARY",
                "summary_recovery_type": "RECOVERED_EXISTING_B9_SUMMARY", "source_mode": "ONTICK_RAW",
                "data_visibility": "RAW_SUMMARY", "confidence_cap": "0.70", "memory_family": "FRICTION_ABSORPTION_MEMORY",
                "raw_agreement": "NUANCED_BY_RAW", "source_quality_state": "SOURCE_QUALITY_USABLE", "b6_memory_candidate_state": "B6_REVIEW_CANDIDATE",
                "raw_texture_role": "RAW_FRICTION", "b6_memory_candidate_score": "0.70", "source_quality_score": "0.60",
                "raw_range_pips": "2.0", "raw_tick_count": "80", "label_fr": "Effort sans résultat", "moment_type": "EFFORT_WITHOUT_RESULT",
                "base": "Base", "reaction": "Reaction", "projection": "Projection", "judgment": "Judgment", "limits": "raw nuance proxy"
            },
            {
                "film_id": "F3", "date": "2026-05-03", "session": "NY", "source_family": "FORCE_SNAPSHOT_DERIVED",
                "summary_recovery_type": "FORCE_SNAPSHOT_DERIVED", "source_mode": "M1_BAR_PROXY", "memory_family": "FRICTION_ABSORPTION_MEMORY",
                "raw_agreement": "RAW_UNAVAILABLE", "b6_memory_candidate_state": "B6_REJECT_RAW_UNAVAILABLE"
            }
        ]
    }
    fp = {"false_positive_context_summary": {"matches_reviewed": 1, "flag_counts": {"SESSION_DIFFERENCE": 1}, "state_counts": {"B6_FALSE_POSITIVE_CONTEXT_MEDIUM": 1}, "primary_message_fr": "La ressemblance n'est pas une repetition."}}
    cards_path = tmp_path / "cards.json"
    fp_path = tmp_path / "fp.json"
    cards_path.write_text(json.dumps(film_cards), encoding="utf-8")
    fp_path.write_text(json.dumps(fp), encoding="utf-8")
    out_dir = tmp_path / "out"
    subprocess.check_call([
        sys.executable,
        "tools/build_t0118_b6_human_terrain_synthesis_v0.py",
        "--film-cards-json", str(cards_path),
        "--false-positive-json", str(fp_path),
        "--output-dir", str(out_dir),
    ])
    summary = json.loads((out_dir / "B6_HUMAN_TERRAIN_SYNTHESIS_V0.json").read_text(encoding="utf-8"))
    assert summary["total_cards"] == 2
    assert summary["integrity"]["raw_unavailable_in_active_cards"] is False
    assert (out_dir / "B6_HUMAN_TERRAIN_SYNTHESIS_V0.zip").exists()


def test_t0118_imports_compile() -> None:
    subprocess.check_call([sys.executable, "-m", "py_compile", "tools/build_t0118_b6_human_terrain_synthesis_v0.py"])
