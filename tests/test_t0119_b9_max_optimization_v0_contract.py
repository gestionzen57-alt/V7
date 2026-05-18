import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "build_t0119_b9_max_optimization_v0.py"


def test_t0119_cli_generates_contract(tmp_path):
    sample = tmp_path / "sample.json"
    sample.write_text(json.dumps({
        "moments": [
            {
                "source_mode": "M1_BAR_PROXY",
                "data_visibility": "RECONSTRUCTED",
                "proxy_vs_raw_verdict": "NUANCED_BY_RAW",
                "raw_texture_role": "RAW_FRICTION_CONFIRMED",
                "b9_effort_load": 4.2,
                "b9_effort_result_ratio": 8.0,
                "b9_directional_efficiency": 0.22,
                "raw_delta_pips": -0.3,
                "raw_range_pips": 2.1,
                "retest_source_fields_version": "T0110_RETEST_SOURCE_FIELDS_V0",
                "b9_retest_source_status": "RETEST_SOURCE_NOT_VISIBLE",
            }
        ]
    }), encoding="utf-8")
    out = tmp_path / "out"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--sequence-summary-json", str(sample), "--output-dir", str(out)],
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["version"] == "T0119_B9_MAX_OPTIMIZATION_V0"
    assert payload["input_moments"] == 1
    assert (out / "B9_MAX_OPTIMIZATION_V0.json").exists()
    assert (out / "B9_MAX_OPTIMIZATION_GAP_MATRIX_V0.csv").exists()
    assert (out / "B9_MAX_OPTIMIZATION_V0.zip").exists()


def test_t0119_outputs_keep_doctrine(tmp_path):
    sample = tmp_path / "sample.json"
    sample.write_text('{"moments": []}', encoding="utf-8")
    out = tmp_path / "out"
    subprocess.run(
        [sys.executable, str(SCRIPT), "--sequence-summary-json", str(sample), "--output-dir", str(out)],
        text=True,
        capture_output=True,
        check=True,
    )
    report = (out / "B9_MAX_OPTIMIZATION_V0.md").read_text(encoding="utf-8")
    assert "B9 ne cherche pas le signal" in report
    assert "Aucun BUY/SELL" in report
    manifest = json.loads((out / "B9_MAX_OPTIMIZATION_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["read_only"] is True
    assert manifest["db_writes"] is False
    assert manifest["telegram"] is False
