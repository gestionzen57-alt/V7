#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V6 - pf_battlefield_radar.py
Version: V0.1

Mission:
    Convert coalition/relation readouts into cockpit-oriented battlefield scenes.

Doctrine:
    BattlefieldRadar does not open a temporal window.
    It says: "here, a battle is preparing / forming / pressurized".
"""

import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


DEFAULT_HIGH_INTEREST = 0.70
DEFAULT_MEDIUM_INTEREST = 0.50
DEFAULT_LOW_INTEREST = 0.30


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


def interest_level(score: float) -> str:
    if score >= DEFAULT_HIGH_INTEREST:
        return "HIGH"
    if score >= DEFAULT_MEDIUM_INTEREST:
        return "MEDIUM"
    if score >= DEFAULT_LOW_INTEREST:
        return "LOW"
    return "WATCH"


def battle_state_from_relation(rel: Mapping[str, Any]) -> str:
    field_state = str(rel.get("field_state", ""))
    score = _safe_float(rel.get("field_score"))

    if field_state == "FIELD_SIDE_SHIFT_ACTIVE" or score >= 0.72:
        return "BATTLE_PRESSURIZED"
    if field_state == "BATTLEFIELD_WINDOW_OPENING" or score >= 0.60:
        return "BATTLE_FORMING"
    if field_state in ("STRUCTURE_BUILDING", "POLARITY_PRESENT_TIMING_WEAK") or score >= 0.45:
        return "BATTLE_PREPARING"
    return "BATTLE_WATCH"


def battle_state_from_coalition(coal: Mapping[str, Any]) -> str:
    cohesion = _safe_float(coal.get("cohesion"))
    ants = _as_list(coal.get("antagonist_candidates"))
    if cohesion >= 0.90 and ants:
        return "BATTLE_PREPARING"
    if cohesion >= 0.85:
        return "COALITION_FIELD_STRONG"
    if cohesion >= 0.75:
        return "COALITION_FIELD_VISIBLE"
    return "BATTLE_WATCH"


def _scene_id(timeframe: Optional[int], time_key: Optional[str], scene_type: str, members: Sequence[str], antagonist: Optional[str]) -> str:
    tf = f"TF{timeframe}" if timeframe is not None else "TFNA"
    t = (time_key or "NO_TIME").replace(":", "").replace("-", "").replace("+", "").replace("T", "_")
    mem = "_".join(members) if members else "NO_COALITION"
    ant = antagonist or "NO_ANT"
    return f"{tf}_{t}_{scene_type}_{mem}_VS_{ant}"


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
    level = interest_level(field_score)
    pattern = str(relation.get("relation_type", "")) or None
    tags = _tags_from_items(relation)

    sentence = (
        f"[TF{timeframe}] {'+'.join(members)} vs {antagonist} — "
        f"{state} / {pattern} / score={field_score:.2f}"
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
    level = interest_level(cohesion)
    pattern = str(coalition.get("state", "")) or None
    tags = _tags_from_items(coalition)

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
        relation_count=relation_count,
        coalition_count=coalition_count,
        temporal_density_state="PENDING",
        tags=tags,
        cockpit_sentence=sentence,
        note=note,
    )


def _scene_sort_key(scene: BattlefieldScene) -> Tuple[int, float, int]:
    interest_rank = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "WATCH": 0}.get(scene.interest_level, 0)
    score = max(scene.field_score, scene.cohesion)
    relation_bonus = 1 if scene.scene_type == "RELATION_ACTIVE" else 0
    return (interest_rank, score, relation_bonus)


def build_battlefield_scenes_from_scan_payload(
    payload: Mapping[str, Any],
    *,
    max_scenes: int = 20,
) -> List[BattlefieldScene]:
    """Build battlefield scenes from run_coalition_relations_once.py V0.3 scan payload."""
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

    scenes.sort(key=_scene_sort_key, reverse=True)
    return scenes[:max_scenes]


def build_battlefield_scenes_from_latest_payload(
    payload: Mapping[str, Any],
    *,
    max_scenes: int = 10,
) -> List[BattlefieldScene]:
    """Build battlefield scenes from run_coalition_relations_once.py V0.3 latest payload."""
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
            f"{scene.interest_level:<6} | {scene.battle_state:<24} | "
            f"{scene.cockpit_sentence}"
        )
    return "\n".join(lines)


def cockpit_global_sentence(scenes: Sequence[BattlefieldScene]) -> str:
    if not scenes:
        return "Radar: aucune bataille stratégique claire."

    high = [s for s in scenes if s.interest_level == "HIGH"]
    active = [s for s in scenes if s.scene_type == "RELATION_ACTIVE"]

    if active:
        best = active[0]
        return f"Radar: bataille relationnelle en préparation — {best.cockpit_sentence}"

    if high:
        best = high[0]
        return f"Radar: coalition forte à surveiller — {best.cockpit_sentence}"

    best = scenes[0]
    return f"Radar: champ d'intérêt faible/moyen — {best.cockpit_sentence}"


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
        "strong_coalition_windows": [],
    }
    scenes = build_battlefield_scenes_from_scan_payload(demo_payload)
    print(json.dumps(scenes_to_dict(scenes), ensure_ascii=False, indent=2))
    print()
    print(cockpit_global_sentence(scenes))
    print(summarize_battlefield_scenes(scenes))
