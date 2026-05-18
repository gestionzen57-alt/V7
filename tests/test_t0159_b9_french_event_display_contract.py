from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "build_t0159_b9_french_event_display_contract.py"
spec = importlib.util.spec_from_file_location("t0159_tool", TOOL)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_contract_covers_required_categories():
    entries = mod.build_entries()
    categories = {e["category"] for e in entries}
    required = {
        "b9_flow_state",
        "b9_retest_source_state",
        "raw_texture_state",
        "source_quality_state",
        "b6_memory_state",
        "telegram_attention_state",
        "technical_limit_state",
    }
    assert required.issubset(categories)
    assert len(entries) >= 30


def test_no_forbidden_language():
    entries = mod.build_entries()
    validation = mod.validate_entries(entries)
    assert validation["status"] == "READY"
    assert validation["forbidden_language_hits"] == []


def test_known_enums_are_present():
    enums = {e["enum"] for e in mod.build_entries()}
    for expected in [
        "FLOW_DIRECTIONAL_DISPLACEMENT",
        "FLOW_ROTATIONAL",
        "RETEST_OUTCOME_ACCEPTED",
        "RAW_PROGRESS_CONFIRMED",
        "RAW_UNAVAILABLE",
        "B6_KEEP_CANDIDATE",
        "READY_FOR_HUMAN_REVIEW_NO_SEND",
    ]:
        assert expected in enums


def test_cli_generates_outputs(tmp_path):
    out = tmp_path / "out"
    result = subprocess.run([
        sys.executable,
        str(TOOL),
        "--output-dir",
        str(out),
        "--strict-exit",
    ], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    path = out / "B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.json"
    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["validation"]["status"] == "READY"
    assert payload["validation"]["entry_count"] >= 30
