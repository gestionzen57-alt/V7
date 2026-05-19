from __future__ import annotations

from pathlib import Path

from b9_dashboard_panel_patcher_v2 import (
    CSS_MARKER_BEGIN,
    HTML_MARKER_BEGIN,
    JS_MARKER_BEGIN,
    find_dashboard_file,
    patch_dashboard,
    patch_from_root,
)


def write_html(path: Path, title: str = "Dashboard") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""<!doctype html>
<html>
<head><title>{title}</title><style>.panel{{color:white;}}</style></head>
<body><div id="main-dashboard"><p>Existing panel</p></div></body>
</html>
""",
        encoding="utf-8",
    )


def test_find_dashboard_prefers_dashboard_v74(tmp_path: Path) -> None:
    fallback = tmp_path / "dashboard_live_v7.2.html"
    preferred = tmp_path / "dashboard_v74.html"
    write_html(fallback, "Fallback")
    write_html(preferred, "Preferred")

    assert find_dashboard_file(tmp_path) == preferred


def test_find_dashboard_falls_back_to_equivalent(tmp_path: Path) -> None:
    fallback = tmp_path / "templates" / "dashboard.html"
    write_html(fallback, "Template")

    assert find_dashboard_file(tmp_path) == fallback


def test_patch_dashboard_injects_html_css_js_and_backup(tmp_path: Path) -> None:
    dashboard = tmp_path / "dashboard_v74.html"
    write_html(dashboard)

    result = patch_dashboard(dashboard)
    text = dashboard.read_text(encoding="utf-8")

    assert result.status == "PATCHED"
    assert result.backup_path.exists()
    assert HTML_MARKER_BEGIN in text
    assert CSS_MARKER_BEGIN in text
    assert JS_MARKER_BEGIN in text
    assert "Nodes Terrain B9 (Live)" in text
    assert "/api/b9-nodes-live" in text


def test_patch_dashboard_is_idempotent(tmp_path: Path) -> None:
    dashboard = tmp_path / "dashboard_v74.html"
    write_html(dashboard)

    first = patch_dashboard(dashboard)
    first_text = dashboard.read_text(encoding="utf-8")
    second = patch_dashboard(dashboard)
    second_text = dashboard.read_text(encoding="utf-8")

    assert first.status == "PATCHED"
    assert second.status == "ALREADY_PRESENT"
    assert first_text == second_text
    assert second_text.count(HTML_MARKER_BEGIN) == 1
    assert second_text.count(CSS_MARKER_BEGIN) == 1
    assert second_text.count(JS_MARKER_BEGIN) == 1


def test_patch_from_root_uses_dashboard_v74(tmp_path: Path) -> None:
    dashboard = tmp_path / "dashboard_v74.html"
    write_html(dashboard)

    result = patch_from_root(tmp_path)

    assert result.dashboard_path == dashboard.resolve()
    assert result.html_present
    assert result.css_present
    assert result.js_present
