import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from build_t0139_b9_session_replay_scorecard import build

class Args:
    scan_root = str(ROOT / "samples" / "b9_session_replay_scorecard_v0")
    input_index_csv = ""
    scan_csv = ""
    output_dir = str(ROOT / "outputs" / "b9_session_replay_scorecard_v0_test")

def test_t0139_session_scorecard_sample_pass():
    summary = build(Args())
    assert summary["files_processed"] >= 4
    assert summary["files_keep"] >= 2
    assert summary["files_rejected"] >= 1
    assert "LONDON" in summary["sessions_detected"]
    assert "OVERLAP" in summary["sessions_detected"] or "NY" in summary["sessions_detected"]
    assert summary["forbidden_language_files"] == 0

def test_t0139_outputs_exist():
    summary = build(Args())
    out = Path(Args.output_dir)
    assert (out / "B9_SESSION_REPLAY_SCORECARD_V0.md").exists()
    assert (out / "B9_SESSION_REPLAY_SCORECARD_ROWS_V0.csv").exists()
    assert (out / "B9_SESSION_REPLAY_SCORECARD_SESSION_COUNTS_V0.csv").exists()
    assert (out / "B9_SESSION_REPLAY_SCORECARD_V0.zip").exists()
    data = json.loads((out / "B9_SESSION_REPLAY_SCORECARD_V0.json").read_text(encoding="utf-8"))
    assert data["read_only"] is True
    assert data["db_write"] is False
    assert data["telegram"] is False
