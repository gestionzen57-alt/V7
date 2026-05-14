from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_dashboard_semantic_display_css_present():
    text = (ROOT / "Core" / "dashboard_v76_terrain_panel.js").read_text(encoding="utf-8", errors="replace")
    assert "PF_V767_SEMANTIC_DISPLAY_CLEANUP_V4" in text
    assert "span:first-child::after" in text
    assert "Reality Board" in text
