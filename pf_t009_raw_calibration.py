"""B9 raw calibration layer V3.2 -> V3.5.

Read-only adapter between B9 M1_BAR_PROXY moments and MT5 raw ticks stored in
``tick_archive.db``. This module never writes to ``powerflow.db`` and does not
depend on UI, cockpit, message transport, or live engine modules.

Mission cap:
    B9 does not become raw-only. B9 learns when MT5 raw confirms, nuances,
    or corrects the proxy reading.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

MODULE_NAME = "pf_t009_raw_calibration"
VERSION = "V3.5"
DEFAULT_PIP_SIZE = 0.0001
DEFAULT_BROKER_TIME_SHIFT_MIN = 180
DEFAULT_RAW_CONFIDENCE_CAP = 0.55
DEFAULT_RAW_SOURCE_MODE = "HISTORICAL_RAW"
DEFAULT_RAW_DATA_VISIBILITY = "MT5_RAW_ALIGNED"
DEFAULT_BROKER = "OneFunded Capital Ltd."
RAW_LIMITS = ["broker-relative", "not central orderbook", "no participant identification"]

RAW_TEXTURE_ROLES = {
    "RAW_PROGRESS_CONFIRMED",
    "RAW_DWELL_CONFIRMED",
    "RAW_ROTATION_CONFIRMED",
    "RAW_FRICTION_CONFIRMED",
    "RAW_PROXY_DIVERGENCE",
    "RAW_UNAVAILABLE",
    "ZERO_DURATION_MOMENT",
}

PROGRESSIVE_WAVE_STATES = {
    "PROGRESSIVE_WAVE_CONFIRMED",
    "PROGRESSIVE_WAVE_WEAK_RAW",
    "PROGRESSIVE_WAVE_ROTATIONAL",
    "PROGRESSIVE_WAVE_PROXY_ONLY",
    "PROJECTION_DECAY",
}


@dataclass(frozen=True)
class RawCalibrationConfig:
    tick_db_path: Optional[str] = None
    symbol: str = "GBPUSD"
    broker: str = DEFAULT_BROKER
    broker_time_shift_min: int = DEFAULT_BROKER_TIME_SHIFT_MIN
    raw_source_mode: str = DEFAULT_RAW_SOURCE_MODE
    raw_data_visibility: str = DEFAULT_RAW_DATA_VISIBILITY
    raw_confidence_cap: float = DEFAULT_RAW_CONFIDENCE_CAP
    pip_size: float = DEFAULT_PIP_SIZE
    minimum_full_coverage_ratio: float = 0.70
    dwell_range_pips: float = 2.5
    rotation_range_to_delta_ratio: float = 1.35
    friction_spread_pips: float = 0.60
    friction_gap_ms: int = 10_000


@dataclass
class RawMetrics:
    raw_coverage: str
    raw_source_mode: str
    raw_data_visibility: str
    broker: str
    broker_time_shift_min: int
    raw_confidence_cap: float
    raw_limits: List[str]
    raw_tick_count: int = 0
    raw_delta_pips: Optional[float] = None
    raw_range_pips: Optional[float] = None
    raw_spread_avg_pips: Optional[float] = None
    raw_gap_max_ms: Optional[int] = None
    raw_texture_role: str = "RAW_UNAVAILABLE"
    proxy_vs_raw_verdict: str = "RAW_UNAVAILABLE"
    raw_window_start_mt5: Optional[str] = None
    raw_window_end_mt5: Optional[str] = None
    aligned_window_start_mt4_plus_3h: Optional[str] = None
    aligned_window_end_mt4_plus_3h: Optional[str] = None
    zero_duration_status: Optional[str] = None
    progressive_wave_state: Optional[str] = None


def parse_dt(value: Any) -> Optional[datetime]:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, (int, float)):
        numeric = float(value)
        if numeric > 10_000_000_000:
            numeric /= 1000.0
        dt = datetime.fromtimestamp(numeric, tz=timezone.utc)
    else:
        text = str(value).strip().replace("Z", "+00:00")
        if not text:
            return None
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            try:
                dt = datetime.fromisoformat(text.replace(" ", "T"))
            except ValueError:
                return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def iso_utc(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def round_or_none(value: Optional[float], digits: int = 4) -> Optional[float]:
    if value is None:
        return None
    return round(float(value), digits)


def _get_moment_time(moment: Mapping[str, Any], key: str) -> Optional[datetime]:
    for candidate in (key, key.replace("time_", ""), f"{key}_utc"):
        if candidate in moment:
            dt = parse_dt(moment.get(candidate))
            if dt is not None:
                return dt
    return None


def _proxy_delta(moment: Mapping[str, Any]) -> float:
    for key in ("center_delta_pips", "proxy_delta_pips", "delta_pips"):
        value = to_float(moment.get(key))
        if value is not None:
            return value
    start = to_float(moment.get("center_start"))
    end = to_float(moment.get("center_end"))
    if start is not None and end is not None:
        return (end - start) / DEFAULT_PIP_SIZE
    return 0.0


def _moment_type(moment: Mapping[str, Any]) -> str:
    return str(moment.get("moment_type") or moment.get("type") or moment.get("label") or "")


def _is_progressive(moment: Mapping[str, Any]) -> bool:
    text = f"{_moment_type(moment)} {moment.get('label_fr', '')} {moment.get('scene_role', '')}".upper()
    return "PROGRESSIVE_WAVE" in text or "VAGUE PROGRESSIVE" in text


def _is_projection_decay(moment: Mapping[str, Any]) -> bool:
    text = f"{_moment_type(moment)} {moment.get('label_fr', '')} {moment.get('scene_role', '')}".upper()
    return "PROJECTION_DECAY" in text or "PROJECTION DECAY" in text


def _connect_read_only(db_path: str | Path) -> sqlite3.Connection:
    p = Path(db_path)
    uri = p.resolve().as_uri() + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def _read_raw_ticks(
    db_path: str | Path,
    symbol: str,
    source_mode: str,
    raw_start: datetime,
    raw_end: datetime,
) -> List[sqlite3.Row]:
    con = _connect_read_only(db_path)
    con.row_factory = sqlite3.Row
    try:
        cur = con.cursor()
        cur.execute(
            """
            SELECT ts_utc, bid, ask, mid, spread, gap_ms, time_msc
            FROM tick_stream
            WHERE symbol = ?
              AND source_mode = ?
              AND ts_utc >= ?
              AND ts_utc < ?
            ORDER BY ts_utc, capture_seq
            """,
            (symbol, source_mode, iso_utc(raw_start), iso_utc(raw_end)),
        )
        return list(cur.fetchall())
    finally:
        con.close()


def _coverage_from_ticks(ticks: Sequence[sqlite3.Row], raw_start: datetime, raw_end: datetime, cfg: RawCalibrationConfig) -> str:
    if not ticks:
        return "MISSING"
    total_seconds = max((raw_end - raw_start).total_seconds(), 1.0)
    first = parse_dt(ticks[0]["ts_utc"])
    last = parse_dt(ticks[-1]["ts_utc"])
    if first is None or last is None:
        return "PARTIAL"
    observed = max((last - first).total_seconds(), 0.0)
    return "FULL" if observed / total_seconds >= cfg.minimum_full_coverage_ratio else "PARTIAL"


def _mid(row: Mapping[str, Any]) -> Optional[float]:
    mid = to_float(row["mid"])
    if mid is not None and mid != 0.0:
        return mid
    bid = to_float(row["bid"])
    ask = to_float(row["ask"])
    if bid is not None and ask is not None and bid != 0.0 and ask != 0.0:
        return (bid + ask) / 2.0
    return None


def _spread_pips(row: Mapping[str, Any], pip_size: float) -> Optional[float]:
    spread = to_float(row["spread"])
    if spread is None or spread == 0.0:
        bid = to_float(row["bid"])
        ask = to_float(row["ask"])
        if bid is not None and ask is not None and ask >= bid:
            spread = ask - bid
    if spread is None:
        return None
    return spread / pip_size


def _gap_ms_values(ticks: Sequence[sqlite3.Row]) -> List[int]:
    gaps: List[int] = []
    prev_msc: Optional[int] = None
    for row in ticks:
        gap = row["gap_ms"] if "gap_ms" in row.keys() else None
        if gap is not None:
            try:
                gaps.append(int(gap))
                continue
            except (TypeError, ValueError):
                pass
        msc = row["time_msc"] if "time_msc" in row.keys() else None
        try:
            current = int(msc) if msc is not None else None
        except (TypeError, ValueError):
            current = None
        if current is not None and prev_msc is not None:
            gaps.append(max(current - prev_msc, 0))
        if current is not None:
            prev_msc = current
    return gaps


def classify_raw_texture(
    moment: Mapping[str, Any],
    raw_delta_pips: Optional[float],
    raw_range_pips: Optional[float],
    raw_spread_avg_pips: Optional[float],
    raw_gap_max_ms: Optional[int],
    cfg: RawCalibrationConfig,
) -> Tuple[str, str, Optional[str]]:
    proxy_delta = _proxy_delta(moment)
    raw_delta = raw_delta_pips or 0.0
    raw_range = raw_range_pips or 0.0

    if _is_projection_decay(moment):
        return "RAW_FRICTION_CONFIRMED", "CONFIRMED_BY_RAW", "PROJECTION_DECAY"

    friction = False
    if raw_spread_avg_pips is not None and raw_spread_avg_pips >= cfg.friction_spread_pips:
        friction = True
    if raw_gap_max_ms is not None and raw_gap_max_ms >= cfg.friction_gap_ms:
        friction = True

    same_sign = (proxy_delta == 0 and abs(raw_delta) < 0.1) or (proxy_delta * raw_delta > 0)
    if _is_progressive(moment):
        if abs(raw_delta) < max(1.5, abs(proxy_delta) * 0.35):
            if raw_range >= max(4.0, abs(raw_delta) * cfg.rotation_range_to_delta_ratio):
                return "RAW_ROTATION_CONFIRMED", "NUANCED_BY_RAW", "PROGRESSIVE_WAVE_ROTATIONAL"
            return "RAW_PROXY_DIVERGENCE", "NUANCED_BY_RAW", "PROGRESSIVE_WAVE_WEAK_RAW"
        if not same_sign:
            return "RAW_PROXY_DIVERGENCE", "NUANCED_BY_RAW", "PROGRESSIVE_WAVE_WEAK_RAW"
        if raw_range >= max(4.0, abs(raw_delta) * cfg.rotation_range_to_delta_ratio):
            return "RAW_ROTATION_CONFIRMED", "NUANCED_BY_RAW", "PROGRESSIVE_WAVE_ROTATIONAL"
        return "RAW_PROGRESS_CONFIRMED", "CONFIRMED_BY_RAW", "PROGRESSIVE_WAVE_CONFIRMED"

    if friction:
        return "RAW_FRICTION_CONFIRMED", "CONFIRMED_BY_RAW", None
    if raw_range <= cfg.dwell_range_pips and abs(raw_delta) <= cfg.dwell_range_pips:
        return "RAW_DWELL_CONFIRMED", "CONFIRMED_BY_RAW", None
    if proxy_delta and not same_sign and abs(raw_delta) >= 1.0:
        return "RAW_PROXY_DIVERGENCE", "NUANCED_BY_RAW", None
    if raw_range >= max(4.0, abs(raw_delta) * cfg.rotation_range_to_delta_ratio):
        return "RAW_ROTATION_CONFIRMED", "NUANCED_BY_RAW", None
    return "RAW_PROGRESS_CONFIRMED", "CONFIRMED_BY_RAW", None


def calibrate_moment_with_raw(moment: Mapping[str, Any], cfg: RawCalibrationConfig) -> Dict[str, Any]:
    enriched = dict(moment)
    start = _get_moment_time(moment, "time_start")
    end = _get_moment_time(moment, "time_end")

    base = RawMetrics(
        raw_coverage="MISSING",
        raw_source_mode=cfg.raw_source_mode,
        raw_data_visibility=cfg.raw_data_visibility,
        broker=cfg.broker,
        broker_time_shift_min=cfg.broker_time_shift_min,
        raw_confidence_cap=cfg.raw_confidence_cap,
        raw_limits=list(RAW_LIMITS),
    )

    if start is None or end is None:
        enriched.update(asdict(base))
        enriched["raw_limits"] = list(RAW_LIMITS) + ["missing moment timestamp"]
        return enriched

    raw_start = start - timedelta(minutes=cfg.broker_time_shift_min)
    raw_end = end - timedelta(minutes=cfg.broker_time_shift_min)
    base.raw_window_start_mt5 = iso_utc(raw_start)
    base.raw_window_end_mt5 = iso_utc(raw_end)
    base.aligned_window_start_mt4_plus_3h = iso_utc(raw_start + timedelta(minutes=cfg.broker_time_shift_min))
    base.aligned_window_end_mt4_plus_3h = iso_utc(raw_end + timedelta(minutes=cfg.broker_time_shift_min))

    if raw_end <= raw_start:
        base.raw_coverage = "PARTIAL"
        base.raw_texture_role = "ZERO_DURATION_MOMENT"
        base.proxy_vs_raw_verdict = "ZERO_DURATION_MOMENT"
        base.zero_duration_status = "ZERO_DURATION_MOMENT"
        if _is_progressive(moment):
            base.progressive_wave_state = "PROGRESSIVE_WAVE_PROXY_ONLY"
        enriched.update(asdict(base))
        return enriched

    if not cfg.tick_db_path or not Path(cfg.tick_db_path).exists():
        base.raw_limits = list(RAW_LIMITS) + ["tick_archive.db unavailable"]
        enriched.update(asdict(base))
        return enriched

    ticks = _read_raw_ticks(cfg.tick_db_path, cfg.symbol, cfg.raw_source_mode, raw_start, raw_end)
    base.raw_tick_count = len(ticks)
    base.raw_coverage = _coverage_from_ticks(ticks, raw_start, raw_end, cfg)

    if not ticks:
        if _is_progressive(moment):
            base.progressive_wave_state = "PROGRESSIVE_WAVE_PROXY_ONLY"
        enriched.update(asdict(base))
        return enriched

    mids = [m for m in (_mid(row) for row in ticks) if m is not None]
    spreads = [s for s in (_spread_pips(row, cfg.pip_size) for row in ticks) if s is not None]
    gaps = _gap_ms_values(ticks)
    if mids:
        base.raw_delta_pips = round((mids[-1] - mids[0]) / cfg.pip_size, 4)
        base.raw_range_pips = round((max(mids) - min(mids)) / cfg.pip_size, 4)
    if spreads:
        base.raw_spread_avg_pips = round(mean(spreads), 4)
    if gaps:
        base.raw_gap_max_ms = max(gaps)

    role, verdict, progressive_state = classify_raw_texture(
        moment,
        base.raw_delta_pips,
        base.raw_range_pips,
        base.raw_spread_avg_pips,
        base.raw_gap_max_ms,
        cfg,
    )
    base.raw_texture_role = role
    base.proxy_vs_raw_verdict = verdict
    base.progressive_wave_state = progressive_state
    enriched.update(asdict(base))
    return enriched


def calibrate_summary_with_raw(summary: Mapping[str, Any], cfg: RawCalibrationConfig) -> Dict[str, Any]:
    output = dict(summary)
    moments = list(output.get("moments") or [])
    calibrated = [calibrate_moment_with_raw(moment, cfg) for moment in moments if isinstance(moment, Mapping)]
    output["moments"] = calibrated
    output["raw_calibration"] = {
        "module": MODULE_NAME,
        "version": VERSION,
        "raw_source_mode": cfg.raw_source_mode,
        "raw_data_visibility": cfg.raw_data_visibility,
        "broker": cfg.broker,
        "broker_time_shift_min": cfg.broker_time_shift_min,
        "raw_confidence_cap": cfg.raw_confidence_cap,
        "raw_limits": list(RAW_LIMITS),
        "tick_db_path": cfg.tick_db_path,
        "symbol": cfg.symbol,
        "mode": "read-only",
        "cap": "B9 ne devient pas raw-only : le raw confirme, nuance ou corrige la lecture proxy.",
    }
    return output


def load_json(path: str | Path) -> Dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def export_json(data: Mapping[str, Any], path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def render_raw_calibration_markdown(summary: Mapping[str, Any]) -> str:
    raw_meta = summary.get("raw_calibration", {}) if isinstance(summary.get("raw_calibration"), Mapping) else {}
    moments = summary.get("moments", []) if isinstance(summary.get("moments"), list) else []
    lines = [
        "# B9 Proxy vs Raw — Calibration V3.2/V3.5",
        "",
        "## Résumé source-aware",
        f"- Module : {raw_meta.get('module', MODULE_NAME)}",
        f"- Version : {raw_meta.get('version', VERSION)}",
        f"- Source raw : {raw_meta.get('raw_source_mode', DEFAULT_RAW_SOURCE_MODE)}",
        f"- Visibilité raw : {raw_meta.get('raw_data_visibility', DEFAULT_RAW_DATA_VISIBILITY)}",
        f"- Broker : {raw_meta.get('broker', DEFAULT_BROKER)}",
        f"- Décalage broker : {raw_meta.get('broker_time_shift_min', DEFAULT_BROKER_TIME_SHIFT_MIN)} min",
        f"- Confidence cap raw : {raw_meta.get('raw_confidence_cap', DEFAULT_RAW_CONFIDENCE_CAP)}",
        "- Limites : broker-relative, not central orderbook, no participant identification",
        "- Règle : B9 ne devient pas raw-only ; le raw confirme, nuance ou corrige le proxy.",
        "",
        "## Moments calibrés",
        "",
        "| Moment | Proxy | Raw MT5 | Ticks | Raw delta | Raw range | Spread avg | Gap max | Rôle raw | Verdict | Progressive state |",
        "|---|---|---|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for m in moments:
        if not isinstance(m, Mapping):
            continue
        label = str(m.get("label_fr") or m.get("moment_type") or m.get("moment_id") or "moment")
        proxy_window = f"{m.get('time_start')} -> {m.get('time_end')}"
        raw_window = f"{m.get('raw_window_start_mt5')} -> {m.get('raw_window_end_mt5')}"
        lines.append(
            "| "
            + " | ".join(
                [
                    label.replace("|", "/"),
                    proxy_window.replace("|", "/"),
                    raw_window.replace("|", "/"),
                    str(m.get("raw_tick_count")),
                    str(m.get("raw_delta_pips")),
                    str(m.get("raw_range_pips")),
                    str(m.get("raw_spread_avg_pips")),
                    str(m.get("raw_gap_max_ms")),
                    str(m.get("raw_texture_role")),
                    str(m.get("proxy_vs_raw_verdict")),
                    str(m.get("progressive_wave_state") or ""),
                ]
            )
            + " |"
        )
    lines.extend([
        "",
        "## Contraintes respectées",
        "- Read-only sur tick_archive.db via mode=ro.",
        "- Aucune écriture powerflow.db.",
        "- Aucun import dashboard / cockpit / telegram.",
        "- Aucun ordre directionnel.",
        "- Footprint exact non affirmé : le raw reste broker-relative.",
    ])
    return "\n".join(lines) + "\n"


def export_markdown(data: Mapping[str, Any], path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render_raw_calibration_markdown(data), encoding="utf-8")
    return p


__all__ = [
    "RawCalibrationConfig",
    "RawMetrics",
    "calibrate_moment_with_raw",
    "calibrate_summary_with_raw",
    "classify_raw_texture",
    "render_raw_calibration_markdown",
    "export_json",
    "export_markdown",
]
