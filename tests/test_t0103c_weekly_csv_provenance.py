from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.t0103c_propagate_weekly_provenance import main  # noqa: E402


def read_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def test_t0103c_propagates_force_snapshot_provenance_to_existing_csv(tmp_path):
    out = tmp_path / "outputs"
    folder = out / "20260504_0000_0059"
    folder.mkdir(parents=True)

    payload = {
        "summary_recovery_type": "FORCE_SNAPSHOT_DERIVED",
        "source_mode": "TF30_BAR_PROXY",
        "data_visibility": "RECONSTRUCTED_FORCE_SNAPSHOT_DERIVED",
        "confidence_cap": 0.25,
        "source_table": "force_snapshots_v2",
        "source_timeframe": 30,
        "moments": [
            {
                "moment_id": "B9M_1",
                "time_start": "2026-05-04T00:00:00Z",
                "time_end": "2026-05-04T00:30:00Z",
                "moment_type": "T009_MOMENT_FORCE_SNAPSHOT_DERIVED",
                "label_fr": "Scene derivee force snapshot",
                "proxy_vs_raw_verdict": "CONFIRMED_BY_RAW",
            }
        ],
    }
    (folder / "t009_sequence_summary_raw_calibrated.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
    )

    csv_path = out / "B9_WEEK_CALIBRATION_RESULTS_20260504_20260515.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "moment_id",
                "time_start",
                "time_end",
                "moment_type",
                "label_fr",
                "proxy_vs_raw_verdict",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "moment_id": "B9M_1",
                "time_start": "2026-05-04T00:00:00Z",
                "time_end": "2026-05-04T00:30:00Z",
                "moment_type": "T009_MOMENT_FORCE_SNAPSHOT_DERIVED",
                "label_fr": "Scene derivee force snapshot",
                "proxy_vs_raw_verdict": "CONFIRMED_BY_RAW",
            }
        )

    assert main(["--output-root", str(out)]) == 0

    rows = read_csv(csv_path)
    assert rows[0]["summary_recovery_type"] == "FORCE_SNAPSHOT_DERIVED"
    assert rows[0]["source_mode"] == "TF30_BAR_PROXY"
    assert rows[0]["data_visibility"] == "RECONSTRUCTED_FORCE_SNAPSHOT_DERIVED"
    assert rows[0]["confidence_cap"] == "0.25"
    assert rows[0]["source_table"] == "force_snapshots_v2"
    assert rows[0]["source_timeframe"] == "30"

    md = (out / "B9_WEEK_CALIBRATION_RESULTS_T0103C_PROVENANCE.md").read_text(encoding="utf-8")
    assert "T0103C_WEEKLY_CSV_PROVENANCE_PROPAGATED" in md
    assert "FORCE_SNAPSHOT_DERIVED" in md


def test_t0103c_extracts_moment_source_profile_over_root(tmp_path):
    out = tmp_path / "outputs"
    folder = out / "20260505_0000_0059"
    folder.mkdir(parents=True)

    payload = {
        "summary_recovery_type": "FORCE_SNAPSHOT_DERIVED",
        "source_mode": "TF5_BAR_PROXY",
        "data_visibility": "RECONSTRUCTED_FORCE_SNAPSHOT_DERIVED",
        "confidence_cap": 0.25,
        "source_table": "force_snapshots_v2",
        "source_timeframe": 5,
        "moments": [
            {
                "moment_id": "B9M_2",
                "time_start": "2026-05-05T00:00:00Z",
                "time_end": "2026-05-05T00:01:00Z",
                "moment_type": "T009_MOMENT_FORCE_SNAPSHOT_DERIVED",
                "label_fr": "Scene M1",
                "source_profile": {
                    "source_mode": "M1_BAR_PROXY",
                    "data_visibility": "RECONSTRUCTED_FORCE_SNAPSHOT_DERIVED",
                    "confidence_cap": 0.35,
                    "source_table": "force_snapshots_v2",
                    "source_timeframe": 1,
                },
            }
        ],
    }
    (folder / "t009_sequence_summary_raw_calibrated.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8"
    )

    assert main(["--output-root", str(out)]) == 0
    csv_path = out / "B9_WEEK_CALIBRATION_RESULTS_T0103C_PROVENANCE.csv"
    rows = read_csv(csv_path)
    assert rows[0]["summary_recovery_type"] == "FORCE_SNAPSHOT_DERIVED"
    assert rows[0]["source_mode"] == "M1_BAR_PROXY"
    assert rows[0]["confidence_cap"] == "0.35"
    assert rows[0]["source_timeframe"] == "1"


def test_t0103c_no_decision_language():
    text = (ROOT / "tools" / "t0103c_propagate_weekly_provenance.py").read_text(encoding="utf-8").lower()
    forbidden = ["buy", "sell", "acheter", "vendre", "take profit", "stop loss"]
    for word in forbidden:
        assert word not in text
