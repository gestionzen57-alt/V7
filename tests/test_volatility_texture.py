"""Unit tests for B7+ Volatility Texture Engine."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "Core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from pf_volatility_texture import (  # noqa: E402
    TEXTURE_MM_NOISE,
    TEXTURE_NEWS_SPIKE,
    TEXTURE_SESSION_FRICTION,
    TEXTURE_STRUCTURAL,
    VolatilityTextureEngine,
)


def test_structural_volatility() -> None:
    """GBP builds steadily. Agitation is coherent and directional."""
    engine = VolatilityTextureEngine(window_micro=5, window_macro=20)
    force = np.array([1.00, 1.05, 1.08, 1.12, 1.15, 1.18, 1.21, 1.24, 1.28, 1.31])
    texture = engine.analyze_texture(
        force,
        spread_series=np.array([1.2] * len(force)),
        session_context={"session": "LONDON", "phase": "MID_SESSION"},
    )
    assert texture["valid"] is True
    assert texture["volatility_texture"]["type"] == TEXTURE_STRUCTURAL
    assert texture["volatility_texture"]["confidence"] >= 0.80


def test_news_spike() -> None:
    """Normal force, shock spike, then partial normalization."""
    engine = VolatilityTextureEngine(window_micro=5, window_macro=20)
    force = np.array([1.00, 1.02, 1.01, 1.50, 1.48, 1.12, 1.14, 1.16, 1.17, 1.18])
    spread = np.array([1.2, 1.2, 1.2, 5.5, 4.8, 2.0, 1.6, 1.4, 1.3, 1.2])
    texture = engine.analyze_texture(
        force,
        spread_series=spread,
        session_context={"session": "NY", "phase": "MID_SESSION"},
    )
    assert texture["valid"] is True
    assert texture["volatility_texture"]["type"] == TEXTURE_NEWS_SPIKE
    assert texture["spread_context"]["spike_detected"] is True


def test_session_friction() -> None:
    """Asian quiet state transitions into London ignition expansion."""
    engine = VolatilityTextureEngine(window_micro=5, window_macro=20)
    force_asian = np.array([1.0] * 20)
    force_london = np.array([1.00, 1.02, 1.05, 1.08, 1.12, 1.16, 1.20, 1.24])
    force = np.concatenate([force_asian, force_london])
    texture = engine.analyze_texture(
        force,
        spread_series=np.array([1.1] * len(force)),
        session_context={"session": "LONDON", "phase": "IGNITION"},
    )
    assert texture["valid"] is True
    assert texture["volatility_texture"]["type"] == TEXTURE_SESSION_FRICTION
    assert texture["session_context"]["alignment"] is True


def test_mm_noise() -> None:
    """Tight range-bound micro-agitation with no net movement."""
    engine = VolatilityTextureEngine(window_micro=5, window_macro=20)
    force = np.array([1.000, 1.003, 0.999, 1.002, 0.998, 1.001, 0.999, 1.002, 1.000, 1.001])
    spread = np.array([0.6] * len(force))
    texture = engine.analyze_texture(
        force,
        spread_series=spread,
        session_context={"session": "ASIAN", "phase": "MID_SESSION"},
    )
    assert texture["valid"] is True
    assert texture["volatility_texture"]["type"] == TEXTURE_MM_NOISE
    assert texture["spread_context"]["behavior"] in {"TIGHT", "STABLE"}


def test_insufficient_force_bars() -> None:
    engine = VolatilityTextureEngine(window_micro=5, window_macro=20)
    texture = engine.analyze_texture([1.0, 1.1, 1.2])
    assert texture["valid"] is False
    assert "INSUFFICIENT_FORCE_BARS" in texture["technical_risks"]
