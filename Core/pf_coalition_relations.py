#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V6 - pf_coalition_relations.py
Version: V0.1

Mission:
    Qualify the battlefield relation between a currency coalition and its
    antagonist candidates.

Doctrine:
    - pf_coalitions.py detects actors that breathe together.
    - pf_coalition_relations.py names the opposition field.
    - It does not compute z_basket.
    - It does not detect temporal nodes.
    - It does not alert Telegram.
    - It does not write DB.
    - It is a safe bridge before patching pf_relations.py.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from pf_personalities import get_devise_profile


CENTER_Z = 0.50
EXTREME_Z = 2.0


@dataclass(frozen=True)
class CoalitionBattlefieldRelation:
    relation_id: str
    coalition_id: str
    coalition_members: Tuple[str, ...]
    antagonist: str
    relation_type: str
    field_state: str
    phase: str
    coalition_polarity: str
    coalition_direction: str
    antagonist_polarity: str
    antagonist_direction: str
    coalition_z: float
    antagonist_z: float
    coalition_slope: float
    antagonist_slope: float
    opposition_score: float
    timing_score: float
    field_score: float
    tags: Tuple[str, ...]
    note: str

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["coalition_members"] = list(self.coalition_members)
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


def role_opposition_score(coalition_members: Sequence[str], antagonist: str) -> float:
    ant = get_profile_safe(antagonist)
    if ant is None:
        return 0.5

    roles = [
        p.role
        for p in (get_profile_safe(c) for c in coalition_members)
        if p is not None
    ]
    if not roles:
        return 0.5

    risk_share = sum(1 for r in roles if r == "RISK") / len(roles)
    refuge_share = sum(1 for r in roles if r == "REFUGE") / len(roles)

    if ant.role == "REFUGE":
        return 0.55 + (0.35 * risk_share)
    if ant.role == "RISK":
        return 0.55 + (0.35 * refuge_share)

    # Pivot antagonist creates structural tension against strongly one-sided coalitions.
    return 0.55 + (0.25 * max(risk_share, refuge_share))


def pivot_gravity_score(coalition_members: Sequence[str], antagonist: str) -> float:
    ant = get_profile_safe(antagonist)
    if ant is None:
        return 0.5
    if ant.role != "PIVOT":
        return 0.45

    # USD as pivot gets slightly stronger gravity effect.
    return 0.8 if ant.devise == "USD" else 0.72


def refuge_opposition_score(coalition_members: Sequence[str], antagonist: str) -> float:
    ant = get_profile_safe(antagonist)
    if ant is None:
        return 0.5

    roles = [
        p.role
        for p in (get_profile_safe(c) for c in coalition_members)
        if p is not None
    ]
    if not roles:
        return 0.5

    refuge_share = sum(1 for r in roles if r == "REFUGE") / len(roles)
    risk_share = sum(1 for r in roles if r == "RISK") / len(roles)

    if ant.role == "RISK":
        return 0.55 + (0.35 * refuge_share)
    if ant.role == "REFUGE":
        return 0.55 + (0.25 * risk_share)
    return 0.5


def lag_relation_score(coalition_members: Sequence[str], antagonist: str) -> float:
    ant = get_profile_safe(antagonist)
    if ant is None:
        return 0.5

    mem_profiles = [get_profile_safe(c) for c in coalition_members]
    mem_profiles = [p for p in mem_profiles if p is not None]
    if not mem_profiles:
        return 0.5

    ant_code = ant.devise
    member_codes = {p.devise for p in mem_profiles}

    # Light boost if leader/follower relationship exists across coalition-antagonist boundary.
    for p in mem_profiles:
        if p.lag_ref == ant_code and p.lag_bars > 0:
            return 0.7

    if ant.lag_ref in member_codes and ant.lag_bars > 0:
        return 0.7

    return 0.5


def personality_relation_score(coalition_members: Sequence[str], antagonist: str) -> float:
    role = role_opposition_score(coalition_members, antagonist)
    pivot = pivot_gravity_score(coalition_members, antagonist)
    refuge = refuge_opposition_score(coalition_members, antagonist)
    lag = lag_relation_score(coalition_members, antagonist)
    return round((0.35 * role) + (0.30 * pivot) + (0.20 * refuge) + (0.15 * lag), 4)

def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(out) or math.isinf(out):
        return default
    return out


def _currency(row: Mapping[str, Any]) -> str:
    return str(row.get("currency", "UNKNOWN")).upper()


def _polarity_from_z(z: float) -> str:
    if z >= CENTER_Z:
        return "HIGH"
    if z <= -CENTER_Z:
        return "LOW"
    return "CENTER"


def _direction_from_slope(slope: float) -> str:
    if slope > 0.04:
        return "RISING"
    if slope < -0.04:
        return "FALLING"
    return "FLAT"


def _vector_map(vectors: Sequence[Mapping[str, Any]]) -> Dict[str, Mapping[str, Any]]:
    out: Dict[str, Mapping[str, Any]] = {}
    for v in vectors:
        cur = _currency(v)
        if cur != "UNKNOWN":
            out[cur] = v
    return out


def _coalition_dict(coalition: Any) -> Dict[str, Any]:
    if hasattr(coalition, "to_dict") and callable(coalition.to_dict):
        return coalition.to_dict()
    if isinstance(coalition, Mapping):
        return dict(coalition)
    if hasattr(coalition, "__dict__"):
        return dict(coalition.__dict__)
    raise TypeError("coalition must be a mapping or expose to_dict()")


def _get_antagonists(coalition: Mapping[str, Any]) -> List[str]:
    raw = coalition.get("antagonist_candidates", [])
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw.upper()]
    return [str(x).upper() for x in raw]


def _score_opposition(coalition_z: float, antagonist_z: float) -> float:
    if coalition_z * antagonist_z >= 0:
        return 0.0
    c = min(abs(coalition_z), 3.0) / 3.0
    a = min(abs(antagonist_z), 3.0) / 3.0
    return round((c + a) / 2.0, 4)


def _score_timing(coalition_slope: float, antagonist_slope: float) -> float:
    if coalition_slope * antagonist_slope >= 0:
        return 0.0
    c = min(abs(coalition_slope), 0.35) / 0.35
    a = min(abs(antagonist_slope), 0.35) / 0.35
    return round((c + a) / 2.0, 4)


def _classify_relation_type(
    coalition_polarity: str,
    coalition_direction: str,
    antagonist_polarity: str,
    antagonist_direction: str,
) -> str:
    if (
        coalition_polarity == "LOW"
        and coalition_direction == "RISING"
        and antagonist_polarity == "HIGH"
        and antagonist_direction == "FALLING"
    ):
        return "LOW_BLOCK_RESPRING_AGAINST_HIGH_FOLDING"

    if (
        coalition_polarity == "HIGH"
        and coalition_direction == "FALLING"
        and antagonist_polarity == "LOW"
        and antagonist_direction == "RISING"
    ):
        return "HIGH_BLOCK_FOLDING_AGAINST_LOW_RESPRING"

    if coalition_polarity != antagonist_polarity and (
        coalition_direction == "FLAT" or antagonist_direction == "FLAT"
    ):
        return "POLARIZED_FIELD_WITH_WEAK_TIMING"

    if coalition_polarity != antagonist_polarity and coalition_direction != antagonist_direction:
        return "COALITION_VS_ANTAGONIST_OPPOSITION"

    if coalition_polarity != antagonist_polarity:
        return "POLARIZED_FIELD_WITH_WEAK_TIMING"

    return "UNQUALIFIED_RELATION"


def _classify_field_state(relation_type: str, opposition_score: float, timing_score: float) -> str:
    field_score = (opposition_score * 0.55) + (timing_score * 0.45)

    if field_score >= 0.72 and relation_type in (
        "LOW_BLOCK_RESPRING_AGAINST_HIGH_FOLDING",
        "HIGH_BLOCK_FOLDING_AGAINST_LOW_RESPRING",
    ):
        return "FIELD_SIDE_SHIFT_ACTIVE"

    if field_score >= 0.58:
        return "BATTLEFIELD_WINDOW_OPENING"

    if opposition_score >= 0.55 and timing_score < 0.35:
        return "POLARITY_PRESENT_TIMING_WEAK"

    if opposition_score < 0.40:
        return "WEAK_FIELD_OPPOSITION"

    return "STRUCTURE_BUILDING"


def _phase_from_relation(relation_type: str, field_state: str) -> str:
    if field_state == "FIELD_SIDE_SHIFT_ACTIVE":
        return "ACTIVE_COALITION_ROTATION"
    if field_state == "BATTLEFIELD_WINDOW_OPENING":
        return "TEMPORAL_WINDOW_PREPARING"
    if relation_type == "LOW_BLOCK_RESPRING_AGAINST_HIGH_FOLDING":
        return "LOW_COALITION_RELEASE_BIRTH"
    if relation_type == "HIGH_BLOCK_FOLDING_AGAINST_LOW_RESPRING":
        return "HIGH_COALITION_RELEASE_BIRTH"
    return "FIELD_RELATION_OBSERVATION"


def _build_tags(
    coalition: Mapping[str, Any],
    antagonist_vector: Mapping[str, Any],
    relation_type: str,
    field_state: str,
) -> Tuple[str, ...]:
    tags: List[str] = []

    for tag in coalition.get("tags", []) or []:
        tags.append(str(tag))

    for tag in antagonist_vector.get("context_tags", antagonist_vector.get("contextual_tags", [])) or []:
        tag = str(tag)
        if tag not in tags:
            tags.append(tag)

    tags.append(relation_type)
    tags.append(field_state)

    unique: List[str] = []
    for tag in tags:
        if tag and tag not in unique:
            unique.append(tag)
    return tuple(unique)


def _build_note(
    coalition_members: Sequence[str],
    antagonist: str,
    relation_type: str,
    field_state: str,
    coalition_z: float,
    antagonist_z: float,
    coalition_slope: float,
    antagonist_slope: float,
) -> str:
    members = "+".join(coalition_members)
    if relation_type == "LOW_BLOCK_RESPRING_AGAINST_HIGH_FOLDING":
        return (
            f"{members} forme un bloc bas en respring contre {antagonist} haut qui plie. "
            f"Champ={field_state}. z_block={coalition_z:+.2f}, z_ant={antagonist_z:+.2f}, "
            f"slope_block={coalition_slope:+.2f}, slope_ant={antagonist_slope:+.2f}."
        )
    if relation_type == "HIGH_BLOCK_FOLDING_AGAINST_LOW_RESPRING":
        return (
            f"{members} forme un bloc haut qui plie contre {antagonist} bas en respring. "
            f"Champ={field_state}. z_block={coalition_z:+.2f}, z_ant={antagonist_z:+.2f}, "
            f"slope_block={coalition_slope:+.2f}, slope_ant={antagonist_slope:+.2f}."
        )
    return (
        f"{members} oppose {antagonist}. Relation={relation_type}, champ={field_state}. "
        f"z_block={coalition_z:+.2f}, z_ant={antagonist_z:+.2f}."
    )


def qualify_coalition_relation(
    coalition: Any,
    vectors: Sequence[Mapping[str, Any]],
) -> List[CoalitionBattlefieldRelation]:
    c = _coalition_dict(coalition)
    vmap = _vector_map(vectors)

    coalition_id = str(c.get("coalition_id", "UNKNOWN_COALITION"))
    members = tuple(str(x).upper() for x in c.get("members", ()))
    coalition_polarity = str(c.get("polarity", "CENTER"))
    coalition_direction = str(c.get("direction", "FLAT"))
    coalition_z = _safe_float(c.get("z_mean", 0.0))
    coalition_slope = _safe_float(c.get("slope_mean", 0.0))

    out: List[CoalitionBattlefieldRelation] = []

    for antagonist in _get_antagonists(c):
        av = vmap.get(antagonist)
        if av is None:
            continue

        antagonist_z = _safe_float(av.get("z_basket", av.get("z_current", 0.0)))
        antagonist_slope = _safe_float(av.get("slope", 0.0))
        antagonist_polarity = _polarity_from_z(antagonist_z)
        antagonist_direction = _direction_from_slope(antagonist_slope)

        relation_type = _classify_relation_type(
            coalition_polarity,
            coalition_direction,
            antagonist_polarity,
            antagonist_direction,
        )
        opposition_score = _score_opposition(coalition_z, antagonist_z)
        timing_score = _score_timing(coalition_slope, antagonist_slope)
        field_state = _classify_field_state(relation_type, opposition_score, timing_score)
        phase = _phase_from_relation(relation_type, field_state)
        base_field_score = (opposition_score * 0.55) + (timing_score * 0.45)
        personality_score = personality_relation_score(members, antagonist)
        # Personality is calibration only (bounded to roughly +/- 0.07 around neutral 0.5).
        field_score = round(
            min(1.0, max(0.0, base_field_score + ((personality_score - 0.5) * 0.14))),
            4,
        )

        tags = _build_tags(c, av, relation_type, field_state)
        note = _build_note(
            members,
            antagonist,
            relation_type,
            field_state,
            coalition_z,
            antagonist_z,
            coalition_slope,
            antagonist_slope,
        )

        out.append(
            CoalitionBattlefieldRelation(
                relation_id=f"{coalition_id}_VS_{antagonist}_{relation_type}",
                coalition_id=coalition_id,
                coalition_members=members,
                antagonist=antagonist,
                relation_type=relation_type,
                field_state=field_state,
                phase=phase,
                coalition_polarity=coalition_polarity,
                coalition_direction=coalition_direction,
                antagonist_polarity=antagonist_polarity,
                antagonist_direction=antagonist_direction,
                coalition_z=round(coalition_z, 4),
                antagonist_z=round(antagonist_z, 4),
                coalition_slope=round(coalition_slope, 4),
                antagonist_slope=round(antagonist_slope, 4),
                opposition_score=opposition_score,
                timing_score=timing_score,
                field_score=field_score,
                tags=tags,
                note=note,
            )
        )

    out.sort(key=lambda r: r.field_score, reverse=True)
    return out


def qualify_coalition_relations(
    coalitions: Sequence[Any],
    vectors: Sequence[Mapping[str, Any]],
) -> List[CoalitionBattlefieldRelation]:
    relations: List[CoalitionBattlefieldRelation] = []
    for coalition in coalitions:
        relations.extend(qualify_coalition_relation(coalition, vectors))
    relations.sort(key=lambda r: r.field_score, reverse=True)
    return relations


def relations_to_dict(relations: Sequence[CoalitionBattlefieldRelation]) -> List[Dict[str, Any]]:
    return [r.to_dict() for r in relations]


def summarize_relations(relations: Sequence[CoalitionBattlefieldRelation]) -> str:
    if not relations:
        return "No active coalition relation."
    lines: List[str] = []
    for r in relations:
        members = "+".join(r.coalition_members)
        lines.append(
            f"{members} vs {r.antagonist}: {r.relation_type} | "
            f"field={r.field_state} | score={r.field_score:.2f} | phase={r.phase}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    demo_coalition = {
        "coalition_id": "EUR_GBP_LOW_ELASTIC_COALITION_RESPRING",
        "members": ["EUR", "GBP"],
        "polarity": "LOW",
        "direction": "RISING",
        "state": "LOW_ELASTIC_COALITION_RESPRING",
        "phase": "MICROFILM_SYNCHRONIZED_FIELD",
        "z_mean": -2.15,
        "slope_mean": 0.125,
        "antagonist_candidates": ["USD"],
        "tags": ["M1_SPECIAL_MICROFILM", "LOCAL_ZONE_WORK"],
    }
    demo_vectors = [
        {"currency": "GBP", "z_basket": -2.24, "slope": 0.14, "context_tags": ["M1_SPECIAL_MICROFILM"]},
        {"currency": "EUR", "z_basket": -2.06, "slope": 0.11, "context_tags": ["M1_SPECIAL_MICROFILM"]},
        {"currency": "USD", "z_basket": 2.45, "slope": -0.18, "context_tags": ["M1_SPECIAL_MICROFILM", "LOCAL_ZONE_WORK"]},
    ]
    rels = qualify_coalition_relation(demo_coalition, demo_vectors)
    print(json.dumps(relations_to_dict(rels), ensure_ascii=False, indent=2))
    print()
    print(summarize_relations(rels))
