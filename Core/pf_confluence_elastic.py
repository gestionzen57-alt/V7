"""
pf_confluence_elastic.py — PowerFlow V7
Brique Confluence Élastique : détection EIE, fractalité, états.
Appelée par run_confluence_alert.py et lab.py / film.py.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

CURRENCIES = ["EUR", "GBP", "JPY", "CHF", "AUD", "NZD", "CAD", "USD"]
FRACTAL_TFS = [15, 30, 60]
ZONE_ACTIVE_STATES = {"ACCUMULATING", "EARLY_EXTREME", "LEAKING", "PRE_EXTREME", "RUPTURE"}
ELASTIC_LABELS_CHARGED = {"ELASTIC_LOADED", "CHARGING"}
MIN_BARS_REQUIRED = 20


@dataclass
class EIEState:
    currency: str
    zone_state: str
    zone_z: float
    zone_dir: str
    elastic_label_tf1: str
    elastic_label_tf5: str
    elastic_score: float
    is_eie: bool
    is_ewz: bool
    is_enz: bool
    is_zne: bool
    fractal_score: int
    fractal_label: str
    regime_context: str = "UNKNOWN"
    noise_ratio: float = 0.0


@dataclass
class ConfluenceSnapshot:
    timestamp: datetime
    states: dict = field(default_factory=dict)

    def eie_currencies(self) -> list:
        return [c for c, s in self.states.items() if s.is_eie]

    def fractal_alert(self) -> bool:
        return any(s.fractal_score >= 2 for s in self.states.values() if s.is_eie)


def _fetch_recent_force(db_path: Path, tf: int, currency: str, bars: int = 50) -> list:
    col = f"force_{currency.lower()}"
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur = con.execute(
            f"SELECT {col} FROM force_snapshots WHERE timeframe=? AND {col} IS NOT NULL "
            f"ORDER BY timestamp DESC LIMIT ?", (tf, bars),
        )
        rows = [r[0] for r in cur.fetchall()]
        con.close()
        return list(reversed(rows))
    except Exception:
        return []


def _latest_snapshot_ts(db_path: Path, tf: int) -> Optional[datetime]:
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur = con.execute(
            "SELECT timestamp FROM force_snapshots WHERE timeframe=? ORDER BY timestamp DESC LIMIT 1", (tf,),
        )
        row = cur.fetchone()
        con.close()
        if row:
            return datetime.fromisoformat(row[0].replace("Z", "+00:00"))
    except Exception:
        pass
    return None


def _compute_elastic(series: list) -> tuple:
    if len(series) < MIN_BARS_REQUIRED:
        return "NEUTRAL", 0.0
    import statistics
    mean = statistics.mean(series)
    std = statistics.stdev(series) if len(series) > 1 else 0.001
    if std == 0:
        std = 0.001
    last = series[-1]
    z = (last - mean) / std
    abs_z = abs(z)
    diffs = [series[i] - series[i - 1] for i in range(1, len(series))]
    last_n = diffs[-5:] if len(diffs) >= 5 else diffs
    sign_changes = sum(1 for i in range(1, len(last_n)) if last_n[i] * last_n[i - 1] < 0)
    asymmetry_score = 1.0 - (sign_changes / max(len(last_n) - 1, 1))
    last_8 = series[-8:]
    if len(last_8) >= 2:
        direction = 1 if last_8[-1] > last_8[0] else -1
        consistent = sum(1 for i in range(1, len(last_8)) if (last_8[i] - last_8[i - 1]) * direction > 0)
        persistence = consistent / (len(last_8) - 1)
    else:
        persistence = 0.5
    score = min(1.0, (abs_z / 3.0) * 0.5 + asymmetry_score * 0.3 + persistence * 0.2)
    if abs_z > 2.0 and persistence > 0.6:
        label = "ELASTIC_LOADED"
    elif abs_z > 1.2 and persistence > 0.4:
        label = "CHARGING"
    elif abs_z < 0.5 or (z * (last - mean) < 0):
        label = "LEAKING"
    else:
        label = "NEUTRAL"
    return label, round(score, 4)


def _zone_state(series: list) -> tuple:
    if len(series) < MIN_BARS_REQUIRED:
        return "NEUTRAL", 0.0, "FLAT"
    import statistics
    mean = statistics.mean(series)
    std = statistics.stdev(series) if len(series) > 1 else 0.001
    if std == 0:
        std = 0.001
    last = series[-1]
    z = (last - mean) / std
    abs_z = abs(z)
    direction = "HIGH" if z > 0 else "LOW"
    if abs_z >= 3.0:
        state = "RUPTURE"
    elif abs_z >= 2.0:
        state = "EARLY_EXTREME"
    elif abs_z >= 1.5:
        state = "ACCUMULATING"
    elif abs_z >= 1.0:
        state = "PRE_EXTREME"
    elif abs_z >= 0.3:
        state = "LEAKING"
    else:
        state = "NEUTRAL"
    return state, round(z, 4), direction


def _fractal_label(score: int) -> str:
    return {0: "NO_ALIGN", 1: "PARTIAL_ALIGN", 2: "ALIGN", 3: "FULL_ALIGN"}.get(score, "NO_ALIGN")


def compute_eie_state(
    db_path: Path,
    currency: str,
    zone_tf: int = 15,
    regime_context: str = "UNKNOWN",
    noise_ratio: float = 0.0,
) -> EIEState:
    zone_series = _fetch_recent_force(db_path, zone_tf, currency, bars=60)
    zone_state, zone_z, zone_dir = _zone_state(zone_series)
    s1 = _fetch_recent_force(db_path, 1, currency, bars=50)
    s5 = _fetch_recent_force(db_path, 5, currency, bars=50)
    label_tf1, _ = _compute_elastic(s1)
    label_tf5, score_tf5 = _compute_elastic(s5)
    zone_active = zone_state in ZONE_ACTIVE_STATES
    elastic_tf1 = label_tf1 in ELASTIC_LABELS_CHARGED
    elastic_tf5 = label_tf5 in ELASTIC_LABELS_CHARGED
    is_eie = zone_active and elastic_tf1 and elastic_tf5
    is_ewz = zone_active and (elastic_tf1 or elastic_tf5) and not is_eie
    is_enz = (elastic_tf1 and elastic_tf5) and not zone_active
    is_zne = zone_active and not elastic_tf1 and not elastic_tf5
    fractal_count = 0
    for ftf in FRACTAL_TFS:
        fs = _fetch_recent_force(db_path, ftf, currency, bars=40)
        fstate, _, _ = _zone_state(fs)
        if fstate in ZONE_ACTIVE_STATES:
            fractal_count += 1
    return EIEState(
        currency=currency, zone_state=zone_state, zone_z=zone_z, zone_dir=zone_dir,
        elastic_label_tf1=label_tf1, elastic_label_tf5=label_tf5, elastic_score=score_tf5,
        is_eie=is_eie, is_ewz=is_ewz, is_enz=is_enz, is_zne=is_zne,
        fractal_score=fractal_count, fractal_label=_fractal_label(fractal_count),
        regime_context=regime_context, noise_ratio=noise_ratio,
    )


def compute_confluence_snapshot(
    db_path: Path,
    zone_tf: int = 15,
    regime_contexts: Optional[dict] = None,
    noise_ratios: Optional[dict] = None,
) -> ConfluenceSnapshot:
    ts = _latest_snapshot_ts(db_path, 1) or datetime.now(timezone.utc)
    snap = ConfluenceSnapshot(timestamp=ts)
    rc = regime_contexts or {}
    nr = noise_ratios or {}
    for currency in CURRENCIES:
        state = compute_eie_state(
            db_path=db_path, currency=currency, zone_tf=zone_tf,
            regime_context=rc.get(currency, "UNKNOWN"), noise_ratio=nr.get(currency, 0.0),
        )
        snap.states[currency] = state
    return snap


def query_eie_history(db_path: Path, currency: str, zone_tf: int = 15, limit: int = 100) -> list:
    col = f"force_{currency.lower()}"
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur = con.execute(
            f"SELECT timestamp, {col} FROM force_snapshots "
            f"WHERE timeframe=5 AND {col} IS NOT NULL "
            f"ORDER BY timestamp DESC LIMIT ?", (limit,),
        )
        rows = list(reversed(cur.fetchall()))
        con.close()
    except Exception:
        return []
    results = []
    window = []
    for ts_str, val in rows:
        window.append(val)
        if len(window) > 50:
            window = window[-50:]
        if len(window) >= MIN_BARS_REQUIRED:
            label, score = _compute_elastic(window)
            zone_state, z, direction = _zone_state(window)
            zone_active = zone_state in ZONE_ACTIVE_STATES
            elastic = label in ELASTIC_LABELS_CHARGED
            results.append({
                "timestamp": ts_str, "currency": currency,
                "zone_state": zone_state, "zone_z": round(z, 4), "zone_dir": direction,
                "elastic_label": label, "elastic_score": score,
                "eie": zone_active and elastic,
                "ewz": zone_active and not elastic,
                "enz": elastic and not zone_active,
            })
    return results


def query_eie_sessions_summary(
    db_path: Path,
    date_str: Optional[str] = None,
    zone_tf: int = 15,
    min_persist: int = 2,
) -> dict:
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cols = ", ".join(f"force_{c.lower()}" for c in CURRENCIES)
        cur = con.execute(
            f"SELECT timestamp, {cols} FROM force_snapshots "
            "WHERE timeframe=5 AND substr(timestamp, 1, 10)=? ORDER BY timestamp", (date_str,),
        )
        rows = cur.fetchall()
        con.close()
    except Exception:
        return {}
    eie_counts = {c: 0 for c in CURRENCIES}
    persist_counters = {c: 0 for c in CURRENCIES}
    windows = {c: [] for c in CURRENCIES}
    for row in rows:
        for i, currency in enumerate(CURRENCIES):
            val = row[i + 1]
            if val is None:
                continue
            w = windows[currency]
            w.append(val)
            if len(w) > 50:
                windows[currency] = w[-50:]
            if len(w) >= MIN_BARS_REQUIRED:
                label, _ = _compute_elastic(w)
                zone_state, _, _ = _zone_state(w)
                is_eie = (zone_state in ZONE_ACTIVE_STATES) and (label in ELASTIC_LABELS_CHARGED)
                if is_eie:
                    persist_counters[currency] += 1
                    if persist_counters[currency] >= min_persist:
                        eie_counts[currency] += 1
                else:
                    persist_counters[currency] = 0
    return {
        "date": date_str,
        "min_persist": min_persist,
        "eie_counts": eie_counts,
        "total_eie": sum(eie_counts.values()),
    }