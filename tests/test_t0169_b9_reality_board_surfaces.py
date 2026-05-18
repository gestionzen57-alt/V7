import json
import csv
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("tools/build_t0169_b9_reality_board_surface_adapter_candidate.py")


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def test_t0169_generates_three_surfaces(tmp_path: Path):
    input_root = tmp_path / "inputs"
    output_root = tmp_path / "outputs"

    write_json(input_root / "B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.json", {
        "candidate_id": "B9C_TEST_001",
        "scene_state": "COUNTER_BREATH_REJECTED",
        "source_quality": "RAW_NUANCED",
        "data_visibility": "PARTIAL_BUT_DISPLAYABLE",
        "current_zone": "lower-zone active",
        "session": "London",
        "retest_state": "failed retest",
        "center_path": "center of gravity drifting lower",
    })
    write_json(input_root / "T0167_B9_B6_REALIGNMENT_V0.json", {
        "candidate_id": "B9C_TEST_001",
        "memory_family": "failed counter-breath after lower acceptance",
        "top_match_film_id": "GOLDEN_013",
        "technical_limits": ["memory alignment only"]
    })
    write_json(input_root / "B9_TRADER_ATTENTION_PACKET_V0.json", {
        "technical_risks": [{"risk": "STALE_PACKET", "details": "age beyond display freshness guard"}]
    })

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--core-root",
            str(tmp_path),
            "--input-root",
            str(input_root),
            "--output-root",
            str(output_root),
            "--strict-exit",
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["candidate_id"] == "B9C_TEST_001"
    assert payload["display_readiness"] in {"READY", "READY_WITH_WARNINGS", "PARTIAL"}

    read_model_path = output_root / "b9_reality_board_read_model_v01" / "B9_REALITY_BOARD_READ_MODEL_V01.json"
    scene_panel_path = output_root / "b9_reality_board_scene_panel_candidate_v01" / "B9_REALITY_BOARD_SCENE_PANEL_CANDIDATE_V01.json"
    adapter_path = output_root / "b9_reality_board_surface_adapter_candidate_v0" / "B9_REALITY_BOARD_SURFACE_ADAPTER_CANDIDATE_V0.json"
    assert read_model_path.exists()
    assert scene_panel_path.exists()
    assert adapter_path.exists()

    read_model = json.loads(read_model_path.read_text(encoding="utf-8"))
    assert read_model["candidate_id"] == "B9C_TEST_001"
    assert read_model["memory_family"] == "failed counter-breath after lower acceptance"
    assert read_model["display_doctrine"] == "Dashboard displays; it does not decide."

    adapter = json.loads(adapter_path.read_text(encoding="utf-8"))
    assert adapter["display_contract"]["decision_layer"] is False
    assert adapter["display_contract"]["database_write"] is False


def test_t0169_partial_when_inputs_missing(tmp_path: Path):
    output_root = tmp_path / "outputs"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--core-root",
            str(tmp_path),
            "--output-root",
            str(output_root),
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["display_readiness"] == "PARTIAL"
    assert "reality_board_integration_candidate" in payload["missing_inputs"]

    read_model = json.loads((output_root / "b9_reality_board_read_model_v01" / "B9_REALITY_BOARD_READ_MODEL_V01.json").read_text(encoding="utf-8"))
    assert read_model["scene_state"] == "SCENE_NOT_AVAILABLE"
    assert any("Missing inputs" in item for item in read_model["technical_limits"])


def test_t0169_input_inventory_csv(tmp_path: Path):
    input_root = tmp_path / "inputs"
    output_root = tmp_path / "outputs"
    write_json(input_root / "B9_LIVE_BRIEF_ONCE_V0.json", {
        "candidate_id": "B9C_TEST_002",
        "scene_state": "PULLBACK_ABSORBED",
    })

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--core-root",
            str(tmp_path),
            "--input-root",
            str(input_root),
            "--output-root",
            str(output_root),
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    inventory = output_root / "T0169_B9_REALITY_BOARD_DASHBOARD_SURFACES_INPUTS.csv"
    assert inventory.exists()
    rows = list(csv.DictReader(inventory.open("r", encoding="utf-8")))
    found = {row["input_key"]: row["found"] for row in rows}
    assert found["live_brief_once"] == "True"
