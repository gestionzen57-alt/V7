from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pf_t009_zone_memory_object_builder as mod


def sample_path() -> Path:
    return Path(__file__).resolve().parents[1] / "samples" / "b9_zone_memory_object_builder_v0" / "sample_t009_sequence_summary_zone_memory.json"


def test_t0141_builds_zone_memory_objects() -> None:
    summary = json.loads(sample_path().read_text(encoding="utf-8"))
    result = mod.build_zone_memory_objects(summary)
    assert result["version"] == mod.VERSION
    assert result["zone_object_count"] >= 4
    assert result["rejected_raw_unavailable_moments"] == 1
    assert not result["missing_required_field_counts"]
    assert not result["forbidden_language_hits"]
    assert result["read_only"] is True
    assert result["db_write"] is False
    assert result["dashboard"] is False
    assert result["telegram"] is False
    assert result["buy_sell"] is False
    assert result["probability_of_success"] is False
    states = set(result["state_counts"].keys())
    assert "ZONE_MEMORY_REJECTED" in states or "ZONE_MEMORY_CONSUMED" in states
    assert any(obj["zone_memory_state"] == "ZONE_MEMORY_DEFENDED" for obj in result["zone_objects"])


def test_t0141_cli_outputs(tmp_path: Path) -> None:
    cmd = [
        sys.executable,
        "tools/build_t0141_b9_zone_memory_object_builder.py",
        "--sequence-summary-json",
        str(sample_path()),
        "--output-dir",
        str(tmp_path),
    ]
    completed = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[1], text=True, capture_output=True, check=True)
    assert "T0141_B9_ZONE_MEMORY_OBJECT_BUILDER_V0" in completed.stdout
    assert (tmp_path / "B9_ZONE_MEMORY_OBJECTS_V0.json").exists()
    assert (tmp_path / "B9_ZONE_MEMORY_OBJECTS_V0.csv").exists()
    assert (tmp_path / "B9_ZONE_MEMORY_OBJECTS_V0.md").exists()
    assert (tmp_path / "B9_ZONE_MEMORY_OBJECT_BUILDER_V0.zip").exists()
