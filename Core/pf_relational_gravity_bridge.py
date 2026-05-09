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

BRIDGE_VERSION = "0.1.4"  # P1.2 bridge_guard


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
    dominant_leader: str               # currency name / MIXED / UNKNOWN
    dominant_antagonist: str           # string or NONE
    aligned_tfs: list[int]             # TFs agreeing on direction
    counter_tf: Optional[int]          # TF disagreeing (M1 counter = 1)
    max_score: float
    # ── Guard fields V0.1.2 ──────────────────────────────────────
    direction_consistency: str         # ALIGNED / PARTIAL / SPLIT / UNKNOWN
    leader_consistency: str            # CONSISTENT / PARTIAL / CONFLICT / UNKNOWN
    antagonist_consistency: str        # CLEAN / DEDUPED / NONE
    topline_reliable: bool             # False if MIXED/CONFLICT
    # ── Topline State V0.1.3 ─────────────────────────────────────
    topline_state: str                 # qualification lisible du champ cross-TF
    # ── Bridge Guard P1.2 ────────────────────────────────────────
    summary: str                       # one-line cockpit-safe summary
    # ─────────────────────────────────────────────────────────────
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
) -> tuple[str, str, str, str, list[int], Optional[int], float, str, str, str, bool]:
    """
    Returns:
        cross_tf_state, dominant_direction, dominant_leader,
        dominant_antagonist, aligned_tfs, counter_tf, max_score,
        direction_consistency, leader_consistency, antagonist_consistency,
        topline_reliable

    P1.2 bridge guard:
        A final RELATIONAL_GRAVITY_MIXED field must never be exposed as a
        clear top-level leader. The guard is applied after cross-TF
        classification, because the state can become MIXED even when a
        direction majority exists.
    """
    loaded = {tf: s for tf, s in slots.items() if s.loaded and s.status in ("OK", "PARTIAL")}

    if not loaded:
        return (
            "RELATIONAL_GRAVITY_MISSING",
            "UNKNOWN", "UNKNOWN", "NONE",
            [], None, 0.0,
            "UNKNOWN", "UNKNOWN", "NONE", False,
        )

    directions  = {tf: s.direction for tf, s in loaded.items()}
    leaders     = {tf: s.leader    for tf, s in loaded.items()}
    antagonists = {tf: s.antagonist for tf, s in loaded.items()}
    scores      = {tf: s.score     for tf, s in loaded.items()}

    max_score = max(scores.values()) if scores else 0.0

    # ── Direction majority vote ──────────────────────────────────
    up_tfs   = [tf for tf, d in directions.items() if d == "UP"]
    down_tfs = [tf for tf, d in directions.items() if d == "DOWN"]

    if len(up_tfs) > len(down_tfs):
        dominant_direction = "UP"
        aligned_tfs  = sorted(up_tfs)
        counter_tfs  = sorted(down_tfs)
    elif len(down_tfs) > len(up_tfs):
        dominant_direction = "DOWN"
        aligned_tfs  = sorted(down_tfs)
        counter_tfs  = sorted(up_tfs)
    else:
        dominant_direction = "MIXED"
        aligned_tfs  = []
        counter_tfs  = []

    counter_tf = counter_tfs[0] if counter_tfs else None

    # ── direction_consistency ────────────────────────────────────
    n_loaded = len(loaded)
    n_aligned = len(aligned_tfs)
    if dominant_direction == "MIXED":
        direction_consistency = "SPLIT"
    elif n_aligned == n_loaded:
        direction_consistency = "ALIGNED"
    elif n_aligned >= 2:
        direction_consistency = "PARTIAL"
    else:
        direction_consistency = "SPLIT"

    # ── Provisional leader vote on aligned TFs ───────────────────
    # This is deliberately provisional. P1.2 final guard below can
    # demote it if the cross-TF field is classified as MIXED.
    if dominant_direction == "MIXED" or direction_consistency == "SPLIT":
        dominant_leader    = "MIXED"
        leader_consistency = "CONFLICT"
    else:
        leader_votes: dict[str, int] = {}
        for tf in aligned_tfs:
            ldr = leaders.get(tf, "UNKNOWN")
            if ldr and ldr not in ("UNKNOWN", "MIXED"):
                leader_votes[ldr] = leader_votes.get(ldr, 0) + 1

        if not leader_votes:
            dominant_leader    = "UNKNOWN"
            leader_consistency = "UNKNOWN"
        else:
            max_votes = max(leader_votes.values())
            top_leaders = sorted(
                [ldr for ldr, votes in leader_votes.items() if votes == max_votes]
            )
            if len(top_leaders) == 1:
                dominant_leader = top_leaders[0]
                leader_consistency = "CONSISTENT" if len(leader_votes) == 1 else "PARTIAL"
            else:
                dominant_leader = "MIXED"
                leader_consistency = "CONFLICT"

    # ── Dominant antagonist — deduplicate, exclude dominant_leader ─
    antag_votes: dict[str, int] = {}
    for tf in aligned_tfs:
        antag_str = antagonists.get(tf, "NONE")
        if antag_str and antag_str != "NONE":
            for antag in antag_str.split("/"):
                antag = antag.strip()
                if antag:
                    antag_votes[antag] = antag_votes.get(antag, 0) + 1

    # Remove dominant_leader from antagonist if it is a real currency.
    if dominant_leader not in ("MIXED", "UNKNOWN", "NONE", ""):
        antag_votes.pop(dominant_leader, None)

    if antag_votes:
        dominant_antagonist = "/".join(
            sorted(antag_votes, key=lambda k: (-antag_votes[k], k))
        )
        antagonist_consistency = "CLEAN" if len(antag_votes) <= 2 else "DEDUPED"
    else:
        dominant_antagonist = "NONE"
        antagonist_consistency = "NONE"

    # ── Initial reliability before final cross-TF classification ──
    topline_reliable = (
        dominant_direction not in ("MIXED", "UNKNOWN")
        and leader_consistency not in ("CONFLICT", "UNKNOWN")
        and direction_consistency in ("ALIGNED", "PARTIAL")
    )

    # ── Cross-TF state classification ────────────────────────────
    all_tfs     = sorted(loaded.keys())
    all_aligned = set(aligned_tfs) == set(all_tfs) and len(all_tfs) >= 3

    if all_aligned:
        cross_tf_state = "RELATIONAL_GRAVITY_ALIGNED_M1_M5_M15"
    elif counter_tf == 1 and 5 in aligned_tfs and 15 in aligned_tfs:
        cross_tf_state = "M1_RELATIONAL_COUNTERFIELD"
    elif 5 in aligned_tfs and 15 in aligned_tfs and 1 not in aligned_tfs:
        cross_tf_state = "M5_M15_RELATIONAL_ALIGNMENT"
    else:
        cross_tf_state = "RELATIONAL_GRAVITY_MIXED"

    # ── P1.2 Bridge Guard — final anti-misleading topline ─────────
    # A MIXED cross-TF field is not allowed to expose a clear top-level
    # leader, even if a majority direction exists or the aligned TFs share
    # the same leader. TF-level details remain untouched in tf_details.
    if cross_tf_state == "RELATIONAL_GRAVITY_MIXED":
        dominant_leader = "MIXED"
        leader_consistency = "CONFLICT"
        topline_reliable = False

        # dominant_antagonist is kept as a deduped field description, but
        # it must never contain a real dominant_leader. Here the leader is
        # MIXED, so no real currency is removed. The invariant is still
        # enforced defensively for future changes.
        if dominant_leader not in ("MIXED", "UNKNOWN", "NONE", ""):
            filtered = [
                a for a in dominant_antagonist.split("/")
                if a and a != dominant_leader
            ]
            dominant_antagonist = "/".join(filtered) if filtered else "NONE"

    return (
        cross_tf_state,
        dominant_direction,
        dominant_leader,
        dominant_antagonist,
        aligned_tfs,
        counter_tf,
        round(max_score, 3),
        direction_consistency,
        leader_consistency,
        antagonist_consistency,
        topline_reliable,
    )

# ─────────────────────────────────────────────
# TOPLINE STATE
# ─────────────────────────────────────────────

def _compute_topline_state(
    cross_tf_state: str,
    dominant_direction: str,
    dominant_leader: str,
    direction_consistency: str,
    leader_consistency: str,
    topline_reliable: bool,
    slots: dict[int, "GravitySlot"],
) -> str:
    """
    Produit topline_state — qualification lisible de la fiabilité
    du champ gravitationnel cross-TF.

    Ordre de priorité des règles (première qui s'applique gagne) :

    1. données TF partielles / manquantes
       → RELATIONAL_GRAVITY_TOPLINE_PARTIAL

    2. topline_reliable == True
       → RELATIONAL_GRAVITY_TOPLINE_RELIABLE

    3. direction_consistency == ALIGNED + leader_consistency == CONFLICT
       → RELATIONAL_GRAVITY_DIRECTION_ALIGNED_LEADER_CONFLICT

    4. direction_consistency == PARTIAL + leader_consistency == CONFLICT
       → RELATIONAL_GRAVITY_PARTIAL_DIRECTION_LEADER_CONFLICT

    5. cross_tf_state == MIXED ou dominant_leader == MIXED
       et direction_consistency != ALIGNED
       → RELATIONAL_GRAVITY_MIXED_TOPLINE_UNRELIABLE

    6. défaut
       → RELATIONAL_GRAVITY_MIXED_TOPLINE_UNRELIABLE
    """
    # Règle 1 — données TF partielles ou manquantes (priorité max)
    has_missing = any(not s.loaded for s in slots.values())
    has_partial = any(s.loaded and s.status == "PARTIAL" for s in slots.values())
    if has_missing or has_partial:
        return "RELATIONAL_GRAVITY_TOPLINE_PARTIAL"

    # Règle 2 — fiable
    if topline_reliable:
        return "RELATIONAL_GRAVITY_TOPLINE_RELIABLE"

    # Règle 3 — direction alignée mais leaders en conflit
    if direction_consistency == "ALIGNED" and leader_consistency == "CONFLICT":
        return "RELATIONAL_GRAVITY_DIRECTION_ALIGNED_LEADER_CONFLICT"

    # Règle 4 — direction partielle et leaders en conflit
    if direction_consistency == "PARTIAL" and leader_consistency == "CONFLICT":
        return "RELATIONAL_GRAVITY_PARTIAL_DIRECTION_LEADER_CONFLICT"

    # Règle 5 — mixed/unreliable
    if (
        cross_tf_state == "RELATIONAL_GRAVITY_MIXED"
        or dominant_leader == "MIXED"
    ) and direction_consistency != "ALIGNED":
        return "RELATIONAL_GRAVITY_MIXED_TOPLINE_UNRELIABLE"

    # Règle 6 — défaut
    return "RELATIONAL_GRAVITY_MIXED_TOPLINE_UNRELIABLE"




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
        direction_consistency,
        leader_consistency,
        antagonist_consistency,
        topline_reliable,
    ) = _compute_cross_tf_state(slots)

    notes: list[str] = []
    missing = [tf for tf, s in slots.items() if not s.loaded]
    if missing:
        notes.append(f"TF missing: {missing}")

    partial = [tf for tf, s in slots.items() if s.loaded and s.status == "PARTIAL"]
    if partial:
        notes.append(f"TF partial: {partial}")

    if cross_tf_state == "RELATIONAL_GRAVITY_MIXED":
        notes.append("mixed_field: cross-TF relational gravity is mixed; topline leader is not reliable")

    if leader_consistency == "CONFLICT":
        notes.append("leader_conflict: dominant_leader forced to MIXED; topline_reliable set to false")

    if dominant_leader != "MIXED" and dominant_leader in dominant_antagonist.split("/"):
        notes.append("antagonist_guard: dominant_leader removed from dominant_antagonist")
        dominant_antagonist = "/".join(
            [a for a in dominant_antagonist.split("/") if a and a != dominant_leader]
        ) or "NONE"

    topline_state = _compute_topline_state(
        cross_tf_state=cross_tf_state,
        dominant_direction=dominant_direction,
        dominant_leader=dominant_leader,
        direction_consistency=direction_consistency,
        leader_consistency=leader_consistency,
        topline_reliable=topline_reliable,
        slots=slots,
    )

    if topline_reliable:
        summary = (
            f"relational gravity topline reliable: {dominant_direction} "
            f"leader={dominant_leader} antagonist={dominant_antagonist}"
        )
    elif cross_tf_state == "RELATIONAL_GRAVITY_MIXED":
        summary = (
            "mixed field / leader conflict: top-level relational gravity "
            "is unreliable; tf_details remain authoritative"
        )
    elif leader_consistency == "CONFLICT":
        summary = (
            "leader conflict: top-level relational gravity is unreliable; "
            "tf_details remain authoritative"
        )
    else:
        summary = "relational gravity topline unavailable or partial; tf_details remain authoritative"

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
        direction_consistency=direction_consistency,
        leader_consistency=leader_consistency,
        antagonist_consistency=antagonist_consistency,
        topline_reliable=topline_reliable,
        topline_state=topline_state,
        summary=summary,
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
        # ── Guard fields V0.1.2 ──────────────────────────────────
        "direction_consistency": block.direction_consistency,
        "leader_consistency": block.leader_consistency,
        "antagonist_consistency": block.antagonist_consistency,
        "topline_reliable": block.topline_reliable,
        # ── Topline State V0.1.3 ─────────────────────────────────
        "topline_state": block.topline_state,
        # ── Bridge Guard P1.2 ────────────────────────────────────
        "summary": block.summary,
        # ─────────────────────────────────────────────────────────
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
