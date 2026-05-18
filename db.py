"""
PowerFlow V3 — DB Compagnon V1
==============================
Module de persistance SQLite pour les signaux PowerFlow.

Doctrine : simple sur l'essentiel, profond sur le vivant, lucide sur la construction.

Règles de conception :
- SQLite pur (module standard `sqlite3`, aucune dépendance externe).
- `log_signal` est NON-BLOQUANT : toute exception est avalée et loggée
  en console, jamais remontée — le moteur PowerFlow ne doit jamais
  crasher à cause de la DB.
- Les fonctions de lecture retournent des listes de dicts plats,
  prêtes à être consommées par un dashboard ou une API.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any


# ---------------------------------------------------------------------------
# Schéma — gardé ici pour que `init_db` soit autonome (même sans schema.sql).
# ---------------------------------------------------------------------------
_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS signals (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at              TEXT    NOT NULL,
    symbol                  TEXT    NOT NULL,
    timeframe               INTEGER NOT NULL,
    signal_type             TEXT    NOT NULL,
    dev_strong              TEXT    NOT NULL,
    dev_weak                TEXT    NOT NULL,
    score                   INTEGER NOT NULL,
    level                   TEXT    NOT NULL,
    spread_ok               INTEGER NOT NULL,
    volume_badge            TEXT,
    note                    TEXT,
    price                   REAL,
    is_post_extreme         INTEGER NOT NULL DEFAULT 0,
    post_extreme_side       TEXT,
    has_convergence         INTEGER NOT NULL DEFAULT 0,
    conv_tf1                INTEGER,
    conv_tf2                INTEGER,
    conv_niveau             TEXT,
    conv_delta              REAL,
    conv_bonus              INTEGER,
    is_slingshot_sequence   INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_signals_created_at   ON signals(created_at);
CREATE INDEX IF NOT EXISTS idx_signals_symbol       ON signals(symbol);
CREATE INDEX IF NOT EXISTS idx_signals_signal_type  ON signals(signal_type);
CREATE INDEX IF NOT EXISTS idx_signals_level        ON signals(level);

CREATE TABLE IF NOT EXISTS context_htf (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id       INTEGER NOT NULL,
    bias            TEXT,
    bias_state      TEXT,
    scenario        TEXT,
    aligned_count   INTEGER,
    fractal_rank    INTEGER,
    leader_tf       TEXT,
    htf_bonus       INTEGER,
    details_json    TEXT,
    FOREIGN KEY (signal_id) REFERENCES signals(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_context_signal_id ON context_htf(signal_id);

CREATE TABLE IF NOT EXISTS force_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at      TEXT    NOT NULL,
    symbol          TEXT    NOT NULL,
    timeframe       INTEGER NOT NULL,
    bid             REAL,
    spread          REAL,
    force_gbp       REAL,
    force_usd       REAL,
    force_eur       REAL,
    force_jpy       REAL,
    force_cad       REAL,
    force_chf       REAL,
    force_aud       REAL
);

CREATE INDEX IF NOT EXISTS idx_force_snapshots_created_at
    ON force_snapshots(created_at);
CREATE INDEX IF NOT EXISTS idx_force_snapshots_symbol_tf_created_at
    ON force_snapshots(symbol, timeframe, created_at);

-- ---------------------------------------------------------------------------
-- Force Snapshots V2 - EA extended sonde
-- Legacy force_snapshots remains untouched for existing modules.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS force_snapshots_v2 (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at      TEXT    NOT NULL,
    symbol          TEXT    NOT NULL,
    timeframe       INTEGER NOT NULL,

    bar_time        REAL,
    bar_close_time  REAL,
    server_time     REAL,
    capture_time    REAL,
    is_closed_bar   INTEGER,

    bid             REAL,
    ask             REAL,
    mid             REAL,

    spread          REAL,
    spread_points   REAL,
    spread_price    REAL,
    spread_pips     REAL,

    open            REAL,
    high            REAL,
    low             REAL,
    close           REAL,
    tick_volume     REAL,

    pip_range       REAL,
    pip_body        REAL,
    pip_change      REAL,

    force_gbp       REAL,
    force_usd       REAL,
    force_eur       REAL,
    force_jpy       REAL,
    force_cad       REAL,
    force_chf       REAL,
    force_aud       REAL,
    force_nzd       REAL
);

CREATE INDEX IF NOT EXISTS idx_force_snapshots_v2_created_at
    ON force_snapshots_v2(created_at);

CREATE INDEX IF NOT EXISTS idx_force_snapshots_v2_symbol_tf_created_at
    ON force_snapshots_v2(symbol, timeframe, created_at);

CREATE UNIQUE INDEX IF NOT EXISTS idx_force_snapshots_v2_symbol_tf_bar_time
    ON force_snapshots_v2(symbol, timeframe, bar_time);

"""


# ---------------------------------------------------------------------------
# Helpers internes
# ---------------------------------------------------------------------------

def _log(msg: str) -> None:
    """Log console minimaliste — jamais de stacktrace côté moteur."""
    print(f"[db.py] {msg}")


def _iso_from_ts(ts: float | None) -> str:
    """Convertit un timestamp unix en ISO8601 UTC. Fallback sur maintenant."""
    try:
        if ts is None:
            return datetime.now(timezone.utc).isoformat()
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def _bool_to_int(val: Any) -> int:
    """Convertit un bool/int/None en 0/1 pour SQLite."""
    return 1 if bool(val) else 0


def _row_to_dict(row: sqlite3.Row) -> dict:
    """Transforme une Row SQLite en dict propre."""
    return {k: row[k] for k in row.keys()}


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def init_db(db_path: str) -> sqlite3.Connection | None:
    """
    Ouvre (ou crée) la base SQLite et s'assure que les tables existent.

    Retourne la connexion, ou None en cas d'échec (le moteur continue
    alors sans persistance).
    """
    try:
        # Crée le dossier parent si nécessaire
        parent = os.path.dirname(os.path.abspath(db_path))
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)

        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # Active les clés étrangères (désactivées par défaut dans SQLite)
        conn.execute("PRAGMA foreign_keys = ON;")
        # WAL : meilleures perfs en écriture concurrente
        conn.execute("PRAGMA journal_mode = WAL;")

        # Crée le schéma (idempotent)
        conn.executescript(_SCHEMA_SQL)
        conn.commit()

        _log(f"DB initialisée : {db_path}")
        return conn

    except Exception as e:
        _log(f"ERREUR init_db({db_path}) : {e}")
        return None


# ---------------------------------------------------------------------------
# Écriture
# ---------------------------------------------------------------------------

def log_signal(conn: sqlite3.Connection | None, sig: dict, htf: dict) -> int | None:
    """
    Insère un signal et son contexte HTF.

    NON-BLOQUANT : toute exception est avalée et loggée.
    Retourne l'id du signal inséré, ou None si échec / conn absente.
    """
    if conn is None:
        return None

    try:
        # --- Extraction des champs signal (avec défauts prudents) --------
        created_at = _iso_from_ts(sig.get("timestamp"))
        convergence = sig.get("convergence") or None
        has_conv = convergence is not None

        # Champs post-extrême : optionnels côté moteur, on accepte leur absence
        is_post_extreme = _bool_to_int(sig.get("is_post_extreme", False))
        post_extreme_side = sig.get("post_extreme_side")
        is_slingshot_sequence = _bool_to_int(sig.get("is_slingshot_sequence", False))

        signal_row = (
            created_at,
            sig.get("symbol", ""),
            int(sig.get("timeframe", 0)),
            sig.get("signal_type", ""),
            sig.get("dev_strong", ""),
            sig.get("dev_weak", ""),
            int(sig.get("score", 0)),
            sig.get("level", "STANDARD"),
            _bool_to_int(sig.get("spread_ok", False)),
            sig.get("volume_badge"),
            sig.get("note", ""),
            sig.get("price"),
            is_post_extreme,
            post_extreme_side,
            _bool_to_int(has_conv),
            (convergence or {}).get("tf1") if has_conv else None,
            (convergence or {}).get("tf2") if has_conv else None,
            (convergence or {}).get("niveau") if has_conv else None,
            (convergence or {}).get("delta") if has_conv else None,
            (convergence or {}).get("bonus") if has_conv else None,
            is_slingshot_sequence,
        )

        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO signals (
                created_at, symbol, timeframe, signal_type,
                dev_strong, dev_weak, score, level, spread_ok,
                volume_badge, note, price,
                is_post_extreme, post_extreme_side,
                has_convergence, conv_tf1, conv_tf2, conv_niveau,
                conv_delta, conv_bonus,
                is_slingshot_sequence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            signal_row,
        )
        signal_id = cur.lastrowid

        # --- Contexte HTF ------------------------------------------------
        details = htf.get("details", []) if htf else []
        try:
            details_json = json.dumps(details, ensure_ascii=False)
        except Exception:
            details_json = "[]"

        htf_row = (
            signal_id,
            (htf or {}).get("bias"),
            (htf or {}).get("bias_state"),
            (htf or {}).get("scenario"),
            (htf or {}).get("aligned_count"),
            (htf or {}).get("fractal_rank"),
            (htf or {}).get("leader"),
            (htf or {}).get("htf_bonus"),
            details_json,
        )

        cur.execute(
            """
            INSERT INTO context_htf (
                signal_id, bias, bias_state, scenario,
                aligned_count, fractal_rank, leader_tf,
                htf_bonus, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            htf_row,
        )

        conn.commit()
        return signal_id

    except Exception as e:
        # NON-BLOQUANT : on log et on rend la main au moteur
        _log(f"ERREUR log_signal : {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return None



def insert_force_snapshot(conn: sqlite3.Connection | None, snapshot: dict) -> int | None:
    """
    Ins?re un snapshot de force brute.

    NON-BLOQUANT : toute exception est aval?e et logg?e.
    Retourne l'id ins?r?, ou None si ?chec / conn absente.
    """
    if conn is None:
        return None

    try:
        created_at = snapshot.get("created_at")
        if not created_at:
            created_at = datetime.now(timezone.utc).isoformat()

        row = (
            created_at,
            str(snapshot.get("symbol", "")).upper(),
            int(snapshot.get("timeframe", 0)),
            snapshot.get("bid"),
            snapshot.get("spread"),
            snapshot.get("force_gbp"),
            snapshot.get("force_usd"),
            snapshot.get("force_eur"),
            snapshot.get("force_jpy"),
            snapshot.get("force_cad"),
            snapshot.get("force_chf"),
            snapshot.get("force_aud"),
        )

        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO force_snapshots (
                created_at, symbol, timeframe, bid, spread,
                force_gbp, force_usd, force_eur, force_jpy,
                force_cad, force_chf, force_aud
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            row,
        )
        conn.commit()
        return cur.lastrowid

    except Exception as e:
        _log(f"ERREUR insert_force_snapshot : {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return None


# ---------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------

# Requête commune : signal + contexte HTF jointé (LEFT JOIN pour tolérer
# d'éventuels signaux sans HTF, même si en pratique il y en a toujours un).
_SELECT_JOIN = """
SELECT
    s.*,
    c.bias          AS htf_bias,
    c.bias_state    AS htf_bias_state,
    c.scenario      AS htf_scenario,
    c.aligned_count AS htf_aligned_count,
    c.fractal_rank  AS htf_fractal_rank,
    c.leader_tf     AS htf_leader_tf,
    c.htf_bonus     AS htf_bonus,
    c.details_json  AS htf_details_json
FROM signals s
LEFT JOIN context_htf c ON c.signal_id = s.id
"""


def _hydrate(row: sqlite3.Row) -> dict:
    """Transforme une row jointe en dict, en désérialisant details_json."""
    d = _row_to_dict(row)
    raw = d.pop("htf_details_json", None)
    try:
        d["htf_details"] = json.loads(raw) if raw else []
    except Exception:
        d["htf_details"] = []
    return d


def _safe_fetch(conn: sqlite3.Connection | None, sql: str, params: tuple) -> list[dict]:
    """Exécute une requête de lecture en avalant les exceptions."""
    if conn is None:
        return []
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        return [_hydrate(r) for r in cur.fetchall()]
    except Exception as e:
        _log(f"ERREUR fetch : {e}")
        return []


def get_last_signals(conn: sqlite3.Connection | None, limit: int = 20) -> list[dict]:
    """Retourne les N derniers signaux (plus récents d'abord), avec contexte HTF."""
    sql = _SELECT_JOIN + " ORDER BY s.id DESC LIMIT ?"
    return _safe_fetch(conn, sql, (int(limit),))


def get_signals_by_pair(
    conn: sqlite3.Connection | None,
    symbol: str,
    limit: int = 50,
) -> list[dict]:
    """Retourne les signaux filtrés par paire (symbol), plus récents d'abord."""
    sql = _SELECT_JOIN + " WHERE s.symbol = ? ORDER BY s.id DESC LIMIT ?"
    return _safe_fetch(conn, sql, (symbol, int(limit)))


def get_signals_by_type(
    conn: sqlite3.Connection | None,
    signal_type: str,
    limit: int = 50,
) -> list[dict]:
    """Retourne les signaux filtrés par type, plus récents d'abord."""
    sql = _SELECT_JOIN + " WHERE s.signal_type = ? ORDER BY s.id DESC LIMIT ?"
    return _safe_fetch(conn, sql, (signal_type, int(limit)))


def get_premium_signals(conn: sqlite3.Connection | None, limit: int = 20) -> list[dict]:
    """Retourne uniquement les signaux de niveau PREMIUM."""
    sql = _SELECT_JOIN + " WHERE s.level = 'PREMIUM' ORDER BY s.id DESC LIMIT ?"
    return _safe_fetch(conn, sql, (int(limit),))


# ---------------------------------------------------------------------------
# Exemple d'utilisation
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import time

    conn = init_db("powerflow.db")
    sig = {
        "symbol": "GBPUSD", "timeframe": 15, "signal_type": "CROSS",
        "timestamp": time.time(), "dev_strong": "gbp", "dev_weak": "usd",
        "score": 7, "level": "PREMIUM", "spread_ok": True,
        "volume_badge": "HIGH", "note": "Croisement propre M15", "price": 1.2734,
        "convergence": {"tf1": 15, "tf2": 60, "label1": "M15", "label2": "H1",
                        "niveau": "FORT", "bonus": 2, "delta": 0.8},
    }
    htf = {"bias": "GBP", "bias_state": "VALIDE", "scenario": "TENDANCE",
           "aligned_count": 4, "fractal_rank": 4, "leader": "M15",
           "details": ["M15 ✅", "M30 ✅", "H1 ✅", "H4 ❌"], "htf_bonus": 2}
    print("id inséré :", log_signal(conn, sig, htf))
    print("derniers :", get_last_signals(conn, limit=3))

# ---------------------------------------------------------------------------
# POWERFLOW EXTENDED SNAPSHOT V2 OVERRIDE
# ---------------------------------------------------------------------------
def insert_force_snapshot(conn: sqlite3.Connection | None, snapshot: dict) -> int | None:
    # Legacy table is kept stable for existing modules.
    # V2 table receives EA extended data when available.
    if conn is None:
        return None

    try:
        legacy_row = (
            str(snapshot.get("created_at") or datetime.now(timezone.utc).isoformat()),
            str(snapshot.get("symbol", "")).upper(),
            int(snapshot.get("timeframe", 0)),
            snapshot.get("bid"),
            snapshot.get("spread"),
            snapshot.get("force_gbp"),
            snapshot.get("force_usd"),
            snapshot.get("force_eur"),
            snapshot.get("force_jpy"),
            snapshot.get("force_cad"),
            snapshot.get("force_chf"),
            snapshot.get("force_aud"),
        )

        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO force_snapshots (
                created_at, symbol, timeframe, bid, spread,
                force_gbp, force_usd, force_eur, force_jpy,
                force_cad, force_chf, force_aud
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            legacy_row,
        )
        legacy_id = cur.lastrowid
        conn.commit()

    except Exception as e:
        _log(f"ERREUR insert_force_snapshot legacy: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return None

    try:
        v2_row = (
            str(snapshot.get("created_at") or datetime.now(timezone.utc).isoformat()),
            str(snapshot.get("symbol", "")).upper(),
            int(snapshot.get("timeframe", 0)),

            snapshot.get("bar_time"),
            snapshot.get("bar_close_time"),
            snapshot.get("server_time"),
            snapshot.get("capture_time"),
            _bool_to_int(snapshot.get("is_closed_bar")),

            snapshot.get("bid"),
            snapshot.get("ask"),
            snapshot.get("mid"),

            snapshot.get("spread"),
            snapshot.get("spread_points"),
            snapshot.get("spread_price"),
            snapshot.get("spread_pips"),

            snapshot.get("open"),
            snapshot.get("high"),
            snapshot.get("low"),
            snapshot.get("close"),
            snapshot.get("tick_volume"),

            snapshot.get("pip_range"),
            snapshot.get("pip_body"),
            snapshot.get("pip_change"),

            snapshot.get("force_gbp"),
            snapshot.get("force_usd"),
            snapshot.get("force_eur"),
            snapshot.get("force_jpy"),
            snapshot.get("force_cad"),
            snapshot.get("force_chf"),
            snapshot.get("force_aud"),
            snapshot.get("force_nzd"),
        )

        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR IGNORE INTO force_snapshots_v2 (
                created_at, symbol, timeframe,
                bar_time, bar_close_time, server_time, capture_time, is_closed_bar,
                bid, ask, mid,
                spread, spread_points, spread_price, spread_pips,
                open, high, low, close, tick_volume,
                pip_range, pip_body, pip_change,
                force_gbp, force_usd, force_eur, force_jpy,
                force_cad, force_chf, force_aud, force_nzd
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            v2_row,
        )
        conn.commit()

    except Exception as e:
        _log(f"WARN insert_force_snapshot_v2: {e}")
        try:
            conn.rollback()
        except Exception:
            pass

    return legacy_id

# ---------------------------------------------------------------------------
# POWERFLOW FORCE SNAPSHOT V2 ADAPTED INSERT - schema-aware override
# ---------------------------------------------------------------------------
def _snapshot_get_any(snapshot: dict, *keys: str, default=None):
    """Return first non-empty value among aliases."""
    for key in keys:
        try:
            value = snapshot.get(key)
        except Exception:
            value = None
        if value is not None and value != "":
            return value
    return default


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    """Return current SQLite table columns; empty set if table is missing."""
    try:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table_name})")
        return {str(row[1]) for row in cur.fetchall()}
    except Exception:
        return set()


def _insert_force_snapshot_legacy(conn: sqlite3.Connection, snapshot: dict) -> int | None:
    """Stable legacy insert into force_snapshots."""
    created_at = str(_snapshot_get_any(snapshot, "created_at", default=datetime.now(timezone.utc).isoformat()))
    row = (
        created_at,
        str(_snapshot_get_any(snapshot, "symbol", default="")).upper(),
        int(_snapshot_get_any(snapshot, "timeframe", "tf", default=0) or 0),
        _snapshot_get_any(snapshot, "bid"),
        _snapshot_get_any(snapshot, "spread", "spread_price", "spread_pips"),
        _snapshot_get_any(snapshot, "force_gbp", "gbp"),
        _snapshot_get_any(snapshot, "force_usd", "usd"),
        _snapshot_get_any(snapshot, "force_eur", "eur"),
        _snapshot_get_any(snapshot, "force_jpy", "jpy"),
        _snapshot_get_any(snapshot, "force_cad", "cad"),
        _snapshot_get_any(snapshot, "force_chf", "chf"),
        _snapshot_get_any(snapshot, "force_aud", "aud"),
    )
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO force_snapshots (
            created_at, symbol, timeframe, bid, spread,
            force_gbp, force_usd, force_eur, force_jpy,
            force_cad, force_chf, force_aud
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        row,
    )
    return cur.lastrowid


def insert_force_snapshot_v2_adapted(conn: sqlite3.Connection | None, snapshot: dict) -> int | None:
    """
    Insert EA extended force snapshot into force_snapshots_v2 with schema adaptation.

    Supports both known schemas:
    - legacy/core schema: timeframe, force_gbp, force_usd, ...
    - adapted/current schema: tf, tf_name, shift, gbp, usd, ...

    NON-BLOQUANT: returns None on failure and never crashes PowerFlow.
    """
    if conn is None:
        return None

    try:
        columns = _table_columns(conn, "force_snapshots_v2")
        if not columns:
            _log("WARN insert_force_snapshot_v2_adapted: force_snapshots_v2 table missing")
            return None

        created_at = str(_snapshot_get_any(snapshot, "created_at", default=datetime.now(timezone.utc).isoformat()))
        tf_value = int(_snapshot_get_any(snapshot, "tf", "timeframe", default=0) or 0)

        values_by_column = {
            "created_at": created_at,
            "symbol": str(_snapshot_get_any(snapshot, "symbol", default="")).upper(),
            "timeframe": tf_value,
            "tf": tf_value,
            "tf_name": _snapshot_get_any(snapshot, "tf_name", "timeframe_name"),
            "bar_time": _snapshot_get_any(snapshot, "bar_time"),
            "bar_close_time": _snapshot_get_any(snapshot, "bar_close_time"),
            "server_time": _snapshot_get_any(snapshot, "server_time"),
            "capture_time": _snapshot_get_any(snapshot, "capture_time"),
            "shift": _snapshot_get_any(snapshot, "shift"),
            "is_closed_bar": _bool_to_int(_snapshot_get_any(snapshot, "is_closed_bar", default=False)),
            "open": _snapshot_get_any(snapshot, "open"),
            "high": _snapshot_get_any(snapshot, "high"),
            "low": _snapshot_get_any(snapshot, "low"),
            "close": _snapshot_get_any(snapshot, "close"),
            "tick_volume": _snapshot_get_any(snapshot, "tick_volume"),
            "spread": _snapshot_get_any(snapshot, "spread"),
            "spread_points": _snapshot_get_any(snapshot, "spread_points"),
            "spread_price": _snapshot_get_any(snapshot, "spread_price"),
            "spread_pips": _snapshot_get_any(snapshot, "spread_pips"),
            "bid": _snapshot_get_any(snapshot, "bid"),
            "ask": _snapshot_get_any(snapshot, "ask"),
            "mid": _snapshot_get_any(snapshot, "mid"),
            "pip_range": _snapshot_get_any(snapshot, "pip_range"),
            "pip_body": _snapshot_get_any(snapshot, "pip_body"),
            "pip_change": _snapshot_get_any(snapshot, "pip_change"),
            "aud": _snapshot_get_any(snapshot, "aud", "force_aud"),
            "gbp": _snapshot_get_any(snapshot, "gbp", "force_gbp"),
            "jpy": _snapshot_get_any(snapshot, "jpy", "force_jpy"),
            "usd": _snapshot_get_any(snapshot, "usd", "force_usd"),
            "cad": _snapshot_get_any(snapshot, "cad", "force_cad"),
            "eur": _snapshot_get_any(snapshot, "eur", "force_eur"),
            "chf": _snapshot_get_any(snapshot, "chf", "force_chf"),
            "nzd": _snapshot_get_any(snapshot, "nzd", "force_nzd"),
            "force_aud": _snapshot_get_any(snapshot, "force_aud", "aud"),
            "force_gbp": _snapshot_get_any(snapshot, "force_gbp", "gbp"),
            "force_jpy": _snapshot_get_any(snapshot, "force_jpy", "jpy"),
            "force_usd": _snapshot_get_any(snapshot, "force_usd", "usd"),
            "force_cad": _snapshot_get_any(snapshot, "force_cad", "cad"),
            "force_eur": _snapshot_get_any(snapshot, "force_eur", "eur"),
            "force_chf": _snapshot_get_any(snapshot, "force_chf", "chf"),
            "force_nzd": _snapshot_get_any(snapshot, "force_nzd", "nzd"),
        }

        preferred_order = [
            "created_at", "symbol", "timeframe", "tf", "tf_name",
            "bar_time", "bar_close_time", "server_time", "capture_time", "shift", "is_closed_bar",
            "open", "high", "low", "close", "tick_volume",
            "bid", "ask", "mid", "spread", "spread_points", "spread_price", "spread_pips",
            "pip_range", "pip_body", "pip_change",
            "aud", "gbp", "jpy", "usd", "cad", "eur", "chf", "nzd",
            "force_aud", "force_gbp", "force_jpy", "force_usd", "force_cad", "force_eur", "force_chf", "force_nzd",
        ]

        insert_cols = [c for c in preferred_order if c in columns and c in values_by_column]
        if "symbol" not in insert_cols and "symbol" in columns:
            insert_cols.append("symbol")
        if "created_at" in columns and "created_at" not in insert_cols:
            insert_cols.insert(0, "created_at")

        sql = "INSERT OR IGNORE INTO force_snapshots_v2 (" + ", ".join(insert_cols) + ") VALUES (" + ", ".join(["?"] * len(insert_cols)) + ")"
        row = tuple(values_by_column.get(c) for c in insert_cols)
        cur = conn.cursor()
        cur.execute(sql, row)
        conn.commit()
        return cur.lastrowid

    except Exception as e:
        _log(f"ERREUR insert_force_snapshot_v2_adapted: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return None


def insert_force_snapshot(conn: sqlite3.Connection | None, snapshot: dict) -> int | None:
    """
    Schema-aware force snapshot insert.

    Writes legacy force_snapshots when the table exists, then writes adapted
    force_snapshots_v2. Returns the legacy id when inserted, else the v2 id.
    NON-BLOQUANT: DB errors never crash PowerFlow.
    """
    if conn is None:
        return None

    legacy_id = None
    try:
        if _table_columns(conn, "force_snapshots"):
            legacy_id = _insert_force_snapshot_legacy(conn, snapshot)
            conn.commit()
    except Exception as e:
        _log(f"WARN insert_force_snapshot legacy: {e}")
        try:
            conn.rollback()
        except Exception:
            pass

    v2_id = insert_force_snapshot_v2_adapted(conn, snapshot)
    return legacy_id if legacy_id is not None else v2_id
