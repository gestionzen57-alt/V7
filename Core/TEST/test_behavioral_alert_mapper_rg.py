"""
test_behavioral_alert_mapper_rg.py
PowerFlow V6 — Tests unitaires pour pf_relational_gravity_alerts.py

Couvre :
- les 6 règles d'alerte
- les cas de fallback (bloc absent, malformé)
- les niveaux HOT / WATCH / INFO
- la sérialisation

Usage :
    python test_behavioral_alert_mapper_rg.py
"""

import sys
from pf_relational_gravity_alerts import (
    extract_relational_gravity_alerts,
    rg_alert_to_dict,
    ALERT_ALIGNED,
    ALERT_LEADER_PULLING,
    ALERT_M1_COUNTERFIELD,
    ALERT_M5_M15_ALIGNMENT,
    ALERT_COALITION_ANTAGONIST,
    ALERT_MIXED_INFO,
    LEVEL_HOT, LEVEL_WATCH, LEVEL_INFO,
)


# ─────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────

def _tf_detail(
    direction: str = "UP",
    leader: str = "GBP",
    antagonist: str = "USD",
    score: float = 0.90,
    signatures: list[str] | None = None,
    status: str = "OK",
) -> dict:
    return {
        "loaded": True,
        "source_file": "output/test.json",
        "status": status,
        "primary_state": "LEADER_PULLING_AWAY",
        "group": ["GBP", "EUR"],
        "direction": direction,
        "gap_mode": "EXPANDING",
        "leader": leader,
        "antagonist": antagonist,
        "score": score,
        "confidence": "HIGH",
        "lab_signatures": signatures or ["LEADER_PULLING_AWAY", "COALITION_VS_ANTAGONIST_EXPANSION"],
        "interpretation": "Test interpretation.",
    }


def _cockpit(rg_block: dict | None) -> dict:
    state: dict = {
        "meta": {}, "db_vision": {}, "current_scene": {},
        "temporal_nodes": {}, "flow_events": [], "fractal_context": {},
        "telegram": {}, "next_watch": {},
    }
    if rg_block is not None:
        state["relational_gravity"] = rg_block
    return state


def _rg_aligned(score: float = 0.90) -> dict:
    return {
        "bridge_version": "0.1",
        "cross_tf_state": "RELATIONAL_GRAVITY_ALIGNED_M1_M5_M15",
        "dominant_direction": "UP",
        "dominant_leader": "GBP",
        "dominant_antagonist": "USD/JPY",
        "aligned_tfs": [1, 5, 15],
        "counter_tf": None,
        "max_score": score,
        "notes": [],
        "tf_details": {
            "1":  _tf_detail(score=score),
            "5":  _tf_detail(score=score),
            "15": _tf_detail(score=score),
        },
    }


def _rg_m1_counter() -> dict:
    return {
        "bridge_version": "0.1",
        "cross_tf_state": "M1_RELATIONAL_COUNTERFIELD",
        "dominant_direction": "UP",
        "dominant_leader": "GBP",
        "dominant_antagonist": "USD",
        "aligned_tfs": [5, 15],
        "counter_tf": 1,
        "max_score": 0.88,
        "notes": [],
        "tf_details": {
            "1":  _tf_detail(direction="DOWN", leader="USD", score=0.80),
            "5":  _tf_detail(direction="UP",   leader="GBP", score=0.88),
            "15": _tf_detail(direction="UP",   leader="GBP", score=0.85),
        },
    }


def _rg_m5_m15() -> dict:
    return {
        "bridge_version": "0.1",
        "cross_tf_state": "M5_M15_RELATIONAL_ALIGNMENT",
        "dominant_direction": "UP",
        "dominant_leader": "GBP",
        "dominant_antagonist": "USD",
        "aligned_tfs": [5, 15],
        "counter_tf": None,
        "max_score": 0.83,
        "notes": ["TF missing: [1]"],
        "tf_details": {
            "1":  {"loaded": False, "status": "FILE_MISSING", "direction": "UNKNOWN",
                   "leader": "UNKNOWN", "antagonist": "NONE", "score": 0.0,
                   "confidence": "LOW", "lab_signatures": [], "interpretation": "",
                   "primary_state": "RELATIONAL_GRAVITY_MISSING", "group": [],
                   "gap_mode": "UNKNOWN", "source_file": ""},
            "5":  _tf_detail(direction="UP", leader="GBP", score=0.83),
            "15": _tf_detail(direction="UP", leader="GBP", score=0.81),
        },
    }


def _rg_mixed() -> dict:
    return {
        "bridge_version": "0.1",
        "cross_tf_state": "RELATIONAL_GRAVITY_MIXED",
        "dominant_direction": "MIXED",
        "dominant_leader": "UNKNOWN",
        "dominant_antagonist": "NONE",
        "aligned_tfs": [],
        "counter_tf": None,
        "max_score": 0.35,
        "notes": [],
        "tf_details": {},
    }


# ─────────────────────────────────────────────
# TEST RUNNER
# ─────────────────────────────────────────────

PASS = 0
FAIL = 0


def check(label: str, condition: bool) -> None:
    global PASS, FAIL
    if condition:
        print(f"  ✓ {label}")
        PASS += 1
    else:
        print(f"  ✗ FAIL: {label}")
        FAIL += 1


def section(title: str) -> None:
    print(f"\n── {title}")


# ─────────────────────────────────────────────
# TESTS
# ─────────────────────────────────────────────

def test_no_rg_block() -> None:
    section("Bloc absent / malformé")
    cockpit = _cockpit(None)
    alerts = extract_relational_gravity_alerts(cockpit)
    check("Aucune alerte si bloc absent", len(alerts) == 0)

    cockpit2 = _cockpit({"wrong_key": 1})
    alerts2 = extract_relational_gravity_alerts(cockpit2)
    check("Aucune alerte si bloc malformé", len(alerts2) == 0)

    cockpit3 = {"meta": {}}  # pas de relational_gravity
    alerts3 = extract_relational_gravity_alerts(cockpit3)
    check("Aucune alerte sur cockpit vide", len(alerts3) == 0)


def test_aligned_hot() -> None:
    section("RELATIONAL_GRAVITY_ALIGNED_ALERT — HOT")
    cockpit = _cockpit(_rg_aligned(score=0.90))
    alerts = extract_relational_gravity_alerts(cockpit)
    names = [a.alert_name for a in alerts]
    check("Alerte ALIGNED produite", ALERT_ALIGNED in names)
    aligned = next(a for a in alerts if a.alert_name == ALERT_ALIGNED)
    check("Niveau HOT (score 0.90 >= 0.85)", aligned.level == LEVEL_HOT)
    check("dominant_direction UP", aligned.dominant_direction == "UP")
    check("dominant_leader GBP", aligned.dominant_leader == "GBP")
    check("aligned_tfs = [1,5,15]", aligned.aligned_tfs == [1, 5, 15])


def test_aligned_watch() -> None:
    section("RELATIONAL_GRAVITY_ALIGNED_ALERT — WATCH (score < 0.85)")
    cockpit = _cockpit(_rg_aligned(score=0.82))
    alerts = extract_relational_gravity_alerts(cockpit)
    aligned = next((a for a in alerts if a.alert_name == ALERT_ALIGNED), None)
    check("Alerte ALIGNED produite", aligned is not None)
    check("Niveau WATCH (score 0.82 < 0.85)", aligned is not None and aligned.level == LEVEL_WATCH)


def test_leader_pulling_hot() -> None:
    section("LEADER_PULLING_AWAY_ALERT — HOT")
    cockpit = _cockpit(_rg_aligned(score=0.90))
    alerts = extract_relational_gravity_alerts(cockpit)
    leader = next((a for a in alerts if a.alert_name == ALERT_LEADER_PULLING), None)
    check("Alerte LEADER_PULLING produite", leader is not None)
    check("Niveau HOT (aligned + score >= 0.85)", leader is not None and leader.level == LEVEL_HOT)
    check("dominant_leader GBP", leader is not None and leader.dominant_leader == "GBP")


def test_leader_pulling_watch() -> None:
    section("LEADER_PULLING_AWAY_ALERT — WATCH (m5_m15 only)")
    cockpit = _cockpit(_rg_m5_m15())
    alerts = extract_relational_gravity_alerts(cockpit)
    leader = next((a for a in alerts if a.alert_name == ALERT_LEADER_PULLING), None)
    check("Alerte LEADER_PULLING produite", leader is not None)
    check("Niveau WATCH", leader is not None and leader.level == LEVEL_WATCH)


def test_leader_pulling_suppressed_low_score() -> None:
    section("LEADER_PULLING_AWAY_ALERT — supprimé si score < 0.80")
    rg = _rg_aligned(score=0.75)
    cockpit = _cockpit(rg)
    alerts = extract_relational_gravity_alerts(cockpit)
    leader = next((a for a in alerts if a.alert_name == ALERT_LEADER_PULLING), None)
    check("Pas d'alerte LEADER si score 0.75 < 0.80", leader is None)


def test_m1_counterfield() -> None:
    section("M1_RELATIONAL_COUNTERFIELD_ALERT")
    cockpit = _cockpit(_rg_m1_counter())
    alerts = extract_relational_gravity_alerts(cockpit)
    names = [a.alert_name for a in alerts]
    check("Alerte M1_COUNTERFIELD produite", ALERT_M1_COUNTERFIELD in names)
    counter = next(a for a in alerts if a.alert_name == ALERT_M1_COUNTERFIELD)
    check("Niveau WATCH", counter.level == LEVEL_WATCH)
    check("counter_tf = 1", counter.counter_tf == 1)
    check("aligned_tfs = [5,15]", counter.aligned_tfs == [5, 15])
    check("Pas d'alerte ALIGNED (mauvais cross_tf_state)", ALERT_ALIGNED not in names)


def test_m5_m15_alignment_watch() -> None:
    section("M5_M15_RELATIONAL_ALIGNMENT_ALERT — WATCH")
    cockpit = _cockpit(_rg_m5_m15())
    alerts = extract_relational_gravity_alerts(cockpit)
    names = [a.alert_name for a in alerts]
    check("Alerte M5_M15_ALIGNMENT produite", ALERT_M5_M15_ALIGNMENT in names)
    a = next(x for x in alerts if x.alert_name == ALERT_M5_M15_ALIGNMENT)
    check("Niveau WATCH (score 0.83 >= 0.80)", a.level == LEVEL_WATCH)


def test_m5_m15_alignment_info() -> None:
    section("M5_M15_RELATIONAL_ALIGNMENT_ALERT — INFO (score < 0.80)")
    rg = _rg_m5_m15()
    rg["max_score"] = 0.72
    cockpit = _cockpit(rg)
    alerts = extract_relational_gravity_alerts(cockpit)
    a = next((x for x in alerts if x.alert_name == ALERT_M5_M15_ALIGNMENT), None)
    check("Alerte M5_M15 produite", a is not None)
    check("Niveau INFO (score 0.72 < 0.80)", a is not None and a.level == LEVEL_INFO)


def test_coalition_antagonist() -> None:
    section("COALITION_VS_ANTAGONIST_EXPANSION_ALERT")
    cockpit = _cockpit(_rg_aligned(score=0.90))
    alerts = extract_relational_gravity_alerts(cockpit)
    names = [a.alert_name for a in alerts]
    check("Alerte COALITION_ANTAGONIST produite", ALERT_COALITION_ANTAGONIST in names)
    a = next(x for x in alerts if x.alert_name == ALERT_COALITION_ANTAGONIST)
    check("Niveau INFO", a.level == LEVEL_INFO)
    check("dominant_antagonist non vide", bool(a.dominant_antagonist) and a.dominant_antagonist != "NONE")


def test_coalition_antagonist_suppressed_no_antag() -> None:
    section("COALITION_VS_ANTAGONIST — supprimé si antagonist NONE")
    rg = _rg_aligned(score=0.90)
    rg["dominant_antagonist"] = "NONE"
    for tf_data in rg["tf_details"].values():
        tf_data["antagonist"] = "NONE"
    cockpit = _cockpit(rg)
    alerts = extract_relational_gravity_alerts(cockpit)
    a = next((x for x in alerts if x.alert_name == ALERT_COALITION_ANTAGONIST), None)
    check("Pas d'alerte si antagonist=NONE", a is None)


def test_mixed_info() -> None:
    section("RELATIONAL_GRAVITY_MIXED_INFO")
    cockpit = _cockpit(_rg_mixed())
    alerts = extract_relational_gravity_alerts(cockpit)
    names = [a.alert_name for a in alerts]
    check("Alerte MIXED_INFO produite", ALERT_MIXED_INFO in names)
    a = next(x for x in alerts if x.alert_name == ALERT_MIXED_INFO)
    check("Niveau INFO", a.level == LEVEL_INFO)
    check("Pas d'alerte ALIGNED", ALERT_ALIGNED not in names)
    check("Pas d'alerte LEADER", ALERT_LEADER_PULLING not in names)


def test_serialization() -> None:
    section("Sérialisation rg_alert_to_dict")
    cockpit = _cockpit(_rg_aligned(score=0.90))
    alerts = extract_relational_gravity_alerts(cockpit)
    check("Au moins 1 alerte", len(alerts) > 0)
    d = rg_alert_to_dict(alerts[0])
    for key in ["alert_name", "level", "source", "cross_tf_state",
                "dominant_direction", "dominant_leader", "dominant_antagonist",
                "aligned_tfs", "counter_tf", "max_score", "reason",
                "interpretation", "tags"]:
        check(f"Clé '{key}' présente", key in d)
    check("source = relational_gravity", d.get("source") == "relational_gravity")


def test_no_buy_sell() -> None:
    section("Pas de BUY/SELL dans les alertes")
    cockpit = _cockpit(_rg_aligned(score=0.95))
    alerts = extract_relational_gravity_alerts(cockpit)
    for a in alerts:
        d = rg_alert_to_dict(a)
        full_text = str(d).upper()
        check(
            f"{a.alert_name} — pas de BUY/SELL",
            "BUY" not in full_text and "SELL" not in full_text
        )


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 66)
    print("  TEST SUITE — pf_relational_gravity_alerts.py")
    print("=" * 66)

    test_no_rg_block()
    test_aligned_hot()
    test_aligned_watch()
    test_leader_pulling_hot()
    test_leader_pulling_watch()
    test_leader_pulling_suppressed_low_score()
    test_m1_counterfield()
    test_m5_m15_alignment_watch()
    test_m5_m15_alignment_info()
    test_coalition_antagonist()
    test_coalition_antagonist_suppressed_no_antag()
    test_mixed_info()
    test_serialization()
    test_no_buy_sell()

    print(f"\n{'=' * 66}")
    print(f"  RÉSULTAT : {PASS} ✓  |  {FAIL} ✗")
    print(f"{'=' * 66}\n")

    sys.exit(0 if FAIL == 0 else 1)
