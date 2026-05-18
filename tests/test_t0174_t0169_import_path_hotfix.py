from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from tools.apply_t0174_t0169_import_path_hotfix import apply_or_report, VERSION


def make_core(tmp_path: Path, with_builder: bool = True, already: bool = False) -> Path:
    core = tmp_path / "core"
    tools = core / "tools"
    tools.mkdir(parents=True)
    if with_builder:
        text = "from pf_t009_reality_board_surface_adapter_candidate import run\n\nif __name__ == '__main__':\n    run(None)\n"
        if already:
            text = (
                "from pathlib import Path\nimport sys\n\n"
                "ROOT = Path(__file__).resolve().parents[1]\n"
                "if str(ROOT) not in sys.path:\n"
                "    sys.path.insert(0, str(ROOT))\n\n"
                + text
            )
        (tools / "build_t0169_b9_reality_board_surface_adapter_candidate.py").write_text(text, encoding="utf-8")
    return core


def test_t0174_applies_import_path_hotfix(tmp_path):
    core = make_core(tmp_path, with_builder=True, already=False)
    out = tmp_path / "out"
    result = apply_or_report(core, out, apply=True)
    assert result.version == VERSION
    assert result.hotfix_state == "PATCH_APPLIED"
    assert result.changed is True
    target = core / "tools" / "build_t0169_b9_reality_board_surface_adapter_candidate.py"
    text = target.read_text(encoding="utf-8")
    assert "Path(__file__).resolve().parents[1]" in text
    assert "sys.path.insert(0, str(ROOT))" in text
    assert (out / "T0174_T0169_IMPORT_PATH_HOTFIX_REPORT.json").exists()


def test_t0174_already_patched_is_idempotent(tmp_path):
    core = make_core(tmp_path, with_builder=True, already=True)
    out = tmp_path / "out"
    result = apply_or_report(core, out, apply=True)
    assert result.hotfix_state == "ALREADY_PATCHED"
    assert result.changed is False
    assert result.keys_present_after == ["Path(__file__).resolve().parents[1]", "sys.path.insert(0, str(ROOT))"]


def test_t0174_missing_builder_blocks_without_crashing(tmp_path):
    core = make_core(tmp_path, with_builder=False)
    out = tmp_path / "out"
    result = apply_or_report(core, out, apply=True)
    assert result.hotfix_state == "BLOCKED_T0169_BUILDER_NOT_FOUND"
    assert result.target_exists is False
    data = json.loads((out / "T0174_T0169_IMPORT_PATH_HOTFIX_REPORT.json").read_text(encoding="utf-8"))
    assert data["hotfix_state"] == "BLOCKED_T0169_BUILDER_NOT_FOUND"
