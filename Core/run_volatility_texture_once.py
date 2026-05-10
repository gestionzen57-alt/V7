"""run_volatility_texture_once.py — One-shot B7+ Volatility Texture runner."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from pf_volatility_texture import ENGINE_VERSION, VolatilityTextureEngine

RUNNER_VERSION = "VolatilityTextureRunnerV0.1Standalone"


CURRENCY_CODES = {"EUR", "GBP", "USD", "JPY", "CHF", "CAD", "AUD", "NZD", "XAU"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def project_root() -> Path:
    cwd = Path.cwd().resolve()
    if cwd.name.lower() == "core":
        return cwd.parent
    return cwd


def resolve_path(path_value: str, prefer_core: bool = False) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    root = project_root()
    cwd = Path.cwd().resolve()
    candidates = []
    if prefer_core:
        candidates.extend([cwd / path, root / "Core" / path, root / path])
    else:
        candidates.extend([root / path, cwd / path])
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return candidates[0].resolve()


def resolve_output_path(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    root = project_root()
    return (root / path).resolve()


def connect_readonly(db_path: Path) -> sqlite3.Connection:
    uri = f"file:{db_path.as_posix()}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def table_columns(conn: sqlite3.Connection, table: str = "force_snapshots") -> List[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [str(row[1]) for row in rows]


def normalize_name(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalnum())


def find_first_column(columns: Sequence[str], candidates: Sequence[str]) -> Optional[str]:
    normalized = {normalize_name(col): col for col in columns}
    for candidate in candidates:
        key = normalize_name(candidate)
        if key in normalized:
            return normalized[key]
    return None


def split_symbol(symbol: str) -> Tuple[str, str]:
    cleaned = "".join(ch for ch in symbol.upper() if ch.isalpha())
    if len(cleaned) >= 6:
        return cleaned[:3], cleaned[3:6]
    return "GBP", "USD"


def currency_column_candidates(currency: str) -> List[str]:
    c = currency.upper()
    l = c.lower()
    return [
        c,
        l,
        f"force_{l}",
        f"force_{c}",
        f"{l}_force",
        f"{c}_force",
        f"zscore_{l}",
        f"z_score_{l}",
        f"{l}_zscore",
        f"score_{l}",
        f"{l}_score",
        f"strength_{l}",
        f"{l}_strength",
    ]


def pair_column_candidates(symbol: str) -> List[str]:
    s = "".join(ch for ch in symbol.upper() if ch.isalnum())
    l = s.lower()
    return [
        s,
        l,
        f"force_{l}",
        f"force_{s}",
        f"{l}_force",
        f"{s}_force",
        f"price_{l}",
        f"close_{l}",
        "close",
        "price",
        "value",
        "force",
    ]


def spread_column_candidates(symbol: str) -> List[str]:
    s = "".join(ch for ch in symbol.upper() if ch.isalnum())
    l = s.lower()
    return [
        f"spread_{l}",
        f"{l}_spread",
        "spread",
        "spread_pips",
        "bid_ask_spread",
        "ask_bid_spread",
    ]


def load_force_and_spread_data(
    db_path: Path,
    symbol: str,
    timeframe: int,
    recent_bars: int,
) -> Tuple[np.ndarray, Optional[np.ndarray], Dict[str, Any]]:
    conn = connect_readonly(db_path)
    try:
        columns = table_columns(conn, "force_snapshots")
        timestamp_col = find_first_column(columns, ["timestamp", "time", "datetime", "ts", "created_at"])
        timeframe_col = find_first_column(columns, ["timeframe", "tf", "period", "time_frame"])
        if not timestamp_col or not timeframe_col:
            raise RuntimeError(
                "force_snapshots must expose timestamp/timeframe columns; "
                f"available_columns={columns}"
            )

        base, quote = split_symbol(symbol)
        base_col = find_first_column(columns, currency_column_candidates(base))
        quote_col = find_first_column(columns, currency_column_candidates(quote))
        pair_col = find_first_column(columns, pair_column_candidates(symbol))
        spread_col = find_first_column(columns, spread_column_candidates(symbol))

        select_cols: List[str] = [timestamp_col, timeframe_col]
        mode = None
        if base_col and quote_col:
            select_cols.extend([base_col, quote_col])
            mode = "currency_difference"
        elif pair_col:
            select_cols.append(pair_col)
            mode = "pair_column"
        else:
            raise RuntimeError(
                "No force columns found for symbol; "
                f"symbol={symbol}, base={base}, quote={quote}, available_columns={columns}"
            )
        if spread_col:
            select_cols.append(spread_col)

        quoted_cols = ", ".join([f'"{col}"' for col in select_cols])
        query = (
            f'SELECT {quoted_cols} FROM force_snapshots '
            f'WHERE "{timeframe_col}" = ? '
            f'ORDER BY "{timestamp_col}" DESC LIMIT ?'
        )
        rows = conn.execute(query, (int(timeframe), int(recent_bars))).fetchall()
        rows = list(reversed(rows))
        if not rows:
            return np.asarray([], dtype=float), None, {
                "db_path": str(db_path),
                "symbol": symbol,
                "timeframe": timeframe,
                "rows": 0,
                "available_columns": columns,
                "mode": mode,
            }

        force_values: List[float] = []
        spread_values: List[float] = []
        for row in rows:
            if mode == "currency_difference":
                base_value = float(row[2])
                quote_value = float(row[3])
                force_values.append(base_value - quote_value)
                spread_index = 4
            else:
                force_values.append(float(row[2]))
                spread_index = 3
            if spread_col and len(row) > spread_index and row[spread_index] is not None:
                try:
                    spread_values.append(float(row[spread_index]))
                except (TypeError, ValueError):
                    pass

        metadata = {
            "db_path": str(db_path),
            "symbol": symbol,
            "timeframe": timeframe,
            "rows": len(rows),
            "first_timestamp": rows[0][0],
            "last_timestamp": rows[-1][0],
            "available_columns": columns,
            "timestamp_column": timestamp_col,
            "timeframe_column": timeframe_col,
            "base_column": base_col,
            "quote_column": quote_col,
            "pair_column": pair_col,
            "spread_column": spread_col,
            "mode": mode,
        }
        spread = np.asarray(spread_values, dtype=float) if spread_values else None
        return np.asarray(force_values, dtype=float), spread, metadata
    finally:
        conn.close()


def fallback_session_context() -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    hour = now.hour + now.minute / 60.0
    if 12 <= hour < 16:
        session = "OVERLAP"
        phase = "MAX_VELOCITY_BATTLEFIELD"
    elif 7 <= hour < 12:
        session = "LONDON"
        phase = "IGNITION" if hour < 8 else "MID_SESSION"
    elif 16 <= hour < 21:
        session = "NY"
        phase = "MID_SESSION"
    else:
        session = "ASIAN"
        phase = "IGNITION" if 22 <= hour or hour < 1 else "MID_SESSION"
    return {
        "session": session,
        "phase": phase,
        "source": "fallback_runner_clock",
        "timestamp": utc_now_iso(),
    }


def load_session_context() -> Dict[str, Any]:
    try:
        from pf_session_overlay import SessionContextProvider  # type: ignore

        provider = SessionContextProvider()
        for method_name in ["get_current_session_context", "current_context", "get_context"]:
            method = getattr(provider, method_name, None)
            if callable(method):
                ctx = method()
                if isinstance(ctx, dict):
                    ctx.setdefault("source", "pf_session_overlay")
                    return ctx
    except Exception:
        pass
    return fallback_session_context()


def build_error_result(
    error: str,
    db_path: Path,
    output_path: Path,
    technical_risks: Optional[List[str]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "timestamp": utc_now_iso(),
        "runner_version": RUNNER_VERSION,
        "engine_version": ENGINE_VERSION,
        "db_path": str(db_path),
        "output_path": str(output_path),
        "valid": False,
        "error": error,
        "technical_risks": technical_risks or ["VOLATILITY_TEXTURE_RUNTIME_ERROR"],
    }
    if extra:
        result.update(extra)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run B7+ Volatility Texture one-shot analysis.")
    parser.add_argument("--db", required=True, help="Path to powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--timeframe", type=int, default=1)
    parser.add_argument("--recent-bars", type=int, default=100)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--output", default="output/volatility_texture.json")
    parser.add_argument("--session", default=None, help="Optional session override")
    parser.add_argument("--phase", default=None, help="Optional session phase override")
    args = parser.parse_args()

    db_path = resolve_path(args.db, prefer_core=True)
    output_path = resolve_output_path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        force_series, spread_series, source = load_force_and_spread_data(
            db_path=db_path,
            symbol=args.symbol,
            timeframe=args.timeframe,
            recent_bars=args.recent_bars,
        )
        session_ctx = load_session_context()
        if args.session:
            session_ctx["session"] = args.session.upper()
            session_ctx["source"] = "cli_override"
        if args.phase:
            session_ctx["phase"] = args.phase.upper()
            session_ctx["source"] = "cli_override"

        engine = VolatilityTextureEngine(window_micro=5, window_macro=20)
        result = engine.analyze_texture(
            force_series=force_series,
            spread_series=spread_series,
            session_context=session_ctx,
            symbol=args.symbol,
            timeframe=args.timeframe,
        )
        result.update(
            {
                "runner_version": RUNNER_VERSION,
                "db_path": str(db_path),
                "output_path": str(output_path),
                "source": source,
                "recent_bars_requested": args.recent_bars,
            }
        )
    except Exception as exc:
        result = build_error_result(
            error=str(exc),
            db_path=db_path,
            output_path=output_path,
            technical_risks=["VOLATILITY_TEXTURE_RUNTIME_ERROR"],
        )

    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2 if args.pretty else None, ensure_ascii=False)

    print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False))
    if not result.get("valid"):
        sys.exit(1)


if __name__ == "__main__":
    main()
