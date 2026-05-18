from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_live_chain_contract_validator import run, VERSION


def sample_root() -> Path:
    root = Path(__file__).resolve().parents[1]
    candidates = [
        root / "samples" / "b9_live_chain_contract_validator_v0" / "core_root_sample",
        root / "samples" / "b9_live_chain_contract_validator_v0" / "b9_live_chain_contract_validator_v0" / "core_root_sample",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise AssertionError(f"T0172 sample core_root_sample missing. Checked: {candidates}")


def test_t0172_sample_contract_review_not_blocked(tmp_path):
    args = SimpleNamespace(core_root=str(sample_root()), output_dir=str(tmp_path / "out"), file_map=None)
    summary = run(args)
    assert summary["version"] == VERSION
    assert summary["steps_checked"] == 10
    assert summary["steps_found"] == 10
    assert summary["candidate_consistency_ok"] is True
    assert summary["candidate_id"] == "B9LSC_E49A7AEC65CE"
    assert summary["match_count"] == 3
    assert summary["top_match_film_id"] == "B6FC_20260511_1641_010496DB"
    assert summary["false_positive_context_available"] is True
    assert not summary["forbidden_language_hits"]
    assert summary["contract_state"] in {
        "B9_LIVE_CHAIN_CONTRACT_PASS",
        "B9_LIVE_CHAIN_CONTRACT_REVIEW_TECHNICAL_RISK",
    }


def test_t0172_missing_inputs_blocks(tmp_path):
    root = tmp_path / "empty_core"
    root.mkdir()
    args = SimpleNamespace(core_root=str(root), output_dir=str(tmp_path / "out"), file_map=None)
    summary = run(args)
    assert summary["contract_state"] == "B9_LIVE_CHAIN_CONTRACT_BLOCKED_MISSING_INPUTS"
    assert summary["missing_steps"]
    assert summary["steps_found"] == 0


def test_t0172_candidate_mismatch_blocks(tmp_path):
    import shutil
    src = sample_root()
    dst = tmp_path / "core"
    shutil.copytree(src, dst)
    path = dst / "outputs" / "b9_live_brief_once_v0" / "B9_LIVE_BRIEF_ONCE_V0.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["candidate_id"] = "B9LSC_OTHER"
    path.write_text(json.dumps(data), encoding="utf-8")
    args = SimpleNamespace(core_root=str(dst), output_dir=str(tmp_path / "out"), file_map=None)
    summary = run(args)
    assert summary["contract_state"] == "B9_LIVE_CHAIN_CONTRACT_BLOCKED_CANDIDATE_MISMATCH"
    assert summary["candidate_consistency_ok"] is False
