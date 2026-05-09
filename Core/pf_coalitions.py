#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V6 - pf_coalitions.py
Version: V0.1

Mission:
    Detect currency coalitions from already-computed behavioral profiles.

Doctrine:
    - pf_personalities.py measures individual currency identity.
    - pf_zone_dynamics.py reads zone respiration.
    - pf_zone_context_logger.py stores zone diagnostics.
    - pf_coalitions.py groups currencies that breathe together.

This module does not:
    - compute z_basket from raw force_snapshots
    - decide temporal nodes
    - write to DB
    - alert Telegram
    - depend on Cockpit
"""

from __future__ import annotations

import itertools
import json
import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from pf_personalities import get_devise_profile


DEFAULT_MIN_MEMBERS = 2
DEFAULT_MAX_Z_GAP = 0.55
DEFAULT_MAX_SLOPE_GAP = 0.18
DEFAULT_MAX_CURVATURE_GAP = 0.14
DEFAULT_MIN_ABS_Z = 1.20
DEFAULT_MIN_COHESION = 0.62
EXTREME_Z = 2.0
CENTER_Z = 0.50


@dataclass(frozen=True)
class CurrencyVector:
    currency: str
    z_basket: float
    slope: float = 0.0
    curvature: float = 0.0
    phase: str = "UNKNOWN"
    quality: str = "UNKNOWN"
    zone_state: Optional[str] = None
    zone_level: Optional[str] = None
    context_score: float = 0.0
    context_tags: Tuple[str, ...] = ()

    @property
    def polarity(self) -> str:
        if self.z_basket >= CENTER_Z:
            return "HIGH"
        if self.z_basket <= -CENTER_Z:
            return "LOW"
        return "CENTER"

    @property
    def direction(self) -> str:
        if self.slope > 0.04:
            return "RISING"
        if self.slope < -0.04:
            return "FALLING"
        return "FLAT"

    @property
    def is_tense(self) -> bool:
        return abs(self.z_basket) >= DEFAULT_MIN_ABS_Z

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["context_tags"] = list(self.context_tags)
        data["polarity"] = self.polarity
        data["direction"] = self.direction
        return data


@dataclass(frozen=True)
class CurrencyCoalition:
    coalition_id: str
    members: Tuple[str, ...]
    polarity: str
    direction: str
    state: str
    phase: str
    z_mean: float
    z_dispersion: float
    slope_mean: float
    slope_dispersion: float
    curvature_mean: float
    context_score_mean: float
    cohesion: float
    leader: Optional[str]
    follower: Optional[str]
    antagonist_candidates: Tuple[str, ...]
    tags: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["members"] = list(self.members)
        data["antagonist_candidates"] = list(self.antagonist_candidates)
        data["tags"] = list(self.tags)
        return data



def get_profile_safe(currency: str):
    """Safe profile accessor: uppercase + None-tolerant."""
    if not currency:
        return None
    try:
        return get_devise_profile(str(currency).upper())
    except Exception:
        return None


def volatility_compatibility_score(a: str, b: str) -> float:
    pa = get_profile_safe(a)
    pb = get_profile_safe(b)

    if pa is None or pb is None:
        return 0.5
    if pa.volatility_class == pb.volatility_class:
        return 1.0

    pair = {pa.volatility_class, pb.volatility_class}
    if pair == {"MEDIUM", "HIGH"} or pair == {"MEDIUM", "LOW"}:
        return 0.75
    return 0.55


def role_compatibility_score(a: str, b: str) -> float:
    pa = get_profile_safe(a)
    pb = get_profile_safe(b)

    if pa is None or pb is None:
        return 0.5
    if pa.role == pb.role:
        return 1.0

    # RISK/PIVOT remains structurally closer than REFUGE/RISK in coalition flows.
    pair = {pa.role, pb.role}
    if pair == {"RISK", "PIVOT"}:
        return 0.8
    if pair == {"REFUGE", "PIVOT"}:
        return 0.7
    return 0.6


def tempo_compatibility_score(a: str, b: str) -> float:
    pa = get_profile_safe(a)
    pb = get_profile_safe(b)

    if pa is None or pb is None:
        return 0.5

    gap = abs(pa.tempo_tf - pb.tempo_tf)
    if gap == 0:
        return 1.0
    if gap <= 10:
        return 0.85
    if gap <= 20:
        return 0.7
    return 0.55


def personality_compatibility_score(a: str, b: str) -> float:
    """Light aggregate score [0..1] from personality compatibility."""
    v = volatility_compatibility_score(a, b)
    r = role_compatibility_score(a, b)
    t = tempo_compatibility_score(a, b)
    return round((0.35 * v) + (0.35 * r) + (0.30 * t), 4)

def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(out) or math.isinf(out):
        return default
    return out


def _mean(values: Sequence[float]) -> float:
    clean = [v for v in values if not math.isnan(v) and not math.isinf(v)]
    return sum(clean) / len(clean) if clean else 0.0


def _spread(values: Sequence[float]) -> float:
    clean = [v for v in values if not math.isnan(v) and not math.isinf(v)]
    if not clean:
        return 0.0
    return max(clean) - min(clean)


def _tuple_tags(value: Any) -> Tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    try:
        return tuple(str(x) for x in value)
    except TypeError:
        return (str(value),)


def vector_from_mapping(row: Mapping[str, Any]) -> CurrencyVector:
    """Build a CurrencyVector from personality and/or zone diagnostic mapping."""
    tags = row.get("context_tags", row.get("contextual_tags", ()))
    return CurrencyVector(
        currency=str(row.get("currency", "UNKNOWN")).upper(),
        z_basket=_safe_float(row.get("z_basket", row.get("z_current", 0.0))),
        slope=_safe_float(row.get("slope", 0.0)),
        curvature=_safe_float(row.get("curvature", row.get("depth_acceleration", 0.0))),
        phase=str(row.get("phase", "UNKNOWN")),
        quality=str(row.get("quality", "UNKNOWN")),
        zone_state=row.get("zone_state", row.get("state")),
        zone_level=row.get("zone_level"),
        context_score=_safe_float(row.get("context_score", 0.0)),
        context_tags=_tuple_tags(tags),
    )


def vectors_from_personality_result(
    personality_result: Mapping[str, Any],
    zone_diagnostics: Optional[Mapping[str, Mapping[str, Any]]] = None,
) -> List[CurrencyVector]:
    """Merge pf_personalities result with optional zone diagnostics by currency.

    Expected personality_result shape:
        {"currencies": {"USD": {...}, "GBP": {...}}}

    zone_diagnostics shape:
        {"USD": zone_diag_dict, "GBP": zone_diag_dict}
    """
    currencies = personality_result.get("currencies", {})
    zone_diagnostics = zone_diagnostics or {}

    vectors: List[CurrencyVector] = []
    for currency, pdata in currencies.items():
        merged: Dict[str, Any] = dict(pdata)
        zdata = zone_diagnostics.get(str(currency).upper(), {})
        if zdata:
            merged["zone_state"] = zdata.get("state")
            merged["zone_level"] = zdata.get("zone_level")
            merged["context_score"] = zdata.get("context_score", merged.get("context_score", 0.0))
            merged["context_tags"] = zdata.get("context_tags", zdata.get("contextual_tags", ()))
        merged["currency"] = str(currency).upper()
        vectors.append(vector_from_mapping(merged))
    return vectors


def are_compatible(
    a: CurrencyVector,
    b: CurrencyVector,
    *,
    max_z_gap: float = DEFAULT_MAX_Z_GAP,
    max_slope_gap: float = DEFAULT_MAX_SLOPE_GAP,
    max_curvature_gap: float = DEFAULT_MAX_CURVATURE_GAP,
    min_abs_z: float = DEFAULT_MIN_ABS_Z,
) -> bool:
    """Pair compatibility: same side, close tension, close timing."""
    if a.currency == b.currency:
        return False
    if a.polarity == "CENTER" or b.polarity == "CENTER":
        return False
    if a.polarity != b.polarity:
        return False
    if abs(a.z_basket) < min_abs_z or abs(b.z_basket) < min_abs_z:
        return False
    if abs(a.z_basket - b.z_basket) > max_z_gap:
        return False
    if a.direction != b.direction:
        return False
    if a.direction == "FLAT":
        return False
    if abs(a.slope - b.slope) > max_slope_gap:
        return False
    if abs(a.curvature - b.curvature) > max_curvature_gap:
        return False
    return True


def _connected_components(
    vectors: Sequence[CurrencyVector],
    edges: Sequence[Tuple[str, str]],
) -> List[List[CurrencyVector]]:
    by_currency = {v.currency: v for v in vectors}
    graph: Dict[str, set[str]] = {v.currency: set() for v in vectors}
    for a, b in edges:
        graph.setdefault(a, set()).add(b)
        graph.setdefault(b, set()).add(a)

    seen: set[str] = set()
    comps: List[List[CurrencyVector]] = []
    for cur in graph:
        if cur in seen:
            continue
        stack = [cur]
        seen.add(cur)
        comp: List[str] = []
        while stack:
            node = stack.pop()
            comp.append(node)
            for nxt in graph.get(node, set()):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        comp_vectors = [by_currency[c] for c in comp if c in by_currency]
        if comp_vectors:
            comps.append(comp_vectors)
    return comps


def _common_tags(vectors: Sequence[CurrencyVector]) -> Tuple[str, ...]:
    if not vectors:
        return ()
    sets = [set(v.context_tags) for v in vectors if v.context_tags]
    if not sets:
        return ()
    common = set.intersection(*sets) if sets else set()
    return tuple(sorted(common))


def _coalition_state(polarity: str, direction: str, z_mean: float, zone_states: Sequence[Optional[str]]) -> str:
    strong = abs(z_mean) >= EXTREME_Z
    zone_set = {str(s) for s in zone_states if s}

    if polarity == "LOW" and direction == "RISING":
        return "LOW_ELASTIC_COALITION_RESPRING" if strong else "LOW_COALITION_RISING"
    if polarity == "LOW" and direction == "FALLING":
        return "LOW_PRESSURE_COALITION_EXPANDING"
    if polarity == "HIGH" and direction == "FALLING":
        return "HIGH_PRESSURE_COALITION_FOLDING" if strong else "HIGH_COALITION_FALLING"
    if polarity == "HIGH" and direction == "RISING":
        return "HIGH_PRESSURE_COALITION_EXPANDING"

    if "ACCUMULATING" in zone_set:
        return f"{polarity}_ACCUMULATING_COALITION"
    return f"{polarity}_COALITION"


def _coalition_phase(state: str, common_tags: Sequence[str]) -> str:
    tags = set(common_tags)
    if "M1_SPECIAL_MICROFILM" in tags:
        return "MICROFILM_SYNCHRONIZED_FIELD"
    if "M5_M15_INTERMEDIATE_FIELD" in tags:
        return "INTERMEDIATE_SYNCHRONIZED_FIELD"
    if "SCENARIO_ZONE_WORK" in tags or "H1_SCENARIO_CURVE" in tags:
        return "SCENARIO_SYNCHRONIZED_FIELD"
    if "RESPRING" in state:
        return "SYNCHRONIZED_RESPRING"
    if "FOLDING" in state:
        return "SYNCHRONIZED_FOLDING"
    return "SYNCHRONIZED_FIELD"


def _leader_follower(vectors: Sequence[CurrencyVector]) -> Tuple[Optional[str], Optional[str]]:
    if not vectors:
        return None, None
    ranked = sorted(vectors, key=lambda v: abs(v.slope), reverse=True)
    leader = ranked[0].currency
    follower = ranked[-1].currency if len(ranked) > 1 else None
    return leader, follower


def _cohesion_score(
    z_dispersion: float,
    slope_dispersion: float,
    curvature_dispersion: float,
    common_tag_count: int,
    members: Sequence[str],
) -> float:
    z_part = max(0.0, 1.0 - z_dispersion / max(DEFAULT_MAX_Z_GAP, 1e-9))
    slope_part = max(0.0, 1.0 - slope_dispersion / max(DEFAULT_MAX_SLOPE_GAP, 1e-9))
    curv_part = max(0.0, 1.0 - curvature_dispersion / max(DEFAULT_MAX_CURVATURE_GAP, 1e-9))
    tag_bonus = min(0.12, common_tag_count * 0.03)

    personality_parts: List[float] = []
    for a, b in itertools.combinations(members, 2):
        personality_parts.append(personality_compatibility_score(a, b))
    personality_mean = _mean(personality_parts) if personality_parts else 0.5

    base = (0.45 * z_part + 0.35 * slope_part + 0.20 * curv_part) + tag_bonus

    # Light calibration only: personality acts as +/- 8% adjustment around neutral 0.5.
    calibrated = base + ((personality_mean - 0.5) * 0.16)

    return round(min(1.0, max(0.0, calibrated)), 4)


def _find_antagonists(coalition: Sequence[CurrencyVector], all_vectors: Sequence[CurrencyVector]) -> Tuple[str, ...]:
    if not coalition:
        return ()
    coalition_curs = {v.currency for v in coalition}
    polarity = coalition[0].polarity
    slope_mean = _mean([v.slope for v in coalition])
    antagonists: List[str] = []
    for v in all_vectors:
        if v.currency in coalition_curs:
            continue
        if v.polarity == "CENTER" or v.polarity == polarity:
            continue
        # Antagonist either moves opposite, or folds/rebounds toward the coalition field.
        opposite_slope = slope_mean * v.slope < 0
        toward_center = (v.z_basket > 0 and v.slope < 0) or (v.z_basket < 0 and v.slope > 0)
        if opposite_slope or toward_center:
            antagonists.append(v.currency)
    return tuple(antagonists)


def build_coalition(
    vectors: Sequence[CurrencyVector],
    all_vectors: Sequence[CurrencyVector],
) -> Optional[CurrencyCoalition]:
    if len(vectors) < DEFAULT_MIN_MEMBERS:
        return None

    polarity = vectors[0].polarity
    directions = [v.direction for v in vectors]
    direction = max(set(directions), key=directions.count)

    z_values = [v.z_basket for v in vectors]
    slope_values = [v.slope for v in vectors]
    curvature_values = [v.curvature for v in vectors]
    z_mean = _mean(z_values)
    z_disp = _spread(z_values)
    slope_mean = _mean(slope_values)
    slope_disp = _spread(slope_values)
    curvature_mean = _mean(curvature_values)
    curvature_disp = _spread(curvature_values)
    tags = _common_tags(vectors)

    cohesion = _cohesion_score(
        z_disp,
        slope_disp,
        curvature_disp,
        len(tags),
        [v.currency for v in vectors],
    )
    if cohesion < DEFAULT_MIN_COHESION:
        return None

    members = tuple(sorted(v.currency for v in vectors))
    state = _coalition_state(polarity, direction, z_mean, [v.zone_state for v in vectors])
    phase = _coalition_phase(state, tags)
    leader, follower = _leader_follower(vectors)
    antagonists = _find_antagonists(vectors, all_vectors)

    return CurrencyCoalition(
        coalition_id=f"{'_'.join(members)}_{state}",
        members=members,
        polarity=polarity,
        direction=direction,
        state=state,
        phase=phase,
        z_mean=round(z_mean, 4),
        z_dispersion=round(z_disp, 4),
        slope_mean=round(slope_mean, 4),
        slope_dispersion=round(slope_disp, 4),
        curvature_mean=round(curvature_mean, 4),
        context_score_mean=round(_mean([v.context_score for v in vectors]), 4),
        cohesion=cohesion,
        leader=leader,
        follower=follower,
        antagonist_candidates=antagonists,
        tags=tags,
    )


def detect_currency_coalitions(
    vectors: Sequence[CurrencyVector | Mapping[str, Any]],
    *,
    min_members: int = DEFAULT_MIN_MEMBERS,
    max_z_gap: float = DEFAULT_MAX_Z_GAP,
    max_slope_gap: float = DEFAULT_MAX_SLOPE_GAP,
    max_curvature_gap: float = DEFAULT_MAX_CURVATURE_GAP,
    min_abs_z: float = DEFAULT_MIN_ABS_Z,
) -> List[CurrencyCoalition]:
    """Detect synchronized currency coalitions.

    Input can be CurrencyVector objects or dictionaries from Personality/ZoneDynamics.
    """
    normalized: List[CurrencyVector] = [
        v if isinstance(v, CurrencyVector) else vector_from_mapping(v)
        for v in vectors
    ]

    normalized = [v for v in normalized if v.currency != "UNKNOWN"]

    edges: List[Tuple[str, str]] = []
    for a, b in itertools.combinations(normalized, 2):
        if are_compatible(
            a,
            b,
            max_z_gap=max_z_gap,
            max_slope_gap=max_slope_gap,
            max_curvature_gap=max_curvature_gap,
            min_abs_z=min_abs_z,
        ):
            edges.append((a.currency, b.currency))

    components = _connected_components(normalized, edges)

    out: List[CurrencyCoalition] = []
    for comp in components:
        if len(comp) < min_members:
            continue
        coalition = build_coalition(comp, normalized)
        if coalition is not None:
            out.append(coalition)

    out.sort(key=lambda c: (c.cohesion, abs(c.z_mean), c.context_score_mean), reverse=True)
    return out


def coalitions_to_dict(coalitions: Sequence[CurrencyCoalition]) -> List[Dict[str, Any]]:
    return [c.to_dict() for c in coalitions]


def summarize_coalitions(coalitions: Sequence[CurrencyCoalition]) -> str:
    if not coalitions:
        return "No active currency coalition."
    lines: List[str] = []
    for c in coalitions:
        members = "+".join(c.members)
        ant = "+".join(c.antagonist_candidates) if c.antagonist_candidates else "-"
        lines.append(
            f"{members}: {c.state} | phase={c.phase} | cohesion={c.cohesion:.2f} | "
            f"z={c.z_mean:+.2f} | slope={c.slope_mean:+.2f} | leader={c.leader} | antagonist={ant}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    demo_vectors = [
        {"currency": "GBP", "z_basket": -2.24, "slope": 0.14, "curvature": 0.04, "phase": "EARLY_RESPRING", "context_tags": ["M1_SPECIAL_MICROFILM", "LOCAL_ZONE_WORK"]},
        {"currency": "EUR", "z_basket": -2.06, "slope": 0.11, "curvature": 0.03, "phase": "EARLY_RESPRING", "context_tags": ["M1_SPECIAL_MICROFILM", "LOCAL_ZONE_WORK"]},
        {"currency": "USD", "z_basket": 2.45, "slope": -0.18, "curvature": -0.06, "phase": "FOLDING_FROM_HIGH", "context_tags": ["M1_SPECIAL_MICROFILM", "LOCAL_ZONE_WORK"]},
        {"currency": "JPY", "z_basket": 0.20, "slope": 0.01, "curvature": 0.00, "phase": "NEUTRAL_ZONE"},
    ]
    result = detect_currency_coalitions(demo_vectors)
    print(json.dumps(coalitions_to_dict(result), ensure_ascii=False, indent=2))
    print()
    print(summarize_coalitions(result))
