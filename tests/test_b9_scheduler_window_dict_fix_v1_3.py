from __future__ import annotations

import py_compile
from pathlib import Path


def test_scheduler_window_dict_fix_markers() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (root / "Core" / "scheduler_powerflow_turbo_wrapper.py").read_text(encoding="utf-8")
    assert "_b9_build_window_payload" in text
    assert '"B9_WINDOW_DICT_V1"' in text
    assert "Sending window payload contract=dict" in text
    assert "Retrying with compact dict tick window" in text
    assert 'name == "run_powerflow_live_stack_once.py"' in text
    assert '"--once", "--symbols"' in text  # still only for scheduler_powerflow.py


def test_scheduler_py_compile() -> None:
    root = Path(__file__).resolve().parents[1]
    py_compile.compile(str(root / "Core" / "scheduler_powerflow_turbo_wrapper.py"), doraise=True)
