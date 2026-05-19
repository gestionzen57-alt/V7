from __future__ import annotations

import py_compile
from pathlib import Path


def test_validate_b9_production_final_py_compile() -> None:
    root = Path(__file__).resolve().parents[1]
    py_compile.compile(str(root / "Core" / "validate_b9_production_final.py"), doraise=True)


def test_validation_pack_markers() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "Core" / "validate_b9_production_final.py").read_text(encoding="utf-8")
    assert "check_flask" in text
    assert "check_tick_archive" in text
    assert "run_scheduler_loop" in text
    assert "RAPPORT_VALIDATION_B9_PRODUCTION_FINAL.md" in text
