# pf_market_open_validator.py
"""
PowerFlow V7.1 - Market Open Validator

Role:
    Validate that B4, B5 and EIE outputs are not frozen during market-open flow.

Contract:
    - Strict read-only SQLite connection.
    - No cockpit_* import.
    - No DB writes.
    - Can validate from JSON outputs or compute DB proxy metrics.

Output shape:
    {
      "b4": {"status": "PASS/FAIL", ...},
      "b5": {"status": "PASS/FAIL", ...},
      "eie": {"status": "PASS/FAIL", ...}
    }
"""

from __future__ import annotations

import contextlib
import dataclasses
import datetime as dt
import itertools
import json
import logging
import math
import os
import sqlite3
import statistics
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

LOGGER = logging.getLogger(__name__)

DEFAULT_TABLE = "force_snapshots"
DEFAULT_TIMEFRAMES: tuple[int, ...] = (1, 5, 15)
DEFAULT_TIMESTAMP_COLUMNS: tuple[str, ...] = (
    "timestamp",
    "ts",
    "datetime",
    "created_at",
    "time",
    "bar_time",
    "snapshot_time",
)
DEFAULT_CURRENCY_COLUMNS: tuple[str, ...] = (
    "USD",
    "EUR",
    "GBP",
    "JPY",
    "CHF",
    "CAD",
    "AUD",
    "NZD",
)

UTC = dt.timezone.utc


class MarketOpenValidatorError(RuntimeError):
    """Raised when validation cannot inspect its inputs safely."""


@dataclasses.dataclass(frozen=True)
class SeriesPoint:
    timestamp: dt.datetime
    values: dict[str, float]


@dataclasses.dataclass(frozen=True)
class ValidationBlock:
    status: str
    reason: str
    metrics: dict[str, Any]
    technical_risks: list[str]

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def connect_readonly(db_path: str | os.PathLike[str]) -> sqlite3.Connection:
    """
    Open SQLite DB in strict read-only URI mode.

    Required PowerFlow contract:
        sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    """
    db_path_str = str(db_path)
    conn = sqlite3.connect(f"file:{db_path_str}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def quote_identifier(identifier: str) -> str:
    if "\x00" in identifier:
        raise ValueError("Invalid SQLite identifier")
    return '"' + identifier.replace('"', '""') + '"'


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def _columns(conn: sqlite3.Connection, table: str) -> list[str]:
    rows = conn.execute(f"PRAGMA table_info({quote_identifier(table)})").fetchall()
    return [str(row["name"]) for row in rows]


def detect_column_case_insensitive(
    conn: sqlite3.Connection,
    table: str,
    wanted: str,
) -> str | None:
    for column in _columns(conn, table):
        if column.lower() == wanted.lower():
            return column
    return None


def detect_timestamp_column(
    conn: sqlite3.Connection,
    table: str = DEFAULT_TABLE,
    candidates: Sequence[str] = DEFAULT_TIMESTAMP_COLUMNS,
) -> str:
    cols = _columns(conn, table)
    normalized = {col.lower(): col for col in cols}

    for candidate in candidates:
        found = normalized.get(candidate.lower())
        if found:
            return found

    timestamp_like = [
        col for col in cols
        if "time" in col.lower() or "date" in col.lower() or col.lower() == "ts"
    ]
    if timestamp_like:
        return timestamp_like[0]

    raise MarketOpenValidatorError(
        f"No timestamp-like column found in {table!r}. Available columns: {cols}"
    )


def detect_symbol_column(conn: sqlite3.Connection, table: str = DEFAULT_TABLE) -> str | None:
    cols = _columns(conn, table)
    normalized = {col.lower(): col for col in cols}
    for candidate in ("symbol", "pair", "instrument"):
        if candidate in normalized:
            return normalized[candidate]
    return None


def detect_currency_columns(
    conn: sqlite3.Connection,
    table: str = DEFAULT_TABLE,
    preferred: Sequence[str] = DEFAULT_CURRENCY_COLUMNS,
) -> list[str]:
    cols = _columns(conn, table)
    normalized = {col.upper(): col for col in cols}

    found = [normalized[item] for item in preferred if item in normalized]
    if found:
        return found

    excluded = {
        "id",
        "rowid",
        "timestamp",
        "ts",
        "datetime",
        "created_at",
        "time",
        "bar_time",
        "snapshot_time",
        "timeframe",
        "symbol",
        "pair",
        "instrument",
    }
    sample = conn.execute(f"SELECT * FROM {quote_identifier(table)} LIMIT 25").fetchall()
    numeric_candidates: list[str] = []

    for col in cols:
        if col.lower() in excluded:
            continue
        numeric_seen = False
        for row in sample:
            value = row[col]
            if value is None:
                continue
            with contextlib.suppress(TypeError, ValueError):
                float(value)
                numeric_seen = True
                break
        if numeric_seen:
            numeric_candidates.append(col)

    return numeric_candidates


def parse_timestamp(value: Any) -> dt.datetime | None:
    if value is None:
        return None

    if isinstance(value, dt.datetime):
        parsed = value
    elif isinstance(value, (int, float)):
        raw = float(value)
        if raw > 10_000_000_000:
            raw /= 1000.0
        try:
            parsed = dt.datetime.fromtimestamp(raw, tz=UTC)
        except (OverflowError, OSError, ValueError):
            return None
    else:
        text = str(value).strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"

        parsed = None
        with contextlib.suppress(ValueError):
            parsed = dt.datetime.fromisoformat(text)

        if parsed is None:
            for fmt in (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y.%m.%d %H:%M:%S",
            ):
                with contextlib.suppress(ValueError):
                    parsed = dt.datetime.strptime(text, fmt)
                    break

        if parsed is None:
            return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def normalize_since(since: str | None) -> str | None:
    if since is None:
        return None
    text = str(since).strip()
    return text or None


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(result):
        return None
    return result


def load_json(path: str | os.PathLike[str] | None) -> Any:
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def walk_json_values(obj: Any, keys: set[str]) -> list[Any]:
    values: list[Any] = []

    if isinstance(obj, Mapping):
        for key, value in obj.items():
            if str(key) in keys:
                values.append(value)
            values.extend(walk_json_values(value, keys))
    elif isinstance(obj, list):
        for item in obj:
            values.extend(walk_json_values(item, keys))

    return values


def walk_json_records(obj: Any) -> list[Mapping[str, Any]]:
    records: list[Mapping[str, Any]] = []
    if isinstance(obj, Mapping):
        records.append(obj)
        for value in obj.values():
            records.extend(walk_json_records(value))
    elif isinstance(obj, list):
        for item in obj:
            records.extend(walk_json_records(item))
    return records


def rank(values: Sequence[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    i = 0

    while i < len(indexed):
        j = i + 1
        while j < len(indexed) and indexed[j][1] == indexed[i][1]:
            j += 1

        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[indexed[k][0]] = avg_rank
        i = j

    return ranks


def pearson(x: Sequence[float], y: Sequence[float]) -> float | None:
    if len(x) != len(y) or len(x) < 3:
        return None

    mean_x = statistics.fmean(x)
    mean_y = statistics.fmean(y)
    dx = [value - mean_x for value in x]
    dy = [value - mean_y for value in y]
    sx = math.sqrt(sum(value * value for value in dx))
    sy = math.sqrt(sum(value * value for value in dy))

    if sx <= 1e-12 or sy <= 1e-12:
        return None

    return sum(a * b for a, b in zip(dx, dy)) / (sx * sy)


def spearman(x: Sequence[float], y: Sequence[float]) -> float | None:
    if len(x) != len(y) or len(x) < 3:
        return None
    return pearson(rank(x), rank(y))


def stdev_or_zero(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    return float(statistics.pstdev(values))


def _fetch_series(
    conn: sqlite3.Connection,
    table: str,
    tf_col: str,
    tf: int,
    timestamp_col: str,
    currency_cols: Sequence[str],
    since: str | None,
    symbol_col: str | None = None,
    symbol: str | None = None,
) -> list[SeriesPoint]:
    where = [f"{quote_identifier(tf_col)} = ?"]
    params: list[Any] = [tf]

    if since:
        where.append(f"{quote_identifier(timestamp_col)} >= ?")
        params.append(since)

    if symbol_col and symbol:
        where.append(f"{quote_identifier(symbol_col)} = ?")
        params.append(symbol)

    selected_cols = [timestamp_col, *currency_cols]
    sql = (
        "SELECT "
        + ", ".join(quote_identifier(col) for col in selected_cols)
        + f" FROM {quote_identifier(table)} "
        + f"WHERE {' AND '.join(where)} "
        + f"ORDER BY {quote_identifier(timestamp_col)} ASC"
    )

    points: list[SeriesPoint] = []
    for row in conn.execute(sql, params).fetchall():
        ts = parse_timestamp(row[timestamp_col])
        if ts is None:
            continue

        values: dict[str, float] = {}
        for col in currency_cols:
            parsed = _safe_float(row[col])
            if parsed is not None:
                values[col.upper()] = parsed

        if values:
            points.append(SeriesPoint(timestamp=ts, values=values))

    return points


def _filter_recent_points(
    points: Sequence[SeriesPoint],
    recent_minutes: int | None,
    now: dt.datetime,
) -> list[SeriesPoint]:
    if recent_minutes is None or recent_minutes <= 0:
        return list(points)

    lower = now - dt.timedelta(minutes=recent_minutes)
    return [point for point in points if point.timestamp >= lower]


def _series_for_currency(points: Sequence[SeriesPoint], currency: str) -> list[float]:
    key = currency.upper()
    return [point.values[key] for point in points if key in point.values]


def dominant_period_bars(values: Sequence[float], max_lag: int | None = None) -> int | None:
    """
    Lightweight autocorrelation-based dominant period estimator.

    Returns 1 for static / near-static series, matching the known weekend-static
    B4 symptom that this validator must catch.
    """
    cleaned = [float(v) for v in values if math.isfinite(float(v))]
    n = len(cleaned)
    if n < 8:
        return None

    if stdev_or_zero(cleaned) <= 1e-12:
        return 1

    lag_max = max_lag or min(40, max(2, n // 3))
    best_lag: int | None = None
    best_corr = -math.inf

    for lag in range(1, lag_max + 1):
        left = cleaned[:-lag]
        right = cleaned[lag:]
        corr = pearson(left, right)
        if corr is None:
            continue
        if corr > best_corr:
            best_corr = corr
            best_lag = lag

    return best_lag


def rolling_windows(values: Sequence[float], window: int, step: int) -> Iterable[list[float]]:
    if window <= 0:
        raise ValueError("window must be > 0")
    if step <= 0:
        raise ValueError("step must be > 0")

    if len(values) < window:
        return

    for start in range(0, len(values) - window + 1, step):
        yield list(values[start:start + window])


def validate_b4_from_json(
    payload: Any,
    static_threshold: float = 0.95,
    min_points: int = 3,
) -> ValidationBlock:
    raw_values = walk_json_values(payload, {"dominant_period_bars", "dominant_period"})
    periods: list[int] = []

    for value in raw_values:
        parsed = _safe_float(value)
        if parsed is not None:
            periods.append(int(round(parsed)))

    if not periods:
        return ValidationBlock(
            status="FAIL",
            reason="No dominant_period_bars values found in B4 JSON.",
            metrics={"source": "json", "periods_count": 0},
            technical_risks=["B4_OUTPUT_MISSING_DOMINANT_PERIOD"],
        )

    counter = Counter(periods)
    most_common_value, most_common_count = counter.most_common(1)[0]
    static_ratio = most_common_count / len(periods)
    is_static = (
        len(periods) < min_points
        or len(counter) <= 1
        or static_ratio >= static_threshold
        or (len(counter) == 1 and most_common_value == 1)
    )

    risks: list[str] = []
    if is_static:
        risks.append("B4_STATIC_DOMINANT_PERIOD")
    if most_common_value == 1 and static_ratio >= static_threshold:
        risks.append("B4_WEEKEND_STATIC_SIGNATURE")

    return ValidationBlock(
        status="FAIL" if is_static else "PASS",
        reason="B4 dominant_period_bars is dynamic." if not is_static else "B4 dominant_period_bars appears frozen.",
        metrics={
            "source": "json",
            "periods_count": len(periods),
            "unique_periods": sorted(counter.keys()),
            "unique_periods_count": len(counter),
            "most_common_period": most_common_value,
            "static_ratio": round(static_ratio, 6),
            "static_threshold": static_threshold,
        },
        technical_risks=risks,
    )


def validate_b5_from_json(
    payload: Any,
    min_rho_std: float = 0.02,
    min_points: int = 4,
) -> ValidationBlock:
    raw_values = walk_json_values(payload, {"rho", "spearman_rho", "avg_rho"})
    rhos = [float(value) for value in (_safe_float(item) for item in raw_values) if value is not None]

    if not rhos:
        return ValidationBlock(
            status="FAIL",
            reason="No rho/spearman_rho values found in B5 JSON.",
            metrics={"source": "json", "rho_count": 0},
            technical_risks=["B5_OUTPUT_MISSING_RHO"],
        )

    rounded = [round(value, 4) for value in rhos]
    rho_std = stdev_or_zero(rhos)
    rho_range = max(rhos) - min(rhos) if rhos else 0.0
    is_dynamic = len(rhos) >= min_points and rho_std >= min_rho_std and len(set(rounded)) > 1

    return ValidationBlock(
        status="PASS" if is_dynamic else "FAIL",
        reason="B5 rho fluctuates." if is_dynamic else "B5 rho appears frozen.",
        metrics={
            "source": "json",
            "rho_count": len(rhos),
            "rho_std": round(rho_std, 6),
            "rho_range": round(rho_range, 6),
            "unique_rounded_rho_count": len(set(rounded)),
            "min_rho_std": min_rho_std,
        },
        technical_risks=[] if is_dynamic else ["B5_RHO_STATIC_OR_INSUFFICIENT_FLUCTUATION"],
    )


def validate_eie_from_json(
    payload: Any,
    min_score_std: float = 0.01,
    min_points: int = 3,
) -> ValidationBlock:
    state_keys = {
        "state",
        "eie_state",
        "elastic_state",
        "confluence_state",
        "zone_state",
        "label",
    }
    score_keys = {
        "elastic_score",
        "eie_score",
        "score",
        "confidence",
        "fractalite",
        "fractality",
    }

    records = walk_json_records(payload)
    states: list[str] = []
    for record in records:
        for key in state_keys:
            if key in record and record[key] is not None:
                text = str(record[key]).upper()
                if any(token in text for token in ("EIE", "EWZ", "ENZ", "ZNE", "NEUTRAL")):
                    states.append(text)

    scores = [
        float(value)
        for value in (_safe_float(item) for item in walk_json_values(payload, score_keys))
        if value is not None
    ]

    all_neutral = bool(states) and all(state in {"ZNE", "NEUTRAL"} for state in states)
    state_dynamic = len(set(states)) > 1
    score_dynamic = len(scores) >= min_points and stdev_or_zero(scores) >= min_score_std
    is_dynamic = (state_dynamic or score_dynamic) and not all_neutral

    risks: list[str] = []
    if not states and not scores:
        risks.append("EIE_OUTPUT_MISSING_STATE_AND_SCORE")
    if all_neutral:
        risks.append("EIE_ALL_NEUTRAL_STATIC")
    if not is_dynamic and not risks:
        risks.append("EIE_STATIC_OUTPUT")

    return ValidationBlock(
        status="PASS" if is_dynamic else "FAIL",
        reason="EIE output is dynamic." if is_dynamic else "EIE output appears frozen or neutral-only.",
        metrics={
            "source": "json",
            "states_count": len(states),
            "unique_states": sorted(set(states)),
            "scores_count": len(scores),
            "score_std": round(stdev_or_zero(scores), 6) if scores else None,
            "min_score_std": min_score_std,
            "all_neutral": all_neutral,
        },
        technical_risks=risks,
    )


def validate_b4_from_db(
    conn: sqlite3.Connection,
    table: str,
    tf_col: str,
    timestamp_col: str,
    currency_cols: Sequence[str],
    timeframes: Sequence[int],
    since: str | None,
    symbol_col: str | None,
    symbol: str | None,
    recent_minutes: int | None,
    now: dt.datetime,
    window: int = 48,
    step: int = 6,
    static_threshold: float = 0.95,
) -> ValidationBlock:
    periods: list[int] = []
    details: list[dict[str, Any]] = []

    for tf in timeframes:
        points = _fetch_series(
            conn=conn,
            table=table,
            tf_col=tf_col,
            tf=tf,
            timestamp_col=timestamp_col,
            currency_cols=currency_cols,
            since=since,
            symbol_col=symbol_col,
            symbol=symbol,
        )
        points = _filter_recent_points(points, recent_minutes, now)

        for currency in currency_cols:
            values = _series_for_currency(points, currency)
            local_periods: list[int] = []
            for window_values in rolling_windows(values, window=window, step=step) or []:
                period = dominant_period_bars(window_values)
                if period is not None:
                    local_periods.append(period)

            if local_periods:
                periods.extend(local_periods)
                counter = Counter(local_periods)
                details.append(
                    {
                        "timeframe": tf,
                        "currency": currency.upper(),
                        "periods_count": len(local_periods),
                        "unique_periods": sorted(counter.keys()),
                        "most_common_period": counter.most_common(1)[0][0],
                    }
                )

    if not periods:
        return ValidationBlock(
            status="FAIL",
            reason="Insufficient DB data to compute B4 proxy dominant periods.",
            metrics={"source": "db_proxy", "periods_count": 0, "window": window, "step": step},
            technical_risks=["B4_INSUFFICIENT_DATA"],
        )

    counter = Counter(periods)
    most_common_value, most_common_count = counter.most_common(1)[0]
    static_ratio = most_common_count / len(periods)
    is_static = (
        len(counter) <= 1
        or static_ratio >= static_threshold
        or (len(counter) == 1 and most_common_value == 1)
    )

    risks: list[str] = []
    if is_static:
        risks.append("B4_STATIC_DOMINANT_PERIOD")
    if most_common_value == 1 and static_ratio >= static_threshold:
        risks.append("B4_WEEKEND_STATIC_SIGNATURE")

    return ValidationBlock(
        status="FAIL" if is_static else "PASS",
        reason="B4 proxy dominant periods are dynamic." if not is_static else "B4 proxy dominant periods appear frozen.",
        metrics={
            "source": "db_proxy",
            "periods_count": len(periods),
            "unique_periods": sorted(counter.keys()),
            "unique_periods_count": len(counter),
            "most_common_period": most_common_value,
            "static_ratio": round(static_ratio, 6),
            "static_threshold": static_threshold,
            "window": window,
            "step": step,
            "details": details[:40],
        },
        technical_risks=risks,
    )


def validate_b5_from_db(
    conn: sqlite3.Connection,
    table: str,
    tf_col: str,
    timestamp_col: str,
    currency_cols: Sequence[str],
    timeframes: Sequence[int],
    since: str | None,
    symbol_col: str | None,
    symbol: str | None,
    recent_minutes: int | None,
    now: dt.datetime,
    window: int = 48,
    step: int = 6,
    min_rho_std: float = 0.02,
) -> ValidationBlock:
    rhos: list[float] = []
    details: list[dict[str, Any]] = []

    currencies = [col.upper() for col in currency_cols]
    pairs = list(itertools.combinations(currencies, 2))

    for tf in timeframes:
        points = _fetch_series(
            conn=conn,
            table=table,
            tf_col=tf_col,
            tf=tf,
            timestamp_col=timestamp_col,
            currency_cols=currency_cols,
            since=since,
            symbol_col=symbol_col,
            symbol=symbol,
        )
        points = _filter_recent_points(points, recent_minutes, now)

        by_currency = {
            currency.upper(): _series_for_currency(points, currency)
            for currency in currency_cols
        }

        for left, right in pairs:
            x = by_currency.get(left, [])
            y = by_currency.get(right, [])
            n = min(len(x), len(y))
            if n < window:
                continue

            pair_rhos: list[float] = []
            for start in range(0, n - window + 1, step):
                rho = spearman(x[start:start + window], y[start:start + window])
                if rho is not None and math.isfinite(rho):
                    pair_rhos.append(float(rho))

            if pair_rhos:
                rhos.extend(pair_rhos)
                details.append(
                    {
                        "timeframe": tf,
                        "pair": f"{left}_{right}",
                        "rho_count": len(pair_rhos),
                        "rho_std": round(stdev_or_zero(pair_rhos), 6),
                        "rho_min": round(min(pair_rhos), 6),
                        "rho_max": round(max(pair_rhos), 6),
                    }
                )

    if not rhos:
        return ValidationBlock(
            status="FAIL",
            reason="Insufficient DB data to compute B5 proxy rho.",
            metrics={"source": "db_proxy", "rho_count": 0, "window": window, "step": step},
            technical_risks=["B5_INSUFFICIENT_DATA"],
        )

    rounded = [round(value, 4) for value in rhos]
    rho_std = stdev_or_zero(rhos)
    rho_range = max(rhos) - min(rhos)
    is_dynamic = rho_std >= min_rho_std and len(set(rounded)) > 1

    return ValidationBlock(
        status="PASS" if is_dynamic else "FAIL",
        reason="B5 proxy rho fluctuates." if is_dynamic else "B5 proxy rho appears frozen.",
        metrics={
            "source": "db_proxy",
            "rho_count": len(rhos),
            "rho_std": round(rho_std, 6),
            "rho_range": round(rho_range, 6),
            "unique_rounded_rho_count": len(set(rounded)),
            "min_rho_std": min_rho_std,
            "window": window,
            "step": step,
            "details": details[:40],
        },
        technical_risks=[] if is_dynamic else ["B5_RHO_STATIC_OR_INSUFFICIENT_FLUCTUATION"],
    )


def zscore_last(values: Sequence[float]) -> float | None:
    if len(values) < 10:
        return None
    mean = statistics.fmean(values)
    sd = stdev_or_zero(values)
    if sd <= 1e-12:
        return 0.0
    return (values[-1] - mean) / sd


def classify_eie_proxy(
    tf1_values: Sequence[float],
    tf5_values: Sequence[float],
    tf15_values: Sequence[float],
    zone_threshold: float,
    elastic_ratio_threshold: float,
) -> tuple[str, float]:
    """
    Lightweight EIE proxy:
        - zone active from TF15 z-score.
        - elastic loaded from TF1 micro-variance vs TF5 macro-variance.
    """
    z15 = zscore_last(tf15_values[-50:])
    if z15 is None:
        return "UNKNOWN", 0.0

    tf1_tail = list(tf1_values[-30:])
    tf5_tail = list(tf5_values[-30:])

    if len(tf1_tail) < 10 or len(tf5_tail) < 10:
        return "UNKNOWN", abs(z15)

    micro = stdev_or_zero([b - a for a, b in zip(tf1_tail, tf1_tail[1:])])
    macro = stdev_or_zero([b - a for a, b in zip(tf5_tail, tf5_tail[1:])])
    ratio = micro / max(macro, 1e-12)

    zone_active = abs(z15) >= zone_threshold
    elastic_loaded = ratio >= elastic_ratio_threshold
    score = abs(z15) + min(ratio, 5.0) / 5.0

    if zone_active and elastic_loaded:
        return "EIE", score
    if zone_active:
        return "EWZ", score
    if elastic_loaded:
        return "ENZ", score
    return "ZNE", score


def validate_eie_from_db(
    conn: sqlite3.Connection,
    table: str,
    tf_col: str,
    timestamp_col: str,
    currency_cols: Sequence[str],
    since: str | None,
    symbol_col: str | None,
    symbol: str | None,
    recent_minutes: int | None,
    now: dt.datetime,
    zone_threshold: float = 1.2,
    elastic_ratio_threshold: float = 1.2,
) -> ValidationBlock:
    points_by_tf: dict[int, list[SeriesPoint]] = {}
    for tf in (1, 5, 15):
        points = _fetch_series(
            conn=conn,
            table=table,
            tf_col=tf_col,
            tf=tf,
            timestamp_col=timestamp_col,
            currency_cols=currency_cols,
            since=since,
            symbol_col=symbol_col,
            symbol=symbol,
        )
        points_by_tf[tf] = _filter_recent_points(points, recent_minutes, now)

    states: list[str] = []
    scores: list[float] = []
    details: list[dict[str, Any]] = []

    for currency in currency_cols:
        tf1_values = _series_for_currency(points_by_tf[1], currency)
        tf5_values = _series_for_currency(points_by_tf[5], currency)
        tf15_values = _series_for_currency(points_by_tf[15], currency)

        state, score = classify_eie_proxy(
            tf1_values=tf1_values,
            tf5_values=tf5_values,
            tf15_values=tf15_values,
            zone_threshold=zone_threshold,
            elastic_ratio_threshold=elastic_ratio_threshold,
        )
        if state != "UNKNOWN":
            states.append(state)
            scores.append(score)
            details.append(
                {
                    "currency": currency.upper(),
                    "state": state,
                    "score": round(score, 6),
                    "tf1_points": len(tf1_values),
                    "tf5_points": len(tf5_values),
                    "tf15_points": len(tf15_values),
                }
            )

    if not states:
        return ValidationBlock(
            status="FAIL",
            reason="Insufficient DB data to compute EIE proxy.",
            metrics={"source": "db_proxy", "states_count": 0},
            technical_risks=["EIE_INSUFFICIENT_DATA"],
        )

    all_neutral = all(state == "ZNE" for state in states)
    dynamic_state = len(set(states)) > 1
    dynamic_score = len(scores) >= 3 and stdev_or_zero(scores) >= 0.01
    is_dynamic = (dynamic_state or dynamic_score) and not all_neutral

    risks: list[str] = []
    if all_neutral:
        risks.append("EIE_ALL_NEUTRAL_STATIC")
    if not is_dynamic and not risks:
        risks.append("EIE_STATIC_PROXY_OUTPUT")

    return ValidationBlock(
        status="PASS" if is_dynamic else "FAIL",
        reason="EIE proxy is dynamic." if is_dynamic else "EIE proxy appears frozen or neutral-only.",
        metrics={
            "source": "db_proxy",
            "states_count": len(states),
            "unique_states": sorted(set(states)),
            "scores_count": len(scores),
            "score_std": round(stdev_or_zero(scores), 6),
            "zone_threshold": zone_threshold,
            "elastic_ratio_threshold": elastic_ratio_threshold,
            "all_neutral": all_neutral,
            "details": details,
        },
        technical_risks=risks,
    )


def _latest_timestamp(
    conn: sqlite3.Connection,
    table: str,
    timestamp_col: str,
    since: str | None,
) -> dt.datetime | None:
    where = ""
    params: list[Any] = []
    if since:
        where = f"WHERE {quote_identifier(timestamp_col)} >= ?"
        params.append(since)

    sql = (
        f"SELECT MAX({quote_identifier(timestamp_col)}) AS last_ts "
        f"FROM {quote_identifier(table)} {where}"
    )
    row = conn.execute(sql, params).fetchone()
    if row is None:
        return None
    return parse_timestamp(row["last_ts"])


def validate_market_open(
    db_path: str | os.PathLike[str] = "powerflow.db",
    since: str | None = None,
    timeframes: Sequence[int] = DEFAULT_TIMEFRAMES,
    symbol: str | None = None,
    table: str = DEFAULT_TABLE,
    recent_minutes: int | None = 180,
    max_market_stale_minutes: int = 15,
    b4_json_path: str | os.PathLike[str] | None = None,
    b5_json_path: str | os.PathLike[str] | None = None,
    eie_json_path: str | os.PathLike[str] | None = None,
    b4_window: int = 48,
    b5_window: int = 48,
    step: int = 6,
    b4_static_threshold: float = 0.95,
    b5_min_rho_std: float = 0.02,
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    """Validate B4/B5/EIE liveness."""
    now_utc = (now or dt.datetime.now(tz=UTC)).astimezone(UTC)
    since_text = normalize_since(since)

    b4_payload = load_json(b4_json_path)
    b5_payload = load_json(b5_json_path)
    eie_payload = load_json(eie_json_path)

    report: dict[str, Any] = {
        "module": "pf_market_open_validator",
        "version": "7.1.0",
        "generated_at": now_utc.isoformat(),
        "db_path": str(db_path),
        "table": table,
        "since": since_text,
        "recent_minutes": recent_minutes,
        "timeframes": [int(tf) for tf in timeframes],
        "symbol": symbol,
        "mode": {
            "b4": "json" if b4_payload is not None else "db_proxy",
            "b5": "json" if b5_payload is not None else "db_proxy",
            "eie": "json" if eie_payload is not None else "db_proxy",
        },
    }

    with connect_readonly(db_path) as conn:
        if not _table_exists(conn, table):
            raise MarketOpenValidatorError(f"Missing table {table!r}")

        tf_col = detect_column_case_insensitive(conn, table, "timeframe")
        if tf_col is None:
            raise MarketOpenValidatorError(
                f"Table {table!r} has no timeframe column. Columns: {_columns(conn, table)}"
            )

        timestamp_col = detect_timestamp_column(conn, table)
        currency_cols = detect_currency_columns(conn, table)
        symbol_col = detect_symbol_column(conn, table)

        if not currency_cols:
            raise MarketOpenValidatorError(f"No currency/numeric columns detected in {table!r}")

        last_ts = _latest_timestamp(conn, table, timestamp_col, since_text)
        last_age_seconds = (
            max(0.0, (now_utc - last_ts).total_seconds())
            if last_ts is not None
            else None
        )
        market_data_fresh = (
            last_age_seconds is not None
            and last_age_seconds <= max_market_stale_minutes * 60
        )

        report.update(
            {
                "timestamp_column": timestamp_col,
                "timeframe_column": tf_col,
                "symbol_column": symbol_col,
                "currency_columns": [col.upper() for col in currency_cols],
                "last_db_timestamp": last_ts.isoformat() if last_ts else None,
                "last_db_age_seconds": round(last_age_seconds, 3)
                if last_age_seconds is not None
                else None,
                "max_market_stale_minutes": max_market_stale_minutes,
                "market_data_fresh": market_data_fresh,
            }
        )

        b4 = (
            validate_b4_from_json(b4_payload, static_threshold=b4_static_threshold)
            if b4_payload is not None
            else validate_b4_from_db(
                conn=conn,
                table=table,
                tf_col=tf_col,
                timestamp_col=timestamp_col,
                currency_cols=currency_cols,
                timeframes=timeframes,
                since=since_text,
                symbol_col=symbol_col,
                symbol=symbol,
                recent_minutes=recent_minutes,
                now=now_utc,
                window=b4_window,
                step=step,
                static_threshold=b4_static_threshold,
            )
        )

        b5 = (
            validate_b5_from_json(b5_payload, min_rho_std=b5_min_rho_std)
            if b5_payload is not None
            else validate_b5_from_db(
                conn=conn,
                table=table,
                tf_col=tf_col,
                timestamp_col=timestamp_col,
                currency_cols=currency_cols,
                timeframes=timeframes,
                since=since_text,
                symbol_col=symbol_col,
                symbol=symbol,
                recent_minutes=recent_minutes,
                now=now_utc,
                window=b5_window,
                step=step,
                min_rho_std=b5_min_rho_std,
            )
        )

        eie = (
            validate_eie_from_json(eie_payload)
            if eie_payload is not None
            else validate_eie_from_db(
                conn=conn,
                table=table,
                tf_col=tf_col,
                timestamp_col=timestamp_col,
                currency_cols=currency_cols,
                since=since_text,
                symbol_col=symbol_col,
                symbol=symbol,
                recent_minutes=recent_minutes,
                now=now_utc,
            )
        )

    report["b4"] = b4.to_dict()
    report["b5"] = b5.to_dict()
    report["eie"] = eie.to_dict()

    technical_risks: list[str] = []
    if not report.get("market_data_fresh"):
        technical_risks.append("MARKET_DATA_STALE_OR_UNAVAILABLE")

    for key in ("b4", "b5", "eie"):
        technical_risks.extend(report[key].get("technical_risks", []))

    block_statuses = [report[key]["status"] for key in ("b4", "b5", "eie")]
    report["overall_status"] = (
        "PASS"
        if report.get("market_data_fresh") and all(status == "PASS" for status in block_statuses)
        else "FAIL"
    )
    report["technical_risks"] = sorted(set(technical_risks))
    return report


def dumps_report(report: Mapping[str, Any], pretty: bool = False) -> str:
    return json.dumps(
        report,
        ensure_ascii=False,
        indent=2 if pretty else None,
        sort_keys=pretty,
    )


def parse_timeframes(value: str | Iterable[int]) -> tuple[int, ...]:
    if isinstance(value, str):
        items = [part.strip() for part in value.split(",") if part.strip()]
        if not items:
            raise ValueError("timeframes cannot be empty")
        parsed = tuple(int(item) for item in items)
    else:
        parsed = tuple(int(item) for item in value)

    if any(tf <= 0 for tf in parsed):
        raise ValueError("timeframes must be positive integers")
    return parsed


__all__ = [
    "MarketOpenValidatorError",
    "connect_readonly",
    "detect_currency_columns",
    "dumps_report",
    "parse_timeframes",
    "validate_market_open",
]
