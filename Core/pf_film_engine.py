#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
pf_film_engine.py

PowerFlow V7.1 — Film Engine.

Role:
    Translate replay JSON frames and optional behavioral alert queue into a
    chronological Markdown film.

Doctrine:
    - No DB connection.
    - No cockpit import.
    - No trading decision.
    - No BUY/SELL.
    - No alert censorship.
    - Behavioral translation only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
import json


TimestampValue = str | datetime


DEFAULT_REPLAY_KEYS: Tuple[str, ...] = (
    "frames",
    "replay",
    "timeline",
    "snapshots",
    "items",
    "data",
)

DEFAULT_ALERT_KEYS: Tuple[str, ...] = (
    "alerts",
    "items",
    "queue",
    "behavioral_alert_queue",
)

DEFAULT_TIMESTAMP_FIELDS: Tuple[str, ...] = (
    "timestamp",
    "time",
    "created_at",
    "generated_at_utc",
    "frame_timestamp",
    "snapshot_timestamp",
)

DEFAULT_ENTITY_FIELDS: Tuple[str, ...] = (
    "currency",
    "devise",
    "symbol",
    "pair",
    "leader",
    "entity",
)

DEFAULT_TIMEFRAME_FIELDS: Tuple[str, ...] = (
    "timeframe",
    "tf",
    "period",
)


@dataclass(frozen=True)
class FilmEngineConfig:
    title: str = "PowerFlow Film"
    include_raw_evidence: bool = True
    m1_m5_angle_gap_threshold: float = 12.0
    strong_angle_threshold: float = 35.0
    compression_ratio_threshold: float = 0.70
    elastic_score_threshold: float = 0.65
    max_evidence_items: int = 5


@dataclass(frozen=True)
class FilmEvent:
    timestamp: datetime
    source: str
    scene_type: str
    title: str
    entity: str = "GLOBAL"
    timeframe: Optional[int] = None
    level: Optional[str] = None
    maturity: Optional[str] = None
    details: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    order: int = 0

    def sort_key(self) -> Tuple[datetime, int, str, str]:
        return (self.timestamp, self.order, self.entity, self.scene_type)


@dataclass
class FilmState:
    previous_angle_by_entity_tf: Dict[Tuple[str, int], float] = field(default_factory=dict)
    latest_m5_angle_by_entity: Dict[str, float] = field(default_factory=dict)
    latest_m5_speed_by_entity: Dict[str, str] = field(default_factory=dict)


def load_json_file(path: str | Path) -> Any:
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_utc_timestamp(value: Any) -> Optional[datetime]:
    if value is None:
        return None

    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return None

        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"

        try:
            dt = datetime.fromisoformat(normalized)
        except ValueError:
            return None
    else:
        return None

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def first_present(mapping: Dict[str, Any], fields: Sequence[str]) -> Optional[Any]:
    for field_name in fields:
        value = mapping.get(field_name)
        if value is not None and value != "":
            return value
    return None


def first_present_nested(mapping: Dict[str, Any], fields: Sequence[str]) -> Optional[Any]:
    direct = first_present(mapping, fields)
    if direct is not None:
        return direct

    for nested_key in (
        "payload",
        "frame",
        "snapshot",
        "kinematics",
        "energy_context",
        "regime_context",
        "session_context",
        "density",
        "temporal_density",
        "confluence",
    ):
        nested = mapping.get(nested_key)
        if isinstance(nested, dict):
            value = first_present_nested(nested, fields)
            if value is not None:
                return value

    return None


def extract_timestamp(item: Dict[str, Any]) -> Optional[datetime]:
    value = first_present_nested(item, DEFAULT_TIMESTAMP_FIELDS)
    return parse_utc_timestamp(value)


def extract_entity(item: Dict[str, Any]) -> str:
    value = first_present_nested(item, DEFAULT_ENTITY_FIELDS)
    if value is not None:
        return str(value)

    currencies = item.get("currencies")
    if isinstance(currencies, list) and currencies:
        return str(currencies[0])

    return "GLOBAL"


def parse_timeframe(value: Any) -> Optional[int]:
    if value is None:
        return None

    if isinstance(value, int):
        return value

    if isinstance(value, float) and value.is_integer():
        return int(value)

    if isinstance(value, str):
        cleaned = value.strip().upper().replace("TF", "").replace("M", "")
        if cleaned.isdigit():
            return int(cleaned)

    return None


def extract_timeframe(item: Dict[str, Any]) -> Optional[int]:
    value = first_present_nested(item, DEFAULT_TIMEFRAME_FIELDS)
    return parse_timeframe(value)


def extract_float(item: Dict[str, Any], fields: Sequence[str]) -> Optional[float]:
    value = first_present_nested(item, fields)
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def extract_bool(item: Dict[str, Any], fields: Sequence[str]) -> Optional[bool]:
    value = first_present_nested(item, fields)

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1", "y"}:
            return True
        if lowered in {"false", "no", "0", "n"}:
            return False

    return None


def extract_str(item: Dict[str, Any], fields: Sequence[str]) -> Optional[str]:
    value = first_present_nested(item, fields)
    if value is None:
        return None
    return str(value)


def normalize_record_list(payload: Any, candidate_keys: Sequence[str]) -> List[Dict[str, Any]]:
    if payload is None:
        return []

    if isinstance(payload, list):
        return [item if isinstance(item, dict) else {"raw_value": item} for item in payload]

    if isinstance(payload, dict):
        for key in candidate_keys:
            value = payload.get(key)
            if isinstance(value, list):
                return [item if isinstance(item, dict) else {"raw_value": item} for item in value]

        nested_payload = payload.get("payload")
        if nested_payload is not None:
            return normalize_record_list(nested_payload, candidate_keys)

        return [payload]

    return [{"raw_value": payload}]


def normalize_replay_frames(payload: Any) -> List[Dict[str, Any]]:
    return normalize_record_list(payload, DEFAULT_REPLAY_KEYS)


def normalize_alerts(payload: Any) -> List[Dict[str, Any]]:
    return normalize_record_list(payload, DEFAULT_ALERT_KEYS)


def compact_evidence(evidence: Dict[str, Any], max_items: int) -> Dict[str, Any]:
    cleaned: Dict[str, Any] = {}

    for key, value in evidence.items():
        if value is None:
            continue

        if isinstance(value, (str, int, float, bool)):
            cleaned[key] = value
        elif isinstance(value, list):
            cleaned[key] = value[:max_items]
        elif isinstance(value, dict):
            cleaned[key] = {
                str(k): v
                for k, v in list(value.items())[:max_items]
                if isinstance(v, (str, int, float, bool)) or v is None
            }

        if len(cleaned) >= max_items:
            break

    return cleaned


def detect_frame_events(
    frame: Dict[str, Any],
    state: FilmState,
    config: FilmEngineConfig,
    order: int,
) -> List[FilmEvent]:
    timestamp = extract_timestamp(frame)
    if timestamp is None:
        return []

    entity = extract_entity(frame)
    timeframe = extract_timeframe(frame)
    events: List[FilmEvent] = []

    angle = extract_float(frame, ("angle_kalman", "angle", "slope", "force_angle"))
    speed = extract_str(frame, ("speed_state", "speed", "velocity_state"))
    noise_ratio = extract_float(frame, ("noise_ratio", "noise"))
    first_detachment = extract_bool(frame, ("first_detachment", "first_detachment_micro"))
    acceleration = extract_float(frame, ("acceleration", "accel", "force_acceleration"))

    cycle_state = extract_str(frame, ("cycle_state", "temporal_state", "density_state"))
    compression_ratio = extract_float(frame, ("compression_ratio", "cycle_compression_ratio"))
    dominant_period = extract_float(frame, ("dominant_period_bars", "dominant_period"))

    elastic_score = extract_float(frame, ("elastic_tension_score", "elastic_score", "eie_score"))
    tension_signature = extract_str(frame, ("tension_signature", "energy_signature", "signature"))
    eie_state = extract_str(frame, ("eie_state", "elastic_state", "confluence_state"))
    zone_state = extract_str(frame, ("zone_state", "zone"))

    release_state = extract_str(frame, ("release_state", "release", "rupture_state"))
    regime = extract_str(frame, ("regime", "regime_state"))
    cascade_state = extract_str(frame, ("cascade_state", "sequence_velocity"))

    if first_detachment is True:
        details = ["Premier décrochage cinématique détecté."]
        if timeframe == 1:
            details.append("M1 expose une naissance de mouvement.")
        if speed:
            details.append(f"Vitesse: {speed}.")
        if angle is not None:
            details.append(f"Angle: {angle:.2f}.")
        if noise_ratio is not None:
            details.append(f"Noise ratio: {noise_ratio:.3f}.")

        events.append(
            FilmEvent(
                timestamp=timestamp,
                source="replay",
                scene_type="INFLEXION",
                title="Naissance d'une inflexion cinématique",
                entity=entity,
                timeframe=timeframe,
                details=details,
                evidence=compact_evidence(
                    {
                        "first_detachment": first_detachment,
                        "angle": angle,
                        "speed_state": speed,
                        "noise_ratio": noise_ratio,
                    },
                    config.max_evidence_items,
                ),
                order=order,
            )
        )

    if angle is not None and timeframe is not None:
        previous_key = (entity, timeframe)
        previous_angle = state.previous_angle_by_entity_tf.get(previous_key)
        state.previous_angle_by_entity_tf[previous_key] = angle

        if previous_angle is not None:
            delta_angle = angle - previous_angle
            if abs(delta_angle) >= config.strong_angle_threshold:
                direction = "accélération" if delta_angle > 0 else "décélération"
                events.append(
                    FilmEvent(
                        timestamp=timestamp,
                        source="replay",
                        scene_type="KINEMATIC_SHIFT",
                        title=f"Changement d'angle marqué: {direction}",
                        entity=entity,
                        timeframe=timeframe,
                        details=[
                            f"Angle précédent: {previous_angle:.2f}.",
                            f"Angle actuel: {angle:.2f}.",
                            f"Delta: {delta_angle:.2f}.",
                        ],
                        evidence=compact_evidence(
                            {
                                "previous_angle": previous_angle,
                                "current_angle": angle,
                                "delta_angle": delta_angle,
                            },
                            config.max_evidence_items,
                        ),
                        order=order,
                    )
                )

    if timeframe == 5 and angle is not None:
        state.latest_m5_angle_by_entity[entity] = angle
        if speed:
            state.latest_m5_speed_by_entity[entity] = speed

    if timeframe == 1 and angle is not None:
        m5_angle = state.latest_m5_angle_by_entity.get(entity)
        if m5_angle is not None:
            gap = angle - m5_angle
            if abs(gap) >= config.m1_m5_angle_gap_threshold:
                title = (
                    "M1 prend de l'avance sur M5"
                    if gap > 0
                    else "M1 se replie sous le relais M5"
                )
                events.append(
                    FilmEvent(
                        timestamp=timestamp,
                        source="replay",
                        scene_type="M1_M5_DESYNC",
                        title=title,
                        entity=entity,
                        timeframe=timeframe,
                        details=[
                            f"Angle M1: {angle:.2f}.",
                            f"Dernier angle M5 connu: {m5_angle:.2f}.",
                            f"Écart M1-M5: {gap:.2f}.",
                        ],
                        evidence=compact_evidence(
                            {
                                "m1_angle": angle,
                                "m5_angle": m5_angle,
                                "angle_gap": gap,
                            },
                            config.max_evidence_items,
                        ),
                        order=order,
                    )
                )

    if cycle_state:
        cycle_upper = cycle_state.upper()
        if "COMPRESS" in cycle_upper:
            details = ["Les oscillations temporelles se compriment."]
            if compression_ratio is not None:
                details.append(f"Compression ratio: {compression_ratio:.3f}.")
            if dominant_period is not None:
                details.append(f"Période dominante: {dominant_period:g} barres.")

            events.append(
                FilmEvent(
                    timestamp=timestamp,
                    source="replay",
                    scene_type="COMPRESSION",
                    title="Compression temporelle visible",
                    entity=entity,
                    timeframe=timeframe,
                    details=details,
                    evidence=compact_evidence(
                        {
                            "cycle_state": cycle_state,
                            "compression_ratio": compression_ratio,
                            "dominant_period_bars": dominant_period,
                        },
                        config.max_evidence_items,
                    ),
                    order=order,
                )
            )

        elif "EXPAND" in cycle_upper:
            events.append(
                FilmEvent(
                    timestamp=timestamp,
                    source="replay",
                    scene_type="EXPANSION",
                    title="Respiration temporelle en expansion",
                    entity=entity,
                    timeframe=timeframe,
                    details=["Les oscillations s'élargissent après compression ou rotation."],
                    evidence=compact_evidence(
                        {
                            "cycle_state": cycle_state,
                            "compression_ratio": compression_ratio,
                            "dominant_period_bars": dominant_period,
                        },
                        config.max_evidence_items,
                    ),
                    order=order,
                )
            )

    if compression_ratio is not None and compression_ratio >= config.compression_ratio_threshold:
        events.append(
            FilmEvent(
                timestamp=timestamp,
                source="replay",
                scene_type="COMPRESSION_RATIO",
                title="Compression ratio élevé",
                entity=entity,
                timeframe=timeframe,
                details=[f"Compression ratio: {compression_ratio:.3f}."],
                evidence=compact_evidence(
                    {"compression_ratio": compression_ratio},
                    config.max_evidence_items,
                ),
                order=order,
            )
        )

    if elastic_score is not None and elastic_score >= config.elastic_score_threshold:
        events.append(
            FilmEvent(
                timestamp=timestamp,
                source="replay",
                scene_type="ELASTIC_TENSION",
                title="Naissance d'une tension élastique",
                entity=entity,
                timeframe=timeframe,
                details=[f"Elastic score: {elastic_score:.3f}."],
                evidence=compact_evidence(
                    {
                        "elastic_tension_score": elastic_score,
                        "tension_signature": tension_signature,
                        "eie_state": eie_state,
                        "zone_state": zone_state,
                    },
                    config.max_evidence_items,
                ),
                order=order,
            )
        )

    if tension_signature:
        signature_upper = tension_signature.upper()
        if "ELASTIC" in signature_upper or "LOADED" in signature_upper:
            events.append(
                FilmEvent(
                    timestamp=timestamp,
                    source="replay",
                    scene_type="ELASTIC_SIGNATURE",
                    title="Signature d'élastique chargé",
                    entity=entity,
                    timeframe=timeframe,
                    details=[f"Signature: {tension_signature}."],
                    evidence=compact_evidence(
                        {"tension_signature": tension_signature},
                        config.max_evidence_items,
                    ),
                    order=order,
                )
            )

    if eie_state:
        eie_upper = eie_state.upper()
        if "EIE" in eie_upper or "ELASTIC" in eie_upper:
            events.append(
                FilmEvent(
                    timestamp=timestamp,
                    source="replay",
                    scene_type="EIE",
                    title="Zone élastique active",
                    entity=entity,
                    timeframe=timeframe,
                    details=[f"État EIE: {eie_state}."],
                    evidence=compact_evidence(
                        {
                            "eie_state": eie_state,
                            "elastic_score": elastic_score,
                            "zone_state": zone_state,
                        },
                        config.max_evidence_items,
                    ),
                    order=order,
                )
            )

    if release_state:
        release_upper = release_state.upper()
        if any(token in release_upper for token in ("RUPTURE", "RELEASE", "CONFIRMED", "ATTEMPT")):
            events.append(
                FilmEvent(
                    timestamp=timestamp,
                    source="replay",
                    scene_type="RELEASE",
                    title="Libération ou tentative de rupture",
                    entity=entity,
                    timeframe=timeframe,
                    details=[f"Release state: {release_state}."],
                    evidence=compact_evidence(
                        {"release_state": release_state},
                        config.max_evidence_items,
                    ),
                    order=order,
                )
            )

    if regime:
        regime_upper = regime.upper()
        if any(token in regime_upper for token in ("COMPRESSION", "TENDANCE", "RANGE", "TRANSITION")):
            events.append(
                FilmEvent(
                    timestamp=timestamp,
                    source="replay",
                    scene_type="REGIME",
                    title=f"Contexte régime: {regime}",
                    entity=entity,
                    timeframe=timeframe,
                    details=["Le régime HTF qualifie la scène courante."],
                    evidence=compact_evidence(
                        {"regime": regime},
                        config.max_evidence_items,
                    ),
                    order=order,
                )
            )

    if cascade_state:
        cascade_upper = cascade_state.upper()
        if "HIGH" in cascade_upper or "BUILDING" in cascade_upper:
            events.append(
                FilmEvent(
                    timestamp=timestamp,
                    source="replay",
                    scene_type="CASCADE",
                    title="Cascade d'événements en accélération",
                    entity=entity,
                    timeframe=timeframe,
                    details=[f"Cascade state: {cascade_state}."],
                    evidence=compact_evidence(
                        {"cascade_state": cascade_state},
                        config.max_evidence_items,
                    ),
                    order=order,
                )
            )

    if acceleration is not None and abs(acceleration) > 0:
        if abs(acceleration) >= 0.10:
            events.append(
                FilmEvent(
                    timestamp=timestamp,
                    source="replay",
                    scene_type="ACCELERATION",
                    title="Accélération mesurable du flux",
                    entity=entity,
                    timeframe=timeframe,
                    details=[f"Accélération: {acceleration:.6f}."],
                    evidence=compact_evidence(
                        {"acceleration": acceleration},
                        config.max_evidence_items,
                    ),
                    order=order,
                )
            )

    return events


def alert_title(alert_type: str) -> str:
    upper = alert_type.upper()

    if "FIRST_DETACHMENT" in upper:
        return "Alerte: premier détachement"
    if "EIE" in upper or "ELASTIC" in upper:
        return "Alerte: tension élastique"
    if "CYCLE_COMPRESS" in upper or "COMPRESSION" in upper:
        return "Alerte: compression active"
    if "CASCADE" in upper or "SEQUENCE_VELOCITY" in upper:
        return "Alerte: cascade d'événements"
    if "DIVERGENT" in upper:
        return "Alerte: divergence relationnelle"
    if "CODEPENDANT" in upper or "SYNCHRO" in upper:
        return "Alerte: coalition ou codépendance"
    if "REGIME" in upper:
        return "Alerte: contexte régime"
    if "RELEASE" in upper or "RUPTURE" in upper:
        return "Alerte: libération du flux"

    return f"Alerte: {alert_type}"


def detect_alert_events(
    alert: Dict[str, Any],
    config: FilmEngineConfig,
    order: int,
) -> List[FilmEvent]:
    timestamp = extract_timestamp(alert)
    if timestamp is None:
        return []

    alert_type = str(
        first_present_nested(alert, ("alert_type", "type", "event_type"))
        or "UNKNOWN_ALERT"
    )

    entity = extract_entity(alert)
    timeframe = extract_timeframe(alert)
    level = str(alert.get("level")) if alert.get("level") is not None else None
    maturity = str(alert.get("maturity")) if alert.get("maturity") is not None else None

    details: List[str] = [f"Type: {alert_type}."]

    if level:
        details.append(f"Niveau: {level}.")
    if maturity:
        details.append(f"Maturité: {maturity}.")

    capture_quality = extract_str(alert, ("capture_quality",))
    relay_quality = extract_str(alert, ("relay_quality",))
    if capture_quality:
        details.append(f"Capture: {capture_quality}.")
    if relay_quality:
        details.append(f"Relais: {relay_quality}.")

    technical_risks = alert.get("technical_risks")
    if isinstance(technical_risks, list) and technical_risks:
        details.append("Risques techniques: " + ", ".join(str(item) for item in technical_risks) + ".")

    next_watch = alert.get("next_watch")
    if isinstance(next_watch, list) and next_watch:
        details.append("À surveiller ensuite: " + ", ".join(str(item) for item in next_watch) + ".")

    evidence = compact_evidence(
        {
            "alert_type": alert_type,
            "level": level,
            "maturity": maturity,
            "capture_quality": capture_quality,
            "relay_quality": relay_quality,
            "technical_risks": technical_risks,
            "next_watch": next_watch,
        },
        config.max_evidence_items,
    )

    return [
        FilmEvent(
            timestamp=timestamp,
            source="alert_queue",
            scene_type="ALERT",
            title=alert_title(alert_type),
            entity=entity,
            timeframe=timeframe,
            level=level,
            maturity=maturity,
            details=details,
            evidence=evidence,
            order=order,
        )
    ]


def events_from_payloads(
    replay_payload: Any,
    alert_payload: Any | None = None,
    config: FilmEngineConfig | None = None,
) -> List[FilmEvent]:
    cfg = config or FilmEngineConfig()
    state = FilmState()

    replay_frames = normalize_replay_frames(replay_payload)
    alerts = normalize_alerts(alert_payload) if alert_payload is not None else []

    stamped_frames = [
        frame for frame in replay_frames if isinstance(frame, dict) and extract_timestamp(frame) is not None
    ]
    stamped_frames.sort(key=lambda item: extract_timestamp(item) or datetime.min.replace(tzinfo=timezone.utc))

    events: List[FilmEvent] = []

    for order, frame in enumerate(stamped_frames):
        events.extend(detect_frame_events(frame, state=state, config=cfg, order=order))

    base_order = len(stamped_frames) + 1

    for offset, alert in enumerate(alerts):
        if isinstance(alert, dict):
            events.extend(detect_alert_events(alert, config=cfg, order=base_order + offset))

    events.sort(key=lambda event: event.sort_key())
    return events


def format_timestamp(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%H:%M UTC")


def format_date(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")


def format_tf(timeframe: Optional[int]) -> str:
    if timeframe is None:
        return ""
    if timeframe < 60:
        return f"M{timeframe}"
    if timeframe % 60 == 0:
        hours = timeframe // 60
        return f"H{hours}"
    return f"TF{timeframe}"


def markdown_escape(value: Any) -> str:
    text = str(value)
    return text.replace("|", "\\|")


def render_event_line(event: FilmEvent, include_raw_evidence: bool) -> str:
    tf = format_tf(event.timeframe)
    prefix_parts = [format_timestamp(event.timestamp)]

    if event.entity:
        prefix_parts.append(event.entity)

    if tf:
        prefix_parts.append(tf)

    if event.level:
        prefix_parts.append(event.level)

    if event.maturity:
        prefix_parts.append(event.maturity)

    prefix = " / ".join(markdown_escape(part) for part in prefix_parts)

    line = f"- **{prefix}** — {markdown_escape(event.title)}"

    if event.details:
        line += "  \n  " + " ".join(markdown_escape(detail) for detail in event.details)

    if include_raw_evidence and event.evidence:
        evidence_parts = [
            f"`{markdown_escape(key)}={markdown_escape(value)}`"
            for key, value in event.evidence.items()
        ]
        line += "  \n  Evidence: " + ", ".join(evidence_parts)

    return line


def render_scene_summary(events: Sequence[FilmEvent]) -> str:
    if not events:
        return "Aucune scène détectée dans les données fournies."

    counter: Dict[str, int] = {}
    for event in events:
        counter[event.scene_type] = counter.get(event.scene_type, 0) + 1

    ordered = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    return ", ".join(f"{scene_type}: {count}" for scene_type, count in ordered)


def render_markdown_film(
    events: Sequence[FilmEvent],
    config: FilmEngineConfig | None = None,
) -> str:
    cfg = config or FilmEngineConfig()

    generated_at = datetime.now(timezone.utc)
    dates = sorted({format_date(event.timestamp) for event in events})
    date_label = ", ".join(dates) if dates else "n/a"

    lines: List[str] = [
        f"# {cfg.title}",
        "",
        f"**Generated at UTC:** {generated_at.isoformat()}",
        f"**Film dates:** {date_label}",
        f"**Scenes detected:** {len(events)}",
        "",
        "## Synthèse",
        "",
        render_scene_summary(events),
        "",
        "## Frise chronologique",
        "",
    ]

    if not events:
        lines.append("_Aucune scène exploitable détectée._")
        lines.append("")
        return "\n".join(lines)

    current_date: Optional[str] = None

    for event in events:
        event_date = format_date(event.timestamp)
        if event_date != current_date:
            current_date = event_date
            lines.extend(["", f"### {current_date}", ""])

        lines.append(render_event_line(event, include_raw_evidence=cfg.include_raw_evidence))

    lines.extend(
        [
            "",
            "## Lecture PowerFlow",
            "",
            "Le film traduit les frames et alertes en scènes comportementales.",
            "Il expose les tensions, compressions, inflexions, désynchronisations M1/M5, cascades et libérations détectées.",
            "Il ne filtre pas les alertes et ne transforme aucune perception en décision.",
            "",
        ]
    )

    return "\n".join(lines)


def generate_film_markdown(
    replay_payload: Any,
    alert_payload: Any | None = None,
    config: FilmEngineConfig | None = None,
) -> str:
    cfg = config or FilmEngineConfig()
    events = events_from_payloads(
        replay_payload=replay_payload,
        alert_payload=alert_payload,
        config=cfg,
    )
    return render_markdown_film(events, config=cfg)


def generate_film_markdown_from_files(
    replay_file: str | Path,
    queue_file: str | Path | None = None,
    config: FilmEngineConfig | None = None,
) -> str:
    replay_payload = load_json_file(replay_file)
    alert_payload = load_json_file(queue_file) if queue_file else None

    return generate_film_markdown(
        replay_payload=replay_payload,
        alert_payload=alert_payload,
        config=config,
    )


__all__ = [
    "FilmEngineConfig",
    "FilmEvent",
    "generate_film_markdown",
    "generate_film_markdown_from_files",
    "events_from_payloads",
    "normalize_replay_frames",
    "normalize_alerts",
]