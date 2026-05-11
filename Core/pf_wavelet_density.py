from __future__ import annotations

import json
import math
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
try:
    import pywt  # type: ignore
except Exception:
    pywt = None

VALID_STATES = ("WAVELET_COMPRESSING", "WAVELET_EXPANDING", "WAVELET_MULTI_SCALE", "WAVELET_TRANSITIONING", "WAVELET_SILENT")
CURRENCIES = ("gbp", "usd", "eur", "jpy", "chf", "cad", "aud", "nzd")
TIME_CANDIDATES = ("timestamp", "time", "ts", "datetime", "created_at", "date")
TF_CANDIDATES = ("timeframe", "tf", "period", "timeframe_minutes", "frame")
SYMBOL_CANDIDATES = ("symbol", "pair", "instrument", "asset")
LONG_CURRENCY_CANDIDATES = ("currency", "ccy", "devise")
LONG_VALUE_CANDIDATES = ("value", "force", "score", "strength", "zscore", "z_score", "power", "raw_value")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def _safe_float(x: Any) -> Optional[float]:
    try:
        v = float(x)
        if math.isfinite(v):
            return v
    except Exception:
        return None
    return None


class WaveletDensityEngine:
    """B4+ Wavelet Morlet density engine with schema-flexible signal loading."""

    min_tf5_rows = 30

    def compute(self, db_path: str, symbol: str = "GBPUSD", timeframes: Optional[List[int]] = None) -> Dict[str, Any]:
        tfs = [int(x) for x in (timeframes or [1, 5, 15])]
        base_currency = symbol[:3].lower() if symbol else "gbp"
        results: List[Dict[str, Any]] = []
        global_risks: List[str] = []
        schema_meta: Dict[str, Any] = {}

        try:
            series_by_tf, schema_meta = self._load_series_by_tf(db_path, symbol, base_currency, tfs)
        except Exception as exc:
            return {
                "symbol": symbol,
                "status": "INSUFFICIENT_DATA",
                "method": "CWT_MORLET",
                "technical_risks": ["SCHEMA_LOAD_FAILED", str(exc)],
                "results": [],
                "timestamp": _utc_now(),
                "timestamp_utc": _utc_now(),
            }

        tf5_len = len(series_by_tf.get(5, []))
        if 5 in tfs and tf5_len < self.min_tf5_rows:
            global_risks.append(f"TF5_ROWS_LT_{self.min_tf5_rows}")

        for tf in tfs:
            values = np.asarray(series_by_tf.get(int(tf), []), dtype=float)
            item = self._compute_one(values, tf, base_currency)
            item.update({"schema_mode": schema_meta.get("schema_mode"), "source_column": schema_meta.get("source_column")})
            results.append(item)

        status = "ACTIVE" if not global_risks else "INSUFFICIENT_DATA"
        return {
            "symbol": symbol,
            "status": status,
            "method": "CWT_MORLET",
            "currency": base_currency.upper(),
            "timeframes": tfs,
            "schema_mode": schema_meta.get("schema_mode"),
            "source_column": schema_meta.get("source_column"),
            "technical_risks": global_risks,
            "results": results,
            "timestamp": _utc_now(),
            "timestamp_utc": _utc_now(),
        }

    def _compute_one(self, values: np.ndarray, tf: int, currency: str) -> Dict[str, Any]:
        risks: List[str] = []
        if values.size < 8:
            return self._silent(tf, currency, 0, ["INSUFFICIENT_ROWS"])
        values = values[np.isfinite(values)]
        if values.size < 8:
            return self._silent(tf, currency, int(values.size), ["NON_FINITE_SERIES"])
        centered = values - float(np.nanmean(values))
        if float(np.nanstd(centered)) < 1e-9:
            return self._silent(tf, currency, int(values.size), ["WAVELET_SILENT_VALID_STATIC_OR_FLAT"])

        max_scale = max(3, min(64, values.size // 2))
        scales = np.arange(2, max_scale + 1)
        if pywt is not None:
            coeffs, _freqs = pywt.cwt(centered, scales, "morl")
            power = np.abs(coeffs) ** 2
        else:
            risks.append("PYWT_UNAVAILABLE_NUMPY_FFT_FALLBACK_USED")
            power = self._fallback_power(centered, scales)

        recent_power = np.nanmean(power[:, max(0, power.shape[1] - min(10, power.shape[1])):], axis=1)
        total_power = float(np.nansum(recent_power))
        if total_power <= 1e-9:
            return self._silent(tf, currency, int(values.size), risks + ["LOW_WAVELET_ENERGY"])

        dominant_idx = int(np.nanargmax(recent_power))
        dominant_scale = int(scales[dominant_idx])
        short_band = recent_power[scales <= max(4, max_scale // 4)]
        long_band = recent_power[scales >= max(5, max_scale // 2)]
        short_energy = float(np.nansum(short_band)) if short_band.size else 0.0
        long_energy = float(np.nansum(long_band)) if long_band.size else 0.0
        energy_ratio = float(short_energy / (long_energy + 1e-9))

        threshold = float(np.nanmax(recent_power) * 0.45)
        active_bands = int(np.sum(recent_power >= threshold))
        multi_scale = bool(active_bands >= 2)

        if power.shape[1] >= 12:
            early = np.nanmean(power[:, -12:-6], axis=1)
            late = np.nanmean(power[:, -6:], axis=1)
            early_scale = int(scales[int(np.nanargmax(early))])
            late_scale = int(scales[int(np.nanargmax(late))])
        else:
            early_scale = dominant_scale
            late_scale = dominant_scale

        if late_scale < early_scale:
            drift = "COMPRESSING"
        elif late_scale > early_scale:
            drift = "EXPANDING"
        else:
            drift = "STABLE"
        compression_onset = bool(drift == "COMPRESSING" and energy_ratio > 1.05)

        if multi_scale:
            state = "WAVELET_MULTI_SCALE"
        elif compression_onset or (dominant_scale <= max(4, max_scale // 4) and energy_ratio > 1.0):
            state = "WAVELET_COMPRESSING"
        elif dominant_scale >= max(5, max_scale // 2) and energy_ratio < 1.0:
            state = "WAVELET_EXPANDING"
        elif drift != "STABLE":
            state = "WAVELET_TRANSITIONING"
        else:
            state = "WAVELET_SILENT" if total_power < 1e-6 else "WAVELET_TRANSITIONING"

        return {
            "currency": currency.upper(),
            "timeframe": int(tf),
            "wavelet_state": state,
            "dominant_scale_bars": int(max(1, dominant_scale)),
            "wavelet_energy_ratio": round(float(energy_ratio), 6),
            "scale_drift_direction": drift,
            "multi_scale_flag": multi_scale,
            "compression_onset": compression_onset,
            "method": "CWT_MORLET" if pywt is not None else "FFT_SCALE_FALLBACK",
            "rows_used": int(values.size),
            "technical_risks": risks,
            "timestamp": _utc_now(),
            "timestamp_utc": _utc_now(),
        }

    def _silent(self, tf: int, currency: str, rows: int, risks: List[str]) -> Dict[str, Any]:
        return {
            "currency": currency.upper(),
            "timeframe": int(tf),
            "wavelet_state": "WAVELET_SILENT",
            "dominant_scale_bars": 1,
            "wavelet_energy_ratio": 0.0,
            "scale_drift_direction": "STABLE",
            "multi_scale_flag": False,
            "compression_onset": False,
            "method": "CWT_MORLET",
            "rows_used": int(rows),
            "technical_risks": risks,
            "timestamp": _utc_now(),
            "timestamp_utc": _utc_now(),
        }

    def _fallback_power(self, centered: np.ndarray, scales: np.ndarray) -> np.ndarray:
        out = []
        x = np.asarray(centered, dtype=float)
        for s in scales:
            win = max(3, int(s))
            kernel = np.sin(np.linspace(0, 2 * np.pi, win)) * np.hanning(win)
            conv = np.convolve(x, kernel, mode="same")
            out.append(conv * conv)
        return np.asarray(out, dtype=float)

    def _connect_ro(self, db_path: str) -> sqlite3.Connection:
        return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)

    def _table_columns(self, conn: sqlite3.Connection) -> List[str]:
        return [str(r[1]) for r in conn.execute("PRAGMA table_info(force_snapshots)").fetchall()]

    def _find_col(self, cols: List[str], candidates: Iterable[str]) -> Optional[str]:
        wanted = {_norm(c) for c in candidates}
        for c in cols:
            if _norm(c) in wanted:
                return c
        return None

    def _currency_col(self, cols: List[str], cur: str) -> Optional[str]:
        cur = _norm(cur)
        for c in cols:
            n = _norm(c)
            if n == cur or n == f"force{cur}" or n == f"{cur}force" or n.endswith(cur) or n.startswith(cur):
                if n not in {"currency", "ccy"}:
                    return c
        return None

    def _numeric_cols(self, conn: sqlite3.Connection, cols: List[str], excluded: Iterable[Optional[str]]) -> List[str]:
        ex = {x for x in excluded if x}
        out: List[str] = []
        for c in cols:
            if c in ex or _norm(c) in {"id", "rowid", "symbol", "pair", "instrument"}:
                continue
            try:
                vals = conn.execute(f'SELECT "{c}" FROM force_snapshots WHERE "{c}" IS NOT NULL LIMIT 20').fetchall()
            except Exception:
                continue
            if any(_safe_float(v[0]) is not None for v in vals):
                out.append(c)
        return out

    def _load_series_by_tf(self, db_path: str, symbol: str, base_currency: str, timeframes: Iterable[int]) -> Tuple[Dict[int, List[float]], Dict[str, Any]]:
        conn = self._connect_ro(db_path)
        try:
            cols = self._table_columns(conn)
            if not cols:
                raise RuntimeError("force_snapshots table not found")
            time_col = self._find_col(cols, TIME_CANDIDATES)
            tf_col = self._find_col(cols, TF_CANDIDATES)
            sym_col = self._find_col(cols, SYMBOL_CANDIDATES)
            cur_col = self._find_col(cols, LONG_CURRENCY_CANDIDATES)
            val_col = self._find_col(cols, LONG_VALUE_CANDIDATES)
            if tf_col is None:
                raise RuntimeError("timeframe column not detected")
            order_col = time_col or "rowid"
            series_by_tf: Dict[int, List[float]] = {int(tf): [] for tf in timeframes}
            source_col = None
            schema_mode = None

            wide = self._currency_col(cols, base_currency)
            if wide:
                schema_mode = "wide_currency"
                source_col = wide
                raw = self._select_rows(conn, [order_col, tf_col, wide], tf_col, sym_col, symbol, timeframes, order_col)
                for row in raw:
                    v = _safe_float(row.get(wide))
                    if v is not None:
                        series_by_tf.setdefault(int(float(row[tf_col])), []).append(v)
            elif cur_col and val_col:
                schema_mode = "long_currency"
                source_col = val_col
                raw = self._select_rows(conn, [order_col, tf_col, cur_col, val_col], tf_col, sym_col, symbol, timeframes, order_col)
                filtered = [r for r in raw if _norm(r.get(cur_col, "")) == _norm(base_currency)]
                if not filtered:
                    filtered = raw
                for row in filtered:
                    v = _safe_float(row.get(val_col))
                    if v is not None:
                        series_by_tf.setdefault(int(float(row[tf_col])), []).append(v)
            else:
                nums = self._numeric_cols(conn, cols, [time_col, tf_col, sym_col, cur_col, val_col])
                if not nums:
                    raise RuntimeError("no numeric signal column detected")
                schema_mode = "generic_numeric_stream"
                source_col = nums[0]
                raw = self._select_rows(conn, [order_col, tf_col, source_col], tf_col, sym_col, symbol, timeframes, order_col)
                for row in raw:
                    v = _safe_float(row.get(source_col))
                    if v is not None:
                        series_by_tf.setdefault(int(float(row[tf_col])), []).append(v)
            return series_by_tf, {"schema_mode": schema_mode, "source_column": source_col, "time_column": time_col or "rowid", "timeframe_column": tf_col, "symbol_column": sym_col}
        finally:
            conn.close()

    def _select_rows(self, conn: sqlite3.Connection, select_cols: List[str], tf_col: str, sym_col: Optional[str], symbol: str, timeframes: Iterable[int], order_col: str) -> List[Dict[str, Any]]:
        tf_list = [int(x) for x in timeframes]
        ph = ",".join("?" for _ in tf_list)
        quoted = ", ".join([f'"{c}"' if c != "rowid" else "rowid" for c in select_cols])
        order_q = f'"{order_col}"' if order_col != "rowid" else "rowid"
        base = f'SELECT {quoted} FROM force_snapshots WHERE "{tf_col}" IN ({ph})'
        if sym_col:
            rows = conn.execute(base + f' AND "{sym_col}" = ? ORDER BY "{tf_col}", {order_q}', list(tf_list) + [symbol]).fetchall()
            if rows:
                return [dict(zip(select_cols, r)) for r in rows]
        rows = conn.execute(base + f' ORDER BY "{tf_col}", {order_q}', list(tf_list)).fetchall()
        return [dict(zip(select_cols, r)) for r in rows]


def parse_tfs(raw: str) -> List[int]:
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


def main() -> int:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="powerflow.db")
    p.add_argument("--symbol", default="GBPUSD")
    p.add_argument("--tfs", default="1,5,15")
    p.add_argument("--pretty", action="store_true")
    args = p.parse_args()
    result = WaveletDensityEngine().compute(args.db, args.symbol, parse_tfs(args.tfs))
    out_dir = Path("output/dashboard_surface")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "wavelet.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
