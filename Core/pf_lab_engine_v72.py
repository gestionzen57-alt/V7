#!/usr/bin/env python3
"""
PowerFlow V7.2 — Lab Engine

Purpose
-------
Replay a historical DB window in read-only mode, enrich the sequence with
PowerFlow V7.2 metrics, detect behavioral scenes, measure observed
cause/consequence windows, and emit human-readable lab reports.

Doctrine
--------
- No BUY/SELL.
- No trade decision.
- No alert filtering.
- No DB write to powerflow.db.
- No dependency on cockpit/telegram.
- Does not call pf_flow_nodes.py because it is a legacy write-aware module.

The machine replays, measures, names, and compares.
The trader decides.
"""

from __future__ import annotations

import html
import json
import math
import os
import sqlite3
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


VERSION = "LabEngineV72.0.1"
METHOD = "powerflow_lab_engine_v72_readonly"


CURRENCIES = ("GBP", "USD", "EUR", "JPY", "CAD", "CHF", "AUD", "NZD")
TIMESTAMP_CANDIDATES = ("timestamp", "time", "datetime", "created_at", "ts", "date")
TF_CANDIDATES = ("timeframe", "tf", "timeframe_minutes", "period")
SYMBOL_CANDIDATES = ("symbol", "pair", "instrument")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        # SQLite exports sometimes use "YYYY-mm-dd HH:MM:SS"
        try:
            dt = datetime.strptime(text[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_date_time(date_s: str, time_s: str) -> datetime:
    raw = f"{date_s}T{time_s}:00" if len(time_s.split(":")) == 2 else f"{date_s}T{time_s}"
    dt = datetime.fromisoformat(raw)
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def minute_floor(dt: datetime) -> str:
    return dt.replace(second=0, microsecond=0).isoformat().replace("+00:00", "Z")


def norm_col(name: str) -> str:
    return name.lower().strip()


def q(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def safe_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        v = float(value)
        if not math.isfinite(v):
            return None
        return v
    except (TypeError, ValueError):
        return None


def mean(values: Sequence[float]) -> Optional[float]:
    vals = [v for v in values if v is not None and math.isfinite(v)]
    return float(sum(vals) / len(vals)) if vals else None


def stdev(values: Sequence[float]) -> Optional[float]:
    vals = [v for v in values if v is not None and math.isfinite(v)]
    if len(vals) < 2:
        return None
    return float(statistics.pstdev(vals))


def median(values: Sequence[float]) -> Optional[float]:
    vals = [v for v in values if v is not None and math.isfinite(v)]
    return float(statistics.median(vals)) if vals else None


def rankdata(vals: Sequence[float]) -> List[float]:
    pairs = sorted((v, i) for i, v in enumerate(vals))
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(pairs):
        j = i
        while j + 1 < len(pairs) and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        avg_rank = (i + j + 2) / 2.0
        for k in range(i, j + 1):
            ranks[pairs[k][1]] = avg_rank
        i = j + 1
    return ranks


def spearman(x: Sequence[float], y: Sequence[float]) -> Optional[float]:
    pairs = [(a, b) for a, b in zip(x, y) if a is not None and b is not None and math.isfinite(a) and math.isfinite(b)]
    if len(pairs) < 4:
        return None
    xs, ys = zip(*pairs)
    rx = rankdata(xs)
    ry = rankdata(ys)
    mx = sum(rx) / len(rx)
    my = sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    denx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    deny = math.sqrt(sum((b - my) ** 2 for b in ry))
    if denx <= 0 or deny <= 0:
        return None
    return float(num / (denx * deny))


def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def symbol_to_pair(symbol: str) -> Tuple[str, str]:
    s = (symbol or "GBPUSD").upper().replace("/", "").replace("_", "")
    if len(s) >= 6:
        return s[:3], s[3:6]
    return "GBP", "USD"


@dataclass
class LabConfig:
    db_path: Path
    symbol: str
    start_dt: datetime
    end_dt: datetime
    tfs: List[int]
    out_root: Path
    outcome_window: int = 30
    hypothesis: str = "all"
    table: Optional[str] = None


class LabEngineV72:
    def __init__(self, config: LabConfig):
        self.config = config
        self.base_currency, self.quote_currency = symbol_to_pair(config.symbol)
        self.technical_risks: List[str] = []

    # ------------------------------------------------------------------
    # DB / replay
    # ------------------------------------------------------------------

    def connect_readonly(self) -> sqlite3.Connection:
        path = self.config.db_path
        if not path.exists():
            raise FileNotFoundError(f"DB not found: {path}")
        uri = f"file:{path.as_posix()}?mode=ro" if not path.is_absolute() else f"file:{path.as_posix()}?mode=ro"
        return sqlite3.connect(uri, uri=True)

    def list_tables(self, conn: sqlite3.Connection) -> List[str]:
        return [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

    def table_columns(self, conn: sqlite3.Connection, table: str) -> List[str]:
        return [r[1] for r in conn.execute(f"PRAGMA table_info({q(table)})").fetchall()]

    def choose_table(self, conn: sqlite3.Connection) -> str:
        if self.config.table:
            return self.config.table
        tables = self.list_tables(conn)
        preferred = ["force_snapshots", "force_rolling", "force_rolling_window"]
        for p in preferred:
            if p in tables:
                return p
        if tables:
            self.technical_risks.append("FORCE_TABLE_AUTO_SELECTED")
            return tables[0]
        raise RuntimeError("No table found in DB")

    def choose_column(self, columns: Sequence[str], candidates: Sequence[str]) -> Optional[str]:
        by_norm = {norm_col(c): c for c in columns}
        for cand in candidates:
            if cand in by_norm:
                return by_norm[cand]
        return None

    def currency_col(self, columns: Sequence[str], currency: str) -> Optional[str]:
        target_names = [
            f"force_{currency.lower()}",
            f"force_{currency.upper()}",
            f"FORCE_{currency.upper()}",
            currency.lower(),
            currency.upper(),
        ]
        by_norm = {norm_col(c): c for c in columns}
        for target in target_names:
            if norm_col(target) in by_norm:
                return by_norm[norm_col(target)]
        return None

    def load_rows(self) -> Dict[str, Any]:
        conn = self.connect_readonly()
        try:
            table = self.choose_table(conn)
            columns = self.table_columns(conn, table)
            ts_col = self.choose_column(columns, TIMESTAMP_CANDIDATES)
            tf_col = self.choose_column(columns, TF_CANDIDATES)
            symbol_col = self.choose_column(columns, SYMBOL_CANDIDATES)

            if not ts_col:
                raise RuntimeError(f"No timestamp column found in {table}")

            where = [f"{q(ts_col)} >= ?", f"{q(ts_col)} <= ?"]
            params: List[Any] = [
                self.config.start_dt.isoformat().replace("+00:00", "Z"),
                self.config.end_dt.isoformat().replace("+00:00", "Z"),
            ]

            if symbol_col:
                where.append(f"({q(symbol_col)} = ? OR {q(symbol_col)} IS NULL)")
                params.append(self.config.symbol)

            if tf_col and self.config.tfs:
                placeholders = ",".join("?" for _ in self.config.tfs)
                where.append(f"CAST({q(tf_col)} AS INTEGER) IN ({placeholders})")
                params.extend(self.config.tfs)

            sql = f"SELECT * FROM {q(table)} WHERE {' AND '.join(where)} ORDER BY {q(ts_col)} ASC"
            conn.row_factory = sqlite3.Row
            rows = [dict(r) for r in conn.execute(sql, params).fetchall()]

            return {
                "table": table,
                "columns": columns,
                "timestamp_column": ts_col,
                "timeframe_column": tf_col,
                "symbol_column": symbol_col,
                "rows": rows,
            }
        finally:
            conn.close()

    def build_replay_raw(self, loaded: Dict[str, Any]) -> Dict[str, Any]:
        rows = loaded["rows"]
        ts_col = loaded["timestamp_column"]
        tf_col = loaded["timeframe_column"]

        frames: Dict[str, Dict[str, Any]] = {}

        for row in rows:
            dt = parse_dt(row.get(ts_col))
            if not dt:
                continue
            minute = minute_floor(dt)
            frame = frames.setdefault(minute, {"minute": minute, "rows_count": 0, "timeframes": {}})
            frame["rows_count"] += 1

            tf = row.get(tf_col) if tf_col else None
            tf_key = str(int(tf)) if safe_float(tf) is not None else "UNKNOWN"
            frame["timeframes"].setdefault(tf_key, []).append(row)

        ordered = [frames[k] for k in sorted(frames.keys())]
        tfs_found = sorted({tf for f in ordered for tf in f["timeframes"].keys()})

        return {
            "valid": True,
            "method": METHOD,
            "version": VERSION,
            "generated_at": utc_now_iso(),
            "db_path": str(self.config.db_path),
            "table": loaded["table"],
            "symbol": self.config.symbol,
            "window": {
                "start": self.config.start_dt.isoformat().replace("+00:00", "Z"),
                "end": self.config.end_dt.isoformat().replace("+00:00", "Z"),
            },
            "timestamp_column": loaded["timestamp_column"],
            "timeframe_column": loaded["timeframe_column"],
            "symbol_column": loaded["symbol_column"],
            "frames_count": len(ordered),
            "rows_count": len(rows),
            "timeframes_found": tfs_found,
            "technical_risks": list(dict.fromkeys(self.technical_risks)),
            "frames": ordered,
        }

    # ------------------------------------------------------------------
    # Enrichment
    # ------------------------------------------------------------------

    def row_force(self, row: Dict[str, Any], columns: Sequence[str], currency: str) -> Optional[float]:
        col = self.currency_col(columns, currency)
        return safe_float(row.get(col)) if col else None

    def choose_primary_row(self, frame: Dict[str, Any], preferred_tf: int = 1) -> Optional[Dict[str, Any]]:
        tfs = frame.get("timeframes", {})
        if str(preferred_tf) in tfs and tfs[str(preferred_tf)]:
            return tfs[str(preferred_tf)][-1]
        # Choose lowest available TF as microfilm.
        numeric = []
        for k in tfs:
            try:
                numeric.append(int(k))
            except ValueError:
                pass
        if numeric:
            k = str(sorted(numeric)[0])
            return tfs[k][-1]
        for rows in tfs.values():
            if rows:
                return rows[-1]
        return None

    def frame_pair_force_by_tf(self, frame: Dict[str, Any], columns: Sequence[str]) -> Dict[str, Dict[str, Any]]:
        out: Dict[str, Dict[str, Any]] = {}
        for tf, rows in frame.get("timeframes", {}).items():
            if not rows:
                continue
            row = rows[-1]
            bf = self.row_force(row, columns, self.base_currency)
            qf = self.row_force(row, columns, self.quote_currency)
            diff = bf - qf if bf is not None and qf is not None else None
            out[tf] = {
                "base_force": bf,
                "quote_force": qf,
                "force_diff": diff,
            }
        return out

    def enrich_frames(self, replay_raw: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        columns = loaded["columns"]
        frames = replay_raw["frames"]

        enriched_frames: List[Dict[str, Any]] = []
        history_diff: List[float] = []
        history_base: List[float] = []
        history_quote: List[float] = []

        prev_diff: Optional[float] = None
        prev_angle: Optional[float] = None

        for idx, frame in enumerate(frames):
            by_tf = self.frame_pair_force_by_tf(frame, columns)
            primary_row = self.choose_primary_row(frame)
            primary_tf = None
            primary_diff = None
            base_force = None
            quote_force = None

            if by_tf:
                numeric = []
                for k in by_tf:
                    try:
                        numeric.append(int(k))
                    except ValueError:
                        pass
                primary_tf = str(sorted(numeric)[0]) if numeric else next(iter(by_tf))
                primary_diff = by_tf[primary_tf]["force_diff"]
                base_force = by_tf[primary_tf]["base_force"]
                quote_force = by_tf[primary_tf]["quote_force"]

            if primary_diff is not None:
                history_diff.append(primary_diff)
            if base_force is not None:
                history_base.append(base_force)
            if quote_force is not None:
                history_quote.append(quote_force)

            angle = None if primary_diff is None or prev_diff is None else primary_diff - prev_diff
            speed = None if angle is None else abs(angle)
            acceleration = None if angle is None or prev_angle is None else angle - prev_angle

            recent_angles = []
            if len(history_diff) >= 2:
                for a, b in zip(history_diff[-12:-1], history_diff[-11:]):
                    recent_angles.append(b - a)

            noise = self.compute_noise_ratio(recent_angles)
            b1 = self.classify_regime(history_diff)
            b4 = self.classify_cycle(history_diff, noise)
            b5 = self.classify_spearman(history_base, history_quote)
            eie = self.classify_eie(history_diff)
            b7 = self.classify_b7(by_tf, enriched_frames)

            pseudo_alert = {
                "alert_type": "LAB_FRAME",
                "symbol": self.config.symbol,
                "timeframe": int(primary_tf) if primary_tf and primary_tf.isdigit() else None,
                "timestamp": frame["minute"],
                "regime_context": {"regime": b1["regime"], "confidence": b1["confidence"]},
                "session_context": {"session": session_from_time(frame["minute"])},
                "EIE_state": eie["eie_state"],
                "B4_state": b4["cycle_state"],
                "B5_direction": b5["direction"],
                "B3_noise_ratio": noise,
                "B7_state": b7["resonance_state"],
                "technical_risks": [],
            }

            scene = infer_scene_safe(pseudo_alert)
            footprint = classify_structural_footprint(b1, b4, b5, eie, b7, noise, scene)

            enriched = {
                "minute": frame["minute"],
                "index": idx,
                "rows_count": frame["rows_count"],
                "primary_tf": primary_tf,
                "pair": {
                    "symbol": self.config.symbol,
                    "base": self.base_currency,
                    "quote": self.quote_currency,
                    "base_force": base_force,
                    "quote_force": quote_force,
                    "force_diff": primary_diff,
                },
                "B1_regime": b1,
                "B3_kinematics": {
                    "angle_proxy": angle,
                    "speed_magnitude": speed,
                    "acceleration_proxy": acceleration,
                    "noise_ratio": noise,
                    "kinematics_state": classify_kinematics(angle, speed, noise),
                },
                "B4_density": b4,
                "B5_relation": b5,
                "EIE_zone": eie,
                "B7_resonance": b7,
                "scene_context": scene,
                "structural_footprint": footprint,
                "by_timeframe": by_tf,
                "technical_risks": list(dict.fromkeys(
                    b1.get("technical_risks", []) +
                    b4.get("technical_risks", []) +
                    b5.get("technical_risks", []) +
                    eie.get("technical_risks", []) +
                    b7.get("technical_risks", []) +
                    scene.get("technical_risks", []) +
                    footprint.get("technical_risks", [])
                )),
            }

            enriched_frames.append(enriched)

            if primary_diff is not None:
                prev_diff = primary_diff
            if angle is not None:
                prev_angle = angle

        return {
            "valid": True,
            "method": METHOD,
            "version": VERSION,
            "generated_at": utc_now_iso(),
            "symbol": self.config.symbol,
            "frames_count": len(enriched_frames),
            "technical_risks": list(dict.fromkeys(self.technical_risks)),
            "frames": enriched_frames,
        }

    def compute_noise_ratio(self, angles: Sequence[float]) -> Optional[float]:
        vals = [v for v in angles if v is not None and math.isfinite(v)]
        if len(vals) < 4:
            return None
        sd = statistics.pstdev(vals)
        avg_abs = sum(abs(v) for v in vals) / len(vals)
        if avg_abs <= 1e-9:
            return 0.0
        return round(clamp(sd / (avg_abs * 3.0), 0.0, 1.0), 6)

    def classify_regime(self, diffs: Sequence[float]) -> Dict[str, Any]:
        vals = [v for v in diffs[-36:] if v is not None and math.isfinite(v)]
        if len(vals) < 8:
            return {"regime": "UNKNOWN", "confidence": 0.0, "technical_risks": ["INSUFFICIENT_REGIME_WINDOW"]}

        recent = vals[-12:]
        long = vals
        recent_range = max(recent) - min(recent)
        long_range = max(long) - min(long)
        trend = recent[-1] - recent[0]
        sd_recent = stdev(recent) or 0.0
        sd_long = stdev(long) or 0.0
        compression_ratio = recent_range / long_range if long_range > 1e-9 else 0.0

        if compression_ratio < 0.35 and sd_recent < sd_long:
            regime = "COMPRESSION"
            confidence = 0.70
        elif abs(trend) > (sd_long * 1.25 if sd_long else 0.0) and abs(trend) > recent_range * 0.45:
            regime = "TENDANCE"
            confidence = 0.66
        elif recent_range < (sd_long * 1.15 if sd_long else recent_range + 1):
            regime = "RANGE"
            confidence = 0.58
        else:
            regime = "TRANSITION"
            confidence = 0.52

        return {
            "regime": regime,
            "confidence": round(confidence, 4),
            "compression_ratio_proxy": round(compression_ratio, 6),
            "trend_proxy": round(trend, 6),
            "technical_risks": ["REGIME_PROXY_NOT_HMM"],
        }

    def classify_cycle(self, diffs: Sequence[float], noise: Optional[float]) -> Dict[str, Any]:
        vals = [v for v in diffs if v is not None and math.isfinite(v)]
        if len(vals) < 16:
            return {"cycle_state": "UNKNOWN", "compression_ratio": None, "technical_risks": ["INSUFFICIENT_B4_WINDOW"]}

        short = vals[-8:]
        mid = vals[-24:] if len(vals) >= 24 else vals
        sd_short = stdev(short) or 0.0
        sd_mid = stdev(mid) or 0.0
        ratio = sd_short / sd_mid if sd_mid > 1e-9 else 0.0

        if noise is not None and noise > 0.60:
            state = "CYCLE_NOISY"
        elif ratio < 0.65:
            state = "CYCLE_COMPRESSING"
        elif ratio > 1.25:
            state = "CYCLE_EXPANDING"
        else:
            state = "CYCLE_STABLE"

        risks = ["B4_PROXY_NOT_WAVELET"]
        if state == "CYCLE_COMPRESSING" and noise is not None and noise > 0.35:
            risks.append("B4_COMPRESSING_WITH_B3_NOISE_HIGH")

        return {
            "cycle_state": state,
            "compression_ratio": round(1.0 - clamp(ratio, 0.0, 1.0), 6),
            "vol_ratio_short_mid": round(ratio, 6),
            "technical_risks": risks,
        }

    def classify_spearman(self, base_values: Sequence[float], quote_values: Sequence[float]) -> Dict[str, Any]:
        rho = spearman(base_values[-30:], quote_values[-30:])
        if rho is None:
            return {"spearman_rho": None, "direction": "UNKNOWN", "tail_signal": "UNKNOWN", "technical_risks": ["INSUFFICIENT_B5_WINDOW"]}

        if rho > 0.70:
            direction = "SYNCHRO"
        elif rho < -0.50:
            direction = "DIVERGENT"
        else:
            direction = "NEUTRAL"

        if rho > 0.85:
            tail = "CODEPENDANT_EXTREME"
        elif rho < -0.85:
            tail = "DIVERGENT_EXTREME"
        else:
            tail = "MIXED_PROBABILISTE" if -0.50 <= rho <= 0.70 else direction

        return {
            "spearman_rho": round(rho, 6),
            "direction": tail if tail in {"CODEPENDANT_EXTREME", "DIVERGENT_EXTREME"} else direction,
            "relation_state": direction,
            "tail_signal": tail,
            "technical_risks": ["B5_RELATION_NOT_LEADERSHIP"],
        }

    def classify_eie(self, diffs: Sequence[float]) -> Dict[str, Any]:
        vals = [v for v in diffs[-48:] if v is not None and math.isfinite(v)]
        if len(vals) < 12:
            return {"eie_state": "UNKNOWN", "zscore_proxy": None, "technical_risks": ["INSUFFICIENT_EIE_WINDOW"]}

        m = mean(vals) or 0.0
        sd = stdev(vals) or 0.0
        z = (vals[-1] - m) / sd if sd > 1e-9 else 0.0
        az = abs(z)

        if az > 2.2:
            state = "ELASTIC_IN_EXTREME"
        elif az > 1.5:
            state = "PRE_EXTREME"
        elif az > 1.0:
            state = "ACCUMULATING"
        else:
            state = "NEUTRAL"

        return {
            "eie_state": state,
            "zscore_proxy": round(z, 6),
            "technical_risks": ["EIE_PROXY_NOT_FULL_CONFLUENCE"],
        }

    def classify_b7(self, by_tf: Dict[str, Dict[str, Any]], previous_frames: List[Dict[str, Any]]) -> Dict[str, Any]:
        diffs = []
        for tf, data in by_tf.items():
            d = data.get("force_diff")
            if d is not None:
                diffs.append((tf, d))

        if len(diffs) < 2:
            return {"resonance_state": "SILENT", "resonance_score": 0.0, "technical_risks": ["INSUFFICIENT_TF_RESONANCE"]}

        signs = [1 if d > 0 else -1 if d < 0 else 0 for _, d in diffs]
        nonzero = [s for s in signs if s != 0]
        if not nonzero:
            return {"resonance_state": "SILENT", "resonance_score": 0.0, "technical_risks": []}

        pos = nonzero.count(1)
        neg = nonzero.count(-1)
        alignment = max(pos, neg) / len(nonzero)

        if alignment >= 0.80:
            state = "RESONANT"
        elif alignment <= 0.55:
            state = "DISSONANT"
        else:
            state = "LAGGED"

        return {
            "resonance_state": state,
            "resonance_score": round(alignment, 6),
            "technical_risks": ["B7_PROXY_SIMPLE_TF_SIGN_ALIGNMENT"],
        }

    # ------------------------------------------------------------------
    # Scenes and outcomes
    # ------------------------------------------------------------------

    def build_scene_timeline(self, replay_enriched: Dict[str, Any]) -> Dict[str, Any]:
        scenes = []
        for frame in replay_enriched["frames"]:
            scene = frame.get("scene_context", {})
            scene_id = scene.get("scene_id", "UNKNOWN_SCENE")
            conf = scene.get("scene_confidence_non_blocking", 0.0)
            footprint = frame.get("structural_footprint", {})
            comp = get_nested(scene, ["compression_qualification", "compression_label"], "UNKNOWN")

            if scene_id != "UNKNOWN_SCENE" or comp in {"COMPRESSION_REAL_CANDIDATE", "COMPRESSION_FAKE_RISK"} or footprint.get("footprint_state") != "NO_STRUCTURAL_FOOTPRINT":
                scenes.append({
                    "minute": frame["minute"],
                    "index": frame["index"],
                    "scene_id": scene_id,
                    "scene_family": scene.get("scene_family", "UNKNOWN"),
                    "scene_confidence_non_blocking": conf,
                    "compression_qualification": comp,
                    "structural_footprint": footprint,
                    "B1_regime": frame.get("B1_regime", {}).get("regime"),
                    "B4_state": frame.get("B4_density", {}).get("cycle_state"),
                    "B5_direction": frame.get("B5_relation", {}).get("direction"),
                    "EIE_state": frame.get("EIE_zone", {}).get("eie_state"),
                    "B7_state": frame.get("B7_resonance", {}).get("resonance_state"),
                    "technical_risks": frame.get("technical_risks", []),
                })

        return {
            "valid": True,
            "method": METHOD,
            "version": VERSION,
            "generated_at": utc_now_iso(),
            "total_scenes": len(scenes),
            "scenes": scenes,
        }

    def build_cause_consequence(self, replay_enriched: Dict[str, Any], scene_timeline: Dict[str, Any]) -> Dict[str, Any]:
        frames = replay_enriched["frames"]
        events = []
        outcome_window = self.config.outcome_window

        for scene in scene_timeline["scenes"]:
            idx = scene["index"]
            before = frames[max(0, idx - 15):idx]
            after = frames[idx + 1:min(len(frames), idx + 1 + outcome_window)]
            current = frames[idx]

            before_summary = summarize_window(before)
            after_summary = summarize_window(after)
            outcome = classify_outcome(current, after, outcome_window)

            events.append({
                "t0": scene["minute"],
                "index": idx,
                "scene_id": scene["scene_id"],
                "compression_qualification": scene["compression_qualification"],
                "cause_window_minutes": 15,
                "consequence_window_minutes": outcome_window,
                "before": before_summary,
                "at_event": event_snapshot(current),
                "after": after_summary,
                "observed_outcome": outcome,
                "technical_risks": list(dict.fromkeys(scene.get("technical_risks", []) + outcome.get("technical_risks", []))),
            })

        return {
            "valid": True,
            "method": METHOD,
            "version": VERSION,
            "generated_at": utc_now_iso(),
            "events_count": len(events),
            "events": events,
        }

    def build_lab_metrics(self, replay_enriched: Dict[str, Any], scene_timeline: Dict[str, Any], cause_consequence: Dict[str, Any]) -> Dict[str, Any]:
        frames = replay_enriched["frames"]
        scenes = scene_timeline["scenes"]

        by_scene = Counter(s["scene_id"] for s in scenes)
        by_comp = Counter(s["compression_qualification"] for s in scenes)
        by_footprint = Counter(get_nested(s, ["structural_footprint", "footprint_state"], "UNKNOWN") for s in scenes)
        by_outcome = Counter(e["observed_outcome"]["outcome"] for e in cause_consequence["events"])

        noise_values = [get_nested(f, ["B3_kinematics", "noise_ratio"]) for f in frames]
        noise_values = [v for v in noise_values if v is not None]
        move_bars = [get_nested(e, ["observed_outcome", "bars_to_move"]) for e in cause_consequence["events"]]
        move_bars = [v for v in move_bars if v is not None]

        return {
            "valid": True,
            "method": METHOD,
            "version": VERSION,
            "generated_at": utc_now_iso(),
            "symbol": self.config.symbol,
            "window": {
                "start": self.config.start_dt.isoformat().replace("+00:00", "Z"),
                "end": self.config.end_dt.isoformat().replace("+00:00", "Z"),
            },
            "frames_count": len(frames),
            "scenes_count": len(scenes),
            "by_scene_id": dict(by_scene),
            "by_compression_qualification": dict(by_comp),
            "by_structural_footprint": dict(by_footprint),
            "by_observed_outcome": dict(by_outcome),
            "median_bars_to_move": median(move_bars),
            "average_noise_ratio": mean(noise_values),
            "hypothesis": self.config.hypothesis,
            "hypothesis_notes": self.hypothesis_notes(by_comp, by_outcome),
            "technical_risks": list(dict.fromkeys(self.technical_risks + collect_risks(frames))),
            "no_trade_decision": True,
            "no_filtering": True,
            "db_readonly": True,
        }

    def hypothesis_notes(self, by_comp: Counter, by_outcome: Counter) -> List[str]:
        notes = []
        if self.config.hypothesis in {"all", "compression_real_vs_fake"}:
            real = by_comp.get("COMPRESSION_REAL_CANDIDATE", 0)
            fake = by_comp.get("COMPRESSION_FAKE_RISK", 0)
            notes.append(f"compression_real_candidate={real}")
            notes.append(f"compression_fake_risk={fake}")
        if self.config.hypothesis in {"all", "second_leg"}:
            notes.append(f"second_leg_confirmed={by_outcome.get('SECOND_LEG_CONFIRMED', 0)}")
        return notes

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------

    def write_film(self, scene_timeline: Dict[str, Any], cause_consequence: Dict[str, Any], path: Path) -> None:
        lines = [
            "# PowerFlow V7.2 — Film comportemental",
            "",
            f"**Generated at:** {utc_now_iso()}",
            f"**Symbol:** `{self.config.symbol}`",
            f"**Window:** `{self.config.start_dt.isoformat().replace('+00:00','Z')}` → `{self.config.end_dt.isoformat().replace('+00:00','Z')}`",
            "",
            "## Doctrine",
            "",
            "Ce film rejoue et nomme les scènes observées. Il ne produit aucune décision.",
            "",
        ]

        if not cause_consequence["events"]:
            lines += ["Aucune scène structurée détectée dans cette fenêtre.", ""]
        else:
            for event in cause_consequence["events"]:
                lines += [
                    f"## {event['t0']} — {event['scene_id']}",
                    "",
                    f"- Compression qualification : `{event['compression_qualification']}`",
                    f"- Outcome observé : `{event['observed_outcome']['outcome']}`",
                    f"- Bars to move : `{event['observed_outcome'].get('bars_to_move')}`",
                    "",
                    "### Avant",
                    "",
                    dict_to_bullets(event["before"]),
                    "",
                    "### À t0",
                    "",
                    dict_to_bullets(event["at_event"]),
                    "",
                    "### Après",
                    "",
                    dict_to_bullets(event["after"]),
                    "",
                    "### Risques techniques",
                    "",
                    "\n".join(f"- `{r}`" for r in event.get("technical_risks", [])) or "- Aucun",
                    "",
                ]

        path.write_text("\n".join(lines), encoding="utf-8")

    def write_markdown_report(self, lab_metrics: Dict[str, Any], path: Path) -> None:
        lines = [
            "# PowerFlow V7.2 — Lab Report",
            "",
            f"**Generated at:** {lab_metrics.get('generated_at')}",
            f"**Symbol:** `{lab_metrics.get('symbol')}`",
            f"**Frames:** `{lab_metrics.get('frames_count')}`",
            f"**Scenes:** `{lab_metrics.get('scenes_count')}`",
            "",
            "## Doctrine",
            "",
            "- Read-only DB.",
            "- No BUY/SELL.",
            "- No trade decision.",
            "- No filtering.",
            "- Footprints are candidates, never institutional certainties.",
            "",
            "## Scene distribution",
            "",
            dict_to_bullets(lab_metrics.get("by_scene_id", {})),
            "",
            "## Compression qualification",
            "",
            dict_to_bullets(lab_metrics.get("by_compression_qualification", {})),
            "",
            "## Structural footprints",
            "",
            dict_to_bullets(lab_metrics.get("by_structural_footprint", {})),
            "",
            "## Observed outcomes",
            "",
            dict_to_bullets(lab_metrics.get("by_observed_outcome", {})),
            "",
            "## Metrics",
            "",
            f"- Median bars to move: `{lab_metrics.get('median_bars_to_move')}`",
            f"- Average noise ratio: `{lab_metrics.get('average_noise_ratio')}`",
            "",
            "## Hypothesis notes",
            "",
            "\n".join(f"- `{x}`" for x in lab_metrics.get("hypothesis_notes", [])) or "- None",
            "",
            "## Technical risks",
            "",
            "\n".join(f"- `{x}`" for x in lab_metrics.get("technical_risks", [])) or "- None",
            "",
        ]
        path.write_text("\n".join(lines), encoding="utf-8")

    def write_html_report(self, lab_metrics: Dict[str, Any], cause_consequence: Dict[str, Any], path: Path) -> None:
        cards = []
        for event in cause_consequence["events"][:200]:
            risks = "".join(f"<span class='badge'>{html.escape(str(r))}</span>" for r in event.get("technical_risks", []))
            cards.append(f"""
<section class="card">
  <h2>{html.escape(event['t0'])} — {html.escape(event['scene_id'])}</h2>
  <p><strong>Compression:</strong> {html.escape(event['compression_qualification'])}</p>
  <p><strong>Outcome:</strong> {html.escape(event['observed_outcome']['outcome'])} | bars={html.escape(str(event['observed_outcome'].get('bars_to_move')))}</p>
  <h3>At event</h3><pre>{html.escape(json.dumps(event['at_event'], indent=2, ensure_ascii=False))}</pre>
  <h3>Risks</h3><p>{risks or 'None'}</p>
</section>
""")

        doc = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>PowerFlow V7.2 Lab Report</title>
<style>
body{{background:#0a0a0a;color:#e6e6e6;font-family:Courier New,monospace;padding:20px}}
h1,h2{{color:#fff}} .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}}
.metric,.card{{background:#111;border:1px solid #252525;border-left:4px solid #00ff66;border-radius:10px;padding:12px;margin:12px 0}}
.value{{font-size:24px;color:#00ff66;font-weight:bold}} pre{{background:#050505;padding:10px;overflow:auto;border-radius:8px}}
.badge{{display:inline-block;padding:2px 6px;border:1px solid #333;border-radius:999px;margin:2px;color:#ffe600}}
</style>
</head>
<body>
<h1>PowerFlow V7.2 — Lab Report</h1>
<p>Read-only replay. No filtering. No trade decision.</p>
<div class="grid">
<div class="metric"><div>Frames</div><div class="value">{lab_metrics.get('frames_count')}</div></div>
<div class="metric"><div>Scenes</div><div class="value">{lab_metrics.get('scenes_count')}</div></div>
<div class="metric"><div>Median bars to move</div><div class="value">{lab_metrics.get('median_bars_to_move')}</div></div>
<div class="metric"><div>Average noise</div><div class="value">{lab_metrics.get('average_noise_ratio')}</div></div>
</div>
<h2>Metrics raw</h2>
<pre>{html.escape(json.dumps(lab_metrics, indent=2, ensure_ascii=False))}</pre>
<h2>Events</h2>
{''.join(cards) if cards else '<p>No structured events detected.</p>'}
</body>
</html>"""
        path.write_text(doc, encoding="utf-8")

    def run(self) -> Dict[str, Any]:
        loaded = self.load_rows()
        run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.config.symbol}_{self.config.start_dt.strftime('%H%M')}_{self.config.end_dt.strftime('%H%M')}"
        out_dir = self.config.out_root / "lab_runs" / run_id
        out_dir.mkdir(parents=True, exist_ok=True)

        replay_raw = self.build_replay_raw(loaded)
        replay_enriched = self.enrich_frames(replay_raw, loaded)
        scene_timeline = self.build_scene_timeline(replay_enriched)
        cause_consequence = self.build_cause_consequence(replay_enriched, scene_timeline)
        lab_metrics = self.build_lab_metrics(replay_enriched, scene_timeline, cause_consequence)

        write_json(out_dir / "replay_raw.json", replay_raw)
        write_json(out_dir / "replay_enriched.json", replay_enriched)
        write_json(out_dir / "scene_timeline.json", scene_timeline)
        write_json(out_dir / "cause_consequence.json", cause_consequence)
        write_json(out_dir / "lab_metrics.json", lab_metrics)
        self.write_film(scene_timeline, cause_consequence, out_dir / "film_behavioral.md")
        self.write_markdown_report(lab_metrics, out_dir / "lab_report.md")
        self.write_html_report(lab_metrics, cause_consequence, out_dir / "lab_report.html")

        return {
            "valid": True,
            "method": METHOD,
            "version": VERSION,
            "run_id": run_id,
            "out_dir": str(out_dir),
            "files": {
                "replay_raw": str(out_dir / "replay_raw.json"),
                "replay_enriched": str(out_dir / "replay_enriched.json"),
                "scene_timeline": str(out_dir / "scene_timeline.json"),
                "cause_consequence": str(out_dir / "cause_consequence.json"),
                "lab_metrics": str(out_dir / "lab_metrics.json"),
                "film_behavioral": str(out_dir / "film_behavioral.md"),
                "lab_report_md": str(out_dir / "lab_report.md"),
                "lab_report_html": str(out_dir / "lab_report.html"),
            },
            "summary": {
                "frames_count": lab_metrics["frames_count"],
                "scenes_count": lab_metrics["scenes_count"],
                "by_scene_id": lab_metrics["by_scene_id"],
                "by_compression_qualification": lab_metrics["by_compression_qualification"],
                "by_structural_footprint": lab_metrics["by_structural_footprint"],
                "by_observed_outcome": lab_metrics["by_observed_outcome"],
            },
            "technical_risks": lab_metrics["technical_risks"],
            "no_trade_decision": True,
            "no_filtering": True,
            "db_readonly": True,
        }


# ----------------------------------------------------------------------
# Helpers outside class
# ----------------------------------------------------------------------

def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def get_nested(obj: Dict[str, Any], path: Sequence[str], default: Any = None) -> Any:
    cur: Any = obj
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur


def classify_kinematics(angle: Optional[float], speed: Optional[float], noise: Optional[float]) -> str:
    if angle is None:
        return "UNKNOWN"
    if noise is not None and noise > 0.60:
        return "NOISY"
    if speed is not None and speed > 0:
        if angle > 0:
            return "UP_ACCELERATION"
        if angle < 0:
            return "DOWN_ACCELERATION"
    return "STABLE"


def session_from_time(minute: str) -> str:
    dt = parse_dt(minute)
    if not dt:
        return "UNKNOWN"
    h = dt.hour
    if 0 <= h < 7:
        return "ASIAN"
    if 7 <= h < 12:
        return "LONDON"
    if 12 <= h < 17:
        return "NY_OVERLAP"
    if 17 <= h < 22:
        return "NY"
    return "OFF_HOURS"


def infer_scene_safe(alert: Dict[str, Any]) -> Dict[str, Any]:
    try:
        from pf_scene_registry import infer_scene  # type: ignore
        return infer_scene(alert)
    except Exception:
        # Fallback minimal scene logic if Scene Registry not installed.
        b4 = str(alert.get("B4_state", "UNKNOWN"))
        regime = get_nested(alert, ["regime_context", "regime"], "UNKNOWN")
        b5 = str(alert.get("B5_direction", "UNKNOWN"))
        eie = str(alert.get("EIE_state", "UNKNOWN"))
        noise = alert.get("B3_noise_ratio")

        comp = "NO_B4_COMPRESSION"
        if "COMPRESS" in b4:
            if regime in {"COMPRESSION", "TRANSITION"} and b5 not in {"NEUTRAL", "UNKNOWN"} and eie not in {"NEUTRAL", "UNKNOWN", "ABSENT"} and (noise is None or noise < 0.35):
                comp = "COMPRESSION_REAL_CANDIDATE"
                scene_id = "ZONE_BREATH_COMPRESSION"
                conf = 0.72
            elif regime in {"RANGE", "UNKNOWN"} and b5 in {"NEUTRAL", "UNKNOWN"} and (noise is not None and noise > 0.35):
                comp = "COMPRESSION_FAKE_RISK"
                scene_id = "ZONE_BREATH_COMPRESSION"
                conf = 0.55
            else:
                comp = "COMPRESSION_AMBIGUOUS"
                scene_id = "UNKNOWN_SCENE"
                conf = 0.25
        else:
            scene_id = "UNKNOWN_SCENE"
            conf = 0.0

        return {
            "scene_id": scene_id,
            "scene_family": "COMPRESSION" if scene_id == "ZONE_BREATH_COMPRESSION" else "UNKNOWN",
            "scene_confidence_non_blocking": conf,
            "compression_qualification": {"compression_label": comp, "technical_risks": []},
            "technical_risks": ["SCENE_REGISTRY_NOT_AVAILABLE"],
            "metrics_only": True,
            "no_filtering": True,
            "no_trade_decision": True,
        }


def classify_structural_footprint(
    b1: Dict[str, Any],
    b4: Dict[str, Any],
    b5: Dict[str, Any],
    eie: Dict[str, Any],
    b7: Dict[str, Any],
    noise: Optional[float],
    scene: Dict[str, Any],
) -> Dict[str, Any]:
    regime = b1.get("regime")
    cycle = b4.get("cycle_state")
    rel = b5.get("direction")
    eie_state = eie.get("eie_state")
    b7_state = b7.get("resonance_state")
    scene_id = scene.get("scene_id")

    risks = ["INFERENCE_ONLY", "NO_VOLUME_DATA", "NO_ORDERBOOK_DATA"]
    score = 0.0

    if regime in {"COMPRESSION", "TRANSITION", "TENDANCE"}:
        score += 0.18
    if cycle in {"CYCLE_COMPRESSING", "CYCLE_EXPANDING", "CYCLE_STABLE"}:
        score += 0.16
    if rel not in {"NEUTRAL", "UNKNOWN", None}:
        score += 0.18
    if eie_state not in {"NEUTRAL", "UNKNOWN", "ABSENT", None}:
        score += 0.18
    if noise is not None and noise < 0.25:
        score += 0.14
    if b7_state in {"RESONANT", "LAGGED"}:
        score += 0.10
    if scene_id not in {"UNKNOWN_SCENE", None}:
        score += 0.06

    if score >= 0.70:
        state = "STRUCTURAL_FLOW_FOOTPRINT_CANDIDATE"
    elif scene_id == "PULLBACK_ABSORBED":
        state = "ABSORPTION_FOOTPRINT_CANDIDATE"
    elif scene_id == "REPULSION_CLEAN":
        state = "CLEAN_REPULSION_FOOTPRINT_CANDIDATE"
    elif scene_id == "PRICE_LAG_CATCH_UP":
        state = "DELAYED_CATCH_UP_FOOTPRINT_CANDIDATE"
    else:
        state = "NO_STRUCTURAL_FOOTPRINT"

    if noise is not None and noise > 0.35:
        risks.append("B3_NOISE_HIGH")
    if rel in {"NEUTRAL", "UNKNOWN", None}:
        risks.append("B5_RELATION_UNCLEAR")
    if eie_state in {"NEUTRAL", "UNKNOWN", "ABSENT", None}:
        risks.append("EIE_ABSENT")

    return {
        "footprint_state": state,
        "confidence_non_blocking": round(clamp(score), 4),
        "technical_risks": risks,
    }


def summarize_window(frames: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not frames:
        return {"frames": 0, "technical_risks": ["EMPTY_WINDOW"]}

    regimes = Counter(get_nested(f, ["B1_regime", "regime"], "UNKNOWN") for f in frames)
    cycles = Counter(get_nested(f, ["B4_density", "cycle_state"], "UNKNOWN") for f in frames)
    relations = Counter(get_nested(f, ["B5_relation", "direction"], "UNKNOWN") for f in frames)
    scenes = Counter(get_nested(f, ["scene_context", "scene_id"], "UNKNOWN_SCENE") for f in frames)
    footprints = Counter(get_nested(f, ["structural_footprint", "footprint_state"], "NO_STRUCTURAL_FOOTPRINT") for f in frames)
    diffs = [get_nested(f, ["pair", "force_diff"]) for f in frames]
    diffs = [d for d in diffs if d is not None]
    noise = [get_nested(f, ["B3_kinematics", "noise_ratio"]) for f in frames]
    noise = [n for n in noise if n is not None]

    return {
        "frames": len(frames),
        "dominant_regime": regimes.most_common(1)[0][0],
        "dominant_cycle": cycles.most_common(1)[0][0],
        "dominant_relation": relations.most_common(1)[0][0],
        "dominant_scene": scenes.most_common(1)[0][0],
        "dominant_footprint": footprints.most_common(1)[0][0],
        "force_diff_start": diffs[0] if diffs else None,
        "force_diff_end": diffs[-1] if diffs else None,
        "force_diff_delta": (diffs[-1] - diffs[0]) if len(diffs) >= 2 else None,
        "avg_noise_ratio": mean(noise),
    }


def event_snapshot(frame: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "minute": frame.get("minute"),
        "force_diff": get_nested(frame, ["pair", "force_diff"]),
        "B1_regime": frame.get("B1_regime"),
        "B3_kinematics": frame.get("B3_kinematics"),
        "B4_density": frame.get("B4_density"),
        "B5_relation": frame.get("B5_relation"),
        "EIE_zone": frame.get("EIE_zone"),
        "B7_resonance": frame.get("B7_resonance"),
        "scene_context": frame.get("scene_context"),
        "structural_footprint": frame.get("structural_footprint"),
    }


def classify_outcome(current: Dict[str, Any], after: List[Dict[str, Any]], outcome_window: int) -> Dict[str, Any]:
    cur_diff = get_nested(current, ["pair", "force_diff"])
    if cur_diff is None or not after:
        return {"outcome": "NO_FOLLOW_THROUGH", "bars_to_move": None, "technical_risks": ["NO_AFTER_WINDOW_OR_FORCE_DIFF"]}

    cur = float(cur_diff)
    future_diffs = [get_nested(f, ["pair", "force_diff"]) for f in after]
    future_diffs = [float(d) for d in future_diffs if d is not None]
    if not future_diffs:
        return {"outcome": "NO_FOLLOW_THROUGH", "bars_to_move": None, "technical_risks": ["NO_FUTURE_FORCE_DIFF"]}

    deltas = [d - cur for d in future_diffs]
    max_abs = max(abs(d) for d in deltas)
    end_delta = future_diffs[-1] - cur
    threshold = max(0.5, (stdev(future_diffs) or 0.0) * 0.8)

    bars_to_move = None
    for i, d in enumerate(deltas, start=1):
        if abs(d) >= threshold:
            bars_to_move = i
            break

    if max_abs < threshold:
        outcome = "NO_FOLLOW_THROUGH"
    elif abs(end_delta) >= threshold and bars_to_move is not None and bars_to_move <= max(3, outcome_window // 3):
        outcome = "RELEASE_CONFIRMED"
    elif bars_to_move is not None and bars_to_move > max(3, outcome_window // 3):
        outcome = "DELAYED_RELEASE"
    elif end_delta * deltas[0] < 0:
        outcome = "REJECTION"
    else:
        outcome = "SECOND_LEG_CONFIRMED" if max_abs >= threshold * 1.5 else "MOVE_OBSERVED"

    return {
        "outcome": outcome,
        "bars_to_move": bars_to_move,
        "max_abs_force_extension": round(max_abs, 6),
        "end_delta": round(end_delta, 6),
        "threshold_used": round(threshold, 6),
        "technical_risks": ["OUTCOME_PROXY_FORCE_DIFF"],
    }


def collect_risks(frames: List[Dict[str, Any]]) -> List[str]:
    out = []
    for f in frames:
        out.extend(f.get("technical_risks", []))
    return list(dict.fromkeys(out))


def dict_to_bullets(obj: Any) -> str:
    if isinstance(obj, dict):
        if not obj:
            return "- Empty"
        return "\n".join(f"- `{k}`: `{v}`" for k, v in obj.items())
    return f"- `{obj}`"


def run_lab(config: LabConfig) -> Dict[str, Any]:
    return LabEngineV72(config).run()
