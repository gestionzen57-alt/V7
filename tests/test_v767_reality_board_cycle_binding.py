from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_v767_reality_board_cycle_hook_is_bound():
    text = (ROOT / "run_powerflow_v76_telegram_cycle.ps1").read_text(encoding="utf-8", errors="replace")
    assert "PF_V767_REALITY_BOARD_CYCLE_HOOK_BEGIN" in text
    assert "PF_V767_REALITY_BOARD_CYCLE_HOOK_END" in text
    assert "pf_reality_board_state_once.py" in text
    assert '--symbol "GBPUSD"' in text
    assert "V7.6.7 REALITY BOARD REFRESH" in text
