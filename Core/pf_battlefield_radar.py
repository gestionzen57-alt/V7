#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V6 - pf_battlefield_radar.py
Version: V0.2

Mission:
    Convert coalition/relation readouts into cockpit-oriented battlefield scenes.

V0.2 changes:
    - Active relations are strategically prioritized above isolated coalitions.
    - Coalition interest thresholds are less inflated.
    - Adds strategic_score.
    - Keeps BattlefieldRadar strictly before TemporalDensity / TemporalWindowActive.

Doctrine:
    BattlefieldRadar ne dit pas "la fenêtre est ouverte".
    Il dit "ici, une bataille se prépare".
"""

import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from pf_personalities import get_devise_profile


# Relation thresholds: a relation is already more strategic because it has antagonist.
REL_HIGH = 0.70
REL_MEDIUM = 0.55
REL_LOW = 0.45

# Coalition thresholds: high cohesion alone is useful, but not equal to relation active.
COAL_HIGH = 0.90
COAL_MEDIUM = 0.80
COAL_LOW = 0.75


@dataclass(frozen=True)
class BattlefieldScene:
    scene_id: str
    timeframe: Optional[int]
    time_key: Optional[str]
    battle_state: str
    interest_level: str
    scene_type: str
    main_antagonist: Optional[str]
    main_coalition: Tuple[str, ...]
    dominant_pattern: Optional[str]
    field_score: float
    cohesion: float
    strategic_score: float
    relation_count: int
    coalition_count: int
    temporal_density_state: str
    tags: Tuple[str, ...]
    cockpit_sentence: str
    note: str

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["main_coalition"] = list(self.main_coalition)
        data["tags"] = list(self.tags)
        return data



def get_profile_safe(currency: Optional[str]):
    """Safe profile accessor: uppercase + None-tolerant."""
    if not currency:
        return None
    try:
        return get_devise_profile(str(currency).upper())
    except Exception:
        return None


def antagonist_role_weight(antagonist: Optional[str]) -> float:
    p = get_profile_safe(antagonist)
    if p is None:
        return 0.0
    if p.role == "PIVOT":
        return 0.06 if p.devise == "USD" else 0.05
    if p.role == "REFUGE":
        return 0.04
    if p.role == "RISK":
        return 0.03
    return 0.0


def coalition_role_mix_weight(members: Sequence[str]) -> float:
    profiles = [get_profile_safe(m) for m in members]
    profiles = [p for p in profiles if p is not None]

    if not profiles:
        return 0.0

    roles = [p.role for p in profiles]
    risk_share = sum(1 for r in roles if r == "RISK") / len(roles)
    refuge_share = sum(1 for r in roles if r == "REFUGE") / len(roles)

    # Encourage structurally coherent coalitions without overpowering base score.
    return (max(risk_share, refuge_share) - 0.5) * 0.04


def timeframe_personality_weight(
    timeframe: Optional[int],
    members: Sequence[str],
    antagonist: Optional[str],
) -> float:
    if timeframe is None:
        return 0.0

    profiles = [get_profile_safe(m) for m in members]
    ant = get_profile_safe(antagonist)
    if ant is not None:
        profiles.append(ant)

    tempos = [
        p.tempo_tf
        for p in profiles
        if p is not None and getattr(p, "tempo_tf", 0) > 0
    ]
    if not tempos:
        return 0.0

    mean_tempo = sum(tempos) / len(tempos)
    gap = abs(float(timeframe) - mean_tempo)

    if gap <= 5:
        return 0.03
    if gap <= 12:
        return 0.015
    if gap >= 25:
        return -0.02
    return 0.0


def radar_personality_weight(
    scene_type: str,
    timeframe: Optional[int],
    members: Sequence[str],
    antagonist: Optional[str],
) -> float:
    role_w = antagonist_role_weight(antagonist)
    mix_w = coalition_role_mix_weight(members)
    tf_w = timeframe_personality_weight(timeframe, members, antagonist)

    base = role_w + mix_w + tf_w

    # Relation active keeps priority in V0.2 hierarchy.
    if scene_type == "RELATION_ACTIVE":
        base += 0.01 if antagonist else 0.0

    # Coalition-only scenes must remain below relation-active scenes.
    if scene_type == "COALITION_STRONG":
        base -= 0.01

    return max(-0.08, min(0.08, round(base, 4)))

def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _members_from_relation(rel: Mapping[str, Any]) -> Tuple[str, ...]:
    return tuple(str(x).upper() for x in _as_list(rel.get("coalition_members")))


def _members_from_coalition(coal: Mapping[str, Any]) -> Tuple[str, ...]:
    return tuple(str(x).upper() for x in _as_list(coal.get("members")))


def _tags_from_items(*items: Mapping[str, Any]) -> Tuple[str, ...]:
    tags: List[str] = []
    for item in items:
        for tag in _as_list(item.get("tags")):
            s = str(tag)
            if s and s not in tags:
                tags.append(s)
    return tuple(tags)


def interest_level_for_relation(score: float) -> str:
    if score >= REL_HIGH:
        return "HIGH"
    if score >= REL_MEDIUM:
        return "MEDIUM"
    if score >= REL_LOW:
        return "LOW"
    return "WATCH"


def interest_level_for_coalition(cohesion: float) -> str:
    if cohesion >= COAL_HIGH:
        return "HIGH"
    if cohesion >= COAL_MEDIUM:
        return "MEDIUM"
    if cohesion >= COAL_LOW:
        return "LOW"
    return "WATCH"


def battle_state_from_relation(rel: Mapping[str, Any]) -> str:
    field_state = str(rel.get("field_state", ""))
    score = _safe_float(rel.get("field_score"))

    if field_state == "FIELD_SIDE_SHIFT_ACTIVE" or score >= 0.72:
        return "BATTLE_PRESSURIZED"
    if field_state == "BATTLEFIELD_WINDOW_OPENING" or score >= 0.55:
        return "BATTLE_FORMING"
    if field_state in ("STRUCTURE_BUILDING", "POLARITY_PRESENT_TIMING_WEAK") or score >= 0.45:
        return "BATTLE_PREPARING"
    return "BATTLE_WATCH"


def battle_state_from_coalition(coal: Mapping[str, Any]) -> str:
    cohesion = _safe_float(coal.get("cohesion"))
    ants = _as_list(coal.get("antagonist_candidates"))

    if cohesion >= 0.90 and ants:
        return "BATTLE_PREPARING"
    if cohesion >= 0.90:
        return "COALITION_FIELD_STRONG"
    if cohesion >= 0.80:
        return "COALITION_FIELD_VISIBLE"
    if cohesion >= 0.75:
        return "COALITION_FIELD_WATCH"
    return "BATTLE_WATCH"


def _scene_id(timeframe: Optional[int], time_key: Optional[str], scene_type: str, members: Sequence[str], antagonist: Optional[str]) -> str:
    tf = f"TF{timeframe}" if timeframe is not None else "TFNA"
    t = (time_key or "NO_TIME").replace(":", "").replace("-", "").replace("+", "").replace("T", "_")
    mem = "_".join(members) if members else "NO_COALITION"
    ant = antagonist or "NO_ANT"
    return f"{tf}_{t}_{scene_type}_{mem}_VS_{ant}"


def relation_strategic_score(
    field_score: float,
    *,
    timeframe: Optional[int] = None,
    members: Sequence[str] = (),
    antagonist: Optional[str] = None,
) -> float:
    """Relation gets structural priority because it contains antagonist."""
    base = 1.0 + field_score
    calib = radar_personality_weight("RELATION_ACTIVE", timeframe, members, antagonist)
    return round(base + calib, 4)


def coalition_strategic_score(
    cohesion: float,
    has_antagonist_candidate: bool,
    *,
    timeframe: Optional[int] = None,
    members: Sequence[str] = (),
    antagonist: Optional[str] = None,
) -> float:
    bonus = 0.08 if has_antagonist_candidate else 0.0
    base = 0.70 + min(cohesion, 1.0) * 0.30 + bonus
    calib = radar_personality_weight("COALITION_STRONG", timeframe, members, antagonist)
    return round(base + calib, 4)


def scene_from_relation(
    relation: Mapping[str, Any],
    *,
    timeframe: Optional[int] = None,
    time_key: Optional[str] = None,
    relation_count: int = 1,
    coalition_count: int = 0,
) -> BattlefieldScene:
    members = _members_from_relation(relation)
    antagonist = str(relation.get("antagonist")) if relation.get("antagonist") else None
    field_score = _safe_float(relation.get("field_score"))
    state = battle_state_from_relation(relation)
    level = interest_level_for_relation(field_score)
    pattern = str(relation.get("relation_type", "")) or None
    tags = _tags_from_items(relation)
    strategic_score = relation_strategic_score(field_score)

    sentence = (
        f"[TF{timeframe}] {'+'.join(members)} vs {antagonist} — "
        f"{state} / {pattern} / field={field_score:.2f}"
    )

    note = (
        f"Relation collective détectée: {'+'.join(members)} contre {antagonist}. "
        f"BattlefieldRadar classe la scène comme {state}. "
        "TemporalDensity non encore évalué."
    )

    return BattlefieldScene(
        scene_id=_scene_id(timeframe, time_key, "RELATION", members, antagonist),
        timeframe=timeframe,
        time_key=time_key,
        battle_state=state,
        interest_level=level,
        scene_type="RELATION_ACTIVE",
        main_antagonist=antagonist,
        main_coalition=members,
        dominant_pattern=pattern,
        field_score=round(field_score, 4),
        cohesion=0.0,
        strategic_score=strategic_score,
        relation_count=relation_count,
        coalition_count=coalition_count,
        temporal_density_state="PENDING",
        tags=tags,
        cockpit_sentence=sentence,
        note=note,
    )


def scene_from_coalition(
    coalition: Mapping[str, Any],
    *,
    timeframe: Optional[int] = None,
    time_key: Optional[str] = None,
    relation_count: int = 0,
    coalition_count: int = 1,
) -> BattlefieldScene:
    members = _members_from_coalition(coalition)
    antagonists = _as_list(coalition.get("antagonist_candidates"))
    antagonist = str(antagonists[0]) if antagonists else None
    cohesion = _safe_float(coalition.get("cohesion"))
    state = battle_state_from_coalition(coalition)
    level = interest_level_for_coalition(cohesion)
    pattern = str(coalition.get("state", "")) or None
    tags = _tags_from_items(coalition)
    strategic_score = coalition_strategic_score(cohesion, antagonist is not None)

    sentence = (
        f"[TF{timeframe}] {'+'.join(members)} — {state} / "
        f"{pattern} / cohesion={cohesion:.2f}"
    )

    note = (
        f"Coalition forte détectée: {'+'.join(members)}. "
        "Aucune relation active propre au seuil courant. "
        "Scène d'intérêt cockpit, pas fenêtre temporelle active."
    )

    return BattlefieldScene(
        scene_id=_scene_id(timeframe, time_key, "COALITION", members, antagonist),
        timeframe=timeframe,
        time_key=time_key,
        battle_state=state,
        interest_level=level,
        scene_type="COALITION_STRONG",
        main_antagonist=antagonist,
        main_coalition=members,
        dominant_pattern=pattern,
        field_score=0.0,
        cohesion=round(cohesion, 4),
        strategic_score=strategic_score,
        relation_count=relation_count,
        coalition_count=coalition_count,
        temporal_density_state="PENDING",
        tags=tags,
        cockpit_sentence=sentence,
        note=note,
    )


def _scene_sort_key(scene: BattlefieldScene) -> Tuple[int, float, float]:
    # Active relations first, then strategic score.
    type_rank = 2 if scene.scene_type == "RELATION_ACTIVE" else 1
    interest_rank = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "WATCH": 0}.get(scene.interest_level, 0)
    return (type_rank, scene.strategic_score, interest_rank)


def dedupe_scenes(scenes: Sequence[BattlefieldScene]) -> List[BattlefieldScene]:
    """Keep best scene for repeated same battle family."""
    by_key: Dict[Tuple[Any, ...], BattlefieldScene] = {}

    for scene in scenes:
        key = (
            scene.timeframe,
            scene.scene_type,
            tuple(scene.main_coalition),
            scene.main_antagonist,
            scene.dominant_pattern,
        )
        current = by_key.get(key)
        if current is None or _scene_sort_key(scene) > _scene_sort_key(current):
            by_key[key] = scene

    out = list(by_key.values())
    out.sort(key=_scene_sort_key, reverse=True)
    return out


def build_battlefield_scenes_from_scan_payload(
    payload: Mapping[str, Any],
    *,
    max_scenes: int = 20,
    dedupe: bool = True,
) -> List[BattlefieldScene]:
    timeframe = payload.get("timeframe")
    scenes: List[BattlefieldScene] = []

    for window in payload.get("active_windows", []) or []:
        time_key = window.get("time_key")
        relations = window.get("active_relations", []) or []
        coalitions = window.get("strong_coalitions", []) or []
        for rel in relations:
            scenes.append(scene_from_relation(
                rel,
                timeframe=timeframe,
                time_key=time_key,
                relation_count=len(relations),
                coalition_count=len(coalitions),
            ))

    for window in payload.get("strong_coalition_windows", []) or []:
        time_key = window.get("time_key")
        coalitions = window.get("strong_coalitions", []) or []
        for coal in coalitions:
            scenes.append(scene_from_coalition(
                coal,
                timeframe=timeframe,
                time_key=time_key,
                relation_count=0,
                coalition_count=len(coalitions),
            ))

    if dedupe:
        scenes = dedupe_scenes(scenes)
    else:
        scenes.sort(key=_scene_sort_key, reverse=True)

    return scenes[:max_scenes]


def build_battlefield_scenes_from_latest_payload(
    payload: Mapping[str, Any],
    *,
    max_scenes: int = 10,
    dedupe: bool = True,
) -> List[BattlefieldScene]:
    timeframe = payload.get("timeframe")
    time_key = payload.get("time_key")
    scenes: List[BattlefieldScene] = []

    active_relations = payload.get("active_relations", []) or []
    strong_coalitions = payload.get("strong_coalitions", []) or []

    for rel in active_relations:
        scenes.append(scene_from_relation(
            rel,
            timeframe=timeframe,
            time_key=time_key,
            relation_count=len(active_relations),
            coalition_count=len(strong_coalitions),
        ))

    for coal in strong_coalitions:
        scenes.append(scene_from_coalition(
            coal,
            timeframe=timeframe,
            time_key=time_key,
            relation_count=len(active_relations),
            coalition_count=len(strong_coalitions),
        ))

    if dedupe:
        scenes = dedupe_scenes(scenes)
    else:
        scenes.sort(key=_scene_sort_key, reverse=True)

    return scenes[:max_scenes]


def scenes_to_dict(scenes: Sequence[BattlefieldScene]) -> List[Dict[str, Any]]:
    return [s.to_dict() for s in scenes]


def summarize_battlefield_scenes(scenes: Sequence[BattlefieldScene]) -> str:
    if not scenes:
        return "Aucune bataille en préparation au seuil courant."

    lines: List[str] = []
    for scene in scenes:
        lines.append(
            f"{scene.time_key or '-'} | TF={scene.timeframe} | "
            f"{scene.interest_level:<6} | {scene.scene_type:<16} | "
            f"{scene.battle_state:<24} | strategic={scene.strategic_score:.2f} | "
            f"{scene.cockpit_sentence}"
        )
    return "\n".join(lines)


def cockpit_global_sentence(scenes: Sequence[BattlefieldScene]) -> str:
    if not scenes:
        return "Radar: aucune bataille stratégique claire."

    active = [s for s in scenes if s.scene_type == "RELATION_ACTIVE"]
    if active:
        best = active[0]
        return f"Radar: bataille relationnelle prioritaire — {best.cockpit_sentence}"

    best = scenes[0]
    if best.interest_level in ("HIGH", "MEDIUM"):
        return f"Radar: coalition forte à surveiller — {best.cockpit_sentence}"

    return f"Radar: champ d'intérêt faible — {best.cockpit_sentence}"


if __name__ == "__main__":
    demo_payload = {
        "timeframe": 15,
        "active_windows": [
            {
                "time_key": "2026-05-01T08:15:00+00:00",
                "active_relations": [
                    {
                        "coalition_members": ["AUD", "CAD"],
                        "antagonist": "JPY",
                        "relation_type": "LOW_BLOCK_RESPRING_AGAINST_HIGH_FOLDING",
                        "field_state": "STRUCTURE_BUILDING",
                        "field_score": 0.57,
                        "tags": ["M5_M15_INTERMEDIATE_FIELD"],
                    }
                ],
                "strong_coalitions": [],
            }
        ],
        "strong_coalition_windows": [
            {
                "time_key": "2026-05-01T23:13:00+00:00",
                "strong_coalitions": [
                    {
                        "members": ["CHF", "EUR"],
                        "state": "HIGH_PRESSURE_COALITION_FOLDING",
                        "phase": "MICROFILM_SYNCHRONIZED_FIELD",
                        "cohesion": 0.94,
                        "antagonist_candidates": [],
                        "tags": ["M1_SPECIAL_MICROFILM"],
                    }
                ],
            }
        ],
    }
    scenes = build_battlefield_scenes_from_scan_payload(demo_payload)
    print(json.dumps(scenes_to_dict(scenes), ensure_ascii=False, indent=2))
    print()
    print(cockpit_global_sentence(scenes))
    print(summarize_battlefield_scenes(scenes))
