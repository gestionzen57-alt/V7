# pf_spearman_gravity.py — PowerFlow V7 — B5 Relational Copula
# Corrélation de rang Spearman rolling par paire de devises
# Version : 1.0.0 — 2026-05-09
# Read-only DB. Remplace heuristique MIXED par probabilité mesurée.

from __future__ import annotations
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np


CURRENCIES = ["GBP", "USD", "EUR", "JPY", "CAD", "CHF", "AUD"]

SYNCHRO_THRESHOLD = 0.70    # rho > 0.70 → SYNCHRO
DIVERGE_THRESHOLD = -0.50   # rho < -0.50 → DIVERGENT
TAIL_THRESHOLD = 0.85       # rho > 0.85 → co-dépendance extrême


@dataclass
class SpearmanPairResult:
    pair: str
    currency_a: str
    currency_b: str
    timeframe: int
    spearman_rho: float       # -1.0 → +1.0
    direction: str            # SYNCHRO / DIVERGENT / NEUTRAL
    tail_signal: str          # CODEPENDANT_EXTREME / NORMAL / DIVERGENT_EXTREME
    bars_analyzed: int
    timestamp: str


def _fetch_two_series(
    db_path: str,
    col_a: str,
    col_b: str,
    timeframe: int,
    bars: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """Fetch two force series aligned by rowid. Read-only."""
    uri = f"file:{db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        rows = conn.execute(
            f"SELECT {col_a}, {col_b} FROM force_snapshots "
            f"WHERE timeframe=? AND {col_a} IS NOT NULL AND {col_b} IS NOT NULL "
            f"ORDER BY created_at DESC LIMIT ?",
            (timeframe, bars),
        ).fetchall()
        if not rows:
            return np.array([]), np.array([])
        a = np.array([r[0] for r in rows], dtype=float)
        b = np.array([r[1] for r in rows], dtype=float)
        return a[::-1], b[::-1]  # chronologique
    finally:
        conn.close()


def _spearman_rho(a: np.ndarray, b: np.ndarray) -> float:
    """Spearman rank correlation — numpy pur, sans scipy."""
    if len(a) < 5:
        return 0.0
    rank_a = np.argsort(np.argsort(a)).astype(float)
    rank_b = np.argsort(np.argsort(b)).astype(float)
    n = len(rank_a)
    d2 = np.sum((rank_a - rank_b) ** 2)
    rho = 1.0 - (6.0 * d2) / (n * (n**2 - 1))
    return float(np.clip(rho, -1.0, 1.0))


def compute_spearman_pair(
    db_path: str,
    currency_a: str,
    currency_b: str,
    timeframe: int,
    bars: int = 30,
) -> Optional[SpearmanPairResult]:
    """Compute Spearman rho for one pair × TF."""
    col_a = f"force_{currency_a.lower()}"
    col_b = f"force_{currency_b.lower()}"

    a, b = _fetch_two_series(db_path, col_a, col_b, timeframe, bars)
    if len(a) < 10:
        return None

    rho = _spearman_rho(a, b)

    # Direction
    if rho >= SYNCHRO_THRESHOLD:
        direction = "SYNCHRO"
    elif rho <= DIVERGE_THRESHOLD:
        direction = "DIVERGENT"
    else:
        direction = "NEUTRAL"

    # Tail signal
    if rho >= TAIL_THRESHOLD:
        tail_signal = "CODEPENDANT_EXTREME"
    elif rho <= -TAIL_THRESHOLD:
        tail_signal = "DIVERGENT_EXTREME"
    else:
        tail_signal = "NORMAL"

    pair = f"{currency_a.upper()}_{currency_b.upper()}"
    return SpearmanPairResult(
        pair=pair,
        currency_a=currency_a.upper(),
        currency_b=currency_b.upper(),
        timeframe=timeframe,
        spearman_rho=round(rho, 3),
        direction=direction,
        tail_signal=tail_signal,
        bars_analyzed=len(a),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def compute_spearman_all_pairs(
    db_path: str,
    timeframes: List[int],
    bars: int = 30,
    currencies: List[str] = None,
) -> Dict[str, Dict[int, Optional[SpearmanPairResult]]]:
    """Compute all pairs × all TFs."""
    if currencies is None:
        currencies = CURRENCIES

    pairs = []
    for i, a in enumerate(currencies):
        for b in currencies[i+1:]:
            pairs.append((a, b))

    results = {}
    for a, b in pairs:
        pair_key = f"{a}_{b}"
        results[pair_key] = {}
        for tf in timeframes:
            results[pair_key][tf] = compute_spearman_pair(
                db_path, a, b, tf, bars
            )
    return results


def format_spearman_summary(results: Dict) -> dict:
    """Format pour cockpit JSON + enrichissement RG bridge."""
    synchro_pairs = []
    divergent_pairs = []
    tail_extreme = []
    mixed_resolved = []

    details = {}
    for pair, tfs in results.items():
        pair_tfs = {}
        directions = []
        for tf, r in tfs.items():
            if r is None:
                continue
            pair_tfs[f"TF{tf}"] = {
                "spearman_rho": r.spearman_rho,
                "direction": r.direction,
                "tail_signal": r.tail_signal,
            }
            directions.append(r.direction)
            if r.tail_signal == "CODEPENDANT_EXTREME":
                tail_extreme.append(f"{pair}_TF{tf}")

        if pair_tfs:
            details[pair] = pair_tfs
            # Consensus multi-TF
            if all(d == "SYNCHRO" for d in directions):
                synchro_pairs.append(pair)
            elif all(d == "DIVERGENT" for d in directions):
                divergent_pairs.append(pair)
            elif len(set(directions)) > 1:
                # Résolution MIXED : mesurée, pas heuristique
                rhos = [
                    r.spearman_rho
                    for r in tfs.values()
                    if r is not None
                ]
                avg_rho = round(float(np.mean(rhos)), 3)
                mixed_resolved.append({
                    "pair": pair,
                    "avg_rho": avg_rho,
                    "note": "MIXED_PROBABILISTE"
                })

    return {
        "state": "SPEARMAN_GRAVITY_ACTIVE",
        "synchro_pairs": synchro_pairs,
        "divergent_pairs": divergent_pairs,
        "tail_extreme": tail_extreme,
        "mixed_resolved": mixed_resolved,
        "details": details,
        "mixed_count": len(mixed_resolved),
        "synchro_count": len(synchro_pairs),
        "divergent_count": len(divergent_pairs),
    }
