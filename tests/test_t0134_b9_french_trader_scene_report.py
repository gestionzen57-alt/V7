from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import build_t0134_b9_french_trader_scene_report as mod
from pf_t009_french_trader_scene_report import REPORT_SECTIONS


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_t0134_sample_report_passes(tmp_path: Path) -> None:
    sample = ROOT / "samples" / "b9_french_trader_scene_report_v0" / "sample_t009_sequence_summary_french_report.json"
    memory = ROOT / "samples" / "b9_french_trader_scene_report_v0" / "sample_b9_memory_brief_v0.json"
    manifest = mod.run(sample, tmp_path, memory_brief_json=memory)
    assert manifest["report_state"] == "PASS"
    assert manifest["moments"] == 3
    assert manifest["forbidden_language_hit_count"] == 0
    assert (tmp_path / "B9_FRENCH_TRADER_SCENE_REPORT_V0.md").exists()
    assert (tmp_path / "B9_FRENCH_TRADER_SCENE_REPORT_ROWS_V0.csv").exists()
    report = _load(tmp_path / "B9_FRENCH_TRADER_SCENE_REPORT_V0.json")
    first = report["moment_reports"][0]
    for section in REPORT_SECTIONS:
        assert first.get(section)
    md = (tmp_path / "B9_FRENCH_TRADER_SCENE_REPORT_V0.md").read_text(encoding="utf-8")
    assert "Ce que b9 voit" in md
    assert "B9 ne cherche pas le signal" in md


def test_t0134_contract_flags_are_safe(tmp_path: Path) -> None:
    sample = ROOT / "samples" / "b9_french_trader_scene_report_v0" / "sample_t009_sequence_summary_french_report.json"
    manifest = mod.run(sample, tmp_path)
    assert manifest["read_only"] is True
    assert manifest["db_write"] is False
    assert manifest["dashboard"] is False
    assert manifest["telegram"] is False
    assert manifest["order_execution"] is False
    assert manifest["probability_of_success"] is False
