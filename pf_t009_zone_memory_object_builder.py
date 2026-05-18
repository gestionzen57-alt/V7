"""B9 Zone Memory Object Builder V0.

Read-only helper that converts B9/T009 moments into local zone memory objects.
It does not write databases, does not emit trading signals, and does not claim
raw truth from proxy/reconstructed summaries.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

VERSION = "T0141_B9_ZONE_MEMORY_OBJECT_BUILDER_V0"

FORBIDDEN_LANGUAGE = (
    "BUY",
    "SELL",
    "ACHETER",
    "VENDRE",
    "TAKE PROFIT",
    "STOP LOSS",
    "PROBABILITE DE SUCCES",
    "PROBABILITÉ DE SUCCÈS",
    "SUCCESS RATE",
    "WIN RATE",
)

REQUIRED_ZONE_FIELDS = (
    "zone_id",
    "date",
    "first_seen",
    "last_tested",
    "zone_low",
    "zone_high",
    "zone_center",
    "zone_width_pips",
    "test_count",
    "accepted_count",
    "rejected_count",
    "defended_count",
    "consumed_count",
    "pending_count",
    "fresh",
    "consumed",
    "zone_memory_state",
    "dominant_scene_role",
    "source_family",
    "summary_recovery_type",
    "source_mode",
    "data_visibility",
    "confidence_cap",
    "proxy_vs_raw_verdict",
    "source_quality_state",
    "zone_memory_reading_fr",
    "technical_limits",
)


def _first_present(mapping: Mapping[str, Any], keys: Sequence[str], default: Any = None) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value not in (None, "", [], {}):
            return value
    return default


def _to_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    if value in (None, "", "None", "null"):
        return default
    try:
        f = float(value)
        if math.isnan(f):
            return default
        return f
    except (TypeError, ValueError):
        return default


def _pips(a: float, b: float) -> float:
    return round(abs(a - b) * 10000.0, 4)


def _time_key(value: Any) -> str:
    if value in (None, ""):
        return ""
    return str(value)


def _date_from_time(value: str) -> str:
    if not value:
        return "UNKNOWN_DATE"
    return value[:10]


def _normalize_text(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return " ".join(_normalize_text(v) for v in value)
    if isinstance(value, dict):
        return " ".join(f"{k} {_normalize_text(v)}" for k, v in value.items())
    return str(value or "")


def find_forbidden_language(payload: Any) -> List[str]:
    text = _normalize_text(payload).upper()
    return sorted({term for term in FORBIDDEN_LANGUAGE if term in text})


def _extract_moments(summary: Mapping[str, Any]) -> List[Dict[str, Any]]:
    for key in ("moments", "items", "scenes"):
        value = summary.get(key)
        if isinstance(value, list):
            return [dict(v) for v in value if isinstance(v, Mapping)]
    if isinstance(summary.get("summary"), Mapping):
        nested = summary["summary"]
        for key in ("moments", "items", "scenes"):
            value = nested.get(key)
            if isinstance(value, list):
                return [dict(v) for v in value if isinstance(v, Mapping)]
    return []


def _extract_zone_bounds(moment: Mapping[str, Any]) -> Optional[Tuple[float, float]]:
    low = _to_float(_first_present(moment, [
        "zone_low", "zone_min", "b9_zone_low", "price_zone_low", "zone_lower", "low", "center_min", "b9_center_min"
    ]))
    high = _to_float(_first_present(moment, [
        "zone_high", "zone_max", "b9_zone_high", "price_zone_high", "zone_upper", "high", "center_max", "b9_center_max"
    ]))
    if low is None or high is None:
        center = _to_float(_first_present(moment, [
            "zone_center", "center", "center_start", "center_end", "b9_center_start", "b9_center_end", "bid_start", "bid_end"
        ]))
        range_pips = _to_float(_first_present(moment, ["center_range", "center_range_pips", "raw_range_pips", "range_pips"]), 2.0)
        if center is None:
            return None
        half = max((range_pips or 2.0) / 2.0 / 10000.0, 0.00005)
        return (round(center - half, 6), round(center + half, 6))
    if low > high:
        low, high = high, low
    if abs(high - low) < 0.00001:
        low -= 0.00005
        high += 0.00005
    return (round(low, 6), round(high, 6))


def _zone_bucket(low: float, high: float, symbol: str = "GBPUSD") -> str:
    center = (low + high) / 2.0
    # 5-pip bucket to group nearby micro-zones while keeping memory local.
    bucket = round(center / 0.0005) * 0.0005
    return f"{symbol}:{bucket:.4f}"


def _status_from_moment(moment: Mapping[str, Any]) -> str:
    text = _normalize_text({
        "label": _first_present(moment, ["label_fr", "label", "moment_type", "b9_scene_role", "b9_scene_role_fr"]),
        "retest": _first_present(moment, ["retest_result", "b9_native_retest_judgment", "retest_judgment_fr"]),
        "verdict": _first_present(moment, ["price_verdict", "b9_price_verdict", "judgment", "b9_scene_role"]),
        "reading": _first_present(moment, ["reading_fr", "b9_effort_result_progress_reading_fr", "b9_center_path_reading_fr"]),
    }).upper()
    if any(k in text for k in ("FAILED_REINTEGRATION", "REINTEGRATION ECHOUE", "RÉINTÉGRATION ÉCHOU", "REINTEGRATION ECHOUEE")):
        return "REJECTED"
    if any(k in text for k in ("RETEST_FAILED", "REJET", "REJECT", "REFUSE", "REFUS")):
        return "REJECTED"
    if any(k in text for k in ("DEFENDED", "DEFENDUE", "DÉFENDUE", "ZONE BASSE DEFEND", "LOW_ZONE_DEFENDED")):
        return "DEFENDED"
    if any(k in text for k in ("ACCEPTED", "ACCEPTE", "ACCEPTÉ", "ACCEPTATION")):
        return "ACCEPTED"
    if any(k in text for k in ("CONSUMED", "CONSOMM", "HIGH_ZONE_CONSUMED", "ZONE_CONSUMED")):
        return "CONSUMED"
    return "PENDING"


def _scene_role(moment: Mapping[str, Any]) -> str:
    role = _first_present(moment, [
        "b9_scene_role", "scene_role", "b9_effort_result_progress_state", "moment_type", "label", "label_fr"
    ], "SCENE_ROLE_UNKNOWN")
    return str(role).strip() or "SCENE_ROLE_UNKNOWN"


def _state_from_counts(accepted: int, rejected: int, defended: int, consumed_count: int, pending: int) -> str:
    if consumed_count > 0:
        return "ZONE_MEMORY_CONSUMED"
    if rejected > 0 and accepted == 0 and defended == 0:
        return "ZONE_MEMORY_REJECTED"
    if defended > 0:
        return "ZONE_MEMORY_DEFENDED"
    if accepted > 0:
        return "ZONE_MEMORY_ACCEPTED"
    if pending > 0:
        return "ZONE_MEMORY_PENDING"
    return "ZONE_MEMORY_REVIEW_REQUIRED"


def _reading_fr(state: str, zone_center: float, tests: int) -> str:
    center = f"{zone_center:.5f}"
    if state == "ZONE_MEMORY_DEFENDED":
        return f"Zone mémoire autour de {center} défendue au moins une fois ; B9 la conserve comme zone vivante à comparer."
    if state == "ZONE_MEMORY_ACCEPTED":
        return f"Zone mémoire autour de {center} acceptée dans le film ; elle peut servir de repère de scène, sans décision."
    if state == "ZONE_MEMORY_REJECTED":
        return f"Zone mémoire autour de {center} rejetée ou retestée défavorablement ; elle marque un node potentiel de changement de rôle."
    if state == "ZONE_MEMORY_CONSUMED":
        return f"Zone mémoire autour de {center} consommée ; B9 la garde comme trace historique, pas comme zone active dure."
    if state == "ZONE_MEMORY_PENDING":
        return f"Zone mémoire autour de {center} travaillée {tests} fois mais encore en attente de jugement clair."
    return f"Zone autour de {center} à revoir : données partielles ou rôle de scène insuffisamment qualifié."


def _technical_limits(moment_group: Sequence[Mapping[str, Any]]) -> List[str]:
    limits = {
        "zone memory object is derived from B9 summary fields, not from a centralized order book",
        "read-only builder; no DB write",
        "zone memory is a behavioral trace, not an execution instruction",
        "no execution-direction language; no outcome-rate claim",
    }
    for moment in moment_group:
        for key in ("technical_limits", "limits", "b9_source_quality_limits", "b9_effort_result_progress_limits", "b9_center_path_limits"):
            value = moment.get(key)
            if isinstance(value, list):
                limits.update(str(v) for v in value if v)
            elif value:
                limits.add(str(value))
        source_mode = str(moment.get("source_mode", "")).upper()
        data_visibility = str(moment.get("data_visibility", "")).upper()
        if "PROXY" in source_mode or "RECONSTRUCT" in data_visibility:
            limits.add("proxy or reconstructed source: do not harden as raw truth")
        if str(moment.get("proxy_vs_raw_verdict", "")).upper() == "NUANCED_BY_RAW":
            limits.add("NUANCED_BY_RAW remains nuanced; it is not CONFIRMED_BY_RAW")
    return sorted(limits)


def _make_zone_id(date: str, center: float, first_seen: str, bucket: str) -> str:
    raw = f"{date}|{center:.5f}|{first_seen}|{bucket}".encode("utf-8")
    digest = hashlib.sha1(raw).hexdigest().upper()[:10]
    date_part = date.replace("-", "") if date and date != "UNKNOWN_DATE" else "UNKNOWN"
    return f"B9ZM_{date_part}_{center:.5f}_{digest}".replace(".", "P")


def build_zone_memory_objects(summary: Mapping[str, Any]) -> Dict[str, Any]:
    moments = _extract_moments(summary)
    groups: Dict[str, List[Dict[str, Any]]] = {}
    bounds_by_bucket: Dict[str, List[Tuple[float, float]]] = {}
    symbol = str(summary.get("symbol") or summary.get("pair") or "GBPUSD")

    rejected_raw_unavailable = 0
    skipped_no_zone = 0
    for moment in moments:
        verdict = str(moment.get("proxy_vs_raw_verdict", "")).upper()
        state = str(moment.get("b6_memory_candidate_state", "")).upper()
        if verdict == "RAW_UNAVAILABLE" or state == "B6_REJECT_RAW_UNAVAILABLE":
            rejected_raw_unavailable += 1
            continue
        bounds = _extract_zone_bounds(moment)
        if bounds is None:
            skipped_no_zone += 1
            continue
        bucket = _zone_bucket(bounds[0], bounds[1], symbol=symbol)
        groups.setdefault(bucket, []).append(dict(moment))
        bounds_by_bucket.setdefault(bucket, []).append(bounds)

    objects: List[Dict[str, Any]] = []
    all_times = [_time_key(_first_present(m, ["time_start", "start_time", "start"])) for m in moments]
    max_time = max((t for t in all_times if t), default="")

    for bucket, group in sorted(groups.items()):
        bounds_list = bounds_by_bucket[bucket]
        low = round(min(b[0] for b in bounds_list), 6)
        high = round(max(b[1] for b in bounds_list), 6)
        center = round((low + high) / 2.0, 6)
        times_start = [_time_key(_first_present(m, ["time_start", "start_time", "start"])) for m in group]
        times_end = [_time_key(_first_present(m, ["time_end", "end_time", "end"])) for m in group]
        first_seen = min((t for t in times_start if t), default="")
        last_tested = max((t for t in times_end if t), default=max((t for t in times_start if t), default=""))
        date = _date_from_time(first_seen)

        statuses = [_status_from_moment(m) for m in group]
        accepted = statuses.count("ACCEPTED")
        rejected = statuses.count("REJECTED")
        defended = statuses.count("DEFENDED")
        consumed_count = statuses.count("CONSUMED")
        pending = statuses.count("PENDING")
        state = _state_from_counts(accepted, rejected, defended, consumed_count, pending)
        consumed = state == "ZONE_MEMORY_CONSUMED"
        fresh = bool(last_tested and last_tested == max_time and not consumed)

        role_counts: Dict[str, int] = {}
        for m in group:
            role = _scene_role(m)
            role_counts[role] = role_counts.get(role, 0) + 1
        dominant_role = sorted(role_counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] if role_counts else "SCENE_ROLE_UNKNOWN"

        source_family = str(_first_present(group[0], ["source_family", "summary_recovery_type"], "SOURCE_FAMILY_UNKNOWN"))
        summary_recovery_type = str(_first_present(group[0], ["summary_recovery_type"], source_family))
        source_mode = str(_first_present(group[0], ["source_mode"], "SOURCE_MODE_UNKNOWN"))
        data_visibility = str(_first_present(group[0], ["data_visibility"], "DATA_VISIBILITY_UNKNOWN"))
        confidence_cap = _first_present(group[0], ["confidence_cap"], "")
        proxy_vs_raw_verdict = str(_first_present(group[0], ["proxy_vs_raw_verdict"], "PROXY_RAW_VERDICT_UNKNOWN"))
        source_quality_state = str(_first_present(group[0], ["source_quality_state", "b9_source_quality_native_state"], "SOURCE_QUALITY_UNKNOWN"))

        obj = {
            "zone_id": _make_zone_id(date, center, first_seen, bucket),
            "date": date,
            "first_seen": first_seen,
            "last_tested": last_tested,
            "zone_low": low,
            "zone_high": high,
            "zone_center": center,
            "zone_width_pips": _pips(low, high),
            "test_count": len(group),
            "accepted_count": accepted,
            "rejected_count": rejected,
            "defended_count": defended,
            "consumed_count": consumed_count,
            "pending_count": pending,
            "fresh": fresh,
            "consumed": consumed,
            "zone_memory_state": state,
            "dominant_scene_role": dominant_role,
            "source_family": source_family,
            "summary_recovery_type": summary_recovery_type,
            "source_mode": source_mode,
            "data_visibility": data_visibility,
            "confidence_cap": confidence_cap,
            "proxy_vs_raw_verdict": proxy_vs_raw_verdict,
            "source_quality_state": source_quality_state,
            "zone_memory_reading_fr": _reading_fr(state, center, len(group)),
            "technical_limits": _technical_limits(group),
            "source_moment_count": len(group),
            "source_moment_labels": sorted({_scene_role(m) for m in group}),
        }
        objects.append(obj)

    state_counts: Dict[str, int] = {}
    for obj in objects:
        state_counts[obj["zone_memory_state"]] = state_counts.get(obj["zone_memory_state"], 0) + 1

    missing_required: Dict[str, int] = {}
    for field in REQUIRED_ZONE_FIELDS:
        count = sum(1 for obj in objects if obj.get(field) in (None, "", []))
        if count:
            missing_required[field] = count

    output = {
        "version": VERSION,
        "symbol": symbol,
        "moments_input": len(moments),
        "zone_objects": objects,
        "zone_object_count": len(objects),
        "state_counts": state_counts,
        "rejected_raw_unavailable_moments": rejected_raw_unavailable,
        "skipped_no_zone_moments": skipped_no_zone,
        "missing_required_field_counts": missing_required,
        "forbidden_language_hits": find_forbidden_language(objects),
        "read_only": True,
        "db_write": False,
        "dashboard": False,
        "telegram": False,
        "buy_sell": False,
        "probability_of_success": False,
    }
    return output


__all__ = [
    "VERSION",
    "REQUIRED_ZONE_FIELDS",
    "build_zone_memory_objects",
    "find_forbidden_language",
]
