import json
import subprocess
import sys
from pathlib import Path


def test_t0123_cli_generates_required_outputs(tmp_path):
    sample = {
        "metadata": {"test": True},
        "moments": [
            {
                "time_start": "2026-05-15T08:00:00Z",
                "time_end": "2026-05-15T08:14:00Z",
                "label_fr": "Effort sans résultat",
                "source_mode": "M1_BAR_PROXY",
                "data_visibility": "RECONSTRUCTED",
                "proxy_vs_raw_verdict": "NUANCED_BY_RAW",
                "raw_delta_pips": 0.8,
                "raw_range_pips": 5.2,
                "raw_time_shift_min": 0,
            },
            {
                "time_start": "2026-05-15T10:11:00Z",
                "time_end": "2026-05-15T10:23:00Z",
                "label_fr": "Vague progressive",
                "source_mode": "M1_BAR_PROXY",
                "data_visibility": "RECONSTRUCTED",
                "proxy_vs_raw_verdict": "CONFIRMED_BY_RAW",
                "raw_delta_pips": 11.5,
                "raw_range_pips": 11.5,
            },
        ],
    }
    input_path = tmp_path / "before.json"
    input_path.write_text(json.dumps(sample), encoding="utf-8")
    out_dir = tmp_path / "out"
    script = Path(__file__).resolve().parents[1] / "tools" / "build_t0123_b9_v4_replay_runtime_comparison.py"
    res = subprocess.run([sys.executable, str(script), "--before-summary-json", str(input_path), "--output-dir", str(out_dir)], text=True, capture_output=True)
    assert res.returncode == 0, res.stdout + res.stderr
    report = json.loads((out_dir / "B9_V4_REPLAY_RUNTIME_COMPARISON_V0.json").read_text(encoding="utf-8"))
    assert report["before_moment_count"] == 2
    assert report["after_moment_count"] == 2
    assert report["total_missing_required_fields"] == 0
    assert report["runtime_comparison_state"].startswith("PASS")
    assert (out_dir / "B9_V4_REPLAY_RUNTIME_COMPARISON_V0.zip").exists()


def test_t0123_no_forbidden_language_in_generated_sample(tmp_path):
    sample = {"moments": [{"label_fr": "Centre de gravité qui descend", "raw_delta_pips": -7.0}]}
    input_path = tmp_path / "before.json"
    input_path.write_text(json.dumps(sample), encoding="utf-8")
    out_dir = tmp_path / "out"
    script = Path(__file__).resolve().parents[1] / "tools" / "build_t0123_b9_v4_replay_runtime_comparison.py"
    res = subprocess.run([sys.executable, str(script), "--before-summary-json", str(input_path), "--output-dir", str(out_dir)], text=True, capture_output=True)
    assert res.returncode == 0, res.stdout + res.stderr
    report = json.loads((out_dir / "B9_V4_REPLAY_RUNTIME_COMPARISON_V0.json").read_text(encoding="utf-8"))
    assert report["forbidden_language_hits"] == []
