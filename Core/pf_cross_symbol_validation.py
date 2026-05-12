"""B8 Cross-Symbol Validation — PowerFlow V7.

Purpose
-------
Validate whether a currency move observed on one pair is a true global
currency driver or only the inverse leg of another currency weakness.

Doctrine
--------
This module is a perception engine. It names and qualifies a driver.
It never emits BUY/SELL instructions and never writes to the database.
"""

from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

try:
    import numpy as np
except Exception:  # pragma: no cover - numpy should be available in runtime
    np = None


DEFAULT_CROSS_MAP: Dict[str, List[str]] = {
    "GBP": ["GBPUSD", "GBPEUR", "GBPJPY", "GBPCHF", "GBPCAD", "GBPAUD"],
    "EUR": ["EURUSD", "EURGBP", "EURJPY", "EURCHF", "EURCAD", "EURAUD"],
    "USD": ["USDJPY", "USDCHF", "USDCAD", "AUDUSD", "GBPUSD", "EURUSD"],
    "JPY": ["GBPJPY", "EURJPY", "USDJPY", "CHFJPY", "CADJPY", "AUDJPY"],
    "CHF": ["GBPCHF", "EURCHF", "USDCHF", "CHFJPY", "CADCHF", "AUDCHF"],
    "CAD": ["GBPCAD", "EURCAD", "USDCAD", "CADJPY", "CADCHF", "AUDCAD"],
    "AUD": ["GBPAUD", "EURAUD", "AUDUSD", "AUDJPY", "AUDCHF", "AUDCAD"],
}

# Classification thresholds are intentionally named and centralized.
VERY_STRONG_ANGLE = 60.0
STRONG_ANGLE = 45.0
NEUTRAL_ANGLE = 20.0
HIGH_CONSISTENCY = 0.80
MEDIUM_CONSISTENCY = 0.70
MINIMUM_USABLE_PAIRS = 2


@dataclass
class CrossValidationMetrics:
    """Metrics for one validated currency, for example GBP."""

    symbol: str
    angles: Dict[str, float]
    mean_angle: float
    std_angle: float
    consistency_score: float
    global_strength: str
    confidence: float


@dataclass
class DriverDetection:
    """Verdict on the real observed driver."""

    primary_driver: str
    secondary_driver: Optional[str]
    confidence: float
    evidence: Dict


@dataclass
class CrossValidationState:
    """Complete B8 state output."""

    timestamp: str
    symbol: str
    timeframe: int
    metrics: CrossValidationMetrics
    driver_detection: DriverDetection
    cross_pair_details: Dict[str, float]
    alert_triggered: bool
    alert_type: Optional[str]


class CrossValidationError(RuntimeError):
    """Raised when B8 cannot compute a usable state."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _open_readonly(db_path: str) -> sqlite3.Connection:
    """Open SQLite DB in read-only mode, as required for pf_* modules."""

    path = Path(db_path)
    if not path.exists():
        raise CrossValidationError(f"Database not found: {db_path}")
    return sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)


def _table_columns(conn: sqlite3.Connection, table_name: str) -> List[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return [str(row[1]) for row in rows]


def _detect_time_column(columns: Sequence[str]) -> str:
    for candidate in ("timestamp", "created_at", "time", "datetime"):
        if candidate in columns:
            return candidate
    raise CrossValidationError(
        "force_snapshots requires a timestamp-like column: timestamp or created_at"
    )


def _value_at(row: sqlite3.Row, column_names: Sequence[str], fallback: float = 0.0) -> float:
    for column in column_names:
        if column in row.keys() and row[column] is not None:
            try:
                value = float(row[column])
                if math.isfinite(value):
                    return value
            except (TypeError, ValueError):
                continue
    return fallback


def _signed_angle_for_pair(base_symbol: str, pair: str, raw_angle: float) -> float:
    """Normalize pair angle so positive means base_symbol strength.

    If validating USD and the available pair is GBPUSD, a positive pair angle
    expresses GBP vs USD, therefore USD strength is the inverse.
    """

    symbol = base_symbol.upper()
    pair = pair.upper()
    if pair.startswith(symbol):
        return raw_angle
    if pair.endswith(symbol):
        return -raw_angle
    return raw_angle


def _fallback_angle_from_prices(rows: Sequence[sqlite3.Row]) -> Optional[float]:
    """Estimate an angle from close/open when B3 angle columns are absent.

    This is a graceful fallback for tests or older DB snapshots. Production B8
    should preferably consume B3 angle columns if present.
    """

    if len(rows) < 2:
        return None
    first = rows[-1]
    last = rows[0]
    keys = set(last.keys())
    close_col = "close" if "close" in keys else None
    open_col = "open" if "open" in keys else None
    if close_col is None and open_col is None:
        return None
    try:
        start = float(first[close_col or open_col])
        end = float(last[close_col or open_col])
    except (TypeError, ValueError):
        return None
    if start == 0:
        return None
    pct_change = (end - start) / abs(start)
    # Scale percentage change into a bounded perceptive angle.
    return max(-89.0, min(89.0, math.degrees(math.atan(pct_change * 1000.0))))


def extract_angles_for_symbol(
    symbol: str,
    db_path: str,
    timeframe: int,
    window: int = 20,
    cross_map: Optional[Dict[str, List[str]]] = None,
) -> Dict[str, float]:
    """Read latest B3-like angles for all available crosses of a currency.

    The function first looks for angle columns produced by the kinematics layer.
    Supported column names include angle_kalman, angle, force_angle,
    slope_angle, and kalman_angle. When no angle column exists, it estimates a
    fallback angle from price movement if OHLC fields are present.
    """

    symbol = symbol.upper()
    pairs = (cross_map or DEFAULT_CROSS_MAP).get(symbol)
    if not pairs:
        raise CrossValidationError(f"No cross-pair map configured for symbol {symbol}")

    conn = _open_readonly(db_path)
    conn.row_factory = sqlite3.Row
    try:
        columns = _table_columns(conn, "force_snapshots")
        if not columns:
            raise CrossValidationError("Table force_snapshots not found or has no columns")
        time_column = _detect_time_column(columns)
        placeholders = ",".join("?" for _ in pairs)
        query = (
            f"SELECT * FROM force_snapshots "
            f"WHERE symbol IN ({placeholders}) AND timeframe = ? "
            f"ORDER BY {time_column} DESC"
        )
        rows = conn.execute(query, [*pairs, timeframe]).fetchall()
    finally:
        conn.close()

    by_pair: Dict[str, List[sqlite3.Row]] = {pair: [] for pair in pairs}
    for row in rows:
        pair = str(row["symbol"]).upper()
        if pair in by_pair and len(by_pair[pair]) < window:
            by_pair[pair].append(row)

    angle_columns = (
        "angle_kalman",
        "kalman_angle",
        "angle",
        "force_angle",
        "slope_angle",
        "angle_deg",
        "angle_degrees",
    )

    angles: Dict[str, float] = {}
    for pair, pair_rows in by_pair.items():
        if not pair_rows:
            continue
        latest = pair_rows[0]
        if any(col in latest.keys() for col in angle_columns):
            raw = _value_at(latest, angle_columns)
        else:
            fallback = _fallback_angle_from_prices(pair_rows)
            if fallback is None:
                continue
            raw = fallback
        angles[pair] = round(_signed_angle_for_pair(symbol, pair, raw), 4)

    if len(angles) < MINIMUM_USABLE_PAIRS:
        raise CrossValidationError(
            f"Not enough usable cross pairs for {symbol}: {len(angles)} found, "
            f"minimum {MINIMUM_USABLE_PAIRS} required"
        )
    return angles


def calculate_consistency_score(angles: Dict[str, float]) -> float:
    """Return 0-1 score measuring whether all normalized angles cohere."""

    values = [float(v) for v in angles.values() if math.isfinite(float(v))]
    if not values:
        return 0.0
    if len(values) == 1:
        return 1.0
    if np is not None:
        mean_abs = float(np.mean(np.abs(values)))
        std = float(np.std(values))
    else:  # pragma: no cover
        mean_abs = sum(abs(v) for v in values) / len(values)
        mean = sum(values) / len(values)
        std = math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))
    if mean_abs < 1e-9:
        return 1.0 if std < 1e-9 else 0.0
    score = 1.0 - (std / mean_abs)
    return round(max(0.0, min(1.0, score)), 4)


def classify_global_strength(mean_angle: float, consistency_score: float) -> str:
    """Classify global currency strength from mean angle and coherence."""

    if mean_angle > VERY_STRONG_ANGLE and consistency_score > HIGH_CONSISTENCY:
        return "VERY_STRONG"
    if mean_angle > STRONG_ANGLE and consistency_score > MEDIUM_CONSISTENCY:
        return "STRONG"
    if abs(mean_angle) < NEUTRAL_ANGLE and consistency_score > 0.60:
        return "NEUTRAL"
    if mean_angle < -VERY_STRONG_ANGLE and consistency_score > HIGH_CONSISTENCY:
        return "VERY_WEAK"
    if mean_angle < -STRONG_ANGLE and consistency_score > MEDIUM_CONSISTENCY:
        return "WEAK"
    return "MIXED_SIGNAL"


def _driver_from_global_strength(symbol: str, global_strength: str) -> str:
    if global_strength in {"VERY_STRONG", "STRONG"}:
        return f"{symbol}_STRENGTH"
    if global_strength in {"VERY_WEAK", "WEAK"}:
        return f"{symbol}_WEAKNESS"
    return "MIXED"


def _detect_counter_currency_outlier(symbol: str, angles: Dict[str, float]) -> Tuple[Optional[str], Dict]:
    """Detect cases like GBPUSD high while other GBP crosses are weak.

    Returns a likely counter-currency driver such as USD_WEAKNESS when a single
    counter currency explains the outlier better than global base strength.
    """

    evidence: Dict[str, object] = {}
    if len(angles) < 3:
        return None, {"outlier_check": "insufficient_pairs"}

    values = list(angles.values())
    median = sorted(values)[len(values) // 2]
    best_pair: Optional[str] = None
    best_gap = 0.0
    for pair, angle in angles.items():
        gap = angle - median
        if gap > best_gap:
            best_gap = gap
            best_pair = pair

    if not best_pair:
        return None, {"outlier_check": "none"}

    other_angles = [angle for pair, angle in angles.items() if pair != best_pair]
    other_mean = sum(other_angles) / len(other_angles)
    outlier_angle = angles[best_pair]

    evidence.update(
        {
            "outlier_pair": best_pair,
            "outlier_angle": round(outlier_angle, 4),
            "other_pairs_mean_angle": round(other_mean, 4),
            "outlier_gap_vs_other_mean": round(outlier_angle - other_mean, 4),
        }
    )

    # If validating GBP and GBPUSD is strongly positive while the rest of GBP
    # crosses are flat/negative, the clean perceptive label is USD_WEAKNESS.
    if outlier_angle >= STRONG_ANGLE and other_mean < NEUTRAL_ANGLE:
        if best_pair.startswith(symbol):
            counter = best_pair[len(symbol) :]
            evidence["reasoning"] = f"{best_pair} outlier: {symbol} strong mainly versus {counter}"
            return f"{counter}_WEAKNESS", evidence
        if best_pair.endswith(symbol):
            counter = best_pair[: -len(symbol)]
            evidence["reasoning"] = f"{best_pair} outlier: {symbol} move mostly reflects {counter} strength"
            return f"{counter}_STRENGTH", evidence

    return None, evidence


def detect_driver(symbol: str, angles: Dict[str, float], consistency_score: float) -> DriverDetection:
    """Detect the most plausible driver without turning it into an order."""

    symbol = symbol.upper()
    values = [float(v) for v in angles.values()]
    mean_angle = sum(values) / len(values) if values else 0.0
    global_strength = classify_global_strength(mean_angle, consistency_score)

    evidence: Dict[str, object] = {
        "angles": angles,
        "mean_angle": round(mean_angle, 4),
        "consistency_score": round(consistency_score, 4),
        "global_strength": global_strength,
        "all_pairs_positive": all(v > 0 for v in values),
        "all_pairs_negative": all(v < 0 for v in values),
        "method": "B8_cross_symbol_validation",
    }

    if global_strength in {"VERY_STRONG", "STRONG", "VERY_WEAK", "WEAK"}:
        driver = _driver_from_global_strength(symbol, global_strength)
        confidence = min(1.0, max(0.0, 0.55 + 0.45 * consistency_score))
        evidence["reasoning"] = f"{symbol} coherent across crosses; global_strength={global_strength}"
        return DriverDetection(driver, None, round(confidence, 4), evidence)

    outlier_driver, outlier_evidence = _detect_counter_currency_outlier(symbol, angles)
    evidence.update(outlier_evidence)
    if outlier_driver:
        # Outlier cases are useful but less robust than coherent global strength.
        dispersion_confidence = max(0.0, min(1.0, 1.0 - consistency_score))
        confidence = max(0.55, min(0.9, 0.50 + 0.40 * dispersion_confidence))
        return DriverDetection(outlier_driver, f"{symbol}_NOT_CONFIRMED", round(confidence, 4), evidence)

    evidence["reasoning"] = "Cross-pair angles are dispersed; no clean driver named."
    confidence = max(0.0, min(0.65, 1.0 - consistency_score))
    return DriverDetection("MIXED", None, round(confidence, 4), evidence)


def _confidence_from_metrics(mean_angle: float, consistency_score: float) -> float:
    magnitude_score = min(1.0, abs(mean_angle) / 75.0)
    return round(max(0.0, min(1.0, 0.35 * magnitude_score + 0.65 * consistency_score)), 4)


def validate_cross_symbol(
    symbol: str,
    db_path: str,
    timeframe: int,
    window: int = 20,
    cross_map: Optional[Dict[str, List[str]]] = None,
) -> CrossValidationState:
    """Full B8 pipeline: extract angles, compute metrics, detect driver."""

    symbol = symbol.upper()
    angles = extract_angles_for_symbol(symbol, db_path, timeframe, window, cross_map)
    values = [float(v) for v in angles.values()]
    mean_angle = float(np.mean(values)) if np is not None else sum(values) / len(values)
    std_angle = float(np.std(values)) if np is not None else math.sqrt(
        sum((v - mean_angle) ** 2 for v in values) / len(values)
    )
    consistency_score = calculate_consistency_score(angles)
    global_strength = classify_global_strength(mean_angle, consistency_score)
    confidence = _confidence_from_metrics(mean_angle, consistency_score)

    metrics = CrossValidationMetrics(
        symbol=symbol,
        angles=angles,
        mean_angle=round(mean_angle, 4),
        std_angle=round(std_angle, 4),
        consistency_score=consistency_score,
        global_strength=global_strength,
        confidence=confidence,
    )
    driver_detection = detect_driver(symbol, angles, consistency_score)

    state = CrossValidationState(
        timestamp=_utc_now(),
        symbol=symbol,
        timeframe=timeframe,
        metrics=metrics,
        driver_detection=driver_detection,
        cross_pair_details=angles,
        alert_triggered=False,
        alert_type=None,
    )

    alert = trigger_alert_if_needed(state)
    if alert:
        state.alert_triggered = True
        state.alert_type = alert.get("b8_alert_type")
    return state


def trigger_alert_if_needed(state: CrossValidationState) -> Optional[Dict]:
    """Return a perception alert when B8 has a useful named driver."""

    metrics = state.metrics
    driver = state.driver_detection

    alert_type: Optional[str] = None
    level = "INFO"
    if (
        driver.primary_driver.endswith("_STRENGTH")
        or driver.primary_driver.endswith("_WEAKNESS")
    ) and driver.confidence >= 0.80:
        alert_type = "DRIVER_CONFIRMED"
    elif driver.primary_driver != "MIXED" and driver.secondary_driver:
        alert_type = "DRIVER_CONTRADICTION"
    elif metrics.consistency_score < 0.50:
        alert_type = "MIXED_SIGNAL"
        level = "WATCH"

    if alert_type is None:
        return None

    readable = {
        "DRIVER_CONFIRMED": f"Driver confirmed: {driver.primary_driver}",
        "DRIVER_CONTRADICTION": f"Driver contradiction/context: {driver.primary_driver}",
        "MIXED_SIGNAL": "Mixed cross-symbol signal: no clean global driver",
    }[alert_type]

    return {
        "alert_type": "DRIVER_DETECTION_CONFIRMED" if alert_type == "DRIVER_CONFIRMED" else alert_type,
        "b8_alert_type": alert_type,
        "level": level,
        "maturity": "CONFIRMED" if alert_type != "MIXED_SIGNAL" else "CANDIDATE",
        "timestamp": state.timestamp,
        "symbol": state.symbol,
        "timeframe": state.timeframe,
        "message": readable,
        "driver": driver.primary_driver,
        "confidence": driver.confidence,
        "cross_validation_context": {
            "mean_angle": metrics.mean_angle,
            "std_angle": metrics.std_angle,
            "consistency_score": metrics.consistency_score,
            "global_strength": metrics.global_strength,
            "angles_by_pair": state.cross_pair_details,
            "evidence": driver.evidence,
        },
        "technical_risks": [],
        "note": "Perception context only. Trader filters and decides.",
    }


def state_to_dict(state: CrossValidationState) -> Dict:
    """Convert dataclass state to plain dict."""

    return asdict(state)


def state_to_json(state: CrossValidationState, pretty: bool = False) -> str:
    """Serialize state to JSON."""

    return json.dumps(state_to_dict(state), indent=2 if pretty else None, ensure_ascii=False)
