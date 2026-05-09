"""
pf_relational_gravity_bridge.py
PowerFlow V6 — Relational Gravity Cockpit Bridge V0.1

Lit les JSON produits par pf_relational_gravity_probe.py.
Calcule le cross-TF state.
Retourne un bloc prêt à injecter dans cockpit_agentic_state_v01.py.

READ-ONLY JSON. Jamais de DB. Jamais de calcul moteur.
Aucune dépendance telegram_* ou capture_*.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────────────
# PATHS — ordre de priorité V0.1.1 → V0.1 fallback
# ─────────────────────────────────────────────

GRAVITY_JSON_PATHS: dict[int, list[str]] = {
    1:  [
        "output/relational_gravity_m1_v011.json",
        "output/relational_gravity_m1.json",
    ],
    5:  [
        "output/relational_gravity_m5_v011.json",
        "output/relational_gravity_m5.json",
    ],
    15: [
        "output/relational_gravity_m15_v011.json",
        "output/relational_gravity_m15.json",
    ],
}

BRIDGE_VERSION = "0.1"


# ─────────────────────────────────────────────
# CROSS-TF STATES
# ─────────────────────────────────────────────

CROSS_TF_STATES = {
    "RELATIONAL_GRAVITY_ALIGNED_M1_M5_M15",
    "M1_RELATIONAL_COUNTERFIELD",
    "M5_M15_RELATIONAL_ALIGNMENT",
    "RELATIONAL_GRAVITY_MIXED",
    "RELATIONAL_GRAVITY_MISSING",
}


# ─────────────────────────────────────────────
# DATA CLASS
# ─────────────────────────────────────────────

@dataclass
class GravitySlot:
    """Single TF gravity reading. None fields = file missing or status NO_DATA."""
    timeframe: int
    loaded: bool
    source_file: str
    status: str                        # OK / PARTIAL / NO_DATA / FILE_MISSING
    primary_state: str
    group: list[str]
    direction: str
    gap_mode: str
    leader: str
    antagonist: str
    score: float
    confidence: str
    lab_signatures: list[str]
    interpretation: str


@dataclass
class RelationalGravityCockpitBlock:
    bridge_version: str
    cross_tf_state: str
    slots: dict[int, GravitySlot]      # keyed by timeframe
    dominant_direction: str            # UP / DOWN / MIXED / UNKNOWN
    dominant_leader: str               # currency name or UNKNOWN
    dominant_antagonist: str           # string or NONE
    aligned_tfs: list[int]             # TFs agreeing on direction
    counter_tf: Optional[int]          # TF disagreeing (M1 counter = 1)
    max_score: float
    notes: list[str] = field(default_factory=list)


# ─────────────────────────────────────────────
# JSON LOADER
# ─────────────────────────────────────────────

def _load_gravity_slot(timeframe: int, base_dir: str = ".") -> GravitySlot:
    """Try each path in priority order. Return slot with status FILE_MISSING if none found."""
    paths = GRAVITY_JSON_PATHS.get(timeframe, [])
    base = Path(base_dir)

    for rel_path in paths:
        full_path = base / rel_path
        if full_path.exists():
            try:
                raw = json.loads(full_path.read_text(encoding="utf-8"))
                return GravitySlot(
                    timeframe=timeframe,
                    loaded=True,
                    source_file=str(full_path),
                    status=raw.get("status", "UNKNOWN"),
                    primary_state=raw.get("primary_state", "RELATIONAL_GRAVITY_NOISE"),
                    group=raw.get("group", []),
                    direction=raw.get("direction", "UNKNOWN"),
                    gap_mode=raw.get("gap_mode", "UNKNOWN"),
                    leader=raw.get("leader", "UNKNOWN"),
                    antagonist=raw.get("antagonist", "NONE"),
                    score=float(raw.get("score", 0.0)),
                    confidence=raw.get("confidence", "LOW"),
                    lab_signatures=raw.get("lab_signatures", []),
                    interpretation=raw.get("interpretation", ""),
                )
            except (json.JSONDecodeError, KeyError, ValueError):
                continue  # try next path

    # Nothing found
    return GravitySlot(
        timeframe=timeframe,
        loaded=False,
        source_file="",
        status="FILE_MISSING",
        primary_state="RELATIONAL_GRAVITY_MISSING",
        group=[],
        direction="UNKNOWN",
        gap_mode="UNKNOWN",
        leader="UNKNOWN",
        antagonist="NONE",
        score=0.0,
        confidence="LOW",
        lab_signatures=["RELATIONAL_GRAVITY_MISSING"],
        interpretation=f"Gravity JSON not found for TF{timeframe}.",
    )


# ─────────────────────────────────────────────
# CROSS-TF LOGIC
# ─────────────────────────────────────────────

def _compute_cross_tf_state(
    slots: dict[int, GravitySlot],
) -> tuple[str, str, str, str, list[int], Optional[int], float]:
    """
    Returns:
        cross_tf_state, dominant_direction, dominant_leader,
        dominant_antagonist, aligned_tfs, counter_tf, max_score
    """
    notes: list[str] = []

    loaded = {tf: s for tf, s in slots.items() if s.loaded and s.status in ("OK", "PARTIAL")}

    if not loaded:
        return (
            "RELATIONAL_GRAVITY_MISSING",
            "UNKNOWN", "UNKNOWN", "NONE",
            [], None, 0.0
        )

    # Directions per TF
    directions = {tf: s.direction for tf, s in loaded.items()}
    leaders = {tf: s.leader for tf, s in loaded.items()}
    antagonists = {tf: s.antagonist for tf, s in loaded.items()}
    scores = {tf: s.score for tf, s in loaded.items()}

    max_score = max(scores.values()) if scores else 0.0

    # Dominant direction: majority vote
    up_tfs = [tf for tf, d in directions.items() if d == "UP"]
    down_tfs = [tf for tf, d in directions.items() if d == "DOWN"]

    if len(up_tfs) > len(down_tfs):
        dominant_direction = "UP"
        aligned_tfs = sorted(up_tfs)
        counter_tfs = sorted(down_tfs)
    elif len(down_tfs) > len(up_tfs):
        dominant_direction = "DOWN"
        aligned_tfs = sorted(down_tfs)
        counter_tfs = sorted(up_tfs)
    else:
        dominant_direction = "MIXED"
        aligned_tfs = []
        counter_tfs = []

    counter_tf = counter_tfs[0] if counter_tfs else None

    # Dominant leader: most frequent non-UNKNOWN leader in aligned TFs
    leader_votes: dict[str, int] = {}
    for tf in aligned_tfs:
        ldr = leaders.get(tf, "UNKNOWN")
        if ldr and ldr != "UNKNOWN":
            leader_votes[ldr] = leader_votes.get(ldr, 0) + 1
    dominant_leader = (
        max(leader_votes, key=leader_votes.__getitem__)
        if leader_votes else "UNKNOWN"
    )

    # Dominant antagonist: most common across aligned TFs
    antag_votes: dict[str, int] = {}
    for tf in aligned_tfs:
        antag_str = antagonists.get(tf, "NONE")
        if antag_str and antag_str != "NONE":
            for a in antag_str.split("/"):
                a = a.strip()
                if a:
                    antag_votes[a] = antag_votes.get(a, 0) + 1
    dominant_antagonist = (
        "/".join(sorted(antag_votes, key=antag_votes.__getitem__, reverse=True))
        if antag_votes else "NONE"
    )

    # Cross-TF state classification
    all_tfs = sorted(loaded.keys())
    all_aligned = set(aligned_tfs) == set(all_tfs) and len(all_tfs) >= 3

    if all_aligned:
        cross_tf_state = "RELATIONAL_GRAVITY_ALIGNED_M1_M5_M15"

    elif counter_tf == 1 and 5 in aligned_tfs and 15 in aligned_tfs:
        # M5 + M15 agree, M1 counter
        cross_tf_state = "M1_RELATIONAL_COUNTERFIELD"

    elif 5 in aligned_tfs and 15 in aligned_tfs and 1 not in aligned_tfs:
        # M5 + M15 agree, M1 absent or counter
        cross_tf_state = "M5_M15_RELATIONAL_ALIGNMENT"

    elif dominant_direction == "MIXED" or len(aligned_tfs) < 2:
        cross_tf_state = "RELATIONAL_GRAVITY_MIXED"

    else:
        # Partial alignment — at least 2 TFs agree but not all
        cross_tf_state = "RELATIONAL_GRAVITY_MIXED"

    return (
        cross_tf_state,
        dominant_direction,
        dominant_leader,
        dominant_antagonist,
        aligned_tfs,
        counter_tf,
        round(max_score, 3),
    )


# ─────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────

def build_relational_gravity_block(
    base_dir: str = ".",
    timeframes: Optional[list[int]] = None,
) -> RelationalGravityCockpitBlock:
    """
    Main entry point for cockpit_agentic_state_v01.py.

    Usage:
        from pf_relational_gravity_bridge import build_relational_gravity_block
        rg_block = build_relational_gravity_block(base_dir=".")
        cockpit_state["relational_gravity"] = relational_gravity_block_to_dict(rg_block)

    Args:
        base_dir: root directory where output/ folder lives
        timeframes: which TFs to load (default: [1, 5, 15])

    Returns:
        RelationalGravityCockpitBlock ready to serialize
    """
    if timeframes is None:
        timeframes = [1, 5, 15]

    slots: dict[int, GravitySlot] = {}
    for tf in timeframes:
        slots[tf] = _load_gravity_slot(tf, base_dir=base_dir)

    (
        cross_tf_state,
        dominant_direction,
        dominant_leader,
        dominant_antagonist,
        aligned_tfs,
        counter_tf,
        max_score,
    ) = _compute_cross_tf_state(slots)

    notes: list[str] = []
    missing = [tf for tf, s in slots.items() if not s.loaded]
    if missing:
        notes.append(f"TF missing: {missing}")

    partial = [tf for tf, s in slots.items() if s.loaded and s.status == "PARTIAL"]
    if partial:
        notes.append(f"TF partial: {partial}")

    return RelationalGravityCockpitBlock(
        bridge_version=BRIDGE_VERSION,
        cross_tf_state=cross_tf_state,
        slots=slots,
        dominant_direction=dominant_direction,
        dominant_leader=dominant_leader,
        dominant_antagonist=dominant_antagonist,
        aligned_tfs=aligned_tfs,
        counter_tf=counter_tf,
        max_score=max_score,
        notes=notes,
    )


# ─────────────────────────────────────────────
# SERIALIZER
# ─────────────────────────────────────────────

def relational_gravity_block_to_dict(block: RelationalGravityCockpitBlock) -> dict:
    """Serialize block to plain dict for JSON cockpit state."""
    return {
        "bridge_version": block.bridge_version,
        "cross_tf_state": block.cross_tf_state,
        "dominant_direction": block.dominant_direction,
        "dominant_leader": block.dominant_leader,
        "dominant_antagonist": block.dominant_antagonist,
        "aligned_tfs": block.aligned_tfs,
        "counter_tf": block.counter_tf,
        "max_score": block.max_score,
        "notes": block.notes,
        "tf_details": {
            str(tf): {
                "loaded": s.loaded,
                "source_file": s.source_file,
                "status": s.status,
                "primary_state": s.primary_state,
                "group": s.group,
                "direction": s.direction,
                "gap_mode": s.gap_mode,
                "leader": s.leader,
                "antagonist": s.antagonist,
                "score": s.score,
                "confidence": s.confidence,
                "lab_signatures": s.lab_signatures,
                "interpretation": s.interpretation,
            }
            for tf, s in block.slots.items()
        },
    }
