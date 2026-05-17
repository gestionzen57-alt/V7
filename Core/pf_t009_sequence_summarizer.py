"""T009 Sequence Summarizer V3.1 / B9.

Read-only transformation layer:
raw T009 battlefield events -> compact human-readable B9 moments.

Scope:
- V0.1: replay/DB validation support through robust summaries.
- V1: why/how narrative fields.
- V2: scene causality fields.
- V3: fractal scene chaptering.

The module does not import engine, UI surface, external alert surface, or database writers.
It only reads JSON files and writes summary artifacts requested by the caller.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

MODULE_NAME = "pf_t009_sequence_summarizer"
VERSION = "V3.1.1"
DEFAULT_PIP_SIZE = 0.0001
DEFAULT_MAX_GAP_SEC = 300
DEFAULT_PRICE_MERGE_PIPS = 5.0

MOMENT_LABELS_FR: Dict[str, str] = {
    "T009_MOMENT_EFFORT_WITHOUT_RESULT": "Effort sans résultat",
    "T009_MOMENT_ABSORPTION_SHELF": "Palier d'absorption / étagère d'équilibre",
    "T009_MOMENT_CENTER_MIGRATION_UP": "Centre de gravité qui monte",
    "T009_MOMENT_CENTER_MIGRATION_DOWN": "Centre de gravité qui descend",
    "T009_MOMENT_PROGRESSIVE_WAVE": "Vague progressive",
    "T009_MOMENT_CORRECTIVE_WAVE": "Vague corrective",
    "T009_MOMENT_BREAKOUT_PENDING_RETEST": "Cassure en attente de jugement",
    "T009_MOMENT_BREAK_RETEST_FAILED": "Retest échoué",
    "T009_MOMENT_RETRACE_DECISION_AREA": "Zone de décision au retracement",
    "T009_MOMENT_FLOW_BREATHING": "Respiration du flux",
    "T009_MOMENT_GENERIC_BATTLEFIELD": "Zone de friction locale",
}

MOMENT_CHAPTERS_FR: Dict[str, str] = {
    "T009_MOMENT_EFFORT_WITHOUT_RESULT": "Décision de zone",
    "T009_MOMENT_ABSORPTION_SHELF": "Construction de shelf",
    "T009_MOMENT_CENTER_MIGRATION_UP": "Migration de centre",
    "T009_MOMENT_CENTER_MIGRATION_DOWN": "Migration de centre",
    "T009_MOMENT_PROGRESSIVE_WAVE": "Mémoire déplacée",
    "T009_MOMENT_CORRECTIVE_WAVE": "Respiration",
    "T009_MOMENT_BREAKOUT_PENDING_RETEST": "Test / retest",
    "T009_MOMENT_BREAK_RETEST_FAILED": "Test / retest",
    "T009_MOMENT_RETRACE_DECISION_AREA": "Décision de zone",
    "T009_MOMENT_FLOW_BREATHING": "Respiration",
    "T009_MOMENT_GENERIC_BATTLEFIELD": "Ouverture / transition",
}

MOMENT_ROLES_FR: Dict[str, str] = {
    "T009_MOMENT_EFFORT_WITHOUT_RESULT": "preuve_de_frein",
    "T009_MOMENT_ABSORPTION_SHELF": "construction_memoire",
    "T009_MOMENT_CENTER_MIGRATION_UP": "deplacement_memoire",
    "T009_MOMENT_CENTER_MIGRATION_DOWN": "deplacement_memoire",
    "T009_MOMENT_PROGRESSIVE_WAVE": "extension_par_paliers",
    "T009_MOMENT_CORRECTIVE_WAVE": "respiration_apres_extension",
    "T009_MOMENT_BREAKOUT_PENDING_RETEST": "jugement_en_attente",
    "T009_MOMENT_BREAK_RETEST_FAILED": "refus_de_retest",
    "T009_MOMENT_RETRACE_DECISION_AREA": "zone_a_juger",
    "T009_MOMENT_FLOW_BREATHING": "pause_structuree",
    "T009_MOMENT_GENERIC_BATTLEFIELD": "transition_locale",
}


@dataclass
class NormalizedEvent:
    timestamp: Optional[str] = None
    event_type: Optional[str] = None
    zone_low: Optional[float] = None
    zone_high: Optional[float] = None
    zone_center: Optional[float] = None
    battle_score: Optional[float] = None
    absorption_score: Optional[float] = None
    compression_score: Optional[float] = None
    dwell_score: Optional[float] = None
    failed_displacement_score: Optional[float] = None
    pressure_score: Optional[float] = None
    activity_score: Optional[float] = None
    signed_delta: Optional[float] = None
    delta_imbalance: Optional[float] = None
    flip_rate: Optional[float] = None
    price_range_pips: Optional[float] = None
    source_mode: Optional[str] = None
    data_visibility: Optional[str] = None
    confidence_cap: Optional[float] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Moment:
    moment_id: str
    moment_type: str
    label_fr: str
    time_start: Optional[str]
    time_end: Optional[str]
    zone_low: Optional[float]
    zone_high: Optional[float]
    center_start: Optional[float]
    center_end: Optional[float]
    center_min: Optional[float]
    center_max: Optional[float]
    center_delta_pips: float
    center_range_pips: float
    center_path: List[float]
    max_favorable_excursion_pips: float
    max_adverse_excursion_pips: float
    migration_direction: str
    event_count: int
    avg_absorption_score: Optional[float]
    avg_battle_score: Optional[float]
    avg_compression_score: Optional[float]
    avg_dwell_score: Optional[float]
    avg_failed_displacement_score: Optional[float]
    avg_pressure_score: Optional[float]
    source_mode: Optional[str]
    data_visibility: Optional[str]
    confidence_cap: Optional[float]
    reading_fr: str
    why_it_matters_fr: str
    how_detected_fr: str
    evidence_fr: List[str]
    limits_fr: List[str]
    source_profile: Dict[str, Any]
    effort_role: str
    retest_status: str
    memory_state: str
    zone_memory: Dict[str, Any]
    # V1 why/how narrative fields.
    what_happens_fr: str
    how_it_happened_fr: str
    mechanism_fr: str
    proof_summary_fr: str
    # V2 scene causality fields.
    previous_context_fr: str
    cause_fr: str
    reaction_fr: str
    consequence_fr: str
    memory_shift_fr: str
    retest_role_fr: str
    # V3 fractal scene fields.
    scene_id: str
    scene_role: str
    parent_scene: Dict[str, Any]
    child_moments: List[str]
    session_chapter: str
    fractal_reading_fr: str


def load_json(path: str | Path, default: Any = None) -> Any:
    """Load JSON from path. Missing or empty files return default.

    UTF-8 BOM is accepted because Windows/PowerShell tooling can produce it.
    """
    p = Path(path)
    if default is None:
        default = {}
    if not p.exists():
        return default
    text = p.read_text(encoding="utf-8-sig").strip()
    if not text:
        return default
    return json.loads(text)


def load_state(path: str | Path) -> Dict[str, Any]:
    data = load_json(path, default={})
    return data if isinstance(data, dict) else {}


def load_events(path: str | Path) -> List[Dict[str, Any]]:
    data = load_json(path, default=[])
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ("events", "battlefield_events", "t009_events", "items", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        # A single event-shaped dict is accepted.
        if any(k in data for k in ("event_type", "type", "timestamp", "ts_utc", "zone")):
            return [data]
    return []


def _first_present(data: Dict[str, Any], paths: Sequence[str]) -> Any:
    return _nested_get(data, *paths)


def _deep_find_key(data: Any, key: str) -> Any:
    """Find first key occurrence in nested replay reports.

    Replay reports may wrap shifted/original start fields under window, replay,
    metadata, sequence, or custom payloads. V3.1.1 accepts those shapes without
    requiring the caller to flatten the report.
    """
    if isinstance(data, dict):
        if key in data:
            return data[key]
        for value in data.values():
            found = _deep_find_key(value, key)
            if found is not None:
                return found
    elif isinstance(data, list):
        for item in data:
            found = _deep_find_key(item, key)
            if found is not None:
                return found
    return None


def _build_time_remap(replay_report: Optional[Dict[str, Any]]) -> Optional[Tuple[datetime, datetime]]:
    """Return (shifted_start, original_start) for replay timestamp remapping."""
    if not isinstance(replay_report, dict) or not replay_report:
        return None
    shifted = _nested_get(
        replay_report,
        "shifted_start_utc",
        "replay.shifted_start_utc",
        "time_remap.shifted_start_utc",
        "metadata.shifted_start_utc",
        "sequence.shifted_start_utc",
        "window.shifted_start_utc",
    )
    original = _nested_get(
        replay_report,
        "original_start_utc",
        "replay.original_start_utc",
        "time_remap.original_start_utc",
        "metadata.original_start_utc",
        "sequence.original_start_utc",
        "window.original_start_utc",
    )
    if shifted is None:
        shifted = _deep_find_key(replay_report, "shifted_start_utc")
    if original is None:
        original = _deep_find_key(replay_report, "original_start_utc")
    shifted_dt = _parse_time(shifted)
    original_dt = _parse_time(original)
    if shifted_dt is None or original_dt is None:
        return None
    return shifted_dt, original_dt


def _apply_time_remap(dt: Optional[datetime], time_remap: Optional[Tuple[datetime, datetime]]) -> Optional[datetime]:
    if dt is None or time_remap is None:
        return dt
    shifted_start, original_start = time_remap
    return original_start + (dt - shifted_start)


def _nested_get(data: Dict[str, Any], *paths: str) -> Any:
    for path in paths:
        current: Any = data
        found = True
        for part in path.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                found = False
                break
        if found:
            return current
    return None


def _to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_time(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        # Accept epoch seconds or milliseconds.
        numeric = float(value)
        if numeric > 10_000_000_000:
            numeric /= 1000.0
        return datetime.fromtimestamp(numeric, tz=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    for candidate in (text, text.replace(" ", "T")):
        try:
            dt = datetime.fromisoformat(candidate)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue
    return None


def _iso_utc(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _avg(values: Iterable[Optional[float]]) -> Optional[float]:
    nums = [v for v in values if v is not None]
    if not nums:
        return None
    return sum(nums) / len(nums)


def _round_or_none(value: Optional[float], digits: int = 6) -> Optional[float]:
    if value is None:
        return None
    return round(value, digits)


def _dominant(values: Iterable[Optional[str]]) -> Optional[str]:
    clean = [str(v) for v in values if v]
    if not clean:
        return None
    return Counter(clean).most_common(1)[0][0]


def normalize_event(
    event: Dict[str, Any],
    state_defaults: Optional[Dict[str, Any]] = None,
    time_remap: Optional[Tuple[datetime, datetime]] = None,
) -> NormalizedEvent:
    """Normalize one event while tolerating schema variations."""
    state_defaults = state_defaults or {}
    zone_low = _to_float(_nested_get(event, "zone.low", "zone_low", "bucket.zone_low", "price_zone.low"))
    zone_high = _to_float(_nested_get(event, "zone.high", "zone_high", "bucket.zone_high", "price_zone.high"))
    zone_center = _to_float(_nested_get(event, "zone.center", "zone_center", "bucket.zone_center", "price_zone.center"))
    if zone_center is None and zone_low is not None and zone_high is not None:
        zone_center = (zone_low + zone_high) / 2.0

    scores = event.get("scores") if isinstance(event.get("scores"), dict) else {}
    components = scores.get("components") if isinstance(scores.get("components"), dict) else {}
    features = event.get("features") if isinstance(event.get("features"), dict) else {}

    source_mode = _nested_get(event, "source_mode", "source.source_mode")
    if source_mode is None:
        source_mode = _nested_get(state_defaults, "source_mode", "source.source_mode", "source.mode")

    data_visibility = _nested_get(event, "data_visibility", "source.data_visibility")
    if data_visibility is None:
        data_visibility = _nested_get(state_defaults, "data_visibility", "source.data_visibility")

    confidence_cap = _to_float(_nested_get(event, "confidence_cap", "source.confidence_cap"))
    if confidence_cap is None:
        confidence_cap = _to_float(_nested_get(state_defaults, "confidence_cap", "source.confidence_cap"))

    # Historical event time: prefer original raw evidence time over replay/run timestamp.
    raw_ts_value = _nested_get(
        event,
        "evidence.L1_raw.first_ts_utc",
        "evidence.l1_raw.first_ts_utc",
        "evidence.L1_raw.ts_utc",
        "evidence.l1_raw.ts_utc",
        "evidence.L1_raw.timestamp",
        "evidence.l1_raw.timestamp",
    )
    ts_value = raw_ts_value if raw_ts_value is not None else _nested_get(event, "ts_utc", "timestamp", "time", "created_at", "bucket.timestamp")
    dt = _parse_time(ts_value)

    return NormalizedEvent(
        timestamp=_iso_utc(dt),
        event_type=str(_nested_get(event, "event_type", "type", "name") or "UNKNOWN"),
        zone_low=zone_low,
        zone_high=zone_high,
        zone_center=zone_center,
        battle_score=_to_float(_nested_get(event, "scores.battle_score", "battle_score") or scores.get("battle_score")),
        absorption_score=_to_float(_nested_get(event, "scores.absorption_score", "absorption_score") or scores.get("absorption_score")),
        compression_score=_to_float(_nested_get(event, "scores.components.compression_score", "compression_score") or components.get("compression_score")),
        dwell_score=_to_float(_nested_get(event, "scores.components.dwell_score", "dwell_score") or components.get("dwell_score")),
        failed_displacement_score=_to_float(_nested_get(event, "scores.components.failed_displacement_score", "failed_displacement_score") or components.get("failed_displacement_score")),
        pressure_score=_to_float(_nested_get(event, "scores.components.pressure_score", "pressure_score") or components.get("pressure_score")),
        activity_score=_to_float(_nested_get(event, "scores.components.activity_score", "activity_score") or components.get("activity_score")),
        signed_delta=_to_float(_nested_get(event, "features.signed_delta", "signed_delta") or features.get("signed_delta")),
        delta_imbalance=_to_float(_nested_get(event, "features.delta_imbalance", "delta_imbalance") or features.get("delta_imbalance")),
        flip_rate=_to_float(_nested_get(event, "features.flip_rate", "flip_rate") or features.get("flip_rate")),
        price_range_pips=_to_float(_nested_get(event, "features.price_range_pips", "price_range_pips") or features.get("price_range_pips")),
        source_mode=str(source_mode) if source_mode is not None else None,
        data_visibility=str(data_visibility) if data_visibility is not None else None,
        confidence_cap=confidence_cap,
        raw=event,
    )


def normalize_events(
    events: Sequence[Dict[str, Any]],
    state: Optional[Dict[str, Any]] = None,
    replay_report: Optional[Dict[str, Any]] = None,
) -> List[NormalizedEvent]:
    time_remap = _build_time_remap(replay_report)
    normalized = [normalize_event(e, state_defaults=state, time_remap=time_remap) for e in events]
    normalized.sort(key=lambda e: _parse_time(e.timestamp) or datetime.min.replace(tzinfo=timezone.utc))
    return normalized


def group_events(
    events: Sequence[NormalizedEvent],
    max_gap_sec: int = DEFAULT_MAX_GAP_SEC,
    price_merge_pips: float = DEFAULT_PRICE_MERGE_PIPS,
    pip_size: float = DEFAULT_PIP_SIZE,
) -> List[List[NormalizedEvent]]:
    """Group consecutive events by time gap and center distance."""
    groups: List[List[NormalizedEvent]] = []
    current: List[NormalizedEvent] = []
    max_price_delta = price_merge_pips * pip_size

    for event in events:
        if not current:
            current = [event]
            continue

        prev = current[-1]
        prev_dt = _parse_time(prev.timestamp)
        dt = _parse_time(event.timestamp)
        time_break = False
        if prev_dt is not None and dt is not None:
            time_break = (dt - prev_dt).total_seconds() > max_gap_sec

        price_break = False
        if prev.zone_center is not None and event.zone_center is not None:
            price_break = abs(event.zone_center - prev.zone_center) > max_price_delta

        if time_break or price_break:
            groups.append(current)
            current = [event]
        else:
            current.append(event)

    if current:
        groups.append(current)
    return groups


def _split_group_on_center_inflexion(
    group: Sequence[NormalizedEvent],
    pip_size: float = DEFAULT_PIP_SIZE,
    min_leg_events: int = 2,
    inflexion_pips: float = 4.0,
    retrace_pips: float = 1.5,
) -> List[List[NormalizedEvent]]:
    """Split one large group when the center path makes a meaningful turn.

    V0 was endpoint-driven. B9 V0.1 reads the path of the center inside the
    group, so a progression followed by retrace is no longer collapsed into one
    false effort-without-result moment.
    """
    group = list(group)
    if len(group) < (min_leg_events * 2):
        return [group]
    centers = [event.zone_center for event in group]
    if any(center is None for center in centers):
        return [group]
    values = [float(center) for center in centers if center is not None]
    start = values[0]
    end = values[-1]
    max_idx = max(range(len(values)), key=values.__getitem__)
    min_idx = min(range(len(values)), key=values.__getitem__)
    center_range_pips = (max(values) - min(values)) / pip_size

    up_excursion = (values[max_idx] - start) / pip_size
    up_retrace = (values[max_idx] - end) / pip_size
    down_excursion = (start - values[min_idx]) / pip_size
    down_retrace = (end - values[min_idx]) / pip_size

    candidates: List[Tuple[float, int]] = []
    if (
        up_excursion >= inflexion_pips
        and up_retrace >= retrace_pips
        and max_idx + 1 >= min_leg_events
        and len(values) - (max_idx + 1) >= min_leg_events
    ):
        candidates.append((up_excursion + up_retrace, max_idx + 1))
    if (
        down_excursion >= inflexion_pips
        and down_retrace >= retrace_pips
        and min_idx + 1 >= min_leg_events
        and len(values) - (min_idx + 1) >= min_leg_events
    ):
        candidates.append((down_excursion + down_retrace, min_idx + 1))

    # V3.1: also split multi-turn paths even when the final endpoint makes a
    # new extreme. London 11:00-12:00 showed migration -> partial reaction ->
    # renewed pressure; endpoint-only logic still fused that into one moment.
    signed_steps: List[Tuple[int, int, float]] = []
    for i in range(1, len(values)):
        step_pips = (values[i] - values[i - 1]) / pip_size
        if abs(step_pips) >= retrace_pips:
            signed_steps.append((i, 1 if step_pips > 0 else -1, abs(step_pips)))
    previous_sign: Optional[int] = None
    for idx, sign, magnitude in signed_steps:
        if previous_sign is not None and sign != previous_sign:
            split_at = idx
            if split_at >= min_leg_events and len(values) - split_at >= min_leg_events and center_range_pips >= inflexion_pips:
                candidates.append((center_range_pips + magnitude, split_at))
                break
        previous_sign = sign

    if not candidates:
        return [group]
    _, split_at = max(candidates, key=lambda item: item[0])
    left = group[:split_at]
    right = group[split_at:]
    if not left or not right:
        return [group]
    return [left] + _split_group_on_center_inflexion(
        right,
        pip_size=pip_size,
        min_leg_events=min_leg_events,
        inflexion_pips=inflexion_pips,
        retrace_pips=retrace_pips,
    )


def split_groups_on_center_inflexion(groups: Sequence[Sequence[NormalizedEvent]], pip_size: float = DEFAULT_PIP_SIZE) -> List[List[NormalizedEvent]]:
    split: List[List[NormalizedEvent]] = []
    for group in groups:
        split.extend(_split_group_on_center_inflexion(group, pip_size=pip_size))
    return split


def _migration_direction(delta_pips: float) -> str:
    if delta_pips >= 2.0:
        return "UP"
    if delta_pips <= -2.0:
        return "DOWN"
    return "STABLE"


def _source_limits(source_mode: Optional[str], data_visibility: Optional[str], confidence_cap: Optional[float]) -> List[str]:
    limits: List[str] = []
    if source_mode:
        limits.append(source_mode)
        if source_mode == "M1_BAR_PROXY":
            limits.append("M1_BAR_PROXY : lecture reconstruite, pas footprint raw tick complet")
    if data_visibility:
        limits.append(data_visibility)
        if data_visibility == "RECONSTRUCTED":
            limits.append("RECONSTRUCTED : microfilm approxime")
    if confidence_cap is not None:
        limits.append(f"confidence_cap={confidence_cap}")
    limits.append("delta proxy : pression deduite, delta agressif reel non garanti")
    # Deduplicate while preserving order.
    seen = set()
    result: List[str] = []
    for item in limits:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result




def _source_profile(source_mode: Optional[str], data_visibility: Optional[str], confidence_cap: Optional[float]) -> Dict[str, Any]:
    """Return mandatory source profile for source-aware B9 language."""
    source_mode = source_mode or "UNKNOWN"
    data_visibility = data_visibility or "UNKNOWN"
    cautious = source_mode == "M1_BAR_PROXY" or data_visibility == "RECONSTRUCTED"
    if cautious:
        quality = "PROXY_CAUTION"
        language = "Lecture reconstruite M1_BAR_PROXY : utile pour scène, centre et effort/résultat ; pas un footprint raw tick complet."
    elif source_mode in {"ONTICK_RAW", "HISTORICAL_RAW"}:
        quality = "RAW_AVAILABLE"
        language = "Lecture raw tick disponible : le microfilm est plus précis, mais B9 reste une lecture de situation."
    else:
        quality = "UNKNOWN_SOURCE"
        language = "Source incomplète : B9 conserve la lecture mais limite la force de qualification."
    return {
        "source_mode": source_mode,
        "data_visibility": data_visibility,
        "confidence_cap": confidence_cap,
        "quality": quality,
        "language_fr": language,
        "limitations": _source_limits(source_mode, data_visibility, confidence_cap),
    }


def _classify_effort_role(moment_type: str, metrics: Dict[str, Any]) -> str:
    center_range = metrics.get("center_range_pips") or 0.0
    delta = metrics.get("center_delta_pips") or 0.0
    favorable = metrics.get("max_favorable_excursion_pips") or 0.0
    adverse = metrics.get("max_adverse_excursion_pips") or 0.0
    absorption = metrics.get("avg_absorption_score") or 0.0
    failed = metrics.get("avg_failed_displacement_score") or 0.0
    if moment_type == "T009_MOMENT_PROGRESSIVE_WAVE" or (abs(delta) >= 4.0 and favorable >= 4.0):
        return "FUEL"
    if absorption >= 0.70 and failed >= 0.65 and center_range < 4.0:
        return "ABSORPTION"
    if moment_type in {"T009_MOMENT_ABSORPTION_SHELF", "T009_MOMENT_RETRACE_DECISION_AREA"}:
        return "BRAKE"
    if center_range >= 6.0 and favorable >= 4.0 and adverse >= 1.5:
        return "MIXED_PATH"
    return "LOCAL_TRACE"


def _infer_retest_status(moment_type: str, metrics: Dict[str, Any], previous_metrics: Optional[Dict[str, Any]]) -> str:
    if moment_type == "T009_MOMENT_BREAK_RETEST_FAILED":
        return "FAILED"
    if moment_type == "T009_MOMENT_BREAKOUT_PENDING_RETEST":
        return "PENDING"
    if previous_metrics and _zone_overlap(metrics, previous_metrics):
        if moment_type in {"T009_MOMENT_PROGRESSIVE_WAVE", "T009_MOMENT_CENTER_MIGRATION_UP", "T009_MOMENT_CENTER_MIGRATION_DOWN"}:
            return "ACCEPTED"
        return "ACTIVE_RETEST"
    if moment_type == "T009_MOMENT_RETRACE_DECISION_AREA":
        return "PENDING"
    return "NOT_ISOLATED"


def _infer_memory_state(moment_type: str, metrics: Dict[str, Any], retest_status: str) -> str:
    direction = metrics.get("migration_direction")
    if moment_type == "T009_MOMENT_ABSORPTION_SHELF":
        return "STABLE_MEMORY"
    if direction == "UP":
        return "MEMORY_SHIFT_UP"
    if direction == "DOWN":
        return "MEMORY_SHIFT_DOWN"
    if retest_status == "FAILED":
        return "MEMORY_REJECTED"
    if retest_status == "PENDING":
        return "MEMORY_PENDING_JUDGMENT"
    return "LOCAL_MEMORY_ACTIVE"


def _build_zone_memory(metrics: Dict[str, Any], memory_state: str) -> Dict[str, Any]:
    return {
        "zone_low": _round_or_none(metrics.get("zone_low"), 6),
        "zone_high": _round_or_none(metrics.get("zone_high"), 6),
        "zone_center_start": _round_or_none(metrics.get("center_start"), 6),
        "zone_center_end": _round_or_none(metrics.get("center_end"), 6),
        "first_seen": metrics.get("time_start"),
        "last_seen": metrics.get("time_end"),
        "last_tested": metrics.get("time_end"),
        "state": memory_state,
        "event_count": metrics.get("event_count", 0),
        "source_mode": metrics.get("source_mode"),
        "data_visibility": metrics.get("data_visibility"),
        "confidence_cap": _round_or_none(metrics.get("confidence_cap"), 4),
    }


def _metrics_for_group(group: Sequence[NormalizedEvent], pip_size: float = DEFAULT_PIP_SIZE) -> Dict[str, Any]:
    centers = [e.zone_center for e in group if e.zone_center is not None]
    center_path = [round(float(e.zone_center), 6) for e in group if e.zone_center is not None]
    lows = [e.zone_low for e in group if e.zone_low is not None]
    highs = [e.zone_high for e in group if e.zone_high is not None]
    center_start = centers[0] if centers else None
    center_end = centers[-1] if centers else None
    center_delta_pips = 0.0
    if center_start is not None and center_end is not None:
        center_delta_pips = (center_end - center_start) / pip_size
    center_min = min(centers) if centers else None
    center_max = max(centers) if centers else None
    center_range_pips = 0.0
    if centers and center_min is not None and center_max is not None:
        center_range_pips = (center_max - center_min) / pip_size

    max_favorable_excursion_pips = 0.0
    max_adverse_excursion_pips = 0.0
    up_excursion_pips = 0.0
    down_excursion_pips = 0.0
    if center_start is not None and center_min is not None and center_max is not None:
        up_from_start = (center_max - center_start) / pip_size
        down_from_start = (center_start - center_min) / pip_size
        up_excursion_pips = max(0.0, up_from_start)
        down_excursion_pips = max(0.0, down_from_start)
        if center_delta_pips > 0:
            max_favorable_excursion_pips = max(0.0, up_from_start)
            max_adverse_excursion_pips = max(0.0, down_from_start)
        elif center_delta_pips < 0:
            max_favorable_excursion_pips = max(0.0, down_from_start)
            max_adverse_excursion_pips = max(0.0, up_from_start)
        else:
            max_favorable_excursion_pips = max(0.0, up_from_start, down_from_start)
            max_adverse_excursion_pips = min(max(0.0, up_from_start), max(0.0, down_from_start))

    confidence_values = [e.confidence_cap for e in group if e.confidence_cap is not None]
    return {
        "time_start": group[0].timestamp,
        "time_end": group[-1].timestamp,
        "zone_low": min(lows) if lows else None,
        "zone_high": max(highs) if highs else None,
        "center_start": center_start,
        "center_end": center_end,
        "center_min": center_min,
        "center_max": center_max,
        "center_delta_pips": center_delta_pips,
        "center_range_pips": center_range_pips,
        "center_path": center_path,
        "max_favorable_excursion_pips": max_favorable_excursion_pips,
        "max_adverse_excursion_pips": max_adverse_excursion_pips,
        "up_excursion_pips": up_excursion_pips,
        "down_excursion_pips": down_excursion_pips,
        "migration_direction": _migration_direction(center_delta_pips),
        "event_count": len(group),
        "avg_absorption_score": _avg(e.absorption_score for e in group),
        "avg_battle_score": _avg(e.battle_score for e in group),
        "avg_compression_score": _avg(e.compression_score for e in group),
        "avg_dwell_score": _avg(e.dwell_score for e in group),
        "avg_failed_displacement_score": _avg(e.failed_displacement_score for e in group),
        "avg_pressure_score": _avg(e.pressure_score for e in group),
        "source_mode": _dominant(e.source_mode for e in group),
        "data_visibility": _dominant(e.data_visibility for e in group),
        "confidence_cap": min(confidence_values) if confidence_values else None,
    }


def classify_group(metrics: Dict[str, Any], previous_metrics: Optional[Dict[str, Any]] = None) -> str:
    """Classify one group with readable V0/V1/V2/V3-compatible heuristics."""
    event_count = metrics["event_count"]
    delta = metrics["center_delta_pips"]
    center_range = metrics["center_range_pips"]
    absorption = metrics.get("avg_absorption_score") or 0.0
    compression = metrics.get("avg_compression_score") or 0.0
    dwell = metrics.get("avg_dwell_score") or 0.0
    failed = metrics.get("avg_failed_displacement_score") or 0.0
    pressure = metrics.get("avg_pressure_score") or 0.0
    favorable_excursion = metrics.get("max_favorable_excursion_pips") or 0.0
    up_excursion = metrics.get("up_excursion_pips") or 0.0

    if delta <= -4.0 and event_count >= 4:
        return "T009_MOMENT_CENTER_MIGRATION_DOWN"

    if up_excursion >= 4.0 and event_count >= 4 and pressure >= 0.55:
        return "T009_MOMENT_PROGRESSIVE_WAVE"

    if absorption >= 0.70 and failed >= 0.65 and abs(delta) < 3.0 and center_range < 4.0 and favorable_excursion < 4.0:
        return "T009_MOMENT_EFFORT_WITHOUT_RESULT"

    if abs(delta) < 2.0 and event_count >= 4 and dwell >= 0.75 and compression >= 0.75:
        return "T009_MOMENT_ABSORPTION_SHELF"

    if event_count <= 2 and previous_metrics and previous_metrics.get("event_count", 0) >= 4:
        prev_low = previous_metrics.get("zone_low")
        prev_high = previous_metrics.get("zone_high")
        center = metrics.get("center_end")
        if prev_low is not None and prev_high is not None and center is not None and prev_low <= center <= prev_high:
            return "T009_MOMENT_FLOW_BREATHING"

    if previous_metrics:
        prev_delta = previous_metrics.get("center_delta_pips", 0.0)
        if abs(prev_delta) >= 6.0 and abs(delta) < abs(prev_delta) * 0.55 and (delta * prev_delta) < 0:
            if absorption >= 0.55 or compression >= 0.55 or pressure >= 0.55:
                return "T009_MOMENT_RETRACE_DECISION_AREA"
            return "T009_MOMENT_CORRECTIVE_WAVE"
        if abs(prev_delta) >= 6.0 and (delta * prev_delta) < 0 and abs(delta) >= 3.0:
            return "T009_MOMENT_BREAK_RETEST_FAILED"

    if delta >= 4.0 and event_count >= 4:
        if pressure >= 0.55 or absorption < 0.70:
            return "T009_MOMENT_PROGRESSIVE_WAVE"
        return "T009_MOMENT_CENTER_MIGRATION_UP"

    if event_count >= 4 and center_range >= 6.0 and pressure >= 0.55:
        return "T009_MOMENT_BREAKOUT_PENDING_RETEST"

    return "T009_MOMENT_GENERIC_BATTLEFIELD"


def _format_time_for_fr(value: Optional[str]) -> str:
    dt = _parse_time(value)
    if dt is None:
        return "heure inconnue"
    return dt.strftime("%H:%M") + " UTC"


def _format_zone(low: Optional[float], high: Optional[float]) -> str:
    if low is None or high is None:
        return "zone inconnue"
    return f"{low:.5f} - {high:.5f}"


def _build_french_text(moment_type: str, metrics: Dict[str, Any]) -> Tuple[str, str, str, List[str]]:
    delta = metrics["center_delta_pips"]
    direction = metrics["migration_direction"]
    zone_low = metrics.get("zone_low")
    zone_high = metrics.get("zone_high")

    common_evidence = [
        f"events regroupés : {metrics['event_count']}",
        f"migration centre : {delta:.1f} pips ({direction})",
        f"chemin interne du centre : range {metrics.get('center_range_pips', 0.0):.1f} pips",
        f"excursion favorable max : {metrics.get('max_favorable_excursion_pips', 0.0):.1f} pips",
        f"excursion adverse max : {metrics.get('max_adverse_excursion_pips', 0.0):.1f} pips",
    ]
    if metrics.get("avg_dwell_score") is not None:
        common_evidence.append(f"dwell moyen : {metrics['avg_dwell_score']:.2f}")
    if metrics.get("avg_compression_score") is not None:
        common_evidence.append(f"compression moyenne : {metrics['avg_compression_score']:.2f}")
    if metrics.get("avg_failed_displacement_score") is not None:
        common_evidence.append(f"failed displacement moyen : {metrics['avg_failed_displacement_score']:.2f}")
    if zone_low is not None and zone_high is not None:
        common_evidence.append(f"zone observee : {zone_low:.5f} - {zone_high:.5f}")

    if moment_type == "T009_MOMENT_EFFORT_WITHOUT_RESULT":
        return (
            "Le flux depense de l'energie, mais le centre de zone gagne peu de terrain.",
            "C'est une trace d'absorption ou de frein local : l'effort existe, mais le resultat prix reste limite.",
            "B9 le voit par absorption elevee, failed displacement eleve et migration de centre faible.",
            common_evidence,
        )
    if moment_type == "T009_MOMENT_ABSORPTION_SHELF":
        return (
            "Le prix habite une zone serree : le champ local forme un palier.",
            "Ce palier devient une memoire de zone, utile pour lire les reactions suivantes.",
            "B9 le voit par events nombreux, dwell/compression eleves et centre stable.",
            common_evidence,
        )
    if moment_type == "T009_MOMENT_CENTER_MIGRATION_UP":
        return (
            "Le centre de gravite local monte par paliers.",
            "La zone memoire ne reste pas fixe : elle migre vers le haut.",
            "B9 le voit par centres successifs plus hauts dans une sequence coherente.",
            common_evidence,
        )
    if moment_type == "T009_MOMENT_CENTER_MIGRATION_DOWN":
        return (
            "Le centre de gravite local descend par paliers.",
            "L'absorption ne bloque pas forcement le flux ; elle peut accompagner une pression descendante.",
            "B9 le voit par centres successifs plus bas dans une sequence coherente.",
            common_evidence,
        )
    if moment_type == "T009_MOMENT_PROGRESSIVE_WAVE":
        return (
            "Une vague progresse : l'effort produit un deplacement visible du centre.",
            "Le mouvement avance par traces successives au lieu de rester bloque dans la meme zone.",
            "B9 le voit par migration nette du centre et zones successives coherentes.",
            common_evidence,
        )
    if moment_type == "T009_MOMENT_CORRECTIVE_WAVE":
        return (
            "Le flux respire contre l'extension precedente.",
            "Cette correction aide a distinguer respiration structuree et invalidation de scene.",
            "B9 le voit par retour oppose apres extension, avec progression moins nette.",
            common_evidence,
        )
    if moment_type == "T009_MOMENT_BREAKOUT_PENDING_RETEST":
        return (
            "La zone est sortie de son enveloppe, mais la cassure reste en attente de jugement.",
            "Le retour vers la zone dira si la scene accepte la sortie ou la reintegre.",
            "B9 le voit par extension hors zone et absence de retest clair dans le groupe courant.",
            common_evidence,
        )
    if moment_type == "T009_MOMENT_BREAK_RETEST_FAILED":
        return (
            "La tentative initiale n'est pas validee par le retour.",
            "Le retest defavorable transforme la cassure en information fragile ou piege possible.",
            "B9 le voit par retour oppose apres extension et centre qui revient contre la zone.",
            common_evidence,
        )
    if moment_type == "T009_MOMENT_RETRACE_DECISION_AREA":
        return (
            "Le retracement revient sur une zone de decision.",
            "La scene doit etre lue par la reaction a cette zone : absorption, respiration ou invalidation.",
            "B9 le voit par retour vers zone importante avec compression ou absorption.",
            common_evidence,
        )
    if moment_type == "T009_MOMENT_FLOW_BREATHING":
        return (
            "La densite d'events baisse et le flux reprend de l'air.",
            "La respiration permet de distinguer pause locale et vraie rupture de scene.",
            "B9 le voit par groupe plus leger apres sequence dense et retour en zone memoire.",
            common_evidence,
        )
    return (
        "Le microfilm local produit une scene lisible mais non specialisee en V3.",
        "Ce moment conserve la trace pour la synthese sans forcer une etiquette trop precise.",
        "B9 le voit par regroupement temps/prix et metriques de zone disponibles.",
        common_evidence,
    )


def _build_v1_text(moment_type: str, metrics: Dict[str, Any], reading: str, why: str, how: str, evidence: Sequence[str]) -> Dict[str, str]:
    mechanism_by_type = {
        "T009_MOMENT_EFFORT_WITHOUT_RESULT": "Effort eleve + failed displacement eleve + centre peu mobile.",
        "T009_MOMENT_ABSORPTION_SHELF": "Dwell et compression eleves dans une zone serree.",
        "T009_MOMENT_CENTER_MIGRATION_UP": "Centres successifs plus hauts avec coherence de zone.",
        "T009_MOMENT_CENTER_MIGRATION_DOWN": "Centres successifs plus bas avec coherence de zone.",
        "T009_MOMENT_PROGRESSIVE_WAVE": "L'effort produit un deplacement net du centre.",
        "T009_MOMENT_CORRECTIVE_WAVE": "Retour oppose apres une extension plus forte.",
        "T009_MOMENT_BREAKOUT_PENDING_RETEST": "Sortie de zone visible mais jugement par retour encore incomplet.",
        "T009_MOMENT_BREAK_RETEST_FAILED": "Retour defavorable apres extension initiale.",
        "T009_MOMENT_RETRACE_DECISION_AREA": "Retour vers zone importante avec absorption ou compression.",
        "T009_MOMENT_FLOW_BREATHING": "Densite plus faible apres sequence dense, sans invalidation majeure.",
    }
    proof_summary = "; ".join(str(item) for item in evidence[:4])
    return {
        "what_happens_fr": reading,
        "how_it_happened_fr": how.replace("B9 le voit par ", "La scene se construit par "),
        "mechanism_fr": mechanism_by_type.get(moment_type, "Regroupement temps/prix avec metriques disponibles."),
        "proof_summary_fr": proof_summary,
    }


def _zone_overlap(current: Dict[str, Any], previous: Dict[str, Any]) -> bool:
    cur_low, cur_high = current.get("zone_low"), current.get("zone_high")
    prev_low, prev_high = previous.get("zone_low"), previous.get("zone_high")
    if None in (cur_low, cur_high, prev_low, prev_high):
        return False
    return max(cur_low, prev_low) <= min(cur_high, prev_high)


def _build_v2_text(moment_type: str, metrics: Dict[str, Any], previous_metrics: Optional[Dict[str, Any]], previous_type: Optional[str]) -> Dict[str, str]:
    previous_context = "Premier moment exploitable de la sequence."
    cause = "La cause locale reste a confirmer par le contexte precedent."
    reaction = "Le flux laisse une nouvelle trace locale."
    consequence = "La scene garde cette zone comme information active."
    memory_shift = "La memoire locale reste a surveiller."
    retest_role = "Aucun retest distinct n'est isole dans ce moment."

    if previous_metrics:
        prev_label = MOMENT_LABELS_FR.get(previous_type or "", "moment precedent")
        previous_context = f"Le moment precedent etait : {prev_label}."
        if previous_type == "T009_MOMENT_ABSORPTION_SHELF" and metrics.get("migration_direction") == "DOWN":
            cause = "Le palier precedent n'a pas tenu comme centre actif."
            reaction = "Le flux accepte progressivement une zone plus basse."
            consequence = "La memoire active se deplace vers le bas."
            memory_shift = "Memoire deplacee vers le bas, sur un centre inferieur."
        elif previous_type == "T009_MOMENT_ABSORPTION_SHELF" and metrics.get("migration_direction") == "UP":
            cause = "Le palier precedent sert de base de reprise locale."
            reaction = "Le flux reprend du terrain par paliers."
            consequence = "La memoire active migre vers un centre superieur."
            memory_shift = "Memoire deplacee vers le haut."
        elif moment_type == "T009_MOMENT_BREAK_RETEST_FAILED":
            cause = "La tentative initiale revient contre sa zone de depart."
            reaction = "Le retour ne confirme pas l'acceptation de la sortie."
            consequence = "La cassure devient fragile dans la lecture B9."
            memory_shift = "La memoire revient vers la zone precedente."
            retest_role = "Le retest refuse la validation de la sortie."
        elif moment_type == "T009_MOMENT_RETRACE_DECISION_AREA":
            cause = "Une extension precedente appelle une interrogation de zone."
            reaction = "Le retracement revient tester la memoire active."
            consequence = "La suite depend de la reaction autour de cette zone."
            memory_shift = "La memoire reste active mais pas encore deplacee."
            retest_role = "Le retest sert de juge de la scene."
        elif moment_type == "T009_MOMENT_FLOW_BREATHING":
            cause = "La sequence dense precedente relache temporairement la pression."
            reaction = "Le flux revient respirer dans ou pres de la zone memoire."
            consequence = "La scene ralentit sans prouver une invalidation majeure."
            memory_shift = "La memoire reste active mais n'est pas encore deplacee."
        elif _zone_overlap(metrics, previous_metrics):
            cause = "La nouvelle trace se forme dans le voisinage de la memoire precedente."
            reaction = "Le flux reutilise une zone deja active."
            consequence = "La zone conserve un role dans le chapitre courant."
            memory_shift = "Memoire stable ou recyclee."

    if moment_type == "T009_MOMENT_PROGRESSIVE_WAVE":
        reaction = "Le flux transforme l'effort en progression visible."
        consequence = "La scene avance par paliers plutot que de rester bloquee."
        if metrics.get("migration_direction") == "UP":
            memory_shift = "Memoire deplacee vers un centre superieur."
        elif metrics.get("migration_direction") == "DOWN":
            memory_shift = "Memoire deplacee vers le bas, sur un centre inferieur."
    if moment_type == "T009_MOMENT_EFFORT_WITHOUT_RESULT":
        reaction = "L'effort est absorbe ou freine localement."
        consequence = "La zone devient une information de tension contenue."
        memory_shift = "Pas de deplacement net de memoire."
    if moment_type == "T009_MOMENT_ABSORPTION_SHELF":
        reaction = "Le flux reste accroche dans une zone serree."
        consequence = "Un palier de memoire locale se construit."
        memory_shift = "Memoire stabilisee autour du centre actuel."

    return {
        "previous_context_fr": previous_context,
        "cause_fr": cause,
        "reaction_fr": reaction,
        "consequence_fr": consequence,
        "memory_shift_fr": memory_shift,
        "retest_role_fr": retest_role,
    }


def _build_v3_text(moment_type: str, metrics: Dict[str, Any], index: int) -> Dict[str, Any]:
    chapter = MOMENT_CHAPTERS_FR.get(moment_type, "Ouverture / transition")
    role = MOMENT_ROLES_FR.get(moment_type, "transition_locale")
    scene_id = f"B9SC-{index:03d}"
    parent_scene = {
        "scene_id": "B9SESSION-001",
        "model": "base -> réaction -> projection -> jugement",
        "base_fr": "zone de mémoire locale",
        "reaction_fr": "réaction du centre et du chemin interne",
        "projection_fr": "extension ou respiration mesurée par le centre",
        "judgment_fr": "jugement par retest ou par absence de progrès durable",
        "read_only": True,
    }
    if moment_type in ("T009_MOMENT_CENTER_MIGRATION_UP", "T009_MOMENT_CENTER_MIGRATION_DOWN"):
        fractal = "Les traces locales ne sont pas isolées : chaque palier devient la cause possible du palier suivant."
    elif moment_type == "T009_MOMENT_ABSORPTION_SHELF":
        fractal = "Le microfilm construit une étagère locale qui peut devenir le pivot du chapitre suivant."
    elif moment_type in ("T009_MOMENT_BREAKOUT_PENDING_RETEST", "T009_MOMENT_BREAK_RETEST_FAILED"):
        fractal = "Le moment local sert de juge : la scène ne vaut que par sa réaction au retour."
    elif moment_type == "T009_MOMENT_FLOW_BREATHING":
        fractal = "La respiration locale relie une séquence dense à la prochaine décision de zone."
    else:
        fractal = "Le microfilm devient moment, le moment devient pièce d'une scène de session."
    return {
        "scene_id": scene_id,
        "scene_role": role,
        "parent_scene": parent_scene,
        "child_moments": [],
        "session_chapter": chapter,
        "fractal_reading_fr": fractal,
    }


def build_moments(groups: Sequence[Sequence[NormalizedEvent]], pip_size: float = DEFAULT_PIP_SIZE) -> List[Moment]:
    moments: List[Moment] = []
    previous_metrics: Optional[Dict[str, Any]] = None
    previous_type: Optional[str] = None
    for index, group in enumerate(groups, start=1):
        metrics = _metrics_for_group(group, pip_size=pip_size)
        moment_type = classify_group(metrics, previous_metrics=previous_metrics)
        label = MOMENT_LABELS_FR.get(moment_type, MOMENT_LABELS_FR["T009_MOMENT_GENERIC_BATTLEFIELD"])
        reading, why, how, evidence = _build_french_text(moment_type, metrics)
        v1 = _build_v1_text(moment_type, metrics, reading, why, how, evidence)
        v2 = _build_v2_text(moment_type, metrics, previous_metrics, previous_type)
        v3 = _build_v3_text(moment_type, metrics, index)
        limits = _source_limits(metrics.get("source_mode"), metrics.get("data_visibility"), metrics.get("confidence_cap"))
        source_profile = _source_profile(metrics.get("source_mode"), metrics.get("data_visibility"), metrics.get("confidence_cap"))
        effort_role = _classify_effort_role(moment_type, metrics)
        retest_status = _infer_retest_status(moment_type, metrics, previous_metrics)
        memory_state = _infer_memory_state(moment_type, metrics, retest_status)
        zone_memory = _build_zone_memory(metrics, memory_state)
        moments.append(
            Moment(
                moment_id=f"T009M-{index:03d}",
                moment_type=moment_type,
                label_fr=label,
                time_start=metrics["time_start"],
                time_end=metrics["time_end"],
                zone_low=_round_or_none(metrics["zone_low"], 6),
                zone_high=_round_or_none(metrics["zone_high"], 6),
                center_start=_round_or_none(metrics["center_start"], 6),
                center_end=_round_or_none(metrics["center_end"], 6),
                center_min=_round_or_none(metrics["center_min"], 6),
                center_max=_round_or_none(metrics["center_max"], 6),
                center_delta_pips=round(metrics["center_delta_pips"], 2),
                center_range_pips=round(metrics["center_range_pips"], 2),
                center_path=metrics.get("center_path", []),
                max_favorable_excursion_pips=round(metrics["max_favorable_excursion_pips"], 2),
                max_adverse_excursion_pips=round(metrics["max_adverse_excursion_pips"], 2),
                migration_direction=metrics["migration_direction"],
                event_count=metrics["event_count"],
                avg_absorption_score=_round_or_none(metrics["avg_absorption_score"], 4),
                avg_battle_score=_round_or_none(metrics["avg_battle_score"], 4),
                avg_compression_score=_round_or_none(metrics["avg_compression_score"], 4),
                avg_dwell_score=_round_or_none(metrics["avg_dwell_score"], 4),
                avg_failed_displacement_score=_round_or_none(metrics["avg_failed_displacement_score"], 4),
                avg_pressure_score=_round_or_none(metrics["avg_pressure_score"], 4),
                source_mode=metrics["source_mode"],
                data_visibility=metrics["data_visibility"],
                confidence_cap=_round_or_none(metrics["confidence_cap"], 4),
                reading_fr=reading,
                why_it_matters_fr=why,
                how_detected_fr=how,
                evidence_fr=evidence,
                limits_fr=limits,
                source_profile=source_profile,
                effort_role=effort_role,
                retest_status=retest_status,
                memory_state=memory_state,
                zone_memory=zone_memory,
                what_happens_fr=v1["what_happens_fr"],
                how_it_happened_fr=v1["how_it_happened_fr"],
                mechanism_fr=v1["mechanism_fr"],
                proof_summary_fr=v1["proof_summary_fr"],
                previous_context_fr=v2["previous_context_fr"],
                cause_fr=v2["cause_fr"],
                reaction_fr=v2["reaction_fr"],
                consequence_fr=v2["consequence_fr"],
                memory_shift_fr=v2["memory_shift_fr"],
                retest_role_fr=v2["retest_role_fr"],
                scene_id=v3["scene_id"],
                scene_role=v3["scene_role"],
                parent_scene=v3["parent_scene"],
                child_moments=v3["child_moments"],
                session_chapter=v3["session_chapter"],
                fractal_reading_fr=v3["fractal_reading_fr"],
            )
        )
        previous_metrics = metrics
        previous_type = moment_type
    return moments


def _session_summary(moments: Sequence[Moment]) -> Dict[str, Any]:
    chapters = Counter(m.session_chapter for m in moments)
    directions = Counter(m.migration_direction for m in moments)
    return {
        "scene_id": "B9SESSION-001",
        "moment_count": len(moments),
        "chapters": dict(chapters),
        "dominant_migration": directions.most_common(1)[0][0] if directions else None,
        "reading_fr": "B9 relie les micro-traces en chapitres de session sans transformer la lecture en signal.",
    }


def _source_summary(state: Dict[str, Any], events: Sequence[NormalizedEvent], state_file: str | Path, events_file: str | Path) -> Dict[str, Any]:
    source_mode = _dominant(e.source_mode for e in events) or _nested_get(state, "source_mode", "source.source_mode")
    data_visibility = _dominant(e.data_visibility for e in events) or _nested_get(state, "data_visibility", "source.data_visibility")
    confidence_values = [e.confidence_cap for e in events if e.confidence_cap is not None]
    confidence_cap = min(confidence_values) if confidence_values else _to_float(_nested_get(state, "confidence_cap", "source.confidence_cap"))
    profile = _source_profile(str(source_mode) if source_mode is not None else None, str(data_visibility) if data_visibility is not None else None, confidence_cap)
    return {
        "state_file": str(state_file),
        "events_file": str(events_file),
        "event_count": len(events),
        "source_mode": source_mode,
        "data_visibility": data_visibility,
        "confidence_cap": confidence_cap,
        "source_profile": profile,
    }


_REMAP_TIME_KEYS = {
    "time_start",
    "time_end",
    "first_seen",
    "last_seen",
    "last_tested",
    "start_utc",
    "end_utc",
    "timestamp",
    "ts_utc",
}


def _remap_iso_value(value: Any, time_remap: Optional[Tuple[datetime, datetime]]) -> Any:
    dt = _parse_time(value)
    if dt is None:
        return value
    return _iso_utc(_apply_time_remap(dt, time_remap))


def _remap_time_fields_inplace(value: Any, time_remap: Optional[Tuple[datetime, datetime]]) -> None:
    """Recursively remap known timestamp fields in an export object.

    This is deliberately applied at export-summary level, not classification level:
    scores, labels, moments, scenes, zones and grouping stay unchanged. Only the
    outward-facing clock is translated from replay time to original market time.
    """
    if time_remap is None:
        return
    if isinstance(value, dict):
        for key, item in list(value.items()):
            if key in _REMAP_TIME_KEYS and item is not None:
                value[key] = _remap_iso_value(item, time_remap)
            else:
                _remap_time_fields_inplace(item, time_remap)
    elif isinstance(value, list):
        for item in value:
            _remap_time_fields_inplace(item, time_remap)


def remap_summary_times(summary: Dict[str, Any], replay_report: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Return summary with exported replay timestamps converted to original time.

    If no usable replay report is provided, the summary is returned unchanged.
    """
    time_remap = _build_time_remap(replay_report)
    if time_remap is None:
        return summary
    _remap_time_fields_inplace(summary, time_remap)
    shifted_start, original_start = time_remap
    source = summary.setdefault("source", {})
    source["replay_time_remap"] = {
        "applied": True,
        "original_start_utc": _iso_utc(original_start),
        "shift_delta_seconds": int((shifted_start - original_start).total_seconds()),
        "note_fr": "Horaires exportes remappes vers le temps original de marche.",
    }
    return summary


def summarize_events(
    state: Dict[str, Any],
    events: Sequence[Dict[str, Any]],
    state_file: str | Path = "",
    events_file: str | Path = "",
    max_gap_sec: int = DEFAULT_MAX_GAP_SEC,
    price_merge_pips: float = DEFAULT_PRICE_MERGE_PIPS,
    pip_size: float = DEFAULT_PIP_SIZE,
    replay_report: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    normalized = normalize_events(events, state=state, replay_report=replay_report)
    groups = group_events(normalized, max_gap_sec=max_gap_sec, price_merge_pips=price_merge_pips, pip_size=pip_size)
    groups = split_groups_on_center_inflexion(groups, pip_size=pip_size)
    moments = build_moments(groups, pip_size=pip_size)
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    summary = {
        "module": MODULE_NAME,
        "version": VERSION,
        "generated_at_utc": generated_at,
        "source": _source_summary(state, normalized, state_file, events_file),
        "session_scene": _session_summary(moments),
        "moments": [asdict(m) for m in moments],
    }
    return remap_summary_times(summary, replay_report)


def export_json(summary: Dict[str, Any], path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def render_markdown(summary: Dict[str, Any]) -> str:
    source = summary.get("source", {})
    moments = summary.get("moments", [])
    session = summary.get("session_scene", {})
    lines: List[str] = [
        "# T009 Sequence Summary V3.1.1",
        "",
        "## Resume",
        f"- Version : {summary.get('version')}",
        f"- Nombre events bruts : {source.get('event_count', 0)}",
        f"- Nombre moments : {len(moments)}",
        f"- Source mode : {source.get('source_mode') or 'UNKNOWN'}",
        f"- Data visibility : {source.get('data_visibility') or 'UNKNOWN'}",
        f"- Confidence cap : {source.get('confidence_cap')}",
        "- Limites : lecture B9 read-only, sans moteur, sans surfaces externes, sans fusion multi-devise prématurée.",
        f"- Source profile : {source.get('source_profile', {}).get('quality', 'UNKNOWN')}",
        f"- Langage source : {source.get('source_profile', {}).get('language_fr', '')}",
        "- Cap : B9 cherche la trace laissée par l'effort, pas une instruction.",
        "",
        "## Scene de session",
        f"- Scene : {session.get('scene_id', 'B9SESSION-001')}",
        f"- Chapitres : {session.get('chapters', {})}",
        f"- Lecture : {session.get('reading_fr', '')}",
        "",
        "## Moments cles",
        "",
    ]
    if not moments:
        lines.extend([
            "Aucun moment detecte.",
            "",
            "Limites : aucun event T009 exploitable dans le fichier fourni.",
        ])
        return "\n".join(lines) + "\n"

    for idx, moment in enumerate(moments, start=1):
        start = _format_time_for_fr(moment.get("time_start"))
        end = _format_time_for_fr(moment.get("time_end"))
        lines.extend([
            f"### Moment {idx} - {start} a {end}",
            f"**Titre :** {moment.get('label_fr')}",
            f"**Type interne :** `{moment.get('moment_type')}`",
            f"**Scene :** `{moment.get('scene_id')}` / role `{moment.get('scene_role')}`",
            f"**Parent scene :** {moment.get('parent_scene', {})}",
            f"**Chapitre :** {moment.get('session_chapter')}",
            f"**Zone :** {moment.get('zone_low')} -> {moment.get('zone_high')}",
            f"**Centre :** {moment.get('center_start')} -> {moment.get('center_end')} | min {moment.get('center_min')} | max {moment.get('center_max')}",
            f"**Chemin centre :** range {moment.get('center_range_pips')} pips | excursion favorable {moment.get('max_favorable_excursion_pips')} pips | adverse {moment.get('max_adverse_excursion_pips')} pips",
            f"**Center path :** {moment.get('center_path', [])}",
            f"**Effort role :** {moment.get('effort_role')}",
            f"**Retest status :** {moment.get('retest_status')}",
            f"**Memory state :** {moment.get('memory_state')}",
            f"**Zone memory :** {moment.get('zone_memory', {})}",
            "",
            "**Ce qui se passe**",
            moment.get("what_happens_fr") or moment.get("reading_fr", ""),
            "",
            "**Pourquoi c'est important**",
            moment.get("why_it_matters_fr", ""),
            "",
            "**Comment cela se produit**",
            moment.get("how_it_happened_fr", ""),
            "",
            "**Mecanisme**",
            moment.get("mechanism_fr", ""),
            "",
            "**Comment B9 le voit**",
            moment.get("how_detected_fr", ""),
            "",
            "**Cause / reaction / consequence**",
            f"- Contexte precedent : {moment.get('previous_context_fr', '')}",
            f"- Cause : {moment.get('cause_fr', '')}",
            f"- Reaction : {moment.get('reaction_fr', '')}",
            f"- Consequence : {moment.get('consequence_fr', '')}",
            f"- Deplacement memoire : {moment.get('memory_shift_fr', '')}",
            f"- Role du retest : {moment.get('retest_role_fr', '')}",
            "",
            "**Lecture fractale**",
            moment.get("fractal_reading_fr", ""),
            "",
            "**Preuves**",
        ])
        for item in moment.get("evidence_fr", []):
            lines.append(f"- {item}")
        if moment.get("proof_summary_fr"):
            lines.append(f"- resume preuve : {moment.get('proof_summary_fr')}")
        lines.extend(["", "**Source profile**", str(moment.get("source_profile", {})), "", "**Limites**"])
        for item in moment.get("limits_fr", []):
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines) + "\n"


def export_markdown(summary: Dict[str, Any], path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render_markdown(summary), encoding="utf-8")
    return p


def summarize_files(
    state_file: str | Path,
    events_file: str | Path,
    output_dir: str | Path,
    max_gap_sec: int = DEFAULT_MAX_GAP_SEC,
    price_merge_pips: float = DEFAULT_PRICE_MERGE_PIPS,
    pip_size: float = DEFAULT_PIP_SIZE,
    replay_report_file: str | Path | None = None,
) -> Dict[str, Path | Dict[str, Any]]:
    state = load_state(state_file)
    events = load_events(events_file)
    replay_report = load_json(replay_report_file, default={}) if replay_report_file else None
    summary = summarize_events(
        state=state,
        events=events,
        state_file=state_file,
        events_file=events_file,
        max_gap_sec=max_gap_sec,
        price_merge_pips=price_merge_pips,
        pip_size=pip_size,
        replay_report=replay_report,
    )
    out = Path(output_dir)
    json_path = export_json(summary, out / "t009_sequence_summary.json")
    md_path = export_markdown(summary, out / "t009_sequence_summary.md")
    return {"summary": summary, "json_path": json_path, "markdown_path": md_path}


def validate_summary_contract(summary: Dict[str, Any]) -> List[str]:
    """Return human-readable validation problems. Does not raise.

    This helper is used by tests and V0.1 validation reports. It never touches DB.
    """
    problems: List[str] = []
    moments = summary.get("moments", [])
    if not isinstance(moments, list):
        return ["moments field is not a list"]
    for idx, moment in enumerate(moments, start=1):
        for key in (
            "label_fr",
            "reading_fr",
            "what_happens_fr",
            "why_it_matters_fr",
            "how_it_happened_fr",
            "mechanism_fr",
            "proof_summary_fr",
            "previous_context_fr",
            "cause_fr",
            "reaction_fr",
            "consequence_fr",
            "memory_shift_fr",
            "retest_role_fr",
            "scene_id",
            "scene_role",
            "session_chapter",
            "fractal_reading_fr",
            "source_profile",
            "effort_role",
            "retest_status",
            "memory_state",
            "zone_memory",
            "center_path",
            "source_mode",
            "data_visibility",
            "confidence_cap",
        ):
            if key not in moment:
                problems.append(f"moment {idx} missing {key}")
        if not moment.get("limits_fr"):
            problems.append(f"moment {idx} missing limits_fr")
    return problems


__all__ = [
    "NormalizedEvent",
    "Moment",
    "load_json",
    "load_state",
    "load_events",
    "normalize_event",
    "normalize_events",
    "group_events",
    "split_groups_on_center_inflexion",
    "classify_group",
    "build_moments",
    "summarize_events",
    "summarize_files",
    "export_json",
    "export_markdown",
    "render_markdown",
    "validate_summary_contract",
]
