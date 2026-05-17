"""T009 Sequence Summarizer V0 / B9.

Read-only transformation layer:
raw T009 battlefield events -> a compact sequence of human-readable B9 moments.

The module does not import engine, dashboard, telegram, or database writers.
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
VERSION = "V0"
DEFAULT_PIP_SIZE = 0.0001
DEFAULT_MAX_GAP_SEC = 300
DEFAULT_PRICE_MERGE_PIPS = 5.0

MOMENT_LABELS_FR: Dict[str, str] = {
    "T009_MOMENT_EFFORT_WITHOUT_RESULT": "Effort sans resultat",
    "T009_MOMENT_ABSORPTION_SHELF": "Palier d'absorption / etagere d'equilibre",
    "T009_MOMENT_CENTER_MIGRATION_UP": "Centre de gravite qui monte",
    "T009_MOMENT_CENTER_MIGRATION_DOWN": "Centre de gravite qui descend",
    "T009_MOMENT_PROGRESSIVE_WAVE": "Vague progressive",
    "T009_MOMENT_CORRECTIVE_WAVE": "Vague corrective",
    "T009_MOMENT_BREAKOUT_PENDING_RETEST": "Cassure en attente de jugement",
    "T009_MOMENT_BREAK_RETEST_FAILED": "Retest echoue",
    "T009_MOMENT_RETRACE_DECISION_AREA": "Zone de decision au retracement",
    "T009_MOMENT_FLOW_BREATHING": "Respiration du flux",
    "T009_MOMENT_GENERIC_BATTLEFIELD": "Moment de bataille local",
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
    center_delta_pips: float
    center_range_pips: float
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


def load_json(path: str | Path, default: Any = None) -> Any:
    """Load JSON from path. Missing or empty files return default."""
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


def normalize_event(event: Dict[str, Any], state_defaults: Optional[Dict[str, Any]] = None) -> NormalizedEvent:
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

    ts_value = _nested_get(event, "ts_utc", "timestamp", "time", "created_at", "bucket.timestamp")
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


def normalize_events(events: Sequence[Dict[str, Any]], state: Optional[Dict[str, Any]] = None) -> List[NormalizedEvent]:
    normalized = [normalize_event(e, state_defaults=state) for e in events]
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
    limits.append("delta proxy : pression deduite, delta achat/vente reel non garanti")
    # Deduplicate while preserving order.
    seen = set()
    result: List[str] = []
    for item in limits:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _metrics_for_group(group: Sequence[NormalizedEvent], pip_size: float = DEFAULT_PIP_SIZE) -> Dict[str, Any]:
    centers = [e.zone_center for e in group if e.zone_center is not None]
    lows = [e.zone_low for e in group if e.zone_low is not None]
    highs = [e.zone_high for e in group if e.zone_high is not None]
    center_start = centers[0] if centers else None
    center_end = centers[-1] if centers else None
    center_delta_pips = 0.0
    if center_start is not None and center_end is not None:
        center_delta_pips = (center_end - center_start) / pip_size
    center_range_pips = 0.0
    if centers:
        center_range_pips = (max(centers) - min(centers)) / pip_size

    confidence_values = [e.confidence_cap for e in group if e.confidence_cap is not None]
    return {
        "time_start": group[0].timestamp,
        "time_end": group[-1].timestamp,
        "zone_low": min(lows) if lows else None,
        "zone_high": max(highs) if highs else None,
        "center_start": center_start,
        "center_end": center_end,
        "center_delta_pips": center_delta_pips,
        "center_range_pips": center_range_pips,
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
    """Classify one group with readable V0 heuristics."""
    event_count = metrics["event_count"]
    delta = metrics["center_delta_pips"]
    center_range = metrics["center_range_pips"]
    absorption = metrics.get("avg_absorption_score") or 0.0
    compression = metrics.get("avg_compression_score") or 0.0
    dwell = metrics.get("avg_dwell_score") or 0.0
    failed = metrics.get("avg_failed_displacement_score") or 0.0
    pressure = metrics.get("avg_pressure_score") or 0.0

    if absorption >= 0.70 and failed >= 0.65 and abs(delta) < 3.0:
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

    if delta <= -4.0 and event_count >= 4:
        return "T009_MOMENT_CENTER_MIGRATION_DOWN"

    if event_count >= 4 and center_range >= 6.0 and pressure >= 0.55:
        return "T009_MOMENT_BREAKOUT_PENDING_RETEST"

    return "T009_MOMENT_GENERIC_BATTLEFIELD"


def _format_time_for_fr(value: Optional[str]) -> str:
    dt = _parse_time(value)
    if dt is None:
        return "heure inconnue"
    return dt.strftime("%H:%M") + " UTC"


def _build_french_text(moment_type: str, metrics: Dict[str, Any]) -> Tuple[str, str, str, List[str]]:
    label = MOMENT_LABELS_FR.get(moment_type, MOMENT_LABELS_FR["T009_MOMENT_GENERIC_BATTLEFIELD"])
    delta = metrics["center_delta_pips"]
    direction = metrics["migration_direction"]
    zone_low = metrics.get("zone_low")
    zone_high = metrics.get("zone_high")

    common_evidence = [
        f"events regroupes : {metrics['event_count']}",
        f"migration centre : {delta:.1f} pips ({direction})",
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
        "Le microfilm local produit une scene lisible mais non specialisee en V0.",
        "Ce moment conserve la trace pour la synthese sans forcer une etiquette trop precise.",
        "B9 le voit par regroupement temps/prix et metriques de zone disponibles.",
        common_evidence,
    )


def build_moments(groups: Sequence[Sequence[NormalizedEvent]], pip_size: float = DEFAULT_PIP_SIZE) -> List[Moment]:
    moments: List[Moment] = []
    previous_metrics: Optional[Dict[str, Any]] = None
    for index, group in enumerate(groups, start=1):
        metrics = _metrics_for_group(group, pip_size=pip_size)
        moment_type = classify_group(metrics, previous_metrics=previous_metrics)
        label = MOMENT_LABELS_FR.get(moment_type, MOMENT_LABELS_FR["T009_MOMENT_GENERIC_BATTLEFIELD"])
        reading, why, how, evidence = _build_french_text(moment_type, metrics)
        limits = _source_limits(metrics.get("source_mode"), metrics.get("data_visibility"), metrics.get("confidence_cap"))
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
                center_delta_pips=round(metrics["center_delta_pips"], 2),
                center_range_pips=round(metrics["center_range_pips"], 2),
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
            )
        )
        previous_metrics = metrics
    return moments


def _source_summary(state: Dict[str, Any], events: Sequence[NormalizedEvent], state_file: str | Path, events_file: str | Path) -> Dict[str, Any]:
    source_mode = _dominant(e.source_mode for e in events) or _nested_get(state, "source_mode", "source.source_mode")
    data_visibility = _dominant(e.data_visibility for e in events) or _nested_get(state, "data_visibility", "source.data_visibility")
    confidence_values = [e.confidence_cap for e in events if e.confidence_cap is not None]
    confidence_cap = min(confidence_values) if confidence_values else _to_float(_nested_get(state, "confidence_cap", "source.confidence_cap"))
    return {
        "state_file": str(state_file),
        "events_file": str(events_file),
        "event_count": len(events),
        "source_mode": source_mode,
        "data_visibility": data_visibility,
        "confidence_cap": confidence_cap,
    }


def summarize_events(
    state: Dict[str, Any],
    events: Sequence[Dict[str, Any]],
    state_file: str | Path = "",
    events_file: str | Path = "",
    max_gap_sec: int = DEFAULT_MAX_GAP_SEC,
    price_merge_pips: float = DEFAULT_PRICE_MERGE_PIPS,
    pip_size: float = DEFAULT_PIP_SIZE,
) -> Dict[str, Any]:
    normalized = normalize_events(events, state=state)
    groups = group_events(normalized, max_gap_sec=max_gap_sec, price_merge_pips=price_merge_pips, pip_size=pip_size)
    moments = build_moments(groups, pip_size=pip_size)
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "module": MODULE_NAME,
        "version": VERSION,
        "generated_at_utc": generated_at,
        "source": _source_summary(state, normalized, state_file, events_file),
        "moments": [asdict(m) for m in moments],
    }


def export_json(summary: Dict[str, Any], path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def render_markdown(summary: Dict[str, Any]) -> str:
    source = summary.get("source", {})
    moments = summary.get("moments", [])
    lines: List[str] = [
        "# T009 Sequence Summary V0",
        "",
        "## Resume",
        f"- Nombre events bruts : {source.get('event_count', 0)}",
        f"- Nombre moments : {len(moments)}",
        f"- Source mode : {source.get('source_mode') or 'UNKNOWN'}",
        f"- Data visibility : {source.get('data_visibility') or 'UNKNOWN'}",
        f"- Confidence cap : {source.get('confidence_cap')}",
        "- Limites : lecture B9 read-only, sans moteur, sans Telegram, sans dashboard, sans croisement B8.",
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
            f"**Zone :** {moment.get('zone_low')} -> {moment.get('zone_high')}",
            f"**Type interne :** `{moment.get('moment_type')}`",
            "",
            "**Ce qui se passe**",
            moment.get("reading_fr", ""),
            "",
            "**Pourquoi c'est important**",
            moment.get("why_it_matters_fr", ""),
            "",
            "**Comment B9 le voit**",
            moment.get("how_detected_fr", ""),
            "",
            "**Preuves**",
        ])
        for item in moment.get("evidence_fr", []):
            lines.append(f"- {item}")
        lines.extend(["", "**Limites**"])
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
) -> Dict[str, Path | Dict[str, Any]]:
    state = load_state(state_file)
    events = load_events(events_file)
    summary = summarize_events(
        state=state,
        events=events,
        state_file=state_file,
        events_file=events_file,
        max_gap_sec=max_gap_sec,
        price_merge_pips=price_merge_pips,
        pip_size=pip_size,
    )
    out = Path(output_dir)
    json_path = export_json(summary, out / "t009_sequence_summary.json")
    md_path = export_markdown(summary, out / "t009_sequence_summary.md")
    return {"summary": summary, "json_path": json_path, "markdown_path": md_path}


__all__ = [
    "NormalizedEvent",
    "Moment",
    "load_state",
    "load_events",
    "normalize_event",
    "normalize_events",
    "group_events",
    "classify_group",
    "build_moments",
    "summarize_events",
    "summarize_files",
    "export_json",
    "export_markdown",
    "render_markdown",
]
