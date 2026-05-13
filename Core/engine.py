# ============================================================
# PowerFlow V5 — engine.py
# Moteur de détection — adapté config V5
#
# Changements vs V3 :
#  - ZERO valeur hardcodée de seuil
#  - get_level_high/low(tf), get_kiss_frolement(tf), get_kiss_force_rejet(tf)
#  - get_fakeout_delay(tf), get_fakeout_gap(tf), get_marge_croisement(tf)
#  - LVL_SURCHAUFFE / LVL_SURVENTE → fonctions dynamiques par TF
#  - Noms de variables anciens supprimés (COMPRESSION_ATR_FACTOR etc)
# ============================================================

import time
import os
import json
from datetime import datetime, timezone
from collections import deque, defaultdict
from models import Tick, HTFContext, Signal, Brain
from system_config import (
    HTF_RADAR_ENABLED,
    VOLUME_FILTER_ENABLED, VOLUME_SPIKE_RATIO, VOLUME_SPIKE_MIN_TICKS,
    MAX_SPREAD, ANTISPAM_SECONDS,
    ALERT_CROSS_BASIC, ALERT_SUPER_SWITCH,
    ALERT_FAKEOUT, ALERT_SNIPER_REVERSAL,
    ALERT_CONVERGENCE, ALERT_SLINGSHOT,
    ALERT_EXTREME_LEVELS, ALERT_KISS_REJECT,
    ALERT_COMPRESSION, ALERT_COMPRESSION_SQUEEZE,
    DEBUG_CROSS, DEBUG_CONVERGENCE, TIMEFRAMES,
    # V5 : helpers dynamiques par TF
    get_level_high, get_level_low,
    get_kiss_frolement, get_kiss_force_rejet,
    get_fakeout_delay, get_fakeout_gap,
    get_marge_croisement,
    # Seuils compression V5
    COMPRESSION_THRESHOLD, COMPRESSION_MIN_BARS,
    LIBERATION_THRESHOLD, LIBERATION_MAX_BARS,
    PENTE_THRESHOLD, CROSS_MIN_DELTA,
    LOCK_DOMINANT_MIN, LOCK_OTHERS_MAX, LOCK_MIN_BARS,
)
from db import init_db, log_signal

# Module C — Temporal Nodes Integration (optionnel)
try:
    from pf_temporal_nodes import get_temporal_nodes_for_engine
    from engine_temporal_nodes import process_temporal_nodes_for_engine
    from telegram_v6 import send_temporal_node_alert
    TEMPORAL_NODES_ENABLED = True
except ImportError:
    TEMPORAL_NODES_ENABLED = False

DB_CONN = init_db("powerflow.db")

# ============================================================
# SCORES DE BASE
# ============================================================
BASE_SCORES = {
    "SNIPER_REVERSAL":       4,
    "SUPER_SWITCH":          4,
    "CONVERGENCE":           3,
    "KISS_REJECT":           3,
    "FAKEOUT":               3,
    "SLINGSHOT":             3,
    "COMPRESSION":           2,
    "COMPRESSION_BREAK":     3,
    "COMPRESSION_SQUEEZE":   4,
    "CROSS":                 1,
    "EXTREME_HIGH":          2,
    "EXTREME_LOW":           2,
}

# ============================================================
# MÉMOIRES GLOBALES
# ============================================================
cross_states         = {}
antispam             = {}
vol_history          = defaultdict(lambda: deque(maxlen=30))
recent_crosses       = {}
convergence_antispam = {}
slingshot_states     = {}
slingshot_sequence   = {}
approach_states      = {}
zone_battle_states   = {}
compression_states   = {}
squeeze_states       = {}
time_compression_states = {}

TF_LABELS = {1: "M1", 5: "M5", 15: "M15", 30: "M30", 60: "H1", 240: "H4"}


# ============================================================
# LEGACY BEHAVIORAL BUS V7
# ============================================================
def _pfv7_utc_iso(dt) -> str:
    """Normalize datetime-like values to UTC ISO string for V7 proof traces."""
    try:
        if dt is None:
            return datetime.now(timezone.utc).isoformat()
        if hasattr(dt, "tzinfo"):
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        return str(dt)
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def _pfv7_symbol_dir(symbol: str) -> str:
    out_dir = os.path.join("output", "dashboard_surface", str(symbol).upper())
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def _pfv7_behavioral_jsonl_path(symbol: str) -> str:
    return os.path.join(_pfv7_symbol_dir(symbol), "legacy_behavioral_events.jsonl")


def _pfv7_timecomp_jsonl_path(symbol: str) -> str:
    return os.path.join(_pfv7_symbol_dir(symbol), "legacy_timecomp_events.jsonl")


def _pfv7_event_time_risks(event_at: str, detected_at: str) -> list[str]:
    risks: list[str] = []
    try:
        ea = datetime.fromisoformat(str(event_at).replace("Z", "+00:00"))
        da = datetime.fromisoformat(str(detected_at).replace("Z", "+00:00"))
        if ea.tzinfo is None:
            ea = ea.replace(tzinfo=timezone.utc)
        if da.tzinfo is None:
            da = da.replace(tzinfo=timezone.utc)
        delta = (ea.astimezone(timezone.utc) - da.astimezone(timezone.utc)).total_seconds()
        if delta > 120:
            risks.append("EVENT_TIME_AHEAD_OF_DETECTED_AT")
        elif delta < -7200:
            risks.append("EVENT_TIME_STALE_VS_DETECTED_AT")
    except Exception:
        risks.append("EVENT_TIME_PARSE_UNCLEAR")
    return risks


def _pfv7_signal_layer(signal_type: str) -> str:
    st = str(signal_type or "").upper()
    if st in {"TIME_COMP_LOCK", "TIME_COMP_BREAK"}:
        return "TEMPORAL"
    if st in {"COMPRESSION", "COMPRESSION_BREAK", "COMPRESSION_SQUEEZE"}:
        return "ENERGY"
    if st in {"SLINGSHOT", "APPROACH", "CROSS", "CONVERGENCE", "SUPER_SWITCH", "FAKEOUT"}:
        return "TACTICAL"
    if st in {"KISS_REJECT", "EXTREME_HIGH", "EXTREME_LOW"}:
        return "ZONE_REACTION"
    return "LEGACY"


def _pfv7_event_role(signal_type: str) -> str:
    st = str(signal_type or "").upper()
    return {
        "TIME_COMP_LOCK": "TEMPORAL_LOCK",
        "TIME_COMP_BREAK": "TEMPORAL_RELEASE",
        "SLINGSHOT": "TACTICAL_REARM_RELEASE",
        "KISS_REJECT": "ZONE_REPULSION",
        "COMPRESSION": "ELASTIC_LOADING_LEGACY",
        "COMPRESSION_BREAK": "ELASTIC_RELEASE_LEGACY",
        "COMPRESSION_SQUEEZE": "PRESSURE_SQUEEZE",
        "APPROACH": "CROSS_OR_REJECT_IMMINENT",
        "EXTREME_HIGH": "ZONE_PRESSURE_HIGH",
        "EXTREME_LOW": "ZONE_PRESSURE_LOW",
        "FAKEOUT": "TRAP_OR_REINTEGRATION",
        "SUPER_SWITCH": "FORCE_SWITCH",
        "CONVERGENCE": "MULTI_TF_CONVERGENCE",
        "CROSS": "DOMINANCE_CROSS",
    }.get(st, st or "UNKNOWN")


def _pfv7_pair_bias_from_signal(sig) -> str:
    try:
        symbol = str(getattr(sig, "symbol", "")).upper()
        strong = str(getattr(sig, "dev_strong", "")).upper()
        weak = str(getattr(sig, "dev_weak", "")).upper()
        if len(symbol) >= 6 and strong and weak:
            base = symbol[:3]
            quote = symbol[3:6]
            if strong == base and weak == quote:
                return "PAIR_UP"
            if strong == quote and weak == base:
                return "PAIR_DOWN"
    except Exception:
        pass
    return "UNKNOWN"


def _pfv7_write_jsonl(path: str, record: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _write_legacy_behavioral_event(record: dict) -> dict:
    """Append one V7 legacy behavioral proof record."""
    try:
        symbol = str(record.get("symbol", "UNKNOWN")).upper()
        event_at = str(record.get("event_at") or datetime.now(timezone.utc).isoformat())
        detected_at = str(record.get("detected_at") or datetime.now(timezone.utc).isoformat())
        risks = list(record.get("technical_risks") or [])
        for risk in _pfv7_event_time_risks(event_at, detected_at):
            if risk not in risks:
                risks.append(risk)
        record["technical_risks"] = risks
        record.setdefault("source", "legacy_engine")
        record.setdefault("method", "LEGACY_BEHAVIORAL_BUS_V7A")
        _pfv7_write_jsonl(_pfv7_behavioral_jsonl_path(symbol), record)
    except Exception as exc:
        print(f"[engine] legacy behavioral bus ignored: {exc}")
    return record


def _write_legacy_behavioral_signal(sig, htf=None, tick=None) -> dict:
    """Mirror an existing legacy Signal into V7 JSONL. Does not affect alert flow."""
    detected_at = datetime.now(timezone.utc).isoformat()
    event_at = _pfv7_utc_iso(getattr(sig, "timestamp", None) or getattr(tick, "timestamp", None))
    signal_type = str(getattr(sig, "signal_type", "UNKNOWN")).upper()
    symbol = str(getattr(sig, "symbol", getattr(tick, "symbol", "UNKNOWN"))).upper()
    tf = int(getattr(sig, "timeframe", getattr(tick, "timeframe", 0)) or 0)
    tf_label = TF_LABELS.get(tf, f"M{tf}")
    record = {
        "source": "legacy_engine",
        "method": "LEGACY_BEHAVIORAL_BUS_V7A",
        "symbol": symbol,
        "timeframe": tf,
        "tf_label": tf_label,
        "event": signal_type,
        "event_role": _pfv7_event_role(signal_type),
        "layer": _pfv7_signal_layer(signal_type),
        "event_at": event_at,
        "detected_at": detected_at,
        "bias": _pfv7_pair_bias_from_signal(sig),
        "score_hint": getattr(sig, "score", None),
        "level": getattr(sig, "level", None),
        "price": getattr(sig, "price", None) or getattr(tick, "bid", None),
        "dev_strong": getattr(sig, "dev_strong", None),
        "dev_weak": getattr(sig, "dev_weak", None),
        "spread_ok": getattr(sig, "spread_ok", None),
        "volume_badge": getattr(sig, "volume_badge", None),
        "note": getattr(sig, "note", ""),
        "htf_bias": getattr(htf, "bias", None),
        "htf_bias_state": getattr(htf, "bias_state", None),
        "htf_scenario": getattr(htf, "scenario", None),
        "technical_risks": [],
    }
    return _write_legacy_behavioral_event(record)


def _pfv7_timecomp_event_type(tc_ev: dict) -> str:
    phase = str(tc_ev.get("phase", "")).upper()
    if phase == "LOCK":
        return "TIME_COMP_LOCK"
    if phase == "BREAK":
        return "TIME_COMP_BREAK"
    return f"TIME_COMP_{phase or 'UNKNOWN'}"


def _pfv7_timecomp_direction(tc_ev: dict) -> str:
    if str(tc_ev.get("phase", "")).upper() != "BREAK":
        return "NONE"
    try:
        start = float(tc_ev.get("from_bid", tc_ev.get("center", 0.0)) or 0.0)
        end = float(tc_ev.get("bid", 0.0) or 0.0)
        if end > start:
            return "PAIR_UP"
        if end < start:
            return "PAIR_DOWN"
    except Exception:
        pass
    return "UNKNOWN"


def _write_legacy_timecomp_event_v7bus(symbol: str, tf: int, tf_label: str, tick: Tick, tc_ev: dict) -> dict:
    """Write TIME-COMP into both dedicated temporal JSONL and common behavioral bus."""
    event_at = _pfv7_utc_iso(getattr(tick, "timestamp", None))
    detected_at = datetime.now(timezone.utc).isoformat()
    phase = str(tc_ev.get("phase", "")).upper()
    event_name = _pfv7_timecomp_event_type(tc_ev)
    direction = _pfv7_timecomp_direction(tc_ev)
    price_from = tc_ev.get("from_bid", tc_ev.get("center"))
    price_to = tc_ev.get("bid")
    risks = _pfv7_event_time_risks(event_at, detected_at)

    temporal = {
        "source": "legacy_engine",
        "method": "LEGACY_TIMECOMP_BRIDGE_V7A",
        "layer": "TEMPORAL",
        "symbol": str(symbol).upper(),
        "timeframe": int(tf),
        "tf_label": tf_label,
        "event": event_name,
        "phase": phase,
        "direction": direction,
        "event_at": event_at,
        "detected_at": detected_at,
        "price_from": price_from,
        "price_to": price_to,
        "center": tc_ev.get("center"),
        "band": tc_ev.get("band"),
        "ticks": tc_ev.get("ticks"),
        "bid": tc_ev.get("bid"),
        "from_bid": tc_ev.get("from_bid"),
        "technical_risks": risks,
    }
    try:
        _pfv7_write_jsonl(_pfv7_timecomp_jsonl_path(symbol), temporal)
    except Exception as exc:
        print(f"[engine] legacy timecomp jsonl ignored: {exc}")

    behavioral = dict(temporal)
    behavioral.update({
        "method": "LEGACY_BEHAVIORAL_BUS_V7A",
        "event_role": _pfv7_event_role(event_name),
        "bias": direction if direction in ("PAIR_UP", "PAIR_DOWN") else "UNKNOWN",
        "score_hint": 2.0 if phase == "LOCK" else 3.5,
        "price": price_to,
        "note": f"TIME-COMP {phase} {tf_label} ticks={tc_ev.get('ticks')}",
    })
    _write_legacy_behavioral_event(behavioral)
    return temporal


# ============================================================
# LEGACY TIME-COMP → V7 TEMPORAL BRIDGE
# ============================================================
def _utc_iso(dt) -> str:
    """Normalize datetime-like values to UTC ISO string."""
    if dt is None:
        return datetime.now(timezone.utc).isoformat()
    try:
        if hasattr(dt, "tzinfo"):
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        pass
    try:
        return str(dt)
    except Exception:
        return datetime.now(timezone.utc).isoformat()

def _legacy_timecomp_event_type(tc_ev: dict) -> str:
    phase = str(tc_ev.get("phase", "")).upper()
    if phase == "LOCK":
        return "TIME_COMP_LOCK"
    if phase == "BREAK":
        return "TIME_COMP_BREAK"
    return f"TIME_COMP_{phase or 'UNKNOWN'}"

def _legacy_timecomp_direction(tc_ev: dict) -> str:
    if str(tc_ev.get("phase", "")).upper() != "BREAK":
        return "NONE"
    try:
        start = float(tc_ev.get("from_bid", tc_ev.get("center", 0.0)) or 0.0)
        end = float(tc_ev.get("bid", 0.0) or 0.0)
        if end > start:
            return "PAIR_UP"
        if end < start:
            return "PAIR_DOWN"
    except Exception:
        pass
    return "UNKNOWN"

def _legacy_timecomp_jsonl_path(symbol: str) -> str:
    out_dir = os.path.join("output", "dashboard_surface", symbol.upper())
    os.makedirs(out_dir, exist_ok=True)
    return os.path.join(out_dir, "legacy_timecomp_events.jsonl")

def _write_legacy_timecomp_event(symbol: str, tf: int, tf_label: str, tick: Tick, tc_ev: dict) -> dict:
    """Write one legacy TIME-COMP event as a V7-readable JSONL proof.

    This does not change the legacy detection. It only turns console perception
    into a TEMPORAL proof consumable by V7 readers / Spine.
    """
    event_at = _utc_iso(getattr(tick, "timestamp", None))
    detected_at = datetime.now(timezone.utc).isoformat()
    phase = str(tc_ev.get("phase", "")).upper()
    direction = _legacy_timecomp_direction(tc_ev)

    price_from = tc_ev.get("from_bid", tc_ev.get("center"))
    price_to = tc_ev.get("bid")

    event = {
        "source": "legacy_engine",
        "layer": "TEMPORAL",
        "symbol": symbol.upper(),
        "timeframe": int(tf),
        "tf_label": tf_label,
        "event": _legacy_timecomp_event_type(tc_ev),
        "phase": phase,
        "direction": direction,
        "event_at": event_at,
        "detected_at": detected_at,
        "price_from": price_from,
        "price_to": price_to,
        "center": tc_ev.get("center"),
        "band": tc_ev.get("band"),
        "ticks": tc_ev.get("ticks"),
        "bid": tc_ev.get("bid"),
        "from_bid": tc_ev.get("from_bid"),
        "technical_risks": [],
    }

    path = _legacy_timecomp_jsonl_path(symbol)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return event


# ============================================================
# MAPPING Signal / HTFContext → DB
# ============================================================
def signal_to_db_dict(sig) -> dict:
    return {
        "symbol":               getattr(sig, "symbol", ""),
        "timeframe":            getattr(sig, "timeframe", 0),
        "signal_type":          getattr(sig, "signal_type", ""),
        "timestamp":            getattr(sig, "timestamp", None),
        "dev_strong":           getattr(sig, "dev_strong", ""),
        "dev_weak":             getattr(sig, "dev_weak", ""),
        "score":                getattr(sig, "score", 0),
        "level":                getattr(sig, "level", "STANDARD"),
        "spread_ok":            getattr(sig, "spread_ok", False),
        "volume_badge":         getattr(sig, "volume_badge", None),
        "note":                 getattr(sig, "note", ""),
        "convergence":          getattr(sig, "convergence", None),
        "price":                getattr(sig, "price", None),
        "is_post_extreme":      getattr(sig, "is_post_extreme", False),
        "post_extreme_side":    getattr(sig, "post_extreme_side", None),
        "is_slingshot_sequence": getattr(sig, "is_slingshot_sequence", False),
    }

def htf_to_db_dict(htf) -> dict:
    if htf is None:
        return {}
    return {
        "bias":          getattr(htf, "bias", None),
        "bias_state":    getattr(htf, "bias_state", None),
        "scenario":      getattr(htf, "scenario", None),
        "aligned_count": getattr(htf, "aligned_count", 0),
        "fractal_rank":  getattr(htf, "fractal_rank", 0),
        "leader":        getattr(htf, "leader", None),
        "details":       getattr(htf, "details", []),
        "htf_bonus":     getattr(htf, "htf_bonus", 0),
    }

def persist_signal(sig, htf) -> None:
    label = (f"{getattr(sig,'signal_type','?')} "
             f"{getattr(sig,'symbol','?')} M{getattr(sig,'timeframe','?')}")
    try:
        if DB_CONN is None:
            print(f"[DB KO] {label} | DB_CONN=None")
            return
        before = DB_CONN.total_changes
        log_signal(DB_CONN, signal_to_db_dict(sig), htf_to_db_dict(htf))
        delta = DB_CONN.total_changes - before
        print(f"[DB {'OK' if delta>0 else '?'}] {label} | +{delta}")
    except Exception as e:
        print(f"[DB KO] {label} | {e}")

def log_flow_regime(htf, sig) -> None:
    return  # observation désactivée

# ============================================================
# VOLUME
# ============================================================
def check_volume(tick: Tick, uid: str) -> str:
    if not VOLUME_FILTER_ENABLED:
        return ""
    vol_now = getattr(tick, "volume", 0)
    key  = f"{uid}_volhist"
    hist = vol_history[key]
    hist.append(vol_now)
    avg = sum(hist) / len(hist) if hist else 1
    if avg <= 0:
        avg = 1
    if vol_now > avg * VOLUME_SPIKE_RATIO and vol_now > VOLUME_SPIKE_MIN_TICKS:
        last = vol_history.get(f"{uid}_lastspike", 0)
        if isinstance(last, deque):
            last = 0
        if time.time() - last > 180:
            vol_history[f"{uid}_lastspike"] = time.time()
            return "💰 SMART MONEY — Injection massive détectée !"
    return ""

# ============================================================
# HTF RADAR
# ============================================================
def build_htf_context(pair, tf, dev_a, dev_b, brain) -> HTFContext:
    if not HTF_RADAR_ENABLED:
        return HTFContext(bias="NEUTRAL", bias_state="NA",
                         aligned_count=0, htf_bonus=0,
                         leader="NA", fractal_rank=0, scenario="NA", details=[])
    map_sup = {
        1:   [(5,"M5"),(15,"M15"),(30,"M30"),(60,"H1"),(240,"H4")],
        5:   [(15,"M15"),(30,"M30"),(60,"H1"),(240,"H4")],
        15:  [(30,"M30"),(60,"H1"),(240,"H4")],
        30:  [(60,"H1"),(240,"H4")],
        60:  [(240,"H4")],
        240: [],
    }
    superiors = map_sup.get(tf, [])
    aligned, details, leader, dominant_bias = 0, [], "NA", "NEUTRAL"
    for tf_num, tf_name in superiors:
        key = f"{pair}M{tf_num}"
        if key not in brain:
            details.append(f"{tf_name} ⬜"); continue
        t = brain[key]
        dom = dev_a if t.val_a >= t.val_b else dev_b
        if dom == dev_a:
            aligned += 1
            details.append(f"{tf_name} ✅")
            if leader == "NA":
                leader, dominant_bias = tf_name, dev_a
        else:
            details.append(f"{tf_name} ❌")
    total = len(superiors)
    bonus = 3 if aligned >= 4 else (2 if aligned >= 3 else (1 if aligned >= 2 else 0))
    fractal_rank = round((aligned / total) * 5) if total > 0 else 0
    bias_state = ("VALIDE" if aligned == total and total > 0
                  else ("CONTRE" if aligned == 0 else "MIXTE"))
    scenario = ("TENDANCE" if fractal_rank >= 4
                else ("RANGE" if fractal_rank >= 2 else "RETOURNEMENT"))
    return HTFContext(
        bias=dominant_bias.upper() if dominant_bias != "NEUTRAL" else "NEUTRAL",
        bias_state=bias_state, aligned_count=aligned, htf_bonus=bonus,
        leader=leader, fractal_rank=fractal_rank, scenario=scenario, details=details,
    )

# ============================================================
# SCORING
# ============================================================
def score_signal(signal_type, tf, volume_badge, htf_bonus, spread_ok) -> tuple:
    score = BASE_SCORES.get(signal_type, 1)
    if volume_badge: score += 3
    score += htf_bonus
    score += (1 if spread_ok else -2)
    if tf == 1 and signal_type == "CROSS":
        score -= 1
    level = "PREMIUM" if score >= 8 else ("CONFIRM" if score >= 5 else "STANDARD")
    return score, level

# ============================================================
# ANTI-SPAM
# ============================================================
def can_alert(key):
    return time.time() - antispam.get(key, 0) > ANTISPAM_SECONDS

def mark_alerted(key):
    antispam[key] = time.time()

# ============================================================
# CONVERGENCE DOUBLE
# ============================================================
CONVERGENCE_WINDOWS = {
    (1,5):10, (1,15):20, (5,15):20, (5,30):30,
    (15,30):30, (15,60):45,
}

def register_cross(pair, tf, strong, weak):
    key = f"{pair}M{tf}"
    recent_crosses[key] = {"pair":pair,"tf":tf,"strong":strong,"weak":weak,"ts":time.time()}
    to_del = [k for k,v in recent_crosses.items() if time.time()-v["ts"]>7200]
    for k in to_del: del recent_crosses[k]

def detect_convergence(pair, tf, strong, weak, htf):
    now = time.time()
    candidates = []
    for _, rec in recent_crosses.items():
        if rec["pair"]!=pair or rec["tf"]==tf: continue
        if rec["strong"]!=strong or rec["weak"]!=weak: continue
        pair_tfs = tuple(sorted([tf, rec["tf"]]))
        window   = CONVERGENCE_WINDOWS.get(pair_tfs, 15)
        delta    = abs(now - rec["ts"]) / 60.0
        if delta < window:
            candidates.append({"tf_other": rec["tf"], "delta": delta})
    if not candidates: return None
    best = sorted(candidates, key=lambda x: x["delta"])[0]
    tf1, tf2 = min(tf, best["tf_other"]), max(tf, best["tf_other"])
    if max(tf1,tf2)>=30 and htf.bias_state=="VALIDE" and htf.fractal_rank>=2:
        niveau, bonus = "PREMIUM", 3
    elif max(tf1,tf2)>=15:
        niveau, bonus = "FORTE", 2
    else:
        niveau, bonus = "VALIDEE", 1
    dedup = f"{pair}_{tf1}_{tf2}_{strong}_{weak}_{niveau}"
    if time.time() - convergence_antispam.get(dedup, 0) < 300: return None
    convergence_antispam[dedup] = time.time()
    return {"tf1":tf1,"tf2":tf2,
            "label1":TF_LABELS.get(tf1,f"M{tf1}"),
            "label2":TF_LABELS.get(tf2,f"M{tf2}"),
            "delta":round(best["delta"],1),"niveau":niveau,"bonus":bonus}

# ============================================================
# COMPRESSION DYNAMIQUE (seuils V5 par TF)
# ============================================================
def get_compression_band(tick: Tick) -> float:
    return COMPRESSION_THRESHOLD.get(tick.timeframe, 13.0)

def detect_compression(tick: Tick, uid: str):
    results = []
    band     = get_compression_band(tick)
    min_bars = COMPRESSION_MIN_BARS.get(tick.timeframe, 3)
    cooldown = 600

    for dev, val in [(tick.dev_a, tick.val_a), (tick.dev_b, tick.val_b)]:
        k_state  = f"{uid}_{dev}_comp_state"
        k_center = f"{uid}_{dev}_comp_center"
        k_ticks  = f"{uid}_{dev}_comp_ticks"
        k_ts     = f"{uid}_{dev}_comp_ts"
        state    = compression_states.get(k_state, "NEUTRE")
        center   = compression_states.get(k_center, val)
        ticks    = compression_states.get(k_ticks, 0)

        if state == "NEUTRE":
            compression_states.update({k_state:"WATCHING",k_center:val,k_ticks:1})
            continue

        if abs(val - center) <= band:
            ticks += 1
            compression_states[k_ticks] = ticks
            center = center*0.85 + val*0.15
            compression_states[k_center] = center
            if ticks >= min_bars and state == "WATCHING":
                compression_states[k_state] = "COMPRIME"
                last_ts = compression_states.get(k_ts, 0)
                if time.time() - last_ts >= cooldown:
                    compression_states[k_ts] = time.time()
                    results.append({"phase":"COMPRESSION","dev":dev,"val":round(val,1),
                                    "center":round(center,1),"band":round(band,2),"ticks":ticks})
        else:
            if state == "COMPRIME":
                direction = "HAUT" if val > center + band else "BAS"
                results.append({"phase":"BREAK","dev":dev,"val":round(val,1),
                                "center":round(center,1),"direction":direction,"band":round(band,2)})
            compression_states.update({k_state:"WATCHING",k_center:val,k_ticks:1})

    return results if results else None

def detect_compression_squeeze(tick: Tick, prev: Tick, uid: str):
    squeeze_min_momentum = 0.8
    squeeze_min_ticks    = 2
    squeeze_gap_shrink   = True
    cooldown             = 600

    candidates = [
        (tick.dev_a, tick.val_a, prev.val_a, tick.dev_b, tick.val_b, prev.val_b),
        (tick.dev_b, tick.val_b, prev.val_b, tick.dev_a, tick.val_a, prev.val_a),
    ]
    for comp_dev, comp_now, _, opp_dev, opp_now, opp_prev in candidates:
        k_comp = f"{uid}_{comp_dev}_comp_state"
        if compression_states.get(k_comp) != "COMPRIME":
            squeeze_states[f"{uid}_{comp_dev}_sq_ticks"] = 0
            continue
        opp_momentum = opp_now - opp_prev
        gap_shrinks  = tick.gap < prev.gap
        if opp_momentum >= squeeze_min_momentum and ((not squeeze_gap_shrink) or gap_shrinks):
            sq_key = f"{uid}_{comp_dev}_sq_ticks"
            sl_key = f"{uid}_{comp_dev}_sq_last"
            sq_ticks = squeeze_states.get(sq_key, 0) + 1
            squeeze_states[sq_key] = sq_ticks
            if sq_ticks >= squeeze_min_ticks:
                if time.time() - squeeze_states.get(sl_key, 0) >= cooldown:
                    squeeze_states[sl_key] = time.time()
                    squeeze_states[sq_key] = 0
                    return {"compressed_dev":comp_dev,"pressure_dev":opp_dev,
                            "compressed_val":round(comp_now,1),"pressure_val":round(opp_now,1),
                            "pressure_momentum":round(opp_momentum,2),
                            "gap_prev":round(prev.gap,1),"gap_now":round(tick.gap,1),
                            "ticks":squeeze_min_ticks}
        else:
            squeeze_states[f"{uid}_{comp_dev}_sq_ticks"] = 0
    return None

# ============================================================
# CROISEMENT + KISS + FAKEOUT — seuils V5 dynamiques par TF
# ============================================================
KISS_RESET_BUFFER = 0.5

def detect_cross(tick: Tick, prev: Tick, uid: str):
    tf   = tick.timeframe
    state_now  = "A_DOM" if tick.val_a >= tick.val_b else "B_DOM"
    state_prev = "A_DOM" if prev.val_a >= prev.val_b else "B_DOM"

    # Seuils V5 dynamiques
    kiss_frolement    = get_kiss_frolement(tf)
    kiss_force_rejet  = get_kiss_force_rejet(tf)
    fakeout_delay     = get_fakeout_delay(tf)
    fakeout_gap       = get_fakeout_gap(tf)
    lvl_surcht_debut  = get_level_high(tf)
    lvl_survente_debut= get_level_low(tf)

    cur_gap  = tick.gap
    prev_gap = cross_states.get(f"{uid}_gap", 0.0)
    if cur_gap > prev_gap:
        cross_states[f"{uid}_gap"] = cur_gap

    if DEBUG_CROSS:
        print(f"  🔍 {uid} | prev={state_prev}({prev.val_a:.1f}/{prev.val_b:.1f}) "
              f"now={state_now}({tick.val_a:.1f}/{tick.val_b:.1f})")

    # --- PAS DE CROISEMENT : test KISS_REJECT ---
    if state_now == state_prev:
        rejet_state = cross_states.get(f"{uid}_kiss_state", "NEUTRE")
        if cur_gap > kiss_frolement + kiss_force_rejet + KISS_RESET_BUFFER:
            cross_states[f"{uid}_kiss_state"] = "NEUTRE"
        gap_delta      = cur_gap - prev.gap
        cond_frolement = prev.gap <= kiss_frolement
        cond_explosion = gap_delta >= kiss_force_rejet
        cond_nouveau   = rejet_state != "REJET_EN_COURS"
        if cond_frolement and cond_explosion and cond_nouveau:
            cross_states[f"{uid}_kiss_state"] = "REJET_EN_COURS"
            cross_states[f"{uid}_state"]      = state_now
            if DEBUG_CROSS:
                print(f"  💋 KISS_REJECT {uid} | gap {prev.gap:.1f}→{cur_gap:.1f} "
                      f"(+{gap_delta:.1f}) | frolement≤{kiss_frolement:.1f} force≥{kiss_force_rejet:.1f}")
            return "KISS_REJECT"
        return None

    # --- CROISEMENT ---
    now_ts        = time.time()
    last_cross_ts = cross_states.get(f"{uid}_time", 0.0)
    max_gap_bef   = cross_states.get(f"{uid}_gap", 0.0)
    cross_states[f"{uid}_state"]      = state_now
    cross_states[f"{uid}_time"]       = now_ts
    cross_states[f"{uid}_gap"]        = 0.0
    cross_states[f"{uid}_kiss_state"] = "NEUTRE"

    prev_strong = max(prev.val_a, prev.val_b)
    tick_strong = max(tick.val_a, tick.val_b)

    if (last_cross_ts > 0
            and now_ts - last_cross_ts < fakeout_delay
            and max_gap_bef > fakeout_gap):
        return "FAKEOUT"

    if prev_strong < lvl_survente_debut and tick_strong > 55:
        return "SUPER_SWITCH"
    if prev_strong > lvl_surcht_debut   and tick_strong < 45:
        return "SUPER_SWITCH"

    return "CROSS"

# ============================================================
# SLINGSHOT
# ============================================================
def detect_slingshot(tick: Tick, prev: Tick, uid: str):
    key  = f"{uid}_slingshot"
    v_a  = tick.val_a - prev.val_a
    v_b  = tick.val_b - prev.val_b
    recul   = v_a < -0.2 and v_b < -0.2
    explo_a = v_a > 0.8 and v_b < -0.2
    explo_b = v_b > 0.8 and v_a < -0.2
    state   = slingshot_states.get(key, "NEUTRE")
    if recul:
        slingshot_states[key] = "ARME"; return None
    if state == "ARME":
        if explo_a: slingshot_states[key]="NEUTRE"; return "SLINGSHOT_A"
        if explo_b: slingshot_states[key]="NEUTRE"; return "SLINGSHOT_B"
        if v_a > 0 and v_b > 0: slingshot_states[key]="NEUTRE"
    return None

# ============================================================
# APPROCHE IMMINENTE — seuils V5 dynamiques
# ============================================================
APPROACH_GAP_TRIGGER  = 12.0
APPROACH_GAP_CANCEL   = 18.0
APPROACH_MIN_MOMENTUM = 0.8

def detect_approach(tick: Tick, prev: Tick, uid: str):
    if tick.gap > APPROACH_GAP_CANCEL:
        approach_states[uid] = {"active": False}; return None
    if tick.val_a >= tick.val_b:
        challenger, ch_now, ch_prv = tick.dev_b, tick.val_b, prev.val_b
        dominant,   dom_val       = tick.dev_a, tick.val_a
    else:
        challenger, ch_now, ch_prv = tick.dev_a, tick.val_a, prev.val_a
        dominant,   dom_val       = tick.dev_b, tick.val_b
    momentum = ch_now - ch_prv
    if momentum < APPROACH_MIN_MOMENTUM or tick.gap > APPROACH_GAP_TRIGGER: return None
    last_ts = approach_states.get(uid, {}).get("ts_start", 0)
    if time.time() - last_ts < 300: return None
    lvl_low = get_level_low(tick.timeframe)
    zone_origine = ("SURVENTE" if ch_prv < lvl_low else ("BAS" if ch_prv < 40 else "NEUTRE"))
    approach_states[uid] = {"active":True,"actor":challenger,"val_start":ch_prv,
                            "ts_start":time.time(),"ticks":1}
    return {"challenger":challenger,"dominant":dominant,"gap":round(tick.gap,1),
            "momentum":round(momentum,2),"zone_origine":zone_origine,
            "challenger_val":round(ch_now,1),"dominant_val":round(dom_val,1)}

# ============================================================
# ZONE DE BATAILLE — seuils V5 dynamiques
# ============================================================
def detect_zone_battle(tick: Tick, prev: Tick, uid: str):
    if tick.timeframe not in (15, 30, 60, 240): return None
    if time.time() - zone_battle_states.get(f"{uid}_ts", 0) < 1800: return None
    lvl_high = get_level_high(tick.timeframe)
    lvl_low  = get_level_low(tick.timeframe)
    result = None
    if   tick.val_b >= lvl_high and prev.val_b < lvl_high:
        result = {"actor":tick.dev_b,"opponent":tick.dev_a,"zone":"HAUTE",
                  "val_actor":round(tick.val_b,1),"val_opp":round(tick.val_a,1),"direction":"surchauffe"}
    elif tick.val_a >= lvl_high and prev.val_a < lvl_high:
        result = {"actor":tick.dev_a,"opponent":tick.dev_b,"zone":"HAUTE",
                  "val_actor":round(tick.val_a,1),"val_opp":round(tick.val_b,1),"direction":"surchauffe"}
    elif tick.val_b <= lvl_low and prev.val_b > lvl_low:
        result = {"actor":tick.dev_b,"opponent":tick.dev_a,"zone":"BASSE",
                  "val_actor":round(tick.val_b,1),"val_opp":round(tick.val_a,1),"direction":"survente"}
    elif tick.val_a <= lvl_low and prev.val_a > lvl_low:
        result = {"actor":tick.dev_a,"opponent":tick.dev_b,"zone":"BASSE",
                  "val_actor":round(tick.val_a,1),"val_opp":round(tick.val_b,1),"direction":"survente"}
    if result:
        zone_battle_states[f"{uid}_ts"] = time.time()
    return result

# ============================================================
# COMPRESSION TEMPORELLE (bid) — Mission 6, observation seule
# ============================================================
TIME_COMP_ATR_FACTOR  = 0.8
TIME_COMP_FALLBACK_PIPS = {1:3,5:5,15:8,30:12,60:20,240:40}
TIME_COMP_MIN_TICKS     = {1:15,5:10,15:8,30:6,60:5,240:4}
TIME_COMP_COOLDOWN      = 600

def _pip_size(symbol: str) -> float:
    return 0.01 if "JPY" in symbol.upper() else 0.0001

def _time_comp_band(tick: Tick) -> float:
    if getattr(tick, "atr", 0.0) and tick.atr > 0.0:
        return tick.atr * TIME_COMP_ATR_FACTOR
    return TIME_COMP_FALLBACK_PIPS.get(tick.timeframe, 8) * _pip_size(tick.symbol)

def detect_time_compression(tick: Tick, uid: str):
    bid = float(getattr(tick,"bid",0.0) or 0.0)
    if bid <= 0.0: return None
    band = _time_comp_band(tick)
    if band <= 0.0: return None
    min_ticks = TIME_COMP_MIN_TICKS.get(tick.timeframe, 8)
    k_state  = f"{uid}_tc_state"
    k_center = f"{uid}_tc_center"
    k_ticks  = f"{uid}_tc_ticks"
    k_ts     = f"{uid}_tc_ts"
    state    = time_compression_states.get(k_state, "NEUTRE")
    center   = time_compression_states.get(k_center, bid)
    ticks    = time_compression_states.get(k_ticks, 0)
    if state == "NEUTRE":
        time_compression_states.update({k_state:"WATCHING",k_center:bid,k_ticks:1})
        return None
    if abs(bid - center) <= band:
        ticks += 1
        time_compression_states[k_ticks] = ticks
        center = center*0.90 + bid*0.10
        time_compression_states[k_center] = center
        if ticks >= min_ticks and state == "WATCHING":
            time_compression_states[k_state] = "LOCKED"
            return {"phase":"LOCK","center":round(center,5),"band":round(band,5),
                    "ticks":ticks,"bid":round(bid,5)}
        return None
    if state == "LOCKED":
        last_break = time_compression_states.get(k_ts, 0.0)
        if time.time() - last_break < TIME_COMP_COOLDOWN:
            time_compression_states.update({k_state:"WATCHING",k_center:bid,k_ticks:1})
            return None
        time_compression_states[k_ts] = time.time()
        result = {"phase":"BREAK","center":round(center,5),"band":round(band,5),
                  "ticks":ticks,"bid":round(bid,5),"from_bid":round(center,5)}
        time_compression_states.update({k_state:"WATCHING",k_center:bid,k_ticks:1})
        return result
    time_compression_states.update({k_state:"WATCHING",k_center:bid,k_ticks:1})
    return None

# ============================================================
# BUILD NOTE
# ============================================================
def build_note(signal_type, tick, htf, conv) -> str:
    tf_lbl = TF_LABELS.get(tick.timeframe, f"M{tick.timeframe}")
    lines  = []
    if   signal_type == "FAKEOUT":      lines.append("⚠️ Croisement précédent était un piège")
    elif signal_type == "SUPER_SWITCH": lines.append("💥 Croisement violent depuis zone extrême")
    elif signal_type == "KISS_REJECT":  lines.append("💋 Frôlement puis rejet net sans croisement")
    elif conv:
        lines.append(f"🔗 Convergence {conv['label1']}+{conv['label2']} "
                     f"— {conv['niveau']} ({conv['delta']} min)")
    else:
        lines.append(f"📊 Croisement {tf_lbl}")
    lines.append(f"HTF: {htf.bias} | {htf.bias_state} | "
                 f"{htf.aligned_count} TF alignés | {htf.scenario}")
    lines.append(f"Leader: {htf.leader} | Rang fractal: {htf.fractal_rank}/5")
    if htf.details:
        lines.append(" ".join(htf.details))
    return "\n".join(lines)

# ============================================================
# PROCESS_TICK — orchestrateur principal
# ============================================================
async def process_tick(tick: Tick, prev: Tick, brain: Brain, send_alert):
    if tick.timeframe not in TIMEFRAMES:
        return

    uid  = f"{tick.symbol}M{tick.timeframe}"
    pair = tick.symbol
    tf   = tick.timeframe
    dev_a, dev_b = tick.dev_a, tick.dev_b

    # Seuils V5 pour ce TF
    lvl_surcht_max   = get_level_high(tf)
    lvl_surcht_debut = get_level_high(tf)
    lvl_survente_max = get_level_low(tf)
    lvl_survente_debut = get_level_low(tf)

    spread_ok    = tick.spread <= MAX_SPREAD
    volume_badge = check_volume(tick, uid)
    htf          = build_htf_context(pair, tf, dev_a, dev_b, brain)

    if DEBUG_CROSS:
        print(f"⚙️ V5 process_tick {pair} M{tf} | "
              f"A={tick.val_a:.1f} {dev_a.upper()} | B={tick.val_b:.1f} {dev_b.upper()}")

    # --- Compression temporelle legacy -> preuve TEMPORAL V7 ---
    try:
        tc_ev = detect_time_compression(tick, uid)
        if tc_ev:
            tf_lbl = TF_LABELS.get(tf, f"M{tf}")
            tc_record = _write_legacy_timecomp_event_v7bus(pair, tf, tf_lbl, tick, tc_ev)
            stamp = f"[event_at={tc_record['event_at']} detected_at={tc_record['detected_at']}]"
            if tc_ev["phase"] == "LOCK":
                print(stamp)
                print(f"🔒 TIME-COMP LOCK | {pair} {tf_lbl} | "
                      f"bid {tc_ev['bid']} ±{tc_ev['band']} | {tc_ev['ticks']} ticks")
            else:
                print(stamp)
                print(f"💨 TIME-COMP BREAK | {pair} {tf_lbl} | "
                      f"bid {tc_ev['from_bid']}→{tc_ev['bid']} | {tc_ev['ticks']} ticks")
    except Exception as e:
        print(f"[engine] detect_time_compression ignoré : {e}")

    # --- APPROCHE ---
    approach = detect_approach(tick, prev, uid)
    if approach:
        spam_key = f"APPROACH_{uid}_{approach['challenger']}"
        if can_alert(spam_key):
            mark_alerted(spam_key)
            tf_lbl = TF_LABELS.get(tf, f"M{tf}")
            ch, dom = approach["challenger"].upper(), approach["dominant"].upper()
            note_ap = (f"⏳ APPROCHE IMMINENTE — {pair} {tf_lbl}\n"
                       f"{ch} remonte vers {dom} — écart {approach['gap']} pts\n"
                       f"{ch}={approach['challenger_val']} → {dom}={approach['dominant_val']}\n"
                       f"Momentum +{approach['momentum']}/tick | Depuis zone {approach['zone_origine']}\n"
                       f"Prépare-toi : CROSS ou REJET imminent")
            sc, lv = score_signal("CROSS", tf, volume_badge, htf.htf_bonus, spread_ok)
            sig = Signal(symbol=pair, timeframe=tf, signal_type="APPROACH",
                         timestamp=tick.timestamp, dev_strong=approach["dominant"],
                         dev_weak=approach["challenger"], score=sc, level=lv,
                         htf=htf, volume_badge=volume_badge, note=note_ap, spread_ok=spread_ok)
            await send_alert(sig, htf, brain)
            persist_signal(sig, htf); _write_legacy_behavioral_signal(sig, htf, tick=tick)

    # --- ZONE BATTLE ---
    zone = detect_zone_battle(tick, prev, uid)
    if zone:
        spam_key = f"ZONE_{uid}_{zone['actor']}"
        if can_alert(spam_key):
            mark_alerted(spam_key)
            tf_lbl = TF_LABELS.get(tf, f"M{tf}")
            stype  = "EXTREME_HIGH" if zone["zone"]=="HAUTE" else "EXTREME_LOW"
            note_z = (f"⚔️ {zone['actor'].upper()} entre en zone {zone['zone']} "
                      f"({zone['direction']}) — {zone['val_actor']}\n"
                      f"{zone['opponent'].upper()} à {zone['val_opp']}\n"
                      f"Surveille : compression → break ou rejet")
            sc, lv = score_signal(stype, tf, volume_badge, htf.htf_bonus, spread_ok)
            sig = Signal(symbol=pair, timeframe=tf, signal_type=stype,
                         timestamp=tick.timestamp, dev_strong=zone["actor"],
                         dev_weak=zone["opponent"], score=sc, level=lv,
                         htf=htf, volume_badge=volume_badge, note=note_z, spread_ok=spread_ok)
            await send_alert(sig, htf, brain)
            persist_signal(sig, htf); _write_legacy_behavioral_signal(sig, htf, tick=tick)

    # --- EXTREME LEVELS ---
    if ALERT_EXTREME_LEVELS:
        for dev, val in [(dev_a, tick.val_a), (dev_b, tick.val_b)]:
            key_ex    = f"{uid}_{dev}_extreme"
            prev_state = cross_states.get(key_ex, "NEUTRE")
            lvl_h = get_level_high(tf)
            lvl_l = get_level_low(tf)
            if val >= lvl_h and prev_state != "HAUT":
                cross_states[key_ex] = "HAUT"
                spam_key = f"EXTREME_HIGH_{uid}_{dev}"
                if can_alert(spam_key):
                    mark_alerted(spam_key)
                    strong = dev; weak = dev_b if dev==dev_a else dev_a
                    sc, lv = score_signal("EXTREME_HIGH", tf, volume_badge, htf.htf_bonus, spread_ok)
                    sig = Signal(symbol=pair, timeframe=tf, signal_type="EXTREME_HIGH",
                                 timestamp=tick.timestamp, dev_strong=strong, dev_weak=weak,
                                 score=sc, level=lv, htf=htf, volume_badge=volume_badge,
                                 note=f"🔴 {dev.upper()} en surchauffe ({val:.1f} ≥ {lvl_h})",
                                 spread_ok=spread_ok)
                    await send_alert(sig, htf, brain); persist_signal(sig, htf); _write_legacy_behavioral_signal(sig, htf, tick=tick)
            elif val <= lvl_l and prev_state != "BAS":
                cross_states[key_ex] = "BAS"
                spam_key = f"EXTREME_LOW_{uid}_{dev}"
                if can_alert(spam_key):
                    mark_alerted(spam_key)
                    strong = dev; weak = dev_b if dev==dev_a else dev_a
                    sc, lv = score_signal("EXTREME_LOW", tf, volume_badge, htf.htf_bonus, spread_ok)
                    sig = Signal(symbol=pair, timeframe=tf, signal_type="EXTREME_LOW",
                                 timestamp=tick.timestamp, dev_strong=strong, dev_weak=weak,
                                 score=sc, level=lv, htf=htf, volume_badge=volume_badge,
                                 note=f"🟢 {dev.upper()} en survente ({val:.1f} ≤ {lvl_l})",
                                 spread_ok=spread_ok)
                    await send_alert(sig, htf, brain); persist_signal(sig, htf); _write_legacy_behavioral_signal(sig, htf, tick=tick)
            elif lvl_l < val < lvl_h:
                cross_states[key_ex] = "NEUTRE"

    # --- SLINGSHOT ---
    if ALERT_SLINGSHOT:
        sling = detect_slingshot(tick, prev, uid)
        if sling:
            exploding = dev_a if sling=="SLINGSHOT_A" else dev_b
            weak      = dev_b if exploding==dev_a else dev_a
            spam_key  = f"SLINGSHOT_{uid}_{exploding}"
            if can_alert(spam_key):
                mark_alerted(spam_key)
                sc, lv = score_signal("SLINGSHOT", tf, volume_badge, htf.htf_bonus, spread_ok)
                now_ts  = time.time()
                seq_key = f"{pair}_{exploding}_SLING"
                seq_tag = ""
                last    = slingshot_sequence.get(seq_key)
                if last and last.get("last_tf")==5 and tf==15 and (now_ts-last.get("ts",0))<=2700:
                    sc += 2; seq_tag = " | Séquence M5→M15 ✅"
                slingshot_sequence[seq_key] = {"last_tf":tf,"ts":now_ts}
                lv = "PREMIUM" if sc>=8 else ("CONFIRM" if sc>=5 else "STANDARD")
                sig = Signal(symbol=pair, timeframe=tf, signal_type="SLINGSHOT",
                             timestamp=tick.timestamp, dev_strong=exploding, dev_weak=weak,
                             score=sc, level=lv, htf=htf, volume_badge=volume_badge,
                             note=f"🎯 {exploding.upper()} explose après repli conjoint{seq_tag}",
                             spread_ok=spread_ok)
                await send_alert(sig, htf, brain); persist_signal(sig, htf); _write_legacy_behavioral_signal(sig, htf, tick=tick)

    # --- COMPRESSION ---
    if ALERT_COMPRESSION:
        comp_events = detect_compression(tick, uid)
        if comp_events:
            ev      = max(comp_events, key=lambda e: abs(e["val"]-50.0))
            dev_c   = ev["dev"]
            opp_c   = dev_b if dev_c==dev_a else dev_a
            spam_key = f"COMP_{uid}_{dev_c}_{ev['phase']}"
            if can_alert(spam_key):
                mark_alerted(spam_key)
                tf_lbl = TF_LABELS.get(tf, f"M{tf}")
                if ev["phase"] == "COMPRESSION":
                    stype = "COMPRESSION"
                    note_c = (f"🔒 COMPRESSION — {dev_c.upper()} en palier\n"
                              f"{pair} {tf_lbl}\n"
                              f"{dev_c.upper()} stagne autour de {ev['center']} "
                              f"depuis {ev['ticks']} bougies\n"
                              f"Couloir ±{ev['band']:.1f} pts | {opp_c.upper()}="
                              f"{tick.val_b if dev_c==dev_a else tick.val_a:.1f}\n"
                              f"⚡ Break ou rejet imminent\n"
                              f"HTF: {htf.bias} | {htf.bias_state} | {htf.scenario}")
                else:
                    stype  = "COMPRESSION_BREAK"
                    arrow  = "🚀" if ev["direction"]=="HAUT" else "💥"
                    sens   = "Rupture haussière" if ev["direction"]=="HAUT" else "Rejet baissier"
                    note_c = (f"{arrow} SORTIE PALIER — {dev_c.upper()} {sens}\n"
                              f"{pair} {tf_lbl}\n"
                              f"{dev_c.upper()} quitte le palier {ev['center']} → {ev['val']}\n"
                              f"Direction : {ev['direction']} | Bande ±{ev['band']:.1f} pts")
                sc, lv = score_signal(stype, tf, volume_badge, htf.htf_bonus, spread_ok)
                sig = Signal(symbol=pair, timeframe=tf, signal_type=stype,
                             timestamp=tick.timestamp, dev_strong=dev_c, dev_weak=opp_c,
                             score=sc, level=lv, htf=htf, volume_badge=volume_badge,
                             note=note_c, spread_ok=spread_ok)
                await send_alert(sig, htf, brain); persist_signal(sig, htf); _write_legacy_behavioral_signal(sig, htf, tick=tick)

    # --- COMPRESSION SQUEEZE ---
    if ALERT_COMPRESSION_SQUEEZE:
        sq = detect_compression_squeeze(tick, prev, uid)
        if sq:
            spam_key = f"SQUEEZE_{uid}_{sq['compressed_dev']}_{sq['pressure_dev']}"
            if can_alert(spam_key):
                mark_alerted(spam_key)
                tf_lbl = TF_LABELS.get(tf, f"M{tf}")
                sc, lv = score_signal("COMPRESSION_SQUEEZE", tf, volume_badge, htf.htf_bonus, spread_ok)
                note_sq = (f"🧲 COMPRESSION SQUEEZE\n{pair} {tf_lbl}\n"
                           f"{sq['compressed_dev'].upper()} compressé autour de {sq['compressed_val']}\n"
                           f"{sq['pressure_dev'].upper()} pousse : +{sq['pressure_momentum']}/tick\n"
                           f"Écart : {sq['gap_prev']}→{sq['gap_now']}\n"
                           f"⚠️ Pression adverse | HTF: {htf.bias} | {htf.bias_state}")
                sig = Signal(symbol=pair, timeframe=tf, signal_type="COMPRESSION_SQUEEZE",
                             timestamp=tick.timestamp,
                             dev_strong=sq["pressure_dev"], dev_weak=sq["compressed_dev"],
                             score=sc, level=lv, htf=htf, volume_badge=volume_badge,
                             note=note_sq, spread_ok=spread_ok)
                await send_alert(sig, htf, brain); persist_signal(sig, htf); _write_legacy_behavioral_signal(sig, htf, tick=tick)

    # --- CROSS / FAKEOUT / SUPER_SWITCH / KISS_REJECT ---
    signal_type = detect_cross(tick, prev, uid)
    if signal_type is None:
        return

    strong = dev_a if tick.val_a >= tick.val_b else dev_b
    weak   = dev_b if strong==dev_a else dev_a

    if signal_type == "KISS_REJECT":
        if not ALERT_KISS_REJECT: return
        spam_key = f"KISS_REJECT_{uid}_{strong}"
        if not can_alert(spam_key): return
        mark_alerted(spam_key)
        tf_lbl  = TF_LABELS.get(tf, f"M{tf}")
        kf      = get_kiss_frolement(tf)
        kfr     = get_kiss_force_rejet(tf)
        sc, lv  = score_signal("KISS_REJECT", tf, volume_badge, htf.htf_bonus, spread_ok)
        val_s   = tick.val_a if strong==dev_a else tick.val_b
        lvl_h   = get_level_high(tf)
        note_zone = " | Zone propre ✅" if val_s < lvl_h-10 else (" | ⚠️ Zone extrème" if val_s > lvl_h+5 else "")
        if val_s < lvl_h-10: sc += 1
        elif val_s > lvl_h+5: sc -= 1
        lv = "PREMIUM" if sc>=8 else ("CONFIRM" if sc>=5 else "STANDARD")
        ct = htf.bias not in ("NEUTRAL","NA") and htf.bias.upper()!=strong.upper()
        titre = "⚠️ KISS REJECT CONTRE-TENDANCE" if ct else "💋 KISS REJECT"
        note  = (f"{titre} — {pair} {tf_lbl}\n"
                 f"{strong.upper()} rejette le {weak.upper()}{note_zone}\n"
                 f"{strong.upper()}={val_s:.1f} | Gap {prev.gap:.1f}→{tick.gap:.1f} (+{tick.gap-prev.gap:.1f})\n"
                 f"HTF: {htf.bias} | {htf.bias_state} | {htf.scenario}\n"
                 f"Score: {sc} → {lv} | Frolement≤{kf:.1f} | Force≥{kfr:.1f}")
        sig = Signal(symbol=pair, timeframe=tf, signal_type="KISS_REJECT",
                     timestamp=tick.timestamp, dev_strong=strong, dev_weak=weak,
                     score=sc, level=lv, htf=htf, volume_badge=volume_badge,
                     note=note, spread_ok=spread_ok)
        await send_alert(sig, htf, brain); persist_signal(sig, htf); _write_legacy_behavioral_signal(sig, htf, tick=tick); return

    # --- CROSS PRINCIPAL ---
    register_cross(pair, tf, strong, weak)
    conv = detect_convergence(pair, tf, strong, weak, htf)

    if   signal_type=="FAKEOUT"      and ALERT_FAKEOUT:      final_type="FAKEOUT"
    elif signal_type=="SUPER_SWITCH" and ALERT_SUPER_SWITCH: final_type="SUPER_SWITCH"
    elif conv                        and ALERT_CONVERGENCE:  final_type="CONVERGENCE"
    elif ALERT_CROSS_BASIC:                                  final_type="CROSS"
    else: return

    spam_key = f"{final_type}_{uid}_{strong}"
    if not can_alert(spam_key): return
    mark_alerted(spam_key)

    sc, lv = score_signal(final_type, tf, volume_badge, htf.htf_bonus, spread_ok)

    # Bonus post-extrême M5/M15
    extreme_tag = ""
    if tf in (5,15) and final_type in ("CROSS","SUPER_SWITCH","FAKEOUT"):
        lvl_l = get_level_low(tf)
        lvl_h = get_level_high(tf)
        bonus_extreme = 0
        if   (strong==dev_a and prev.val_a<=lvl_l) or (strong==dev_b and prev.val_b<=lvl_l):
            bonus_extreme = 1 if tf==5 else 2; extreme_tag=f" | M{tf} post-survente ✅"
        elif (weak==dev_a and prev.val_a>=lvl_h) or (weak==dev_b and prev.val_b>=lvl_h):
            bonus_extreme = 1 if tf==5 else 2; extreme_tag=f" | M{tf} post-surchauffe ✅"
        if bonus_extreme > 0:
            sc += bonus_extreme
            # Bonus extrême fort
            if (prev.val_a<=get_level_low(tf) or prev.val_b<=get_level_low(tf)
                    or prev.val_a>=get_level_high(tf) or prev.val_b>=get_level_high(tf)):
                sc += 1; extreme_tag += " Extrême fort"
    if conv: sc += conv["bonus"]
    lv = "PREMIUM" if sc>=8 else ("CONFIRM" if sc>=5 else "STANDARD")

    note = build_note(signal_type, tick, htf, conv)
    if extreme_tag: note += extreme_tag

    sig = Signal(symbol=pair, timeframe=tf, signal_type=final_type,
                 timestamp=tick.timestamp, dev_strong=strong, dev_weak=weak,
                 score=sc, level=lv, htf=htf, volume_badge=volume_badge,
                 note=note, spread_ok=spread_ok, convergence=conv)

    print(f"🔥 V5 signal : {sig.signal_type} {pair} M{tf} "
          f"{strong.upper()}>{weak.upper()} score={sc} {lv}")
    await send_alert(sig, htf, brain)
    persist_signal(sig, htf); _write_legacy_behavioral_signal(sig, htf, tick=tick)

# ============================================================
# MODULE C — TEMPORAL NODES INTEGRATION
# ============================================================

async def process_temporal_nodes_cycle(symbols=None, db_path="powerflow.db"):
    """
    Détection des nodes temporels en parallèle du moteur principal.
    
    À appeler périodiquement (toutes les 10 sec) depuis la boucle principale.
    """
    
    if not TEMPORAL_NODES_ENABLED:
        return None
    
    if symbols is None:
        symbols = ["GBPUSD", "EURUSD", "GBPJPY"]
    
    results = {}
    
    for symbol in symbols:
        try:
            # 1. Détecter nodes
            nodes_data = get_temporal_nodes_for_engine(
                db_path=db_path,
                symbol=symbol,
                timeframes=[1, 5, 15, 30, 60],
                mode="live"
            )
            
            # 2. Traiter alertes
            alerts = process_temporal_nodes_for_engine(
                symbol=symbol,
                nodes_data=nodes_data,
                db_path=db_path,
                send_telegram_callback=send_temporal_node_alert
            )
            
            # 3. Log
            if alerts.get("critical_alerts"):
                print(f"🚨 {symbol}: {len(alerts['critical_alerts'])} CRITICAL alerts!")
            
            results[symbol] = alerts
        
        except Exception as e:
            print(f"⚠️ Temporal nodes error {symbol}: {e}")
            results[symbol] = {"error": str(e)}
    
    return results
