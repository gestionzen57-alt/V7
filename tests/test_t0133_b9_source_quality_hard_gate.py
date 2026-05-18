from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('build_t0133', ROOT / 'tools' / 'build_t0133_b9_source_quality_hard_gate.py')
mod = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod)


def test_t0133_sample_source_quality_gate_passes(tmp_path: Path) -> None:
    sample = ROOT / 'samples' / 'b9_source_quality_hard_gate_v0' / 'sample_t009_sequence_summary_source_quality.json'
    manifest = mod.build(sample, tmp_path)
    assert manifest['moments'] == 5
    assert manifest['missing_required_field_counts'] == {}
    assert manifest['forbidden_language_hits'] == []
    assert manifest['nuanced_promoted_to_confirmed_count'] == 0
    assert manifest['raw_unavailable_allowed_count'] == 0
    assert manifest['state_counts']['SOURCE_RAW_UNAVAILABLE_REJECTED'] == 1
    assert manifest['state_counts']['SOURCE_RAW_NUANCED'] == 2
    assert manifest['state_counts']['SOURCE_RAW_CONFIRMED'] == 2


def test_t0133_never_hardens_proxy_or_nuanced(tmp_path: Path) -> None:
    sample = ROOT / 'samples' / 'b9_source_quality_hard_gate_v0' / 'sample_t009_sequence_summary_source_quality.json'
    manifest = mod.build(sample, tmp_path)
    enriched = mod.load_json(tmp_path / 'B9_SOURCE_QUALITY_HARD_GATE_ENRICHED_SUMMARY_V0.json')
    moments = enriched['moments']
    nuanced = [m for m in moments if m.get('proxy_vs_raw_verdict') == 'NUANCED_BY_RAW']
    assert nuanced
    assert all(m['b9_confirmation_claim_allowed'] is False for m in nuanced)
    proxy = [m for m in moments if 'PROXY' in m.get('source_mode', '')]
    assert proxy
    assert all(m['b9_raw_claim_allowed'] is False for m in proxy)
    raw_full = [m for m in moments if m.get('data_visibility') == 'FULL_RAW']
    assert raw_full[0]['b9_raw_claim_allowed'] is True
