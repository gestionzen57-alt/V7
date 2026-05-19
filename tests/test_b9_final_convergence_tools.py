from pathlib import Path
import subprocess
import sys


def test_dashboard_patcher_injects_once(tmp_path):
    repo = tmp_path
    core = repo / "Core"
    core.mkdir()
    dash = core / "dashboard_powerflow_v74.html"
    dash.write_text("<html><body><h1>Dash</h1></body></html>", encoding="utf-8")
    script = Path(__file__).resolve().parents[1] / "tools" / "patch_dashboard_b9_b8_panels.py"
    subprocess.check_call([sys.executable, str(script), "--repo-root", str(repo)])
    first = dash.read_text(encoding="utf-8")
    assert "B9_B8_PANELS_START" in first
    subprocess.check_call([sys.executable, str(script), "--repo-root", str(repo)])
    second = dash.read_text(encoding="utf-8")
    assert second.count("B9_B8_PANELS_START") == 1


def test_final_state_validator_reports_missing(tmp_path):
    script = Path(__file__).resolve().parents[1] / "tools" / "validate_b9_final_state.py"
    proc = subprocess.run([sys.executable, str(script)], cwd=str(tmp_path), text=True, capture_output=True)
    assert proc.returncode == 1
    assert "MISSING" in proc.stdout
