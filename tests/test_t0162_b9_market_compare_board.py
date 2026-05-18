from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / 'tools' / 'build_t0162_b9_market_compare_board.py'
spec = importlib.util.spec_from_file_location('t0162', MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def test_t0162_sample_board_outputs(tmp_path: Path) -> None:
    sample_dir = Path(__file__).resolve().parents[1] / 'samples' / 'b9_market_compare_board_v0'
    board = mod.build_board('sample', Path(__file__).resolve().parents[1], sample_dir, tmp_path, top_k=5)
    assert board['board_state'] == 'PASS'
    assert board['doctrine']['compare_is_not_predict'] is True
    assert board['doctrine']['no_buy_sell'] is True
    assert board['compare_summary']['match_count'] >= 2
    assert board['compare_summary']['golden_match_count'] >= 1
    assert board['source_quality_summary']['verdict'] in {
        'COMPARISON_ALLOWED_SOURCE_QUALITY_READABLE',
        'COMPARISON_ALLOWED_SOURCE_QUALITY_LIMITED',
    }
    assert (tmp_path / 'B9_MARKET_COMPARE_BOARD_V0.json').exists()
    assert (tmp_path / 'B9_MARKET_COMPARE_BOARD_V0.md').exists()
    assert (tmp_path / 'B9_MARKET_COMPARE_BOARD_MATCHES_V0.csv').exists()
    assert (tmp_path / 'B9_MARKET_COMPARE_BOARD_DIFFERENCES_V0.csv').exists()
    assert (tmp_path / 'B9_MARKET_COMPARE_BOARD_TECHNICAL_RISKS_V0.csv').exists()
    # Backward-compatible aliases remain available for any early T0162 consumer.
    assert (tmp_path / 'B9_MARKET_COMPARE_BOARD_V0_MATCHES_V0.csv').exists()


def test_t0162_runtime_missing_inputs_blocks_cleanly(tmp_path: Path) -> None:
    empty_core = tmp_path / 'empty_core'
    empty_core.mkdir()
    board = mod.build_board('runtime', empty_core, empty_core, tmp_path / 'out', top_k=3)
    assert board['board_state'] == 'BLOCKED_MISSING_INPUTS'
    assert board['input_summary']['required_inputs_found'] == 0
    risk_codes = {r['risk_code'] for r in board['technical_risks']}
    assert 'MISSING_REQUIRED_INPUT' in risk_codes
    assert board['source_quality_summary']['verdict'] == 'COMPARISON_BLOCKED_REQUIRED_INPUT_MISSING'


def test_t0162_recursive_runtime_discovery(tmp_path: Path) -> None:
    core = tmp_path / 'core'
    nested = core / 'outputs' / 'custom_nested_board_inputs'
    nested.mkdir(parents=True)
    (nested / 'B9_LIVE_BRIEF_ONCE_V0.json').write_text(json.dumps({'symbol': 'GBPUSD', 'current_scene': 'LOWER_ZONE_RANGE_ACTIVE', 'memory_family': 'LOWER_LOCK'}), encoding='utf-8')
    (nested / 'B9_TRADER_ATTENTION_PACKET_V0.json').write_text(json.dumps({'session': 'LONDON', 'retest': 'RETEST_UNKNOWN', 'center_path': 'CENTER_DRIFT_DOWN'}), encoding='utf-8')
    (nested / 'T0150_B9_GOLDEN_TERRAIN_CASES_V1.csv').write_text('case_id,case_label,session,center_path\nG1,LOWER_ZONE_RANGE_ACTIVE,LONDON,CENTER_DRIFT_DOWN\n', encoding='utf-8')
    board = mod.build_board('runtime', core, core, tmp_path / 'out', top_k=3)
    assert board['input_summary']['required_inputs_found'] == 3
    assert board['board_state'] == 'PASS'
    notes = {r['note'] for r in board['input_summary']['inputs'] if r['found']}
    assert 'recursive_fallback' in notes
