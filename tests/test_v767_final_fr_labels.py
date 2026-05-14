from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
RAW = [
    "DATA FIRST",
    "REALITY BOARD",
    "ALIGNED_OR_PARTIAL",
    "LATE_HIGH_REJECTION_WITH_DEEP_UNWIND",
    "READING_PARTIAL",
    "HIGH_ZONE_EXHAUSTION_RISK",
]

def test_dashboard_static_labels_are_final_fr():
    for rel in ["dashboard_v76_terrain_panel.js", "Core/dashboard_v76_terrain_panel.js"]:
        text = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
        assert "DATA FIRST" not in text
        assert "REALITY BOARD" not in text
        assert "RÉALITÉ MARCHÉ" in text

def test_generated_reality_board_has_final_fr_display_fields():
    subprocess.run(
        [sys.executable, str(ROOT / "patch" / "pf_reality_board_state_once.py"), "--symbol", "GBPUSD"],
        cwd=str(ROOT),
        check=True,
    )
    state = json.loads((ROOT / "output" / "dashboard_surface" / "GBPUSD" / "reality_board_state.json").read_text(encoding="utf-8"))
    assert state.get("final_fr_labels_polish") == "V1_DISPLAY_ONLY"
    blob = json.dumps({
        "labels": state.get("labels_fr", {}),
        "display": state.get("display_fr", {}),
        "telegram": state.get("telegram_candidate", {}).get("text_fr", ""),
    }, ensure_ascii=False)
    for raw in RAW:
        assert raw not in blob
    assert "RÉALITÉ MARCHÉ" in blob
    assert "LECTURE TERRAIN" in blob
    assert "alignement partiel" in blob
    assert "high tardif rejeté puis unwind profond" in blob
    assert "lecture partielle" in blob
    assert "risque d’épuisement en zone haute" in blob
