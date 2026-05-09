#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V6 — cockpit_reader.py (FLASK VERSION)

Serveur Flask du Cockpit PowerFlow V6.
Fournit les routes API pour le terminal et l'UI web.

Routes:
  GET /api/temporal-nodes?symbol=GBPUSD&mode=live&tf=1,5,15
  GET /api/cockpit-state?symbol=GBPUSD
  GET /api/health
  GET / → HTML cockpit
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from collections import Counter
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from flask import Flask, jsonify, request

import pf_normalizer as alignment_mod

try:
    import pf_flow_nodes as flow_nodes_mod
except Exception:
    flow_nodes_mod = None

from pf_memory import (
    atomic_write_json,
    ensure_output_dir,
    load_previous_state,
    append_state_history,
    compare_cockpit_states,
)

# Import temporal nodes detector
try:
    from pf_temporal_nodes import get_temporal_nodes_for_engine
except ImportError:
    get_temporal_nodes_for_engine = None

# ============================================================
# FLASK APP SETUP
# ============================================================

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# ============================================================
# CONSTANTES
# ============================================================

VERSION = "COCKPIT_V6.0"

SIGNALS_DECLENCHEURS = {
    "CROSS", "SUPER_SWITCH", "KISS_REJECT",
    "COMPRESSION_BREAK", "COMPRESSION_SQUEEZE",
}

SIGNALS_FILTRES_NEG = {"FAKEOUT"}

SIGNALS_MICROFILM = {
    "COMPRESSION", "SLINGSHOT_A", "SLINGSHOT_B",
    "APPROACH", "ZONE_BATTLE", "CONVERGENCE",
    "EXTREME_HIGH", "EXTREME_LOW",
}

SCENES_CONFIRMATIVES = {
    "COALITION_PUSH", "TREND_CONTINUATION",
    "COMPRESSION_RELEASE", "ROTATION_BUILDING",
    "OPPOSITION_REBALANCE",
}

SCENES_NEUTRES = {
    "CENTER_BATTLE", "COMPRESSION_BUILD",
    "CHAOS_NO_TRADE", "NEGATIVE_MIRROR_SYNC",
}

INTEREST_RANK = {
    "IGNORE":             0,
    "WATCH_ZONE":         1,
    "STRUCTURE_BUILDING": 2,
    "TACTICAL_READY":     3,
    "SIGNAL_VALIDATED":   4,
}

INTEREST_ICON = {
    "IGNORE":             "⚪",
    "WATCH_ZONE":         "🔵",
    "STRUCTURE_BUILDING": "🟡",
    "TACTICAL_READY":     "🟠",
    "SIGNAL_VALIDATED":   "🔴",
}

TF_LABELS = {1:"M1", 5:"M5", 15:"M15", 30:"M30", 60:"H1", 240:"H4", 1440:"D1", 10080:"W1"}

DB_FRESH_SEC = 5 * 60
DB_AGING_SEC = 20 * 60

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone() is not None


def _col_exists(conn: sqlite3.Connection, table: str, col: str) -> bool:
    try:
        cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return any(c[1] == col for c in cols)
    except Exception:
        return False


def get_recent_signals(db_path: str, symbol: str, limit: int = 30) -> List[Dict]:
    """Lit les signaux récents pour un symbole depuis la table signals."""
    if not os.path.exists(db_path):
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        if not _table_exists(conn, "signals"):
            return []
        has_context = _table_exists(conn, "context_htf")
        has_created = _col_exists(conn, "signals", "created_at")
        order_col   = "created_at" if has_created else "id"
        sym_filter  = f"WHERE s.symbol = '{symbol.upper()}'"

        if has_context:
            rows = conn.execute(f"""
                SELECT s.created_at, s.symbol, s.timeframe, s.signal_type,
                       s.dev_strong, s.dev_weak, s.score, s.level,
                       COALESCE(c.bias,'NA') AS bias,
                       COALESCE(c.bias_state,'NA') AS bias_state,
                       COALESCE(c.scenario,'NA') AS scenario,
                       COALESCE(c.aligned_count,0) AS aligned_count,
                       COALESCE(c.fractal_rank,0) AS fractal_rank,
                       COALESCE(c.leader_tf,'NA') AS leader_tf
                FROM signals s
                LEFT JOIN context_htf c ON c.signal_id = s.id
                {sym_filter}
                ORDER BY s.{order_col} DESC LIMIT ?
            """, (limit,)).fetchall()
        else:
            rows = conn.execute(f"""
                SELECT created_at, symbol, timeframe, signal_type,
                       dev_strong, dev_weak, score, level
                FROM signals s
                {sym_filter}
                ORDER BY {order_col} DESC LIMIT ?
            """, (limit,)).fetchall()

        return [dict(r) for r in rows]
    except Exception as e:
        return [{"error": str(e)}]
    finally:
        conn.close()


def get_db_age_seconds(db_path: str, symbol: str) -> Optional[int]:
    """Retourne l'âge en secondes du dernier snapshot force pour ce symbole."""
    if not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    try:
        if not _table_exists(conn, "force_snapshots"):
            return None
        row = conn.execute(
            "SELECT created_at FROM force_snapshots WHERE symbol=? ORDER BY datetime(created_at) DESC LIMIT 1",
            (symbol.upper(),)
        ).fetchone()
        if not row or not row[0]:
            return None
        dt = datetime.fromisoformat(str(row[0]).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0, int((datetime.now(timezone.utc) - dt).total_seconds()))
    except Exception:
        return None
    finally:
        conn.close()


def db_freshness_label(age_sec: Optional[int]) -> str:
    if age_sec is None:
        return "UNKNOWN"
    if age_sec <= DB_FRESH_SEC:
        return "FRESH"
    if age_sec <= DB_AGING_SEC:
        return "AGING"
    return "STALE"


# ============================================================
# FLASK ROUTES
# ============================================================

@app.route('/', methods=['GET'])
def index():
    """Serve cockpit HTML."""
    try:
        with open('cockpit_ui_web.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>cockpit_ui_web.html not found</h1>", 404


@app.route('/api/temporal-nodes', methods=['GET'])
def get_temporal_nodes_api():
    """
    GET /api/temporal-nodes?symbol=GBPUSD&mode=live&tf=1,5,15,30,60

    Retourne JSON avec nodes_by_tf, summary, fractal_alignment.
    """
    if not get_temporal_nodes_for_engine:
        return jsonify({
            "error": "pf_temporal_nodes module not available",
            "status": "error"
        }), 500

    try:
        symbol         = request.args.get('symbol', 'GBPUSD')
        mode           = request.args.get('mode', 'live')
        timeframes_str = request.args.get('tf', '1,5,15,30,60')
        db_path        = request.args.get('db', 'powerflow.db')

        timeframes = [int(t.strip()) for t in timeframes_str.split(',')]

        nodes_data = get_temporal_nodes_for_engine(
            db_path=db_path,
            symbol=symbol,
            timeframes=timeframes,
            mode=mode
        )

        return jsonify(nodes_data), 200

    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500


@app.route('/api/temporal-nodes/health', methods=['GET'])
def temporal_nodes_health():
    """Health check pour API Temporal Nodes."""
    return jsonify({
        "status": "ok",
        "service": "temporal_nodes_api",
        "version": "1.0"
    }), 200


@app.route('/api/cockpit-state', methods=['GET'])
def get_cockpit_state():
    """
    GET /api/cockpit-state?symbol=GBPUSD

    Retourne l'état Cockpit V6 : signaux, alignement, fraîcheur DB.
    """
    try:
        symbol  = request.args.get('symbol', 'GBPUSD').upper()
        db_path = request.args.get('db', 'powerflow.db')

        sig_rows   = get_recent_signals(db_path, symbol, limit=40)
        db_age_sec = get_db_age_seconds(db_path, symbol)
        freshness  = db_freshness_label(db_age_sec)

        tfs = [1, 5, 15, 30, 60]
        try:
            alignment = alignment_mod.detect_tf_alignment(
                symbol=symbol,
                timeframes=tfs,
                db_path=db_path,
                bars=25,
                devises_arg="eur,gbp,usd",
            )
        except Exception:
            alignment = {"verdict": "ERROR", "aligned_tfs": [], "conflict_tfs": []}

        return jsonify({
            "symbol":          symbol,
            "freshness":       freshness,
            "db_age_seconds":  db_age_sec,
            "signals_count":   len(sig_rows),
            "alignment":       alignment.to_dict() if hasattr(alignment, "to_dict") else (alignment if isinstance(alignment, dict) else {"error": "alignment error"}),
        }), 200

    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check — API is alive."""
    return jsonify({
        "status":  "ok",
        "service": "cockpit_reader",
        "version": VERSION,
    }), 200


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("🚀 Starting PowerFlow V6 Cockpit Server")
    logger.info("📊 Routes disponibles :")
    logger.info("   GET /                      → HTML Cockpit")
    logger.info("   GET /api/temporal-nodes    → Temporal Nodes API")
    logger.info("   GET /api/cockpit-state     → Cockpit V6 State")
    logger.info("   GET /api/temporal-nodes/health → Health Nodes")
    logger.info("   GET /api/health            → Health check")
    logger.info("")
    logger.info("🌐 http://localhost:8880")

    app.run(host='localhost', port=8880, debug=False, threaded=True)