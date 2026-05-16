"""B8 data visibility checker for PowerFlow V7.6.7.

This module qualifies data coverage, freshness, and allowed evidence role for
B8 multidevise symbols. It is intentionally read-only against powerflow.db.

Doctrine:
- B8 is the multidevise field engine, not only cross-symbol validation.
- This checker does not decide market direction. It qualifies the evidence.
- Thin/stale symbols remain visible, but their role and weight are lowered.
- D1/W1 are target HTF timeframes, but missing D1/W1 does not block current B8.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class VisibilityThresholds:
    """Configurable thresholds for B8 visibility classification."""

    coverage_dense_min: int = 200
    coverage_normal_min: int = 50
    freshness_live_max_sec: int = 300
    freshness_normal_max_sec: int = 600
    freshness_stale_max_sec: int = 3600
    snapshot_lookback_hours: int = 24


class B8DataVisibilityChecker:
    """Qualify coverage and freshness for B8 multidevise evidence.

    Coverage states:
        DENSE, NORMAL, THIN, MISSING

    Freshness states:
        LIVE, NORMAL, STALE, MISSING

    Role states:
        PRIMARY: usable as strong B8 evidence.
        CONTEXT_ONLY: usable as supporting context with reduced weight.
        EXCLUDED: do not use as B8 evidence because data is absent/critical.

    The checker never writes to the target database. It opens SQLite using
    mode=ro and returns structured diagnostic dictionaries.
    """

    MINIMUM_TFS = ("M5", "M15", "M30", "H1", "H4")
    FUTURE_TFS = ("D1", "W1")
    EXPECTED_TFS = MINIMUM_TFS + FUTURE_TFS

    B8_13_CURRENT = (
        "GBPUSD",
        "EURUSD",
        "AUDUSD",
        "NZDUSD",
        "USDJPY",
        "USDCAD",
        "USDCHF",
        "EURGBP",
        "GBPJPY",
        "GBPAUD",
        "GBPCAD",
        "GBPCHF",
        "GBPNZD",
    )

    B8_28_TARGET = (
        "EURUSD",
        "GBPUSD",
        "AUDUSD",
        "NZDUSD",
        "USDJPY",
        "USDCHF",
        "USDCAD",
        "EURGBP",
        "EURJPY",
        "EURCHF",
        "EURCAD",
        "EURAUD",
        "EURNZD",
        "GBPJPY",
        "GBPCHF",
        "GBPCAD",
        "GBPAUD",
        "GBPNZD",
        "AUDJPY",
        "AUDCHF",
        "AUDCAD",
        "AUDNZD",
        "NZDJPY",
        "NZDCHF",
        "NZDCAD",
        "CADJPY",
        "CADCHF",
        "CHFJPY",
    )

    KNOWN_SPARSE_SYMBOLS = {"USDJPY"}

    _TIMEFRAME_ALIASES = {
        "1": "M1",
        "5": "M5",
        "15": "M15",
        "30": "M30",
        "60": "H1",
        "240": "H4",
        "1440": "D1",
        "10080": "W1",
        "M1": "M1",
        "M5": "M5",
        "M15": "M15",
        "M30": "M30",
        "H1": "H1",
        "H4": "H4",
        "D1": "D1",
        "W1": "W1",
        "PERIOD_M1": "M1",
        "PERIOD_M5": "M5",
        "PERIOD_M15": "M15",
        "PERIOD_M30": "M30",
        "PERIOD_H1": "H1",
        "PERIOD_H4": "H4",
        "PERIOD_D1": "D1",
        "PERIOD_W1": "W1",
    }

    def __init__(
        self,
        db_path: Optional[str] = None,
        thresholds: Optional[VisibilityThresholds] = None,
    ) -> None:
        self.db_path = db_path
        self.thresholds = thresholds or VisibilityThresholds()
        self.last_checks: Dict[str, Dict[str, Any]] = {}

    def check_symbol_visibility(
        self,
        symbol: str,
        db_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Check coverage, freshness, role, and risks for one symbol."""
        symbol = self._normalize_symbol(symbol)
        db = db_path or self.db_path

        if not symbol:
            return self._empty_visibility_state("", "SYMBOL_MISSING")
        if not db:
            return self._empty_visibility_state(symbol, "DB_PATH_MISSING")

        try:
            source_table = self._get_snapshot_table(db, symbol=symbol)
            if not source_table:
                return self._empty_visibility_state(symbol, "SNAPSHOT_TABLE_MISSING")

            coverage_info = self._count_snapshots(symbol, db, source_table)
            coverage_state = self._classify_coverage(coverage_info["count"])

            available_tfs, missing_tfs = self._detect_available_tfs(
                symbol, db, source_table
            )
            last_update = self._get_last_update_timestamp(symbol, db, source_table)
            age_sec = self._compute_age_seconds(last_update) if last_update else None
            freshness_state = self._classify_freshness(age_sec)

            role_allowed = self._determine_role(
                symbol=symbol,
                coverage=coverage_state,
                freshness=freshness_state,
                available_tfs=available_tfs,
            )
            technical_risks = self._detect_technical_risks(
                symbol=symbol,
                coverage=coverage_state,
                freshness=freshness_state,
                available_tfs=available_tfs,
                source_table=source_table,
            )
            b8_weight_cap = self._determine_weight_cap(
                symbol=symbol,
                coverage=coverage_state,
                freshness=freshness_state,
                role=role_allowed,
                technical_risks=technical_risks,
            )
            quality_score = self._score_data_quality(
                coverage=coverage_state,
                freshness=freshness_state,
                tf_count=len(available_tfs),
            )

            result = {
                "symbol": symbol,
                "source_table": source_table,
                "coverage_state": coverage_state,
                "coverage_count": coverage_info["count"],
                "freshness_state": freshness_state,
                "last_update": last_update,
                "last_update_age_sec": age_sec if age_sec is not None else -1,
                "available_tfs": sorted(available_tfs, key=self._tf_sort_key),
                "missing_tfs": sorted(missing_tfs, key=self._tf_sort_key),
                "role_allowed": role_allowed,
                "technical_risks": sorted(set(technical_risks)),
                "b8_weight_cap": round(b8_weight_cap, 2),
                "data_quality_score": round(quality_score, 2),
                "timestamp": self._utc_now(),
            }
            self.last_checks[symbol] = result
            return result
        except Exception as exc:  # defensive boundary for runtime safety
            return self._error_visibility_state(symbol, str(exc))

    def check_b8_universe_visibility(
        self,
        symbols: Sequence[str],
        db_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Check overall B8 field visibility across a symbol universe."""
        clean_symbols = [self._normalize_symbol(s) for s in symbols if self._normalize_symbol(s)]
        symbol_states = {
            symbol: self.check_symbol_visibility(symbol, db_path)
            for symbol in clean_symbols
        }

        dense = sum(
            1 for state in symbol_states.values() if state["coverage_state"] == "DENSE"
        )
        normal = sum(
            1 for state in symbol_states.values() if state["coverage_state"] == "NORMAL"
        )
        thin = sum(
            1 for state in symbol_states.values() if state["coverage_state"] == "THIN"
        )
        missing = sum(
            1 for state in symbol_states.values() if state["coverage_state"] == "MISSING"
        )

        primary = [
            symbol
            for symbol, state in symbol_states.items()
            if state["role_allowed"] == "PRIMARY"
        ]
        context_only = [
            symbol
            for symbol, state in symbol_states.items()
            if state["role_allowed"] == "CONTEXT_ONLY"
        ]
        excluded = [
            symbol
            for symbol, state in symbol_states.items()
            if state["role_allowed"] == "EXCLUDED"
        ]

        all_risks = set()
        for state in symbol_states.values():
            all_risks.update(state.get("technical_risks", []))

        universe = self._classify_universe(clean_symbols)
        field_visibility = self._classify_field_visibility(
            dense=dense,
            normal=normal,
            missing=missing,
            total=len(clean_symbols),
        )

        result = {
            "universe": universe,
            "symbols_expected": len(clean_symbols),
            "symbols_present": len(clean_symbols) - missing,
            "symbols_dense": dense,
            "symbols_normal": normal,
            "symbols_thin": thin,
            "symbols_missing": missing,
            "primary_symbols": sorted(primary),
            "context_only_symbols": sorted(context_only),
            "excluded_symbols": sorted(excluded),
            "field_visibility": field_visibility,
            "technical_risks": sorted(all_risks),
            "timestamp": self._utc_now(),
            "detail": {
                symbol: {
                    "source_table": state.get("source_table"),
                    "coverage_state": state["coverage_state"],
                    "freshness_state": state["freshness_state"],
                    "role_allowed": state["role_allowed"],
                    "b8_weight_cap": state.get("b8_weight_cap", 1.0),
                    "data_quality_score": state.get("data_quality_score", 0.0),
                    "technical_risks": state.get("technical_risks", []),
                }
                for symbol, state in symbol_states.items()
            },
        }
        return result

    def _get_snapshot_table(
        self,
        db_path: str,
        symbol: Optional[str] = None,
    ) -> Optional[str]:
        """Detect force_snapshots_v2 or force_snapshots, preferring v2.

        If a symbol is supplied and v2 exists but has no rows for the symbol while
        v1 has rows, this method falls back to force_snapshots. That avoids false
        MISSING states during migrations where both tables coexist.
        """
        tables = self._list_tables(db_path)
        candidates = [t for t in ("force_snapshots_v2", "force_snapshots") if t in tables]
        if not candidates:
            return None
        if symbol is None:
            return candidates[0]

        usable = []
        for table in candidates:
            if not self._table_has_required_columns(db_path, table):
                continue
            count = self._count_rows_for_symbol(db_path, table, symbol)
            usable.append((table, count))

        if not usable:
            return candidates[0]

        for table, count in usable:
            if table == "force_snapshots_v2" and count > 0:
                return table
        for table, count in usable:
            if table == "force_snapshots" and count > 0:
                return table
        return usable[0][0]

    def _count_snapshots(
        self,
        symbol: str,
        db_path: str,
        table: str,
    ) -> Dict[str, Any]:
        """Count snapshots for symbol in the configured lookback window."""
        with self._connect_ro(db_path) as conn:
            columns = self._get_columns(conn, table)
            time_col = self._detect_time_column(columns)
            query = f"""
                SELECT COUNT(*) AS cnt
                FROM {table}
                WHERE UPPER(symbol) = UPPER(?)
                  AND {time_col} > datetime('now', ?)
            """
            lookback = f"-{int(self.thresholds.snapshot_lookback_hours)} hours"
            row = conn.execute(query, [symbol, lookback]).fetchone()
            return {"count": int(row["cnt"] if row else 0), "symbol": symbol}

    def _detect_available_tfs(
        self,
        symbol: str,
        db_path: str,
        table: str,
    ) -> Tuple[List[str], List[str]]:
        """Detect timeframes with any data for symbol."""
        with self._connect_ro(db_path) as conn:
            columns = self._get_columns(conn, table)
            tf_col = self._detect_timeframe_column(columns)
            if not tf_col:
                return [], list(self.EXPECTED_TFS)
            query = f"""
                SELECT DISTINCT {tf_col} AS tf
                FROM {table}
                WHERE UPPER(symbol) = UPPER(?)
            """
            rows = conn.execute(query, [symbol]).fetchall()

        available = sorted(
            {self._normalize_timeframe(row["tf"]) for row in rows if row["tf"] is not None},
            key=self._tf_sort_key,
        )
        missing = [tf for tf in self.EXPECTED_TFS if tf not in available]
        return available, missing

    def _get_last_update_timestamp(
        self,
        symbol: str,
        db_path: str,
        table: str,
    ) -> Optional[str]:
        """Return most recent snapshot timestamp for symbol."""
        with self._connect_ro(db_path) as conn:
            columns = self._get_columns(conn, table)
            time_col = self._detect_time_column(columns)
            query = f"""
                SELECT {time_col} AS ts
                FROM {table}
                WHERE UPPER(symbol) = UPPER(?)
                ORDER BY {time_col} DESC
                LIMIT 1
            """
            row = conn.execute(query, [symbol]).fetchone()
            return str(row["ts"]) if row and row["ts"] is not None else None

    def _classify_coverage(self, count: int) -> str:
        if count >= self.thresholds.coverage_dense_min:
            return "DENSE"
        if count >= self.thresholds.coverage_normal_min:
            return "NORMAL"
        if count > 0:
            return "THIN"
        return "MISSING"

    def _classify_freshness(self, age_sec: Optional[int]) -> str:
        if age_sec is None:
            return "MISSING"
        if age_sec <= self.thresholds.freshness_live_max_sec:
            return "LIVE"
        if age_sec <= self.thresholds.freshness_normal_max_sec:
            return "NORMAL"
        if age_sec <= self.thresholds.freshness_stale_max_sec:
            return "STALE"
        return "MISSING"

    def _compute_age_seconds(self, timestamp: str) -> Optional[int]:
        """Compute UTC age for common SQLite/ISO timestamp formats."""
        if not timestamp:
            return None
        try:
            raw = str(timestamp).strip()
            if raw.endswith("Z"):
                parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            elif "T" in raw:
                parsed = datetime.fromisoformat(raw)
            else:
                parsed = datetime.strptime(raw.split(".")[0], "%Y-%m-%d %H:%M:%S")
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds()
            return max(0, int(age))
        except Exception:
            return None

    def _determine_role(
        self,
        symbol: str,
        coverage: str,
        freshness: str,
        available_tfs: Sequence[str],
    ) -> str:
        """Determine allowed evidence role for a symbol."""
        available_set = set(available_tfs)
        has_minimum = all(tf in available_set for tf in self.MINIMUM_TFS)

        if coverage == "MISSING" or freshness == "MISSING":
            return "EXCLUDED"
        if not has_minimum:
            return "EXCLUDED"
        if coverage == "DENSE" and freshness in {"LIVE", "NORMAL"}:
            return "PRIMARY"
        if coverage in {"NORMAL", "THIN"} and freshness in {"LIVE", "NORMAL", "STALE"}:
            return "CONTEXT_ONLY"
        return "EXCLUDED"

    def _detect_technical_risks(
        self,
        symbol: str,
        coverage: str,
        freshness: str,
        available_tfs: Sequence[str],
        source_table: Optional[str] = None,
    ) -> List[str]:
        risks: List[str] = []
        available_set = set(available_tfs)

        if coverage == "MISSING":
            risks.append(f"{symbol}_MISSING" if symbol else "SYMBOL_MISSING")
        elif coverage == "THIN":
            risks.append("LOW_SAMPLE_COUNT")
            risks.append("SPARSE_SYMBOL")
            risks.append(f"{symbol}_THIN")

        if freshness in {"STALE", "MISSING"}:
            risks.append("FEED_INTERMITTENT")
        if freshness == "MISSING":
            risks.append("LAST_UPDATE_MISSING")

        if any(tf not in available_set for tf in self.MINIMUM_TFS):
            risks.append("INCOMPLETE_TF_COVERAGE")
        if any(tf not in available_set for tf in self.FUTURE_TFS):
            risks.append("HTF_D1_W1_MISSING")

        if symbol in self.KNOWN_SPARSE_SYMBOLS and coverage == "THIN":
            risks.append("KNOWN_SPARSE_SYMBOL")
        if source_table == "force_snapshots":
            risks.append("LEGACY_SNAPSHOT_TABLE")

        return risks

    def _determine_weight_cap(
        self,
        symbol: str,
        coverage: str,
        freshness: str,
        role: str,
        technical_risks: Sequence[str],
    ) -> float:
        """Cap future B8 evidence weight based on visibility quality."""
        if role == "EXCLUDED":
            return 0.0
        if symbol in self.KNOWN_SPARSE_SYMBOLS and coverage == "THIN":
            return 0.25
        if coverage == "THIN" or freshness == "STALE":
            return 0.35
        if role == "CONTEXT_ONLY":
            return 0.60
        return 1.0

    def _score_data_quality(self, coverage: str, freshness: str, tf_count: int) -> float:
        score = 0.0
        score += {"DENSE": 0.50, "NORMAL": 0.30, "THIN": 0.10}.get(coverage, 0.0)
        score += {"LIVE": 0.30, "NORMAL": 0.20, "STALE": 0.05}.get(freshness, 0.0)
        score += min(1.0, tf_count / float(len(self.MINIMUM_TFS))) * 0.20
        return max(0.0, min(1.0, score))

    def _classify_universe(self, symbols: Sequence[str]) -> str:
        symbol_set = set(symbols)
        if len(symbols) == 13 and symbol_set == set(self.B8_13_CURRENT):
            return "B8_13_CURRENT"
        if len(symbols) == 28 and symbol_set == set(self.B8_28_TARGET):
            return "B8_28_TARGET"
        return "B8_CUSTOM"

    def _classify_field_visibility(
        self,
        dense: int,
        normal: int,
        missing: int,
        total: int,
    ) -> str:
        if total <= 0:
            return "CRITICAL"
        if dense >= max(8, int(total * 0.60)) and missing == 0:
            return "STRONG"
        if dense + normal >= max(8, int(total * 0.60)) and missing <= 2:
            return "TACTICAL_OK"
        if dense + normal >= max(5, int(total * 0.35)) and missing <= 4:
            return "DEGRADED"
        return "CRITICAL"

    def _list_tables(self, db_path: str) -> List[str]:
        with self._connect_ro(db_path) as conn:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        return [str(row["name"]) for row in rows]

    def _table_has_required_columns(self, db_path: str, table: str) -> bool:
        with self._connect_ro(db_path) as conn:
            columns = self._get_columns(conn, table)
        return "symbol" in columns and self._detect_time_column(columns) is not None

    def _count_rows_for_symbol(self, db_path: str, table: str, symbol: str) -> int:
        try:
            with self._connect_ro(db_path) as conn:
                row = conn.execute(
                    f"SELECT COUNT(*) AS cnt FROM {table} WHERE UPPER(symbol) = UPPER(?)",
                    [symbol],
                ).fetchone()
            return int(row["cnt"] if row else 0)
        except Exception:
            return 0

    def _connect_ro(self, db_path: str) -> sqlite3.Connection:
        resolved = Path(db_path).resolve()
        conn = sqlite3.connect(f"file:{resolved}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_columns(self, conn: sqlite3.Connection, table: str) -> List[str]:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return [str(row["name"]) for row in rows]

    def _detect_time_column(self, columns: Iterable[str]) -> Optional[str]:
        column_set = set(columns)
        for candidate in (
            "timestamp",
            "created_at",
            "logged_at",
            "bar_time",
            "time",
            "datetime",
        ):
            if candidate in column_set:
                return candidate
        return None

    def _detect_timeframe_column(self, columns: Iterable[str]) -> Optional[str]:
        column_set = set(columns)
        for candidate in ("timeframe", "tf", "tf_name", "period"):
            if candidate in column_set:
                return candidate
        return None

    def _normalize_symbol(self, symbol: Any) -> str:
        return str(symbol or "").strip().upper()

    def _normalize_timeframe(self, value: Any) -> str:
        raw = str(value).strip().upper()
        return self._TIMEFRAME_ALIASES.get(raw, raw)

    def _tf_sort_key(self, tf: str) -> int:
        order = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440, "W1": 10080}
        return order.get(tf, 999999)

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _empty_visibility_state(self, symbol: str, reason: str) -> Dict[str, Any]:
        result = {
            "symbol": symbol,
            "source_table": None,
            "coverage_state": "MISSING",
            "coverage_count": 0,
            "freshness_state": "MISSING",
            "last_update": None,
            "last_update_age_sec": -1,
            "available_tfs": [],
            "missing_tfs": list(self.EXPECTED_TFS),
            "role_allowed": "EXCLUDED",
            "technical_risks": [reason],
            "b8_weight_cap": 0.0,
            "data_quality_score": 0.0,
            "timestamp": self._utc_now(),
        }
        if symbol:
            self.last_checks[symbol] = result
        return result

    def _error_visibility_state(self, symbol: str, error: str) -> Dict[str, Any]:
        return self._empty_visibility_state(symbol, f"ERROR:{error}")


__all__ = ["B8DataVisibilityChecker", "VisibilityThresholds"]
