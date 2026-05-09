"""
pf_regime_engine.py — PowerFlow V6
HTF Regime heuristic engine (no HMM — insufficient history).

3 regimes: COMPRESSION / TENDANCE / RANGE
Computed from:
  - rolling volatility (H4 equivalent)
  - median angle across recent bars (H1 equivalent)
  - extended z-score of force spread

Per-TF regime + htf_context_stack synthesis: W / D / H4 / H1
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

# ── TF mapping (minutes → regime label key) ──────────────────────────────

TF_LABEL: Dict[int, str] = {
    60:    "H1",
    240:   "H4",
    1440:  "D",
    10080: "W",
}

REGIME_COLOR: Dict[str, str] = {
    "COMPRESSION": "ORANGE",
    "TENDANCE":    "GREEN",
    "RANGE":       "BLUE",
    "TRANSITION":  "YELLOW",
    "UNKNOWN":     "GREY",
}

CURRENCIES = ["gbp", "usd", "eur", "jpy", "cad", "chf", "aud"]

# ── Thresholds (tunable on powerflow.db) ─────────────────────────────────

# Volatility (std of force spread over rolling window)
VOL_COMPRESSION_MAX = 0.8    # below = compressed
VOL_RANGE_MAX       = 2.5    # between = range
# above VOL_RANGE_MAX = potential tendency

# Median angle of top currency (absolute)
ANGLE_FLAT_MAX       = 0.08   # below = flat
ANGLE_TENDENCY_MIN   = 0.20   # above = directional

# Z-score spread (max-min normalised force at each bar)
ZSCORE_COMPRESSION_MAX = 0.6
ZSCORE_TENDENCY_MIN    = 1.2


# ── Data structures ───────────────────────────────────────────────────────

@dataclass
class RegimeResult:
    timeframe: int
    tf_label: str
    regime: str              # COMPRESSION | TENDANCE | RANGE | TRANSITION | UNKNOWN
    confidence: float        # 0.0 – 1.0
    regime_color: str
    vol_rolling: float
    median_angle: float
    zscore_spread: float
    n_bars: int


@dataclass
class HTFContextStack:
    W:  str = "UNKNOWN"
    D:  str = "UNKNOWN"
    H4: str = "UNKNOWN"
    H1: str = "UNKNOWN"


@dataclass
class RegimeEngineOutput:
    dominant_regime: str
    confidence: float
    regime_color: str
    htf_context_stack: Dict[str, str]
    per_tf: Dict[int, RegimeResult] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)


# ── DB fetch ──────────────────────────────────────────────────────────────

def _fetch_force_matrix(db_path: str,
                        symbol: str,
                        timeframe: int,
                        bars: int) -> np.ndarray:
    """
    Returns (bars, n_currencies) ndarray of force values, chronological.
    Returns empty array if no data.
    """
    uri = f"file:{db_path}?mode=ro"
    cols = ", ".join(f"force_{c}" for c in CURRENCIES)
    with sqlite3.connect(uri, uri=True) as conn:
        rows = conn.execute(
            f"""
            SELECT {cols}
            FROM force_snapshots
            WHERE symbol = ? AND timeframe = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (symbol, timeframe, bars),
        ).fetchall()

    if not rows:
        return np.empty((0, len(CURRENCIES)))

    arr = np.array([[float(v) if v is not None else np.nan
                     for v in row]
                    for row in reversed(rows)], dtype=float)
    return arr


# ── Heuristic metrics ─────────────────────────────────────────────────────

def _rolling_volatility(matrix: np.ndarray, window: int = 10) -> float:
    """
    Volatility = std of cross-currency spread (max-min) per bar, rolling.
    Measures how dispersed the force field is moment-to-moment.
    """
    if matrix.shape[0] < window:
        spreads = np.nanmax(matrix, axis=1) - np.nanmin(matrix, axis=1)
    else:
        tail = matrix[-window:]
        spreads = np.nanmax(tail, axis=1) - np.nanmin(tail, axis=1)

    if len(spreads) == 0:
        return 0.0
    return float(np.nanstd(spreads))


def _median_angle(matrix: np.ndarray) -> float:
    """
    Median angular change of the dominant (highest-range) currency over last 3 bars.
    Positive = UP, negative = DOWN.
    """
    if matrix.shape[0] < 2:
        return 0.0

    tail = matrix[-3:] if matrix.shape[0] >= 3 else matrix
    # Per-currency range to find dominant
    ranges = np.nanmax(tail, axis=0) - np.nanmin(tail, axis=0)
    dom_idx = int(np.nanargmax(ranges))

    dom_series = tail[:, dom_idx]
    angles = np.diff(dom_series)
    if len(angles) == 0:
        return 0.0
    return float(np.nanmedian(angles))


def _zscore_spread(matrix: np.ndarray, window: int = 20) -> float:
    """
    Z-score of latest cross-currency spread vs rolling std.
    High z-score = currencies diverged (tendency).
    Low z-score = currencies compressed.
    """
    if matrix.shape[0] < 3:
        return 0.0

    tail = matrix[-window:] if matrix.shape[0] >= window else matrix

    # Spread per bar
    spreads = np.nanmax(tail, axis=1) - np.nanmin(tail, axis=1)
    if len(spreads) < 2:
        return 0.0

    mu = float(np.nanmean(spreads[:-1]))
    sigma = float(np.nanstd(spreads[:-1]))
    if sigma < 1e-8:
        return 0.0

    latest = spreads[-1]
    return float((latest - mu) / sigma)


# ── Regime classifier ─────────────────────────────────────────────────────

def _classify_regime(vol: float, angle: float, zscore: float) -> tuple[str, float]:
    """
    Returns (regime, confidence) from the three heuristic metrics.
    Confidence reflects how many metrics agree.
    """
    angle_abs = abs(angle)

    votes: Dict[str, float] = {"COMPRESSION": 0.0, "TENDANCE": 0.0, "RANGE": 0.0}

    # Volatility vote
    if vol < VOL_COMPRESSION_MAX:
        votes["COMPRESSION"] += 1.0
    elif vol > VOL_RANGE_MAX:
        votes["TENDANCE"] += 0.7
        votes["RANGE"] += 0.3
    else:
        votes["RANGE"] += 1.0

    # Angle vote
    if angle_abs < ANGLE_FLAT_MAX:
        votes["COMPRESSION"] += 0.8
        votes["RANGE"] += 0.2
    elif angle_abs > ANGLE_TENDENCY_MIN:
        votes["TENDANCE"] += 1.0
    else:
        votes["RANGE"] += 0.8

    # Z-score vote
    if zscore < ZSCORE_COMPRESSION_MAX:
        votes["COMPRESSION"] += 0.9
    elif zscore > ZSCORE_TENDENCY_MIN:
        votes["TENDANCE"] += 0.9
    else:
        votes["RANGE"] += 0.7

    total = sum(votes.values())
    if total < 1e-8:
        return "UNKNOWN", 0.0

    winner = max(votes, key=lambda k: votes[k])
    confidence = round(votes[winner] / total, 3)

    # Transition: winner not dominant enough
    if confidence < 0.40:
        return "TRANSITION", confidence

    return winner, confidence


# ── Per-TF compute ────────────────────────────────────────────────────────

def compute_tf_regime(db_path: str,
                      symbol: str,
                      timeframe: int,
                      bars: int = 60) -> Optional[RegimeResult]:
    """Compute regime for a single TF. Returns None on insufficient data."""
    matrix = _fetch_force_matrix(db_path, symbol, timeframe, bars)

    if matrix.shape[0] < 3:
        return None

    vol    = _rolling_volatility(matrix)
    angle  = _median_angle(matrix)
    zscore = _zscore_spread(matrix)

    regime, confidence = _classify_regime(vol, angle, zscore)
    label = TF_LABEL.get(timeframe, f"TF{timeframe}")

    return RegimeResult(
        timeframe=timeframe,
        tf_label=label,
        regime=regime,
        confidence=confidence,
        regime_color=REGIME_COLOR.get(regime, "GREY"),
        vol_rolling=round(vol, 4),
        median_angle=round(angle, 6),
        zscore_spread=round(zscore, 4),
        n_bars=matrix.shape[0],
    )


# ── HTF Context Stack synthesis ───────────────────────────────────────────

def _build_htf_stack(per_tf: Dict[int, RegimeResult]) -> Dict[str, str]:
    """Map per-TF results into W/D/H4/H1 stack."""
    stack = {"W": "UNKNOWN", "D": "UNKNOWN", "H4": "UNKNOWN", "H1": "UNKNOWN"}
    for tf, result in per_tf.items():
        label = TF_LABEL.get(tf)
        if label and label in stack:
            stack[label] = result.regime
    return stack


def _dominant_regime(per_tf: Dict[int, RegimeResult]) -> tuple[str, float]:
    """
    Weighted dominant regime: longer TFs have stronger weight (HTF gravity doctrine).
    W=4, D=3, H4=2, H1=1
    """
    tf_weights = {10080: 4, 1440: 3, 240: 2, 60: 1}
    votes: Dict[str, float] = {}

    for tf, res in per_tf.items():
        w = tf_weights.get(tf, 1)
        r = res.regime
        votes[r] = votes.get(r, 0.0) + w * res.confidence

    if not votes:
        return "UNKNOWN", 0.0

    total = sum(votes.values())
    winner = max(votes, key=lambda k: votes[k])
    confidence = round(votes[winner] / total, 3) if total > 0 else 0.0
    return winner, confidence


# ── Main entry point ──────────────────────────────────────────────────────

def compute_regime(db_path: str,
                   symbol: str,
                   timeframes: Optional[List[int]] = None,
                   bars: int = 60) -> RegimeEngineOutput:
    """
    Compute HTF regime across multiple timeframes.

    Args:
        db_path:    path to powerflow.db
        symbol:     e.g. "GBPUSD"
        timeframes: list of TF minutes, default [60, 240, 1440, 10080]
        bars:       lookback bars per TF

    Returns:
        RegimeEngineOutput with dominant regime + htf_context_stack
    """
    if timeframes is None:
        timeframes = [60, 240, 1440, 10080]

    per_tf: Dict[int, RegimeResult] = {}
    notes: List[str] = []

    for tf in timeframes:
        try:
            result = compute_tf_regime(db_path, symbol, tf, bars)
            if result is None:
                notes.append(f"TF{tf}: insufficient data")
            else:
                per_tf[tf] = result
        except Exception as e:
            notes.append(f"TF{tf}: error — {e}")

    if not per_tf:
        return RegimeEngineOutput(
            dominant_regime="UNKNOWN",
            confidence=0.0,
            regime_color="GREY",
            htf_context_stack={"W": "UNKNOWN", "D": "UNKNOWN",
                               "H4": "UNKNOWN", "H1": "UNKNOWN"},
            per_tf={},
            notes=notes or ["No valid timeframe data"],
        )

    dominant, confidence = _dominant_regime(per_tf)
    htf_stack = _build_htf_stack(per_tf)

    return RegimeEngineOutput(
        dominant_regime=dominant,
        confidence=confidence,
        regime_color=REGIME_COLOR.get(dominant, "GREY"),
        htf_context_stack=htf_stack,
        per_tf=per_tf,
        notes=notes,
    )


# ── Serialiser ────────────────────────────────────────────────────────────

def regime_output_to_dict(out: RegimeEngineOutput) -> dict:
    return {
        "regime": out.dominant_regime,
        "confidence": out.confidence,
        "regime_color": out.regime_color,
        "htf_context_stack": out.htf_context_stack,
        "per_tf": {
            tf: {
                "tf_label":      r.tf_label,
                "regime":        r.regime,
                "confidence":    r.confidence,
                "regime_color":  r.regime_color,
                "vol_rolling":   r.vol_rolling,
                "median_angle":  r.median_angle,
                "zscore_spread": r.zscore_spread,
                "n_bars":        r.n_bars,
            }
            for tf, r in out.per_tf.items()
        },
        "notes": out.notes,
    }
