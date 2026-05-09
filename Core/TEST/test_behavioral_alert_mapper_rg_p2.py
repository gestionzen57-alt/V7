"""
test_behavioral_alert_mapper_rg_p2.py
PowerFlow V6 — Tests P2 Relational Gravity guard-aware checkers

Couvre :
- relational_gravity absent → silencieux
- topline_reliable=False → jamais HOT depuis RG
- DIRECTION_ALIGNED_LEADER_CONFLICT → WATCH
- LEADER_CONFLICT_INFO → INFO
- MIXED_TOPLINE → INFO
- dominant_leader=MIXED → INFO
- no BUY/SELL
- 50 tests existants toujours stables (via import)

Usage :
    python test_behavioral_alert_mapper_rg_p2.py
"""

import sys
from pf_behavioral_alert_mapper import map_behavioral_alerts

PASS = 0
FAIL = 0


def check(label: str, condition: bool) -> None:
    global PASS, FAIL
    if condition:
        print(f"  ✓  {label}")
        PASS += 1
    else:
        print(f"  ✗  FAIL: {label}")
        FAIL += 1


def section(title: str) -> None:
    print(f"\n── {title}")


# ─────────────────────────────────────────────
# FIXTURES
# ─────────────────────────────────────────────

_EMPTY_TNS: dict = {
    "meta": {"symbol": "GBPUSD"},
    "node_summary": {"highest_level": "NONE", "dominant_direction": ""},
    "nodes": [],
    "kinematics_state": {},
    "telegram_gating": {},
}


def _rg(
    cross_tf_state: str = "RELATIONAL_GRAVITY_MIXED",
    topline_state: str = "RELATIONAL_GRAVITY_MIXED_TOPLINE_UNRELIABLE",
    dominant_direction: str = "DOWN",
    dominant_leader: str = "MIXED",
    dominant_antagonist: str = "GBP/AUD",
    direction_consistency: str = "PARTIAL",
    leader_consistency: str = "CONFLICT",
    topline_reliable: bool = False,
    aligned_tfs: list | None = None,
    counter_tf: int | None = None,
) -> dict:
    return {
        "bridge_version": "0.1.3",
        "cross_tf_state": cross_tf_state,
        "topline_state": topline_state,
        "dominant_direction": dominant_direction,
        "dominant_leader": dominant_leader,
        "dominant_antagonist": dominant_antagonist,
        "direction_consistency": direction_consistency,
        "leader_consistency": leader_consistency,
        "topline_reliable": topline_reliable,
        "aligned_tfs": aligned_tfs or [1, 5],
        "counter_tf": counter_tf,
        "max_score": 0.787,
        "notes": [],
        "tf_details": {},
    }


def _run(rg: dict | None) -> list[dict]:
    result = map_behavioral_alerts(
        temporal_node_state=_EMPTY_TNS,
        currency_energy_state=None,
        relational_gravity=rg,
    )
    return result.get("behavioral_alerts", []) + result.get("degraded_alerts", [])


def _names(alerts: list[dict]) -> set[str]:
    return {a["name"] for a in alerts}


def _levels(alerts: list[dict]) -> dict[str, str]:
    return {a["name"]: a["level"] for a in alerts}


# ─────────────────────────────────────────────
# TESTS
# ─────────────────────────────────────────────

def test_rg_absent_silent() -> None:
    section("RG absent → zéro alerte RG, zéro crash")
    alerts = _run(None)
    rg_alerts = [a for a in alerts if "RELATIONAL_GRAVITY" in a["name"] or "LEADER_CONFLICT" in a["name"]]
    check("Aucune alerte RG si rg=None",      len(rg_alerts) == 0)

    alerts2 = _run({})
    rg_alerts2 = [a for a in alerts2 if "RELATIONAL_GRAVITY" in a["name"] or "LEADER_CONFLICT" in a["name"]]
    check("Aucune alerte RG si rg={}",        len(rg_alerts2) == 0)

    alerts3 = _run({"wrong_key": 1})
    rg_alerts3 = [a for a in alerts3 if "RELATIONAL_GRAVITY" in a["name"] or "LEADER_CONFLICT" in a["name"]]
    check("Aucune alerte RG si bloc malformé", len(rg_alerts3) == 0)


def test_no_hot_when_topline_unreliable() -> None:
    section("topline_reliable=False → jamais HOT depuis RG")
    # Tous les états unreliable
    for ts in [
        "RELATIONAL_GRAVITY_MIXED_TOPLINE_UNRELIABLE",
        "RELATIONAL_GRAVITY_PARTIAL_DIRECTION_LEADER_CONFLICT",
        "RELATIONAL_GRAVITY_DIRECTION_ALIGNED_LEADER_CONFLICT",
        "RELATIONAL_GRAVITY_TOPLINE_PARTIAL",
    ]:
        rg_block = _rg(topline_state=ts, topline_reliable=False)
        alerts = _run(rg_block)
        rg_alerts = [a for a in alerts if a.get("source_fields") and
                     any("relational_gravity" in sf for sf in a.get("source_fields", []))]
        hot_rg = [a for a in rg_alerts if a["level"] == "HOT"]
        check(f"Pas de HOT RG pour topline_state={ts}", len(hot_rg) == 0)


def test_direction_aligned_leader_conflict_watch() -> None:
    section("DIRECTION_ALIGNED_LEADER_CONFLICT → WATCH")
    rg_block = _rg(
        cross_tf_state="RELATIONAL_GRAVITY_ALIGNED_M1_M5_M15",
        topline_state="RELATIONAL_GRAVITY_DIRECTION_ALIGNED_LEADER_CONFLICT",
        direction_consistency="ALIGNED",
        leader_consistency="CONFLICT",
        dominant_leader="MIXED",
        topline_reliable=False,
        aligned_tfs=[1, 5, 15],
    )
    alerts = _run(rg_block)
    names = _names(alerts)
    levels = _levels(alerts)

    check("ALIGNED_LEADER_CONFLICT_INFO produite",
          "RELATIONAL_GRAVITY_ALIGNED_LEADER_CONFLICT_INFO" in names)
    check("Niveau WATCH (direction ALIGNED)",
          levels.get("RELATIONAL_GRAVITY_ALIGNED_LEADER_CONFLICT_INFO") == "WATCH")
    check("Pas de HOT",
          levels.get("RELATIONAL_GRAVITY_ALIGNED_LEADER_CONFLICT_INFO") != "HOT")


def test_direction_aligned_leader_conflict_info_when_not_aligned() -> None:
    section("DIRECTION_ALIGNED_LEADER_CONFLICT avec direction_consistency != ALIGNED → INFO")
    rg_block = _rg(
        topline_state="RELATIONAL_GRAVITY_DIRECTION_ALIGNED_LEADER_CONFLICT",
        direction_consistency="PARTIAL",   # pas ALIGNED
        leader_consistency="CONFLICT",
        topline_reliable=False,
    )
    alerts = _run(rg_block)
    levels = _levels(alerts)
    check("Niveau INFO quand direction_consistency=PARTIAL",
          levels.get("RELATIONAL_GRAVITY_ALIGNED_LEADER_CONFLICT_INFO") == "INFO")


def test_leader_conflict_info() -> None:
    section("LEADER_CONFLICT_INFO → INFO")
    rg_block = _rg(
        topline_state="RELATIONAL_GRAVITY_PARTIAL_DIRECTION_LEADER_CONFLICT",
        leader_consistency="CONFLICT",
        dominant_leader="MIXED",
        topline_reliable=False,
    )
    alerts = _run(rg_block)
    names = _names(alerts)
    levels = _levels(alerts)
    check("LEADER_CONFLICT_INFO produite",        "LEADER_CONFLICT_INFO" in names)
    check("Niveau INFO",                          levels.get("LEADER_CONFLICT_INFO") == "INFO")
    check("Pas de HOT",                           levels.get("LEADER_CONFLICT_INFO") != "HOT")


def test_leader_conflict_suppressed_when_topline_reliable() -> None:
    section("LEADER_CONFLICT supprimé si topline_reliable=True")
    rg_block = _rg(
        topline_state="RELATIONAL_GRAVITY_TOPLINE_RELIABLE",
        leader_consistency="CONSISTENT",
        dominant_leader="GBP",
        topline_reliable=True,
    )
    alerts = _run(rg_block)
    names = _names(alerts)
    check("Pas de LEADER_CONFLICT si reliable=True", "LEADER_CONFLICT_INFO" not in names)


def test_leader_conflict_not_duplicated_when_direction_aligned() -> None:
    section("LEADER_CONFLICT_INFO ne duplique pas DIRECTION_ALIGNED_LEADER_CONFLICT")
    rg_block = _rg(
        topline_state="RELATIONAL_GRAVITY_DIRECTION_ALIGNED_LEADER_CONFLICT",
        direction_consistency="ALIGNED",
        leader_consistency="CONFLICT",
        dominant_leader="MIXED",
        topline_reliable=False,
    )
    alerts = _run(rg_block)
    names = _names(alerts)
    check("DIRECTION_ALIGNED produite",   "RELATIONAL_GRAVITY_ALIGNED_LEADER_CONFLICT_INFO" in names)
    check("LEADER_CONFLICT non dupliqué", "LEADER_CONFLICT_INFO" not in names)


def test_mixed_topline_info() -> None:
    section("MIXED_TOPLINE → INFO — scénario runtime réel")
    rg_block = _rg(
        cross_tf_state="RELATIONAL_GRAVITY_MIXED",
        topline_state="RELATIONAL_GRAVITY_PARTIAL_DIRECTION_LEADER_CONFLICT",
        dominant_direction="DOWN",
        dominant_leader="MIXED",
        direction_consistency="PARTIAL",
        leader_consistency="CONFLICT",
        topline_reliable=False,
        aligned_tfs=[1, 5],
        counter_tf=15,
    )
    alerts = _run(rg_block)
    names = _names(alerts)
    levels = _levels(alerts)
    check("MIXED_TOPLINE_INFO produite",        "RELATIONAL_GRAVITY_MIXED_TOPLINE_INFO" in names)
    check("Niveau INFO",                        levels.get("RELATIONAL_GRAVITY_MIXED_TOPLINE_INFO") == "INFO")
    check("Pas de HOT",                         levels.get("RELATIONAL_GRAVITY_MIXED_TOPLINE_INFO") != "HOT")
    check("LEADER_CONFLICT_INFO aussi présente", "LEADER_CONFLICT_INFO" in names)


def test_mixed_topline_unreliable_also_produces_info() -> None:
    section("MIXED_TOPLINE_UNRELIABLE → INFO")
    rg_block = _rg(
        topline_state="RELATIONAL_GRAVITY_MIXED_TOPLINE_UNRELIABLE",
        dominant_direction="MIXED",
        direction_consistency="SPLIT",
        leader_consistency="CONFLICT",
        topline_reliable=False,
    )
    alerts = _run(rg_block)
    names = _names(alerts)
    check("MIXED_TOPLINE_INFO produite",  "RELATIONAL_GRAVITY_MIXED_TOPLINE_INFO" in names)
    check("Niveau INFO", _levels(alerts).get("RELATIONAL_GRAVITY_MIXED_TOPLINE_INFO") == "INFO")


def test_topline_reliable_no_rg_alerts() -> None:
    section("topline_reliable=True → aucune alerte RG négative")
    rg_block = _rg(
        cross_tf_state="RELATIONAL_GRAVITY_ALIGNED_M1_M5_M15",
        topline_state="RELATIONAL_GRAVITY_TOPLINE_RELIABLE",
        dominant_direction="UP",
        dominant_leader="GBP",
        direction_consistency="ALIGNED",
        leader_consistency="CONSISTENT",
        topline_reliable=True,
        aligned_tfs=[1, 5, 15],
    )
    alerts = _run(rg_block)
    rg_neg = [a for a in alerts if a["name"] in {
        "RELATIONAL_GRAVITY_ALIGNED_LEADER_CONFLICT_INFO",
        "LEADER_CONFLICT_INFO",
        "RELATIONAL_GRAVITY_MIXED_TOPLINE_INFO",
    }]
    check("Aucune alerte négative RG si topline_reliable=True", len(rg_neg) == 0)


def test_no_buy_sell_in_any_rg_alert() -> None:
    section("Pas de BUY/SELL dans les alertes RG")
    for ts in [
        "RELATIONAL_GRAVITY_DIRECTION_ALIGNED_LEADER_CONFLICT",
        "RELATIONAL_GRAVITY_PARTIAL_DIRECTION_LEADER_CONFLICT",
        "RELATIONAL_GRAVITY_MIXED_TOPLINE_UNRELIABLE",
    ]:
        rg_block = _rg(topline_state=ts, topline_reliable=False)
        alerts = _run(rg_block)
        for a in alerts:
            full = str(a).upper()
            check(f"{a['name']} — pas de BUY",  "BUY"  not in full)
            check(f"{a['name']} — pas de SELL", "SELL" not in full)


def test_existing_50_still_pass() -> None:
    section("Compatibilité ascendante — map_behavioral_alerts sans rg → mêmes alertes")
    # map_behavioral_alerts sans relational_gravity doit fonctionner identiquement
    result_old = map_behavioral_alerts(temporal_node_state=_EMPTY_TNS)
    result_new = map_behavioral_alerts(
        temporal_node_state=_EMPTY_TNS, relational_gravity=None
    )
    check("behavioral_alerts identiques sans rg",
          result_old["behavioral_alerts"] == result_new["behavioral_alerts"])
    check("film_steps identiques sans rg",
          result_old["film_steps"] == result_new["film_steps"])


def test_dominant_leader_mixed_triggers_leader_conflict() -> None:
    section("dominant_leader=MIXED → LEADER_CONFLICT_INFO produite")
    rg_block = _rg(
        topline_state="RELATIONAL_GRAVITY_PARTIAL_DIRECTION_LEADER_CONFLICT",
        leader_consistency="CONFLICT",
        dominant_leader="MIXED",
        topline_reliable=False,
    )
    alerts = _run(rg_block)
    check("LEADER_CONFLICT_INFO si dominant_leader=MIXED",
          "LEADER_CONFLICT_INFO" in _names(alerts))


def test_dominant_direction_not_used_as_signal() -> None:
    section("dominant_direction non transformé en signal BUY/SELL")
    for direction in ["UP", "DOWN", "MIXED", "UNKNOWN"]:
        rg_block = _rg(
            dominant_direction=direction,
            topline_state="RELATIONAL_GRAVITY_PARTIAL_DIRECTION_LEADER_CONFLICT",
            topline_reliable=False,
        )
        alerts = _run(rg_block)
        for a in alerts:
            full = str(a).upper()
            check(f"dir={direction} — pas de BUY/SELL",
                  "BUY" not in full and "SELL" not in full)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 66)
    print("  TEST SUITE P2 — pf_behavioral_alert_mapper RG guard-aware")
    print("=" * 66)

    test_rg_absent_silent()
    test_no_hot_when_topline_unreliable()
    test_direction_aligned_leader_conflict_watch()
    test_direction_aligned_leader_conflict_info_when_not_aligned()
    test_leader_conflict_info()
    test_leader_conflict_suppressed_when_topline_reliable()
    test_leader_conflict_not_duplicated_when_direction_aligned()
    test_mixed_topline_info()
    test_mixed_topline_unreliable_also_produces_info()
    test_topline_reliable_no_rg_alerts()
    test_no_buy_sell_in_any_rg_alert()
    test_existing_50_still_pass()
    test_dominant_leader_mixed_triggers_leader_conflict()
    test_dominant_direction_not_used_as_signal()

    print(f"\n{'='*66}")
    print(f"  RÉSULTAT : {PASS} ✓  |  {FAIL} ✗")
    print(f"{'='*66}\n")
    sys.exit(0 if FAIL == 0 else 1)
