# -*- coding: utf-8 -*-
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from pf_pair_driver_context import PairDriverAnalyzer, PairDriverResult


def test_analyzer_init():
    analyzer = PairDriverAnalyzer()
    assert analyzer is not None


def test_result_dataclass_available():
    result = PairDriverResult(
        pair_pressure=0.0,
        pair_momentum=0.0,
        driver_type="MIXED_DRIVER",
        driver_label_fr="Driver mixte ou peu clair",
        base_contribution=0.0,
        quote_contribution=0.0,
        confidence=0.0,
    )
    assert result.driver_type == "MIXED_DRIVER"


def test_base_outruns_quote():
    """GBP 0.80 / USD 0.30 -> BASE_OUTRUNS_QUOTE"""
    analyzer = PairDriverAnalyzer()
    result = analyzer.analyze_pair_driver(
        base_force=0.80,
        quote_force=0.30,
        base_delta=0.05,
        quote_delta=0.01,
    )
    assert result["driver_type"] == "BASE_OUTRUNS_QUOTE"
    assert result["pair_pressure"] == pytest.approx(0.50)
    assert "surperforme cotation" in result["driver_label_fr"]


def test_quote_outruns_base():
    """GBP 0.30 / USD 0.80 -> QUOTE_OUTRUNS_BASE"""
    analyzer = PairDriverAnalyzer()
    result = analyzer.analyze_pair_driver(
        base_force=0.30,
        quote_force=0.80,
        base_delta=0.01,
        quote_delta=0.05,
    )
    assert result["driver_type"] == "QUOTE_OUTRUNS_BASE"
    assert result["pair_pressure"] == pytest.approx(-0.50)
    assert "Cotation surperforme" in result["driver_label_fr"]


def test_both_up_base_stronger():
    """Both up, base leads -> BOTH_UP_BASE_STRONGER"""
    analyzer = PairDriverAnalyzer()
    result = analyzer.analyze_pair_driver(
        base_force=0.75,
        quote_force=0.65,
        base_delta=0.02,
        quote_delta=0.01,
    )
    assert result["driver_type"] == "BOTH_UP_BASE_STRONGER"
    assert "Les deux montent" in result["driver_label_fr"]


def test_both_up_quote_stronger():
    analyzer = PairDriverAnalyzer()
    result = analyzer.analyze_pair_driver(
        base_force=0.66,
        quote_force=0.76,
        base_delta=0.01,
        quote_delta=0.02,
    )
    assert result["driver_type"] == "BOTH_UP_QUOTE_STRONGER"


def test_both_down_quote_weaker():
    """Both down, quote weaker -> BOTH_DOWN_QUOTE_WEAKER"""
    analyzer = PairDriverAnalyzer()
    result = analyzer.analyze_pair_driver(
        base_force=0.35,
        quote_force=0.25,
        base_delta=-0.02,
        quote_delta=-0.04,
    )
    assert result["driver_type"] == "BOTH_DOWN_QUOTE_WEAKER"
    assert "cotation plus faible" in result["driver_label_fr"]


def test_both_down_base_weaker():
    analyzer = PairDriverAnalyzer()
    result = analyzer.analyze_pair_driver(
        base_force=0.22,
        quote_force=0.34,
        base_delta=-0.04,
        quote_delta=-0.02,
    )
    assert result["driver_type"] == "BOTH_DOWN_BASE_WEAKER"


def test_quote_weakness_dominant():
    """Quote very weak -> QUOTE_WEAKNESS_DOMINANT"""
    analyzer = PairDriverAnalyzer()
    result = analyzer.analyze_pair_driver(
        base_force=0.70,
        quote_force=0.10,
        base_delta=0.02,
        quote_delta=-0.03,
    )
    assert result["driver_type"] == "QUOTE_WEAKNESS_DOMINANT"
    assert "faible" in result["driver_label_fr"].lower()


def test_pair_pressure_calculation():
    analyzer = PairDriverAnalyzer()
    result = analyzer.analyze_pair_driver(0.60, 0.40, 0.05, 0.02)
    assert result["pair_pressure"] == pytest.approx(0.20)


def test_pair_momentum_calculation():
    analyzer = PairDriverAnalyzer()
    result = analyzer.analyze_pair_driver(0.50, 0.50, 0.08, 0.03)
    assert result["pair_momentum"] == pytest.approx(0.05)


def test_base_momentum_dominant():
    analyzer = PairDriverAnalyzer()
    result = analyzer.analyze_pair_driver(0.50, 0.48, 0.20, 0.02)
    assert result["driver_type"] == "BASE_MOMENTUM_DOMINANT"


def test_quote_momentum_dominant():
    analyzer = PairDriverAnalyzer()
    result = analyzer.analyze_pair_driver(0.50, 0.48, 0.02, 0.20)
    assert result["driver_type"] == "QUOTE_MOMENTUM_DOMINANT"


def test_driver_label_fr_correct():
    analyzer = PairDriverAnalyzer()
    result = analyzer.analyze_pair_driver(0.85, 0.25, 0.04, 0.01)
    assert isinstance(result["driver_label_fr"], str)
    assert len(result["driver_label_fr"]) > 0
    assert "français" not in result["driver_label_fr"]


def test_handles_zero_forces():
    """Handles 0.0 forces safely"""
    analyzer = PairDriverAnalyzer()
    result = analyzer.analyze_pair_driver(0.0, 0.0, 0.0, 0.0)
    assert result["pair_pressure"] == 0.0
    assert result["pair_momentum"] == 0.0
    assert result["driver_type"] != ""
    assert result["base_contribution"] == 0.0
    assert result["quote_contribution"] == 0.0


def test_confidence_score():
    """Higher pressure = higher confidence"""
    analyzer = PairDriverAnalyzer()

    r1 = analyzer.analyze_pair_driver(0.90, 0.20, 0.05, 0.01)
    r2 = analyzer.analyze_pair_driver(0.55, 0.50, 0.01, 0.01)

    assert r1["confidence"] >= r2["confidence"]


def test_clamps_contributions_but_preserves_pressure():
    analyzer = PairDriverAnalyzer()
    result = analyzer.analyze_pair_driver(1.20, -0.10, 0.0, 0.0)
    assert result["pair_pressure"] == pytest.approx(1.30)
    assert result["base_contribution"] == 1.0
    assert result["quote_contribution"] == 0.0
