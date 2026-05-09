#!/usr/bin/env python3
"""
pf_temporal_density.py V0.1

PowerFlow V6 - moteur mathematique pur.
Mesure la densite temporelle COMPRESSED / HOLLOW d'une devise
sur les N dernieres barres disponibles dans force_snapshots.

Contraintes respectees :
- lecture seule sur powerflow.db
- aucune ecriture DB
- aucun import vers la couche affichage
- aucun signal directionnel
- compatible Python 3.10+
"""

from __future__ import annotations

import argparse
import os
import sqlite3
from dataclasses import dataclass
from statistics import mean
from typing import Iterable, Sequence


SUPPORTED_CURRENCIES: tuple[str, ...] = ("GBP", "USD", "EUR", "JPY", "CAD", "CHF", "AUD")
LOW_ACTIVITY_DELTA = 0.5
EPSILON = 1e-9


@dataclass(frozen=True)
class TemporalDensityMetrics:
    currency: str
    timeframe: int
    window: int
    density_score: float
    state: str
    avg_delta: float
    max_delta: float
    low_activity_ratio: float
    note: str

    def as_dict(self) -> dict[str, str | int | float]:
        return {
            "currency": self.currency,
            "timeframe": self.timeframe,
            "window": self.window,
            "density_score": self.density_score,
            "state": self.state,
            "avg_delta": self.avg_delta,
            "max_delta": self.max_delta,
            "low_activity_ratio": self.low_activity_ratio,
            "note": self.note,
        }


def _normalize_currency(currency: str) -> str:
    normalized = currency.strip().upper()
    if normalized not in SUPPORTED_CURRENCIES:
        allowed = ", ".join(SUPPORTED_CURRENCIES)
        raise ValueError(f"Devise non supportee: {currency!r}. Devise attendue: {allowed}")
    return normalized


def _force_column(currency: str) -> str:
    normalized = _normalize_currency(currency)
    return f"force_{normalized.lower()}"


def _connect_read_only(db_path: str) -> sqlite3.Connection:
    absolute_path = os.path.abspath(db_path)
    uri = f"file:{absolute_path}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def _fetch_force_values(
    db_path: str,
    symbol: str,
    timeframe: int,
    currency: str,
    window: int,
) -> list[float]:
    if window < 2:
        raise ValueError("window doit etre >= 2 pour calculer des deltas")

    column = _force_column(currency)
    query = f"""
        SELECT {column}
        FROM force_snapshots
        WHERE symbol = ?
          AND timeframe = ?
          AND {column} IS NOT NULL
        ORDER BY created_at DESC
        LIMIT ?
    """

    with _connect_read_only(db_path) as connection:
        rows = connection.execute(query, (symbol.upper(), int(timeframe), int(window))).fetchall()

    # La requete lit du plus recent au plus ancien. Les deltas doivent suivre le temps.
    values = [float(row[0]) for row in reversed(rows)]
    return values


def _classify_density(score: float) -> str:
    if score > 0.70:
        return "COMPRESSED"
    if 0.45 <= score <= 0.70:
        return "ACTIVE"
    if 0.25 <= score < 0.45:
        return "NEUTRAL"
    if 0.10 <= score < 0.25:
        return "HOLLOW"
    return "DEAD"


def _build_note(state: str) -> str:
    notes = {
        "COMPRESSED": "Marche dense: energie concentree, bataille active.",
        "ACTIVE": "Marche vivant: mouvement regulier sur la fenetre.",
        "NEUTRAL": "Activite moyenne: flux present sans densite forte.",
        "HOLLOW": "Marche creux: beaucoup de barres, peu de mouvement.",
        "DEAD": "Derive plate: PowerFlow se tait.",
    }
    return notes[state]


def _dead_result(currency: str, timeframe: int, window: int, note: str) -> dict[str, str | int | float]:
    return TemporalDensityMetrics(
        currency=currency,
        timeframe=int(timeframe),
        window=int(window),
        density_score=0.0,
        state="DEAD",
        avg_delta=0.0,
        max_delta=0.0,
        low_activity_ratio=1.0,
        note=note,
    ).as_dict()


def analyze_temporal_density(
    db_path: str,
    symbol: str,
    timeframe: int,
    currency: str,
    window: int = 20,
) -> dict[str, str | int | float]:
    """
    Analyse la densite temporelle d'une devise sur les N dernieres barres.

    Args:
        db_path: chemin vers powerflow.db.
        symbol: symbole de marche, ex: "GBPUSD".
        timeframe: timeframe entier, ex: 5 pour M5.
        currency: devise, ex: "GBP".
        window: nombre de barres lues.

    Returns:
        dict contenant currency, timeframe, window, density_score, state,
        avg_delta, max_delta, low_activity_ratio et note.
    """
    normalized_currency = _normalize_currency(currency)
    values = _fetch_force_values(db_path, symbol, timeframe, normalized_currency, window)

    if len(values) < 2:
        return _dead_result(
            normalized_currency,
            timeframe,
            window,
            "Donnees insuffisantes: moins de 2 valeurs exploitables.",
        )

    deltas = [abs(values[index] - values[index - 1]) for index in range(1, len(values))]
    avg_delta = float(mean(deltas))
    max_delta = float(max(deltas))
    low_activity_count = sum(1 for delta in deltas if delta < LOW_ACTIVITY_DELTA)
    low_activity_ratio = float(low_activity_count / len(deltas))

    raw_score = (avg_delta / (max_delta + EPSILON)) * (1.0 - low_activity_ratio)
    density_score = max(0.0, min(1.0, float(raw_score)))
    state = _classify_density(density_score)

    metrics = TemporalDensityMetrics(
        currency=normalized_currency,
        timeframe=int(timeframe),
        window=int(window),
        density_score=round(density_score, 6),
        state=state,
        avg_delta=round(avg_delta, 6),
        max_delta=round(max_delta, 6),
        low_activity_ratio=round(low_activity_ratio, 6),
        note=_build_note(state),
    )
    return metrics.as_dict()


def scan_all_currencies(
    db_path: str,
    symbol: str,
    timeframe: int,
    window: int = 20,
    currencies: Sequence[str] | None = None,
) -> list[dict[str, str | int | float]]:
    """
    Analyse toutes les devises demandees et trie par density_score DESC.
    """
    selected_currencies = currencies or SUPPORTED_CURRENCIES
    results = [
        analyze_temporal_density(
            db_path=db_path,
            symbol=symbol,
            timeframe=timeframe,
            currency=currency,
            window=window,
        )
        for currency in selected_currencies
    ]
    return sorted(results, key=lambda item: float(item["density_score"]), reverse=True)


def format_temporal_density_table(results: Iterable[dict[str, str | int | float]]) -> str:
    """
    Formate une table console lisible sans dependance externe.
    """
    header = "CURRENCY | TF | STATE      | SCORE | AVG_DELTA | NOTE"
    separator = "-" * len(header)
    lines = [header, separator]

    for row in results:
        currency = str(row["currency"])
        timeframe = f"M{int(row['timeframe'])}"
        state = str(row["state"])
        score = float(row["density_score"])
        avg_delta = float(row["avg_delta"])
        note = str(row["note"])
        lines.append(
            f"{currency:<8} | {timeframe:<2} | {state:<10} | {score:>5.2f} | {avg_delta:>9.2f} | {note}"
        )

    return "\n".join(lines)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PowerFlow V6 - Temporal Density V0.1")
    parser.add_argument("--db", required=True, help="Chemin vers powerflow.db")
    parser.add_argument("--symbol", required=True, help="Symbole, ex: GBPUSD")
    parser.add_argument("--tf", required=True, type=int, help="Timeframe entier, ex: 5 pour M5")
    parser.add_argument("--window", default=20, type=int, help="Nombre de barres a analyser")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    results = scan_all_currencies(
        db_path=args.db,
        symbol=args.symbol,
        timeframe=args.tf,
        window=args.window,
    )
    print(format_temporal_density_table(results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
