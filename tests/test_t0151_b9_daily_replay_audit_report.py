from pathlib import Path

from pf_t009_daily_replay_audit_report import build_daily_replay_audit

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "samples" / "b9_daily_replay_audit_report_v0"


def test_t0151_sample_audit_counts(tmp_path):
    audit = build_daily_replay_audit(
        replay_results_csv=SAMPLES / "sample_b9_replay_results.csv",
        session_scorecard_csv=SAMPLES / "sample_b9_session_scorecard.csv",
        golden_cases_csv=SAMPLES / "sample_t0150_golden_cases.csv",
        output_dir=tmp_path,
    )
    assert audit["audit_state"] == "B9_DAILY_REPLAY_AUDIT_PARTIAL"
    assert audit["counts"]["files_or_moments_processed"] == 5
    assert audit["counts"]["seen_cleanly"] >= 2
    assert audit["counts"]["partial_or_fragile"] >= 2
    assert audit["counts"]["rejected_or_unusable"] == 1
    assert audit["forbidden_language_hits"] == []
    assert Path(audit["output_files"]["zip"]).exists()


def test_t0151_rejects_raw_unavailable(tmp_path):
    audit = build_daily_replay_audit(
        replay_results_csv=SAMPLES / "sample_b9_replay_results.csv",
        output_dir=tmp_path,
    )
    rejected = [r for r in audit["rows"] if r["audit_state"] == "B9_REJECTED_OR_UNUSABLE"]
    assert rejected
    assert all(r["raw_unavailable"] for r in rejected)
