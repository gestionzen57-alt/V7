from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_t0138_b9_real_replay_day_pack_runner import run

class Args:
    scan_root = str(ROOT)
    input_index_csv = ""
    input_dir = str(ROOT / "samples" / "b9_real_replay_day_pack_runner_v0")
    output_dir = str(ROOT / "outputs" / "b9_real_replay_day_pack_runner_v0_test")

def test_t0138_sample_batch_pass_or_partial():
    summary = run(Args())
    assert summary["files_processed"] >= 2
    # T0138 runs on real replay candidates. Depending on local field coverage,
    # candidate files may be KEEP or REVIEW; RAW_UNAVAILABLE-only samples must not
    # be promoted to KEEP. The hard contract is: usable candidates are not rejected,
    # forbidden language stays absent, and the batch remains read-only.
    assert summary["files_keep"] + summary["files_review"] >= 2
    assert summary["files_rejected"] >= 1
    assert summary["total_moments"] >= 3
    assert summary["forbidden_language_files"] == 0
    assert summary["read_only"] is True
    assert summary["buy_sell"] is False
    assert summary["probability_of_success"] is False


def test_t0138_outputs_are_written():
    out = Path(Args.output_dir)
    assert (out / "B9_REAL_REPLAY_DAY_RUNNER_V0.json").exists()
    payload = json.loads((out / "B9_REAL_REPLAY_DAY_RUNNER_V0.json").read_text(encoding="utf-8"))
    assert payload["summary"]["read_only"] is True
    assert (out / "B9_REAL_REPLAY_DAY_RESULTS_V0.csv").exists()
    assert (out / "B9_REAL_REPLAY_DAY_RUNNER_V0.md").exists()
