from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def test_direct_cli_output_is_semantic_clean():
    subprocess.run(
        [sys.executable, str(ROOT / "patch" / "pf_reality_board_state_once.py"), "--symbol", "GBPUSD"],
        cwd=str(ROOT),
        check=True,
    )
    path = ROOT / "output" / "dashboard_surface" / "GBPUSD" / "reality_board_state.json"
    state = json.loads(path.read_text(encoding="utf-8"))
    assert state.get("semantic_display_cleanup") == "V8_DIRECT_OUTPUT"
    for key in ("htf", "mtf", "ltf"):
        summary = state["time_profile_roles"][key]["summary_fr"]
        assert "events_total" not in summary
        assert "{" not in summary
        assert len(summary) < 220
    text = state["telegram_candidate"]["text_fr"]
    assert "GBPUSD - Reality Board" in text
    assert "Alternative : Alternative :" not in text
