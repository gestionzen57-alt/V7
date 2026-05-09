#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PowerFlow V6 — Engine Orchestrator Directionnel

Consomme pf_bipolar_node_alert.py version LONG/SHORT.

Validation globale:
SIGNAL_VALIDATED_LONG ou SIGNAL_VALIDATED_SHORT uniquement si:

1. Au moins un TF lourd M15/M30/M60 est en PRE_ALERT_LONG ou PRE_ALERT_SHORT
2. Au moins un TF tactique M1/M5 est en ALERT_LONG ou ALERT_SHORT
3. Le sens lourd et le sens tactique sont identiques

Exemple:
M60 PRE_ALERT_SHORT + M30 PRE_ALERT_SHORT + M5 ALERT_SHORT
=> SIGNAL_VALIDATED_SHORT
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


# ============================================================
# CONSTANTES
# ============================================================

DEFAULT_DB_PATH = "db/powerflow.db"
DEFAULT_SYMBOL = "GBPUSD"

DEFAULT_BASE = None
DEFAULT_QUOTE = None

HEAVY_TFS = (15, 30, 60)
TACTICAL_TFS = (1, 5)
SCAN_TFS = (1, 5, 15, 30, 60)

ROWS_TO_LOAD = 220

OUTPUT_STATE_FILE = "output/pf_engine_orchestrator_state.json"

CURRENCIES = ("gbp", "usd", "eur", "jpy", "cad", "chf", "aud", "nzd")


# ============================================================
# IMPORT SCANNER DIRECTIONNEL
# ============================================================

try:
    from pf_bipolar_node_alert import (
        analyze_tf,
        get_available_timeframes,
        load_snapshots_for_tf,
        pair_label,
    )
except Exception as exc:
    raise RuntimeError(
        "Impossible d'importer pf_bipolar_node_alert.py. "
        "Place pf_engine_orchestrator.py dans le même dossier."
    ) from exc


# ============================================================
# DATA
# ============================================================

@dataclass
class TfSignal:
    tf: int
    symbol: str
    verdict: str
    direction: str
    reason: str
    last_time: str

    base: str
    quote: str
    base_force: float
    quote_force: float

    base_z: float
    quote_z: float
    spread_z: float

    spread: float
    gap_abs: float
    delta_3: float
    delta_5: float

    score_long: float
    score_short: float

    long_tension: bool
    short_tension: bool
    long_thrust: bool
    short_thrust: bool
    long_cross: bool
    short_cross: bool
    quasi_cross: bool
    center_reentry: bool
    compression: bool
    liquidity_absorbed_long: bool
    liquidity_absorbed_short: bool


@dataclass
class OrchestratorResult:
    signal_status: str
    global_verdict: str
    direction: str
    reason: str

    symbol: str
    base: str
    quote: str

    heavy_tfs: List[int]
    tactical_tfs: List[int]

    heavy_pre_alerts: List[TfSignal]
    tactical_alerts: List[TfSignal]
    all_tf_signals: List[TfSignal]

    created_at_epoch: float


# ============================================================
# CONVERSION REPORT SCANNER -> SIGNAL ORCHESTRATOR
# ============================================================

def tf_report_to_signal(report) -> TfSignal:
    return TfSignal(
        tf=int(report.tf),
        symbol=str(report.symbol),
        verdict=str(report.verdict),
        direction=str(report.direction),
        reason=str(report.reason),
        last_time=str(report.last_time),

        base=str(report.base),
        quote=str(report.quote),
        base_force=float(report.base_force),
        quote_force=float(report.quote_force),

        base_z=float(report.base_z_now),
        quote_z=float(report.quote_z_now),
        spread_z=float(report.spread_z_now),

        spread=float(report.pair_spread_now),
        gap_abs=float(report.gap_abs_now),
        delta_3=float(report.pair_spread_delta_3),
        delta_5=float(report.pair_spread_delta_5),

        score_long=float(report.score_long),
        score_short=float(report.score_short),

        long_tension=bool(report.long_tension),
        short_tension=bool(report.short_tension),
        long_thrust=bool(report.long_thrust),
        short_thrust=bool(report.short_thrust),
        long_cross=bool(report.long_cross),
        short_cross=bool(report.short_cross),
        quasi_cross=bool(report.quasi_cross),
        center_reentry=bool(report.center_reentry),
        compression=bool(report.compression),
        liquidity_absorbed_long=bool(report.liquidity_absorbed_long),
        liquidity_absorbed_short=bool(report.liquidity_absorbed_short),
    )


# ============================================================
# SCAN MULTI-TF
# ============================================================

def resolve_tfs(
    db_path: str,
    symbol: str,
    requested_tfs: Optional[Sequence[int]],
) -> List[int]:
    available = set(get_available_timeframes(db_path, symbol))

    if requested_tfs:
        return [tf for tf in requested_tfs if tf in available]

    return [tf for tf in SCAN_TFS if tf in available]


def scan_all_tfs(
    db_path: str,
    symbol: str,
    base: str,
    quote: str,
    tfs: Sequence[int],
    rows: int,
) -> List[TfSignal]:
    signals: List[TfSignal] = []

    for tf in tfs:
        snapshots = load_snapshots_for_tf(
            db_path=db_path,
            symbol=symbol,
            timeframe=tf,
            base=base,
            quote=quote,
            limit=rows,
        )

        report = analyze_tf(
            snapshots=snapshots,
            symbol=symbol,
            tf=tf,
            base=base,
            quote=quote,
        )

        signals.append(tf_report_to_signal(report))

    return signals


# ============================================================
# ORCHESTRATION FRACTALE DIRECTIONNELLE
# ============================================================

def is_heavy_pre_alert(signal: TfSignal, direction: str) -> bool:
    return (
        signal.tf in HEAVY_TFS
        and signal.direction == direction
        and signal.verdict == f"PRE_ALERT_{direction}"
    )


def is_tactical_alert(signal: TfSignal, direction: str) -> bool:
    return (
        signal.tf in TACTICAL_TFS
        and signal.direction == direction
        and signal.verdict == f"ALERT_{direction}"
    )


def orchestrate(
    signals: Sequence[TfSignal],
    symbol: str,
    base: str,
    quote: str,
) -> OrchestratorResult:
    validated_direction = "NONE"
    selected_heavy: List[TfSignal] = []
    selected_tactical: List[TfSignal] = []

    for direction in ("SHORT", "LONG"):
        heavy = [s for s in signals if is_heavy_pre_alert(s, direction)]
        tactical = [s for s in signals if is_tactical_alert(s, direction)]

        if heavy and tactical:
            validated_direction = direction
            selected_heavy = heavy
            selected_tactical = tactical
            break

    if validated_direction != "NONE":
        signal_status = "SIGNAL_VALIDATED"
        global_verdict = f"SIGNAL_VALIDATED_{validated_direction}"
        reason = (
            f"gravité {validated_direction} chargée sur TF lourd "
            f"{[f'M{s.tf}' for s in selected_heavy]} "
            f"+ déclenchement tactique "
            f"{[f'M{s.tf}' for s in selected_tactical]}"
        )
    else:
        signal_status = "NO_GLOBAL_ALERT"
        global_verdict = "NO_GLOBAL_ALERT"
        reason = build_rejection_reason(signals)

    return OrchestratorResult(
        signal_status=signal_status,
        global_verdict=global_verdict,
        direction=validated_direction,
        reason=reason,
        symbol=symbol.upper(),
        base=base.upper(),
        quote=quote.upper(),
        heavy_tfs=list(HEAVY_TFS),
        tactical_tfs=list(TACTICAL_TFS),
        heavy_pre_alerts=selected_heavy,
        tactical_alerts=selected_tactical,
        all_tf_signals=list(signals),
        created_at_epoch=time.time(),
    )


def build_rejection_reason(signals: Sequence[TfSignal]) -> str:
    heavy_long = [s.tf for s in signals if s.tf in HEAVY_TFS and s.verdict == "PRE_ALERT_LONG"]
    heavy_short = [s.tf for s in signals if s.tf in HEAVY_TFS and s.verdict == "PRE_ALERT_SHORT"]

    tactical_long = [s.tf for s in signals if s.tf in TACTICAL_TFS and s.verdict == "ALERT_LONG"]
    tactical_short = [s.tf for s in signals if s.tf in TACTICAL_TFS and s.verdict == "ALERT_SHORT"]

    if heavy_long and tactical_short:
        return (
            f"conflit directionnel: gravité LONG {heavy_long} "
            f"mais tactique SHORT {tactical_short}"
        )

    if heavy_short and tactical_long:
        return (
            f"conflit directionnel: gravité SHORT {heavy_short} "
            f"mais tactique LONG {tactical_long}"
        )

    if heavy_long and not tactical_long:
        return f"gravité LONG présente {heavy_long}, mais aucun ALERT_LONG tactique"

    if heavy_short and not tactical_short:
        return f"gravité SHORT présente {heavy_short}, mais aucun ALERT_SHORT tactique"

    if tactical_long and not heavy_long:
        return f"ALERT_LONG tactique {tactical_long}, mais aucun PRE_ALERT_LONG lourd"

    if tactical_short and not heavy_short:
        return f"ALERT_SHORT tactique {tactical_short}, mais aucun PRE_ALERT_SHORT lourd"

    return "aucune confluence fractale lourd + tactique"


# ============================================================
# OUTPUT
# ============================================================

def write_state(path: str, result: OrchestratorResult) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    payload = asdict(result)

    p.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def flag(value: bool) -> str:
    return "Y" if value else "N"


def print_tf_line(s: TfSignal) -> None:
    print(
        f"[M{s.tf:<3}] "
        f"{s.verdict:<16} "
        f"dir={s.direction:<5} "
        f"{s.symbol:<6} "
        f"{s.base}/{s.quote} | "
        f"Z({s.base})={s.base_z:>6.2f} "
        f"Z({s.quote})={s.quote_z:>6.2f} "
        f"spreadZ={s.spread_z:>6.2f} | "
        f"spread={s.spread:>7.2f} "
        f"|gap|={s.gap_abs:>6.2f} "
        f"d3={s.delta_3:>7.2f} "
        f"d5={s.delta_5:>7.2f} | "
        f"scoreL={s.score_long:>5.2f} "
        f"scoreS={s.score_short:>5.2f} | "
        f"{s.reason}"
    )


def print_result(result: OrchestratorResult, verbose: bool) -> None:
    print("")
    print("=" * 170)
    print(
        f"POWERFLOW V6 ORCHESTRATOR DIRECTIONNEL | "
        f"{pair_label(result.symbol)} | "
        f"base={result.base} quote={result.quote}"
    )
    print("=" * 170)

    for signal in result.all_tf_signals:
        print_tf_line(signal)

        if verbose:
            print(
                "    flags:",
                f"LONG_tension={flag(signal.long_tension)}",
                f"SHORT_tension={flag(signal.short_tension)}",
                f"LONG_thrust={flag(signal.long_thrust)}",
                f"SHORT_thrust={flag(signal.short_thrust)}",
                f"LONG_cross={flag(signal.long_cross)}",
                f"SHORT_cross={flag(signal.short_cross)}",
                f"quasi_cross={flag(signal.quasi_cross)}",
                f"center={flag(signal.center_reentry)}",
                f"compression={flag(signal.compression)}",
                f"liq_LONG={flag(signal.liquidity_absorbed_long)}",
                f"liq_SHORT={flag(signal.liquidity_absorbed_short)}",
            )

    print("-" * 170)
    print(f"GLOBAL VERDICT : {result.global_verdict}")
    print(f"STATUS         : {result.signal_status}")
    print(f"DIRECTION      : {result.direction}")
    print(f"RAISON         : {result.reason}")

    if result.signal_status == "SIGNAL_VALIDATED":
        print("")
        print(f"⚡ {result.global_verdict}")
        print(f"Gravité      : {[f'M{s.tf}' for s in result.heavy_pre_alerts]}")
        print(f"Déclencheur  : {[f'M{s.tf}' for s in result.tactical_alerts]}")

    print("=" * 170)
    print("")


# ============================================================
# CLI
# ============================================================

def parse_tfs(raw: Optional[str]) -> Optional[List[int]]:
    if raw is None or raw.strip() == "":
        return None

    out: List[int] = []

    for part in raw.split(","):
        part = part.strip()
        if part:
            out.append(int(part))

    return out


def derive_base_quote(
    symbol: str,
    base: Optional[str],
    quote: Optional[str],
    actor: Optional[str],
    adverse: Optional[str],
) -> Tuple[str, str]:
    b = base or actor
    q = quote or adverse

    if b and q:
        return b.upper(), q.upper()

    s = symbol.upper()

    if len(s) != 6:
        raise SystemExit(
            "Impossible de dériver base/quote depuis le symbole. "
            "Utilise --base XXX --quote YYY."
        )

    return s[:3], s[3:]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="PowerFlow V6 Engine Orchestrator Directionnel"
    )

    p.add_argument("--db", default=DEFAULT_DB_PATH)
    p.add_argument("--symbol", default=DEFAULT_SYMBOL)

    p.add_argument("--base", default=DEFAULT_BASE)
    p.add_argument("--quote", default=DEFAULT_QUOTE)

    # Compatibilité anciens appels
    p.add_argument("--actor", default=None, help="Alias de --base")
    p.add_argument("--adverse", default=None, help="Alias de --quote")

    p.add_argument(
        "--tfs",
        default=None,
        help="TF à scanner, ex: 1,5,15,30,60",
    )

    p.add_argument("--rows", type=int, default=ROWS_TO_LOAD)
    p.add_argument("--state-file", default=OUTPUT_STATE_FILE)
    p.add_argument("--no-state", action="store_true")
    p.add_argument("--verbose", action="store_true")

    p.add_argument("--loop", action="store_true")
    p.add_argument("--sleep", type=float, default=6.0)

    return p.parse_args()


def run_once(args: argparse.Namespace) -> OrchestratorResult:
    base, quote = derive_base_quote(
        symbol=args.symbol,
        base=args.base,
        quote=args.quote,
        actor=args.actor,
        adverse=args.adverse,
    )

    if base.lower() not in CURRENCIES:
        raise SystemExit(f"Base invalide: {base}")

    if quote.lower() not in CURRENCIES:
        raise SystemExit(f"Quote invalide: {quote}")

    tfs = resolve_tfs(
        db_path=args.db,
        symbol=args.symbol,
        requested_tfs=parse_tfs(args.tfs),
    )

    signals = scan_all_tfs(
        db_path=args.db,
        symbol=args.symbol,
        base=base,
        quote=quote,
        tfs=tfs,
        rows=args.rows,
    )

    result = orchestrate(
        signals=signals,
        symbol=args.symbol,
        base=base,
        quote=quote,
    )

    print_result(result, verbose=args.verbose)

    if not args.no_state:
        write_state(args.state_file, result)

    return result


def main() -> None:
    args = parse_args()

    if args.loop:
        while True:
            try:
                run_once(args)
            except Exception as exc:
                print(f"ERROR | {type(exc).__name__}: {exc}")
            time.sleep(args.sleep)
    else:
        run_once(args)


if __name__ == "__main__":
    main()