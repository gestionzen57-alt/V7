"""
PowerFlow V6 - pf_confluence_gravity.py
Version: V0.1.0

Mission:
    Pont entre EIE persistant (confluence élastique-zone)
    et Relational Gravity (structure relationnelle multi-TF).

    Répond à : cette devise EIE est-elle leader, follower,
               antagonist ou hors groupe dans le champ relationnel ?

Doctrine:
    Si topline_reliable = true  → lecture top-level directe.
    Si topline_reliable = false → descente dans tf_details par devise.
    Ne raconte jamais un leader clair quand topline_reliable=false.

Boundary:
    Lit uniquement des JSON runtime.
    N'écrit pas en DB.
    N'importe pas pf_* moteur directement.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ==========================================================================
# PATHS - ajuste si besoin
# ==========================================================================

DEFAULT_BRIDGE_PATH = Path("output/cockpit_agentic_state_v01.json")
DEFAULT_RG_PATHS: Dict[int, Path] = {
    1:  Path("output/relational_gravity_m1_v011.json"),
    5:  Path("output/relational_gravity_m5_v011.json"),
    15: Path("output/relational_gravity_m15_v011.json"),
}

# ==========================================================================
# CONSTANTS
# ==========================================================================

ROLE_LEADER    = "leader"
ROLE_FOLLOWER  = "follower"
ROLE_ANTAGONIST= "antagonist"
ROLE_GROUP     = "group_member"
ROLE_OUTSIDE   = "outside"

FUSION_STATES = {
    # topline fiable
    "EIE_LEADER_CONFIRMED",      # EIE + leader clair + direction fiable
    "EIE_FOLLOWER_CONFIRMED",    # EIE + follower du groupe dominant
    "EIE_ANTAGONIST",            # EIE + antagoniste = compression contre flux
    # topline non fiable
    "EIE_WITH_RG_CONFLICT",      # EIE mais RG conflictuelle
    "EIE_WITH_RG_PARTIAL",       # EIE + RG partielle (1-2 TF alignés)
    "EIE_WITH_RG_OUTSIDE",       # devise EIE hors groupe RG
    # RG non disponible
    "EIE_NO_RG_DATA",            # JSON manquant ou vide
}

CONFIDENCE_MAP = {
    "EIE_LEADER_CONFIRMED":  "HIGH",
    "EIE_FOLLOWER_CONFIRMED":"MEDIUM",
    "EIE_ANTAGONIST":        "WATCH",
    "EIE_WITH_RG_CONFLICT":  "WATCH",
    "EIE_WITH_RG_PARTIAL":   "WATCH",
    "EIE_WITH_RG_OUTSIDE":   "LOW",
    "EIE_NO_RG_DATA":        "LOW",
}


# ==========================================================================
# OUTPUT
# ==========================================================================

@dataclass(frozen=True)
class ConfluenceGravityResult:
    currency:        str
    eie_persist:     int
    fractal_score:   int
    topline_reliable:bool
    read_mode:       str                    # "TOPLINE" | "TF_DETAILS"
    roles_by_tf:     Dict[int, str]         # {1: "leader", 5: "follower", ...}
    dominant_direction: Optional[str]       # "UP" | "DOWN" | "MIXED" | None
    dominant_leader: Optional[str]
    dominant_antagonist: Optional[str]
    fusion_state:    str
    confidence:      str
    note:            str
    aligned_tfs:     List[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "currency":           self.currency,
            "eie_persist":        self.eie_persist,
            "fractal_score":      self.fractal_score,
            "topline_reliable":   self.topline_reliable,
            "read_mode":          self.read_mode,
            "roles_by_tf":        {str(k): v for k, v in self.roles_by_tf.items()},
            "dominant_direction":  self.dominant_direction,
            "dominant_leader":     self.dominant_leader,
            "dominant_antagonist": self.dominant_antagonist,
            "fusion_state":        self.fusion_state,
            "confidence":          self.confidence,
            "note":                self.note,
            "aligned_tfs":         self.aligned_tfs,
        }


# ==========================================================================
# LOADERS
# ==========================================================================

def _load_json(path: Path) -> Optional[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _load_bridge(path: Path) -> Optional[dict]:
    data = _load_json(path)
    if not data:
        return None
    # Peut être cockpit complet ou directement le bloc RG
    rg = data.get("relational_gravity") or data
    return rg if isinstance(rg, dict) else None


def _load_rg_tf(paths: Dict[int, Path]) -> Dict[int, dict]:
    result = {}
    for tf, path in paths.items():
        data = _load_json(path)
        if data:
            result[tf] = data
    return result


# ==========================================================================
# ROLE DETECTION
# ==========================================================================

def _detect_role(currency: str, tf_data: dict) -> str:
    """Retourne le rôle de la devise dans un snapshot RG TF."""
    cur = currency.upper()

    leader = str(tf_data.get("leader", "")).upper()
    if cur == leader:
        return ROLE_LEADER

    antagonist = str(tf_data.get("antagonist", "")).upper()
    # antagonist peut être "CAD/AUD" — vérifier si currency dedans
    if cur in antagonist.replace(",", "/").split("/"):
        return ROLE_ANTAGONIST

    followers = tf_data.get("followers", [])
    if isinstance(followers, list) and cur in [f.upper() for f in followers]:
        return ROLE_FOLLOWER

    group = tf_data.get("group", [])
    if isinstance(group, list) and cur in [g.upper() for g in group]:
        return ROLE_GROUP

    return ROLE_OUTSIDE


def _roles_from_tf_details(currency: str, tf_details: dict) -> Dict[int, str]:
    """Extrait les rôles par TF depuis tf_details du bridge."""
    roles: Dict[int, str] = {}
    for tf_str, tf_data in tf_details.items():
        try:
            tf = int(tf_str)
        except ValueError:
            continue
        if isinstance(tf_data, dict):
            roles[tf] = _detect_role(currency, tf_data)
    return roles


def _roles_from_rg_tfs(currency: str, rg_by_tf: Dict[int, dict]) -> Dict[int, str]:
    """Extrait les rôles par TF depuis les JSON RG bruts."""
    return {tf: _detect_role(currency, data) for tf, data in rg_by_tf.items()}


# ==========================================================================
# FUSION LOGIC
# ==========================================================================

def _compute_fusion(
    currency: str,
    roles: Dict[int, str],
    topline_reliable: bool,
    dominant_direction: Optional[str],
    dominant_leader: Optional[str],
) -> Tuple[str, str]:
    """Retourne (fusion_state, note)."""

    if not roles:
        return "EIE_NO_RG_DATA", "Aucune donnée RG disponible."

    role_values = list(roles.values())
    n_leader    = role_values.count(ROLE_LEADER)
    n_follower  = role_values.count(ROLE_FOLLOWER)
    n_antagonist= role_values.count(ROLE_ANTAGONIST)
    n_group     = role_values.count(ROLE_GROUP)
    n_outside   = role_values.count(ROLE_OUTSIDE)
    n_tfs       = len(roles)

    if topline_reliable:
        if n_leader >= 1:
            return (
                "EIE_LEADER_CONFIRMED",
                f"{currency} leader RG + EIE actif. Direction {dominant_direction}. Signal fort.",
            )
        if n_follower + n_group >= max(1, n_tfs - 1):
            return (
                "EIE_FOLLOWER_CONFIRMED",
                f"{currency} follower/groupe RG. Direction {dominant_direction} "
                f"portée par {dominant_leader}.",
            )
        if n_antagonist >= 1:
            return (
                "EIE_ANTAGONIST",
                f"{currency} antagoniste du flux RG ({dominant_direction}). "
                f"Compression contre le groupe dominant.",
            )

    # topline non fiable — lecture TF_DETAILS
    if n_outside == n_tfs:
        return (
            "EIE_WITH_RG_OUTSIDE",
            f"{currency} hors groupe RG sur tous les TF. EIE isolé.",
        )

    aligned = n_leader + n_follower + n_group
    if aligned >= 2:
        return (
            "EIE_WITH_RG_PARTIAL",
            f"{currency} partiellement aligné RG ({aligned}/{n_tfs} TF). "
            f"Signal partiel — trader vérifie.",
        )

    if n_antagonist >= 1:
        return (
            "EIE_WITH_RG_CONFLICT",
            f"{currency} conflit RG : rôle antagoniste sur {n_antagonist} TF "
            f"mais EIE actif. Champ contradictoire.",
        )

    return (
        "EIE_WITH_RG_CONFLICT",
        f"{currency} rôles RG mixtes ({role_values}). Pas de lecture claire.",
    )


# ==========================================================================
# PUBLIC API
# ==========================================================================

def analyze_confluence_gravity(
    currency: str,
    eie_persist: int,
    fractal_score: int,
    bridge_path: Path = DEFAULT_BRIDGE_PATH,
    rg_paths: Dict[int, Path] = DEFAULT_RG_PATHS,
) -> ConfluenceGravityResult:
    """
    Fusionne l'état EIE (persistance, fractalité)
    avec la structure relationnelle Relational Gravity.
    """
    cur = currency.upper()

    # --- Charger bridge ---
    bridge = _load_bridge(bridge_path)
    rg_by_tf = _load_rg_tf(rg_paths)

    if not bridge and not rg_by_tf:
        return ConfluenceGravityResult(
            currency=cur, eie_persist=eie_persist, fractal_score=fractal_score,
            topline_reliable=False, read_mode="NO_DATA", roles_by_tf={},
            dominant_direction=None, dominant_leader=None, dominant_antagonist=None,
            fusion_state="EIE_NO_RG_DATA", confidence="LOW",
            note="JSON Relational Gravity introuvables.", aligned_tfs=[],
        )

    # --- Bridge disponible ---
    topline_reliable   = bool(bridge.get("topline_reliable", False)) if bridge else False
    dominant_direction = str(bridge.get("dominant_direction", "MIXED")).upper() if bridge else None
    dominant_leader    = str(bridge.get("dominant_leader", "")).upper() if bridge else None
    dominant_antagonist= str(bridge.get("dominant_antagonist", "")).upper() if bridge else None
    aligned_tfs        = bridge.get("aligned_tfs", []) if bridge else []

    # --- Déterminer rôles par TF ---
    if topline_reliable and bridge:
        tf_details = bridge.get("tf_details", {})
        if tf_details:
            roles = _roles_from_tf_details(cur, tf_details)
            read_mode = "TOPLINE"
        else:
            roles = _roles_from_rg_tfs(cur, rg_by_tf)
            read_mode = "TF_DETAILS"
    else:
        # Non fiable → descendre dans les JSON bruts
        roles = _roles_from_rg_tfs(cur, rg_by_tf)
        read_mode = "TF_DETAILS"

    # --- Fusion ---
    fusion_state, note = _compute_fusion(
        cur, roles, topline_reliable, dominant_direction, dominant_leader
    )
    confidence = CONFIDENCE_MAP.get(fusion_state, "WATCH")

    return ConfluenceGravityResult(
        currency=cur,
        eie_persist=eie_persist,
        fractal_score=fractal_score,
        topline_reliable=topline_reliable,
        read_mode=read_mode,
        roles_by_tf=roles,
        dominant_direction=dominant_direction,
        dominant_leader=dominant_leader,
        dominant_antagonist=dominant_antagonist,
        fusion_state=fusion_state,
        confidence=confidence,
        note=note,
        aligned_tfs=aligned_tfs if isinstance(aligned_tfs, list) else [],
    )