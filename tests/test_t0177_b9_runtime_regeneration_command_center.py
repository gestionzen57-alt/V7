from pathlib import Path
import csv
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_runtime_regeneration_command_center import run


def test_t0177_builds_sample_command_center(tmp_path):
    sample = ROOT / "samples" / "t0177_runtime_regeneration_command_center_v0" / "sample_t0175_missing_inputs.csv"
    payload = run(ROOT, sample, tmp_path / "out")
    assert payload["command_center_state"] == "COMMAND_CENTER_READY"
    assert payload["required_regeneration_count"] == 7
    assert payload["optional_regeneration_count"] == 2
    assert payload["forbidden_language_hits"] == []


def test_t0177_outputs_expected_files(tmp_path):
    sample = ROOT / "samples" / "t0177_runtime_regeneration_command_center_v0" / "sample_t0175_missing_inputs.csv"
    run(ROOT, sample, tmp_path / "out")
    assert (tmp_path / "out" / "B9_RUNTIME_REGENERATION_COMMAND_CENTER_V0.json").exists()
    assert (tmp_path / "out" / "B9_RUNTIME_REGENERATION_COMMAND_CENTER_V0.md").exists()
    assert (tmp_path / "out" / "B9_RUNTIME_REGENERATION_STEPS_V0.csv").exists()
    assert (tmp_path / "out" / "B9_RUNTIME_REGENERATION_COMMAND_CENTER_V0.ps1").exists()


def test_t0177_csv_contains_assignments(tmp_path):
    sample = ROOT / "samples" / "t0177_runtime_regeneration_command_center_v0" / "sample_t0175_missing_inputs.csv"
    run(ROOT, sample, tmp_path / "out")
    with (tmp_path / "out" / "B9_RUNTIME_REGENERATION_STEPS_V0.csv").open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["role"] == "t0169_builder"
    assert any(r["assigned_gpt"] == "GPT Core Runtime B9" for r in rows)
    assert any(r["assigned_gpt"] == "GPT Dashboard Reality Board" for r in rows)
