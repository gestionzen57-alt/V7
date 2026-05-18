"""T0130 - B9 Center Path Internal Film V0.

Read the internal center path of a B9/T009 moment instead of relying only on
center_start -> center_end. This module is read-only and does not decide.
It enriches summaries with center path metrics, shape, visibility and limits.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

VERSION = "T0130_B9_CENTER_PATH_INTERNAL_FILM_V0"
PIP_SCALE = 10000.0
EPS_PIPS = 0.25

REQUIRED_FIELDS = [
    "b9_center_path_version",
    "b9_center_path_visibility",
    "b9_center_path_points",
    "b9_center_start",
    "b9_center_end",
    "b9_center_min",
    "b9_center_max",
    "b9_center_range_pips",
    "b9_center_net_delta_pips",
    "b9_center_max_favorable_excursion_pips",
    "b9_center_max_adverse_excursion_pips",
    "b9_center_inflexion_count",
    "b9_center_path_shape",
    "b9_internal_progress_state",
    "b9_center_path_reading_fr",
    "b9_center_path_limits",
]

PRESERVED_FIELDS = [
    "time_start",
    "time_end",
    "label_fr",
    "moment_type",
    "source_mode",
    "data_visibility",
    "summary_recovery_type",
    "source_family",
    "proxy_vs_raw_verdict",
    "source_quality_state",
]

FORBIDDEN_LANGUAGE = ["BUY", "SELL", "ACHETER", "VENDRE", "probability of success", "probabilite de succes"]


def _first_present(row: Mapping[str, Any], names: Sequence[str]) -> Any:
    for name in names:
        if name in row and row.get(name) not in (None, "", [], {}):
            return row.get(name)
    return None


def _as_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", "."))
        except ValueError:
            return None
    return None


def _as_number_list(raw: Any) -> List[float]:
    if raw in (None, ""):
        return []
    if isinstance(raw, (int, float, str)):
        v = _as_float(raw)
        return [] if v is None else [v]
    if not isinstance(raw, Iterable):
        return []
    values: List[float] = []
    for item in raw:
        if isinstance(item, Mapping):
            candidate = _first_present(item, ["center", "value", "price", "mid", "center_price", "zone_center"])
            v = _as_float(candidate)
        else:
            v = _as_float(item)
        if v is not None:
            values.append(v)
    return values


def _delta_to_pips(delta: float) -> float:
    # Price deltas around FX spot are normally < 0.05. Existing pips fields are usually > 0.05.
    return round(delta * PIP_SCALE, 6) if abs(delta) <= 0.05 else round(delta, 6)


def _range_to_pips(value_range: float) -> float:
    return _delta_to_pips(value_range)


def _round(value: Optional[float], ndigits: int = 6) -> Optional[float]:
    return None if value is None else round(float(value), ndigits)


def _extract_explicit_path(moment: Mapping[str, Any]) -> Tuple[List[float], str]:
    for field in [
        "b9_center_path",
        "center_path",
        "center_values",
        "center_series",
        "centers",
        "center_path_values",
        "center_history",
    ]:
        path = _as_number_list(moment.get(field))
        if len(path) >= 3:
            return path, "CENTER_PATH_VISIBLE"
    return [], "CENTER_PATH_NOT_VISIBLE"


def _extract_start_end(moment: Mapping[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    start = _as_float(_first_present(moment, ["b9_center_start", "center_start", "center", "zone_center_start"]))
    end = _as_float(_first_present(moment, ["b9_center_end", "center_end", "center", "zone_center_end"]))
    return start, end


def _derive_path(moment: Mapping[str, Any]) -> Tuple[List[float], str, List[str]]:
    path, visibility = _extract_explicit_path(moment)
    if path:
        return path, visibility, ["center path comes from explicit path-like fields"]

    start, end = _extract_start_end(moment)
    cmin = _as_float(_first_present(moment, ["b9_center_min", "center_min", "center_low", "zone_low"]))
    cmax = _as_float(_first_present(moment, ["b9_center_max", "center_max", "center_high", "zone_high"]))

    if start is not None and end is not None and cmin is not None and cmax is not None:
        # Conservative proxy: keep start/end exact and include extremes only for internal excursion diagnostics.
        derived = [start]
        if cmax not in (start, end):
            derived.append(cmax)
        if cmin not in (start, end, cmax):
            derived.append(cmin)
        derived.append(end)
        return derived, "CENTER_PATH_PROXY_EXTREMES", [
            "center path is derived from start/end/extremes, not a native chronological path",
            "internal ordering of min/max may be approximate",
        ]

    if start is not None and end is not None:
        return [start, end], "CENTER_PATH_START_END_ONLY", [
            "only center_start and center_end are visible",
            "internal film is not fully observable",
        ]

    return [], "CENTER_PATH_NOT_VISIBLE", ["center path fields are not visible in this moment"]


def _count_inflexions(path: Sequence[float]) -> int:
    if len(path) < 3:
        return 0
    signs: List[int] = []
    for a, b in zip(path, path[1:]):
        delta_pips = _delta_to_pips(b - a)
        if abs(delta_pips) <= EPS_PIPS:
            continue
        signs.append(1 if delta_pips > 0 else -1)
    if not signs:
        return 0
    return sum(1 for prev, cur in zip(signs, signs[1:]) if cur != prev)


def _excursions(path: Sequence[float], net_delta_pips: float) -> Tuple[float, float]:
    if not path:
        return 0.0, 0.0
    start = path[0]
    cmin = min(path)
    cmax = max(path)
    if net_delta_pips >= 0:
        favorable = _delta_to_pips(cmax - start)
        adverse = abs(_delta_to_pips(cmin - start))
    else:
        favorable = abs(_delta_to_pips(cmin - start))
        adverse = _delta_to_pips(cmax - start)
    return round(max(0.0, favorable), 6), round(max(0.0, adverse), 6)


def _shape(path: Sequence[float], visibility: str) -> Tuple[str, str, str]:
    if visibility == "CENTER_PATH_NOT_VISIBLE" or len(path) < 2:
        return "CENTER_PATH_NOT_VISIBLE", "INTERNAL_PATH_NOT_VISIBLE", "Chemin interne du centre non visible. B9 conserve la limite au lieu d'inventer le film."

    start, end = path[0], path[-1]
    cmin, cmax = min(path), max(path)
    range_pips = abs(_range_to_pips(cmax - cmin))
    net_pips = _delta_to_pips(end - start)
    inflexions = _count_inflexions(path)
    absnet = abs(net_pips)
    ratio = 0.0 if range_pips <= EPS_PIPS else absnet / range_pips
    direction = "UP" if net_pips > EPS_PIPS else "DOWN" if net_pips < -EPS_PIPS else "FLAT"

    if range_pips <= 1.0:
        return "CENTER_LOCKED", "INTERNAL_CENTER_LOCKED", "Centre verrouille: le mouvement interne reste trop serre pour parler de progression propre."

    if visibility == "CENTER_PATH_START_END_ONLY":
        if direction == "FLAT":
            return "TWO_POINT_NO_PROGRESS", "INTERNAL_PATH_LOW_VISIBILITY", "Seulement deux points visibles: B9 voit un centre sans progression nette, mais le film interne reste masque."
        return f"TWO_POINT_DRIFT_{direction}", "INTERNAL_PATH_LOW_VISIBILITY", "Seulement center_start/center_end visibles: derive de tendance possible, film interne non confirme."

    if ratio < 0.25 and range_pips >= 4.0:
        return "ROUND_TRIP_NO_PROGRESS", "INTERNAL_ROUND_TRIP_CAUTION", "Le centre fait du chemin mais revient proche de son point de depart: mouvement interne sans deplacement net de memoire."

    if inflexions >= 2 and ratio < 0.55:
        return "SPIKE_AND_RETRACE", "INTERNAL_REVERSAL_VISIBLE", "Le centre montre une projection puis un retour: B9 detecte un film interne que start/end seuls pourraient masquer."

    if ratio >= 0.75 and inflexions <= 1 and direction in ("UP", "DOWN"):
        return f"STRAIGHT_PROGRESS_{direction}", "INTERNAL_PROGRESS_VISIBLE", "Le centre avance de facon lisible: le film interne confirme une progression directionnelle du centre."

    if ratio >= 0.45 and direction in ("UP", "DOWN"):
        return f"STAIR_STEP_PROGRESS_{direction}", "INTERNAL_STAIR_STEP_PROGRESS", "Le centre avance par paliers: progression interne avec respiration locale."

    if direction == "UP":
        return "CENTER_DRIFT_UP", "INTERNAL_CENTER_DRIFT", "Le centre derive vers le haut, mais le chemin interne reste mixte."
    if direction == "DOWN":
        return "CENTER_DRIFT_DOWN", "INTERNAL_CENTER_DRIFT", "Le centre derive vers le bas, mais le chemin interne reste mixte."
    return "MIXED_CENTER_PATH", "INTERNAL_PATH_MIXED", "Chemin interne mixte: information utile pour contexte, sans conclusion dure."


def enrich_moment_center_path(moment: Mapping[str, Any]) -> Dict[str, Any]:
    enriched: Dict[str, Any] = deepcopy(dict(moment))
    path, visibility, limits = _derive_path(enriched)

    if path:
        start, end = path[0], path[-1]
        cmin, cmax = min(path), max(path)
        net_delta_pips = _delta_to_pips(end - start)
        range_pips = abs(_range_to_pips(cmax - cmin))
        mfe, mae = _excursions(path, net_delta_pips)
        inflexions = _count_inflexions(path)
        shape, progress_state, reading = _shape(path, visibility)
    else:
        start = end = cmin = cmax = None
        net_delta_pips = range_pips = mfe = mae = 0.0
        inflexions = 0
        shape, progress_state, reading = _shape(path, visibility)

    if visibility in {"CENTER_PATH_PROXY_EXTREMES", "CENTER_PATH_START_END_ONLY"}:
        limits.append("center path visibility is limited; do not harden proxy path as raw chronology")
    limits.extend([
        "center path is a scene-reading aid, not a trade decision",
        "no execution-order language",
        "no success-probability language",
    ])

    enriched.update(
        {
            "b9_center_path_version": VERSION,
            "b9_center_path_visibility": visibility,
            "b9_center_path_points": len(path),
            "b9_center_start": _round(start),
            "b9_center_end": _round(end),
            "b9_center_min": _round(cmin),
            "b9_center_max": _round(cmax),
            "b9_center_range_pips": round(range_pips, 6),
            "b9_center_net_delta_pips": round(net_delta_pips, 6),
            "b9_center_max_favorable_excursion_pips": round(mfe, 6),
            "b9_center_max_adverse_excursion_pips": round(mae, 6),
            "b9_center_inflexion_count": inflexions,
            "b9_center_path_shape": shape,
            "b9_internal_progress_state": progress_state,
            "b9_center_path_reading_fr": reading,
            "b9_center_path_limits": limits,
        }
    )
    return enriched


def _moments_container(summary: Any) -> Tuple[List[Mapping[str, Any]], str]:
    if isinstance(summary, list):
        return summary, "list"
    if not isinstance(summary, Mapping):
        return [], "none"
    for key in ("moments", "items", "scenes"):
        value = summary.get(key)
        if isinstance(value, list):
            return value, key
    return [], "none"


def enrich_sequence_summary_center_path(summary: Any) -> Any:
    if isinstance(summary, list):
        return [enrich_moment_center_path(m) for m in summary if isinstance(m, Mapping)]
    if not isinstance(summary, Mapping):
        return summary
    out: Dict[str, Any] = deepcopy(dict(summary))
    moments, key = _moments_container(out)
    if key != "none":
        out[key] = [enrich_moment_center_path(m) for m in moments if isinstance(m, Mapping)]
    metadata = dict(out.get("metadata", {})) if isinstance(out.get("metadata"), Mapping) else {}
    metadata["b9_center_path_internal_film_version"] = VERSION
    metadata["b9_center_path_policy"] = "READ_INTERNAL_CENTER_PATH_NOT_ONLY_START_END"
    out["metadata"] = metadata
    return out


def required_field_coverage(moments: Sequence[Mapping[str, Any]]) -> Dict[str, int]:
    return {field: sum(1 for m in moments if field not in m or m.get(field) in (None, "")) for field in REQUIRED_FIELDS}


def forbidden_language_hits(obj: Any) -> List[str]:
    text = str(obj).upper()
    hits: List[str] = []
    for term in FORBIDDEN_LANGUAGE:
        if term.upper() in text:
            hits.append(term)
    return sorted(set(hits))


def preservation_diff(before: Sequence[Mapping[str, Any]], after: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for idx, (b, a) in enumerate(zip(before, after), start=1):
        for field in PRESERVED_FIELDS:
            if b.get(field) != a.get(field):
                rows.append({"moment_index": idx, "field": field, "before": b.get(field), "after": a.get(field)})
    return rows


__all__ = [
    "VERSION",
    "REQUIRED_FIELDS",
    "PRESERVED_FIELDS",
    "enrich_moment_center_path",
    "enrich_sequence_summary_center_path",
    "required_field_coverage",
    "forbidden_language_hits",
    "preservation_diff",
]
