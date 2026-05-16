import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pf_battlefield_flux_cross_symbol import CrossSymbolCoalitionDetector


class FakeBattlefieldFlux:
    def __init__(self, states):
        self.states = states

    def compute_state(self, symbol, lookback_min=30):
        return self.states.get(symbol, {"symbol": symbol, "events": []})


class FakeVisibilityChecker:
    def __init__(self, visibility):
        self.visibility = visibility

    def check_symbol_visibility(self, symbol, db_path=None):
        return self.visibility.get(symbol, {
            "coverage_state": "FULL",
            "role_allowed": "PRIMARY",
            "visibility_quality": 1.0,
            "technical_risks": [],
        })


def event(event_type="T009_BATTLE_LEVEL_BORN", battle=0.80, absorption=0.20, confidence=0.80):
    return {
        "event_type": event_type,
        "battle_score": battle,
        "absorption_score": absorption,
        "confidence": confidence,
        "source_mode": "TIMER_1S_SAMPLE",
        "data_visibility": "LIVE",
    }


def make_detector(states=None, visibility=None):
    detector = CrossSymbolCoalitionDetector()
    detector.bf = FakeBattlefieldFlux(states or {})
    detector.visibility_checker = FakeVisibilityChecker(visibility or {})
    return detector


def test_detector_init():
    detector = CrossSymbolCoalitionDetector()
    assert detector.states == {}
    assert detector.driver_analyzer is not None
    assert detector.visibility_checker is not None


def test_detect_coalition_empty():
    detector = CrossSymbolCoalitionDetector()
    result = detector.detect_coalition([])
    assert result["coalition_detected"] is False
    assert result["coalition_strength"] == 0.0


def test_detect_coalition_single_symbol_ignored():
    detector = CrossSymbolCoalitionDetector()
    result = detector.detect_coalition(["GBPUSD"])
    assert result["coalition_detected"] is False
    assert result["symbols_analyzed"] == ["GBPUSD"]


def test_detect_coalition_detected_with_convergence():
    detector = make_detector({
        "GBPUSD": {"events": [event()]},
        "EURUSD": {"events": [event()]},
        "AUDUSD": {"events": [event()]},
    })
    result = detector.detect_coalition(["GBPUSD", "EURUSD", "AUDUSD"])
    assert result["coalition_detected"] is True
    assert result["coalition_strength"] >= 0.60
    assert len(result["convergence_zones"]) == 1


def test_pair_driver_integration_present():
    detector = make_detector({
        "GBPUSD": {"events": [event(battle=0.90, absorption=0.20)]},
        "EURUSD": {"events": [event(battle=0.70, absorption=0.30)]},
    })
    result = detector.detect_coalition(["GBPUSD", "EURUSD"])
    assert "GBPUSD" in result["pair_drivers"]
    assert "driver_type" in result["pair_drivers"]["GBPUSD"]
    assert result["pair_drivers"]["GBPUSD"]["pair_pressure"] > 0


def test_data_visibility_qualification_primary():
    detector = make_detector(
        {"GBPUSD": {"events": [event()]}, "EURUSD": {"events": [event()]}},
        {"GBPUSD": {"coverage_state": "FULL", "role_allowed": "PRIMARY", "visibility_quality": 1.0}}
    )
    result = detector.detect_coalition(["GBPUSD", "EURUSD"])
    assert result["data_visibility"]["GBPUSD"]["role_allowed"] == "PRIMARY"


def test_usdjpy_thin_context_only_handling():
    detector = make_detector(
        {
            "GBPUSD": {"events": [event()]},
            "USDJPY": {"events": [event(battle=0.95, absorption=0.10)]},
        },
        {
            "GBPUSD": {"coverage_state": "FULL", "role_allowed": "PRIMARY", "visibility_quality": 1.0},
            "USDJPY": {
                "coverage_state": "THIN",
                "role_allowed": "CONTEXT_ONLY",
                "visibility_quality": 0.50,
                "technical_risks": ["USDJPY_THIN"],
            },
        },
    )
    result = detector.detect_coalition(["GBPUSD", "USDJPY"])
    assert result["data_visibility"]["USDJPY"]["coverage_state"] == "THIN"
    assert result["data_visibility"]["USDJPY"]["role_allowed"] == "CONTEXT_ONLY"
    assert result["confidence_factors"]["visibility_quality"] < 1.0


def test_leader_follower_identification():
    detector = make_detector({
        "GBPUSD": {"events": [event(battle=0.90, absorption=0.10)]},
        "GBPJPY": {"events": [event(battle=0.85, absorption=0.15)]},
        "EURUSD": {"events": [event(battle=0.30, absorption=0.70)]},
    })
    result = detector.detect_coalition(["GBPUSD", "GBPJPY", "EURUSD"])
    assert result["leader"] in {"GBP", "USD", "EUR", "JPY", "MIXED"}
    assert "leadership" in result
    assert isinstance(result["follower"], list)


def test_convergence_zones_same_event_type():
    detector = make_detector({
        "GBPUSD": {"events": [event("T009_BATTLE_LEVEL_BORN")]},
        "EURUSD": {"events": [event("T009_BATTLE_LEVEL_BORN")]},
        "USDJPY": {"events": [event("T009_ABSORPTION_CLUSTER")]},
    })
    result = detector.detect_coalition(["GBPUSD", "EURUSD", "USDJPY"])
    conv = result["convergence_zones"]
    assert any(c["event_type"] == "T009_BATTLE_LEVEL_BORN" for c in conv)


def test_divergence_zones_different_event_types():
    detector = make_detector({
        "GBPUSD": {"events": [event("T009_BATTLE_LEVEL_BORN")]},
        "EURUSD": {"events": [event("T009_ABSORPTION_CLUSTER")]},
    })
    result = detector.detect_coalition(["GBPUSD", "EURUSD"])
    assert len(result["divergence_zones"]) == 1
    assert len(result["divergence_zones"][0]["event_types"]) == 2


def test_score_confidence_factors_present():
    detector = make_detector({
        "GBPUSD": {"events": [event()]},
        "EURUSD": {"events": [event()]},
    })
    result = detector.detect_coalition(["GBPUSD", "EURUSD"])
    factors = result["confidence_factors"]
    assert "base_coalition_strength" in factors
    assert "visibility_quality" in factors
    assert "event_alignment" in factors
    assert "driver_clarity" in factors


def test_no_events_safe():
    detector = make_detector({
        "GBPUSD": {"events": []},
        "EURUSD": {"events": []},
    })
    result = detector.detect_coalition(["GBPUSD", "EURUSD"])
    assert result["coalition_detected"] is False
    assert result["pair_drivers"]["GBPUSD"]["pair_pressure"] == 0.0


def test_duplicate_symbols_normalized():
    detector = make_detector({
        "GBPUSD": {"events": [event()]},
        "EURUSD": {"events": [event()]},
    })
    result = detector.detect_coalition(["gbpusd", "GBPUSD", "eurusd"])
    assert result["symbols_analyzed"] == ["GBPUSD", "EURUSD"]


def test_split_symbol_helper():
    detector = CrossSymbolCoalitionDetector()
    assert detector._split_symbol("GBPUSD") == ("GBP", "USD")
    assert detector._split_symbol("XAU") == ("XAU", "USD")


def test_empty_visibility_fallback_safe():
    detector = make_detector({
        "GBPUSD": {"events": [event()]},
        "EURUSD": {"events": [event()]},
    }, {})
    result = detector.detect_coalition(["GBPUSD", "EURUSD"])
    assert result["data_visibility"]["GBPUSD"]["role_allowed"] in {"PRIMARY", "CONTEXT_ONLY", "UNKNOWN"}


def test_cli_requires_two_symbols():
    script = Path(__file__).resolve().parent.parent / "run_battlefield_cross_symbol_once.py"
    result = subprocess.run(
        [sys.executable, str(script), "--symbols", "GBPUSD"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "need at least 2 symbols" in result.stdout


def test_cli_outputs_json(tmp_path):
    script = Path(__file__).resolve().parent.parent / "run_battlefield_cross_symbol_once.py"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--symbols",
            "GBPUSD,EURUSD,USDJPY",
            "--lookback-min",
            "5",
            "--output",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    out = tmp_path / "battlefield_cross_symbol_coalition.json"
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["symbols_analyzed"] == ["GBPUSD", "EURUSD", "USDJPY"]
