from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_reality_board_injection_present_in_core_dashboard_js():
    core_js = ROOT / "Core" / "dashboard_v76_terrain_panel.js"
    assert core_js.exists()
    text = core_js.read_text(encoding="utf-8", errors="replace")
    assert "PF_V767_REALITY_BOARD_PANEL_BEGIN" in text
    assert "POWERFLOW V7.6.7" in text
    assert "REALITY BOARD GBPUSD" in text
    assert "time_profile_roles" in text

def test_dashboard_html_references_v76_panel_or_contains_runtime_loader():
    html = ROOT / "Core" / "dashboard_powerflow_v74.html"
    assert html.exists()
    text = html.read_text(encoding="utf-8", errors="replace")
    assert (
        "dashboard_v76_terrain_panel.js" in text
        or "PF_V767_REALITY_BOARD_PANEL_BEGIN" in text
        or "terrain packet" in text.lower()
    )
