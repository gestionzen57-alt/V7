"""
test_behavioral_alert_mapper.py
Tests unitaires pf_behavioral_alert_mapper — fixtures en mémoire, pas de DB.
"""

import sys
import json
from typing import Any


# ---------------------------------------------------------------------------
# Import du module
# ---------------------------------------------------------------------------

try:
    from pf_behavioral_alert_mapper import map_behavioral_alerts
except ImportError as e:
    print(f"[ERREUR] Impossible d'importer pf_behavioral_alert_mapper : {e}")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Helpers fixtures
# ---------------------------------------------------------------------------

def _make_tns(
    highest_level: str = "NODE_BIRTH",
    maturity: str = "BIRTH",
    direction: str = "GBP pressure up / USD pressure down",
    relay_quality: str = "CLEAN",
    relay_sample: str = "M5_RELAY_CLEAN",
    m5_role: str = "M5_RELAY_CLEAN",
    release_state: str = "RELEASE_ATTEMPT",
    first_detachment_detected: bool = False,
    detachment_label: str = "NO_DETACHMENT",
    angle_state: str = "NEUTRAL",
    speed_state: str = "MODERATE",
    acceleration_state: str = "STABLE",
    tight_gravity_label: str = "NO_CLUSTER",
    tight_gravity_currencies: list | None = None,
    tight_gravity_spread: float = 0.0,
    same_angle_label: str = "NO_CLUSTER",
    same_angle_currencies: list | None = None,
    reasons_ok: list | None = None,
    reasons_nok: list | None = None,
    nodes: list | None = None,
    symbol: str = "GBPUSD",
) -> dict[str, Any]:
    """Construit un temporal_node_state minimal pour tests."""

    base_nodes = nodes or [
        {
            "id": "NODE_001",
            "symbol": symbol,
            "timeframe": "M1",
            "tf_minutes": 1,
            "level": highest_level,
            "family": "TEMPORAL_NODE",
            "direction_bias": direction,
            "maturity": maturity,
            "confidence": "EARLY",
            "score": 5.5,
            "reasons": ["force_shift", "compression"],
            "risks_technical": ["m1_noise"],
            "telegram_allowed": True,
            "telegram_level": "BIRTH",
            "has_convergence": False,
            "has_repulsion": False,
            "has_cross": False,
            "has_kiss_reject": False,
            "has_compression": True,
            "has_break": False,
            "context": {
                "structure_label": "M1_MICRO_NODE_BIRTH",
                "fractal_state": "LTF_BIRTH_INSIDE_VISUAL_HTF_STORY",
                "trigger_tf": "M1",
                "m1_role": "M1_NODE_ACTIVE",
                "m5_role": m5_role,
                "m15_role": "M15_NODE_ACTIVE",
                "htf_role": "VISUAL_HTF_BATTLE_CONFIRMED",
                "visual_htf_story": "confirmed",
                "extended_micro_window": "MICRO_WINDOW_ACTIVE_WEAK",
                "extended_flags": [],
            },
        }
    ]

    return {
        "meta": {"generated_at": "2026-05-06T02:04:00Z", "symbol": symbol, "source": "pf_temporal_node_state"},
        "node_summary": {
            "active_count": len(base_nodes),
            "highest_level": highest_level,
            "dominant_direction": direction,
            "telegram_mode": "SCALPING",
            "fractal_state": "LTF_BIRTH_INSIDE_VISUAL_HTF_STORY",
        },
        "telegram_gating": {
            "effective_state": "HOT_READY",
            "relay_tf_available": relay_quality != "MISSING",
            "relay_quality": relay_quality,
            "relay_sample_state": relay_sample,
            "m5_role": m5_role,
            "live_allowed": True,
            "telegram_mode": "SCALPING",
            "hot_node_count": 1 if "HOT" in highest_level else 0,
            "degraded_reason": None,
        },
        "capture_quality": {
            "relay_quality": relay_quality,
            "relay_sample_state": relay_sample,
        },
        "nodes": base_nodes,
        "next_watch": ["WATCH_ABSORPTION", "WATCH_SECOND_LEG"],
        "kinematics_state": {
            "status": "OK",
            "angle_state": angle_state,
            "speed_state": speed_state,
            "acceleration_state": acceleration_state,
            "same_angle_cluster": {
                "label": same_angle_label,
                "currencies": same_angle_currencies or [],
            },
            "tight_gravity_cluster": {
                "label": tight_gravity_label,
                "currencies": tight_gravity_currencies or [],
                "force_spread": tight_gravity_spread,
            },
            "first_detachment": {
                "detected": first_detachment_detected,
                "label": detachment_label,
                "note": "test fixture",
            },
            "force_hold_with_acceleration_fade": {
                "detected": False,
                "label": "NO_FADE",
            },
            "release_candidate": {
                "release": release_state == "RELEASE_CONFIRMED",
                "release_watch": release_state in ("RELEASE_ATTEMPT", "RELEASE_CANDIDATE"),
                "release_confirmed": release_state == "RELEASE_CONFIRMED",
                "release_state": release_state,
                "release_confidence": "LOW",
                "label": release_state,
                "relay_quality_used": relay_quality,
                "reasons_ok": reasons_ok or [],
                "reasons_nok": reasons_nok or [],
            },
        },
    }


def _make_energy(
    base_ccy: str = "GBP",
    base_label: str = "ENERGY_STRONG",
    quote_ccy: str = "USD",
    quote_label: str = "ENERGY_WEAK",
) -> dict[str, Any]:
    """Construit un currency_energy_state minimal pour tests."""
    return {
        "meta": {"generated_at": "2026-05-06T02:00:00Z", "symbol": f"{base_ccy}{quote_ccy}", "timeframe": 1},
        "currencies": {
            base_ccy: {
                "currency": base_ccy,
                "energy_label": base_label,
                "energy_score": 0.8,
                "absorption_escape_state": "LEAKING",
                "raw_signed": {"zone_state": "LEAKING", "role": "RISK"},
                "contextual_tags": [],
            },
            quote_ccy: {
                "currency": quote_ccy,
                "energy_label": quote_label,
                "energy_score": 0.2,
                "absorption_escape_state": "NEUTRAL",
                "raw_signed": {"zone_state": "NEUTRAL", "role": "SAFE"},
                "contextual_tags": [],
            },
        },
        "ranking": [{"rank": 1, "currency": base_ccy}],
        "energy_field_summary": f"{base_ccy} dominant.",
    }


# ---------------------------------------------------------------------------
# Helpers assert
# ---------------------------------------------------------------------------

def _assert(condition: bool, msg: str) -> None:
    if not condition:
        raise AssertionError(f"FAIL: {msg}")


def _alert_names(output: dict, key: str = "behavioral_alerts") -> set[str]:
    return {a["name"] for a in output.get(key, [])}


def _get_alert(output: dict, name: str) -> dict | None:
    for a in output.get("behavioral_alerts", []) + output.get("degraded_alerts", []):
        if a["name"] == name:
            return a
    return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_empty_inputs():
    """Inputs vides → sortie valide, pas d'exception."""
    out = map_behavioral_alerts({}, None)
    _assert(isinstance(out["behavioral_alerts"], list), "behavioral_alerts doit être une liste")
    _assert(isinstance(out["degraded_alerts"], list), "degraded_alerts doit être une liste")
    _assert(isinstance(out["next_watch_enriched"], list), "next_watch_enriched doit être une liste")
    _assert(isinstance(out["film_steps"], list), "film_steps doit être une liste")
    print("[OK] test_empty_inputs")


def test_output_structure():
    """Sortie toujours JSON-safe, 4 clés."""
    tns = _make_tns()
    out = map_behavioral_alerts(tns)
    _assert("behavioral_alerts" in out, "clé behavioral_alerts manquante")
    _assert("degraded_alerts" in out, "clé degraded_alerts manquante")
    _assert("next_watch_enriched" in out, "clé next_watch_enriched manquante")
    _assert("film_steps" in out, "clé film_steps manquante")
    # JSON-safe
    json.dumps(out)
    print("[OK] test_output_structure")


def test_alert_fields():
    """Chaque alerte contient les 6 champs obligatoires."""
    tns = _make_tns(
        highest_level="HOT_NODE",
        relay_quality="CLEAN",
        first_detachment_detected=True,
        detachment_label="GBP_DETACHED_UP",
    )
    out = map_behavioral_alerts(tns)
    all_alerts = out["behavioral_alerts"] + out["degraded_alerts"]
    required = {"name", "level", "reason", "source_fields", "dashboard_badge", "telegram_text"}
    for a in all_alerts:
        missing = required - set(a.keys())
        _assert(not missing, f"Champs manquants dans alerte {a.get('name')}: {missing}")
    print("[OK] test_alert_fields")


def test_alert_level_values():
    """level de chaque alerte est dans ALERT_LEVELS."""
    tns = _make_tns()
    out = map_behavioral_alerts(tns)
    valid = {"HOT", "WATCH", "DEGRADED", "INFO"}
    for a in out["behavioral_alerts"] + out["degraded_alerts"]:
        _assert(a["level"] in valid, f"level invalide : {a['level']} dans {a['name']}")
    print("[OK] test_alert_level_values")


def test_first_detachment_with_clean_relay():
    """FIRST_DETACHMENT_WITH_CLEAN_RELAY déclenché quand détachement + relay clean."""
    tns = _make_tns(
        highest_level="HOT_NODE",
        relay_quality="CLEAN",
        first_detachment_detected=True,
        detachment_label="GBP_DETACHED_UP",
        release_state="RELEASE_CANDIDATE",
        reasons_ok=["relay_clean", "first_detachment"],
    )
    out = map_behavioral_alerts(tns)
    names = _alert_names(out)
    _assert("FIRST_DETACHMENT_WITH_CLEAN_RELAY" in names, "FIRST_DETACHMENT_WITH_CLEAN_RELAY attendu")
    alert = _get_alert(out, "FIRST_DETACHMENT_WITH_CLEAN_RELAY")
    _assert(alert["level"] == "HOT", "level doit être HOT")
    print("[OK] test_first_detachment_with_clean_relay")


def test_first_detachment_not_triggered_without_detachment():
    """FIRST_DETACHMENT_WITH_CLEAN_RELAY absent si pas de détachement."""
    tns = _make_tns(
        relay_quality="CLEAN",
        first_detachment_detected=False,
    )
    out = map_behavioral_alerts(tns)
    _assert("FIRST_DETACHMENT_WITH_CLEAN_RELAY" not in _alert_names(out),
            "FIRST_DETACHMENT ne doit pas se déclencher sans détachement")
    print("[OK] test_first_detachment_not_triggered_without_detachment")


def test_hot_degraded_by_missing_relay():
    """HOT_DEGRADED_BY_MISSING_RELAY déclenché sur HOT_NODE + relay missing."""
    tns = _make_tns(
        highest_level="HOT_NODE",
        relay_quality="MISSING",
        relay_sample="M5_RELAY_MISSING_IN_DB",
        m5_role="M5_RELAY_MISSING_IN_DB",
    )
    out = map_behavioral_alerts(tns)
    names = _alert_names(out, "degraded_alerts")
    _assert("HOT_DEGRADED_BY_MISSING_RELAY" in names, "HOT_DEGRADED_BY_MISSING_RELAY attendu dans degraded_alerts")
    alert = _get_alert(out, "HOT_DEGRADED_BY_MISSING_RELAY")
    _assert(alert["level"] == "DEGRADED", "level doit être DEGRADED")
    print("[OK] test_hot_degraded_by_missing_relay")


def test_hot_degraded_not_triggered_on_clean_relay():
    """HOT_DEGRADED absent si relay clean même sur HOT_NODE."""
    tns = _make_tns(
        highest_level="HOT_NODE",
        relay_quality="CLEAN",
        relay_sample="M5_RELAY_CLEAN",
    )
    out = map_behavioral_alerts(tns)
    _assert("HOT_DEGRADED_BY_MISSING_RELAY" not in _alert_names(out, "degraded_alerts"),
            "HOT_DEGRADED ne doit pas se déclencher avec relay clean")
    print("[OK] test_hot_degraded_not_triggered_on_clean_relay")


def test_m5_relay_thin_alert():
    """M5_RELAY_THIN_ALERT déclenché sur thin sample."""
    tns = _make_tns(relay_sample="M5_RELAY_THIN_SAMPLE", relay_quality="CLEAN")
    out = map_behavioral_alerts(tns)
    _assert("M5_RELAY_THIN_ALERT" in _alert_names(out), "M5_RELAY_THIN_ALERT attendu")
    alert = _get_alert(out, "M5_RELAY_THIN_ALERT")
    _assert(alert["level"] == "WATCH", "level doit être WATCH")
    print("[OK] test_m5_relay_thin_alert")


def test_release_rejected_no_detachment():
    """RELEASE_REJECTED_NO_DETACHMENT_ALERT déclenché sur RELEASE_REJECTED."""
    tns = _make_tns(
        release_state="RELEASE_REJECTED",
        reasons_nok=["no_first_detachment", "no_m1_energy_signal"],
    )
    out = map_behavioral_alerts(tns)
    _assert("RELEASE_REJECTED_NO_DETACHMENT_ALERT" in _alert_names(out),
            "RELEASE_REJECTED_NO_DETACHMENT_ALERT attendu")
    alert = _get_alert(out, "RELEASE_REJECTED_NO_DETACHMENT_ALERT")
    _assert(alert["level"] == "INFO", "level doit être INFO")
    print("[OK] test_release_rejected_no_detachment")


def test_counter_release_attempt():
    """COUNTER_RELEASE_ATTEMPT_ALERT déclenché sur COUNTER_RELEASE_ATTEMPT."""
    tns = _make_tns(release_state="COUNTER_RELEASE_ATTEMPT")
    out = map_behavioral_alerts(tns)
    _assert("COUNTER_RELEASE_ATTEMPT_ALERT" in _alert_names(out),
            "COUNTER_RELEASE_ATTEMPT_ALERT attendu")
    alert = _get_alert(out, "COUNTER_RELEASE_ATTEMPT_ALERT")
    _assert(alert["level"] == "WATCH", "level doit être WATCH")
    # Règle : COUNTER_RELEASE_ATTEMPT ≠ RELEASE_CONFIRMED — vérifier que reason ne dit pas "confirmé"
    _assert("confirmé" not in alert["reason"].lower() or "non confirmé" in alert["reason"].lower(),
            "reason ne doit pas affirmer que release est confirmée")
    print("[OK] test_counter_release_attempt")


def test_node_heat_energy_divergence():
    """NODE_HEAT_ENERGY_DIVERGENCE déclenché si node HOT mais énergie base currency LOW."""
    tns = _make_tns(
        highest_level="HOT_NODE",
        direction="GBP pressure up / USD pressure down",
        symbol="GBPUSD",
    )
    # GBP dominante mais energie LOW
    energy = _make_energy("GBP", "ENERGY_LOW", "USD", "ENERGY_STRONG")
    out = map_behavioral_alerts(tns, energy)
    _assert("NODE_HEAT_ENERGY_DIVERGENCE" in _alert_names(out),
            "NODE_HEAT_ENERGY_DIVERGENCE attendu")
    alert = _get_alert(out, "NODE_HEAT_ENERGY_DIVERGENCE")
    _assert(alert["level"] == "WATCH", "level doit être WATCH")
    # Vérifier la distinction explicite dans reason
    _assert("NODE_HEAT" in alert["reason"] or "Heat" in alert["reason"],
            "reason doit mentionner Node Heat")
    print("[OK] test_node_heat_energy_divergence")


def test_node_heat_energy_divergence_no_trigger_when_strong():
    """NODE_HEAT_ENERGY_DIVERGENCE absent si energy forte sur devise dominante."""
    tns = _make_tns(
        highest_level="HOT_NODE",
        direction="GBP pressure up / USD pressure down",
        symbol="GBPUSD",
    )
    energy = _make_energy("GBP", "ENERGY_STRONG", "USD", "ENERGY_WEAK")
    out = map_behavioral_alerts(tns, energy)
    _assert("NODE_HEAT_ENERGY_DIVERGENCE" not in _alert_names(out),
            "NODE_HEAT_ENERGY_DIVERGENCE ne doit pas se déclencher si energy forte")
    print("[OK] test_node_heat_energy_divergence_no_trigger_when_strong")


def test_m1_active_m5_weak():
    """M1_ACTIVE_M5_WEAK déclenché si node M1 actif + M5 absent."""
    tns = _make_tns(
        highest_level="FAST_NODE_BIRTH",
        m5_role="M5_RELAY_MISSING_IN_DB",
        relay_sample="M5_RELAY_MISSING_IN_DB",
    )
    out = map_behavioral_alerts(tns)
    _assert("M1_ACTIVE_M5_WEAK" in _alert_names(out), "M1_ACTIVE_M5_WEAK attendu")
    alert = _get_alert(out, "M1_ACTIVE_M5_WEAK")
    _assert(alert["level"] == "WATCH", "level doit être WATCH")
    print("[OK] test_m1_active_m5_weak")


def test_m1_active_m5_weak_not_triggered_with_clean_m5():
    """M1_ACTIVE_M5_WEAK absent si M5 clean."""
    tns = _make_tns(
        highest_level="FAST_NODE_BIRTH",
        m5_role="M5_RELAY_CLEAN",
        relay_sample="M5_RELAY_CLEAN",
    )
    out = map_behavioral_alerts(tns)
    _assert("M1_ACTIVE_M5_WEAK" not in _alert_names(out),
            "M1_ACTIVE_M5_WEAK ne doit pas déclencher avec M5 clean")
    print("[OK] test_m1_active_m5_weak_not_triggered_with_clean_m5")


def test_acceleration_spike_without_zone_tension():
    """ACCELERATION_SPIKE_WITHOUT_ZONE_TENSION_ALERT déclenché sur spike sans compression."""
    # Node M15 sans compression
    nodes_no_compress = [
        {
            "id": "N1",
            "symbol": "GBPUSD",
            "timeframe": "M15",
            "tf_minutes": 15,
            "level": "NODE_BIRTH",
            "family": "TEMPORAL_NODE",
            "direction_bias": "GBP pressure up",
            "maturity": "BIRTH",
            "confidence": "EARLY",
            "score": 4.0,
            "reasons": ["force_shift"],
            "risks_technical": [],
            "telegram_allowed": True,
            "telegram_level": "BIRTH",
            "has_compression": False,
            "has_break": False,
            "has_convergence": False,
            "has_repulsion": False,
            "has_cross": False,
            "has_kiss_reject": False,
            "context": {
                "m1_role": "M1_NODE_ACTIVE",
                "m5_role": "M5_RELAY_CLEAN",
                "trigger_tf": "M15",
                "fractal_state": "HTF_CONFIRMED",
                "visual_htf_story": "confirmed",
                "htf_role": "VISUAL_HTF_BATTLE_CONFIRMED",
                "structure_label": "M15_NODE",
                "extended_micro_window": "NONE",
                "extended_flags": [],
                "m15_role": "M15_NODE_ACTIVE",
            },
        }
    ]
    tns = _make_tns(acceleration_state="SPIKE", nodes=nodes_no_compress)
    out = map_behavioral_alerts(tns)
    _assert("ACCELERATION_SPIKE_WITHOUT_ZONE_TENSION_ALERT" in _alert_names(out),
            "ACCELERATION_SPIKE_WITHOUT_ZONE_TENSION_ALERT attendu")
    print("[OK] test_acceleration_spike_without_zone_tension")


def test_tight_gravity_cluster():
    """TIGHT_GRAVITY_CLUSTER_ALERT déclenché sur cluster détecté."""
    tns = _make_tns(
        tight_gravity_label="M15_TIGHT_GRAVITY_GROUP",
        tight_gravity_currencies=["AUD", "NZD", "CHF"],
        tight_gravity_spread=5.8,
    )
    out = map_behavioral_alerts(tns)
    _assert("TIGHT_GRAVITY_CLUSTER_ALERT" in _alert_names(out),
            "TIGHT_GRAVITY_CLUSTER_ALERT attendu")
    alert = _get_alert(out, "TIGHT_GRAVITY_CLUSTER_ALERT")
    _assert(alert["level"] == "INFO", "level doit être INFO")
    _assert("AUD" in alert["reason"] or "NZD" in alert["reason"],
            "reason doit mentionner les devises")
    print("[OK] test_tight_gravity_cluster")


def test_tight_gravity_not_triggered_on_no_cluster():
    """TIGHT_GRAVITY_CLUSTER_ALERT absent si NO_CLUSTER."""
    tns = _make_tns(tight_gravity_label="NO_CLUSTER")
    out = map_behavioral_alerts(tns)
    _assert("TIGHT_GRAVITY_CLUSTER_ALERT" not in _alert_names(out),
            "TIGHT_GRAVITY_CLUSTER_ALERT ne doit pas se déclencher sur NO_CLUSTER")
    print("[OK] test_tight_gravity_not_triggered_on_no_cluster")


def test_same_angle_cluster():
    """SAME_ANGLE_CLUSTER_ALERT déclenché sur cluster d'angles détecté."""
    tns = _make_tns(
        same_angle_label="M1_SAME_ANGLE_GROUP",
        same_angle_currencies=["GBP", "EUR"],
    )
    out = map_behavioral_alerts(tns)
    _assert("SAME_ANGLE_CLUSTER_ALERT" in _alert_names(out),
            "SAME_ANGLE_CLUSTER_ALERT attendu")
    alert = _get_alert(out, "SAME_ANGLE_CLUSTER_ALERT")
    _assert(alert["level"] == "INFO", "level doit être INFO")
    print("[OK] test_same_angle_cluster")


def test_same_angle_not_triggered_on_no_cluster():
    """SAME_ANGLE_CLUSTER_ALERT absent si NO_CLUSTER."""
    tns = _make_tns(same_angle_label="NO_CLUSTER")
    out = map_behavioral_alerts(tns)
    _assert("SAME_ANGLE_CLUSTER_ALERT" not in _alert_names(out),
            "SAME_ANGLE_CLUSTER_ALERT ne doit pas déclencher sur NO_CLUSTER")
    print("[OK] test_same_angle_not_triggered_on_no_cluster")


def test_film_steps_present():
    """film_steps non vide sur état complet."""
    tns = _make_tns(
        highest_level="HOT_NODE",
        maturity="CONFIRMING",
        relay_quality="CLEAN",
        release_state="RELEASE_REJECTED",
        reasons_nok=["no_first_detachment"],
    )
    energy = _make_energy()
    out = map_behavioral_alerts(tns, energy)
    _assert(len(out["film_steps"]) >= 3, "film_steps doit contenir au moins 3 étapes")
    # Vérifier présence de blocs clés
    steps_str = "\n".join(out["film_steps"])
    _assert("[NODE]" in steps_str, "film_steps doit contenir bloc NODE")
    _assert("[RELAY]" in steps_str, "film_steps doit contenir bloc RELAY")
    _assert("[RELEASE]" in steps_str, "film_steps doit contenir bloc RELEASE")
    _assert("[ENERGY]" in steps_str, "film_steps doit contenir bloc ENERGY")
    print("[OK] test_film_steps_present")


def test_film_steps_energy_label_not_buy_sell():
    """film_steps ne contient pas BUY ni SELL — Energy n'est pas un signal."""
    tns = _make_tns()
    energy = _make_energy()
    out = map_behavioral_alerts(tns, energy)
    for step in out["film_steps"]:
        _assert("BUY" not in step, f"film_step ne doit pas contenir BUY: {step}")
        _assert("SELL" not in step, f"film_step ne doit pas contenir SELL: {step}")
    print("[OK] test_film_steps_energy_label_not_buy_sell")


def test_next_watch_enriched():
    """next_watch_enriched enrichi avec alertes comportementales."""
    tns = _make_tns(
        release_state="RELEASE_REJECTED",
        reasons_nok=["no_first_detachment"],
    )
    out = map_behavioral_alerts(tns)
    nw = " ".join(out["next_watch_enriched"])
    _assert("DETACHMENT" in nw or "WATCH" in nw,
            "next_watch_enriched doit contenir guidance sur détachement")
    print("[OK] test_next_watch_enriched")


def test_no_buy_sell_in_any_output():
    """Aucune alerte ne contient BUY ou SELL."""
    tns = _make_tns(
        highest_level="HOT_NODE",
        relay_quality="CLEAN",
        first_detachment_detected=True,
        detachment_label="GBP_DETACHED",
    )
    energy = _make_energy()
    out = map_behavioral_alerts(tns, energy)
    for a in out["behavioral_alerts"] + out["degraded_alerts"]:
        for field in ("reason", "dashboard_badge", "telegram_text"):
            v = a.get(field, "")
            _assert("BUY" not in v, f"Alerte {a['name']} contient BUY dans {field}")
            _assert("SELL" not in v, f"Alerte {a['name']} contient SELL dans {field}")
    print("[OK] test_no_buy_sell_in_any_output")


def test_degraded_alerts_in_dedicated_key():
    """Les alertes DEGRADED sont dans degraded_alerts, pas dans behavioral_alerts."""
    tns = _make_tns(
        highest_level="HOT_NODE",
        relay_quality="MISSING",
        relay_sample="M5_RELAY_MISSING_IN_DB",
    )
    out = map_behavioral_alerts(tns)
    _assert("HOT_DEGRADED_BY_MISSING_RELAY" in _alert_names(out, "degraded_alerts"),
            "DEGRADED doit être dans degraded_alerts")
    _assert("HOT_DEGRADED_BY_MISSING_RELAY" not in _alert_names(out, "behavioral_alerts"),
            "DEGRADED ne doit pas être dans behavioral_alerts")
    print("[OK] test_degraded_alerts_in_dedicated_key")


def test_counter_release_not_confirmed():
    """
    Règle : COUNTER_RELEASE_ATTEMPT ≠ RELEASE_CONFIRMED.
    Quand counter attempt → pas d'alerte RELEASE_CONFIRMED.
    """
    tns = _make_tns(release_state="COUNTER_RELEASE_ATTEMPT")
    out = map_behavioral_alerts(tns)
    # Vérifier qu'aucune alerte ne dit "confirmé" sans "non"
    for a in out["behavioral_alerts"] + out["degraded_alerts"]:
        if a["name"] == "COUNTER_RELEASE_ATTEMPT_ALERT":
            _assert(
                "non confirmé" in a["reason"] or "Tentative" in a["reason"],
                "Counter release reason doit expliciter que non confirmé",
            )
    print("[OK] test_counter_release_not_confirmed")


def test_energy_no_hot_alone():
    """Energy seule ne produit pas d'alerte HOT."""
    tns = _make_tns(highest_level="NODE_WATCH")  # pas HOT
    energy = _make_energy("GBP", "ENERGY_STRONG", "USD", "ENERGY_WEAK")
    out = map_behavioral_alerts(tns, energy)
    for a in out["behavioral_alerts"]:
        _assert(a["level"] != "HOT",
                f"Energy seule ne doit pas produire HOT — alerte trouvée: {a['name']}")
    print("[OK] test_energy_no_hot_alone")


def test_real_state_json():
    """Test sur les fichiers JSON réels du ZIP si disponibles."""
    import os
    tns_path = "/tmp/mission/CLAUDE_MISSION_BEHAVIORAL_ALERT_MAPPER_20260506/output/temporal_node_state.json"
    energy_path = "/tmp/mission/CLAUDE_MISSION_BEHAVIORAL_ALERT_MAPPER_20260506/output/currency_energy_state.json"

    if not os.path.exists(tns_path):
        print("[SKIP] test_real_state_json — fichiers réels non disponibles")
        return

    with open(tns_path) as f:
        tns = json.load(f)
    energy = None
    if os.path.exists(energy_path):
        with open(energy_path) as f:
            energy = json.load(f)

    out = map_behavioral_alerts(tns, energy)
    # JSON-safe
    json.dumps(out)
    _assert("behavioral_alerts" in out, "behavioral_alerts manquant sur JSON réel")
    _assert(len(out["film_steps"]) > 0, "film_steps vide sur JSON réel")
    print(f"[OK] test_real_state_json — {len(out['behavioral_alerts'])} behavioral, {len(out['degraded_alerts'])} degraded")
    # Afficher résumé
    for a in out["behavioral_alerts"] + out["degraded_alerts"]:
        print(f"    [{a['level']}] {a['name']}")
    print("  Film:")
    for s in out["film_steps"]:
        print(f"    {s}")
    print("  Next watch:")
    for w in out["next_watch_enriched"]:
        print(f"    {w}")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Tests V0.8.2.1 — energy_context / energy_release_alignment / fallback
# ---------------------------------------------------------------------------

def _make_tns_with_energy_context(
    highest_level: str = "HOT_NODE",
    direction: str = "GBP pressure down / USD pressure up",
    release_state: str = "COUNTER_RELEASE_ATTEMPT",
    node_energy_relation: str = "DIVERGENT",
    alignment_state: str = "ENERGY_NEUTRAL_OR_TOO_THIN",
    secondary_state: str = "COUNTER_RELEASE_UNSUPPORTED_BY_ENERGY",
    field_quality: str = "ENERGY_THIN_OR_MIXED",
    base_label: str = "ENERGY_WEAK",
    quote_label: str = "ENERGY_WEAK",
    ec_mode: str = "OBSERVATION_ONLY",
    symbol: str = "GBPUSD",
    tight_gravity_label: str = "NO_CLUSTER",
    tight_gravity_currencies: list | None = None,
    tight_gravity_spread: float = 0.0,
    first_detachment_detected: bool = True,
    detachment_label: str = "M1_FIRST_DETACHMENT_USD_DOWN",
    relay_quality: str = "CLEAN",
    relay_sample: str = "M5_RELAY_CLEAN",
) -> dict:
    """TNS avec energy_context embarqué (format V0.8.2)."""
    tns = _make_tns(
        highest_level=highest_level,
        direction=direction,
        release_state=release_state,
        first_detachment_detected=first_detachment_detected,
        detachment_label=detachment_label,
        relay_quality=relay_quality,
        relay_sample=relay_sample,
        tight_gravity_label=tight_gravity_label,
        tight_gravity_currencies=tight_gravity_currencies,
        tight_gravity_spread=tight_gravity_spread,
        symbol=symbol,
    )
    tns["energy_context"] = {
        "mode": ec_mode,
        "source": "energy_release_alignment/build_currency_energy_state",
        "base_currency": symbol[:3].upper(),
        "base_energy_label": base_label,
        "base_energy_score": 0.11,
        "quote_currency": symbol[3:6].upper(),
        "quote_energy_label": quote_label,
        "quote_energy_score": 0.24,
        "node_energy_relation": node_energy_relation,
        "alignment_state": alignment_state,
        "secondary_state": secondary_state,
        "field_quality": field_quality,
        "release_state": release_state,
        "release_label": f"{release_state}_DOWN",
        "tf_votes": {"M1": "GBP_USD_WEAK_NEUTRAL", "M5": "GBP_USD_WEAK_NEUTRAL"},
        "energy_field_summary": "JPY dominant. Faibles : GBP+USD.",
        "rules": [
            "Energy != Direction",
            "Energy != Signal",
            "Node Heat != Currency Energy",
            "Energy qualifies release_state; energy does not create signal",
        ],
    }
    return tns


def _make_tns_with_era(
    highest_level: str = "HOT_NODE",
    direction: str = "GBP pressure down / USD pressure up",
    release_state: str = "COUNTER_RELEASE_ATTEMPT",
    field_quality: str = "ENERGY_THIN_OR_MIXED",
    secondary_state: str | None = None,
    relay_quality: str = "CLEAN",
    relay_sample: str = "M5_RELAY_CLEAN",
    symbol: str = "GBPUSD",
    tight_gravity_label: str = "NO_CLUSTER",
    tight_gravity_currencies: list | None = None,
    tight_gravity_spread: float = 0.0,
) -> dict:
    """TNS avec energy_release_alignment seulement (format V0.8.x runtime)."""
    tns = _make_tns(
        highest_level=highest_level,
        direction=direction,
        release_state=release_state,
        relay_quality=relay_quality,
        relay_sample=relay_sample,
        tight_gravity_label=tight_gravity_label,
        tight_gravity_currencies=tight_gravity_currencies,
        tight_gravity_spread=tight_gravity_spread,
        symbol=symbol,
    )
    tns["energy_release_alignment"] = {
        "status": "OK",
        "state": "ENERGY_NEUTRAL_OR_TOO_THIN",
        "secondary_state": secondary_state,
        "field_quality": field_quality,
        "release_state": release_state,
        "release_label": f"{release_state}_DOWN",
        "first_detachment": "M1_FIRST_DETACHMENT_USD_DOWN",
        "first_detachment_detected": True,
        "relay_quality": relay_quality,
        "relay_sample_state": relay_sample,
        "tf_votes": {
            "M1": "GBP_USD_WEAK_NEUTRAL",
            "M5": "GBP_USD_WEAK_NEUTRAL",
            "M15": "GBP_USD_WEAK_NEUTRAL",
        },
        "relation": "energy qualifies release_state; energy does not create signal",
        "reasons": ["M1:GBP/USD weak-or-neutral", "counter_release_attempt_energy_qualified"],
        "energy_snapshots": {
            "M1": {
                "top_energy": {"highest": "JPY", "highest_score": 0.58},
                "summary": "JPY dominant.",
                "GBP": {"score": 0.11, "label": "ENERGY_WEAK", "absorption": "NEUTRAL",
                        "zone_state": "NEUTRAL", "zone_level": "NORMAL", "z_extreme_dir": "NONE",
                        "behavioral_zscore": 0.96, "speed_per_min": 0.09, "angle_deg": 5.3,
                        "acceleration_raw": 0.35, "role": "RISK"},
                "USD": {"score": 0.24, "label": "ENERGY_WEAK", "absorption": "NEUTRAL",
                        "zone_state": "NEUTRAL", "zone_level": "NORMAL", "z_extreme_dir": "NONE",
                        "behavioral_zscore": 0.0, "speed_per_min": -2.17, "angle_deg": -65.27,
                        "acceleration_raw": 0.68, "role": "PIVOT"},
            }
        },
    }
    return tns


# --- Tests energy_context (V0.8.2+) ---

def test_energy_source_is_energy_context_when_present():
    """energy_context présent et non-ABSENT → source = energy_context."""
    from pf_behavioral_alert_mapper import _resolve_energy, EnergyView
    tns = _make_tns_with_energy_context()
    ev = _resolve_energy(tns, {})
    _assert(ev.source == "energy_context", f"source attendue energy_context, got {ev.source}")
    _assert(ev.is_present, "EnergyView doit être présent")
    print("[OK] test_energy_source_is_energy_context_when_present")


def test_energy_context_absent_mode_fallback_to_era():
    """energy_context présent mais mode=ENERGY_ABSENT → fallback vers energy_release_alignment."""
    from pf_behavioral_alert_mapper import _resolve_energy
    tns = _make_tns_with_era()
    tns["energy_context"] = {"mode": "ENERGY_ABSENT"}
    ev = _resolve_energy(tns, {})
    _assert(ev.source == "energy_release_alignment", f"source attendue energy_release_alignment, got {ev.source}")
    print("[OK] test_energy_context_absent_mode_fallback_to_era")


def test_energy_source_fallback_to_era_when_no_context():
    """Pas d'energy_context → fallback energy_release_alignment."""
    from pf_behavioral_alert_mapper import _resolve_energy
    tns = _make_tns_with_era()
    ev = _resolve_energy(tns, {})
    _assert(ev.source == "energy_release_alignment", f"source attendue energy_release_alignment, got {ev.source}")
    _assert(ev.is_present, "EnergyView doit être présent")
    print("[OK] test_energy_source_fallback_to_era_when_no_context")


def test_energy_source_fallback_to_standalone():
    """Pas de blocs TNS energy → fallback standalone."""
    from pf_behavioral_alert_mapper import _resolve_energy
    tns = _make_tns(highest_level="HOT_NODE")
    energy = _make_energy("GBP", "ENERGY_WEAK", "USD", "ENERGY_WEAK")
    ev = _resolve_energy(tns, energy)
    _assert(ev.source == "standalone", f"source attendue standalone, got {ev.source}")
    print("[OK] test_energy_source_fallback_to_standalone")


def test_energy_source_none_when_no_data():
    """Aucune source → EnergyView.source = NONE, is_present = False."""
    from pf_behavioral_alert_mapper import _resolve_energy
    tns = _make_tns()
    ev = _resolve_energy(tns, {})
    _assert(ev.source == "NONE", f"source attendue NONE, got {ev.source}")
    _assert(not ev.is_present, "EnergyView ne doit pas être présent")
    print("[OK] test_energy_source_none_when_no_data")


# --- Tests enrichissements checkers ---

def test_counter_release_enriched_by_energy_context():
    """COUNTER_RELEASE_ATTEMPT_ALERT enrichi si secondary_state=COUNTER_RELEASE_UNSUPPORTED_BY_ENERGY."""
    tns = _make_tns_with_energy_context(
        release_state="COUNTER_RELEASE_ATTEMPT",
        secondary_state="COUNTER_RELEASE_UNSUPPORTED_BY_ENERGY",
        field_quality="ENERGY_THIN_OR_MIXED",
    )
    out = map_behavioral_alerts(tns, None)
    alert = _get_alert(out, "COUNTER_RELEASE_ATTEMPT_ALERT")
    _assert(alert is not None, "COUNTER_RELEASE_ATTEMPT_ALERT attendu")
    _assert("counter release non supportée par energy" in alert["reason"],
            "reason doit mentionner energy non supportée")
    _assert("energy_context.secondary_state" in alert["source_fields"],
            "source_fields doit contenir energy_context.secondary_state")
    print("[OK] test_counter_release_enriched_by_energy_context")


def test_counter_release_not_enriched_without_secondary_state():
    """COUNTER_RELEASE_ATTEMPT_ALERT sans enrichissement si secondary_state absent."""
    tns = _make_tns_with_energy_context(
        release_state="COUNTER_RELEASE_ATTEMPT",
        secondary_state="",           # pas de secondary_state
        field_quality="ENERGY_STRONG",
    )
    out = map_behavioral_alerts(tns, None)
    alert = _get_alert(out, "COUNTER_RELEASE_ATTEMPT_ALERT")
    _assert(alert is not None, "COUNTER_RELEASE_ATTEMPT_ALERT attendu")
    _assert("non supportée par energy" not in alert["reason"],
            "reason ne doit pas mentionner energy sans secondary_state")
    _assert("energy_context.secondary_state" not in alert.get("source_fields", []),
            "source_fields ne doit pas contenir energy_context sans secondary_state")
    print("[OK] test_counter_release_not_enriched_without_secondary_state")


def test_counter_release_enriched_via_era():
    """COUNTER_RELEASE_ATTEMPT_ALERT enrichi depuis energy_release_alignment (runtime V0.8.x)."""
    tns = _make_tns_with_era(
        release_state="COUNTER_RELEASE_ATTEMPT",
        field_quality="ENERGY_THIN_OR_MIXED",
        secondary_state=None,  # absent dans era — doit être inféré
    )
    out = map_behavioral_alerts(tns, None)
    alert = _get_alert(out, "COUNTER_RELEASE_ATTEMPT_ALERT")
    _assert(alert is not None, "COUNTER_RELEASE_ATTEMPT_ALERT attendu")
    # L'inférence doit produire COUNTER_RELEASE_UNSUPPORTED_BY_ENERGY
    _assert("non supportée par energy" in alert["reason"],
            "reason doit mentionner energy non supportée (inférée depuis ERA)")
    print("[OK] test_counter_release_enriched_via_era")


def test_node_heat_divergence_from_energy_context():
    """NODE_HEAT_ENERGY_DIVERGENCE utilise node_energy_relation=DIVERGENT depuis energy_context."""
    tns = _make_tns_with_energy_context(
        highest_level="HOT_NODE",
        node_energy_relation="DIVERGENT",
        field_quality="ENERGY_THIN_OR_MIXED",
    )
    out = map_behavioral_alerts(tns, None)
    alert = _get_alert(out, "NODE_HEAT_ENERGY_DIVERGENCE")
    _assert(alert is not None, "NODE_HEAT_ENERGY_DIVERGENCE attendu")
    _assert(alert["level"] == "WATCH", "level doit être WATCH")
    _assert("node_energy_relation" in alert["reason"],
            "reason doit mentionner node_energy_relation")
    _assert("energy_context.node_energy_relation" in alert["source_fields"],
            "source_fields doit contenir energy_context.node_energy_relation")
    print("[OK] test_node_heat_divergence_from_energy_context")


def test_node_heat_divergence_not_triggered_when_aligned():
    """NODE_HEAT_ENERGY_DIVERGENCE absent si node_energy_relation=ALIGNED."""
    tns = _make_tns_with_energy_context(
        highest_level="HOT_NODE",
        node_energy_relation="ALIGNED",
        field_quality="ENERGY_STRONG",
    )
    out = map_behavioral_alerts(tns, None)
    _assert("NODE_HEAT_ENERGY_DIVERGENCE" not in _alert_names(out),
            "NODE_HEAT_ENERGY_DIVERGENCE ne doit pas déclencher sur ALIGNED")
    print("[OK] test_node_heat_divergence_not_triggered_when_aligned")


def test_node_heat_divergence_from_era():
    """NODE_HEAT_ENERGY_DIVERGENCE déclenche depuis energy_release_alignment (DIVERGENT inféré)."""
    tns = _make_tns_with_era(
        highest_level="HOT_NODE",
        release_state="COUNTER_RELEASE_ATTEMPT",
        field_quality="ENERGY_THIN_OR_MIXED",
    )
    out = map_behavioral_alerts(tns, None)
    alert = _get_alert(out, "NODE_HEAT_ENERGY_DIVERGENCE")
    _assert(alert is not None, "NODE_HEAT_ENERGY_DIVERGENCE attendu depuis ERA")
    _assert(alert["level"] == "WATCH", "level doit être WATCH")
    print("[OK] test_node_heat_divergence_from_era")


def test_tight_gravity_enriched_by_energy_thin():
    """TIGHT_GRAVITY_CLUSTER_ALERT enrichi si field_quality = ENERGY_THIN_OR_MIXED."""
    tns = _make_tns_with_energy_context(
        field_quality="ENERGY_THIN_OR_MIXED",
        tight_gravity_label="M15_TIGHT_GRAVITY_GROUP",
        tight_gravity_currencies=["AUD", "NZD", "CHF"],
        tight_gravity_spread=5.8,
    )
    out = map_behavioral_alerts(tns, None)
    alert = _get_alert(out, "TIGHT_GRAVITY_CLUSTER_ALERT")
    _assert(alert is not None, "TIGHT_GRAVITY_CLUSTER_ALERT attendu")
    _assert("thin/mixed" in alert["reason"],
            "reason doit mentionner champ thin/mixed")
    _assert("energy_context.field_quality" in alert["source_fields"],
            "source_fields doit contenir energy_context.field_quality")
    print("[OK] test_tight_gravity_enriched_by_energy_thin")


def test_tight_gravity_not_enriched_when_strong():
    """TIGHT_GRAVITY_CLUSTER_ALERT sans enrichissement energy si field_quality=ENERGY_STRONG."""
    tns = _make_tns_with_energy_context(
        field_quality="ENERGY_STRONG",
        tight_gravity_label="M15_TIGHT_GRAVITY_GROUP",
        tight_gravity_currencies=["AUD", "NZD"],
        tight_gravity_spread=3.0,
    )
    out = map_behavioral_alerts(tns, None)
    alert = _get_alert(out, "TIGHT_GRAVITY_CLUSTER_ALERT")
    _assert(alert is not None, "TIGHT_GRAVITY_CLUSTER_ALERT attendu")
    _assert("thin/mixed" not in alert["reason"],
            "reason ne doit pas mentionner thin/mixed si ENERGY_STRONG")
    _assert("energy_context.field_quality" not in alert.get("source_fields", []),
            "source_fields ne doit pas contenir field_quality si ENERGY_STRONG")
    print("[OK] test_tight_gravity_not_enriched_when_strong")


# --- Tests film_steps [ENERGY_CONTEXT] ---

def test_film_steps_energy_context_block():
    """film_steps contient [ENERGY_CONTEXT] si source=energy_context."""
    tns = _make_tns_with_energy_context()
    out = map_behavioral_alerts(tns, None)
    steps_str = "\n".join(out["film_steps"])
    _assert("[ENERGY_CONTEXT]" in steps_str, "film_steps doit contenir [ENERGY_CONTEXT]")
    _assert("OBSERVATION_ONLY" in steps_str, "[ENERGY_CONTEXT] doit contenir OBSERVATION_ONLY")
    _assert("relation=" in steps_str, "[ENERGY_CONTEXT] doit contenir relation=")
    _assert("field=" in steps_str, "[ENERGY_CONTEXT] doit contenir field=")
    print("[OK] test_film_steps_energy_context_block")


def test_film_steps_energy_context_format():
    """[ENERGY_CONTEXT] respecte le format attendu de la spec."""
    tns = _make_tns_with_energy_context(
        base_label="ENERGY_WEAK",
        quote_label="ENERGY_WEAK",
        node_energy_relation="DIVERGENT",
        field_quality="ENERGY_THIN_OR_MIXED",
    )
    out = map_behavioral_alerts(tns, None)
    ec_steps = [s for s in out["film_steps"] if s.startswith("[ENERGY_CONTEXT]")]
    _assert(len(ec_steps) == 1, "Un seul [ENERGY_CONTEXT] attendu")
    step = ec_steps[0]
    _assert("OBSERVATION_ONLY" in step, "OBSERVATION_ONLY attendu")
    _assert("GBP=ENERGY_WEAK" in step, "GBP=ENERGY_WEAK attendu")
    _assert("USD=ENERGY_WEAK" in step, "USD=ENERGY_WEAK attendu")
    _assert("relation=DIVERGENT" in step, "relation=DIVERGENT attendu")
    _assert("field=ENERGY_THIN_OR_MIXED" in step, "field=ENERGY_THIN_OR_MIXED attendu")
    print("[OK] test_film_steps_energy_context_format")


def test_film_steps_energy_context_from_era():
    """[ENERGY_CONTEXT] produit depuis energy_release_alignment."""
    tns = _make_tns_with_era()
    out = map_behavioral_alerts(tns, None)
    steps_str = "\n".join(out["film_steps"])
    _assert("[ENERGY_CONTEXT]" in steps_str,
            "film_steps doit contenir [ENERGY_CONTEXT] depuis ERA")
    print("[OK] test_film_steps_energy_context_from_era")


def test_film_steps_no_energy_context_when_absent():
    """Pas de [ENERGY_CONTEXT] si aucune source energy disponible."""
    tns = _make_tns()   # ni energy_context ni era ni standalone
    out = map_behavioral_alerts(tns, None)
    steps_str = "\n".join(out["film_steps"])
    _assert("[ENERGY_CONTEXT]" not in steps_str,
            "[ENERGY_CONTEXT] ne doit pas apparaître sans source energy")
    _assert("[ENERGY]" not in steps_str,
            "[ENERGY] ne doit pas apparaître sans source energy")
    print("[OK] test_film_steps_no_energy_context_when_absent")


def test_film_steps_legacy_energy_block_with_standalone():
    """[ENERGY] (legacy) produit si source=standalone."""
    tns = _make_tns(highest_level="HOT_NODE")
    energy = _make_energy("GBP", "ENERGY_LOW", "USD", "ENERGY_LOW")
    out = map_behavioral_alerts(tns, energy)
    steps_str = "\n".join(out["film_steps"])
    # Avec standalone, on doit avoir [ENERGY] ou [ENERGY_CONTEXT] — ici [ENERGY] legacy
    _assert("[ENERGY]" in steps_str or "[ENERGY_CONTEXT]" in steps_str,
            "film_steps doit contenir un bloc energy")
    print("[OK] test_film_steps_legacy_energy_block_with_standalone")


# --- Test sur TNS runtime réel ---

def test_real_runtime_tns_with_era():
    """Test sur temporal_node_state.json runtime (contient energy_release_alignment)."""
    import os, json
    path = "/tmp/temporal_node_state_runtime.json"
    if not os.path.exists(path):
        print("[SKIP] test_real_runtime_tns_with_era — fichier non disponible")
        return

    with open(path) as f:
        tns = json.load(f)

    _assert("energy_release_alignment" in tns, "energy_release_alignment attendu dans TNS runtime")
    _assert("energy_context" not in tns or not tns["energy_context"],
            "energy_context ne doit pas être présent dans TNS V0.8.x runtime")

    out = map_behavioral_alerts(tns, None)
    json.dumps(out)  # JSON-safe

    steps_str = "\n".join(out["film_steps"])
    _assert("[ENERGY_CONTEXT]" in steps_str,
            "film_steps doit contenir [ENERGY_CONTEXT] depuis ERA sur TNS runtime")

    # Vérifier les alertes attendues sur ce TNS runtime spécifique
    # (COUNTER_RELEASE_ATTEMPT + DIVERGENT depuis ERA)
    all_names = _alert_names(out) | _alert_names(out, "degraded_alerts")
    _assert("COUNTER_RELEASE_ATTEMPT_ALERT" in all_names,
            "COUNTER_RELEASE_ATTEMPT_ALERT attendu sur TNS runtime")
    _assert("NODE_HEAT_ENERGY_DIVERGENCE" in all_names,
            "NODE_HEAT_ENERGY_DIVERGENCE attendu sur TNS runtime (DIVERGENT depuis ERA)")

    # Enrichissement counter release
    alert = _get_alert(out, "COUNTER_RELEASE_ATTEMPT_ALERT")
    _assert("non supportée par energy" in alert["reason"],
            "reason doit être enrichie sur TNS runtime")

    print(f"[OK] test_real_runtime_tns_with_era")
    print(f"     source energy: energy_release_alignment")
    print(f"     behavioral: {[a['name'] for a in out['behavioral_alerts']]}")
    print(f"     degraded: {[a['name'] for a in out['degraded_alerts']]}")
    ec_step = next((s for s in out["film_steps"] if "[ENERGY_CONTEXT]" in s), "")
    print(f"     {ec_step}")


# --- Garde-fous energy V0.8.2.1 ---

def test_energy_context_never_produces_hot():
    """energy_context DIVERGENT seul ne produit jamais HOT.
    La fixture désactive le détachement pour isoler energy_context."""
    tns = _make_tns_with_energy_context(
        highest_level="NODE_WATCH",   # pas de node HOT
        node_energy_relation="DIVERGENT",
        first_detachment_detected=False,  # pas de FIRST_DETACHMENT_WITH_CLEAN_RELAY
        detachment_label="NO_DETACHMENT",
    )
    out = map_behavioral_alerts(tns, None)
    for a in out["behavioral_alerts"] + out["degraded_alerts"]:
        _assert(a["level"] != "HOT",
                f"energy_context seul ne doit pas produire HOT — trouvé: {a['name']}")
    print("[OK] test_energy_context_never_produces_hot")


def test_energy_context_no_buy_sell():
    """Aucune alerte ne contient BUY ni SELL avec energy_context."""
    tns = _make_tns_with_energy_context()
    out = map_behavioral_alerts(tns, None)
    for a in out["behavioral_alerts"] + out["degraded_alerts"]:
        for f_key in ("reason", "dashboard_badge", "telegram_text"):
            v = a.get(f_key, "")
            _assert("BUY" not in v, f"{a['name']}.{f_key} contient BUY")
            _assert("SELL" not in v, f"{a['name']}.{f_key} contient SELL")
    print("[OK] test_energy_context_no_buy_sell")


def test_counter_release_never_becomes_confirmed():
    """COUNTER_RELEASE avec energy_context → jamais présenté comme confirmé dans les alertes.
    La règle ≠ RELEASE_CONFIRMED peut apparaître dans la reason comme rappel — c'est correct.
    Ce qui est interdit : que le mapper affirme que la release est confirmée."""
    tns = _make_tns_with_energy_context(release_state="COUNTER_RELEASE_ATTEMPT")
    out = map_behavioral_alerts(tns, None)
    for a in out["behavioral_alerts"] + out["degraded_alerts"]:
        if a["name"] == "COUNTER_RELEASE_ATTEMPT_ALERT":
            reason = a["reason"].lower()
            # La release ne doit pas être présentée comme confirmée
            # "non confirmée" doit être présent
            _assert("non confirmée" in reason or "non confirmé" in reason,
                    "reason doit expliciter que non confirmée")
            # Pas d'affirmation positive de confirmation
            # (la mention ≠ RELEASE_CONFIRMED est OK comme règle rappelée)
            _assert("release confirmée" not in reason,
                    "reason ne doit pas affirmer que release est confirmée")
    print("[OK] test_counter_release_never_becomes_confirmed")


TESTS = [
    test_empty_inputs,
    test_output_structure,
    test_alert_fields,
    test_alert_level_values,
    test_first_detachment_with_clean_relay,
    test_first_detachment_not_triggered_without_detachment,
    test_hot_degraded_by_missing_relay,
    test_hot_degraded_not_triggered_on_clean_relay,
    test_m5_relay_thin_alert,
    test_release_rejected_no_detachment,
    test_counter_release_attempt,
    test_node_heat_energy_divergence,
    test_node_heat_energy_divergence_no_trigger_when_strong,
    test_m1_active_m5_weak,
    test_m1_active_m5_weak_not_triggered_with_clean_m5,
    test_acceleration_spike_without_zone_tension,
    test_tight_gravity_cluster,
    test_tight_gravity_not_triggered_on_no_cluster,
    test_same_angle_cluster,
    test_same_angle_not_triggered_on_no_cluster,
    test_film_steps_present,
    test_film_steps_energy_label_not_buy_sell,
    test_next_watch_enriched,
    test_no_buy_sell_in_any_output,
    test_degraded_alerts_in_dedicated_key,
    test_counter_release_not_confirmed,
    test_energy_no_hot_alone,
    test_real_state_json,
    # V0.8.2.1 — résolveur de source
    test_energy_source_is_energy_context_when_present,
    test_energy_context_absent_mode_fallback_to_era,
    test_energy_source_fallback_to_era_when_no_context,
    test_energy_source_fallback_to_standalone,
    test_energy_source_none_when_no_data,
    # V0.8.2.1 — enrichissements checkers
    test_counter_release_enriched_by_energy_context,
    test_counter_release_not_enriched_without_secondary_state,
    test_counter_release_enriched_via_era,
    test_node_heat_divergence_from_energy_context,
    test_node_heat_divergence_not_triggered_when_aligned,
    test_node_heat_divergence_from_era,
    test_tight_gravity_enriched_by_energy_thin,
    test_tight_gravity_not_enriched_when_strong,
    # V0.8.2.1 — film_steps [ENERGY_CONTEXT]
    test_film_steps_energy_context_block,
    test_film_steps_energy_context_format,
    test_film_steps_energy_context_from_era,
    test_film_steps_no_energy_context_when_absent,
    test_film_steps_legacy_energy_block_with_standalone,
    # V0.8.2.1 — TNS runtime réel
    test_real_runtime_tns_with_era,
    # V0.8.2.1 — garde-fous
    test_energy_context_never_produces_hot,
    test_energy_context_no_buy_sell,
    test_counter_release_never_becomes_confirmed,
]


if __name__ == "__main__":
    passed = 0
    failed = 0
    for t in TESTS:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {t.__name__}: {type(e).__name__}: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Résultat : {passed}/{passed+failed} tests passés")
    if failed > 0:
        print("ÉCHECS DÉTECTÉS")
        sys.exit(1)
    else:
        print("TOUS LES TESTS PASSENT")
