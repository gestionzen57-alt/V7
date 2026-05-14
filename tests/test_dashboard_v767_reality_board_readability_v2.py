from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_reality_board_readability_v2_in_core_dashboard_js():
    text = (ROOT / "Core" / "dashboard_v76_terrain_panel.js").read_text(encoding="utf-8", errors="replace")
    assert "PF_V767_READABILITY_POLISH_V2" in text
    assert "pf-v767-k" in text
    assert "pf-v767-v" in text
    assert "grid-template-columns:repeat(3" in text
    assert "POWERFLOW V7.6.7 - REALITY BOARD GBPUSD" in text

def test_reality_board_readability_v2_in_root_dashboard_js():
    text = (ROOT / "dashboard_v76_terrain_panel.js").read_text(encoding="utf-8", errors="replace")
    assert "PF_V767_READABILITY_POLISH_V2" in text
    assert "pf-v767-k" in text
    assert "POWERFLOW V7.6.7 - REALITY BOARD GBPUSD" in text
