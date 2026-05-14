from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_reality_board_visual_polish_in_core_dashboard_js():
    text = (ROOT / "Core" / "dashboard_v76_terrain_panel.js").read_text(encoding="utf-8", errors="replace")
    assert "PF_V767_VISUAL_POLISH_V1" in text
    assert "POWERFLOW V7.6.7 - REALITY BOARD GBPUSD" in text
    assert "width:calc(100% - 36px)" in text
    assert "max-height:240px" in text

def test_reality_board_visual_polish_in_root_dashboard_js():
    text = (ROOT / "dashboard_v76_terrain_panel.js").read_text(encoding="utf-8", errors="replace")
    assert "PF_V767_VISUAL_POLISH_V1" in text
    assert "POWERFLOW V7.6.7 - REALITY BOARD GBPUSD" in text
