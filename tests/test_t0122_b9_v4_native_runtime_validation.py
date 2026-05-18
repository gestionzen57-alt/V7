from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_t0122_b9_v4_native_runtime_validation as t0122


def test_fallback_enriches_all_required_fields(tmp_path: Path) -> None:
    sample = {
        "moments": [
            {"time_start": "08:00", "time_end": "08:14", "label_fr": "Effort sans résultat", "center_delta_pips": 0.1},
            {"time_start": "10:00", "time_end": "10:23", "label_fr": "Vague progressive", "center_delta_pips": 12.0},
        ]
    }
    enriched = t0122.fallback_enrich_summary(sample)
    moments = t0122.find_moments(enriched)
    assert len(moments) == 2
    for moment in moments:
        for field in t0122.REQUIRED_FIELDS:
            assert moment.get(field) not in (None, ""), field


def test_cli_outputs_manifest_and_pass_state(tmp_path: Path) -> None:
    sample_path = tmp_path / "sample.json"
    sample_path.write_text(json.dumps({
        "moments": [
            {"time_start": "13:00", "time_end": "13:08", "label_fr": "Vague progressive", "center_delta_pips": 6.6}
        ]
    }, ensure_ascii=False), encoding="utf-8")
    out_dir = tmp_path / "out"
    report = t0122.run(t0122.parse_args([
        "--sequence-summary-json", str(sample_path),
        "--summarizer-py", str(tmp_path / "missing_summarizer.py"),
        "--output-dir", str(out_dir),
    ]))
    assert report["input_moments"] == 1
    assert report["total_missing_required_fields"] == 0
    assert report["runtime_validation_state"] in {"PASS", "PASS_WITH_SUMMARIZER_HOOK_WARNING"}
    assert (out_dir / "B9_V4_NATIVE_RUNTIME_VALIDATION_MANIFEST.json").exists()
    assert (out_dir / "B9_V4_NATIVE_RUNTIME_VALIDATION_V0.zip").exists()
