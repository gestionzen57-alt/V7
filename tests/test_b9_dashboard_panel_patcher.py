from __future__ import annotations

from pathlib import Path

from b9_dashboard_panel_patcher import (
    CSS_START,
    HTML_START,
    JS_START,
    find_dashboard,
    patch_dashboard,
)


def _write_dashboard(path: Path) -> None:
    path.write_text(
        """
<!doctype html>
<html>
<head>
<style>
body { background: #000; }
</style>
</head>
<body>
<div id="main-dashboard">
<div class="panel">Existing panel</div>
</div>
<script>
console.log('existing');
</script>
</body>
</html>
""".strip(),
        encoding="utf-8",
    )


def test_find_dashboard_prefers_dashboard_v74(tmp_path: Path) -> None:
    (tmp_path / "static").mkdir()
    (tmp_path / "static" / "dashboard.html").write_text("<html></html>", encoding="utf-8")
    target = tmp_path / "dashboard_v74.html"
    target.write_text("<html></html>", encoding="utf-8")
    assert find_dashboard(tmp_path) == target


def test_patch_dashboard_injects_html_css_js_and_backup(tmp_path: Path) -> None:
    target = tmp_path / "dashboard_v74.html"
    _write_dashboard(target)

    report = patch_dashboard(target)
    text = target.read_text(encoding="utf-8")

    assert report.changed is True
    assert report.backup_path is not None
    assert report.backup_path.exists()
    assert HTML_START in text
    assert CSS_START in text
    assert JS_START in text
    assert "b9-terrain-panel" in text
    assert "fetchB9Nodes" in text


def test_patch_dashboard_is_idempotent(tmp_path: Path) -> None:
    target = tmp_path / "dashboard_v74.html"
    _write_dashboard(target)

    first = patch_dashboard(target)
    text_once = target.read_text(encoding="utf-8")
    second = patch_dashboard(target)
    text_twice = target.read_text(encoding="utf-8")

    assert first.changed is True
    assert second.changed is False
    assert text_once == text_twice
    assert text_twice.count(HTML_START) == 1
    assert text_twice.count(CSS_START) == 1
    assert text_twice.count(JS_START) == 1


def test_patch_dashboard_without_style_or_body(tmp_path: Path) -> None:
    target = tmp_path / "dashboard.html"
    target.write_text("<html><div>minimal</div></html>", encoding="utf-8")

    report = patch_dashboard(target)
    text = target.read_text(encoding="utf-8")

    assert report.html_present is True
    assert report.css_present is True
    assert report.js_present is True
    assert "<style>" in text
    assert "<script>" in text
