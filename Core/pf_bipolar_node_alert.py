#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PowerFlow V6 — Bipolar Node Debug Multi-TF Directionnel

Correction majeure:
- Détection dans les DEUX SENS.
- Plus de biais "acteur doit rebondir".
- Pour GBPUSD:
    LONG  = GBP domine USD => spread GBP-USD monte / positif
    SHORT = USD domine GBP => spread GBP-USD plonge / négatif

Sorties locales:
- NO_ALERT
- PRE_ALERT_LONG
- PRE_ALERT_SHORT
- ALERT_LONG
- ALERT_SHORT

Aucun Telegram.
SQLite local read-only.
"""

from __future__ import annotations

import argparse
import math
import sqlite3
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


# ============================================================
# SEUILS POWERFLOW V6 — CALIBRAGE FACILE
# ============================================================

DEFAULT_DB_PATH = "db/powerflow.db"
DEFAULT_SYMBOL = "GBPUSD"

# Si non fournis, base/quote sont dérivés du symbole.
DEFAULT_BASE = None
DEFAULT_QUOTE = None

DEFAULT_TFS = [1, 5, 15, 30, 60]

ROWS_TO_LOAD = 220
Z_LOOKBACK = 60
MIN_ROWS_FOR_Z = 25
TENSION_WINDOW = 45

# Tension directionnelle
Z_DOMINANT = 1.50
Z_EXTREME = 2.10

# Mouvement directionnel du spread base - quote
MIN_THRUST_DELTA_3 = 3.0
MIN_THRUST_DELTA_5 = 5.0

# Compression / absorption
MIN_GAP_COMPRESSION = 4.0
LIQUIDITY_Z_REBOUND = 0.60

# Quasi-cross autour de 0 du spread base-quote
QUASI_CROSS_DISTANCE = 7.0

# Zone centrale des forces brutes
CENTER_LEVEL = 50.0
CENTER_BAND = 18.0

# Scores
PRE_ALERT_SCORE = 3.4
ALERT_SCORE = 4.6

CURRENCIES = ("gbp", "usd", "eur", "jpy", "cad", "chf", "aud", "nzd")


# ============================================================
# DATA
# ============================================================

@dataclass
class Snapshot:
    created_at: str
    symbol: str
    timeframe: int
    forces: Dict[str, float]
    price: Optional[float] = None
    market_spread: Optional[float] = None


@dataclass
class TfReport:
    tf: int
    rows: int
    symbol: str
    base: str
    quote: str
    last_time: str

    base_force: float
    quote_force: float

    pair_spread_now: float
    pair_spread_prev: float
    pair_spread_delta_1: float
    pair_spread_delta_3: float
    pair_spread_delta_5: float

    base_z_now: float
    quote_z_now: float
    spread_z_now: float

    min_spread_z_window: float
    max_spread_z_window: float

    gap_abs_now: float
    gap_abs_prev: float
    gap_compression: float

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

    direction: str
    score_long: float
    score_short: float
    verdict: str
    reason: str


# ============================================================
# SQLITE
# ============================================================

def connect_readonly(db_path: str) -> sqlite3.Connection:
    path = Path(db_path).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"DB introuvable: {path}")

    uri = f"file:{path.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=2.0)
    conn.row_factory = sqlite3.Row
    return conn


def table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [r["name"] for r in rows]


def detect_time_column(cols: Sequence[str]) -> str:
    for col in ("created_at", "bar_time", "timestamp", "time"):
        if col in cols:
            return col
    raise RuntimeError("Aucune colonne temps trouvée dans force_snapshots.")


def force_col(currency: str) -> str:
    return f"force_{currency.lower()}"


def get_available_timeframes(db_path: str, symbol: str) -> List[int]:
    conn = connect_readonly(db_path)
    try:
        rows = conn.execute(
            """
            SELECT DISTINCT timeframe
            FROM force_snapshots
            WHERE symbol = ?
            ORDER BY timeframe ASC
            """,
            (symbol.upper(),),
        ).fetchall()

        return [int(r["timeframe"]) for r in rows if r["timeframe"] is not None]
    finally:
        conn.close()


def load_snapshots_for_tf(
    db_path: str,
    symbol: str,
    timeframe: int,
    base: str,
    quote: str,
    limit: int,
) -> List[Snapshot]:
    base = base.lower()
    quote = quote.lower()

    conn = connect_readonly(db_path)

    try:
        cols = table_columns(conn, "force_snapshots")
        time_col = detect_time_column(cols)

        required = [
            time_col,
            "symbol",
            "timeframe",
            force_col(base),
            force_col(quote),
        ]

        missing = [c for c in required if c not in cols]
        if missing:
            raise RuntimeError(f"Colonnes manquantes dans force_snapshots: {missing}")

        select_cols = [time_col, "symbol", "timeframe"]

        for cur in CURRENCIES:
            c = force_col(cur)
            if c in cols:
                select_cols.append(c)

        price_col = None
        if "price" in cols:
            price_col = "price"
        elif "bid" in cols:
            price_col = "bid"

        if price_col:
            select_cols.append(price_col)

        if "spread" in cols:
            select_cols.append("spread")

        sql = f"""
            SELECT {", ".join(select_cols)}
            FROM force_snapshots
            WHERE symbol = ?
              AND timeframe = ?
            ORDER BY {time_col} DESC
            LIMIT ?
        """

        rows = conn.execute(sql, (symbol.upper(), timeframe, limit)).fetchall()
        rows = list(reversed(rows))

        out: List[Snapshot] = []

        for r in rows:
            forces: Dict[str, float] = {}

            for cur in CURRENCIES:
                c = force_col(cur)
                if c in r.keys() and r[c] is not None:
                    forces[cur] = float(r[c])

            price = None
            if price_col and price_col in r.keys() and r[price_col] is not None:
                price = float(r[price_col])

            market_spread = None
            if "spread" in r.keys() and r["spread"] is not None:
                market_spread = float(r["spread"])

            out.append(
                Snapshot(
                    created_at=str(r[time_col]),
                    symbol=str(r["symbol"]),
                    timeframe=int(r["timeframe"]),
                    forces=forces,
                    price=price,
                    market_spread=market_spread,
                )
            )

        return out

    finally:
        conn.close()


# ============================================================
# MATH
# ============================================================

def mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return statistics.fmean(values)


def pvariance(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    return statistics.pvariance(values)


def rolling_zscore(values: Sequence[float], lookback: int) -> List[float]:
    z_values: List[float] = []

    for i, value in enumerate(values):
        start = max(0, i - lookback + 1)
        window = list(values[start : i + 1])

        if len(window) < MIN_ROWS_FOR_Z:
            z_values.append(0.0)
            continue

        m = mean(window)
        std = math.sqrt(pvariance(window))

        if std <= 1e-9:
            z_values.append(0.0)
        else:
            z_values.append((value - m) / std)

    return z_values


def delta(values: Sequence[float], bars: int) -> float:
    if len(values) <= bars:
        return 0.0
    return values[-1] - values[-1 - bars]


def find_crosses(spread: Sequence[float], lookback: int) -> Tuple[bool, bool]:
    """
    spread = base - quote

    LONG cross:
        spread passe de <= 0 à > 0

    SHORT cross:
        spread passe de >= 0 à < 0
    """
    if len(spread) < 2:
        return False, False

    start = max(1, len(spread) - lookback)

    long_cross = False
    short_cross = False

    for i in range(len(spread) - 1, start - 1, -1):
        prev_s = spread[i - 1]
        curr_s = spread[i]

        if prev_s <= 0.0 and curr_s > 0.0:
            long_cross = True

        if prev_s >= 0.0 and curr_s < 0.0:
            short_cross = True

    return long_cross, short_cross


def center_reentry(base_force: float, quote_force: float) -> bool:
    return (
        abs(base_force - CENTER_LEVEL) <= CENTER_BAND
        and abs(quote_force - CENTER_LEVEL) <= CENTER_BAND
    )


def compute_score(
    tension_strength: float,
    thrust: bool,
    compression: bool,
    cross: bool,
    quasi_cross: bool,
    center: bool,
    liquidity_absorbed: bool,
) -> float:
    score = tension_strength

    if thrust:
        score *= 1.25
    if compression:
        score *= 1.15
    if cross:
        score *= 1.20
    if quasi_cross:
        score *= 1.08
    if center:
        score *= 1.08
    if liquidity_absorbed:
        score *= 1.20

    return score


# ============================================================
# DÉTECTION DIRECTIONNELLE PAR TF
# ============================================================

def analyze_tf(
    snapshots: List[Snapshot],
    symbol: str,
    tf: int,
    base: str,
    quote: str,
) -> TfReport:
    base_l = base.lower()
    quote_l = quote.lower()

    if not snapshots:
        return empty_report(symbol, tf, base, quote, "NO_ALERT", "aucune donnée")

    last = snapshots[-1]
    base_force_now = last.forces.get(base_l, 0.0)
    quote_force_now = last.forces.get(quote_l, 0.0)

    if len(snapshots) < MIN_ROWS_FOR_Z:
        spread_now = base_force_now - quote_force_now

        return empty_report(
            symbol=symbol,
            tf=tf,
            base=base,
            quote=quote,
            verdict="NO_ALERT",
            reason=f"pas assez de lignes pour Z-score: {len(snapshots)} < {MIN_ROWS_FOR_Z}",
            last_time=last.created_at,
            base_force=base_force_now,
            quote_force=quote_force_now,
            pair_spread=spread_now,
            rows=len(snapshots),
        )

    base_forces = [s.forces[base_l] for s in snapshots]
    quote_forces = [s.forces[quote_l] for s in snapshots]

    pair_spread = [b - q for b, q in zip(base_forces, quote_forces)]

    # Z-score directionnel de la paire.
    # Si spread_z > 0  => base domine quote => LONG.
    # Si spread_z < 0  => quote domine base => SHORT.
    spread_z = rolling_zscore(pair_spread, Z_LOOKBACK)

    # Affichage explicite demandé.
    base_z_series = spread_z
    quote_z_series = [-z for z in spread_z]

    spread_now = pair_spread[-1]
    spread_prev = pair_spread[-2]

    d1 = spread_now - spread_prev
    d3 = delta(pair_spread, 3)
    d5 = delta(pair_spread, 5)

    base_z_now = base_z_series[-1]
    quote_z_now = quote_z_series[-1]
    spread_z_now = spread_z[-1]

    window_start = max(0, len(pair_spread) - TENSION_WINDOW)
    spread_window = pair_spread[window_start:]
    spread_z_window = spread_z[window_start:]

    min_spread_z_window = min(spread_z_window)
    max_spread_z_window = max(spread_z_window)

    gap_abs_now = abs(spread_now)
    gap_abs_prev = abs(spread_prev)
    max_gap_recent = max(abs(x) for x in spread_window)
    gap_compression = max_gap_recent - gap_abs_now

    long_cross, short_cross = find_crosses(pair_spread, lookback=8)

    quasi_cross = gap_abs_now <= QUASI_CROSS_DISTANCE
    is_center = center_reentry(base_force_now, quote_force_now)
    compression = gap_compression >= MIN_GAP_COMPRESSION

    # LONG:
    # base pousse / quote s'effondre / spread monte.
    long_tension = (
        spread_z_now >= Z_DOMINANT
        or max_spread_z_window >= Z_EXTREME
    )

    long_thrust = (
        d3 >= MIN_THRUST_DELTA_3
        or d5 >= MIN_THRUST_DELTA_5
    )

    # SHORT:
    # quote pousse / base s'effondre / spread plonge.
    short_tension = (
        spread_z_now <= -Z_DOMINANT
        or min_spread_z_window <= -Z_EXTREME
    )

    short_thrust = (
        d3 <= -MIN_THRUST_DELTA_3
        or d5 <= -MIN_THRUST_DELTA_5
    )

    # Absorption/fake fold directionnel:
    # LONG = spread a tapé très bas puis remonte.
    # SHORT = spread a tapé très haut puis replonge.
    liquidity_absorbed_long = (
        min_spread_z_window <= -Z_EXTREME
        and (spread_z_now - min_spread_z_window) >= LIQUIDITY_Z_REBOUND
    )

    liquidity_absorbed_short = (
        max_spread_z_window >= Z_EXTREME
        and (max_spread_z_window - spread_z_now) >= LIQUIDITY_Z_REBOUND
    )

    long_strength = max(0.0, max_spread_z_window)
    short_strength = max(0.0, abs(min_spread_z_window))

    score_long = compute_score(
        tension_strength=long_strength,
        thrust=long_thrust,
        compression=compression,
        cross=long_cross,
        quasi_cross=quasi_cross,
        center=is_center,
        liquidity_absorbed=liquidity_absorbed_long,
    )

    score_short = compute_score(
        tension_strength=short_strength,
        thrust=short_thrust,
        compression=compression,
        cross=short_cross,
        quasi_cross=quasi_cross,
        center=is_center,
        liquidity_absorbed=liquidity_absorbed_short,
    )

    verdict, direction, reason = classify_directional(
        long_tension=long_tension,
        short_tension=short_tension,
        long_thrust=long_thrust,
        short_thrust=short_thrust,
        long_cross=long_cross,
        short_cross=short_cross,
        quasi_cross=quasi_cross,
        center=is_center,
        compression=compression,
        liquidity_absorbed_long=liquidity_absorbed_long,
        liquidity_absorbed_short=liquidity_absorbed_short,
        score_long=score_long,
        score_short=score_short,
        spread_now=spread_now,
    )

    return TfReport(
        tf=tf,
        rows=len(snapshots),
        symbol=symbol.upper(),
        base=base.upper(),
        quote=quote.upper(),
        last_time=last.created_at,
        base_force=base_force_now,
        quote_force=quote_force_now,
        pair_spread_now=spread_now,
        pair_spread_prev=spread_prev,
        pair_spread_delta_1=d1,
        pair_spread_delta_3=d3,
        pair_spread_delta_5=d5,
        base_z_now=base_z_now,
        quote_z_now=quote_z_now,
        spread_z_now=spread_z_now,
        min_spread_z_window=min_spread_z_window,
        max_spread_z_window=max_spread_z_window,
        gap_abs_now=gap_abs_now,
        gap_abs_prev=gap_abs_prev,
        gap_compression=gap_compression,
        long_tension=long_tension,
        short_tension=short_tension,
        long_thrust=long_thrust,
        short_thrust=short_thrust,
        long_cross=long_cross,
        short_cross=short_cross,
        quasi_cross=quasi_cross,
        center_reentry=is_center,
        compression=compression,
        liquidity_absorbed_long=liquidity_absorbed_long,
        liquidity_absorbed_short=liquidity_absorbed_short,
        direction=direction,
        score_long=score_long,
        score_short=score_short,
        verdict=verdict,
        reason=reason,
    )


def classify_directional(
    long_tension: bool,
    short_tension: bool,
    long_thrust: bool,
    short_thrust: bool,
    long_cross: bool,
    short_cross: bool,
    quasi_cross: bool,
    center: bool,
    compression: bool,
    liquidity_absorbed_long: bool,
    liquidity_absorbed_short: bool,
    score_long: float,
    score_short: float,
    spread_now: float,
) -> Tuple[str, str, str]:
    """
    Décision directionnelle.
    Le sens est choisi par le score dominant.
    """

    long_behavior = long_thrust or long_cross or quasi_cross or center or liquidity_absorbed_long
    short_behavior = short_thrust or short_cross or quasi_cross or center or liquidity_absorbed_short

    long_active = long_tension and long_behavior
    short_active = short_tension and short_behavior

    # Priorité au score réel, pas à une croyance acteur/adverse.
    if short_active and score_short >= ALERT_SCORE and score_short >= score_long:
        return (
            "ALERT_SHORT",
            "SHORT",
            "quote domine base: spread base-quote plonge / fermeture baissière confirmée",
        )

    if long_active and score_long >= ALERT_SCORE and score_long > score_short:
        return (
            "ALERT_LONG",
            "LONG",
            "base domine quote: spread base-quote monte / fermeture haussière confirmée",
        )

    if short_tension and score_short >= PRE_ALERT_SCORE and score_short >= score_long:
        return (
            "PRE_ALERT_SHORT",
            "SHORT",
            "tension baissière: quote fort, base faible, attente confirmation tactique",
        )

    if long_tension and score_long >= PRE_ALERT_SCORE and score_long > score_short:
        return (
            "PRE_ALERT_LONG",
            "LONG",
            "tension haussière: base fort, quote faible, attente confirmation tactique",
        )

    # Cas direct très lisible même si score pas encore élevé.
    if spread_now < 0 and short_tension:
        return (
            "PRE_ALERT_SHORT",
            "SHORT",
            "spread négatif avec tension SHORT, mais score encore sous seuil ALERT",
        )

    if spread_now > 0 and long_tension:
        return (
            "PRE_ALERT_LONG",
            "LONG",
            "spread positif avec tension LONG, mais score encore sous seuil ALERT",
        )

    return (
        "NO_ALERT",
        "NONE",
        "aucune tension directionnelle exploitable",
    )


def empty_report(
    symbol: str,
    tf: int,
    base: str,
    quote: str,
    verdict: str,
    reason: str,
    last_time: str = "NA",
    base_force: float = 0.0,
    quote_force: float = 0.0,
    pair_spread: float = 0.0,
    rows: int = 0,
) -> TfReport:
    return TfReport(
        tf=tf,
        rows=rows,
        symbol=symbol.upper(),
        base=base.upper(),
        quote=quote.upper(),
        last_time=last_time,
        base_force=base_force,
        quote_force=quote_force,
        pair_spread_now=pair_spread,
        pair_spread_prev=0.0,
        pair_spread_delta_1=0.0,
        pair_spread_delta_3=0.0,
        pair_spread_delta_5=0.0,
        base_z_now=0.0,
        quote_z_now=0.0,
        spread_z_now=0.0,
        min_spread_z_window=0.0,
        max_spread_z_window=0.0,
        gap_abs_now=abs(pair_spread),
        gap_abs_prev=0.0,
        gap_compression=0.0,
        long_tension=False,
        short_tension=False,
        long_thrust=False,
        short_thrust=False,
        long_cross=False,
        short_cross=False,
        quasi_cross=False,
        center_reentry=False,
        compression=False,
        liquidity_absorbed_long=False,
        liquidity_absorbed_short=False,
        direction="NONE",
        score_long=0.0,
        score_short=0.0,
        verdict=verdict,
        reason=reason,
    )


# ============================================================
# PRINT
# ============================================================

def pair_label(symbol: str) -> str:
    s = symbol.upper()
    if len(s) == 6:
        return f"{s[:3]}/{s[3:]}"
    return s


def yn(v: bool) -> str:
    return "Y" if v else "N"


def print_report_line(r: TfReport) -> None:
    print(
        f"[M{r.tf:<3}] {pair_label(r.symbol):<7} "
        f"{r.verdict:<16} "
        f"dir={r.direction:<5} "
        f"rows={r.rows:<4} "
        f"time={r.last_time} | "
        f"{r.base}={r.base_force:>6.2f} "
        f"{r.quote}={r.quote_force:>6.2f} | "
        f"Z({r.base})={r.base_z_now:>6.2f} "
        f"Z({r.quote})={r.quote_z_now:>6.2f} | "
        f"spread={r.pair_spread_now:>7.2f} "
        f"d3={r.pair_spread_delta_3:>7.2f} "
        f"d5={r.pair_spread_delta_5:>7.2f} | "
        f"scoreL={r.score_long:>5.2f} "
        f"scoreS={r.score_short:>5.2f} | "
        f"{r.reason}"
    )


def print_report_verbose(r: TfReport) -> None:
    print(
        "    flags:",
        f"LONG_tension={yn(r.long_tension)}",
        f"SHORT_tension={yn(r.short_tension)}",
        f"LONG_thrust={yn(r.long_thrust)}",
        f"SHORT_thrust={yn(r.short_thrust)}",
        f"LONG_cross={yn(r.long_cross)}",
        f"SHORT_cross={yn(r.short_cross)}",
        f"quasi_cross={yn(r.quasi_cross)}",
        f"center={yn(r.center_reentry)}",
        f"compression={yn(r.compression)}",
        f"liq_LONG={yn(r.liquidity_absorbed_long)}",
        f"liq_SHORT={yn(r.liquidity_absorbed_short)}",
    )
    print(
        "    window:",
        f"minZ_spread={r.min_spread_z_window:.2f}",
        f"maxZ_spread={r.max_spread_z_window:.2f}",
        f"gap_now={r.gap_abs_now:.2f}",
        f"gap_compression={r.gap_compression:.2f}",
    )


# ============================================================
# CLI
# ============================================================

def parse_tfs(raw: Optional[str]) -> Optional[List[int]]:
    if raw is None or raw.strip() == "":
        return None

    out = []
    for part in raw.split(","):
        part = part.strip()
        if part:
            out.append(int(part))

    return out


def derive_base_quote(symbol: str, base: Optional[str], quote: Optional[str]) -> Tuple[str, str]:
    s = symbol.upper()

    if base and quote:
        return base.upper(), quote.upper()

    if len(s) != 6:
        raise SystemExit(
            "Impossible de dériver base/quote depuis le symbole. "
            "Utilise --base XXX --quote YYY."
        )

    return s[:3], s[3:]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="PowerFlow V6 DEBUG MULTI-TF DIRECTIONNEL — LONG/SHORT"
    )

    p.add_argument("--db", default=DEFAULT_DB_PATH)
    p.add_argument("--symbol", default=DEFAULT_SYMBOL)

    p.add_argument("--base", default=DEFAULT_BASE)
    p.add_argument("--quote", default=DEFAULT_QUOTE)

    # Compatibilité avec anciens appels --actor / --adverse
    p.add_argument("--actor", default=None, help="Alias de --base")
    p.add_argument("--adverse", default=None, help="Alias de --quote")

    p.add_argument("--tfs", default=None)
    p.add_argument("--rows", type=int, default=ROWS_TO_LOAD)
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--all-db-tfs", action="store_true")
    p.add_argument("--loop", action="store_true")
    p.add_argument("--sleep", type=float, default=6.0)

    return p.parse_args()


def resolve_timeframes(args: argparse.Namespace) -> List[int]:
    requested = parse_tfs(args.tfs)
    available = get_available_timeframes(args.db, args.symbol)

    if requested:
        return [tf for tf in requested if tf in available]

    if args.all_db_tfs:
        return available

    return [tf for tf in DEFAULT_TFS if tf in available]


def run_once(args: argparse.Namespace) -> None:
    base_arg = args.base or args.actor
    quote_arg = args.quote or args.adverse

    base, quote = derive_base_quote(args.symbol, base_arg, quote_arg)

    if base.lower() not in CURRENCIES:
        raise SystemExit(f"Base invalide: {base}")

    if quote.lower() not in CURRENCIES:
        raise SystemExit(f"Quote invalide: {quote}")

    tfs = resolve_timeframes(args)

    print("")
    print("=" * 170)
    print(
        f"POWERFLOW V6 DIRECTIONAL DEBUG | "
        f"{pair_label(args.symbol)} | "
        f"base={base} quote={quote} | "
        f"spread={base}-{quote} | "
        f"TF={tfs}"
    )
    print("=" * 170)

    if not tfs:
        print("NO_ALERT | aucun TF disponible pour cette paire")
        return

    for tf in tfs:
        snapshots = load_snapshots_for_tf(
            db_path=args.db,
            symbol=args.symbol,
            timeframe=tf,
            base=base,
            quote=quote,
            limit=args.rows,
        )

        report = analyze_tf(
            snapshots=snapshots,
            symbol=args.symbol,
            tf=tf,
            base=base,
            quote=quote,
        )

        print_report_line(report)

        if args.verbose:
            print_report_verbose(report)

    print("=" * 170)
    print("")


def main() -> None:
    args = parse_args()

    if args.loop:
        import time

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