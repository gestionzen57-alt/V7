from pathlib import Path

from b9_dashboard_panel_patcher_v3 import (
    BACKUP_SUFFIX,
    CSS_START,
    HTML_START,
    JS_START,
    find_dashboard,
    patch_dashboard,
    translate_dashboard_text,
)


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_find_dashboard_prefers_dashboard_v74(tmp_path):
    fallback = write(tmp_path / "dashboard_live_v7.2.html", "<html></html>")
    preferred = write(tmp_path / "dashboard_v74.html", "<html></html>")
    assert find_dashboard(tmp_path) == preferred
    assert find_dashboard(tmp_path) != fallback


def test_find_dashboard_falls_back_to_static_dashboard(tmp_path):
    static_dashboard = write(tmp_path / "static" / "dashboard.html", "<html></html>")
    assert find_dashboard(tmp_path) == static_dashboard


def test_translate_dashboard_text_to_french():
    html, changed = translate_dashboard_text("PowerFlow Dashboard <button>Refresh</button> Loading...")
    assert changed is True
    assert "Tableau de Bord PowerFlow" in html
    assert "Actualiser" in html
    assert "Chargement..." in html


def test_patch_dashboard_injects_panel_css_js_translation_and_backup(tmp_path):
    dashboard = write(
        tmp_path / "dashboard_v74.html",
        "<html><head><style>.x{}</style></head><body><h1>PowerFlow Dashboard</h1></body></html>",
    )
    result = patch_dashboard(tmp_path)
    patched = dashboard.read_text(encoding="utf-8")

    assert result.changed is True
    assert result.dashboard_path == dashboard
    assert result.backup_path == dashboard.with_name(dashboard.name + BACKUP_SUFFIX)
    assert result.backup_path.exists()
    assert HTML_START in patched
    assert CSS_START in patched
    assert JS_START in patched
    assert "Tableau de Bord PowerFlow" in patched
    assert "Nodes Terrain B9" in patched
    assert "/api/b9-nodes-live" in patched


def test_patch_dashboard_is_idempotent(tmp_path):
    dashboard = write(tmp_path / "dashboard_v74.html", "<html><head></head><body></body></html>")
    first = patch_dashboard(tmp_path)
    first_text = dashboard.read_text(encoding="utf-8")
    second = patch_dashboard(tmp_path)
    second_text = dashboard.read_text(encoding="utf-8")

    assert first.html_present and first.css_present and first.js_present
    assert second_text == first_text
    assert second.changed is False
    assert second.html_present and second.css_present and second.js_present


def test_patch_dashboard_without_head_body_style(tmp_path):
    dashboard = write(tmp_path / "dashboard_v74.html", "PowerFlow Dashboard")
    result = patch_dashboard(tmp_path)
    patched = dashboard.read_text(encoding="utf-8")
    assert result.html_present is True
    assert result.css_present is True
    assert result.js_present is True
    assert "<style>" in patched
    assert "<script>" in patched
