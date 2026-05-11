from __future__ import annotations

import json
import math
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np

VALID_REGIMES = ("COMPRESSION", "TENDANCE", "RANGE", "TRANSITION")
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


def _softmax(scores: Iterable[float]) -> np.ndarray:
    arr = np.asarray(list(scores), dtype=float)
    arr = arr - np.nanmax(arr)
    exp = np.exp(arr)
    s = float(exp.sum())
    if s <= 0 or not math.isfinite(s):
        return np.ones(len(arr)) / len(arr)
    return exp / s


class HMMRegimeEngine:
    """B1+ HMM MTF regime engine with schema-flexible DB loading.

    Doctrine:
    - DUAL architecture: standalone; does not import or merge B1 Legacy.
    - DB read-only only.
    - MTF activation: H1/M30/M15 aggregate observations; TF1440 is never a blocker.
    - hmmlearn is optional; a deterministic NumPy Gaussian fallback keeps perception alive.
    """

    min_mtf_observations = 50
    default_timeframes = (60, 30, 15)
    optional_context_tfs = (240, 1440)

    def compute(self, db_path: str, symbol: str = "GBPUSD", timeframes: Optional[List[int]] = None) -> Dict[str, Any]:
        tfs = tuple(int(x) for x in (timeframes or list(self.default_timeframes)))
        all_tfs = tuple(dict.fromkeys(list(tfs) + list(self.optional_context_tfs)))
        technical_risks: List[str] = []

        try:
            rows_by_tf, meta = self._load_rows_by_tf(db_path, symbol, all_tfs)
        except Exception as exc:
            return self._insufficient(symbol, tfs, 0, ["SCHEMA_LOAD_FAILED", str(exc)])

        mtf_rows = []
        for tf in tfs:
            mtf_rows.extend(rows_by_tf.get(int(tf), []))
        rows_used = len(mtf_rows)

        if rows_used < self.min_mtf_observations:
            return self._insufficient(
                symbol,
                tfs,
                rows_used,
                [f"MIN_MTF_OBSERVATIONS_{self.min_mtf_observations}_NOT_MET"],
                meta,
            )

        observations = self._build_observations(rows_by_tf, tfs)
        if observations.shape[0] < self.min_mtf_observations:
            return self._insufficient(symbol, tfs, int(observations.shape[0]), ["OBSERVATION_BUILD_TOO_THIN"], meta)

        method = "HMM_GAUSSIAN_FALLBACK_NUMPY"
        state_probs = None
        latest_label = None
        try:
            # Optional path. On Python 3.14 Windows, hmmlearn often has no wheel.
            from hmmlearn.hmm import GaussianHMM  # type: ignore
            X = self._standardize(observations)
            model = GaussianHMM(n_components=4, covariance_type="diag", n_iter=100, random_state=42)
            model.fit(X)
            probs = model.predict_proba(X)[-1]
            means = model.means_
            labels = self._map_components_to_regimes(means)
            state_probs = {labels[i]: float(probs[i]) for i in range(len(probs))}
            # Merge in case two components map to same semantic label.
            merged = {r: 0.0 for r in VALID_REGIMES}
            for k, v in state_probs.items():
                merged[k] += float(v)
            state_probs = merged
            latest_label = max(state_probs, key=state_probs.get)
            method = "HMM_GAUSSIAN"
        except Exception as exc:
            technical_risks.append("HMMLEARN_UNAVAILABLE_NUMPY_FALLBACK_USED")
            technical_risks.append(str(exc)[:180])
            latest = observations[-1]
            state_probs = self._heuristic_gaussian_probabilities(latest, observations)
            latest_label = max(state_probs, key=state_probs.get)

        confidence = float(max(state_probs.values())) if state_probs else 0.0
        context_rows = sum(len(rows_by_tf.get(tf, [])) for tf in self.optional_context_tfs)
        regime_scope = "HTF_ENRICHED" if context_rows > 0 else "MULTI_TF_TACTICAL"

        return {
            "symbol": symbol,
            "regime_hmm": latest_label,
            "regime_confidence_hmm": round(confidence, 6),
            "state_probabilities": {k: round(float(state_probs.get(k, 0.0)), 6) for k in VALID_REGIMES},
            "method": method,
            "status": "ACTIVE",
            "fallback": None,
            "rows_used": int(rows_used),
            "mtf_timeframes": list(tfs),
            "context_timeframes": list(self.optional_context_tfs),
            "regime_scope": regime_scope,
            "schema_mode": meta.get("schema_mode"),
            "observed_columns": meta.get("observed_columns", []),
            "time_column": meta.get("time_column"),
            "timeframe_column": meta.get("timeframe_column"),
            "symbol_column": meta.get("symbol_column"),
            "technical_risks": [x for x in technical_risks if x],
            "timestamp": _utc_now(),
            "timestamp_utc": _utc_now(),
        }

    def _insufficient(self, symbol: str, tfs: Iterable[int], rows_used: int, risks: List[str], meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        meta = meta or {}
        return {
            "symbol": symbol,
            "regime_hmm": None,
            "regime_confidence_hmm": 0.0,
            "state_probabilities": {k: 0.0 for k in VALID_REGIMES},
            "method": "HMM_GAUSSIAN_MTF",
            "status": "INSUFFICIENT_DATA",
            "fallback": "B1_LEGACY",
            "rows_used": int(rows_used),
            "mtf_timeframes": list(tfs),
            "regime_scope": "MULTI_TF_TACTICAL",
            "schema_mode": meta.get("schema_mode"),
            "observed_columns": meta.get("observed_columns", []),
            "technical_risks": risks,
            "timestamp": _utc_now(),
            "timestamp_utc": _utc_now(),
        }

    def _connect_ro(self, db_path: str) -> sqlite3.Connection:
        return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)

    def _table_columns(self, conn: sqlite3.Connection) -> List[str]:
        rows = conn.execute("PRAGMA table_info(force_snapshots)").fetchall()
        return [str(r[1]) for r in rows]

    def _find_col(self, cols: List[str], candidates: Iterable[str]) -> Optional[str]:
        wanted = {_norm(c) for c in candidates}
        for c in cols:
            if _norm(c) in wanted:
                return c
        return None

    def _currency_wide_cols(self, cols: List[str]) -> List[str]:
        out: List[str] = []
        for c in cols:
            n = _norm(c)
            for cur in CURRENCIES:
                if n == cur or n == f"{cur}force" or n == f"force{cur}" or n.endswith(cur) or n.startswith(cur):
                    if n not in ("currency", "ccy") and c not in out:
                        out.append(c)
        return out

    def _numeric_cols(self, conn: sqlite3.Connection, cols: List[str], excluded: Iterable[Optional[str]]) -> List[str]:
        ex = {x for x in excluded if x}
        candidates = [c for c in cols if c not in ex and _norm(c) not in {"id", "rowid", "symbol", "pair", "instrument"}]
        numeric: List[str] = []
        for c in candidates:
            try:
                vals = conn.execute(f'SELECT "{c}" FROM force_snapshots WHERE "{c}" IS NOT NULL LIMIT 20').fetchall()
            except Exception:
                continue
            ok = 0
            for (v,) in vals:
                if _safe_float(v) is not None:
                    ok += 1
            if ok > 0:
                numeric.append(c)
        return numeric

    def _load_rows_by_tf(self, db_path: str, symbol: str, timeframes: Iterable[int]) -> Tuple[Dict[int, List[Dict[str, Any]]], Dict[str, Any]]:
        conn = self._connect_ro(db_path)
        try:
            cols = self._table_columns(conn)
            if not cols:
                raise RuntimeError("force_snapshots table not found or empty schema")
            time_col = self._find_col(cols, TIME_CANDIDATES)
            tf_col = self._find_col(cols, TF_CANDIDATES)
            sym_col = self._find_col(cols, SYMBOL_CANDIDATES)
            cur_col = self._find_col(cols, LONG_CURRENCY_CANDIDATES)
            val_col = self._find_col(cols, LONG_VALUE_CANDIDATES)
            if tf_col is None:
                raise RuntimeError("timeframe column not detected")

            order_col = time_col or "rowid"
            wide_cols = self._currency_wide_cols(cols)
            generic_numeric = self._numeric_cols(conn, cols, [time_col, tf_col, sym_col, cur_col, val_col])
            rows_by_tf: Dict[int, List[Dict[str, Any]]] = {int(tf): [] for tf in timeframes}

            if len(wide_cols) >= 1:
                schema_mode = "wide_currency" if len(wide_cols) >= 2 else "single_currency_wide"
                select_cols = [order_col, tf_col] + wide_cols
                raw = self._select_rows(conn, select_cols, tf_col, sym_col, symbol, timeframes, order_col)
                for row in raw:
                    tf = int(float(row[tf_col]))
                    values = {c: _safe_float(row[c]) for c in wide_cols}
                    values = {c: v for c, v in values.items() if v is not None}
                    if values:
                        rows_by_tf.setdefault(tf, []).append({"t": row.get(order_col), "values": values})
                observed = wide_cols
            elif cur_col and val_col:
                schema_mode = "long_currency"
                select_cols = [order_col, tf_col, cur_col, val_col]
                raw = self._select_rows(conn, select_cols, tf_col, sym_col, symbol, timeframes, order_col)
                bucket: Dict[Tuple[int, Any], Dict[str, float]] = {}
                for row in raw:
                    tf = int(float(row[tf_col]))
                    t = row.get(order_col)
                    cur = str(row.get(cur_col, "value")).lower()
                    val = _safe_float(row.get(val_col))
                    if val is None:
                        continue
                    bucket.setdefault((tf, t), {})[cur] = val
                for (tf, t), values in bucket.items():
                    rows_by_tf.setdefault(tf, []).append({"t": t, "values": values})
                observed = [cur_col, val_col]
            elif len(generic_numeric) >= 1:
                schema_mode = "generic_numeric_stream"
                select_cols = [order_col, tf_col] + generic_numeric
                raw = self._select_rows(conn, select_cols, tf_col, sym_col, symbol, timeframes, order_col)
                for row in raw:
                    tf = int(float(row[tf_col]))
                    values = {c: _safe_float(row[c]) for c in generic_numeric}
                    values = {c: v for c, v in values.items() if v is not None}
                    if values:
                        rows_by_tf.setdefault(tf, []).append({"t": row.get(order_col), "values": values})
                observed = generic_numeric
            else:
                raise RuntimeError("no usable force columns detected in force_snapshots")

            for tf in rows_by_tf:
                rows_by_tf[tf].sort(key=lambda r: str(r.get("t")))
            meta = {
                "schema_mode": schema_mode,
                "observed_columns": observed,
                "time_column": time_col or "rowid",
                "timeframe_column": tf_col,
                "symbol_column": sym_col,
            }
            return rows_by_tf, meta
        finally:
            conn.close()

    def _select_rows(self, conn: sqlite3.Connection, select_cols: List[str], tf_col: str, sym_col: Optional[str], symbol: str, timeframes: Iterable[int], order_col: str) -> List[Dict[str, Any]]:
        tf_list = [int(x) for x in timeframes]
        ph = ",".join("?" for _ in tf_list)
        quoted = ", ".join([f'"{c}"' if c != "rowid" else "rowid" for c in select_cols])
        base = f'SELECT {quoted} FROM force_snapshots WHERE "{tf_col}" IN ({ph})'
        params: List[Any] = list(tf_list)
        if sym_col:
            sql = base + f' AND "{sym_col}" = ? ORDER BY "{tf_col}", ' + (f'"{order_col}"' if order_col != "rowid" else "rowid")
            rows = conn.execute(sql, params + [symbol]).fetchall()
            if rows:
                return [dict(zip(select_cols, r)) for r in rows]
        sql = base + f' ORDER BY "{tf_col}", ' + (f'"{order_col}"' if order_col != "rowid" else "rowid")
        rows = conn.execute(sql, params).fetchall()
        return [dict(zip(select_cols, r)) for r in rows]

    def _build_observations(self, rows_by_tf: Dict[int, List[Dict[str, Any]]], tfs: Iterable[int]) -> np.ndarray:
        obs: List[List[float]] = []
        for tf in tfs:
            rows = rows_by_tf.get(int(tf), [])
            prev_vec: Optional[np.ndarray] = None
            primary_series: List[float] = []
            for row in rows:
                vals = np.asarray(list(row["values"].values()), dtype=float)
                vals = vals[np.isfinite(vals)]
                if vals.size == 0:
                    continue
                primary = float(np.nanmean(vals))
                primary_series.append(primary)
                std_force = float(np.nanstd(vals)) if vals.size > 1 else float(abs(primary))
                cross_dispersion = float(np.nanmax(vals) - np.nanmin(vals)) if vals.size > 1 else 0.0
                if prev_vec is not None and prev_vec.size == vals.size:
                    avg_abs_angle = float(np.nanmean(np.abs(vals - prev_vec)))
                else:
                    avg_abs_angle = 0.0
                if len(primary_series) >= 8:
                    a = np.asarray(primary_series[-8:-1], dtype=float)
                    b = np.asarray(primary_series[-7:], dtype=float)
                    if np.std(a) > 1e-9 and np.std(b) > 1e-9:
                        autocorr = float(np.corrcoef(a, b)[0, 1])
                    else:
                        autocorr = 0.0
                else:
                    autocorr = 0.0
                obs.append([std_force, avg_abs_angle, autocorr, cross_dispersion, float(tf)])
                prev_vec = vals
        return np.asarray(obs, dtype=float)

    def _standardize(self, X: np.ndarray) -> np.ndarray:
        mu = np.nanmean(X, axis=0)
        sd = np.nanstd(X, axis=0)
        sd[sd < 1e-9] = 1.0
        return (X - mu) / sd

    def _map_components_to_regimes(self, means: np.ndarray) -> Dict[int, str]:
        labels: Dict[int, str] = {}
        used: set[str] = set()
        for i, m in enumerate(means):
            std_force, avg_abs_angle, autocorr, cross_dispersion, _tf = m[:5]
            scores = {
                "COMPRESSION": -abs(avg_abs_angle) - abs(cross_dispersion) + max(autocorr, 0),
                "TENDANCE": avg_abs_angle + max(autocorr, 0) + 0.3 * std_force,
                "RANGE": -abs(avg_abs_angle) + 0.5 * max(autocorr, 0) - 0.2 * std_force,
                "TRANSITION": abs(avg_abs_angle) + abs(cross_dispersion) - abs(autocorr),
            }
            label = max(scores, key=scores.get)
            if label in used:
                for alt in VALID_REGIMES:
                    if alt not in used:
                        label = alt
                        break
            used.add(label)
            labels[i] = label
        return labels

    def _heuristic_gaussian_probabilities(self, latest: np.ndarray, X: np.ndarray) -> Dict[str, float]:
        Z = self._standardize(X)
        z = Z[-1]
        std_force, avg_abs_angle, autocorr, cross_dispersion, _tf = z[:5]
        vol_delta = 0.0
        if Z.shape[0] > 6:
            vol_delta = float(z[0] - np.nanmean(Z[-6:-1, 0]))
        scores = [
            -0.7 * abs(avg_abs_angle) - 0.5 * abs(cross_dispersion) + 0.8 * max(autocorr, 0) - 0.2 * abs(vol_delta),
            1.0 * avg_abs_angle + 0.8 * max(autocorr, 0) + 0.2 * std_force,
            -0.8 * abs(avg_abs_angle) + 0.4 * max(autocorr, 0) - 0.3 * abs(std_force),
            0.8 * abs(avg_abs_angle) + 0.8 * abs(vol_delta) + 0.4 * abs(cross_dispersion) - 0.3 * abs(autocorr),
        ]
        probs = _softmax(scores)
        return {reg: float(probs[i]) for i, reg in enumerate(VALID_REGIMES)}


def main() -> int:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="powerflow.db")
    p.add_argument("--symbol", default="GBPUSD")
    p.add_argument("--tfs", default="60,30,15")
    p.add_argument("--pretty", action="store_true")
    args = p.parse_args()
    tfs = [int(x.strip()) for x in args.tfs.split(",") if x.strip()]
    result = HMMRegimeEngine().compute(args.db, args.symbol, tfs)
    out_dir = Path("output/dashboard_surface")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "regime_hmm.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
