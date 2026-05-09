"""
pf_confluence_gravity.py — PowerFlow V7  V0.2.0
Pont EIE × Relational Gravity × Regime (B1) × Spearman (B5).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

DEFAULT_COCKPIT_PATH  = Path("output/cockpit_agentic_state_v01.json")
DEFAULT_RG_PATHS = {
    1:  Path("output/relational_gravity_m1_v011.json"),
    5:  Path("output/relational_gravity_m5_v011.json"),
    15: Path("output/relational_gravity_m15_v011.json"),
}
DEFAULT_REGIME_PATH   = Path("output/regime_engine_state.json")
DEFAULT_SPEARMAN_PATH = Path("output/spearman_gravity_state.json")


@dataclass
class ConfluenceGravityResult:
    currency: str
    fusion_state: str
    confidence: str
    read_mode: str
    roles_by_tf: dict
    regime: str
    regime_confidence: float
    spearman_context: list
    notes: list


def _load_json(path: Path) -> Optional[dict]:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def _role_for_currency(rg_data: dict, currency: str) -> str:
    if not rg_data:
        return "outside"
    leader = rg_data.get("dominant_leader", "")
    antagonist = rg_data.get("dominant_antagonist", "")
    followers = rg_data.get("followers", [])
    group = rg_data.get("group", [])
    if currency == leader:
        return "leader"
    if currency == antagonist:
        return "antagonist"
    if currency in followers:
        return "follower"
    if currency in group:
        return "group_member"
    return "outside"


def _spearman_for_currency(spearman_data: Optional[dict], currency: str) -> list:
    if not spearman_data:
        return []
    result = []
    for p in spearman_data.get("pairs", []):
        pair_str = p.get("pair", "")
        if currency not in pair_str:
            continue
        direction = p.get("direction", "NEUTRAL")
        tail = p.get("tail_signal", "")
        rho = p.get("spearman_rho", 0.0)
        if abs(rho) >= 0.50 or tail in ("CODEPENDANT_EXTREME", "DIVERGENT_EXTREME"):
            other = pair_str.replace(currency, "").replace("_", "")
            result.append(f"{other}:{direction}(rho={rho:.2f})")
    return result


def compute_confluence_gravity(
    currency: str,
    cockpit_path: Path = DEFAULT_COCKPIT_PATH,
    rg_paths: dict = None,
    regime_path: Path = DEFAULT_REGIME_PATH,
    spearman_path: Path = DEFAULT_SPEARMAN_PATH,
) -> ConfluenceGravityResult:
    rg_paths = rg_paths or DEFAULT_RG_PATHS
    notes = []

    # B1 Regime
    regime_data = _load_json(regime_path)
    regime = "UNKNOWN"
    regime_confidence = 0.0
    if regime_data:
        htf = regime_data.get("htf_context_stack", {})
        regime = htf.get("D") or htf.get("H4") or regime_data.get("regime", "UNKNOWN")
        regime_confidence = regime_data.get("confidence", 0.0)
        notes.append(f"B1_regime={regime}({regime_confidence:.2f})")
    else:
        notes.append("B1_regime=MISSING")

    # B5 Spearman
    spearman_data = _load_json(spearman_path)
    spearman_context = _spearman_for_currency(spearman_data, currency)
    if spearman_context:
        notes.append(f"B5_pairs={len(spearman_context)}")

    # Relational Gravity
    cockpit = _load_json(cockpit_path)
    rg_block = cockpit.get("relational_gravity", {}) if cockpit else {}
    topline_reliable = rg_block.get("topline_reliable", False)
    read_mode = "TOPLINE" if topline_reliable else "TF_DETAILS"
    roles_by_tf = {}

    if topline_reliable:
        role = _role_for_currency(rg_block, currency)
        for tf in [1, 5, 15]:
            roles_by_tf[tf] = role
        notes.append("RG_read=TOPLINE")
    else:
        notes.append("RG_read=TF_DETAILS (topline_reliable=false)")
        for tf, path in rg_paths.items():
            tf_data = _load_json(path)
            roles_by_tf[tf] = _role_for_currency(tf_data, currency) if tf_data else "outside"

    if not rg_block and not any(_load_json(p) for p in rg_paths.values()):
        return ConfluenceGravityResult(
            currency=currency, fusion_state="EIE_NO_RG_DATA", confidence="LOW",
            read_mode="NO_DATA", roles_by_tf={}, regime=regime,
            regime_confidence=regime_confidence, spearman_context=spearman_context, notes=notes,
        )

    role_values = list(roles_by_tf.values())
    total = len(role_values) or 1
    leader_count    = role_values.count("leader")
    follower_count  = role_values.count("follower")
    antagonist_count = role_values.count("antagonist")

    if leader_count / total >= 0.66:
        fusion_state, confidence = "EIE_LEADER_CONFIRMED", "HIGH"
    elif follower_count / total >= 0.66:
        fusion_state, confidence = "EIE_FOLLOWER_CONFIRMED", "MEDIUM"
    elif antagonist_count / total >= 0.5:
        fusion_state, confidence = "EIE_ANTAGONIST", "WATCH"
    elif (leader_count + follower_count) / total >= 0.5:
        fusion_state, confidence = "EIE_WITH_RG_PARTIAL", "WATCH"
    elif all(r == "outside" for r in role_values):
        fusion_state, confidence = "EIE_WITH_RG_OUTSIDE", "LOW"
    else:
        fusion_state, confidence = "EIE_WITH_RG_CONFLICT", "WATCH"

    if regime == "RANGE" and confidence == "HIGH":
        confidence = "MEDIUM"
        notes.append("confidence_downgraded: regime=RANGE")
    if regime == "COMPRESSION" and fusion_state == "EIE_LEADER_CONFIRMED":
        notes.append("COMPRESSION+LEADER: signal_quality=MAX")

    return ConfluenceGravityResult(
        currency=currency, fusion_state=fusion_state, confidence=confidence,
        read_mode=read_mode, roles_by_tf=roles_by_tf, regime=regime,
        regime_confidence=regime_confidence, spearman_context=spearman_context, notes=notes,
    )