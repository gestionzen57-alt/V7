"""B9 Terrain Node Builder V0.

Read-only helper that turns enriched B9/T009 moments into terrain nodes.
It does not trade, predict, write DB, emit Telegram, or modify dashboards.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

VERSION = "T0142_B9_TERRAIN_NODE_BUILDER_V0"

FORBIDDEN_TERMS = [
    "BUY", "SELL", "ACHETER", "VENDRE", "LONG", "SHORT",
    "probability of success", "probabilité de succès", "win rate", "take profit", "stop loss",
]

REQUIRED_NODE_FIELDS = [
    "node_id", "date", "time_start", "time_end", "node_role", "origin_zone_id",
    "origin_zone_low", "origin_zone_high", "origin_zone_center",
    "zone_status_before", "zone_status_after", "price_verdict", "scene_role",
    "retest_result", "source_family", "summary_recovery_type", "source_mode",
    "data_visibility", "confidence_cap", "proxy_vs_raw_verdict", "source_quality_state",
    "node_strength_state", "node_memory_relevance", "node_reading_fr", "technical_limits",
]

ACTIVE_REJECT_STATES = {"RAW_UNAVAILABLE", "B6_REJECT_RAW_UNAVAILABLE", "SOURCE_RAW_UNAVAILABLE_REJECTED"}


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip()


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _derive_date(moment: Mapping[str, Any]) -> str:
    date = _safe_str(moment.get("date"))
    if date:
        return date[:10]
    ts = _safe_str(moment.get("time_start") or moment.get("start_time") or moment.get("timestamp"))
    return ts[:10] if len(ts) >= 10 else "UNKNOWN_DATE"


def _stable_id(*parts: Any, prefix: str = "B9NODE") -> str:
    text = "|".join(_safe_str(p) for p in parts)
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:10].upper()
    return f"{prefix}_{digest}"


def _zone_bounds(moment: Mapping[str, Any]) -> Tuple[float, float, float]:
    low_keys = ("zone_low", "origin_zone_low", "b9_zone_low", "raw_zone_low", "price_low", "low", "center_min")
    high_keys = ("zone_high", "origin_zone_high", "b9_zone_high", "raw_zone_high", "price_high", "high", "center_max")
    center_keys = ("zone_center", "origin_zone_center", "b9_zone_center", "center", "center_end", "center_start")
    low = next((_safe_float(moment.get(k), None) for k in low_keys if moment.get(k) not in (None, "")), None)
    high = next((_safe_float(moment.get(k), None) for k in high_keys if moment.get(k) not in (None, "")), None)
    center = next((_safe_float(moment.get(k), None) for k in center_keys if moment.get(k) not in (None, "")), None)
    if center is None:
        center = 0.0
    if low is None and high is None:
        low = high = center
    elif low is None:
        low = min(center, high)
    elif high is None:
        high = max(center, low)
    if low > high:
        low, high = high, low
    if center == 0.0 and (low or high):
        center = (low + high) / 2.0
    return round(low, 5), round(high, 5), round(center, 5)


def _text_blob(moment: Mapping[str, Any]) -> str:
    keys = [
        "label", "label_fr", "moment_type", "scene_role", "b9_scene_role", "b9_scene_role_reading_fr",
        "b9_effort_result_progress_state", "b9_progress_type", "b9_movement_role",
        "retest_result", "retest_judgment_fr", "b9_native_retest_judgment",
        "b9_center_path_shape", "b9_internal_progress_state", "zone_memory_state", "price_verdict",
        "b9_source_quality_gate_state", "raw_texture_role", "reading_fr", "what_happens_fr",
    ]
    return " | ".join(_safe_str(moment.get(k)).upper() for k in keys if _safe_str(moment.get(k)))


def infer_node_role(moment: Mapping[str, Any]) -> str:
    blob = _text_blob(moment)
    retest = _safe_str(moment.get("retest_result") or moment.get("b9_native_retest_judgment")).upper()
    zone_state = _safe_str(moment.get("zone_memory_state") or moment.get("b9_zone_memory_state")).upper()
    scene_role = _safe_str(moment.get("b9_scene_role") or moment.get("scene_role")).upper()
    progress = _safe_str(moment.get("b9_effort_result_progress_state")).upper()

    if any(token in blob for token in ["FAILED_REINTEGRATION", "REINTEGRATION ECHOUEE", "RÉINTÉGRATION ÉCHOUÉE"]):
        return "FAILED_REINTEGRATION_NODE"
    if retest == "RETEST_FAILED" or "RETEST_FAILED" in blob or "RETEST ECHOUE" in blob or "RETEST ÉCHOU" in blob:
        return "RETEST_FAILED_NODE"
    if any(token in blob for token in ["HIGH_REJECTION", "REJET HAUT", "HIGH ZONE REJECT", "PROJECTION_DECAY"]):
        return "HIGH_REJECTION_NODE"
    if any(token in blob for token in ["LOWER_ZONE_DEFENDED", "LOW_ZONE_DEFENDED", "ZONE BASSE DÉFENDUE", "ZONE BASSE DEFENDUE"]):
        return "LOWER_ZONE_DEFENDED_NODE"
    if any(token in blob for token in ["PULLBACK_ABSORBED", "PULLBACK ABSORB", "RECONSTRUCTION"]):
        return "PULLBACK_ABSORBED_NODE"
    if any(token in blob for token in ["SECOND_LEG", "DEUXIEME JAMBE", "DEUXIÈME JAMBE"]):
        return "SECOND_LEG_TRIGGER_NODE"
    if any(token in blob for token in ["EXHAUST", "EPUISEMENT", "ÉPUISEMENT", "CONSUMED", "CONSOMM"]):
        return "HIGH_EXHAUSTION_NODE" if "HIGH" in blob or "HAUT" in blob else "ZONE_CONSUMED_NODE"
    if progress == "CENTER_MIGRATION" or "CENTER_MIGRATION_DOWN" in blob or "MEMORY_SHIFT" in blob:
        return "CENTER_MIGRATION_NODE"
    if progress in {"ABSORPTION_WITHOUT_PROGRESS", "EFFORT_WITHOUT_RESULT"} or "ABSORPTION_SHELF" in blob:
        return "ABSORPTION_SHELF_NODE"
    if "PROGRESSIVE" in blob and "UP" in blob:
        return "PROGRESSIVE_REACTION_NODE"
    if "PROGRESSIVE" in blob and "DOWN" in blob:
        return "PROGRESSIVE_PRESSURE_NODE"
    if zone_state == "ZONE_MEMORY_DEFENDED":
        return "LOWER_ZONE_DEFENDED_NODE"
    if zone_state == "ZONE_MEMORY_REJECTED":
        return "HIGH_REJECTION_NODE" if "HIGH" in blob or "HAUT" in blob else "ZONE_REJECTION_NODE"
    if scene_role:
        return "TERRAIN_NODE_REVIEW_REQUIRED"
    return "TERRAIN_NODE_REVIEW_REQUIRED"


def price_verdict_for_node(node_role: str, moment: Mapping[str, Any]) -> str:
    explicit = _safe_str(moment.get("price_verdict") or moment.get("b9_price_verdict"))
    if explicit:
        return explicit.upper()
    mapping = {
        "FAILED_REINTEGRATION_NODE": "FAILED_REINTEGRATION",
        "RETEST_FAILED_NODE": "REJECTED",
        "HIGH_REJECTION_NODE": "REJECTED",
        "LOWER_ZONE_DEFENDED_NODE": "LOWER_ZONE_DEFENDED",
        "PULLBACK_ABSORBED_NODE": "PULLBACK_ABSORBED",
        "SECOND_LEG_TRIGGER_NODE": "ACCEPTED_AFTER_RETEST",
        "HIGH_EXHAUSTION_NODE": "HIGH_ZONE_EXHAUSTED",
        "ZONE_CONSUMED_NODE": "CONSUMED",
        "CENTER_MIGRATION_NODE": "MEMORY_SHIFTED",
        "ABSORPTION_SHELF_NODE": "PENDING",
        "PROGRESSIVE_REACTION_NODE": "ACCEPTED",
        "PROGRESSIVE_PRESSURE_NODE": "ACCEPTED",
        "ZONE_REJECTION_NODE": "REJECTED",
    }
    return mapping.get(node_role, "PENDING")


def zone_before_after(node_role: str, verdict: str) -> Tuple[str, str]:
    if node_role in {"HIGH_REJECTION_NODE", "RETEST_FAILED_NODE", "FAILED_REINTEGRATION_NODE"}:
        return "ZONE_TESTED", "ZONE_REJECTED"
    if node_role == "LOWER_ZONE_DEFENDED_NODE":
        return "LOW_ZONE_TESTED", "LOW_ZONE_DEFENDED"
    if node_role == "PULLBACK_ABSORBED_NODE":
        return "PULLBACK_TEST", "PULLBACK_ABSORBED"
    if node_role == "SECOND_LEG_TRIGGER_NODE":
        return "RETEST_RESOLVING", "SECOND_LEG_TRIGGERED"
    if node_role in {"CENTER_MIGRATION_NODE", "PROGRESSIVE_REACTION_NODE", "PROGRESSIVE_PRESSURE_NODE"}:
        return "ZONE_WORKED", "MEMORY_SHIFTED"
    if node_role in {"ABSORPTION_SHELF_NODE"}:
        return "ZONE_WORKED", "ZONE_DECISION_PENDING"
    if "CONSUMED" in verdict or "CONSUMED" in node_role:
        return "ZONE_ACTIVE", "ZONE_CONSUMED"
    return "ZONE_UNKNOWN", "ZONE_REVIEW_REQUIRED"


def node_strength_state(moment: Mapping[str, Any], node_role: str) -> str:
    source_quality = _safe_str(moment.get("source_quality_state") or moment.get("b9_source_quality_gate_state")).upper()
    verdict = _safe_str(moment.get("proxy_vs_raw_verdict")).upper()
    confidence_cap = _safe_float(moment.get("confidence_cap"), 0.0)
    if any(_safe_str(moment.get(k)).upper() in ACTIVE_REJECT_STATES for k in ["proxy_vs_raw_verdict", "b9_source_quality_gate_state", "b6_memory_candidate_state"]):
        return "NODE_REJECTED_RAW_UNAVAILABLE"
    if verdict == "CONFIRMED_BY_RAW" or source_quality in {"STRONG", "SOURCE_RAW_CONFIRMED"}:
        return "NODE_STRONG_RAW_CONFIRMED"
    if verdict == "NUANCED_BY_RAW" or "NUANCED" in source_quality:
        return "NODE_USABLE_RAW_NUANCED"
    if confidence_cap and confidence_cap <= 0.35:
        return "NODE_PROXY_LIMITED"
    if source_quality in {"WEAK", "LOW", "SOURCE_QUALITY_WEAK_LIMITED"}:
        return "NODE_LOW_TRUST_REVIEW"
    return "NODE_REVIEW_REQUIRED"


def memory_relevance(node_role: str, strength_state: str) -> str:
    if strength_state == "NODE_REJECTED_RAW_UNAVAILABLE":
        return "NODE_MEMORY_REJECTED"
    if node_role in {"HIGH_REJECTION_NODE", "FAILED_REINTEGRATION_NODE", "LOWER_ZONE_DEFENDED_NODE", "PULLBACK_ABSORBED_NODE", "RETEST_FAILED_NODE", "CENTER_MIGRATION_NODE"}:
        return "NODE_MEMORY_HIGH"
    if node_role in {"ABSORPTION_SHELF_NODE", "PROGRESSIVE_REACTION_NODE", "PROGRESSIVE_PRESSURE_NODE", "SECOND_LEG_TRIGGER_NODE"}:
        return "NODE_MEMORY_MEDIUM"
    return "NODE_MEMORY_REVIEW"


def reading_fr(node_role: str, verdict: str, strength_state: str) -> str:
    labels = {
        "HIGH_REJECTION_NODE": "Node de rejet haut : la zone haute est testée puis refusée par le flux.",
        "FAILED_REINTEGRATION_NODE": "Node de réintégration échouée : le retour dans la zone ne reprend pas le contrôle.",
        "RETEST_FAILED_NODE": "Node de retest échoué : le prix revient juger la zone puis ne confirme pas l'acceptation.",
        "LOWER_ZONE_DEFENDED_NODE": "Node de zone basse défendue : le bas est travaillé sans être cassé proprement.",
        "PULLBACK_ABSORBED_NODE": "Node de pullback absorbé : le retour ne casse pas la provenance de la scène.",
        "SECOND_LEG_TRIGGER_NODE": "Node de déclenchement deuxième jambe : la scène se reconstruit après jugement de zone.",
        "CENTER_MIGRATION_NODE": "Node de migration de mémoire : le centre de gravité se déplace vers une nouvelle zone.",
        "ABSORPTION_SHELF_NODE": "Node de palier d'absorption : beaucoup d'effort, peu de progrès net, zone en décision.",
        "PROGRESSIVE_REACTION_NODE": "Node de réaction progressive : l'effort produit du résultat et déplace la mémoire.",
        "PROGRESSIVE_PRESSURE_NODE": "Node de pression progressive : le flux avance par paliers dans le sens de la pression.",
        "HIGH_EXHAUSTION_NODE": "Node d'épuisement haut : la zone haute devient consommée ou fragile.",
        "ZONE_CONSUMED_NODE": "Node de zone consommée : la mémoire locale perd sa capacité de défense.",
        "ZONE_REJECTION_NODE": "Node de rejet de zone : le test de zone produit un refus lisible.",
    }
    base = labels.get(node_role, "Node terrain à revoir : la scène contient une cristallisation possible mais encore partielle.")
    if strength_state == "NODE_REJECTED_RAW_UNAVAILABLE":
        return base + " Raw indisponible : node exclu de la mémoire active."
    if strength_state == "NODE_PROXY_LIMITED":
        return base + " Lecture proxy limitée : utile pour scène, pas vérité raw."
    return base


def technical_limits(moment: Mapping[str, Any], strength_state: str) -> str:
    limits: List[str] = []
    source_mode = _safe_str(moment.get("source_mode"))
    data_visibility = _safe_str(moment.get("data_visibility"))
    verdict = _safe_str(moment.get("proxy_vs_raw_verdict"))
    if source_mode:
        limits.append(f"source_mode={source_mode}")
    if data_visibility:
        limits.append(f"data_visibility={data_visibility}")
    if verdict:
        limits.append(f"proxy_vs_raw_verdict={verdict}")
    if strength_state == "NODE_PROXY_LIMITED":
        limits.append("lecture proxy : ne pas présenter comme footprint raw")
    if strength_state == "NODE_REJECTED_RAW_UNAVAILABLE":
        limits.append("RAW_UNAVAILABLE : rejet mémoire active")
    if not limits:
        limits.append("limites non renseignées")
    return "; ".join(limits)


def build_nodes(summary: Mapping[str, Any]) -> List[Dict[str, Any]]:
    moments = summary.get("moments") or summary.get("sequence_moments") or summary.get("items") or []
    if not isinstance(moments, list):
        raise ValueError("Summary must contain a list under moments/sequence_moments/items")
    nodes: List[Dict[str, Any]] = []
    for idx, moment in enumerate(moments, start=1):
        if not isinstance(moment, Mapping):
            continue
        date = _derive_date(moment)
        time_start = _safe_str(moment.get("time_start") or moment.get("start_time") or moment.get("timestamp") or f"{date}T00:00:00")
        time_end = _safe_str(moment.get("time_end") or moment.get("end_time") or time_start)
        if any(_safe_str(moment.get(k)).upper() in ACTIVE_REJECT_STATES for k in ["proxy_vs_raw_verdict", "b6_memory_candidate_state", "b9_source_quality_gate_state"]):
            node_role = "RAW_UNAVAILABLE_NODE_REJECTED"
        else:
            node_role = infer_node_role(moment)
        low, high, center = _zone_bounds(moment)
        zone_id = _safe_str(moment.get("zone_id") or moment.get("origin_zone_id") or _stable_id(date, low, high, center, prefix="B9ZONE"))
        verdict = price_verdict_for_node(node_role, moment)
        before, after = zone_before_after(node_role, verdict)
        strength = node_strength_state(moment, node_role)
        relevance = memory_relevance(node_role, strength)
        scene_role = _safe_str(moment.get("b9_scene_role") or moment.get("scene_role") or moment.get("moment_type") or moment.get("label") or moment.get("label_fr") or "SCENE_ROLE_UNKNOWN")
        retest_result = _safe_str(moment.get("retest_result") or moment.get("b9_native_retest_judgment") or "RETEST_NOT_VISIBLE")
        node = {
            "node_id": _stable_id(date, time_start, time_end, zone_id, node_role, idx, prefix="B9NODE"),
            "date": date,
            "time_start": time_start,
            "time_end": time_end,
            "node_role": node_role,
            "origin_zone_id": zone_id,
            "origin_zone_low": low,
            "origin_zone_high": high,
            "origin_zone_center": center,
            "zone_status_before": before,
            "zone_status_after": after,
            "price_verdict": verdict,
            "scene_role": scene_role,
            "retest_result": retest_result,
            "source_family": _safe_str(moment.get("source_family") or moment.get("summary_recovery_type") or "UNKNOWN_SOURCE_FAMILY"),
            "summary_recovery_type": _safe_str(moment.get("summary_recovery_type") or "UNKNOWN_SUMMARY_RECOVERY_TYPE"),
            "source_mode": _safe_str(moment.get("source_mode") or "UNKNOWN_SOURCE_MODE"),
            "data_visibility": _safe_str(moment.get("data_visibility") or "UNKNOWN_DATA_VISIBILITY"),
            "confidence_cap": _safe_str(moment.get("confidence_cap") or ""),
            "proxy_vs_raw_verdict": _safe_str(moment.get("proxy_vs_raw_verdict") or "UNKNOWN_PROXY_RAW_VERDICT"),
            "source_quality_state": _safe_str(moment.get("source_quality_state") or moment.get("b9_source_quality_gate_state") or "UNKNOWN_SOURCE_QUALITY"),
            "node_strength_state": strength,
            "node_memory_relevance": relevance,
            "node_reading_fr": reading_fr(node_role, verdict, strength),
            "technical_limits": technical_limits(moment, strength),
        }
        nodes.append(node)
    return nodes


def summarize_nodes(nodes: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    node_list = list(nodes)
    role_counts: Dict[str, int] = {}
    strength_counts: Dict[str, int] = {}
    relevance_counts: Dict[str, int] = {}
    missing: Dict[str, int] = {}
    forbidden_hits: List[Dict[str, str]] = []
    for node in node_list:
        role_counts[_safe_str(node.get("node_role"), "UNKNOWN")] = role_counts.get(_safe_str(node.get("node_role"), "UNKNOWN"), 0) + 1
        strength_counts[_safe_str(node.get("node_strength_state"), "UNKNOWN")] = strength_counts.get(_safe_str(node.get("node_strength_state"), "UNKNOWN"), 0) + 1
        relevance_counts[_safe_str(node.get("node_memory_relevance"), "UNKNOWN")] = relevance_counts.get(_safe_str(node.get("node_memory_relevance"), "UNKNOWN"), 0) + 1
        for field in REQUIRED_NODE_FIELDS:
            if node.get(field) in (None, ""):
                missing[field] = missing.get(field, 0) + 1
        blob = json.dumps(node, ensure_ascii=False).upper()
        for term in FORBIDDEN_TERMS:
            if term.upper() in blob:
                forbidden_hits.append({"node_id": _safe_str(node.get("node_id")), "term": term})
    return {
        "version": VERSION,
        "node_count": len(node_list),
        "role_counts": role_counts,
        "strength_counts": strength_counts,
        "relevance_counts": relevance_counts,
        "missing_required_field_counts": missing,
        "forbidden_language_hits": forbidden_hits,
        "read_only": True,
        "db_write": False,
        "dashboard": False,
        "telegram": False,
        "buy_sell": False,
        "probability_of_success": False,
    }


def enrich_summary_with_nodes(summary: Mapping[str, Any]) -> Dict[str, Any]:
    out = dict(summary)
    nodes = build_nodes(summary)
    out["b9_terrain_nodes_v0"] = nodes
    out["b9_terrain_node_summary_v0"] = summarize_nodes(nodes)
    return out
