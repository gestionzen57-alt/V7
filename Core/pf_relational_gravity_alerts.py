"""
pf_relational_gravity_alerts.py
PowerFlow V6 — Relational Gravity Alert Rules V0.1

Lit le bloc relational_gravity du cockpit state.
Produit des AlertItem prêts à injecter dans behavioral_alert_queue.

READ-ONLY. Pas de DB. Pas de Telegram. Pas de BUY/SELL.
Zéro crash si relational_gravity absent ou malformé.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


# ─────────────────────────────────────────────
# VERSION
# ─────────────────────────────────────────────

RG_ALERTS_VERSION = "0.1"


# ─────────────────────────────────────────────
# THRESHOLDS
# ─────────────────────────────────────────────

SCORE_HOT_THRESHOLD   = 0.85   # ALIGNED + score >= this → HOT
SCORE_WATCH_THRESHOLD = 0.80   # leader + score >= this  → WATCH


# ─────────────────────────────────────────────
# ALERT LEVELS
# ─────────────────────────────────────────────

LEVEL_HOT   = "HOT"
LEVEL_WATCH = "WATCH"
LEVEL_INFO  = "INFO"


# ─────────────────────────────────────────────
# ALERT NAMES
# ─────────────────────────────────────────────

ALERT_ALIGNED              = "RELATIONAL_GRAVITY_ALIGNED_ALERT"
ALERT_LEADER_PULLING       = "LEADER_PULLING_AWAY_ALERT"
ALERT_M1_COUNTERFIELD      = "M1_RELATIONAL_COUNTERFIELD_ALERT"
ALERT_M5_M15_ALIGNMENT     = "M5_M15_RELATIONAL_ALIGNMENT_ALERT"
ALERT_COALITION_ANTAGONIST = "COALITION_VS_ANTAGONIST_EXPANSION_ALERT"
ALERT_MIXED_INFO           = "RELATIONAL_GRAVITY_MIXED_INFO"


# ─────────────────────────────────────────────
# DATA CLASS
# ─────────────────────────────────────────────

@dataclass
class RGAlertItem:
    alert_name: str
    level: str                        # HOT / WATCH / INFO
    cross_tf_state: str
    dominant_direction: str
    dominant_leader: str
    dominant_antagonist: str
    aligned_tfs: list[int]
    counter_tf: Optional[int]
    max_score: float
    reason: str
    interpretation: str
    source: str = "relational_gravity"
    tags: list[str] = field(default_factory=list)


# ─────────────────────────────────────────────
# SAFE EXTRACTOR
# ─────────────────────────────────────────────

def _extract_rg(cockpit_state: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Safe extraction of relational_gravity block. Returns None if absent/malformed."""
    try:
        rg = cockpit_state.get("relational_gravity")
        if not isinstance(rg, dict):
            return None
        # Minimal validity check
        if "cross_tf_state" not in rg:
            return None
        return rg
    except Exception:
        return None


# ─────────────────────────────────────────────
# ALERT RULES
# ─────────────────────────────────────────────

def _rule_aligned(rg: dict) -> Optional[RGAlertItem]:
    """
    RELATIONAL_GRAVITY_ALIGNED_ALERT
    Condition : ALIGNED_M1_M5_M15 + max_score >= SCORE_HOT_THRESHOLD → HOT
                ALIGNED_M1_M5_M15 + max_score < threshold             → WATCH
    """
    if rg.get("cross_tf_state") != "RELATIONAL_GRAVITY_ALIGNED_M1_M5_M15":
        return None

    score    = float(rg.get("max_score", 0.0))
    leader   = rg.get("dominant_leader", "UNKNOWN")
    antag    = rg.get("dominant_antagonist", "NONE")
    direction = rg.get("dominant_direction", "UNKNOWN")
    tfs      = rg.get("aligned_tfs", [])

    level = LEVEL_HOT if score >= SCORE_HOT_THRESHOLD else LEVEL_WATCH

    reason = (
        f"M1/M5/M15 alignés {direction} — "
        f"leader {leader} — antagoniste {antag} — "
        f"score {score:.3f}"
    )

    interpretation = (
        f"Champ gravitationnel complet : M{'/M'.join(str(t) for t in sorted(tfs))} "
        f"convergent {direction}. "
        f"{leader} domine. Antagoniste : {antag}."
    )

    return RGAlertItem(
        alert_name=ALERT_ALIGNED,
        level=level,
        cross_tf_state=rg["cross_tf_state"],
        dominant_direction=direction,
        dominant_leader=leader,
        dominant_antagonist=antag,
        aligned_tfs=tfs,
        counter_tf=rg.get("counter_tf"),
        max_score=score,
        reason=reason,
        interpretation=interpretation,
        tags=["gravity", "aligned", "cross_tf", level.lower()],
    )


def _rule_leader_pulling(rg: dict) -> Optional[RGAlertItem]:
    """
    LEADER_PULLING_AWAY_ALERT
    Condition : dominant_leader non-UNKNOWN + max_score >= SCORE_WATCH_THRESHOLD
    Niveau    : HOT si ALIGNED + score >= HOT_THRESHOLD, sinon WATCH
    """
    leader = rg.get("dominant_leader", "UNKNOWN")
    if leader == "UNKNOWN":
        return None

    score     = float(rg.get("max_score", 0.0))
    if score < SCORE_WATCH_THRESHOLD:
        return None

    cross     = rg.get("cross_tf_state", "")
    direction = rg.get("dominant_direction", "UNKNOWN")
    antag     = rg.get("dominant_antagonist", "NONE")
    tfs       = rg.get("aligned_tfs", [])

    # Check at least one TF has LEADER_PULLING_AWAY in lab_signatures
    has_pulling = any(
        "LEADER_PULLING_AWAY" in tf_data.get("lab_signatures", [])
        for tf_data in rg.get("tf_details", {}).values()
        if isinstance(tf_data, dict)
    )
    if not has_pulling:
        return None

    level = (
        LEVEL_HOT
        if cross == "RELATIONAL_GRAVITY_ALIGNED_M1_M5_M15" and score >= SCORE_HOT_THRESHOLD
        else LEVEL_WATCH
    )

    reason = (
        f"{leader} prend de l'avance ({direction}) — "
        f"score {score:.3f} — antagoniste {antag}"
    )
    interpretation = (
        f"{leader} tire le groupe {direction}. "
        f"Antagoniste : {antag}. "
        f"Attention à la désynchro si les suiveurs ne rattrapent pas."
    )

    return RGAlertItem(
        alert_name=ALERT_LEADER_PULLING,
        level=level,
        cross_tf_state=cross,
        dominant_direction=direction,
        dominant_leader=leader,
        dominant_antagonist=antag,
        aligned_tfs=tfs,
        counter_tf=rg.get("counter_tf"),
        max_score=score,
        reason=reason,
        interpretation=interpretation,
        tags=["gravity", "leader", "pulling_away", level.lower()],
    )


def _rule_m1_counterfield(rg: dict) -> Optional[RGAlertItem]:
    """
    M1_RELATIONAL_COUNTERFIELD_ALERT
    Condition : cross_tf_state == M1_RELATIONAL_COUNTERFIELD
    Niveau    : WATCH (M1 contre M5/M15 = info tactique importante)
    """
    if rg.get("cross_tf_state") != "M1_RELATIONAL_COUNTERFIELD":
        return None

    direction = rg.get("dominant_direction", "UNKNOWN")
    leader    = rg.get("dominant_leader", "UNKNOWN")
    antag     = rg.get("dominant_antagonist", "NONE")
    score     = float(rg.get("max_score", 0.0))
    tfs       = rg.get("aligned_tfs", [])
    counter   = rg.get("counter_tf")

    # Get M1 direction for context
    m1_data   = rg.get("tf_details", {}).get("1", {})
    m1_dir    = m1_data.get("direction", "UNKNOWN") if isinstance(m1_data, dict) else "UNKNOWN"
    m1_leader = m1_data.get("leader", "UNKNOWN") if isinstance(m1_data, dict) else "UNKNOWN"

    reason = (
        f"M1 {m1_dir} ({m1_leader}) contre M5/M15 {direction} ({leader}) — "
        f"score {score:.3f}"
    )
    interpretation = (
        f"M1 en contre-champ gravitationnel. "
        f"Structure M5/M15 : {direction} / leader {leader}. "
        f"M1 : {m1_dir} / leader {m1_leader}. "
        f"Surveiller si M1 s'aligne ou force une correction structurelle."
    )

    return RGAlertItem(
        alert_name=ALERT_M1_COUNTERFIELD,
        level=LEVEL_WATCH,
        cross_tf_state=rg["cross_tf_state"],
        dominant_direction=direction,
        dominant_leader=leader,
        dominant_antagonist=antag,
        aligned_tfs=tfs,
        counter_tf=counter,
        max_score=score,
        reason=reason,
        interpretation=interpretation,
        tags=["gravity", "m1_counter", "tactical", "watch"],
    )


def _rule_m5_m15_alignment(rg: dict) -> Optional[RGAlertItem]:
    """
    M5_M15_RELATIONAL_ALIGNMENT_ALERT
    Condition : cross_tf_state == M5_M15_RELATIONAL_ALIGNMENT
    Niveau    : WATCH si score >= WATCH_THRESHOLD, sinon INFO
    """
    if rg.get("cross_tf_state") != "M5_M15_RELATIONAL_ALIGNMENT":
        return None

    direction = rg.get("dominant_direction", "UNKNOWN")
    leader    = rg.get("dominant_leader", "UNKNOWN")
    antag     = rg.get("dominant_antagonist", "NONE")
    score     = float(rg.get("max_score", 0.0))
    tfs       = rg.get("aligned_tfs", [])

    level = LEVEL_WATCH if score >= SCORE_WATCH_THRESHOLD else LEVEL_INFO

    reason = (
        f"M5/M15 alignés {direction} — leader {leader} — "
        f"M1 absent ou en contre — score {score:.3f}"
    )
    interpretation = (
        f"Structure M5/M15 cohérente {direction}. "
        f"Leader : {leader}. Antagoniste : {antag}. "
        f"M1 non confirmé — attendre alignement M1 pour signal fort."
    )

    return RGAlertItem(
        alert_name=ALERT_M5_M15_ALIGNMENT,
        level=level,
        cross_tf_state=rg["cross_tf_state"],
        dominant_direction=direction,
        dominant_leader=leader,
        dominant_antagonist=antag,
        aligned_tfs=tfs,
        counter_tf=rg.get("counter_tf"),
        max_score=score,
        reason=reason,
        interpretation=interpretation,
        tags=["gravity", "m5_m15", "structural", level.lower()],
    )


def _rule_coalition_antagonist(rg: dict) -> Optional[RGAlertItem]:
    """
    COALITION_VS_ANTAGONIST_EXPANSION_ALERT
    Condition : dominant_antagonist non-NONE + au moins 1 TF a
                COALITION_VS_ANTAGONIST_EXPANSION dans lab_signatures
    Niveau    : INFO (contexte de champ, pas une naissance)
    """
    antag = rg.get("dominant_antagonist", "NONE")
    if not antag or antag == "NONE":
        return None

    # Check at least one TF has the coalition vs antagonist signature
    has_sig = any(
        "COALITION_VS_ANTAGONIST_EXPANSION" in tf_data.get("lab_signatures", [])
        for tf_data in rg.get("tf_details", {}).values()
        if isinstance(tf_data, dict)
    )
    if not has_sig:
        return None

    direction = rg.get("dominant_direction", "UNKNOWN")
    leader    = rg.get("dominant_leader", "UNKNOWN")
    score     = float(rg.get("max_score", 0.0))
    cross     = rg.get("cross_tf_state", "")
    tfs       = rg.get("aligned_tfs", [])

    reason = (
        f"Coalition {direction} (leader {leader}) s'oppose à {antag} — "
        f"score {score:.3f}"
    )
    interpretation = (
        f"Champ bipolaire actif : groupe {direction} vs {antag}. "
        f"Expansion de la distance coalition/antagoniste détectée."
    )

    return RGAlertItem(
        alert_name=ALERT_COALITION_ANTAGONIST,
        level=LEVEL_INFO,
        cross_tf_state=cross,
        dominant_direction=direction,
        dominant_leader=leader,
        dominant_antagonist=antag,
        aligned_tfs=tfs,
        counter_tf=rg.get("counter_tf"),
        max_score=score,
        reason=reason,
        interpretation=interpretation,
        tags=["gravity", "coalition", "antagonist", "bipolar", "info"],
    )


def _rule_mixed_info(rg: dict) -> Optional[RGAlertItem]:
    """
    RELATIONAL_GRAVITY_MIXED_INFO
    Condition : cross_tf_state == RELATIONAL_GRAVITY_MIXED
    Niveau    : INFO (pas de structure gravitationnelle claire)
    """
    if rg.get("cross_tf_state") != "RELATIONAL_GRAVITY_MIXED":
        return None

    score  = float(rg.get("max_score", 0.0))
    tfs    = rg.get("aligned_tfs", [])

    reason = f"Champ gravitationnel mixte — pas de direction dominante claire — score {score:.3f}"
    interpretation = (
        "Aucune convergence gravitationnelle cross-TF. "
        "Devises en désalignement ou champ plat. "
        "Pas de contexte de compression/expansion exploitable."
    )

    return RGAlertItem(
        alert_name=ALERT_MIXED_INFO,
        level=LEVEL_INFO,
        cross_tf_state=rg["cross_tf_state"],
        dominant_direction=rg.get("dominant_direction", "MIXED"),
        dominant_leader=rg.get("dominant_leader", "UNKNOWN"),
        dominant_antagonist=rg.get("dominant_antagonist", "NONE"),
        aligned_tfs=tfs,
        counter_tf=rg.get("counter_tf"),
        max_score=score,
        reason=reason,
        interpretation=interpretation,
        tags=["gravity", "mixed", "no_structure", "info"],
    )


# ─────────────────────────────────────────────
# RULE PIPELINE
# ─────────────────────────────────────────────

_RULES = [
    _rule_aligned,
    _rule_leader_pulling,
    _rule_m1_counterfield,
    _rule_m5_m15_alignment,
    _rule_coalition_antagonist,
    _rule_mixed_info,
]


# ─────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────

def extract_relational_gravity_alerts(
    cockpit_state: dict[str, Any],
) -> list[RGAlertItem]:
    """
    Main entry point for pf_behavioral_alert_mapper.py.

    Reads cockpit_state["relational_gravity"] and returns a list of RGAlertItem.
    Returns [] if block absent, malformed, or no rule fires.
    Never raises. Never writes DB. Never touches Telegram.

    Usage in pf_behavioral_alert_mapper.py:
        from pf_relational_gravity_alerts import (
            extract_relational_gravity_alerts,
            rg_alert_to_dict,
        )
        rg_alerts = extract_relational_gravity_alerts(cockpit_state)
        for a in rg_alerts:
            behavioral_alert_queue.append(rg_alert_to_dict(a))
    """
    rg = _extract_rg(cockpit_state)
    if rg is None:
        return []

    alerts: list[RGAlertItem] = []
    for rule in _RULES:
        try:
            item = rule(rg)
            if item is not None:
                alerts.append(item)
        except Exception:
            # Rule failure never propagates
            pass

    return alerts


# ─────────────────────────────────────────────
# SERIALIZER
# ─────────────────────────────────────────────

def rg_alert_to_dict(alert: RGAlertItem) -> dict:
    """Serialize RGAlertItem to plain dict for behavioral_alert_queue JSON."""
    return {
        "alert_name": alert.alert_name,
        "level": alert.level,
        "source": alert.source,
        "cross_tf_state": alert.cross_tf_state,
        "dominant_direction": alert.dominant_direction,
        "dominant_leader": alert.dominant_leader,
        "dominant_antagonist": alert.dominant_antagonist,
        "aligned_tfs": alert.aligned_tfs,
        "counter_tf": alert.counter_tf,
        "max_score": alert.max_score,
        "reason": alert.reason,
        "interpretation": alert.interpretation,
        "tags": alert.tags,
    }
