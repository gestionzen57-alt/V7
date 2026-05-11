# -*- coding: utf-8 -*-
"""PowerFlow V7.2 — Cross-Symbol Validation.

Mission:
  - Lire powerflow.db en READ ONLY.
  - Comparer les forces de devises sur plusieurs symboles sans écrire en DB.
  - Distinguer force propre d'une devise vs faiblesse dominante d'une devise opposée.

Doctrine:
  - Aucune décision BUY/SELL.
  - Aucune fusion avec les outputs par symbole.
  - Output cross-symbol dédié: output/dashboard_surface/cross_validation.json.
"""
from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

DEFAULT_SYMBOLS = ["GBPUSD", "EURUSD", "USDJPY"]
DEFAULT_CURRENCIES = ["GBP", "EUR", "USD", "JPY", "XAU", "CAD", "CHF", "AUD"]
MAJOR_3 = {"GBP", "EUR", "USD", "JPY", "CAD", "CHF", "AUD", "NZD", "XAU"}


@dataclass(frozen=True)
class SymbolEvidence:
    symbol: str
    base: str
    quote: str
    timestamp: str | None
    rows: int
    timeframe: int | None
    base_force: float | None
    quote_force: float | None
    pair_diff: float | None
    currency_forces: dict[str, float]
    technical_risks: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "base": self.base,
            "quote": self.quote,
            "timestamp": self.timestamp,
            "rows": self.rows,
            "timeframe": self.timeframe,
            "base_force": self.base_force,
            "quote_force": self.quote_force,
            "pair_diff": self.pair_diff,
            "currency_forces": self.currency_forces,
            "technical_risks": self.technical_risks,
        }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect_ro(db_path: str | Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{Path(db_path)}?mode=ro", uri=True)


def _tables(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return {str(r[0]) for r in rows}


def _columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [str(r[1]) for r in conn.execute(f'PRAGMA table_info("{table}")').fetchall()]


def _pick_table(conn: sqlite3.Connection) -> str:
    tables = _tables(conn)
    for candidate in ("force_snapshots", "force_snapshots_v2"):
        if candidate in tables:
            return candidate
    raise RuntimeError("No force_snapshots table found")


def _timestamp_column(cols: Iterable[str]) -> str | None:
    lower = {c.lower(): c for c in cols}
    for name in ("created_at", "timestamp", "time", "ts", "datetime"):
        if name in lower:
            return lower[name]
    return None


def _timeframe_column(cols: Iterable[str]) -> str | None:
    lower = {c.lower(): c for c in cols}
    for name in ("timeframe", "tf"):
        if name in lower:
            return lower[name]
    return None


def _symbol_column(cols: Iterable[str]) -> str | None:
    lower = {c.lower(): c for c in cols}
    return lower.get("symbol")


def _force_columns(cols: Iterable[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    lower = {c.lower(): c for c in cols}
    for ccy in DEFAULT_CURRENCIES:
        force_name = f"force_{ccy.lower()}"
        raw_name = ccy.lower()
        if force_name in lower:
            out[ccy] = lower[force_name]
        elif raw_name in lower:
            out[ccy] = lower[raw_name]
    return out


def _parse_symbol(symbol: str) -> tuple[str, str]:
    s = symbol.strip().upper().replace("/", "").replace("_", "")
    if len(s) < 6:
        raise ValueError(f"Invalid symbol: {symbol}")
    for base_len in (3, 4):
        base = s[:base_len]
        quote = s[base_len:]
        if base in MAJOR_3 and quote in MAJOR_3:
            return base, quote
    return s[:3], s[3:6]


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        x = float(value)
    except Exception:
        return None
    if math.isnan(x) or math.isinf(x):
        return None
    return x


def _mean_non_null(values: list[Any]) -> float | None:
    xs = [_safe_float(v) for v in values]
    ys = [x for x in xs if x is not None]
    return float(mean(ys)) if ys else None


def _fetch_symbol_evidence(
    conn: sqlite3.Connection,
    table: str,
    symbol: str,
    timeframe: int,
    bars: int,
) -> SymbolEvidence:
    cols = _columns(conn, table)
    sym_col = _symbol_column(cols)
    tf_col = _timeframe_column(cols)
    ts_col = _timestamp_column(cols)
    force_cols = _force_columns(cols)
    base, quote = _parse_symbol(symbol)
    risks: list[str] = []

    if sym_col is None:
        risks.append("SYMBOL_COLUMN_MISSING")
    if tf_col is None:
        risks.append("TIMEFRAME_COLUMN_MISSING")
    if ts_col is None:
        risks.append("TIMESTAMP_COLUMN_MISSING")
    if base not in force_cols:
        risks.append(f"BASE_FORCE_COLUMN_MISSING_{base}")
    if quote not in force_cols:
        risks.append(f"QUOTE_FORCE_COLUMN_MISSING_{quote}")

    select_cols = []
    if ts_col:
        select_cols.append(f'"{ts_col}"')
    for col in force_cols.values():
        select_cols.append(f'"{col}"')
    if not select_cols:
        return SymbolEvidence(symbol, base, quote, None, 0, timeframe, None, None, None, {}, risks)

    where = []
    params: list[Any] = []
    if sym_col:
        where.append(f'UPPER("{sym_col}") = ?')
        params.append(symbol.upper())
    if tf_col:
        where.append(f'"{tf_col}" = ?')
        params.append(timeframe)
    where_sql = " WHERE " + " AND ".join(where) if where else ""
    order_sql = f' ORDER BY "{ts_col}" DESC' if ts_col else ""
    sql = f'SELECT {", ".join(select_cols)} FROM "{table}"{where_sql}{order_sql} LIMIT ?'
    params.append(int(bars))

    try:
        rows = conn.execute(sql, params).fetchall()
    except Exception as exc:
        risks.append(f"SQL_ERROR_{type(exc).__name__}")
        return SymbolEvidence(symbol, base, quote, None, 0, timeframe, None, None, None, {}, risks)

    if not rows:
        risks.append("NO_ROWS_FOR_SYMBOL_TIMEFRAME")
        return SymbolEvidence(symbol, base, quote, None, 0, timeframe, None, None, None, {}, risks)

    # Rows are DESC by timestamp. The first row is latest.
    latest_timestamp = str(rows[0][0]) if ts_col else None
    offset = 1 if ts_col else 0
    col_order = list(force_cols.items())
    currency_forces: dict[str, float] = {}
    for idx, (ccy, _col_name) in enumerate(col_order):
        values = [r[offset + idx] for r in rows]
        avg = _mean_non_null(values)
        if avg is not None:
            currency_forces[ccy] = round(avg, 6)

    base_force = currency_forces.get(base)
    quote_force = currency_forces.get(quote)
    pair_diff = None
    if base_force is not None and quote_force is not None:
        pair_diff = round(base_force - quote_force, 6)
    else:
        risks.append("PAIR_DIFF_UNAVAILABLE")

    return SymbolEvidence(
        symbol=symbol.upper(),
        base=base,
        quote=quote,
        timestamp=latest_timestamp,
        rows=len(rows),
        timeframe=timeframe,
        base_force=base_force,
        quote_force=quote_force,
        pair_diff=pair_diff,
        currency_forces=currency_forces,
        technical_risks=risks,
    )


def _label_strength(score: float | None, evidence_count: int) -> str:
    if score is None or evidence_count <= 0:
        return "UNKNOWN"
    if score >= 0.40:
        return "STRONG"
    if score >= 0.12:
        return "MODERATE"
    if score <= -0.12:
        return "WEAK"
    return "UNKNOWN"


def _normalize_net_scores(raw_scores: dict[str, float]) -> dict[str, float]:
    if not raw_scores:
        return {}
    max_abs = max(abs(v) for v in raw_scores.values()) or 1.0
    if max_abs < 1e-9:
        return {k: 0.0 for k in raw_scores}
    return {k: round(v / max_abs, 6) for k, v in raw_scores.items()}


def _driver_detection(
    labels: dict[str, str],
    normalized: dict[str, float],
    sign_evidence: dict[str, list[float]],
    symbols: list[str],
) -> tuple[str, float, list[str]]:
    risks: list[str] = []

    usd_values = sign_evidence.get("USD", [])
    gbp_values = sign_evidence.get("GBP", [])
    eur_values = sign_evidence.get("EUR", [])
    jpy_values = sign_evidence.get("JPY", [])

    def mostly_negative(vals: list[float], minimum: int = 2) -> bool:
        return len(vals) >= minimum and sum(1 for x in vals if x < 0) >= minimum

    def mostly_positive(vals: list[float], minimum: int = 2) -> bool:
        return len(vals) >= minimum and sum(1 for x in vals if x > 0) >= minimum

    if labels.get("USD") == "WEAK" and mostly_negative(usd_values, 2):
        return "USD_WEAKNESS_DOMINANT", 0.82, risks

    if labels.get("GBP") in {"STRONG", "MODERATE"} and mostly_positive(gbp_values, 2):
        return "GBP_STRENGTH_GENUINE", 0.78, risks

    # EUR divergence: EURUSD positive while EUR is not broadly strong or GBP dominates EUR.
    eurusd_present = "EURUSD" in symbols
    eur_score = normalized.get("EUR")
    gbp_score = normalized.get("GBP")
    if eurusd_present and eur_score is not None and gbp_score is not None:
        if eur_score > 0.10 and gbp_score > eur_score + 0.15:
            risks.append("EUR_DIVERGENCE_INFERRED_WITHOUT_EURGBP_DIRECT_CROSS")
            return "EUR_DIVERGENT", 0.64, risks

    if labels.get("JPY") in {"STRONG", "MODERATE"} and mostly_positive(jpy_values, 2):
        return "JPY_SAFE_HAVEN", 0.74, risks

    if len(symbols) < 3:
        risks.append("CROSS_COVERAGE_THIN_DRIVER_MIXED")
    return "MIXED", 0.50, risks


class CrossSymbolValidator:
    """Cross-symbol force validator for PowerFlow.

    Public API:
        CrossSymbolValidator().compute("powerflow.db", ["GBPUSD", "EURUSD", "USDJPY"])
    """

    def __init__(self, timeframe: int = 1, bars: int = 60) -> None:
        self.timeframe = int(timeframe)
        self.bars = int(bars)

    def compute(self, db_path: str | Path, symbols: list[str] | None = None) -> dict[str, Any]:
        symbols = [s.strip().upper() for s in (symbols or DEFAULT_SYMBOLS) if s.strip()]
        technical_risks: list[str] = []
        evidence: list[SymbolEvidence] = []

        try:
            with _connect_ro(db_path) as conn:
                table = _pick_table(conn)
                for sym in symbols:
                    evidence.append(_fetch_symbol_evidence(conn, table, sym, self.timeframe, self.bars))
        except Exception as exc:
            technical_risks.append(f"DB_READ_ERROR_{type(exc).__name__}")
            table = None

        used = [e.symbol for e in evidence if e.rows > 0 and e.pair_diff is not None]
        if len(used) < 2:
            technical_risks.append("INSUFFICIENT_SYMBOLS_USED_FOR_CROSS_VALIDATION")

        raw_net: dict[str, float] = {}
        evidence_count: dict[str, int] = {}
        sign_evidence: dict[str, list[float]] = {}

        for e in evidence:
            technical_risks.extend(e.technical_risks)
            if e.pair_diff is None:
                continue
            # Pair decomposition: base receives +diff, quote receives -diff.
            raw_net[e.base] = raw_net.get(e.base, 0.0) + e.pair_diff
            raw_net[e.quote] = raw_net.get(e.quote, 0.0) - e.pair_diff
            evidence_count[e.base] = evidence_count.get(e.base, 0) + 1
            evidence_count[e.quote] = evidence_count.get(e.quote, 0) + 1
            sign_evidence.setdefault(e.base, []).append(e.pair_diff)
            sign_evidence.setdefault(e.quote, []).append(-e.pair_diff)

        normalized = _normalize_net_scores(raw_net)
        labels = {
            c: _label_strength(normalized.get(c), evidence_count.get(c, 0))
            for c in ("GBP", "USD", "EUR", "JPY")
        }

        # Coverage risks: these do not block output; they qualify perception.
        if evidence_count.get("GBP", 0) < 2:
            technical_risks.append("GBP_TRUE_STRENGTH_REQUIRES_MORE_GBP_CROSSES")
        if evidence_count.get("EUR", 0) < 2:
            technical_risks.append("EUR_TRUE_STRENGTH_REQUIRES_MORE_EUR_CROSSES")
        if evidence_count.get("JPY", 0) < 2:
            technical_risks.append("JPY_TRUE_STRENGTH_REQUIRES_MORE_JPY_CROSSES")
        if evidence_count.get("USD", 0) < 2:
            technical_risks.append("USD_COVERAGE_THIN")

        driver, driver_confidence, driver_risks = _driver_detection(labels, normalized, sign_evidence, used)
        technical_risks.extend(driver_risks)

        confidence = min(1.0, round(driver_confidence * (0.65 + 0.10 * min(len(used), 3)), 3))
        technical_risks = sorted(set(r for r in technical_risks if r))

        output = {
            "cross_validation": {
                "gbp_true_strength": labels.get("GBP", "UNKNOWN"),
                "usd_true_strength": labels.get("USD", "UNKNOWN"),
                "eur_true_strength": labels.get("EUR", "UNKNOWN"),
                "jpy_true_strength": labels.get("JPY", "UNKNOWN"),
                "driver": driver,
                "confidence": confidence,
                "symbols_used": used,
                "technical_risks": technical_risks,
                "timestamp": _utc_now(),
                "method": "CROSS_SYMBOL_PAIR_DIFF_V1",
                "timeframe": self.timeframe,
                "bars": self.bars,
                "net_strength": {
                    c: {
                        "score": normalized.get(c),
                        "raw_score": round(raw_net.get(c, 0.0), 6),
                        "label": _label_strength(normalized.get(c), evidence_count.get(c, 0)),
                        "evidence_count": evidence_count.get(c, 0),
                    }
                    for c in sorted(set(list(raw_net.keys()) + ["GBP", "USD", "EUR", "JPY"]))
                },
                "symbol_evidence": [e.to_dict() for e in evidence],
                "db_table": table,
            }
        }
        return output


def compute(db_path: str | Path, symbols: list[str] | None = None) -> dict[str, Any]:
    return CrossSymbolValidator().compute(db_path, symbols or DEFAULT_SYMBOLS)


def write_cross_validation_state(state: dict[str, Any], out_path: str | Path, pretty: bool = True) -> None:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(state, ensure_ascii=False, indent=2 if pretty else None) + "\n", encoding="utf-8")
