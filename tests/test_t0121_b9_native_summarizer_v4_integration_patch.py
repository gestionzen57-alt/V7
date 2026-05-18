from __future__ import annotations
import json
from pathlib import Path
from pf_t009_sequence_summarizer_v4_contract import REQUIRED_V4_FIELDS, find_forbidden_language
from pf_t009_sequence_summarizer_v4_integration import enrich_summary_v4_safe, integration_probe
from tools.apply_t0121_b9_native_summarizer_v4_integration import patch_text


def test_v4_integration_enriches_required_fields():
    sample = json.loads(Path("samples/b9_native_summarizer_v4_integration_v0/sample_t009_sequence_summary_raw_calibrated.json").read_text(encoding="utf-8"))
    enriched = enrich_summary_v4_safe(sample)
    assert enriched["b9_v4_integration_state"] == "T0121_NATIVE_INTEGRATION_APPLIED"
    assert find_forbidden_language(enriched) == []
    for moment in enriched["moments"]:
        for field in REQUIRED_V4_FIELDS:
            assert field in moment
            assert moment[field] not in (None, "")


def test_apply_patch_text_is_idempotent_and_hooks_return_summary():
    src = "import json\n\ndef build():\n    summary = {'moments': []}\n    return summary\n"
    patched, report = patch_text(src)
    assert report["state"] == "PATCHED_NATIVE_RETURN_SUMMARY"
    assert "T0121_B9_NATIVE_SUMMARIZER_V4_INTEGRATION_START" in patched
    assert "return _t0121_b9_v4_enrich(summary)" in patched
    patched_again, report_again = patch_text(patched)
    assert report_again["state"] == "ALREADY_PATCHED"
    assert patched_again == patched
    assert integration_probe()["no_buy_sell"] is True
