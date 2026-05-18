from pathlib import Path
import importlib.util
import sys

spec = importlib.util.spec_from_file_location(
    "apply_t0158",
    Path(__file__).resolve().parents[1] / "tools" / "apply_t0158_t0148_json_contract_patch.py",
)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)  # type: ignore[union-attr]


OLD_SOURCE = '''
def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("matches", "rows", "items", "candidates", "moments", "false_positive_rows"):
            if isinstance(value.get(key), list):
                return value[key]
    return []
'''


def test_patch_source_text_adds_similarity_and_context_keys():
    patched, changed = mod.patch_source_text(OLD_SOURCE)
    assert changed is True
    assert '"similar_films"' in patched
    assert '"false_positive_contexts"' in patched
    assert '"matches"' in patched
    assert '"false_positive_rows"' in patched


def test_patch_is_idempotent():
    first, changed_first = mod.patch_source_text(OLD_SOURCE)
    second, changed_second = mod.patch_source_text(first)
    assert changed_first is True
    assert changed_second is False
    assert second.count("similar_films") == 1
    assert second.count("false_positive_contexts") == 1


def test_apply_patch_writes_report(tmp_path):
    target = tmp_path / "pf_t009_live_brief_once_runner.py"
    target.write_text(OLD_SOURCE, encoding="utf-8")
    report_path = tmp_path / "report.json"
    report = mod.apply_patch(target, report_path)
    assert report.patch_state == "PATCH_APPLIED"
    assert report.changed is True
    assert report_path.exists()
    text = target.read_text(encoding="utf-8")
    assert "similar_films" in text
    assert "false_positive_contexts" in text


def test_apply_patch_ignores_forbidden_terms_in_source_guards(tmp_path):
    target = tmp_path / "pf_t009_live_brief_once_runner.py"
    source = OLD_SOURCE + "\nFORBIDDEN_TERMS = ('BUY', 'SELL')\n"
    target.write_text(source, encoding="utf-8")
    report_path = tmp_path / "report.json"
    report = mod.apply_patch(target, report_path)
    assert report.patch_state == "PATCH_APPLIED"
    assert report.forbidden_language_hits == []
