"""
PowerFlow V6 - pf_tension_signature.py
Version: V0.1.2
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

# ==========================================================================
# CONSTANTS
# ==========================================================================

EPSILON: float = 1e-9
ELASTIC_THRESHOLD: float = 2.5
DIRECTIONAL_THRESHOLD: float = 0.35
DEAD_ABS_THRESHOLD: float = 1.00
MIN_BARS: int = 6
MAX_SCORE: float = 50.0

# ==========================================================================
# OUTPUT
# ==========================================================================

@dataclass(frozen=True)
class TensionSignature:
    score: float
    label: str
    micro_var: float
    macro_var: float
    n_bars: int
    note: str

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "label": self.label,
            "micro_var": self.micro_var,
            "macro_var": self.macro_var,
            "n_bars": self.n_bars,
            "note": self.note,
        }

# ==========================================================================
# HELPERS
# ==========================================================================

def _clean(series: Sequence[Optional[float]]) -> List[float]:
    out: List[float] = []
    for v in series:
        if v is None:
            continue
        try:
            out.append(float(v))
        except (TypeError, ValueError):
            continue
    return out


def _variance(values: List[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    return sum((v - mean) ** 2 for v in values) / (n - 1)


def _micro_variance(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    deltas = [values[i] - values[i - 1] for i in range(1, len(values))]
    return _variance(deltas)


def _macro_variance(values: List[float], window: int) -> float:
    if len(values) < window:
        return _variance(values)
    sub_means: List[float] = []
    step = max(1, window // 2)
    i = 0
    while i + window <= len(values):
        chunk = values[i : i + window]
        sub_means.append(sum(chunk) / len(chunk))
        i += step
    if len(sub_means) < 2:
        return _variance(values)
    return _variance(sub_means)

# ==========================================================================
# PUBLIC API
# ==========================================================================

def compute_tension_signature(
    series: Sequence[Optional[float]],
    window: int = 5,
    elastic_threshold: float = ELASTIC_THRESHOLD,
    directional_threshold: float = DIRECTIONAL_THRESHOLD,
    dead_abs_threshold: float = DEAD_ABS_THRESHOLD,
) -> TensionSignature:
    values = _clean(series)
    n = len(values)

    if n < MIN_BARS:
        return TensionSignature(
            score=0.0,
            label="INSUFFICIENT_DATA",
            micro_var=0.0,
            macro_var=0.0,
            n_bars=n,
            note=f"Moins de {MIN_BARS} barres valides ({n} disponibles).",
        )

    micro = _micro_variance(values)
    macro = _macro_variance(values, window)

    if micro < dead_abs_threshold and macro < dead_abs_threshold:
        return TensionSignature(
            score=0.0,
            label="DEAD_CURRENCY",
            micro_var=round(micro, 6),
            macro_var=round(macro, 6),
            n_bars=n,
            note=(
                f"Amplitude absolue negligeable — micro ({micro:.6f}), macro ({macro:.6f}). "
                f"Devise inactive, bruit blanc."
            ),
        )

    # ← ICI le cap MAX_SCORE
    score = min(round(micro / (macro + EPSILON), 4), MAX_SCORE)

    if score > elastic_threshold:
        label = "ELASTIC_LOADED"
        note = (
            f"Micro-agitation elevee ({micro:.4f}) sur fond macro plat ({macro:.4f}). "
            f"Devise comprimee, elastique en charge."
        )
    elif score < directional_threshold:
        label = "DIRECTIONAL_MOVE"
        note = (
            f"Macro-variance dominante ({macro:.4f}) sur micro faible ({micro:.4f}). "
            f"Devise en mouvement directionnel lent."
        )
    else:
        label = "DEAD_CURRENCY"
        note = (
            f"Micro ({micro:.4f}) et macro ({macro:.4f}) equilibres, amplitude presente. "
            f"Devise inactive ou en pause."
        )

    return TensionSignature(
        score=score,
        label=label,
        micro_var=round(micro, 6),
        macro_var=round(macro, 6),
        n_bars=n,
        note=note,
    )