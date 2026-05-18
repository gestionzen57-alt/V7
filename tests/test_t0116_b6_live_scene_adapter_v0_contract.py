import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "build_t0116_b6_live_scene_adapter_v0.py"
SAMPLE = ROOT / "samples" / "b6_live_scene_adapter_v0" / "sample_b9_live_scene_v0.json"


def test_t0116_self_test_passes():
    result = subprocess.run([sys.executable, str(SCRIPT), "--self-test"], cwd=str(ROOT), text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert "SELF_TEST_PASS" in result.stdout


def test_t0116_generates_t0115_compatible_payload(tmp_path):
    out = tmp_path / "out"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--input-json", str(SAMPLE), "--output-dir", str(out)],
        cwd=str(ROOT), text=True, capture_output=True
    )
    assert result.returncode == 0, result.stderr
    payload_path = out / "B6_LIVE_SCENE_QUERY_PAYLOAD_V0.json"
    manifest_path = out / "B6_LIVE_SCENE_ADAPTER_MANIFEST_V0.json"
    assert payload_path.exists()
    assert manifest_path.exists()
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["memory_family"] == "DIRECTIONAL_PROGRESS_MEMORY"
    assert payload["memory_family_origin"].startswith("heuristic")
    for key in ["base", "reaction", "projection", "judgment"]:
        assert payload.get(key)
    assert manifest["integrity_checks"]["db_write"] is False
    assert manifest["query_scene"]["t0115_compatible"] is True
