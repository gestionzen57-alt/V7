from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


def write_board(path: Path) -> None:
    fields = [
        "date","time_start","time_end","source_family","summary_recovery_type","source_mode","data_visibility","confidence_cap",
        "proxy_vs_raw_verdict","proxy_raw_agreement_state","source_quality_score","source_quality_state",
        "b6_memory_candidate_score","b6_memory_candidate_state","raw_texture_role","raw_delta_pips","raw_range_pips",
        "raw_tick_count","moment_type","label_fr","memory_candidate_reason","technical_limits"
    ]
    rows = [
        {
            "date":"2026-05-06","time_start":"2026-05-06T08:00:00+00:00","time_end":"2026-05-06T08:10:00+00:00",
            "source_family":"RECOVERED_EXISTING_B9_SUMMARY","summary_recovery_type":"RECOVERED_EXISTING_B9_SUMMARY",
            "source_mode":"M1_BAR_PROXY","data_visibility":"RECONSTRUCTED","confidence_cap":"0.35",
            "proxy_vs_raw_verdict":"CONFIRMED_BY_RAW","proxy_raw_agreement_state":"CONFIRMED_BY_RAW",
            "source_quality_score":"0.9","source_quality_state":"SOURCE_QUALITY_STRONG","b6_memory_candidate_score":"0.88",
            "b6_memory_candidate_state":"B6_KEEP_CANDIDATE","raw_texture_role":"RAW_PROGRESS_CONFIRMED",
            "raw_delta_pips":"5.0","raw_range_pips":"7.0","raw_tick_count":"120",
            "moment_type":"FLOW_DIRECTIONAL_DISPLACEMENT","label_fr":"Déplacement directionnel proxy",
            "memory_candidate_reason":"keep test","technical_limits":"read-only; no BUY/SELL"
        },
        {
            "date":"2026-05-06","time_start":"2026-05-06T09:00:00+00:00","time_end":"2026-05-06T09:10:00+00:00",
            "source_family":"FORCE_SNAPSHOT_DERIVED","summary_recovery_type":"FORCE_SNAPSHOT_DERIVED",
            "source_mode":"TF30_BAR_PROXY","data_visibility":"RECONSTRUCTED_FORCE_SNAPSHOT_DERIVED","confidence_cap":"0.25",
            "proxy_vs_raw_verdict":"NUANCED_BY_RAW","proxy_raw_agreement_state":"NUANCED_BY_RAW",
            "source_quality_score":"0.35","source_quality_state":"SOURCE_QUALITY_LOW_TRUST","b6_memory_candidate_score":"0.39",
            "b6_memory_candidate_state":"B6_LOW_TRUST_CANDIDATE","raw_texture_role":"RAW_ROTATION_CONFIRMED",
            "raw_delta_pips":"1.0","raw_range_pips":"10.0","raw_tick_count":"50",
            "moment_type":"FLOW_ROTATIONAL","label_fr":"Rotation / respiration de zone",
            "memory_candidate_reason":"low trust test","technical_limits":"low trust"
        },
        {
            "date":"2026-05-06","time_start":"2026-05-06T10:00:00+00:00","time_end":"2026-05-06T10:10:00+00:00",
            "source_family":"FORCE_SNAPSHOT_DERIVED","summary_recovery_type":"FORCE_SNAPSHOT_DERIVED",
            "source_mode":"TF30_BAR_PROXY","data_visibility":"RECONSTRUCTED_FORCE_SNAPSHOT_DERIVED","confidence_cap":"0.25",
            "proxy_vs_raw_verdict":"RAW_UNAVAILABLE","proxy_raw_agreement_state":"RAW_UNAVAILABLE",
            "source_quality_score":"0.0","source_quality_state":"SOURCE_QUALITY_REJECT_RAW_UNAVAILABLE","b6_memory_candidate_score":"0.0",
            "b6_memory_candidate_state":"B6_REJECT_RAW_UNAVAILABLE","raw_texture_role":"RAW_UNAVAILABLE",
            "raw_delta_pips":"0","raw_range_pips":"0","raw_tick_count":"0",
            "moment_type":"FLOW_DIRECTIONAL_DISPLACEMENT","label_fr":"Déplacement directionnel proxy",
            "memory_candidate_reason":"reject test","technical_limits":"raw unavailable"
        },
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_t0113_builder_contract(tmp_path: Path) -> None:
    input_csv = tmp_path / "B6_MEMORY_CANDIDATE_BOARD_V0.csv"
    out_dir = tmp_path / "out"
    write_board(input_csv)
    script = Path(__file__).resolve().parents[1] / "tools" / "build_t0113_b6_film_card_builder_v0.py"
    result = subprocess.run(
        [sys.executable, str(script), "--input-csv", str(input_csv), "--output-dir", str(out_dir)],
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(result.stdout)
    assert payload["input_rows"] == 3
    assert payload["active_film_cards"] == 1
    assert payload["low_trust_rows"] == 1
    assert payload["rejected_rows"] == 1
    assert (out_dir / "B6_FILM_CARDS_V0.csv").exists()
    assert (out_dir / "B6_FILM_CARDS_V0.json").exists()
    assert (out_dir / "B6_FILM_CARDS_V0.md").exists()
    assert (out_dir / "B6_FILM_CARD_LOW_TRUST_AUDIT_V0.csv").exists()
    assert (out_dir / "B6_FILM_CARD_REJECTED_RAW_UNAVAILABLE_V0.csv").exists()
    assert (out_dir / "B6_FILM_LIBRARY_V0.zip").exists()

    with (out_dir / "B6_FILM_CARDS_V0.csv").open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    card = rows[0]
    assert card["film_id"].startswith("B6FC_20260506_")
    assert card["summary_recovery_type"] == "RECOVERED_EXISTING_B9_SUMMARY"
    assert card["raw_agreement"] == "CONFIRMED_BY_RAW"
    assert "no prediction" in card["limits"]
    assert "BUY/SELL" in card["limits"]
