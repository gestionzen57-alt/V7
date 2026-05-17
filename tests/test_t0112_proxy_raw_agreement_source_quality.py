from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.t0112_proxy_raw_agreement_source_quality import compute_t0112, main  # noqa: E402


def test_confirmed_m1_proxy_scores_as_keep_candidate():
    row = {
        "summary_recovery_type": "FORCE_SNAPSHOT_DERIVED",
        "source_mode": "M1_BAR_PROXY",
        "confidence_cap": 0.35,
        "raw_coverage": "FULL",
        "proxy_vs_raw_verdict": "CONFIRMED_BY_RAW",
        "raw_texture_role": "RAW_PROGRESS_CONFIRMED",
        "raw_tick_count": 1200,
        "raw_range_pips": 15.0,
    }
    out = compute_t0112(row)
    assert out["proxy_raw_agreement_state"] == "PROXY_RAW_CONFIRMED_PROGRESS"
    assert out["source_quality_state"] in {"SOURCE_QUALITY_STRONG_FOR_PROXY", "SOURCE_QUALITY_USABLE_WITH_LIMITS"}
    assert out["b6_memory_candidate_state"] in {"B6_KEEP_CANDIDATE", "B6_REVIEW_CANDIDATE"}
    assert out["raw_unavailable_penalty"] == 0.0


def test_raw_unavailable_is_rejected_for_b6():
    row = {
        "summary_recovery_type": "FORCE_SNAPSHOT_DERIVED",
        "source_mode": "M1_BAR_PROXY",
        "confidence_cap": 0.35,
        "raw_coverage": "RAW_UNAVAILABLE",
        "proxy_vs_raw_verdict": "RAW_UNAVAILABLE",
        "raw_texture_role": "RAW_UNAVAILABLE",
        "raw_tick_count": 0,
        "raw_range_pips": 0,
    }
    out = compute_t0112(row)
    assert out["proxy_raw_agreement_state"] == "PROXY_RAW_UNAVAILABLE"
    assert out["source_quality_state"] == "SOURCE_QUALITY_RAW_MISSING"
    assert out["b6_memory_candidate_state"] == "B6_REJECT_RAW_UNAVAILABLE"
    assert out["raw_unavailable_penalty"] > 0


def test_fallback_timeframe_gets_penalty():
    row = {
        "summary_recovery_type": "FORCE_SNAPSHOT_DERIVED",
        "source_mode": "TF30_BAR_PROXY",
        "confidence_cap": 0.25,
        "source_timeframe": 30,
        "raw_coverage": "FULL",
        "proxy_vs_raw_verdict": "NUANCED_BY_RAW",
        "raw_texture_role": "RAW_ROTATION_CONFIRMED",
        "moment_type": "FLOW_DIRECTIONAL_DISPLACEMENT",
        "raw_tick_count": 3000,
        "raw_range_pips": 10,
    }
    out = compute_t0112(row)
    assert out["proxy_raw_agreement_state"] == "PROXY_DIRECTIONAL_NUANCED_BY_RAW_ROTATION"
    assert out["source_timeframe_penalty"] >= 0.18
    assert "COARSE_PROXY_TIMEFRAME" in out["t0112_reason_flags"]


def test_apply_updates_csv_and_json(tmp_path):
    out = tmp_path / "outputs"
    folder = out / "force_snapshot_20260507"
    folder.mkdir(parents=True)

    payload = {
        "summary_recovery_type": "FORCE_SNAPSHOT_DERIVED",
        "source_mode": "M1_BAR_PROXY",
        "data_visibility": "RECONSTRUCTED_FORCE_SNAPSHOT_DERIVED",
        "confidence_cap": 0.35,
        "moments": [
            {
                "moment_id": "m1",
                "time_start": "2026-05-07T01:00:00Z",
                "time_end": "2026-05-07T02:00:00Z",
                "moment_type": "FLOW_FRICTION_ABSORPTION_LIKE",
                "label_fr": "Friction proxy",
                "raw_coverage": "FULL",
                "proxy_vs_raw_verdict": "CONFIRMED_BY_RAW",
                "raw_texture_role": "RAW_PROGRESS_CONFIRMED",
                "raw_tick_count": 1234,
                "raw_range_pips": 12.0,
            }
        ],
    }
    json_path = folder / "t009_sequence_summary_raw_calibrated.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    csv_path = out / "B9_FORCE_SNAPSHOT_DERIVED_RAW_CALIBRATION_SHIFT0.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "moment_id",
                "time_start",
                "time_end",
                "moment_type",
                "label_fr",
                "summary_recovery_type",
                "source_mode",
                "data_visibility",
                "confidence_cap",
                "raw_coverage",
                "proxy_vs_raw_verdict",
                "raw_texture_role",
                "raw_tick_count",
                "raw_range_pips",
            ],
        )
        writer.writeheader()
        writer.writerow(payload["moments"][0] | {
            "summary_recovery_type": "FORCE_SNAPSHOT_DERIVED",
            "source_mode": "M1_BAR_PROXY",
            "data_visibility": "RECONSTRUCTED_FORCE_SNAPSHOT_DERIVED",
            "confidence_cap": 0.35,
        })

    assert main(["--output-root", str(out)]) == 0

    updated = json.loads(json_path.read_text(encoding="utf-8"))
    moment = updated["moments"][0]
    assert moment["t0112_proxy_raw_version"] == "T0112_PROXY_RAW_AGREEMENT_SOURCE_QUALITY_V0"
    assert "proxy_raw_agreement_state" in moment
    assert updated["t0112_proxy_raw_agreement"]["version"] == "T0112_PROXY_RAW_AGREEMENT_SOURCE_QUALITY_V0"

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["t0112_proxy_raw_version"] == "T0112_PROXY_RAW_AGREEMENT_SOURCE_QUALITY_V0"
    assert rows[0]["b6_memory_candidate_state"] in {"B6_KEEP_CANDIDATE", "B6_REVIEW_CANDIDATE"}


def test_no_decision_language():
    text = (ROOT / "tools" / "t0112_proxy_raw_agreement_source_quality.py").read_text(encoding="utf-8").lower()
    forbidden = ["buy now", "sell now", "acheter maintenant", "vendre maintenant", "take profit", "stop loss"]
    for phrase in forbidden:
        assert phrase not in text
