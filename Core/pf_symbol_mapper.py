"""
pf_symbol_mapper.py
PowerFlow V7.1 — Universal symbol -> force column mapper.

Purpose
-------
Centralise symbol awareness so B1-B7 and run_* files stop hardcoding
force_gbp / force_usd. This module is read-only and schema-aware: it can
validate requested force columns against the actual force_snapshots schema.

Doctrine
--------
This module maps perception inputs. It does not predict, trade, filter, or
write to the database.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


DEFAULT_SYMBOL = "GBPUSD"
DEFAULT_TABLE = "force_snapshots"


SYMBOL_FORCE_MAP: Dict[str, Tuple[str, str]] = {
    "GBPUSD": ("force_gbp", "force_usd"),
    "EURUSD": ("force_eur", "force_usd"),
    "USDJPY": ("force_usd", "force_jpy"),
    "XAUUSD": ("force_xau", "force_usd"),
}


class SymbolMappingError(ValueError):
    """Raised when a symbol cannot be mapped safely to DB force columns."""


@dataclass(frozen=True)
class SymbolMapping:
    """Resolved mapping for one trading symbol."""

    symbol: str
    base_asset: str
    quote_asset: str
    base_column: str
    quote_column: str

    @property
    def force_columns(self) -> Tuple[str, str]:
        return self.base_column, self.quote_column

    def as_dict(self) -> Dict[str, object]:
        return {
            "symbol": self.symbol,
            "base_asset": self.base_asset,
            "quote_asset": self.quote_asset,
            "force_columns": [self.base_column, self.quote_column],
        }


def normalize_symbol(symbol: str) -> str:
    """Normalize a user/CLI symbol into PowerFlow canonical uppercase form."""
    cleaned = re.sub(r"[^A-Za-z0-9]", "", str(symbol or "")).upper()
    if not cleaned:
        raise SymbolMappingError("Empty symbol after normalization")
    return cleaned


def parse_symbol_assets(symbol: str) -> Tuple[str, str]:
    """
    Return (base_asset, quote_asset) for a supported PowerFlow symbol.

    Explicit mapping is preferred. A fallback 6-char split exists for future
    FX symbols when their force columns are present and the caller decides to
    add them to SYMBOL_FORCE_MAP later.
    """
    symbol_clean = normalize_symbol(symbol)
    if symbol_clean in SYMBOL_FORCE_MAP:
        base_col, quote_col = SYMBOL_FORCE_MAP[symbol_clean]
        return base_col.replace("force_", "").upper(), quote_col.replace("force_", "").upper()

    if len(symbol_clean) == 6:
        return symbol_clean[:3], symbol_clean[3:]

    raise SymbolMappingError(
        f"Unsupported symbol format {symbol!r}. Add it to SYMBOL_FORCE_MAP explicitly."
    )


def get_force_columns(
    symbol: str,
    db_columns: Optional[Sequence[str]] = None,
    *,
    allow_inferred_fx: bool = False,
) -> Tuple[str, str]:
    """
    Return (force_base_col, force_quote_col) for a symbol.

    Examples
    --------
    GBPUSD -> (force_gbp, force_usd)
    EURUSD -> (force_eur, force_usd)
    USDJPY -> (force_usd, force_jpy)
    XAUUSD -> (force_xau, force_usd)

    If db_columns is provided, both columns are validated against the actual
    table schema. Missing columns raise SymbolMappingError with an explicit
    message; there is no silent fallback.
    """
    symbol_clean = normalize_symbol(symbol)

    if symbol_clean in SYMBOL_FORCE_MAP:
        base_col, quote_col = SYMBOL_FORCE_MAP[symbol_clean]
    elif allow_inferred_fx and len(symbol_clean) == 6:
        base, quote = symbol_clean[:3].lower(), symbol_clean[3:].lower()
        base_col, quote_col = f"force_{base}", f"force_{quote}"
    else:
        supported = ", ".join(sorted(SYMBOL_FORCE_MAP))
        raise SymbolMappingError(
            f"Symbol {symbol_clean} not in mapping. Supported symbols: {supported}."
        )

    if db_columns is not None:
        existing = set(db_columns)
        missing = [col for col in (base_col, quote_col) if col not in existing]
        if missing:
            raise SymbolMappingError(
                f"Symbol {symbol_clean} requires columns {base_col}, {quote_col}; "
                f"missing: {missing}. Available columns: {list(db_columns)}"
            )

    return base_col, quote_col


def resolve_symbol_mapping(
    symbol: str,
    db_columns: Optional[Sequence[str]] = None,
    *,
    allow_inferred_fx: bool = False,
) -> SymbolMapping:
    """Resolve a full SymbolMapping object with optional DB schema validation."""
    symbol_clean = normalize_symbol(symbol)
    base_col, quote_col = get_force_columns(
        symbol_clean,
        db_columns=db_columns,
        allow_inferred_fx=allow_inferred_fx,
    )
    return SymbolMapping(
        symbol=symbol_clean,
        base_asset=base_col.replace("force_", "").upper(),
        quote_asset=quote_col.replace("force_", "").upper(),
        base_column=base_col,
        quote_column=quote_col,
    )


def parse_symbols(raw: Optional[str], *, default: str = DEFAULT_SYMBOL) -> List[str]:
    """Parse CLI symbols like 'GBPUSD,EURUSD,USDJPY' into canonical unique list."""
    source = raw if raw not in (None, "") else default
    values: List[str] = []
    for part in str(source).split(","):
        part = part.strip()
        if not part:
            continue
        normalized = normalize_symbol(part)
        if normalized not in values:
            values.append(normalized)
    return values or [normalize_symbol(default)]


def get_table_columns(conn: sqlite3.Connection, table: str = DEFAULT_TABLE) -> List[str]:
    """Read SQLite table columns using PRAGMA table_info."""
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [str(row[1]) for row in rows]


def get_db_columns(db_path: str, table: str = DEFAULT_TABLE) -> List[str]:
    """Open a DB read-only and return table columns."""
    path = Path(db_path)
    if not path.exists():
        raise FileNotFoundError(f"DB not found: {db_path}")
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return get_table_columns(conn, table=table)
    finally:
        conn.close()


def validate_symbol_against_db(
    db_path: str,
    symbol: str,
    table: str = DEFAULT_TABLE,
) -> SymbolMapping:
    """Resolve mapping and validate required force columns against the DB."""
    columns = get_db_columns(db_path, table=table)
    return resolve_symbol_mapping(symbol, db_columns=columns)


def list_supported_symbols() -> List[str]:
    """Return supported PowerFlow symbols in stable order."""
    return sorted(SYMBOL_FORCE_MAP)


def build_force_select_sql(
    symbol: str,
    timeframe: int,
    db_columns: Sequence[str],
    *,
    table: str = DEFAULT_TABLE,
    limit: int = 100,
    order_desc: bool = True,
) -> Tuple[str, Tuple[object, ...], SymbolMapping]:
    """
    Build a safe force_snapshots SELECT for a symbol/timeframe.

    Column names are validated via SymbolMapper before interpolation. Values
    remain bound parameters.
    """
    mapping = resolve_symbol_mapping(symbol, db_columns=db_columns)
    has_symbol = "symbol" in db_columns
    has_timestamp = "timestamp" in db_columns

    where_parts = ["timeframe = ?"]
    params: List[object] = [int(timeframe)]
    if has_symbol:
        where_parts.insert(0, "symbol = ?")
        params.insert(0, mapping.symbol)

    order_col = "timestamp" if has_timestamp else "rowid"
    direction = "DESC" if order_desc else "ASC"
    sql = f"""
        SELECT {mapping.base_column}, {mapping.quote_column}, {order_col}
        FROM {table}
        WHERE {' AND '.join(where_parts)}
        ORDER BY {order_col} {direction}
        LIMIT {int(limit)}
    """
    return sql, tuple(params), mapping


class SymbolMapper:
    """Class facade for callers that prefer object-style access."""

    SYMBOL_FORCE_MAP = SYMBOL_FORCE_MAP

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        return normalize_symbol(symbol)

    @staticmethod
    def parse_symbols(raw: Optional[str], default: str = DEFAULT_SYMBOL) -> List[str]:
        return parse_symbols(raw, default=default)

    @staticmethod
    def get_force_columns(symbol: str, db_columns: Optional[Sequence[str]] = None) -> Tuple[str, str]:
        return get_force_columns(symbol, db_columns=db_columns)

    @staticmethod
    def resolve(symbol: str, db_columns: Optional[Sequence[str]] = None) -> SymbolMapping:
        return resolve_symbol_mapping(symbol, db_columns=db_columns)

    @staticmethod
    def validate_db(db_path: str, symbol: str, table: str = DEFAULT_TABLE) -> SymbolMapping:
        return validate_symbol_against_db(db_path, symbol, table=table)
