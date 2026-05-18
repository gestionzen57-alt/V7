"""T0121 safe integration layer for B9 V4 sequence-summary enrichment."""
from __future__ import annotations
from typing import Any, MutableMapping
INTEGRATION_VERSION = "T0121_B9_NATIVE_SUMMARIZER_V4_INTEGRATION_V0"

def enrich_summary_v4_safe(summary: Any) -> Any:
    if not isinstance(summary, MutableMapping):
        return summary
    try:
        from pf_t009_sequence_summarizer_v4_contract import enrich_sequence_summary_v4
        enriched = enrich_sequence_summary_v4(summary)
        enriched["b9_v4_integration_version"] = INTEGRATION_VERSION
        enriched["b9_v4_integration_state"] = "T0121_NATIVE_INTEGRATION_APPLIED"
        return enriched
    except Exception as exc:
        out = dict(summary)
        out["b9_v4_integration_version"] = INTEGRATION_VERSION
        out["b9_v4_integration_state"] = "T0121_NATIVE_INTEGRATION_FAIL_OPEN"
        out["b9_v4_integration_error"] = f"{type(exc).__name__}: {exc}"
        return out

def integration_probe() -> dict:
    return {"version": INTEGRATION_VERSION, "state": "READY", "read_only": True, "no_db_write": True, "no_dashboard": True, "no_telegram": True, "no_buy_sell": True, "no_probability_of_success": True}
