import json
import os
from datetime import datetime, timezone


def ensure_output_dir(path="output"):
    os.makedirs(path, exist_ok=True)


def load_previous_state(path="output/cockpit_state.json"):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def atomic_write_json(path, data):
    directory = os.path.dirname(path) or "."
    ensure_output_dir(directory)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


def compare_cockpit_states(previous, current):
    if not isinstance(previous, dict):
        return ["previous state absent"]

    changes = []

    def _append_change(label, old, new):
        if old != new:
            changes.append(f"{label}: {old} -> {new}")

    _append_change("posture", previous.get("posture"), current.get("posture"))

    prev_market = previous.get("market", {}) if isinstance(previous.get("market"), dict) else {}
    curr_market = current.get("market", {}) if isinstance(current.get("market"), dict) else {}
    _append_change("market.dominant_flow", prev_market.get("dominant_flow"), curr_market.get("dominant_flow"))
    _append_change("market.main_focus", prev_market.get("main_focus"), curr_market.get("main_focus"))
    _append_change("market.risk_level", prev_market.get("risk_level"), curr_market.get("risk_level"))

    prev_data = previous.get("data", {}) if isinstance(previous.get("data"), dict) else {}
    curr_data = current.get("data", {}) if isinstance(current.get("data"), dict) else {}
    _append_change("data.is_stale", prev_data.get("is_stale"), curr_data.get("is_stale"))

    _append_change("watchlist", previous.get("watchlist", []), current.get("watchlist", []))
    return changes


def _safe_get_summary(flow):
    if isinstance(flow, dict):
        summary = flow.get("summary")
        if isinstance(summary, dict):
            return summary
    return {}


def _compute_posture(local, contradiction, db_exists, is_stale):
    regime = str(local.get("regime", "")).lower()
    trigger = str(local.get("trigger", "")).lower()
    score = int(contradiction.get("score", 0) or 0)

    if not db_exists or regime == "erreur db":
        return "OFFLINE", "DB inaccessible ou lecture impossible."
    if is_stale is True:
        return "DATA_STALE", "Données DB trop anciennes."
    if score <= -4 or regime in ("seek and destroy", "piégeux"):
        return "DANGER", "Contradiction forte ou contexte piégeux."
    if "pression constructive" in trigger and score >= 1:
        return "ARMED", "Focus clair avec confirmation demandée."
    if score < 1:
        return "WATCH", "Focus intéressant mais non confirmé."
    return "OBSERVE", "Observation par défaut."



def build_agent_control(posture, db_status, is_stale, risk_level, alerts=None, confirmations_required=None):
    alerts = alerts or []
    confirmations_required = confirmations_required or []

    forbidden_actions = [
        "TRADE",
        "PLACE_ORDER",
        "MODIFY_DB",
        "MIGRATE_DB",
        "AUTO_EXECUTE",
    ]

    allowed_actions = [
        "READ_STATE",
        "COMPARE_STATE",
        "REPORT",
        "EXPORT_JSON",
    ]

    if db_status == "KO" or posture == "OFFLINE":
        return {
            "action_required": "FIX_DATA_PIPELINE",
            "blocking_reason": "DB inaccessible ou Cockpit aveugle.",
            "freshness_status": "OFFLINE",
            "next_check": "Verifier bridge.py / powerflow.db / flux MT4.",
            "allowed_agent_actions": allowed_actions,
            "forbidden_agent_actions": forbidden_actions,
            "trading_allowed": False,
            "human_validation_required": True,
        }

    if is_stale is True or posture == "DATA_STALE":
        return {
            "action_required": "REFRESH_DATA",
            "blocking_reason": "Donnees trop anciennes.",
            "freshness_status": "STALE",
            "next_check": "Relancer capture puis attendre nouveau run Cockpit.",
            "allowed_agent_actions": allowed_actions,
            "forbidden_agent_actions": forbidden_actions,
            "trading_allowed": False,
            "human_validation_required": True,
        }

    freshness_status = "FRESH" if is_stale is False else "UNKNOWN"

    if posture == "DANGER":
        return {
            "action_required": "STOP_AND_OBSERVE",
            "blocking_reason": "Risque ou contradiction detectee.",
            "freshness_status": freshness_status,
            "next_check": "Attendre invalidation du danger ou nouvelle scene propre.",
            "allowed_agent_actions": allowed_actions + ["WATCH_RISK"],
            "forbidden_agent_actions": forbidden_actions,
            "trading_allowed": False,
            "human_validation_required": True,
        }

    if posture == "ARMED":
        return {
            "action_required": "CONFIRM_SETUP",
            "blocking_reason": None,
            "freshness_status": freshness_status,
            "next_check": "Confirmer M5/M15 + Pattern1 + flow global.",
            "allowed_agent_actions": allowed_actions + ["WATCH_CONFIRMATIONS"],
            "forbidden_agent_actions": forbidden_actions,
            "trading_allowed": False,
            "human_validation_required": True,
        }

    if posture == "WATCH":
        return {
            "action_required": "WAIT_CONFIRMATION",
            "blocking_reason": "Scenario interessant mais non confirme.",
            "freshness_status": freshness_status,
            "next_check": "Surveiller confirmations: " + ", ".join(confirmations_required) if confirmations_required else "Surveiller confirmation.",
            "allowed_agent_actions": allowed_actions + ["WATCH_CONFIRMATIONS"],
            "forbidden_agent_actions": forbidden_actions,
            "trading_allowed": False,
            "human_validation_required": True,
        }

    return {
        "action_required": "OBSERVE",
        "blocking_reason": None,
        "freshness_status": freshness_status,
        "next_check": "Continuer observation.",
        "allowed_agent_actions": allowed_actions,
        "forbidden_agent_actions": forbidden_actions,
        "trading_allowed": False,
        "human_validation_required": True,
    }

def build_minimal_cockpit_state(local=None, flow=None, contradiction=None, db_exists=True):
    local = local or {}
    contradiction = contradiction or {}
    summary = _safe_get_summary(flow)

    last_signal_age_min = local.get("last_signal_age")
    db_age_seconds = None
    if isinstance(last_signal_age_min, (int, float)):
        db_age_seconds = int(max(0, last_signal_age_min * 60))

    is_stale = None
    if db_age_seconds is not None:
        is_stale = db_age_seconds > 20 * 60

    db_status = "OK" if db_exists else "KO"
    if str(local.get("regime", "")).lower() == "erreur db":
        db_status = "KO"

    posture, posture_reason = _compute_posture(local, contradiction, db_exists=db_exists, is_stale=is_stale)

    if posture == "DANGER":
        risk_level = "HIGH"
    elif posture in ("WATCH", "ARMED"):
        risk_level = "MEDIUM"
    elif posture == "OBSERVE":
        risk_level = "LOW"
    else:
        risk_level = "UNKNOWN"

    dominant_flow = summary.get("flow") if summary.get("flow") not in (None, "") else None
    main_focus = summary.get("top_pair_focus") or local.get("symbol") or None
    main_timeframe = summary.get("leader_tf") if summary.get("leader_tf") else None

    alerts = contradiction.get("alerts") if isinstance(contradiction.get("alerts"), list) else []
    confirmations_required = ["M5/M15", "Pattern1", "flow global"] if posture in ("WATCH", "ARMED") else []
    agent_control = build_agent_control(
        posture=posture,
        db_status=db_status,
        is_stale=is_stale,
        risk_level=risk_level,
        alerts=alerts,
        confirmations_required=confirmations_required,
    )

    return {
        "version": "COCKPIT_V6.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "posture": posture,
        "posture_reason": posture_reason,
        "data": {
            "db_status": db_status,
            "db_age_seconds": db_age_seconds,
            "is_stale": is_stale,
        },
        "market": {
            "dominant_flow": dominant_flow,
            "main_focus": main_focus,
            "main_timeframe": main_timeframe,
            "risk_level": risk_level,
        },
        "watchlist": [],
        "risks": alerts[:5],
        "confirmations_required": confirmations_required,
        "action_required": agent_control.get("action_required"),
        "blocking_reason": agent_control.get("blocking_reason"),
        "freshness_status": agent_control.get("freshness_status"),
        "next_check": agent_control.get("next_check"),
        "allowed_agent_actions": agent_control.get("allowed_agent_actions"),
        "forbidden_agent_actions": agent_control.get("forbidden_agent_actions"),
        "agent_control": agent_control,
        "changes_since_previous_run": [],
        "agent_ready": True,
    }


def append_state_history(path, state):
    directory = os.path.dirname(path) or "."
    ensure_output_dir(directory)
    with open(path, "a", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)
        f.write("\n")


def load_state_history(path, max_lines=300):
    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return []

    if max_lines and max_lines > 0:
        lines = lines[-max_lines:]

    history = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except Exception:
            continue
        if isinstance(item, dict):
            history.append(item)
    return history


def _parse_state_time(state):
    if not isinstance(state, dict):
        return None
    value = state.get("generated_at")
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def find_state_around_age(history, current_state, target_seconds=300):
    current_dt = _parse_state_time(current_state)
    if current_dt is None:
        return None

    best = None
    best_distance = None

    for state in history or []:
        state_dt = _parse_state_time(state)
        if state_dt is None:
            continue

        age_seconds = int((current_dt - state_dt).total_seconds())
        if age_seconds < 0:
            continue

        distance = abs(age_seconds - int(target_seconds))
        if best_distance is None or distance < best_distance:
            best = dict(state)
            best["_age_gap_seconds"] = age_seconds
            best_distance = distance

    return best


def _nested(state, section, key, fallback=None):
    if not isinstance(state, dict):
        return fallback
    value = state.get(section)
    if not isinstance(value, dict):
        return fallback
    return value.get(key, fallback)


def _safe_value(value):
    if value is None:
        return "UNKNOWN"
    if value == "":
        return "UNKNOWN"
    return value


def _change_text(old, new):
    old = _safe_value(old)
    new = _safe_value(new)
    if old == new:
        return f"{new} stable"
    return f"{old} -> {new}"


def _interpret_temporal(reference_state, current_state):
    if not isinstance(reference_state, dict):
        return "unknown"

    old_posture = reference_state.get("posture")
    new_posture = current_state.get("posture")
    old_focus = _nested(reference_state, "market", "main_focus")
    new_focus = _nested(current_state, "market", "main_focus")
    old_stale = _nested(reference_state, "data", "is_stale")
    new_stale = _nested(current_state, "data", "is_stale")

    if old_stale is False and new_stale is True:
        return "vieillit"
    if old_posture == "OBSERVE" and new_posture in ("WATCH", "ARMED"):
        return "renforce"
    if old_posture == "WATCH" and new_posture == "ARMED":
        return "renforce"
    if old_posture in ("WATCH", "ARMED") and new_posture == "DANGER":
        return "invalide"
    if old_posture == new_posture and old_focus == new_focus:
        return "stable"
    return "unknown"


def build_temporal_compare(previous_state, reference_5min_state, current_state):
    previous_available = isinstance(previous_state, dict)
    t5_available = isinstance(reference_5min_state, dict)

    previous = {
        "available": previous_available,
        "posture_change": None,
        "focus_change": None,
        "risk_change": None,
        "stale_change": None,
    }

    if previous_available:
        previous = {
            "available": True,
            "posture_change": _change_text(previous_state.get("posture"), current_state.get("posture")),
            "focus_change": _change_text(
                _nested(previous_state, "market", "main_focus"),
                _nested(current_state, "market", "main_focus"),
            ),
            "risk_change": _change_text(
                _nested(previous_state, "market", "risk_level"),
                _nested(current_state, "market", "risk_level"),
            ),
            "stale_change": _change_text(
                _nested(previous_state, "data", "is_stale"),
                _nested(current_state, "data", "is_stale"),
            ),
        }

    t_minus_5min = {
        "available": t5_available,
        "age_gap_seconds": None,
        "posture_change": None,
        "focus_change": None,
        "risk_change": None,
        "interpretation": "unknown",
    }

    if t5_available:
        t_minus_5min = {
            "available": True,
            "age_gap_seconds": reference_5min_state.get("_age_gap_seconds"),
            "posture_change": _change_text(reference_5min_state.get("posture"), current_state.get("posture")),
            "focus_change": _change_text(
                _nested(reference_5min_state, "market", "main_focus"),
                _nested(current_state, "market", "main_focus"),
            ),
            "risk_change": _change_text(
                _nested(reference_5min_state, "market", "risk_level"),
                _nested(current_state, "market", "risk_level"),
            ),
            "interpretation": _interpret_temporal(reference_5min_state, current_state),
        }

    return {
        "previous": previous,
        "t_minus_5min": t_minus_5min,
    }


def append_postmortem(path, current_state, note="", outcome="unknown"):
    directory = os.path.dirname(path) or "."
    ensure_output_dir(directory)

    market = current_state.get("market", {}) if isinstance(current_state.get("market"), dict) else {}
    temporal = current_state.get("temporal", {}) if isinstance(current_state.get("temporal"), dict) else {}

    record = {
        "version": "COCKPIT_POSTMORTEM_V1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_state_generated_at": current_state.get("generated_at"),
        "posture": current_state.get("posture"),
        "focus": market.get("main_focus"),
        "dominant_flow": market.get("dominant_flow"),
        "risk_level": market.get("risk_level"),
        "action_required": current_state.get("action_required"),
        "blocking_reason": current_state.get("blocking_reason"),
        "temporal": temporal,
        "outcome": outcome or "unknown",
        "human_note": note or "",
        "lesson_candidate": {
            "what_cockpit_saw": {
                "posture": current_state.get("posture"),
                "risk_level": market.get("risk_level"),
                "action_required": current_state.get("action_required"),
            },
            "what_to_review": [
                "Did the posture protect the decision?",
                "Was the signal early, valid, late, or dangerous?",
                "What confirmation was missing?",
            ],
        },
    }

    with open(path, "a", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False)
        f.write("\n")

    return record


def load_jsonl_records(path, max_lines=None):
    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception:
        return []

    if max_lines and max_lines > 0:
        lines = lines[-max_lines:]

    records = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except Exception:
            continue
        if isinstance(item, dict):
            records.append(item)
    return records


def _count_values(records, key, limit=10):
    counts = {}
    for record in records:
        value = record.get(key)
        if value in (None, ""):
            value = "UNKNOWN"
        value = str(value)
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit])


def build_postmortem_lessons(path="output/cockpit_postmortem.jsonl", max_records=300):
    records = load_jsonl_records(path, max_lines=max_records)

    outcomes = _count_values(records, "outcome")
    focuses = _count_values(records, "focus")
    postures = _count_values(records, "posture")
    risks = _count_values(records, "risk_level")
    actions = _count_values(records, "action_required")

    recent = []
    for record in records[-10:]:
        recent.append({
            "created_at": record.get("created_at"),
            "focus": record.get("focus"),
            "posture": record.get("posture"),
            "risk_level": record.get("risk_level"),
            "action_required": record.get("action_required"),
            "outcome": record.get("outcome"),
            "human_note": record.get("human_note"),
        })

    lessons = []

    confirmed = outcomes.get("confirmed", 0)
    invalidated = outcomes.get("invalidated", 0)
    danger = outcomes.get("danger", 0)
    late = outcomes.get("late", 0)
    missed = outcomes.get("missed", 0)

    if confirmed >= 3:
        lessons.append("Les postures Cockpit semblent protéger correctement certaines décisions confirmées.")
    if invalidated >= 2:
        lessons.append("Plusieurs lectures ont été invalidées : renforcer les confirmations avant de passer de WATCH à ARMED.")
    if danger >= 2:
        lessons.append("Les scènes dangereuses reviennent : isoler les conditions de contradiction forte.")
    if late >= 2:
        lessons.append("Signaux tardifs répétés : mesurer l'âge du signal avant toute lecture forte.")
    if missed >= 2:
        lessons.append("Opportunités manquées : vérifier si Cockpit reste trop longtemps en OBSERVE/WATCH.")

    if not lessons:
        lessons.append("Pas encore assez de post-mortems pour extraire une leçon robuste.")

    return {
        "version": "COCKPIT_LESSONS_V1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": path,
        "total_records": len(records),
        "outcomes": outcomes,
        "focuses": focuses,
        "postures": postures,
        "risk_levels": risks,
        "action_required": actions,
        "recent_postmortems": recent,
        "lesson_candidates": lessons,
        "agent_ready": True,
    }

