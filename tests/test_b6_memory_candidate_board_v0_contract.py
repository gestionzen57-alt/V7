from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "build_b6_memory_candidate_board_v0_from_uploads.py"


def load_module():
    spec = importlib.util.spec_from_file_location("b6_board_builder", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_board_fields_contract():
    m = load_module()
    expected = [
        "date", "time_start", "time_end", "source_family", "summary_recovery_type",
        "source_mode", "data_visibility", "confidence_cap", "proxy_vs_raw_verdict",
        "proxy_raw_agreement_state", "source_quality_score", "source_quality_state",
        "b6_memory_candidate_score", "b6_memory_candidate_state", "raw_texture_role",
        "raw_delta_pips", "raw_range_pips", "raw_tick_count", "moment_type",
        "label_fr", "memory_candidate_reason", "technical_limits",
    ]
    assert m.BOARD_FIELDS == expected


def test_b6_states_contract():
    m = load_module()
    assert m.KEEP == "B6_KEEP_CANDIDATE"
    assert m.REVIEW == "B6_REVIEW_CANDIDATE"
    assert m.LOW_TRUST == "B6_LOW_TRUST_CANDIDATE"
    assert m.REJECT_RAW == "B6_REJECT_RAW_UNAVAILABLE"
    assert m.RAW_UNAVAILABLE == "RAW_UNAVAILABLE"
    assert "B6 ne prédit pas" in m.CAP_PHRASE
