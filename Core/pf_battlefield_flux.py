"""
T009 Battlefield Flux - standalone tick-cluster perception module.

Phase 1A contract:
- standalone dry-run perception only;
- no Telegram live send;
- no engine integration;
- no dashboard import;
- no writes to powerflow.db;
- source_mode and data_visibility are exposed in every evidence packet;
- M1 fallback is tagged RECONSTRUCTED with confidence_cap=0.35.
"""

from __future__ import annotations

import json
import math
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:  # Repo-root execution: python Core/run_battlefield_flux_once.py
    from Core.core_score_formulas import (  # type: ignore
        ABSORPTION_CLUSTER_THRESHOLD,
        ABSORPTION_COMPRESSION_MIN,
        ABSORPTION_PRESSURE_MIN,
        BATTLE_ACTIVITY_MIN,
        BATTLE_COMPRESSION_MIN,
        BATTLE_LEVEL_BORN_THRESHOLD,
        compute_absorption_score as phase0_absorption_score,
        compute_battle_score as phase0_battle_score,
    )
except Exception:  # Core-folder execution: python run_battlefield_flux_once.py
    try:
        from core_score_formulas import (  # type: ignore
            ABSORPTION_CLUSTER_THRESHOLD,
            ABSORPTION_COMPRESSION_MIN,
            ABSORPTION_PRESSURE_MIN,
            BATTLE_ACTIVITY_MIN,
            BATTLE_COMPRESSION_MIN,
            BATTLE_LEVEL_BORN_THRESHOLD,
            compute_absorption_score as phase0_absorption_score,
            compute_battle_score as phase0_battle_score,
        )
    except Exception:
        # Defensive fallback for isolated tests. Phase 0 remains the intended source.
        BATTLE_LEVEL_BORN_THRESHOLD = 0.70
        BATTLE_ACTIVITY_MIN = 0.55
        BATTLE_COMPRESSION_MIN = 0.50
        ABSORPTION_CLUSTER_THRESHOLD = 0.65
        ABSORPTION_PRESSURE_MIN = 0.50
        ABSORPTION_COMPRESSION_MIN = 0.55

        def phase0_battle_score(activity: float, compression: float, dwell: float, retest: float, pressure_contention: float) -> float:
            return (0.30 * activity + 0.25 * compression + 0.20 * dwell + 0.15 * retest + 0.10 * pressure_contention)

        def phase0_absorption_score(pressure: float, compression: float, failed_disp: float, dwell: float, activity: float, spread_stab: float) -> float:
            return (0.35 * pressure + 0.25 * compression + 0.15 * failed_disp + 0.10 * dwell + 0.10 * activity + 0.05 * spread_stab)


VALID_SOURCE_MODES = {"ONTICK_RAW", "TIMER_1S_SAMPLE", "M1_BAR_PROXY"}
STALE_VISIBILITY = {"BLIND", "STALE"}


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp a numeric value into a closed interval."""
    if math.isnan(value) or math.isinf(value):
        return lo
    return max(lo, min(hi, value))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso_utc(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_datetime(value: Any) -> Optional[datetime]:
    """Parse common SQLite timestamp forms into UTC datetime."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        # Heuristic: epoch seconds or epoch milliseconds.
        numeric = float(value)
        if numeric > 10_000_000_000:
            numeric /= 1000.0
        return datetime.fromtimestamp(numeric, tz=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    for suffix in ("Z", "+00:00"):
        if text.endswith(suffix):
            text = text[: -len(suffix)]
            break
    candidates = [text, text.replace(" ", "T")]
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y.%m.%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ]
    for candidate in candidates:
        try:
            parsed = datetime.fromisoformat(candidate)
            return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)
        except ValueError:
            pass
        for fmt in formats:
            try:
                parsed = datetime.strptime(candidate, fmt)
                return parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    return None


def _epoch_ms_from_value(value: Any, fallback_dt: Optional[datetime] = None) -> int:
    if value is not None:
        try:
            numeric = float(value)
            if numeric > 10_000_000_000:
                return int(numeric)
            if numeric > 10_000_000:
                return int(numeric * 1000)
        except (TypeError, ValueError):
            parsed = _parse_datetime(value)
            if parsed:
                return int(parsed.timestamp() * 1000)
    if fallback_dt:
        return int(fallback_dt.timestamp() * 1000)
    return int(_utcnow().timestamp() * 1000)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


class BattlefieldFlux:
    """Standalone T009 Battlefield Flux perception module."""

    def __init__(self, db_path: str = "tick_archive.db", fallback_db: str = "powerflow.db"):
        self.db_path = db_path
        self.fallback_db = fallback_db

    # ------------------------------------------------------------------
    # SQLite helpers
    # ------------------------------------------------------------------
    def _connect_readonly(self, db_path: str) -> Optional[sqlite3.Connection]:
        """Open a SQLite DB read-only when possible, without creating files."""
        if db_path == ":memory:":
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            return conn

        path = Path(db_path)
        if not path.exists():
            return None

        uri = f"file:{path.resolve().as_posix()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _table_columns(conn: sqlite3.Connection, table_name: str) -> List[str]:
        try:
            rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        except sqlite3.Error:
            return []
        return [str(row[1]) for row in rows]

    @staticmethod
    def _pick_column(columns: Sequence[str], candidates: Sequence[str]) -> Optional[str]:
        lower_map = {col.lower(): col for col in columns}
        for candidate in candidates:
            if candidate.lower() in lower_map:
                return lower_map[candidate.lower()]
        return None

    @staticmethod
    def _quote_identifier(identifier: str) -> str:
        return '"' + identifier.replace('"', '""') + '"'

    # ------------------------------------------------------------------
    # Loaders
    # ------------------------------------------------------------------
    def load_ticks_primary(self, symbol: str, lookback_min: int) -> List[Dict[str, Any]]:
        """Load recent ticks from tick_archive.db tick_stream table."""
        conn = self._connect_readonly(self.db_path)
        if conn is None:
            return []

        try:
            cutoff_ms = int((_utcnow() - timedelta(minutes=lookback_min)).timestamp() * 1000)
            cursor = conn.execute(
                """
                SELECT * FROM tick_stream
                WHERE symbol = ? AND ts_epoch_ms >= ?
                ORDER BY ts_epoch_ms ASC, capture_seq ASC
                """,
                (symbol, cutoff_ms),
            )
            ticks = [dict(row) for row in cursor.fetchall()]
            for tick in ticks:
                tick.setdefault("source_mode", "TIMER_1S_SAMPLE")
                tick.setdefault("data_visibility", "FRESH")
                tick.setdefault("confidence_cap", 1.0)
                tick.setdefault("live_telegram_allowed", False)
                tick["mid"] = _safe_float(tick.get("mid"), (_safe_float(tick.get("bid")) + _safe_float(tick.get("ask"))) / 2)
            return ticks
        except sqlite3.Error:
            return []
        finally:
            conn.close()

    def load_ticks_fallback(self, symbol: str, lookback_min: int) -> List[Dict[str, Any]]:
        """
        Fallback to M1 bars from powerflow.db.

        Deterministic OHLC reconstruction:
        - if close >= open: open, low, high, close
        - else: open, high, low, close

        No write is performed against powerflow.db.
        """
        conn = self._connect_readonly(self.fallback_db)
        if conn is None:
            return []

        try:
            table_name = self._find_m1_table(conn)
            if not table_name:
                return []

            columns = self._table_columns(conn, table_name)
            symbol_col = self._pick_column(columns, ["symbol", "pair"])
            ts_col = self._pick_column(columns, ["ts", "timestamp", "time", "bar_time", "datetime", "created_at_utc"])
            ts_epoch_col = self._pick_column(columns, ["ts_epoch", "epoch", "epoch_s", "ts_epoch_ms", "time_epoch"])
            open_col = self._pick_column(columns, ["open", "open_price", "o"])
            high_col = self._pick_column(columns, ["high", "high_price", "h"])
            low_col = self._pick_column(columns, ["low", "low_price", "l"])
            close_col = self._pick_column(columns, ["close", "close_price", "c"])
            spread_col = self._pick_column(columns, ["spread", "spread_price", "spread_pips", "spread_points"])
            volume_col = self._pick_column(columns, ["tick_volume", "volume", "vol"])

            required = [ts_col, open_col, high_col, low_col, close_col]
            if any(col is None for col in required):
                return []

            cutoff_dt = _utcnow() - timedelta(minutes=lookback_min)
            cutoff_text = _iso_utc(cutoff_dt)
            quoted_table = self._quote_identifier(table_name)
            order_col = ts_epoch_col or ts_col
            assert ts_col and open_col and high_col and low_col and close_col and order_col

            select_cols = [col for col in [symbol_col, ts_col, ts_epoch_col, open_col, high_col, low_col, close_col, spread_col, volume_col] if col]
            select_sql = ", ".join(self._quote_identifier(col) for col in dict.fromkeys(select_cols))

            where_parts: List[str] = []
            params: List[Any] = []
            if symbol_col:
                where_parts.append(f"{self._quote_identifier(symbol_col)} = ?")
                params.append(symbol)
            if ts_epoch_col:
                where_parts.append(f"{self._quote_identifier(ts_epoch_col)} >= ?")
                params.append(int(cutoff_dt.timestamp()))
            elif ts_col:
                where_parts.append(f"{self._quote_identifier(ts_col)} >= ?")
                params.append(cutoff_text)

            where_sql = "WHERE " + " AND ".join(where_parts) if where_parts else ""
            sql = f"SELECT {select_sql} FROM {quoted_table} {where_sql} ORDER BY {self._quote_identifier(order_col)} ASC"
            bars = [dict(row) for row in conn.execute(sql, params).fetchall()]

            ticks: List[Dict[str, Any]] = []
            pip_size = self._pip_size(symbol)
            default_spread = 2.0 * pip_size

            for bar_index, bar in enumerate(bars):
                open_p = _safe_float(bar.get(open_col))
                high_p = _safe_float(bar.get(high_col))
                low_p = _safe_float(bar.get(low_col))
                close_p = _safe_float(bar.get(close_col))
                if min(open_p, high_p, low_p, close_p) <= 0:
                    continue

                raw_spread = _safe_float(bar.get(spread_col), default_spread) if spread_col else default_spread
                spread = self._normalize_spread(raw_spread, pip_size)
                dt = _parse_datetime(bar.get(ts_col)) if ts_col else None
                base_epoch_ms = _epoch_ms_from_value(bar.get(ts_epoch_col) if ts_epoch_col else None, dt)

                sequence = [open_p, low_p, high_p, close_p] if close_p >= open_p else [open_p, high_p, low_p, close_p]
                for idx, price in enumerate(sequence):
                    ticks.append(
                        {
                            "symbol": symbol,
                            "ts_utc": _iso_utc(dt) if dt else _iso_utc(_utcnow()),
                            "ts_epoch_ms": base_epoch_ms + idx * 250 + bar_index,
                            "bid": price - spread / 2.0,
                            "ask": price + spread / 2.0,
                            "mid": price,
                            "spread": spread,
                            "tick_volume": int(_safe_float(bar.get(volume_col), 0)) if volume_col else None,
                            "source": "powerflow_db_bars_m1",
                            "source_mode": "M1_BAR_PROXY",
                            "capture_seq": idx,
                            "gap_ms": None,
                            "quality_flags": json.dumps(["M1_BAR_PROXY", "RECONSTRUCTED"]),
                            "data_visibility": "RECONSTRUCTED",
                            "confidence_cap": 0.35,
                            "live_telegram_allowed": False,
                        }
                    )
            return ticks
        except sqlite3.Error:
            return []
        finally:
            conn.close()

    def _find_m1_table(self, conn: sqlite3.Connection) -> Optional[str]:
        candidates = ["bars_m1", "m1_bars", "ohlc_m1", "candles_m1"]
        tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        lower_to_actual = {str(table).lower(): str(table) for table in tables}
        for candidate in candidates:
            if candidate.lower() in lower_to_actual:
                return lower_to_actual[candidate.lower()]
        return None

    # ------------------------------------------------------------------
    # Buckets and features
    # ------------------------------------------------------------------
    def build_time_price_buckets(
        self,
        ticks: List[Dict[str, Any]],
        time_bucket_sec: int = 60,
        slide_step_sec: int = 15,
        price_bucket_pip: float = 1.0,
    ) -> List[Dict[str, Any]]:
        """Build sliding time/price buckets over tick-like observations."""
        clean_ticks = [self._normalize_tick(tick) for tick in ticks if self._normalize_tick(tick)]
        if not clean_ticks:
            return []

        clean_ticks.sort(key=lambda item: int(item["ts_epoch_ms"]))
        first_epoch = int(clean_ticks[0]["ts_epoch_ms"])
        last_epoch = int(clean_ticks[-1]["ts_epoch_ms"])
        window_ms = int(time_bucket_sec * 1000)
        step_ms = int(slide_step_sec * 1000)
        buckets: List[Dict[str, Any]] = []

        current_epoch = first_epoch
        while current_epoch <= last_epoch:
            window_start = current_epoch
            window_end = current_epoch + window_ms
            window_ticks = [tick for tick in clean_ticks if window_start <= int(tick["ts_epoch_ms"]) < window_end]
            if window_ticks:
                features = self._compute_cluster_features(window_ticks, price_bucket_pip)
                buckets.append(
                    {
                        "time_bucket_ms": [window_start, window_end],
                        "window_start_utc": _iso_utc(datetime.fromtimestamp(window_start / 1000, tz=timezone.utc)),
                        "window_end_utc": _iso_utc(datetime.fromtimestamp(window_end / 1000, tz=timezone.utc)),
                        "tick_count": len(window_ticks),
                        "ticks": window_ticks,
                        "features": features,
                    }
                )
            current_epoch += step_ms
        return buckets

    def _normalize_tick(self, tick: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        mid = _safe_float(tick.get("mid"))
        bid = _safe_float(tick.get("bid"))
        ask = _safe_float(tick.get("ask"))
        if mid <= 0 and bid > 0 and ask >= bid:
            mid = (bid + ask) / 2.0
        if mid <= 0:
            return None
        if bid <= 0:
            bid = mid
        if ask <= 0:
            ask = mid
        spread = _safe_float(tick.get("spread"), max(0.0, ask - bid))
        normalized = dict(tick)
        normalized.update(
            {
                "bid": bid,
                "ask": ask,
                "mid": mid,
                "spread": max(0.0, spread),
                "ts_epoch_ms": int(_epoch_ms_from_value(tick.get("ts_epoch_ms"), _parse_datetime(tick.get("ts_utc")))),
                "ts_utc": tick.get("ts_utc") or _iso_utc(_utcnow()),
                "source_mode": tick.get("source_mode") or "TIMER_1S_SAMPLE",
                "data_visibility": tick.get("data_visibility") or "FRESH",
            }
        )
        return normalized

    def _compute_cluster_features(self, ticks: List[Dict[str, Any]], price_bucket_pip: float = 1.0) -> Dict[str, Any]:
        """Compute T009 cluster features for one bucket."""
        if not ticks:
            return {}

        ordered = sorted((self._normalize_tick(tick) for tick in ticks), key=lambda item: int(item["ts_epoch_ms"]))
        ordered = [tick for tick in ordered if tick]
        mids = [_safe_float(tick["mid"]) for tick in ordered]
        spreads = [_safe_float(tick.get("spread")) for tick in ordered]
        symbol = str(ordered[0].get("symbol", "GBPUSD"))
        pip_size = self._pip_size(symbol)
        price_bucket_size = max(pip_size, float(price_bucket_pip) * pip_size)

        price_min = min(mids)
        price_max = max(mids)
        price_range = price_max - price_min
        price_range_pips = price_range / pip_size if pip_size else 0.0

        signs: List[int] = []
        for prev, current in zip(mids, mids[1:]):
            delta = current - prev
            if delta > 0:
                signs.append(1)
            elif delta < 0:
                signs.append(-1)

        directional_ticks = len(signs)
        signed_delta = sum(signs)
        sign_changes = sum(1 for prev, current in zip(signs, signs[1:]) if current != prev)
        delta_imbalance = abs(signed_delta) / max(1, directional_ticks)
        flip_rate = sign_changes / max(1, directional_ticks - 1)
        pressure_or_contention_score = max(delta_imbalance, flip_rate)

        price_buckets: Dict[int, int] = {}
        for mid in mids:
            bucket_id = int(round(mid / price_bucket_size))
            price_buckets[bucket_id] = price_buckets.get(bucket_id, 0) + 1
        max_ticks_in_price_bucket = max(price_buckets.values()) if price_buckets else len(mids)
        dwell_score = max_ticks_in_price_bucket / max(1, len(mids))

        close_mid = mids[-1]
        open_mid = mids[0]
        failed_displacement_score = 1.0 - clamp(abs(close_mid - open_mid) / max(price_range, pip_size), 0.0, 1.0)

        spread_mean = sum(spreads) / max(1, len(spreads))
        spread_volatility = self._stddev(spreads)
        normal_spread_volatility = max(pip_size, spread_mean if spread_mean > 0 else pip_size)
        spread_stability_score = 1.0 - clamp(spread_volatility / normal_spread_volatility, 0.0, 1.0)

        quote_change_count = len({(round(_safe_float(tick.get("bid")), 6), round(_safe_float(tick.get("ask")), 6)) for tick in ordered})
        source_modes = sorted({str(tick.get("source_mode", "UNKNOWN")) for tick in ordered})
        data_visibility = self._aggregate_visibility(ordered)

        return {
            "tick_count": len(ordered),
            "signed_delta": signed_delta,
            "directional_ticks": directional_ticks,
            "sign_changes": sign_changes,
            "delta_imbalance": clamp(delta_imbalance),
            "flip_rate": clamp(flip_rate),
            "pressure_or_contention_score": clamp(pressure_or_contention_score),
            "price_range_pips": price_range_pips,
            "price_range": price_range,
            "price_min": price_min,
            "price_max": price_max,
            "open_mid": open_mid,
            "close_mid": close_mid,
            "spread_mean": spread_mean,
            "spread_volatility": spread_volatility,
            "spread_stability_score": clamp(spread_stability_score),
            "quote_change_count": quote_change_count,
            "max_ticks_in_price_bucket": max_ticks_in_price_bucket,
            "dwell_score": clamp(dwell_score),
            "failed_displacement_score": clamp(failed_displacement_score),
            "zone_revisits_last_15m": min(3, sign_changes),
            "price_dwell_zone": price_range_pips < 2.0,
            "source_modes": source_modes,
            "data_visibility": data_visibility,
        }

    # ------------------------------------------------------------------
    # Scores and detections
    # ------------------------------------------------------------------
    def score_components(self, features: Dict[str, Any]) -> Dict[str, float]:
        tick_count = int(features.get("tick_count", 0) or 0)
        activity_score = clamp(tick_count / 60.0)
        compression_score = 1.0 - clamp(_safe_float(features.get("price_range_pips"), 5.0) / 5.0)
        dwell_score = clamp(_safe_float(features.get("dwell_score"), 1.0 if features.get("price_dwell_zone") else 0.3))
        retest_score = clamp(_safe_float(features.get("zone_revisits_last_15m"), 1.5) / 3.0)
        pressure_or_contention_score = clamp(_safe_float(features.get("pressure_or_contention_score"), 0.0))
        pressure_score = clamp(abs(_safe_float(features.get("signed_delta"), 0.0)) / max(1, int(features.get("directional_ticks", tick_count) or tick_count or 1)))
        failed_displacement_score = clamp(_safe_float(features.get("failed_displacement_score"), 0.0))
        spread_stability_score = clamp(_safe_float(features.get("spread_stability_score"), 1.0))
        return {
            "activity_score": activity_score,
            "compression_score": compression_score,
            "dwell_score": dwell_score,
            "retest_score": retest_score,
            "pressure_or_contention_score": pressure_or_contention_score,
            "pressure_score": pressure_score,
            "failed_displacement_score": failed_displacement_score,
            "spread_stability_score": spread_stability_score,
        }

    def score_battle(self, features: Dict[str, Any]) -> float:
        """Compute Phase 0 committee battle score, normalized 0-1."""
        c = self.score_components(features)
        return clamp(phase0_battle_score(c["activity_score"], c["compression_score"], c["dwell_score"], c["retest_score"], c["pressure_or_contention_score"]))

    def score_absorption(self, features: Dict[str, Any]) -> float:
        """Compute Phase 0 committee absorption score, normalized 0-1."""
        c = self.score_components(features)
        return clamp(phase0_absorption_score(c["pressure_score"], c["compression_score"], c["failed_displacement_score"], c["dwell_score"], c["activity_score"], c["spread_stability_score"]))

    def detect_delta_flip(self, ticks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect sign changes in consecutive mid-price deltas."""
        clean_ticks = [self._normalize_tick(tick) for tick in ticks if self._normalize_tick(tick)]
        if len(clean_ticks) < 3:
            return []
        clean_ticks.sort(key=lambda item: int(item["ts_epoch_ms"]))
        mids = [_safe_float(tick["mid"]) for tick in clean_ticks]
        signs: List[int] = []
        sign_indices: List[int] = []
        for index, (prev, current) in enumerate(zip(mids, mids[1:]), start=1):
            if current > prev:
                signs.append(1)
                sign_indices.append(index)
            elif current < prev:
                signs.append(-1)
                sign_indices.append(index)
        events: List[Dict[str, Any]] = []
        for idx in range(1, len(signs)):
            if signs[idx] != signs[idx - 1]:
                tick_index = sign_indices[idx]
                tick = clean_ticks[tick_index]
                events.append(
                    {
                        "type": "T009_CLUSTER_DELTA_FLIP",
                        "ts": tick.get("ts_utc"),
                        "ts_epoch_ms": tick.get("ts_epoch_ms"),
                        "price": mids[tick_index],
                        "from_sign": signs[idx - 1],
                        "to_sign": signs[idx],
                    }
                )
        return events

    def detect_zone_break(self, zone_low: float, zone_high: float, price: float) -> Optional[Dict[str, Any]]:
        """Detect break outside a battle zone."""
        if price < zone_low or price > zone_high:
            return {
                "type": "T009_BATTLE_ZONE_BROKEN",
                "zone": [zone_low, zone_high],
                "break_price": price,
                "direction": "DOWN" if price < zone_low else "UP",
            }
        return None

    # ------------------------------------------------------------------
    # Evidence packets and state
    # ------------------------------------------------------------------
    def build_event_evidence_packet(
        self,
        event_type: str,
        zone: Tuple[float, float],
        scores: Dict[str, Any],
        ticks: List[Dict[str, Any]],
        features: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build a L1/L2/L3 evidence packet for a T009 event."""
        first_tick = ticks[0] if ticks else {}
        symbol = str(first_tick.get("symbol", "GBPUSD"))
        source_mode = str(first_tick.get("source_mode", "UNKNOWN"))
        data_visibility = str(first_tick.get("data_visibility", features.get("data_visibility", "UNKNOWN")))
        confidence_cap = float(first_tick.get("confidence_cap", 1.0 if data_visibility != "RECONSTRUCTED" else 0.35))
        live_telegram_allowed = bool(first_tick.get("live_telegram_allowed", False)) and data_visibility != "RECONSTRUCTED"

        risks = self._technical_risks(source_mode, data_visibility)
        packet = {
            "event_id": f"T009-{symbol}-{event_type}-{int(_utcnow().timestamp() * 1000)}",
            "event_type": event_type,
            "module": "pf_battlefield_flux",
            "phase": "T009_PHASE1A_STANDALONE_DRY_RUN",
            "symbol": symbol,
            "ts_utc": _iso_utc(_utcnow()),
            "source_mode": source_mode,
            "data_visibility": data_visibility,
            "confidence_cap": confidence_cap,
            "live_telegram_allowed": live_telegram_allowed,
            "zone": {"low": zone[0], "high": zone[1], "center": (zone[0] + zone[1]) / 2.0},
            "scores": scores,
            "features": features,
            "evidence": {
                "L1_raw": {
                    "tick_count": len(ticks),
                    "source_mode": source_mode,
                    "data_visibility": data_visibility,
                    "first_ts_utc": ticks[0].get("ts_utc") if ticks else None,
                    "last_ts_utc": ticks[-1].get("ts_utc") if ticks else None,
                },
                "L2_features": features,
                "L3_reading": {
                    "dominant": self._format_reading(event_type, scores),
                    "alternative": self._format_alternative(event_type),
                    "invalidation": "Price accepts outside zone with aligned delta propagation.",
                },
            },
            "technical_risks": risks,
            "reading": {
                "dominant": self._format_reading(event_type, scores),
                "alternative": self._format_alternative(event_type),
                "invalidation": "Price accepts outside zone with aligned delta propagation.",
            },
        }
        return packet

    def compute_state(self, symbol: str = "GBPUSD", lookback_min: int = 30) -> Dict[str, Any]:
        """Compute complete Phase 1A standalone state."""
        ticks = self.load_ticks_primary(symbol, lookback_min)
        source_used = "primary_tick_archive"
        if not ticks:
            ticks = self.load_ticks_fallback(symbol, lookback_min)
            source_used = "fallback_m1_bars"

        buckets = self.build_time_price_buckets(ticks, time_bucket_sec=60, slide_step_sec=15, price_bucket_pip=1.0)
        events: List[Dict[str, Any]] = []
        bucket_summaries: List[Dict[str, Any]] = []

        for bucket in buckets:
            features = bucket["features"]
            components = self.score_components(features)
            battle_score = self.score_battle(features)
            absorption_score = self.score_absorption(features)
            data_visibility = str(features.get("data_visibility", "UNKNOWN"))
            scores = {"battle_score": battle_score, "absorption_score": absorption_score, "components": components}
            zone = (_safe_float(features.get("price_min")), _safe_float(features.get("price_max")))

            bucket_summaries.append(
                {
                    "time_bucket_ms": bucket["time_bucket_ms"],
                    "tick_count": bucket["tick_count"],
                    "scores": scores,
                    "data_visibility": data_visibility,
                    "source_modes": features.get("source_modes", []),
                }
            )

            if (
                battle_score >= BATTLE_LEVEL_BORN_THRESHOLD
                and components["activity_score"] >= BATTLE_ACTIVITY_MIN
                and components["compression_score"] >= BATTLE_COMPRESSION_MIN
                and data_visibility not in STALE_VISIBILITY
            ):
                events.append(self.build_event_evidence_packet("T009_BATTLE_LEVEL_BORN", zone, scores, bucket["ticks"], features))

            if (
                absorption_score >= ABSORPTION_CLUSTER_THRESHOLD
                and components["pressure_score"] >= ABSORPTION_PRESSURE_MIN
                and components["compression_score"] >= ABSORPTION_COMPRESSION_MIN
            ):
                events.append(self.build_event_evidence_packet("T009_ABSORPTION_CLUSTER", zone, scores, bucket["ticks"], features))

        delta_flip_events = self.detect_delta_flip(ticks)
        state = {
            "module": "pf_battlefield_flux",
            "phase": "T009_PHASE1A_STANDALONE_DRY_RUN",
            "symbol": symbol,
            "lookback_min": lookback_min,
            "source_used": source_used,
            "tick_count": len(ticks),
            "bucket_count": len(buckets),
            "event_count": len(events),
            "events": events,
            "delta_flip_events": delta_flip_events,
            "buckets": bucket_summaries,
            "generated_at_utc": _iso_utc(_utcnow()),
        }
        return state

    # ------------------------------------------------------------------
    # Formatting and small utilities
    # ------------------------------------------------------------------
    def _technical_risks(self, source_mode: str, data_visibility: str) -> List[str]:
        risks: List[str] = []
        if source_mode == "TIMER_1S_SAMPLE":
            risks.append("TIMER_1S_SAMPLE_NOT_RAW_TICK")
        if source_mode == "M1_BAR_PROXY" or data_visibility == "RECONSTRUCTED":
            risks.append("RECONSTRUCTED_DATA")
            risks.append("M1_BAR_PROXY_CONFIDENCE_CAP_0_35")
        if source_mode not in VALID_SOURCE_MODES:
            risks.append("UNKNOWN_SOURCE_MODE")
        if data_visibility in STALE_VISIBILITY:
            risks.append(f"DATA_VISIBILITY_{data_visibility}")
        return risks

    def _format_reading(self, event_type: str, scores: Dict[str, Any]) -> str:
        readings = {
            "T009_BATTLE_LEVEL_BORN": "pression presente, passage bloque, niveau de bataille naissant",
            "T009_ABSORPTION_CLUSTER": "pression absorbee, prix stable dans la zone",
            "T009_CLUSTER_DELTA_FLIP": "basculement delta detecte dans le microfilm",
            "T009_BATTLE_ZONE_BROKEN": "cassure de zone de bataille",
        }
        return readings.get(event_type, "evenement T009 detecte")

    def _format_alternative(self, event_type: str) -> str:
        if event_type == "T009_BATTLE_LEVEL_BORN":
            return "Le cluster peut etre une friction locale si le prix accepte rapidement hors zone."
        if event_type == "T009_ABSORPTION_CLUSTER":
            return "L'absorption peut se transformer en break si le dwell disparait et le delta se propage."
        return "Voir les risques techniques et la confirmation prix."

    @staticmethod
    def _stddev(values: Sequence[float]) -> float:
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        return math.sqrt(variance)

    @staticmethod
    def _pip_size(symbol: str) -> float:
        return 0.01 if "JPY" in symbol.upper() else 0.0001

    @staticmethod
    def _normalize_spread(raw_spread: float, pip_size: float) -> float:
        if raw_spread <= 0:
            return 2.0 * pip_size
        # If value looks like spread in points/pips instead of price units, convert gently.
        if raw_spread > 0.01:
            return raw_spread * pip_size
        return raw_spread

    @staticmethod
    def _aggregate_visibility(ticks: Sequence[Dict[str, Any]]) -> str:
        visibilities = {str(tick.get("data_visibility", "FRESH")) for tick in ticks}
        if "BLIND" in visibilities:
            return "BLIND"
        if "STALE" in visibilities:
            return "STALE"
        if "RECONSTRUCTED" in visibilities:
            return "RECONSTRUCTED"
        return "FRESH"


bf = BattlefieldFlux()
