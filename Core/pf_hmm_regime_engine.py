"""
PowerFlow V7.2 — B1+ HMM Regime Engine
Dual architecture: standalone HMM regime perception, never fused with B1 Legacy.

Correction V7.2.1:
- The HMM activation guard is multi-timeframe.
- It does NOT wait for TF1440 / Daily to reach 50 rows.
- Default tactical stack: H1/M30/M15 = [60, 30, 15].
- H4/D can enrich the observation stack when present, but never block activation.
- DB access is read-only only.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math
import sqlite3
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import numpy as np
except Exception as exc:  # pragma: no cover
    raise RuntimeError("numpy is required for pf_hmm_regime_engine.py") from exc

CURRENCIES: Tuple[str, ...] = ("gbp", "usd", "eur", "jpy", "chf", "cad", "aud", "nzd")
VALID_REGIMES: Tuple[str, ...] = ("COMPRESSION", "TENDANCE", "RANGE", "TRANSITION")
DEFAULT_HMM_TIMEFRAMES: Tuple[int, ...] = (60, 30, 15)
CONTEXT_TIMEFRAMES: Tuple[int, ...] = (240, 1440)
MIN_MTF_OBSERVATIONS = 50
MIN_ROWS_PER_TF_FOR_FEATURES = 3


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ro_connect(db_path: str) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)


def _safe_float(value: object) -> float:
    try:
        if value is None:
            return 0.0
        out = float(value)
        if math.isnan(out) or math.isinf(out):
            return 0.0
        return out
    except Exception:
        return 0.0


def _dedupe_timeframes(values: Iterable[int]) -> Tuple[int, ...]:
    seen = set()
    out: List[int] = []
    for v in values:
        iv = int(v)
        if iv > 0 and iv not in seen:
            seen.add(iv)
            out.append(iv)
    return tuple(out)


@dataclass(frozen=True)
class HMMRegimeEngine:
    """Standalone B1+ Gaussian HMM regime perception over a multi-TF stack."""

    min_observations: int = MIN_MTF_OBSERVATIONS
    random_state: int = 42
    max_rows_per_tf: int = 220
    include_context_tfs: bool = True

    def compute(
        self,
        db_path: str,
        symbol: str = "GBPUSD",
        timeframes: Optional[Sequence[int]] = None,
    ) -> Dict[str, object]:
        requested_tfs = _dedupe_timeframes(timeframes or DEFAULT_HMM_TIMEFRAMES)
        context_tfs = CONTEXT_TIMEFRAMES if self.include_context_tfs else ()
        all_tfs = _dedupe_timeframes((*requested_tfs, *context_tfs))

        rows_by_tf = self._load_rows_by_tf(db_path, symbol, all_tfs)
        tactical_rows_by_tf = {tf: rows_by_tf.get(tf, []) for tf in requested_tfs}
        obs_blocks: List[np.ndarray] = []
        observation_tfs: List[int] = []

        for tf in all_tfs:
            block = self._build_observations_for_tf(rows_by_tf.get(tf, []), timeframe=tf)
            if block.shape[0] > 0:
                obs_blocks.append(block)
                observation_tfs.extend([tf] * int(block.shape[0]))

        obs = np.vstack(obs_blocks) if obs_blocks else np.empty((0, 4), dtype=float)
        obs = self._zscore(obs) if obs.shape[0] else obs
        rows_used_by_tf = {str(tf): len(rows_by_tf.get(tf, [])) for tf in all_tfs if len(rows_by_tf.get(tf, [])) > 0}
        tactical_rows = sum(len(v) for v in tactical_rows_by_tf.values())
        observations_used = int(obs.shape[0])

        if observations_used < self.min_observations:
            return {
                "regime_hmm": None,
                "regime_confidence_hmm": 0.0,
                "state_probabilities": {k: 0.0 for k in VALID_REGIMES},
                "method": "HMM_GAUSSIAN",
                "rows_used": tactical_rows,
                "observations_used": observations_used,
                "rows_used_by_tf": rows_used_by_tf,
                "timeframes_requested": list(requested_tfs),
                "timeframes_used": sorted({tf for tf in observation_tfs}),
                "regime_scope": "MULTI_TF_TACTICAL",
                "activation_guard": f"MIN_MTF_OBSERVATIONS>={self.min_observations}",
                "status": "INSUFFICIENT_DATA",
                "fallback": "B1_LEGACY",
                "timestamp": _utc_now(),
                "technical_risks": ["MULTI_TF_INSUFFICIENT_OBSERVATIONS"],
            }

        probs, risk = self._fit_predict_probabilities(obs)
        regime = max(probs, key=probs.get)
        confidence = float(max(probs.values())) if probs else 0.0
        used_tfs = sorted({tf for tf in observation_tfs})
        context_present = [tf for tf in CONTEXT_TIMEFRAMES if len(rows_by_tf.get(tf, [])) >= MIN_ROWS_PER_TF_FOR_FEATURES]
        scope = "HTF_ENRICHED" if context_present else "MULTI_TF_TACTICAL"
        technical_risks = [risk] if risk else []
        if not context_present:
            technical_risks.append("HTF_CONTEXT_THIN_BUT_NOT_BLOCKING")

        return {
            "regime_hmm": regime,
            "regime_confidence_hmm": round(max(0.0, min(1.0, confidence)), 6),
            "state_probabilities": {k: round(float(probs.get(k, 0.0)), 6) for k in VALID_REGIMES},
            "method": "HMM_GAUSSIAN",
            "rows_used": tactical_rows,
            "observations_used": observations_used,
            "rows_used_by_tf": rows_used_by_tf,
            "timeframes_requested": list(requested_tfs),
            "timeframes_used": used_tfs,
            "regime_scope": scope,
            "activation_guard": f"MIN_MTF_OBSERVATIONS>={self.min_observations}",
            "status": "ACTIVE",
            "fallback": None,
            "timestamp": _utc_now(),
            "technical_risks": technical_risks,
        }

    def _load_rows_by_tf(self, db_path: str, symbol: str, timeframes: Sequence[int]) -> Dict[int, List[Dict[str, float]]]:
        columns = ", ".join(["timestamp", "timeframe", *CURRENCIES])
        placeholders = ",".join("?" for _ in timeframes)
        query = f"""
            SELECT {columns}
            FROM force_snapshots
            WHERE symbol = ? AND timeframe IN ({placeholders})
            ORDER BY timeframe ASC, timestamp DESC
        """
        rows_by_tf: Dict[int, List[Dict[str, float]]] = {tf: [] for tf in timeframes}
        with _ro_connect(db_path) as conn:
            cur = conn.execute(query, (symbol, *timeframes))
            for row in cur.fetchall():
                tf = int(row[1])
                if len(rows_by_tf.setdefault(tf, [])) >= self.max_rows_per_tf:
                    continue
                values = {"timestamp": row[0], "timeframe": tf}
                for idx, c in enumerate(CURRENCIES, start=2):
                    values[c] = _safe_float(row[idx])
                rows_by_tf[tf].append(values)
        # Query returns newest first to limit cheaply; restore chronological order per TF.
        for tf in list(rows_by_tf):
            rows_by_tf[tf] = list(reversed(rows_by_tf[tf]))
        return rows_by_tf

    def _build_observations_for_tf(self, rows: Sequence[Dict[str, float]], timeframe: int) -> np.ndarray:
        if len(rows) < MIN_ROWS_PER_TF_FOR_FEATURES:
            return np.empty((0, 4), dtype=float)
        matrix = np.array([[float(r[c]) for c in CURRENCIES] for r in rows], dtype=float)
        if matrix.ndim != 2 or matrix.shape[0] < MIN_ROWS_PER_TF_FOR_FEATURES:
            return np.empty((0, 4), dtype=float)

        deltas = np.diff(matrix, axis=0, prepend=matrix[:1])
        std_force = np.std(matrix, axis=1)
        avg_abs_angle = np.mean(np.abs(deltas), axis=1)
        cross_dispersion = np.max(matrix, axis=1) - np.min(matrix, axis=1)
        mean_force = np.mean(matrix, axis=1)
        autocorr = np.zeros(matrix.shape[0], dtype=float)
        window = min(12, max(3, matrix.shape[0] // 5))
        for i in range(matrix.shape[0]):
            start = max(0, i - window + 1)
            segment = mean_force[start:i + 1]
            if len(segment) >= 3 and float(np.std(segment[:-1])) > 1e-12 and float(np.std(segment[1:])) > 1e-12:
                autocorr[i] = float(np.corrcoef(segment[:-1], segment[1:])[0, 1])
            else:
                autocorr[i] = 0.0

        # Keep the four requested observation families. TF role is carried in metadata, not blended into emissions.
        return np.column_stack([std_force, avg_abs_angle, autocorr, cross_dispersion])

    @staticmethod
    def _zscore(obs: np.ndarray) -> np.ndarray:
        mean = np.mean(obs, axis=0)
        std = np.std(obs, axis=0)
        std[std < 1e-9] = 1.0
        return (obs - mean) / std

    def _fit_predict_probabilities(self, obs: np.ndarray) -> Tuple[Dict[str, float], Optional[str]]:
        try:
            from hmmlearn.hmm import GaussianHMM  # type: ignore
            model = GaussianHMM(
                n_components=4,
                covariance_type="full",
                n_iter=250,
                random_state=self.random_state,
                min_covar=1e-4,
            )
            model.fit(obs)
            posterior = model.predict_proba(obs)[-1]
            means = model.means_
            state_to_regime = self._map_states_to_regimes(means)
            probs = {r: 0.0 for r in VALID_REGIMES}
            for idx, p in enumerate(posterior):
                probs[state_to_regime.get(idx, "TRANSITION")] += float(p)
            return self._normalize(probs), None
        except Exception:
            return self._fallback_probabilities(obs), "HMMLEARN_FALLBACK_HEURISTIC_USED"

    @staticmethod
    def _normalize(probs: Dict[str, float]) -> Dict[str, float]:
        total = sum(max(0.0, float(v)) for v in probs.values())
        if total <= 0:
            return {k: 1.0 / len(VALID_REGIMES) for k in VALID_REGIMES}
        return {k: max(0.0, float(probs.get(k, 0.0))) / total for k in VALID_REGIMES}

    def _map_states_to_regimes(self, means: np.ndarray) -> Dict[int, str]:
        raw: Dict[int, Dict[str, float]] = {}
        for i, m in enumerate(means):
            std_force, avg_abs_angle, autocorr, cross_dispersion = [float(x) for x in m]
            raw[i] = {
                "COMPRESSION": -0.65 * std_force - 0.45 * avg_abs_angle - 0.25 * cross_dispersion,
                "TENDANCE": 0.45 * avg_abs_angle + 0.35 * autocorr + 0.20 * cross_dispersion,
                "RANGE": -0.35 * abs(autocorr) - 0.25 * cross_dispersion - 0.15 * avg_abs_angle,
                "TRANSITION": 0.35 * abs(avg_abs_angle) + 0.35 * abs(std_force) + 0.30 * abs(cross_dispersion),
            }
        mapping: Dict[int, str] = {}
        used = set()
        pairs = sorted(((score, i, reg) for i, scores in raw.items() for reg, score in scores.items()), reverse=True)
        for _, i, reg in pairs:
            if i not in mapping and reg not in used:
                mapping[i] = reg
                used.add(reg)
        remaining = [r for r in VALID_REGIMES if r not in used]
        for i in range(len(means)):
            if i not in mapping:
                mapping[i] = remaining.pop(0) if remaining else "TRANSITION"
        return mapping

    def _fallback_probabilities(self, obs: np.ndarray) -> Dict[str, float]:
        last = obs[-1]
        std_force, avg_abs_angle, autocorr, cross_dispersion = [float(x) for x in last]
        scores = {
            "COMPRESSION": -0.70 * std_force - 0.35 * avg_abs_angle - 0.20 * cross_dispersion,
            "TENDANCE": 0.55 * avg_abs_angle + 0.35 * autocorr + 0.20 * cross_dispersion,
            "RANGE": -0.35 * abs(autocorr) - 0.30 * cross_dispersion - 0.20 * avg_abs_angle,
            "TRANSITION": 0.35 * abs(std_force) + 0.35 * abs(avg_abs_angle) + 0.30 * abs(cross_dispersion),
        }
        values = np.array([scores[k] for k in VALID_REGIMES], dtype=float)
        values = values - np.max(values)
        exps = np.exp(values)
        total = float(np.sum(exps)) or 1.0
        return {k: float(exps[i] / total) for i, k in enumerate(VALID_REGIMES)}


def compute(db_path: str, symbol: str = "GBPUSD", timeframes: Optional[Sequence[int]] = None) -> Dict[str, object]:
    return HMMRegimeEngine().compute(db_path=db_path, symbol=symbol, timeframes=timeframes)
