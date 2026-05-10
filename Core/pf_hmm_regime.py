"""
pf_hmm_regime.py
PowerFlow B1 — HMM Regime Engine V1.2 Standalone Schema-Aware

Gaussian Hidden Markov Model for HTF regime perception.
No external HMM dependency: numpy only.
V1.2 adds force_snapshots schema auto-detection for wide currency columns.

Regime order is fixed and deterministic:
    0 -> COMPRESSION
    1 -> TENDANCE
    2 -> RANGE

Architecture contract:
- pf_* moteur only
- SQLite read-only
- no cockpit/dashboard/telegram import
- no BUY/SELL, no trade decision
- context perception only
"""

from __future__ import annotations

import json
import math
import pickle
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np


MODEL_VERSION = "HMMRegimeV1.2StandaloneSchema"
METHOD = "hmm_gaussian_standalone"
REGIME_ORDER = ("COMPRESSION", "TENDANCE", "RANGE")
STATE_TO_REGIME = {0: "COMPRESSION", 1: "TENDANCE", 2: "RANGE"}
REGIME_TO_STATE = {v: k for k, v in STATE_TO_REGIME.items()}

KALMAN_Q = 0.01
KALMAN_R = 0.10
MIN_TRAINING_SAMPLES = 30
CONFIDENCE_THRESHOLD = 0.60
COVARIANCE_EPS = 1e-4
LOG_EPS = 1e-300


@dataclass
class FeatureFrame:
    timeframe: int
    timestamps: List[str]
    force_pair: List[float]
    angle_raw: List[float]
    speed_raw: List[float]
    zone_raw: List[float]
    observations: np.ndarray
    labels: np.ndarray
    scaler: Dict[str, List[float]]


@dataclass
class TrainingSummary:
    valid: bool
    timeframe: Optional[int]
    samples: int
    last_timestamp: Optional[str]
    label_counts: Dict[str, int]
    transition_matrix: List[List[float]]
    means: List[List[float]]
    covariance_diagonals: List[List[float]]
    technical_risks: List[str]
    error: Optional[str] = None


class StandaloneGaussianHMM:
    """Small deterministic Gaussian HMM implementation for 3 fixed regimes."""

    def __init__(self, n_components: int = 3) -> None:
        self.n_components = n_components
        self.startprob_: Optional[np.ndarray] = None
        self.transmat_: Optional[np.ndarray] = None
        self.means_: Optional[np.ndarray] = None
        self.covars_: Optional[np.ndarray] = None

    @property
    def fitted(self) -> bool:
        return all(
            value is not None
            for value in (self.startprob_, self.transmat_, self.means_, self.covars_)
        )

    def fit_from_labels(self, observations: np.ndarray, labels: np.ndarray) -> None:
        """Estimate HMM parameters from deterministic heuristic labels."""
        x = np.asarray(observations, dtype=float)
        y = np.asarray(labels, dtype=int)
        if x.ndim != 2:
            raise ValueError("observations must be a 2D array")
        if len(x) != len(y):
            raise ValueError("observations and labels length mismatch")
        if len(x) == 0:
            raise ValueError("empty observations")

        n_states = self.n_components
        n_features = x.shape[1]

        # Start probabilities. Strong but smoothed signal from the first labelled state.
        start = np.full(n_states, 1.0, dtype=float)
        start[int(y[0])] += 5.0
        self.startprob_ = start / start.sum()

        # Transition matrix with Laplace smoothing.
        trans = np.ones((n_states, n_states), dtype=float)
        for prev_state, next_state in zip(y[:-1], y[1:]):
            trans[int(prev_state), int(next_state)] += 1.0
        trans /= trans.sum(axis=1, keepdims=True)
        self.transmat_ = trans

        global_mean = np.mean(x, axis=0)
        global_cov = np.cov(x.T) if len(x) > 1 else np.eye(n_features)
        global_cov = self._regularize_cov(global_cov, n_features)

        means = np.zeros((n_states, n_features), dtype=float)
        covars = np.zeros((n_states, n_features, n_features), dtype=float)

        for state in range(n_states):
            state_x = x[y == state]
            if len(state_x) == 0:
                means[state] = global_mean
                covars[state] = global_cov
                continue
            means[state] = np.mean(state_x, axis=0)
            if len(state_x) >= 2:
                cov = np.cov(state_x.T)
            else:
                cov = global_cov
            covars[state] = self._regularize_cov(cov, n_features)

        self.means_ = means
        self.covars_ = covars

    @staticmethod
    def _regularize_cov(cov: np.ndarray, n_features: int) -> np.ndarray:
        cov_arr = np.asarray(cov, dtype=float)
        if cov_arr.ndim == 0:
            cov_arr = np.eye(n_features) * float(cov_arr)
        if cov_arr.ndim == 1:
            cov_arr = np.diag(cov_arr)
        if cov_arr.shape != (n_features, n_features):
            cov_arr = np.eye(n_features)
        cov_arr = np.nan_to_num(cov_arr, nan=0.0, posinf=1.0, neginf=1.0)
        cov_arr = (cov_arr + cov_arr.T) / 2.0
        cov_arr += np.eye(n_features) * COVARIANCE_EPS
        return cov_arr

    def _log_gaussian_prob(self, observations: np.ndarray) -> np.ndarray:
        if not self.fitted:
            raise RuntimeError("model not fitted")
        x = np.asarray(observations, dtype=float)
        n_samples, n_features = x.shape
        log_prob = np.zeros((n_samples, self.n_components), dtype=float)

        for state in range(self.n_components):
            mean = self.means_[state]
            cov = self._regularize_cov(self.covars_[state], n_features)
            sign, logdet = np.linalg.slogdet(cov)
            if sign <= 0:
                cov = cov + np.eye(n_features) * 1e-3
                sign, logdet = np.linalg.slogdet(cov)
            inv_cov = np.linalg.pinv(cov)
            diff = x - mean
            mahal = np.einsum("ij,jk,ik->i", diff, inv_cov, diff)
            log_prob[:, state] = -0.5 * (
                n_features * math.log(2.0 * math.pi) + logdet + mahal
            )
        return log_prob

    @staticmethod
    def _logsumexp(values: np.ndarray) -> float:
        max_v = np.max(values)
        if not np.isfinite(max_v):
            return float(max_v)
        return float(max_v + np.log(np.sum(np.exp(values - max_v))))

    def posterior_last(self, observations: np.ndarray) -> Tuple[int, List[float]]:
        """Forward pass and posterior probabilities for last observation."""
        if not self.fitted:
            raise RuntimeError("model not fitted")
        x = np.asarray(observations, dtype=float)
        if x.ndim != 2 or len(x) == 0:
            raise ValueError("observations must be non-empty 2D array")

        log_emit = self._log_gaussian_prob(x)
        log_start = np.log(np.asarray(self.startprob_, dtype=float) + LOG_EPS)
        log_trans = np.log(np.asarray(self.transmat_, dtype=float) + LOG_EPS)

        alpha = log_start + log_emit[0]
        for t in range(1, len(x)):
            next_alpha = np.zeros(self.n_components, dtype=float)
            for j in range(self.n_components):
                next_alpha[j] = self._logsumexp(alpha + log_trans[:, j]) + log_emit[t, j]
            alpha = next_alpha

        norm = self._logsumexp(alpha)
        probs = np.exp(alpha - norm)
        probs = probs / probs.sum()
        state = int(np.argmax(probs))
        return state, [float(round(p, 6)) for p in probs]


class HMMRegimeEngine:
    """Train and query a standalone Gaussian HMM for PowerFlow B1 regimes."""

    def __init__(self, model_path: Optional[str | Path] = None) -> None:
        self.model_path = Path(model_path).resolve() if model_path else None
        self.model = StandaloneGaussianHMM(n_components=3)
        self.scaler: Optional[Dict[str, List[float]]] = None
        self.training_summary: Optional[Dict[str, Any]] = None
        self.source_columns: Optional[Dict[str, str]] = None

        if self.model_path and self.model_path.exists():
            self.load_model(self.model_path)

    @staticmethod
    def utc_now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def train_on_historical_data(
        self,
        db_path: str | Path,
        tfs: Sequence[int] = (240, 60),
        model_path: Optional[str | Path] = None,
    ) -> Dict[str, Any]:
        """Load DB, extract HTF features, train HMM, and optionally save model."""
        db = Path(db_path).resolve()
        risks: List[str] = []

        if not db.exists():
            summary = TrainingSummary(
                valid=False,
                timeframe=None,
                samples=0,
                last_timestamp=None,
                label_counts={},
                transition_matrix=[],
                means=[],
                covariance_diagonals=[],
                technical_risks=["DB_NOT_FOUND"],
                error=f"DB not found: {db}",
            )
            self.training_summary = asdict(summary)
            return self.training_summary

        frame = self._load_best_feature_frame(db, tfs)
        if frame is None:
            summary = TrainingSummary(
                valid=False,
                timeframe=None,
                samples=0,
                last_timestamp=None,
                label_counts={},
                transition_matrix=[],
                means=[],
                covariance_diagonals=[],
                technical_risks=["INSUFFICIENT_DATA"],
                error="No timeframe had enough usable force snapshots",
            )
            self.training_summary = asdict(summary)
            return self.training_summary

        if len(frame.observations) < MIN_TRAINING_SAMPLES:
            summary = TrainingSummary(
                valid=False,
                timeframe=frame.timeframe,
                samples=len(frame.observations),
                last_timestamp=frame.timestamps[-1] if frame.timestamps else None,
                label_counts=self._label_counts(frame.labels),
                transition_matrix=[],
                means=[],
                covariance_diagonals=[],
                technical_risks=["INSUFFICIENT_DATA"],
                error=f"Need at least {MIN_TRAINING_SAMPLES} samples",
            )
            self.training_summary = asdict(summary)
            return self.training_summary

        self.model = StandaloneGaussianHMM(n_components=3)
        self.model.fit_from_labels(frame.observations, frame.labels)
        self.scaler = frame.scaler

        label_counts = self._label_counts(frame.labels)
        if min(label_counts.values() or [0]) <= 1:
            risks.append("LOW_STATE_DIVERSITY")

        summary = TrainingSummary(
            valid=True,
            timeframe=frame.timeframe,
            samples=len(frame.observations),
            last_timestamp=frame.timestamps[-1] if frame.timestamps else None,
            label_counts=label_counts,
            transition_matrix=np.round(self.model.transmat_, 6).tolist(),
            means=np.round(self.model.means_, 6).tolist(),
            covariance_diagonals=np.round(
                np.array([np.diag(cov) for cov in self.model.covars_]), 6
            ).tolist(),
            technical_risks=risks,
            error=None,
        )
        self.training_summary = asdict(summary)

        target_model_path = Path(model_path).resolve() if model_path else self.model_path
        if target_model_path:
            self.save_model(target_model_path)

        return self.training_summary

    def predict_from_db(
        self,
        db_path: str | Path,
        tfs: Sequence[int] = (240, 60),
        lookback: int = 50,
    ) -> Dict[str, Any]:
        """Predict the current HTF regime from the latest DB snapshots."""
        if not self.model.fitted or self.scaler is None:
            return self._invalid_prediction(
                error="MODEL_NOT_LOADED",
                risks=["HMM_MODEL_MISSING"],
                source={"db_path": str(Path(db_path).resolve())},
            )

        frame = self._load_best_feature_frame(Path(db_path).resolve(), tfs, scaler=self.scaler)
        if frame is None or len(frame.observations) == 0:
            return self._invalid_prediction(
                error="NO_USABLE_OBSERVATIONS",
                risks=["INSUFFICIENT_DATA"],
                source={"db_path": str(Path(db_path).resolve())},
            )

        observations = frame.observations[-lookback:]
        raw_state, probabilities = self.model.posterior_last(observations)
        confidence = float(max(probabilities))
        regime = STATE_TO_REGIME[raw_state]
        risks: List[str] = []
        valid = True
        error = None

        if confidence < CONFIDENCE_THRESHOLD:
            valid = False
            error = "LOW_CONFIDENCE"
            risks.append("LOW_CONFIDENCE")

        return {
            "timestamp": self.utc_now(),
            "regime": regime,
            "confidence": round(confidence, 6),
            "probabilities": probabilities,
            "probability_map": {
                regime_name: probabilities[idx]
                for idx, regime_name in STATE_TO_REGIME.items()
            },
            "raw_state": raw_state,
            "method": METHOD,
            "model_version": MODEL_VERSION,
            "valid": valid,
            "error": error,
            "technical_risks": risks,
            "source": {
                "db_path": str(Path(db_path).resolve()),
                "timeframe": frame.timeframe,
                "samples_used": len(frame.observations),
                "prediction_lookback": min(lookback, len(frame.observations)),
                "last_timestamp": frame.timestamps[-1] if frame.timestamps else None,
            },
            "htf_context_stack": None,
        }

    def predict_regime(self, force_rolling: Sequence[Any]) -> Dict[str, Any]:
        """Predict from a rolling force sequence or a sequence of alert-like rows."""
        if not self.model.fitted or self.scaler is None:
            return self._invalid_prediction(
                error="MODEL_NOT_LOADED",
                risks=["HMM_MODEL_MISSING"],
                source={"input": "force_rolling"},
            )

        if not force_rolling:
            return self._invalid_prediction(
                error="EMPTY_FORCE_ROLLING",
                risks=["INSUFFICIENT_DATA"],
                source={"input": "force_rolling"},
            )

        values = self._extract_force_pair_from_sequence(force_rolling)
        if len(values) < 5:
            return self._invalid_prediction(
                error="INSUFFICIENT_FORCE_ROLLING",
                risks=["INSUFFICIENT_DATA"],
                source={"samples_used": len(values)},
            )

        timestamps = [str(i) for i in range(len(values))]
        frame = self._build_feature_frame_from_series(
            timeframe=0,
            timestamps=timestamps,
            force_pair=values,
            scaler=self.scaler,
        )
        raw_state, probabilities = self.model.posterior_last(frame.observations)
        confidence = float(max(probabilities))
        regime = STATE_TO_REGIME[raw_state]
        valid = confidence >= CONFIDENCE_THRESHOLD
        risks = [] if valid else ["LOW_CONFIDENCE"]

        return {
            "timestamp": self.utc_now(),
            "regime": regime,
            "confidence": round(confidence, 6),
            "probabilities": probabilities,
            "probability_map": {
                regime_name: probabilities[idx]
                for idx, regime_name in STATE_TO_REGIME.items()
            },
            "raw_state": raw_state,
            "method": METHOD,
            "model_version": MODEL_VERSION,
            "valid": valid,
            "error": None if valid else "LOW_CONFIDENCE",
            "technical_risks": risks,
            "source": {"input": "force_rolling", "samples_used": len(values)},
            "htf_context_stack": None,
        }

    def save_model(self, path: str | Path) -> None:
        target = Path(path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "model_version": MODEL_VERSION,
            "method": METHOD,
            "regime_order": REGIME_ORDER,
            "startprob": self.model.startprob_,
            "transmat": self.model.transmat_,
            "means": self.model.means_,
            "covars": self.model.covars_,
            "scaler": self.scaler,
            "training_summary": self.training_summary,
            "source_columns": self.source_columns,
            "saved_at": self.utc_now(),
        }
        with target.open("wb") as f:
            pickle.dump(payload, f)
        self.model_path = target

    def load_model(self, path: str | Path) -> None:
        source = Path(path).resolve()
        with source.open("rb") as f:
            payload = pickle.load(f)
        self.model = StandaloneGaussianHMM(n_components=3)
        self.model.startprob_ = np.asarray(payload["startprob"], dtype=float)
        self.model.transmat_ = np.asarray(payload["transmat"], dtype=float)
        self.model.means_ = np.asarray(payload["means"], dtype=float)
        self.model.covars_ = np.asarray(payload["covars"], dtype=float)
        self.scaler = payload.get("scaler")
        self.training_summary = payload.get("training_summary")
        self.source_columns = payload.get("source_columns")
        self.model_path = source

    def _invalid_prediction(
        self, error: str, risks: List[str], source: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return {
            "timestamp": self.utc_now(),
            "regime": None,
            "confidence": 0.0,
            "probabilities": [0.0, 0.0, 0.0],
            "probability_map": {},
            "raw_state": None,
            "method": METHOD,
            "model_version": MODEL_VERSION,
            "valid": False,
            "error": error,
            "technical_risks": risks,
            "source": source or {},
            "htf_context_stack": None,
        }

    def _load_best_feature_frame(
        self,
        db_path: Path,
        tfs: Sequence[int],
        scaler: Optional[Dict[str, List[float]]] = None,
    ) -> Optional[FeatureFrame]:
        candidates: List[FeatureFrame] = []
        for tf in tfs:
            rows = self._read_force_rows(db_path, int(tf))
            if len(rows) < 5:
                continue
            timestamps = [row[0] for row in rows]
            force_pair = [float(row[1]) - float(row[2]) for row in rows]
            frame = self._build_feature_frame_from_series(
                timeframe=int(tf),
                timestamps=timestamps,
                force_pair=force_pair,
                scaler=scaler,
            )
            candidates.append(frame)

        if not candidates:
            return None

        # Prefer the first timeframe with enough samples. Prompt priority: TF240 then TF60.
        for frame in candidates:
            if len(frame.observations) >= MIN_TRAINING_SAMPLES:
                return frame
        return max(candidates, key=lambda item: len(item.observations))

    def _read_force_rows(self, db_path: Path, timeframe: int) -> List[Tuple[str, float, float]]:
        """Read GBP/USD force rows from force_snapshots with schema auto-detection.

        PowerFlow DBs have evolved: some snapshots use force_gbp/force_usd,
        others use plain currency columns such as GBP/USD or lower-case gbp/usd.
        This resolver accepts both exact and fuzzy currency column names while
        preserving read-only DB access.
        """
        uri = f"file:{db_path}?mode=ro"
        with sqlite3.connect(uri, uri=True) as conn:
            conn.row_factory = sqlite3.Row
            table_columns = self._get_table_columns(conn, "force_snapshots")
            if not table_columns:
                raise RuntimeError("force_snapshots table not found or has no columns")

            schema = self._resolve_force_snapshot_schema(conn, table_columns, timeframe)

            if schema.get("layout") == "long":
                return self._read_force_rows_long(conn, schema, timeframe)

            ts_col = schema["timestamp"]
            tf_col = schema["timeframe"]
            gbp_col = schema["gbp"]
            usd_col = schema["usd"]

            self.source_columns = {
                "layout": "wide",
                "timestamp": ts_col,
                "timeframe": tf_col,
                "gbp": gbp_col,
                "usd": usd_col,
            }

            query = (
                f'SELECT {self._qid(ts_col)} AS timestamp, '
                f'{self._qid(gbp_col)} AS gbp, {self._qid(usd_col)} AS usd '
                f'FROM force_snapshots WHERE {self._qid(tf_col)} = ? '
                f'AND {self._qid(gbp_col)} IS NOT NULL AND {self._qid(usd_col)} IS NOT NULL '
                f'ORDER BY {self._qid(ts_col)} ASC'
            )
            rows = conn.execute(query, (timeframe,)).fetchall()
            return [(str(row["timestamp"]), float(row["gbp"]), float(row["usd"])) for row in rows]

    @staticmethod
    def _qid(identifier: str) -> str:
        """Quote a SQLite identifier safely."""
        return '"' + str(identifier).replace('"', '""') + '"'

    @staticmethod
    def _get_table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
        return [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]

    def _resolve_force_snapshot_schema(
        self, conn: sqlite3.Connection, columns: Sequence[str], timeframe: int
    ) -> Dict[str, str]:
        ts_col = self._pick_timestamp_column(columns)
        tf_col = self._pick_timeframe_column(columns)

        if not ts_col or not tf_col:
            raise RuntimeError(
                "force_snapshots schema unresolved: timestamp/timeframe column missing; "
                f"available_columns={list(columns)}"
            )

        # Wide schema: one row has many currency columns.
        gbp_col = self._pick_currency_column(conn, columns, timeframe, "GBP", exclude={ts_col, tf_col})
        usd_col = self._pick_currency_column(conn, columns, timeframe, "USD", exclude={ts_col, tf_col})
        if gbp_col and usd_col:
            return {
                "layout": "wide",
                "timestamp": ts_col,
                "timeframe": tf_col,
                "gbp": gbp_col,
                "usd": usd_col,
            }

        # Long schema fallback: timestamp/timeframe/currency/value rows.
        currency_col = self._pick_column_fuzzy(
            columns,
            exact=["currency", "ccy", "asset", "name"],
            contains=["currency", "ccy"],
            exclude={ts_col, tf_col},
        )
        value_col = self._pick_column_fuzzy(
            columns,
            exact=["force", "value", "score", "zscore", "strength"],
            contains=["force", "score", "zscore", "strength", "value"],
            exclude={ts_col, tf_col, currency_col} if currency_col else {ts_col, tf_col},
        )
        if currency_col and value_col:
            return {
                "layout": "long",
                "timestamp": ts_col,
                "timeframe": tf_col,
                "currency": currency_col,
                "value": value_col,
            }

        raise RuntimeError(
            "force_snapshots schema unresolved: could not find GBP/USD force columns; "
            f"available_columns={list(columns)}; "
            f"resolved_timestamp={ts_col}; resolved_timeframe={tf_col}"
        )

    def _read_force_rows_long(
        self, conn: sqlite3.Connection, schema: Dict[str, str], timeframe: int
    ) -> List[Tuple[str, float, float]]:
        ts_col = schema["timestamp"]
        tf_col = schema["timeframe"]
        currency_col = schema["currency"]
        value_col = schema["value"]

        self.source_columns = {
            "layout": "long",
            "timestamp": ts_col,
            "timeframe": tf_col,
            "currency": currency_col,
            "value": value_col,
        }

        query = (
            f'SELECT {self._qid(ts_col)} AS timestamp, '
            f'{self._qid(currency_col)} AS currency, {self._qid(value_col)} AS value '
            f'FROM force_snapshots WHERE {self._qid(tf_col)} = ? '
            f"AND UPPER({self._qid(currency_col)}) IN ('GBP', 'USD') "
            f'AND {self._qid(value_col)} IS NOT NULL '
            f'ORDER BY {self._qid(ts_col)} ASC'
        )
        rows = conn.execute(query, (timeframe,)).fetchall()
        by_ts: Dict[str, Dict[str, float]] = {}
        for row in rows:
            ts = str(row["timestamp"])
            currency = str(row["currency"]).upper()
            by_ts.setdefault(ts, {})[currency] = float(row["value"])

        output: List[Tuple[str, float, float]] = []
        for ts in sorted(by_ts.keys()):
            bucket = by_ts[ts]
            if "GBP" in bucket and "USD" in bucket:
                output.append((ts, bucket["GBP"], bucket["USD"]))
        return output

    @staticmethod
    def _pick_timestamp_column(columns: Sequence[str]) -> Optional[str]:
        return HMMRegimeEngine._pick_column_fuzzy(
            columns,
            exact=["timestamp", "ts", "time", "datetime", "date", "created_at", "snapshot_time"],
            contains=["timestamp", "datetime", "snapshot_time"],
            exclude={"timeframe", "tf", "tf_minutes"},
        )

    @staticmethod
    def _pick_timeframe_column(columns: Sequence[str]) -> Optional[str]:
        return HMMRegimeEngine._pick_column_fuzzy(
            columns,
            exact=["timeframe", "tf", "period", "tf_minutes", "timeframe_minutes"],
            contains=["timeframe", "tf_minutes"],
            exclude=set(),
        )

    def _pick_currency_column(
        self,
        conn: sqlite3.Connection,
        columns: Sequence[str],
        timeframe: int,
        currency: str,
        exclude: set[str],
    ) -> Optional[str]:
        c = currency.lower()
        exact = [
            currency,
            currency.upper(),
            currency.lower(),
            f"force_{c}",
            f"{c}_force",
            f"z_{c}",
            f"{c}_z",
            f"zscore_{c}",
            f"{c}_zscore",
            f"score_{c}",
            f"{c}_score",
            f"strength_{c}",
            f"{c}_strength",
            f"value_{c}",
            f"{c}_value",
            f"raw_{c}",
            f"{c}_raw",
        ]
        contains = [c]
        candidates = self._rank_matching_columns(columns, exact=exact, contains=contains, exclude=exclude)
        for col in candidates:
            if self._column_has_numeric_values(conn, col, timeframe):
                return col
        return None

    @staticmethod
    def _pick_column_fuzzy(
        columns: Sequence[str],
        exact: Sequence[str],
        contains: Sequence[str],
        exclude: set[str] | None = None,
    ) -> Optional[str]:
        ranked = HMMRegimeEngine._rank_matching_columns(columns, exact, contains, exclude or set())
        return ranked[0] if ranked else None

    @staticmethod
    def _rank_matching_columns(
        columns: Sequence[str], exact: Sequence[str], contains: Sequence[str], exclude: set[str]
    ) -> List[str]:
        exclude_l = {str(x).lower() for x in exclude if x}
        exact_l = [x.lower() for x in exact if x]
        contains_l = [x.lower() for x in contains if x]
        scored: List[Tuple[int, int, str]] = []
        for col in columns:
            lower = col.lower()
            if lower in exclude_l:
                continue
            score: Optional[int] = None
            if lower in exact_l:
                score = exact_l.index(lower)
            elif any(token in lower for token in contains_l):
                # Prefer short semantic names like GBP over metadata names containing GBP.
                score = 100 + len(lower)
            if score is not None:
                scored.append((score, len(lower), col))
        scored.sort(key=lambda item: (item[0], item[1], item[2].lower()))
        return [item[2] for item in scored]

    def _column_has_numeric_values(
        self, conn: sqlite3.Connection, column: str, timeframe: int, limit: int = 20
    ) -> bool:
        # Timeframe column may not be resolved here, so do a lightweight table-wide sample.
        try:
            query = (
                f'SELECT {self._qid(column)} AS value FROM force_snapshots '
                f'WHERE {self._qid(column)} IS NOT NULL LIMIT ?'
            )
            rows = conn.execute(query, (limit,)).fetchall()
            if not rows:
                return False
            numeric = 0
            for row in rows:
                try:
                    float(row["value"])
                    numeric += 1
                except (TypeError, ValueError):
                    pass
            return numeric > 0
        except sqlite3.Error:
            return False

    @staticmethod
    def _pick_column(columns: Iterable[str], candidates: Sequence[str]) -> Optional[str]:
        column_map = {col.lower(): col for col in columns}
        for candidate in candidates:
            if candidate.lower() in column_map:
                return column_map[candidate.lower()]
        return None

    def _build_feature_frame_from_series(
        self,
        timeframe: int,
        timestamps: Sequence[str],
        force_pair: Sequence[float],
        scaler: Optional[Dict[str, List[float]]] = None,
    ) -> FeatureFrame:
        values = np.asarray(force_pair, dtype=float)
        values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
        smooth = self._kalman_filter(values, q=KALMAN_Q, r=KALMAN_R)

        angle_raw = self._angle_series(smooth)
        speed_raw = self._speed_series(angle_raw)
        zone_raw = self._zone_numeric_series(values)

        raw_features = np.column_stack([angle_raw, speed_raw, zone_raw])
        labels = self._heuristic_labels(angle_raw, speed_raw, zone_raw)
        labels = self._ensure_state_diversity(raw_features, labels)

        if scaler is None:
            means = raw_features.mean(axis=0)
            stds = raw_features.std(axis=0)
            stds = np.where(stds < 1e-9, 1.0, stds)
            # Keep zone in 0..1 instead of z-normalized.
            means[2] = 0.0
            stds[2] = 5.0
            scaler = {"mean": means.tolist(), "std": stds.tolist()}
        else:
            means = np.asarray(scaler["mean"], dtype=float)
            stds = np.asarray(scaler["std"], dtype=float)
            stds = np.where(stds < 1e-9, 1.0, stds)

        observations = (raw_features - means) / stds
        observations = np.nan_to_num(observations, nan=0.0, posinf=0.0, neginf=0.0)

        return FeatureFrame(
            timeframe=timeframe,
            timestamps=list(timestamps),
            force_pair=values.tolist(),
            angle_raw=angle_raw.tolist(),
            speed_raw=speed_raw.tolist(),
            zone_raw=zone_raw.tolist(),
            observations=observations,
            labels=labels,
            scaler=scaler,
        )

    @staticmethod
    def _kalman_filter(values: np.ndarray, q: float, r: float) -> np.ndarray:
        if len(values) == 0:
            return values
        x_est = float(values[0])
        p_est = 1.0
        output = np.zeros(len(values), dtype=float)
        output[0] = x_est
        for i in range(1, len(values)):
            x_pred = x_est
            p_pred = p_est + q
            k_gain = p_pred / (p_pred + r)
            x_est = x_pred + k_gain * (float(values[i]) - x_pred)
            p_est = (1.0 - k_gain) * p_pred
            output[i] = x_est
        return output

    @staticmethod
    def _angle_series(values: np.ndarray) -> np.ndarray:
        if len(values) < 2:
            return np.zeros(len(values), dtype=float)
        diffs = np.gradient(values)
        local_scale = np.zeros(len(values), dtype=float)
        for i in range(len(values)):
            start = max(0, i - 10)
            window = values[start : i + 1]
            local_scale[i] = np.std(window) if len(window) > 1 else np.std(values)
        local_scale = np.where(local_scale < 1e-9, np.std(values) + 1e-6, local_scale)
        normalized_slope = diffs / local_scale
        angles = np.degrees(np.arctan(normalized_slope * 10.0))
        return np.clip(angles, -89.0, 89.0)

    @staticmethod
    def _speed_series(angle: np.ndarray) -> np.ndarray:
        if len(angle) < 2:
            return np.zeros(len(angle), dtype=float)
        return np.abs(np.gradient(angle))

    @staticmethod
    def _zone_numeric_series(values: np.ndarray) -> np.ndarray:
        mean = np.mean(values)
        std = np.std(values)
        if std < 1e-9:
            z = np.zeros(len(values), dtype=float)
        else:
            z = (values - mean) / std
        abs_z = np.abs(z)
        zone = np.zeros(len(values), dtype=float)
        zone[(abs_z >= 0.50) & (abs_z < 0.90)] = 1.0   # PRE_EXTREME
        zone[(abs_z >= 0.90) & (abs_z < 1.20)] = 2.0   # EARLY_EXTREME
        zone[(abs_z >= 1.20) & (abs_z < 1.60)] = 3.0   # ACCUMULATING
        zone[(abs_z >= 1.60) & (abs_z < 2.00)] = 4.0   # LEAKING
        zone[abs_z >= 2.00] = 5.0                      # RUPTURE
        return zone

    @staticmethod
    def _heuristic_labels(angle: np.ndarray, speed: np.ndarray, zone: np.ndarray) -> np.ndarray:
        labels = np.full(len(angle), REGIME_TO_STATE["RANGE"], dtype=int)
        angle_std = np.zeros(len(angle), dtype=float)
        for i in range(len(angle)):
            start = max(0, i - 6)
            angle_std[i] = np.std(angle[start : i + 1])

        abs_angle = np.abs(angle)
        zone_norm = zone / 5.0

        compression_mask = (angle_std < 18.0) & (abs_angle < 42.0) & (zone_norm >= 0.45)
        trend_mask = abs_angle >= 35.0

        labels[compression_mask] = REGIME_TO_STATE["COMPRESSION"]
        labels[trend_mask] = REGIME_TO_STATE["TENDANCE"]
        return labels

    @staticmethod
    def _ensure_state_diversity(features: np.ndarray, labels: np.ndarray) -> np.ndarray:
        """Guarantee every state has data on small HTF samples."""
        y = labels.copy()
        counts = {state: int(np.sum(y == state)) for state in range(3)}
        if all(count > 0 for count in counts.values()):
            return y

        abs_angle = np.abs(features[:, 0])
        speed = features[:, 1]
        zone = features[:, 2]
        n = len(y)
        if n < 3:
            return y

        # TENDANCE: strongest angular displacement.
        trend_count = max(1, int(round(n * 0.25)))
        trend_idx = np.argsort(abs_angle)[-trend_count:]
        y[trend_idx] = REGIME_TO_STATE["TENDANCE"]

        # COMPRESSION: high zone tension but limited angle/speed.
        compression_score = (zone / 5.0) - (abs_angle / 100.0) - (speed / (np.std(speed) + 1.0)) * 0.05
        compression_count = max(1, int(round(n * 0.25)))
        compression_idx = np.argsort(compression_score)[-compression_count:]
        y[compression_idx] = REGIME_TO_STATE["COMPRESSION"]

        # Remaining defaults to RANGE.
        for state in range(3):
            if int(np.sum(y == state)) == 0:
                candidate = int(np.argsort(abs_angle)[n // 2])
                y[candidate] = state
        return y

    @staticmethod
    def _label_counts(labels: np.ndarray) -> Dict[str, int]:
        return {
            STATE_TO_REGIME[state]: int(np.sum(labels == state))
            for state in range(3)
        }

    @staticmethod
    def _extract_force_pair_from_sequence(force_rolling: Sequence[Any]) -> List[float]:
        values: List[float] = []
        for item in force_rolling:
            if isinstance(item, dict):
                if "force_pair" in item:
                    values.append(float(item["force_pair"]))
                elif "force_gbp" in item and "force_usd" in item:
                    values.append(float(item["force_gbp"]) - float(item["force_usd"]))
                elif "gbp" in item and "usd" in item:
                    values.append(float(item["gbp"]) - float(item["usd"]))
                elif "value" in item:
                    values.append(float(item["value"]))
            else:
                values.append(float(item))
        return values


def main() -> None:
    """Small smoke entrypoint. Prefer run_hmm_regime_once.py for CLI usage."""
    print(json.dumps({"module": "pf_hmm_regime", "model_version": MODEL_VERSION, "method": METHOD}, indent=2))


if __name__ == "__main__":
    main()
