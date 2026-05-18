from pathlib import Path
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "apply_t0179_forbidden_language_surface_scan_hotfix.py"

def load_hotfix():
    assert SCRIPT.exists(), f"Missing hotfix script: {SCRIPT}"
    spec = importlib.util.spec_from_file_location("hotfix", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def test_t0179_script_exists_and_loads():
    mod = load_hotfix()
    assert mod is not None

def test_t0179_patch_text_mentions_surface_scan():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "surface" in text.lower()
    assert "forbidden" in text.lower()

def test_t0179_target_builder_exists_after_install():
    target = ROOT / "tools" / "build_t0175_b9_global_chain_contract_lock.py"
    assert target.exists()
