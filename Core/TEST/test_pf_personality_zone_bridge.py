#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V6 - test_pf_personality_zone_bridge.py

Mission:
    Validate the bridge:
        pf_personalities.py -> pf_zone_dynamics.py

Nature:
    - read-only
    - no DB write
    - no Telegram
    - no cockpit mutation
    - no TemporalWindowActive

Usage:
    python test_pf_personality_zone_bridge.py --db powerflow.db --symbol GBPUSD --tf 5 --bars 200 --lookback 20
    python test_pf_personality_zone_bridge.py --db powerflow.db --symbol GBPUSD --tf 1 --bars 300 --lookback 20 --verbose

Exit codes:
    0 = OK, at least one devise diagnosed
    1 = import / setup error
    2 = DB / data error
    3 = no valid z-series
    4 = zone analyzer error for all devises
"""

from __future__ import annotations

import argparse
import inspect
import math
import os
import sqlite3
import sys
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


# ---------------------------------------------------------------------
# Imports guarded: report clean errors instead of crashing silently.
# ---------------------------------------------------------------------

try:
    from pf_relations import get_relation_rows, get_available_devises
except Exception as exc:
    print(f"FATAL import pf_relations failed: {exc}")
    sys.exit(1)

try:
    import pf_personalities
except Exception as exc:
    print(f"FATAL import pf_personalities failed: {exc}")
    sys.exit(1)

try:
    import pf_zone_dynamics
except Exception as exc:
    print(f"FATAL import pf_zone_dynamics failed: {exc}")
    sys.exit(1)


# ---------------------------------------------------------------------
# Small utilities
# ---------------------------------------------------------------------

def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _safe_float(value: Any) -> Optional[float]:
    if _is_number(value):
        return float(value)
    try:
        if value is None:
            return None
        out = float(value)
        if math.isfinite(out):
            return out
    except Exception:
        return None
    return None


def _to_plain(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return value
    return value


def _first_attr_or_key(obj: Any, names: Sequence[str], default: Any = None) -> Any:
    if obj is None:
        return default

    plain = _to_plain(obj)

    if isinstance(plain, dict):
        for name in names:
            if name in plain:
                return plain.get(name)
        # case-insensitive fallback
        lower_map = {str(k).lower(): k for k in plain.keys()}
        for name in names:
            key = lower_map.get(name.lower())
            if key is not None:
                return plain.get(key)
        return default

    for name in names:
        if hasattr(obj, name):
            return getattr(obj, name)

    return default


def extract_numeric_z(raw: Any) -> Optional[float]:
    """
    Accepts:
      - float/int
      - dict/dataclass/object with common z-score fields
    """
    if _is_number(raw):
        return float(raw)

    candidate = _first_attr_or_key(
        raw,
        (
            "z",
            "z_score",
            "zscore",
            "z_current",
            "behavioral_z",
            "behavioral_index",
            "index",
            "score",
            "value",
        ),
        default=None,
    )
    return _safe_float(candidate)


def compact_type(value: Any) -> str:
    if value is None:
        return "None"
    if is_dataclass(value):
        return f"dataclass:{type(value).__name__}"
    return type(value).__name__


# ---------------------------------------------------------------------
# Flexible call adapters
# ---------------------------------------------------------------------

def get_behavioral_function():
    for name in ("behavioral_index", "compute_behavioral_index", "get_behavioral_index"):
        fn = getattr(pf_personalities, name, None)
        if callable(fn):
            return name, fn
    raise AttributeError("No behavioral_index-like function found in pf_personalities")


def get_zone_function():
    for name in ("analyze_zone_dynamics", "analyse_zone_dynamics", "detect_zone_dynamics"):
        fn = getattr(pf_zone_dynamics, name, None)
        if callable(fn):
            return name, fn
    raise AttributeError("No analyze_zone_dynamics-like function found in pf_zone_dynamics")


def call_behavioral_index(
    fn,
    devise: str,
    rows: Sequence[Any],
    index: int,
    devise_cols: Sequence[Any],
    lookback: int,
    symbol: str,
    tf: int,
) -> Any:
    """
    Attempts signature-aware call first.
    Falls back to common positional patterns.
    """
    sig = inspect.signature(fn)
    params = sig.parameters

    kwargs: Dict[str, Any] = {}

    aliases = {
        "devise": devise,
        "currency": devise,
        "cur": devise,
        "rows": rows,
        "data": rows,
        "i": index,
        "idx": index,
        "index": index,
        "bar_index": index,
        "devise_cols": devise_cols,
        "cols": devise_cols,
        "columns": devise_cols,
        "lookback": lookback,
        "window": lookback,
        "symbol": symbol,
        "tf": tf,
        "timeframe": tf,
    }

    for pname, param in params.items():
        if pname in aliases:
            kwargs[pname] = aliases[pname]

    # If we matched all required positional-or-keyword params, use kwargs.
    required = [
        name for name, p in params.items()
        if p.default is inspect._empty
        and p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
    ]

    if all(name in kwargs for name in required):
        return fn(**kwargs)

    # Fallback patterns.
    patterns = [
        (devise, rows, index, devise_cols, lookback),
        (devise, rows, index, devise_cols),
        (rows, index, devise, devise_cols, lookback),
        (rows, index, devise, devise_cols),
        (rows, index, devise, lookback),
    ]

    last_exc = None
    for args in patterns:
        try:
            return fn(*args)
        except TypeError as exc:
            last_exc = exc

    raise TypeError(f"Cannot call behavioral function {fn.__name__}: {last_exc}")


def call_zone_analyzer(
    fn,
    z_series: Sequence[float],
    devise: str,
    symbol: str,
    tf: int,
    lookback: int,
) -> Any:
    """
    Attempts signature-aware call first.
    Falls back to z_series-only call.
    """
    sig = inspect.signature(fn)
    params = sig.parameters

    aliases = {
        "z_series": z_series,
        "series": z_series,
        "values": z_series,
        "scores": z_series,
        "devise": devise,
        "currency": devise,
        "symbol": symbol,
        "tf": tf,
        "timeframe": tf,
        "lookback": lookback,
        "window": lookback,
    }

    kwargs: Dict[str, Any] = {}
    for pname in params.keys():
        if pname in aliases:
            kwargs[pname] = aliases[pname]

    required = [
        name for name, p in params.items()
        if p.default is inspect._empty
        and p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
    ]

    if all(name in kwargs for name in required):
        return fn(**kwargs)

    # fallback: most likely analyzer(z_series)
    try:
        return fn(z_series)
    except TypeError:
        pass

    # fallback: analyzer(z_series, devise)
    try:
        return fn(z_series, devise)
    except TypeError:
        pass

    # fallback: analyzer(z_series, devise, tf)
    return fn(z_series, devise, tf)


# ---------------------------------------------------------------------
# Diagnostics extraction
# ---------------------------------------------------------------------

def extract_diag_summary(diag: Any, z_series: Sequence[float]) -> Dict[str, Any]:
    z_current = _first_attr_or_key(diag, ("z_current", "current_z", "z", "last_z"), default=None)
    z_current = _safe_float(z_current)
    if z_current is None and z_series:
        z_current = float(z_series[-1])

    state = _first_attr_or_key(diag, ("state", "zone_state", "status", "phase"), default="UNKNOWN")

    bars_in_extreme = _first_attr_or_key(
        diag,
        ("bars_in_extreme", "extreme_bars", "bars_extreme", "duration_extreme"),
        default=0,
    )

    pullbacks = _first_attr_or_key(diag, ("pullbacks", "pullback_events"), default=[])
    if pullbacks is None:
        pullbacks = []
    if not isinstance(pullbacks, list):
        try:
            pullbacks = list(pullbacks)
        except Exception:
            pullbacks = []

    absorbed_count = 0
    for p in pullbacks:
        absorbed = _first_attr_or_key(p, ("absorbed", "is_absorbed"), default=False)
        if bool(absorbed):
            absorbed_count += 1

    tension_score = _first_attr_or_key(
        diag,
        ("tension_score", "tension", "pressure_score", "score"),
        default=None,
    )
    tension_score = _safe_float(tension_score)

    note = _first_attr_or_key(diag, ("note", "message", "comment", "diagnostic"), default="")

    return {
        "z_current": z_current,
        "state": str(state),
        "bars_in_extreme": bars_in_extreme,
        "pullbacks_count": len(pullbacks),
        "absorbed_pullbacks": absorbed_count,
        "tension_score": tension_score,
        "note": str(note),
        "diag_type": compact_type(diag),
    }


def print_diag(devise: str, summary: Dict[str, Any]) -> None:
    z_current = summary.get("z_current")
    tension = summary.get("tension_score")

    z_txt = "NA" if z_current is None else f"{z_current:+.3f}"
    tension_txt = "NA" if tension is None else f"{tension:.3f}"

    print("")
    print(f">>> {devise.upper()} <<<")
    print(f"Z actuel        : {z_txt}")
    print(f"Etat            : {summary.get('state')}")
    print(f"Barres extreme  : {summary.get('bars_in_extreme')}")
    print(
        f"Pullbacks       : {summary.get('pullbacks_count')} "
        f"({summary.get('absorbed_pullbacks')} absorbes)"
    )
    print(f"Tension score   : {tension_txt}")
    print(f"Diag type       : {summary.get('diag_type')}")
    note = summary.get("note")
    if note:
        print(f"Note            : {note}")


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PowerFlow V6 - test bridge pf_personalities -> pf_zone_dynamics"
    )
    parser.add_argument("--db", default="powerflow.db", help="SQLite DB path")
    parser.add_argument("--symbol", default="GBPUSD", help="Symbol, e.g. GBPUSD")
    parser.add_argument("--tf", type=int, default=5, help="Timeframe in minutes")
    parser.add_argument("--bars", type=int, default=200, help="Number of rows to load")
    parser.add_argument("--lookback", type=int, default=20, help="Behavioral lookback")
    parser.add_argument("--devise", default="", help="Optional single devise, e.g. gbp")
    parser.add_argument("--verbose", action="store_true", help="Verbose debug output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    print("=" * 78)
    print("PowerFlow V6 - Personality -> Zone Bridge Test")
    print("=" * 78)
    print(f"DB       : {args.db}")
    print(f"Symbol   : {args.symbol.upper()}")
    print(f"TF       : M{args.tf}")
    print(f"Bars     : {args.bars}")
    print(f"Lookback : {args.lookback}")
    print("=" * 78)

    if not os.path.exists(args.db):
        print(f"FATAL DB not found: {args.db}")
        return 2

    try:
        b_name, behavioral_fn = get_behavioral_function()
        z_name, zone_fn = get_zone_function()
    except Exception as exc:
        print(f"FATAL function discovery failed: {exc}")
        return 1

    print(f"Behavioral function : pf_personalities.{b_name}{inspect.signature(behavioral_fn)}")
    print(f"Zone function       : pf_zone_dynamics.{z_name}{inspect.signature(zone_fn)}")

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    try:
        devises = get_available_devises(conn)
        if args.devise:
            selected = args.devise.lower().strip()
            devises = [d for d in devises if d.lower() == selected]
            if not devises:
                print(f"FATAL devise not available: {selected}")
                return 2

        rows, devise_cols = get_relation_rows(
            conn,
            args.symbol.upper(),
            args.tf,
            None,
            args.bars,
            devises,
        )

    except Exception as exc:
        print(f"FATAL DB/data loading failed: {exc}")
        return 2
    finally:
        conn.close()

    print(f"Available devises : {', '.join([d.upper() for d in devises])}")
    print(f"Rows loaded       : {len(rows)}")

    if len(rows) < max(3, args.lookback + 1):
        print("FATAL not enough rows for bridge test")
        return 2

    ok_z = 0
    ok_diag = 0
    failures: List[Tuple[str, str]] = []

    for devise in devises:
        z_series: List[float] = []
        raw_samples: List[str] = []

        for i in range(len(rows)):
            try:
                raw = call_behavioral_index(
                    behavioral_fn,
                    devise=devise,
                    rows=rows,
                    index=i,
                    devise_cols=devise_cols,
                    lookback=args.lookback,
                    symbol=args.symbol.upper(),
                    tf=args.tf,
                )
                if args.verbose and len(raw_samples) < 3:
                    raw_samples.append(compact_type(raw))

                z = extract_numeric_z(raw)
                if z is not None:
                    z_series.append(z)
            except Exception as exc:
                # Beginning of series can fail if lookback is not enough.
                if i >= args.lookback:
                    failures.append((devise, f"behavioral_index at i={i}: {exc}"))
                    break

        if args.verbose:
            print(f"[DEBUG] {devise.upper()} raw sample types: {raw_samples}")

        if not z_series:
            failures.append((devise, "no valid z_series"))
            continue

        ok_z += 1

        try:
            diag = call_zone_analyzer(
                zone_fn,
                z_series=z_series,
                devise=devise,
                symbol=args.symbol.upper(),
                tf=args.tf,
                lookback=args.lookback,
            )
            summary = extract_diag_summary(diag, z_series)
            print_diag(devise, summary)
            ok_diag += 1
        except Exception as exc:
            failures.append((devise, f"zone analyzer failed: {exc}"))

    print("")
    print("=" * 78)
    print("BRIDGE TEST SUMMARY")
    print("=" * 78)
    print(f"Devises tested       : {len(devises)}")
    print(f"Z-series OK          : {ok_z}")
    print(f"Zone diagnostics OK  : {ok_diag}")
    print(f"Failures             : {len(failures)}")

    if failures:
        print("")
        print("FAILURES:")
        for devise, msg in failures[:20]:
            print(f"- {devise.upper()}: {msg}")

    if ok_z == 0:
        print("")
        print("VERDICT: FAIL - no valid z-series")
        return 3

    if ok_diag == 0:
        print("")
        print("VERDICT: FAIL - no zone diagnostic produced")
        return 4

    print("")
    print("VERDICT: OK - Personality feeds Zone Dynamics")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
