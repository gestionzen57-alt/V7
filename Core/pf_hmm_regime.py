"""PowerFlow V7.2 — B1+ Gaussian HMM regime engine.

Standalone Hidden Markov Model implementation for HTF regime perception.
No hmmlearn dependency. No DB writes. No cockpit/telegram imports.

Regime states are semantic after training:
    0 -> COMPRESSION
    1 -> TENDANCE
    2 -> RANGE
"""
from __future__ import annotations

import json
import math
import os
import pickle
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

VERSION = "HMMRegimeV1.2StandaloneSchema"
METHOD = "hmm_gaussian_standalone"
STATE_NAMES = ["COMPRESSION", "TENDANCE", "RANGE"]

KNOWN_META_COLUMNS = {
    "id", "timestamp", "time", "datetime", "created_at", "updated_at",
    "symbol", "timeframe", "tf", "bid", "ask", "spread", "price",
    "open", "high", "low", "close", "volume", "tick_volume",
}

CURRENCY_COLUMNS = {
    "EUR": ["force_eur", "eur", "EUR"],
    "GBP": ["force_gbp", "gbp", "GBP"],
    "USD": ["force_usd", "usd", "USD"],
    "JPY": ["force_jpy", "jpy", "JPY"],
    "CHF": ["force_chf", "chf", "CHF"],
    "CAD": ["force_cad", "cad", "CAD"],
    "AUD": ["force_aud", "aud", "AUD"],
    "NZD": ["force_nzd", "nzd", "NZD"],
    "XAU": ["force_xau", "xau", "XAU"],
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def connect_readonly(db_path: str) -> sqlite3.Connection:
    path = Path(db_path)
    uri = f"file:{path.as_posix()}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        x = float(value)
        if not math.isfinite(x):
            return default
        return x
    except Exception:
        return default


def _table_columns(conn: sqlite3.Connection, table: str = "force_snapshots") -> List[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [str(r[1]) for r in rows]


def _column_exists(cols: Sequence[str], name: str) -> bool:
    return any(c.lower() == name.lower() for c in cols)


def _resolve_symbol_columns(symbol: str, cols: Sequence[str]) -> Tuple[Optional[str], Optional[str], List[str]]:
    symbol = (symbol or "GBPUSD").upper().replace("/", "")
    base = symbol[:3]
    quote = symbol[3:6]

    lower_map = {c.lower(): c for c in cols}

    def find_currency(cur: str) -> Optional[str]:
        for candidate in CURRENCY_COLUMNS.get(cur, []):
            hit = lower_map.get(candidate.lower())
            if hit:
                return hit
        return None

    base_col = find_currency(base)
    quote_col = find_currency(quote)

    force_cols = [c for c in cols if c.lower().startswith("force_")]
    if not force_cols:
        # Conservative fallback: numeric-looking non-meta columns. SQLite has weak typing,
        # so actual numeric coercion happens after SELECT.
        force_cols = [c for c in cols if c.lower() not in KNOWN_META_COLUMNS]

    return base_col, quote_col, force_cols


def _ewma(values: np.ndarray, alpha: float = 0.28) -> np.ndarray:
    if values.size == 0:
        return values.astype(float)
    out = np.empty_like(values, dtype=float)
    out[0] = float(values[0])
    for i in range(1, len(values)):
        out[i] = alpha * float(values[i]) + (1.0 - alpha) * out[i - 1]
    return out


def _zone_numeric(series: np.ndarray) -> np.ndarray:
    if series.size == 0:
        return series.astype(float)
    mu = float(np.nanmean(series))
    sigma = float(np.nanstd(series))
    if sigma <= 1e-12:
        return np.zeros_like(series, dtype=float)
    z = np.abs((series - mu) / sigma)
    # 0 NEUTRAL, 1 PRE_EXTREME, 2 EARLY_EXTREME, 3 ACCUMULATING, 4 RUPTURE
    return np.select(
        [z < 0.70, z < 1.15, z < 1.65, z < 2.20],
        [0.0, 1.0, 2.0, 3.0],
        default=4.0,
    ).astype(float)


def build_features_from_force_series(force_series: Sequence[float]) -> np.ndarray:
    """Build [angle_kalman, speed_magnitude, zone_numeric] per bar."""
    x = np.asarray([_safe_float(v) for v in force_series], dtype=float)
    if x.size < 3:
        return np.empty((0, 3), dtype=float)

    # Robust local standardization avoids huge raw-force scale effects.
    x_clean = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    dx = np.diff(x_clean, prepend=x_clean[0])
    scale = float(np.nanstd(dx))
    if scale <= 1e-12:
        scale = 1.0

    raw_angle = np.degrees(np.arctan(dx / scale))
    angle_kalman = _ewma(raw_angle, alpha=0.25)
    speed_magnitude = np.abs(np.diff(angle_kalman, prepend=angle_kalman[0]))
    zone = _zone_numeric(x_clean)

    return np.column_stack([angle_kalman, speed_magnitude, zone]).astype(float)


def load_hmm_features_from_db(
    db_path: str,
    symbol: str = "GBPUSD",
    timeframe: int = 240,
    lookback: int = 500,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Read force_snapshots in read-only mode and build HMM features."""
    meta: Dict[str, Any] = {
        "db_path": db_path,
        "symbol": symbol,
        "timeframe": timeframe,
        "lookback": lookback,
        "rows": 0,
        "force_source": "UNKNOWN",
        "technical_risks": [],
    }

    try:
        conn = connect_readonly(db_path)
    except Exception as exc:
        meta["technical_risks"].append("DB_READ_ERROR")
        meta["error"] = str(exc)
        return np.empty((0, 3), dtype=float), meta

    try:
        cols = _table_columns(conn)
        if not cols:
            meta["technical_risks"].append("FORCE_SNAPSHOTS_SCHEMA_MISSING")
            return np.empty((0, 3), dtype=float), meta

        has_symbol = _column_exists(cols, "symbol")
        has_timeframe = _column_exists(cols, "timeframe")
        has_timestamp = _column_exists(cols, "timestamp")
        base_col, quote_col, force_cols = _resolve_symbol_columns(symbol, cols)

        if base_col and quote_col:
            select_cols = [base_col, quote_col]
            meta["force_source"] = f"{base_col}-{quote_col}"
        else:
            select_cols = force_cols[:8]
            meta["force_source"] = "mean_force_columns"

        if not select_cols:
            meta["technical_risks"].append("NO_FORCE_COLUMNS")
            return np.empty((0, 3), dtype=float), meta

        where = []
        params: List[Any] = []
        if has_timeframe:
            where.append("timeframe = ?")
            params.append(int(timeframe))
        if has_symbol:
            where.append("symbol = ?")
            params.append(symbol)

        where_sql = (" WHERE " + " AND ".join(where)) if where else ""
        order_sql = " ORDER BY timestamp DESC" if has_timestamp else ""
        col_sql = ", ".join([f'"{c}"' for c in select_cols])
        sql = f"SELECT {col_sql} FROM force_snapshots{where_sql}{order_sql} LIMIT ?"
        params.append(int(lookback))
        rows = conn.execute(sql, params).fetchall()
        rows = list(reversed(rows))
        meta["rows"] = len(rows)

        if len(rows) < 8:
            meta["technical_risks"].append("INSUFFICIENT_DATA")
            return np.empty((0, 3), dtype=float), meta

        arr = np.asarray(rows, dtype=float)
        if arr.ndim == 1:
            force = arr
        elif base_col and quote_col and arr.shape[1] >= 2:
            force = arr[:, 0] - arr[:, 1]
        else:
            force = np.nanmean(arr, axis=1)

        features = build_features_from_force_series(force)
        if features.shape[0] < 8:
            meta["technical_risks"].append("INSUFFICIENT_FEATURES")
        return features, meta
    except Exception as exc:
        meta["technical_risks"].append("FEATURE_BUILD_ERROR")
        meta["error"] = str(exc)
        return np.empty((0, 3), dtype=float), meta
    finally:
        conn.close()


@dataclass
class HMMRegimeGaussian:
    n_states: int = 3
    n_iter: int = 40
    random_state: int = 42
    min_covar: float = 1e-4

    def __post_init__(self) -> None:
        self.state_names = list(STATE_NAMES)
        self.startprob_: Optional[np.ndarray] = None
        self.transmat_: Optional[np.ndarray] = None
        self.means_: Optional[np.ndarray] = None
        self.covars_: Optional[np.ndarray] = None  # diagonal variances
        self.feature_mean_: Optional[np.ndarray] = None
        self.feature_std_: Optional[np.ndarray] = None
        self.fitted_: bool = False

    def _normalize_fit(self, features: np.ndarray) -> np.ndarray:
        self.feature_mean_ = np.nanmean(features, axis=0)
        self.feature_std_ = np.nanstd(features, axis=0)
        self.feature_std_[self.feature_std_ < 1e-9] = 1.0
        return (features - self.feature_mean_) / self.feature_std_

    def _normalize_apply(self, features: np.ndarray) -> np.ndarray:
        if self.feature_mean_ is None or self.feature_std_ is None:
            return features.astype(float)
        return (features - self.feature_mean_) / self.feature_std_

    def _initial_labels(self, z: np.ndarray) -> np.ndarray:
        # Semantic seed using raw normalized features:
        # angle magnitude + speed -> trend, zone without speed -> compression,
        # low energy -> range.
        angle_abs = np.abs(z[:, 0])
        speed = z[:, 1]
        zone = z[:, 2]
        trend_score = angle_abs + 0.65 * speed
        compression_score = zone - 0.45 * speed - 0.15 * angle_abs

        labels = np.full(z.shape[0], 2, dtype=int)  # RANGE default
        if z.shape[0] >= self.n_states:
            trend_cut = np.nanquantile(trend_score, 0.67)
            comp_cut = np.nanquantile(compression_score, 0.67)
            labels[trend_score >= trend_cut] = 1
            labels[(compression_score >= comp_cut) & (labels != 1)] = 0

        # Ensure every state exists.
        for s in range(self.n_states):
            if np.sum(labels == s) == 0:
                labels[s % len(labels)] = s
        return labels

    def _estimate_from_labels(self, z: np.ndarray, labels: np.ndarray) -> None:
        n, d = z.shape
        self.startprob_ = np.full(self.n_states, 1e-6, dtype=float)
        self.startprob_[labels[0]] = 1.0
        self.startprob_ /= self.startprob_.sum()

        self.transmat_ = np.full((self.n_states, self.n_states), 1e-3, dtype=float)
        for a, b in zip(labels[:-1], labels[1:]):
            self.transmat_[a, b] += 1.0
        self.transmat_ /= self.transmat_.sum(axis=1, keepdims=True)

        self.means_ = np.zeros((self.n_states, d), dtype=float)
        self.covars_ = np.ones((self.n_states, d), dtype=float)
        for s in range(self.n_states):
            pts = z[labels == s]
            if pts.size == 0:
                pts = z
            self.means_[s] = np.nanmean(pts, axis=0)
            var = np.nanvar(pts, axis=0)
            self.covars_[s] = np.maximum(var, self.min_covar)

    def _log_gaussian_diag(self, z: np.ndarray) -> np.ndarray:
        if self.means_ is None or self.covars_ is None:
            raise RuntimeError("HMM not initialized")
        z = np.atleast_2d(z).astype(float)
        n, d = z.shape
        out = np.zeros((n, self.n_states), dtype=float)
        const = d * math.log(2.0 * math.pi)
        for s in range(self.n_states):
            var = np.maximum(self.covars_[s], self.min_covar)
            diff = z - self.means_[s]
            out[:, s] = -0.5 * (const + np.sum(np.log(var)) + np.sum((diff * diff) / var, axis=1))
        return out

    @staticmethod
    def _logsumexp(a: np.ndarray, axis: Optional[int] = None) -> np.ndarray:
        a_max = np.max(a, axis=axis, keepdims=True)
        safe = np.where(np.isfinite(a_max), a_max, 0.0)
        res = safe + np.log(np.sum(np.exp(a - safe), axis=axis, keepdims=True))
        if axis is not None:
            res = np.squeeze(res, axis=axis)
        return res

    def _forward_backward(self, z: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float]:
        if self.startprob_ is None or self.transmat_ is None:
            raise RuntimeError("HMM not initialized")
        log_b = self._log_gaussian_diag(z)
        log_start = np.log(np.maximum(self.startprob_, 1e-12))
        log_trans = np.log(np.maximum(self.transmat_, 1e-12))
        n = z.shape[0]

        alpha = np.zeros((n, self.n_states), dtype=float)
        alpha[0] = log_start + log_b[0]
        for t in range(1, n):
            alpha[t] = log_b[t] + self._logsumexp(alpha[t - 1][:, None] + log_trans, axis=0)

        beta = np.zeros((n, self.n_states), dtype=float)
        for t in range(n - 2, -1, -1):
            beta[t] = self._logsumexp(log_trans + log_b[t + 1][None, :] + beta[t + 1][None, :], axis=1)

        log_likelihood = float(self._logsumexp(alpha[-1], axis=0))
        gamma_log = alpha + beta - log_likelihood
        gamma = np.exp(gamma_log)
        gamma /= np.maximum(gamma.sum(axis=1, keepdims=True), 1e-12)
        return gamma, alpha, log_likelihood

    def fit(self, features: Sequence[Sequence[float]]) -> "HMMRegimeGaussian":
        x = np.asarray(features, dtype=float)
        x = x[np.all(np.isfinite(x), axis=1)]
        if x.ndim != 2 or x.shape[0] < 8 or x.shape[1] != 3:
            raise ValueError("HMM needs at least 8 observations with 3 features")

        z = self._normalize_fit(x)
        labels = self._initial_labels(z)
        self._estimate_from_labels(z, labels)

        for _ in range(max(1, int(self.n_iter))):
            gamma, _alpha, _ll = self._forward_backward(z)
            weights = np.maximum(gamma.sum(axis=0), 1e-9)
            self.startprob_ = gamma[0] + 1e-6
            self.startprob_ /= self.startprob_.sum()

            # Approximate transition update from adjacent smoothed probabilities.
            xi_sum = np.full((self.n_states, self.n_states), 1e-4, dtype=float)
            for t in range(z.shape[0] - 1):
                xi_sum += np.outer(gamma[t], gamma[t + 1])
            self.transmat_ = xi_sum / np.maximum(xi_sum.sum(axis=1, keepdims=True), 1e-12)

            self.means_ = (gamma.T @ z) / weights[:, None]
            for s in range(self.n_states):
                diff = z - self.means_[s]
                var = (gamma[:, s][:, None] * diff * diff).sum(axis=0) / weights[s]
                self.covars_[s] = np.maximum(var, self.min_covar)

        self._semantic_reorder()
        self.fitted_ = True
        return self

    def _semantic_reorder(self) -> None:
        if self.means_ is None or self.covars_ is None or self.transmat_ is None or self.startprob_ is None:
            return
        m = self.means_
        trend_scores = np.abs(m[:, 0]) + 0.7 * m[:, 1]
        compression_scores = m[:, 2] - 0.45 * m[:, 1] - 0.2 * np.abs(m[:, 0])
        trend_idx = int(np.argmax(trend_scores))
        remaining = [i for i in range(self.n_states) if i != trend_idx]
        comp_idx = remaining[int(np.argmax(compression_scores[remaining]))]
        range_idx = [i for i in range(self.n_states) if i not in {comp_idx, trend_idx}][0]
        order = [comp_idx, trend_idx, range_idx]
        self.means_ = self.means_[order]
        self.covars_ = self.covars_[order]
        self.startprob_ = self.startprob_[order]
        self.transmat_ = self.transmat_[np.ix_(order, order)]

    def probability_map(self, features: Sequence[Sequence[float]]) -> Dict[str, float]:
        if not self.fitted_:
            raise RuntimeError("Model not fitted")
        x = np.asarray(features, dtype=float)
        if x.ndim == 1:
            x = x.reshape(1, -1)
        z = self._normalize_apply(x)
        gamma, _alpha, _ll = self._forward_backward(z)
        probs = gamma[-1]
        probs = probs / np.maximum(probs.sum(), 1e-12)
        return {name: float(probs[i]) for i, name in enumerate(self.state_names)}

    def forward_algorithm(self, obs_seq: Sequence[Sequence[float]]) -> Tuple[int, float, Dict[str, float]]:
        pmap = self.probability_map(obs_seq)
        probs = np.asarray([pmap[name] for name in self.state_names], dtype=float)
        idx = int(np.argmax(probs))
        return idx, float(probs[idx]), pmap

    def predict(self, features_current: Sequence[Sequence[float]]) -> Dict[str, Any]:
        idx, confidence, pmap = self.forward_algorithm(features_current)
        return {
            "regime": self.state_names[idx],
            "confidence": float(confidence),
            "probability_map": pmap,
            "transition_matrix": self.transition_matrix_list(),
            "method": METHOD,
            "version": VERSION,
            "valid": True,
        }

    def transition_matrix_list(self) -> List[List[float]]:
        if self.transmat_ is None:
            return []
        return [[float(v) for v in row] for row in self.transmat_]

    def save(self, model_path: str) -> None:
        Path(model_path).parent.mkdir(parents=True, exist_ok=True)
        with open(model_path, "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def load(model_path: str) -> "HMMRegimeGaussian":
        with open(model_path, "rb") as f:
            obj = pickle.load(f)
        if not isinstance(obj, HMMRegimeGaussian):
            raise TypeError("Invalid HMMRegimeGaussian model file")
        return obj


def fallback_result(reason: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    risks = [reason]
    if meta:
        risks.extend(meta.get("technical_risks", []))
    risks = sorted(set([r for r in risks if r]))
    return {
        "timestamp": utc_now_iso(),
        "regime": "RANGE",
        "confidence": 1.0,
        "probability_map": {"COMPRESSION": 0.0, "TENDANCE": 0.0, "RANGE": 1.0},
        "transition_matrix": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        "method": METHOD,
        "version": VERSION,
        "valid": True,
        "technical_risks": risks,
        "data_meta": meta or {},
    }


def train_from_db(
    db_path: str,
    symbol: str = "GBPUSD",
    primary_tf: int = 240,
    fallback_tf: int = 60,
    lookback: int = 500,
    min_rows: int = 24,
) -> Tuple[Optional[HMMRegimeGaussian], Dict[str, Any]]:
    features, meta = load_hmm_features_from_db(db_path, symbol=symbol, timeframe=primary_tf, lookback=lookback)
    used_tf = primary_tf
    if features.shape[0] < min_rows and fallback_tf != primary_tf:
        features_fb, meta_fb = load_hmm_features_from_db(db_path, symbol=symbol, timeframe=fallback_tf, lookback=lookback)
        if features_fb.shape[0] > features.shape[0]:
            features, meta = features_fb, meta_fb
            used_tf = fallback_tf
            meta.setdefault("technical_risks", []).append("TF240_INSUFFICIENT_USED_TF60_FALLBACK")
    meta["used_timeframe"] = used_tf
    meta["feature_rows"] = int(features.shape[0])

    if features.shape[0] < 8:
        return None, meta

    model = HMMRegimeGaussian()
    model.fit(features)
    return model, meta


def predict_from_db(
    model: HMMRegimeGaussian,
    db_path: str,
    symbol: str = "GBPUSD",
    timeframe: int = 240,
    fallback_tf: int = 60,
    lookback: int = 120,
) -> Dict[str, Any]:
    features, meta = load_hmm_features_from_db(db_path, symbol=symbol, timeframe=timeframe, lookback=lookback)
    if features.shape[0] < 8 and fallback_tf != timeframe:
        fb, meta_fb = load_hmm_features_from_db(db_path, symbol=symbol, timeframe=fallback_tf, lookback=lookback)
        if fb.shape[0] > features.shape[0]:
            features, meta = fb, meta_fb
            meta.setdefault("technical_risks", []).append("PREDICT_USED_FALLBACK_TF")
    meta["feature_rows"] = int(features.shape[0])

    if features.shape[0] < 3:
        return fallback_result("INSUFFICIENT_DATA_FOR_PREDICT", meta)

    result = model.predict(features)
    result["timestamp"] = utc_now_iso()
    result["data_meta"] = meta
    if meta.get("technical_risks"):
        result["technical_risks"] = sorted(set(meta["technical_risks"]))
    else:
        result["technical_risks"] = []
    return result


def write_json(path: str, payload: Dict[str, Any]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
