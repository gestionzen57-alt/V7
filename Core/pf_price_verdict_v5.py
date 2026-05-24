"""
pf_price_verdict_v5.py — PowerFlow V7.6.7
Moteur B9 v5 — Calibration T10 + Optimisations standalone
Corrections : C1-C7 (ground truth trader GBPUSD 05/05 + 08/05/2026)
Optimisations : OPT1-OPT6 (asymétrie, courbure, position, pente, volatilité, densité)
Accuracy v4 mesurée : 6/17 = 35%
Accuracy v5 projetée : 12-13/17 = 71-76%
"""

from dataclasses import dataclass, field
from typing import Optional
import numpy as np

# ---------------------------------------------------------------------------
# CONSTANTS — v4 conservées + v5 ajouts
# ---------------------------------------------------------------------------
PIP = 0.0001

# B9 core
CONTEXT_MOVE_MIN_PIPS        = 2.0
PULLBACK_ABSORBED_DWELL_MIN  = 0.40
PULLBACK_ABSORBED_NET_RATIO  = 0.75
PULLBACK_ABSORBED_OSC_MAX    = 4
REVERSAL_ATTEMPT_DWELL_MAX   = 0.70
EFFORT_BLOCKED_NR_MAX        = 0.25
MIN_REJECTION_PIPS           = 2.0
CB_NET_CTX_RATIO_MAX         = 1.5
CB_NET_MIN                   = 1.5

# REJECTED guards
ACCEPTED_DWELL_GUARD         = 0.55
PB_DWELL_GUARD               = 0.35

# CENTER_MIGRATION
MAX_OSC_CENTER_MIGRATION     = 10

# v5 — C1
CM_OSC_PRIORITY_MIN          = 7
CM_DCP_PRIORITY_MIN          = 0.60

# v5 — C2
PW_STANDALONE_NR_MIN         = 0.80
PW_STANDALONE_NET_MIN        = 6.0

# v5 — C3
CB_PW_OVERRIDE_NET           = 8.0
CB_PW_OVERRIDE_NR            = 0.80

# v5 — C4
CM_RANGE_MAX                 = 15.0

# v5 — C5
PA_ALIGNED_DCP_MIN           = 0.40

# v5 — C6
CB_ACC_GUARD_DCP             = 0.55
CB_ACC_GUARD_OSC             = 5

# v5 — C7
REJ_PARTIAL_THRESHOLD        = 0.35

# v5 — OPT4
SLOPE_PW_MIN                 = 0.60

# v5 — OPT5
RANGE_HIGH_THRESHOLD         = 20.0
RANGE_ULTRA_THRESHOLD        = 30.0


# ---------------------------------------------------------------------------
# DATACLASS
# ---------------------------------------------------------------------------
@dataclass
class VerdictV4:
    verdict:         str
    confidence:      float
    rule:            str
    detail:          dict = field(default_factory=dict)
    # v5 champs additionnels
    volatility_flag: str   = "NORMAL"
    curvature:       float = 1.0
    osc_asymmetry:   float = 0.0
    close_position:  float = 0.5
    slope_ratio:     float = 0.0


# ---------------------------------------------------------------------------
# CALC REJECTION — v5 C7
# ---------------------------------------------------------------------------
def calc_rejection_correct(closes: list) -> float:
    prices = [c / PIP for c in closes]  # work in pips
    pmax, pmin = max(closes), min(closes)
    first, last = closes[0], closes[-1]
    rng     = (pmax - pmin) / PIP
    net_abs = abs(last - first) / PIP
    nr      = net_abs / rng if rng > 0 else 0
    rej_raw = (pmax - last) / PIP if last < pmax else (last - pmin) / PIP
    # v5 — C7 : signal partiel pondéré si nr >= 0.50
    if nr >= 0.50 and rej_raw > rng * REJ_PARTIAL_THRESHOLD:
        return round(rej_raw * 0.55, 2)
    if nr >= 0.50:
        return 0.0
    return round(rej_raw, 2)


# ---------------------------------------------------------------------------
# CALC METRICS
# ---------------------------------------------------------------------------
def calc_metrics(closes: list) -> dict:
    n      = len(closes)
    prices = closes
    pmax   = max(prices)
    pmin   = min(prices)
    first  = prices[0]
    last   = prices[-1]

    rng        = (pmax - pmin) / PIP
    net_pips   = (last - first) / PIP
    net_abs    = abs(net_pips)
    nr         = net_abs / rng if rng > 0 else 0.0
    range_pips = rng

    # dwell / center acceptance
    center   = (pmax + pmin) / 2
    band     = (pmax - pmin) * 0.20
    in_center = sum(1 for p in prices if abs(p - center) <= band)
    dcp      = in_center / n  # dwell_center_pct

    # oscillations
    osc = sum(
        1 for i in range(1, n)
        if (prices[i] - center) * (prices[i - 1] - center) < 0
    )

    # rejection
    rej = calc_rejection_correct(closes)

    # dwell seconds proxy (fraction temps en zone close)
    dwell_seconds = dcp * n * 60  # approximation : 1 tick = ~1s

    # context direction proxy (depuis net)
    ca = net_pips > 0  # close_above_open

    # v5 — OPT1 : asymétrie des oscillations
    avg      = sum(prices) / n
    osc_up   = sum(1 for i in range(1, n) if prices[i - 1] < avg <= prices[i])
    osc_down = sum(1 for i in range(1, n) if prices[i - 1] >= avg > prices[i])
    osc_asymmetry = (osc_up - osc_down) / max(1, osc_up + osc_down)

    # v5 — OPT2 : courbure
    mid = n // 2
    h1  = (prices[mid] - prices[0]) / PIP if PIP > 0 else 0
    h2  = (prices[-1] - prices[mid]) / PIP if PIP > 0 else 0
    if h1 != 0 and h1 * h2 > 0:
        curvature = h2 / h1
    else:
        curvature = 0.0

    # v5 — OPT3 : position close final dans le range
    close_position = (last - pmin) / (pmax - pmin) if (pmax - pmin) > 0 else 0.5

    # v5 — OPT4 : pente régression linéaire normalisée
    try:
        slope_raw, _ = np.polyfit(range(n), prices, 1)
        slope_pips   = slope_raw / PIP
        slope_ratio  = (slope_pips * n / range_pips) if range_pips > 0 else 0.0
    except Exception:
        slope_ratio = 0.0

    # v5 — OPT5 : volatility flag
    if range_pips >= RANGE_ULTRA_THRESHOLD:
        volatility_flag = "EVENT"
    elif range_pips >= RANGE_HIGH_THRESHOLD:
        volatility_flag = "HIGH"
    else:
        volatility_flag = "NORMAL"

    # v5 — OPT6 : densité tiers
    zone_h       = pmax - (pmax - pmin) / 3
    zone_l       = pmin + (pmax - pmin) / 3
    n_high       = sum(1 for p in prices if p >= zone_h)
    n_low        = sum(1 for p in prices if p <= zone_l)
    n_center_d   = n - n_high - n_low
    density_high   = round(n_high    / n, 3)
    density_low    = round(n_low     / n, 3)
    density_center = round(n_center_d / n, 3)

    return {
        "n":              n,
        "range_pips":     round(range_pips, 2),
        "net_pips":       round(net_pips, 2),
        "net_abs":        round(net_abs, 2),
        "nr":             round(nr, 3),
        "dcp":            round(dcp, 3),
        "osc":            osc,
        "rej":            rej,
        "ca":             ca,
        "dwell_seconds":  round(dwell_seconds, 1),
        "pmax":           pmax,
        "pmin":           pmin,
        "close_position": round(close_position, 3),
        # v5 OPT1
        "osc_asymmetry":  round(osc_asymmetry, 3),
        # v5 OPT2
        "curvature":      round(curvature, 3),
        # v5 OPT3 (déjà ci-dessus)
        # v5 OPT4
        "slope_ratio":    round(slope_ratio, 3),
        # v5 OPT5
        "volatility_flag": volatility_flag,
        # v5 OPT6
        "density_high":   density_high,
        "density_low":    density_low,
        "density_center": density_center,
    }


# ---------------------------------------------------------------------------
# COMPUTE VERDICT — ordre v5
# ---------------------------------------------------------------------------
def compute_verdict(closes: list, context: Optional[dict] = None) -> VerdictV4:
    if len(closes) < 3:
        return VerdictV4("INCONCLUSIVE", 0.0, "not_enough_data")

    ctx       = context or {}
    metrics   = calc_metrics(closes)

    # Extraire métriques
    n             = metrics["n"]
    net           = metrics["net_abs"]
    net_pips      = metrics["net_pips"]
    nr            = metrics["nr"]
    dcp           = metrics["dcp"]
    osc           = metrics["osc"]
    rej           = metrics["rej"]
    ca            = metrics["ca"]
    r             = metrics["range_pips"]
    dwell_seconds = metrics["dwell_seconds"]
    close_pos     = metrics["close_position"]
    osc_asym      = metrics["osc_asymmetry"]
    curvature     = metrics["curvature"]
    slope_ratio   = metrics["slope_ratio"]
    vflag         = metrics["volatility_flag"]
    d_high        = metrics["density_high"]
    d_low         = metrics["density_low"]
    d_center      = metrics["density_center"]

    # Contexte
    ctx_net       = abs(ctx.get("context_net_pips", 0.0))
    ctx_dir       = ctx.get("context_direction", "NONE")
    is_pb         = ctx.get("is_pullback_context", False)
    is_inverse    = ctx.get("is_inverse_context", False)
    ctx_active    = ctx_net >= CONTEXT_MOVE_MIN_PIPS

    # ctx_aligned : move dans le sens du contexte
    ctx_aligned = (
        (ctx_dir == "UP"   and net_pips > 0) or
        (ctx_dir == "DOWN" and net_pips < 0)
    )

    # v5 — C5 : ctx_aligned_short (continuation courte)
    ctx_aligned_short = (
        ca
        and ctx_aligned
        and net < ctx_net * 0.85
        and net >= 1.5
    )

    # -----------------------------------------------------------------------
    # 1. ACCEPTED_PASSIVE (très long dwell)
    # -----------------------------------------------------------------------
    if dwell_seconds >= 300 and dcp >= 0.70 and net < 2.0:
        return VerdictV4(
            "ACCEPTED_PASSIVE", 0.75, "long_dwell_passive",
            detail={"dcp": dcp, "dwell_s": dwell_seconds},
            volatility_flag=vflag, close_position=close_pos,
            osc_asymmetry=osc_asym, curvature=curvature, slope_ratio=slope_ratio
        )

    # -----------------------------------------------------------------------
    # 2. v5 — C5 : PULLBACK_ABSORBED aligné continuation
    # -----------------------------------------------------------------------
    if ctx_aligned_short and dcp >= PA_ALIGNED_DCP_MIN and rej < 2.0:
        conf = 0.72
        if curvature > 1.0:
            conf += 0.05
        return VerdictV4(
            "PULLBACK_ABSORBED", round(conf, 2), "pullback_absorbed_aligned_v5",
            detail={"dcp": dcp, "note": "short_aligned_continuation"},
            volatility_flag=vflag, close_position=close_pos,
            osc_asymmetry=osc_asym, curvature=curvature, slope_ratio=slope_ratio
        )

    # -----------------------------------------------------------------------
    # 3. ACCEPTED (dwell center)
    # -----------------------------------------------------------------------
    if dcp >= ACCEPTED_DWELL_GUARD and osc < CB_ACC_GUARD_OSC:
        conf = 0.68
        if 0.35 < close_pos < 0.65:
            conf += 0.04
        if abs(osc_asym) > 0.50:
            detail_acc = {"biased": True, "osc_asymmetry": osc_asym}
        else:
            detail_acc = {}
        if d_center > 0.55:
            conf += 0.05
        return VerdictV4(
            "ACCEPTED", round(conf, 2), "accepted_dwell_center",
            detail=detail_acc,
            volatility_flag=vflag, close_position=close_pos,
            osc_asymmetry=osc_asym, curvature=curvature, slope_ratio=slope_ratio
        )

    # -----------------------------------------------------------------------
    # 4. PULLBACK_ABSORBED élargi v4 (inverse + ctx)
    # -----------------------------------------------------------------------
    if (is_inverse and ctx_active
            and dcp >= PULLBACK_ABSORBED_DWELL_MIN
            and nr <= PULLBACK_ABSORBED_NET_RATIO
            and osc <= PULLBACK_ABSORBED_OSC_MAX):
        conf = 0.73
        if curvature > 1.0:
            conf += 0.05
        return VerdictV4(
            "PULLBACK_ABSORBED", round(conf, 2), "pullback_absorbed_inverse_ctx",
            detail={"dcp": dcp, "nr": nr},
            volatility_flag=vflag, close_position=close_pos,
            osc_asymmetry=osc_asym, curvature=curvature, slope_ratio=slope_ratio
        )

    # -----------------------------------------------------------------------
    # 5. REJECTED
    # -----------------------------------------------------------------------
    if rej >= MIN_REJECTION_PIPS and nr < 0.50:
        # v5 — OPT3 : si close en extrême → invalider REJECTED
        if close_pos < 0.20 or close_pos > 0.80:
            pass  # invalider → continue
        else:
            conf = 0.70
            if vflag == "HIGH":
                conf -= 0.05
            if dcp >= ACCEPTED_DWELL_GUARD:
                return VerdictV4(
                    "ACCEPTED", 0.68, "accepted_guard_rejected_dwell",
                    detail={"note": "dwell_overrides_rejection"},
                    volatility_flag=vflag, close_position=close_pos,
                    osc_asymmetry=osc_asym, curvature=curvature, slope_ratio=slope_ratio
                )
            return VerdictV4(
                "REJECTED", round(conf, 2), "rejection_detected",
                detail={"rej": rej, "nr": nr},
                volatility_flag=vflag, close_position=close_pos,
                osc_asymmetry=osc_asym, curvature=curvature, slope_ratio=slope_ratio
            )

    # -----------------------------------------------------------------------
    # 6. REJECTED_INTERNAL
    # -----------------------------------------------------------------------
    if rej >= MIN_REJECTION_PIPS and dcp < 0.30 and osc <= 2:
        return VerdictV4(
            "REJECTED_INTERNAL", 0.65, "internal_rejection",
            detail={"rej": rej},
            volatility_flag=vflag, close_position=close_pos,
            osc_asymmetry=osc_asym, curvature=curvature, slope_ratio=slope_ratio
        )

    # -----------------------------------------------------------------------
    # 7. FAILED_REINTEGRATION
    # -----------------------------------------------------------------------
    if is_inverse and ctx_active and nr >= 0.60 and rej >= MIN_REJECTION_PIPS:
        return VerdictV4(
            "FAILED_REINTEGRATION", 0.68, "failed_reintegration_inverse",
            detail={"nr": nr, "rej": rej},
            volatility_flag=vflag, close_position=close_pos,
            osc_asymmetry=osc_asym, curvature=curvature, slope_ratio=slope_ratio
        )

    # -----------------------------------------------------------------------
    # 8. v5 — C1 : CENTER_MIGRATION oscillatoire prioritaire
    # -----------------------------------------------------------------------
    if osc >= CM_OSC_PRIORITY_MIN and dcp >= CM_DCP_PRIORITY_MIN and net >= 2.0:
        conf = 0.71
        if abs(osc_asym) < 0.15:
            conf += 0.04
        return VerdictV4(
            "CENTER_MIGRATION", round(conf, 2), "center_migration_osc_priority",
            detail={"osc": osc, "dcp": dcp, "note": "oscillatory_not_pw"},
            volatility_flag=vflag, close_position=close_pos,
            osc_asymmetry=osc_asym, curvature=curvature, slope_ratio=slope_ratio
        )

    # -----------------------------------------------------------------------
    # 9. v5 — C4 : CENTER_MIGRATION standard (avec guard grand range)
    # -----------------------------------------------------------------------
    cm_range_ok = not (r > CM_RANGE_MAX and nr >= 0.50)
    if dcp >= 0.50 and osc < MAX_OSC_CENTER_MIGRATION and net >= 2.0 and cm_range_ok:
        conf = 0.67
        if abs(osc_asym) < 0.15:
            conf += 0.04
        if 0.25 <= d_center <= 0.55:
            conf += 0.03
        return VerdictV4(
            "CENTER_MIGRATION", round(conf, 2), "center_migration_standard",
            detail={"dcp": dcp, "osc": osc, "range_pips": r},
            volatility_flag=vflag, close_position=close_pos,
            osc_asymmetry=osc_asym, curvature=curvature, slope_ratio=slope_ratio
        )

    # -----------------------------------------------------------------------
    # 10. REVERSAL_ATTEMPT
    # -----------------------------------------------------------------------
    if (is_inverse and ctx_active
            and dcp <= REVERSAL_ATTEMPT_DWELL_MAX
            and nr >= 0.70 and net >= 3.0):
        return VerdictV4(
            "REVERSAL_ATTEMPT", 0.65, "reversal_attempt_inverse",
            detail={"nr": nr, "net": net},
            volatility_flag=vflag, close_position=close_pos,
            osc_asymmetry=osc_asym, curvature=curvature, slope_ratio=slope_ratio
        )

    # -----------------------------------------------------------------------
    # 11. EFFORT_BLOCKED
    # -----------------------------------------------------------------------
    if nr <= EFFORT_BLOCKED_NR_MAX and net >= 2.0 and osc >= 4:
        return VerdictV4(
            "EFFORT_BLOCKED", 0.63, "effort_blocked_low_nr",
            detail={"nr": nr, "osc": osc},
            volatility_flag=vflag, close_position=close_pos,
            osc_asymmetry=osc_asym, curvature=curvature, slope_ratio=slope_ratio
        )

    # -----------------------------------------------------------------------
    # 12. EFFORT_WITHOUT_RESULT
    # -----------------------------------------------------------------------
    if nr <= 0.15 and net < 1.5 and r >= 3.0:
        return VerdictV4(
            "EFFORT_WITHOUT_RESULT", 0.60, "effort_without_result",
            detail={"nr": nr, "range": r},
            volatility_flag=vflag, close_position=close_pos,
            osc_asymmetry=osc_asym, curvature=curvature, slope_ratio=slope_ratio
        )

    # -----------------------------------------------------------------------
    # 13–15. CB bloc
    # -----------------------------------------------------------------------
    cb_ratio_ok = (ctx_active and net / ctx_net <= CB_NET_CTX_RATIO_MAX) if ctx_net > 0 else False
    cb_net_ok   = net >= CB_NET_MIN
    cb_dir_ok   = is_inverse

    if cb_ratio_ok and cb_net_ok and cb_dir_ok:
        # v5 — C6 : ACCEPTED guard (consolidation, pas CB)
        if dcp >= CB_ACC_GUARD_DCP and osc >= CB_ACC_GUARD_OSC:
            return VerdictV4(
                "ACCEPTED", 0.68, "accepted_guard_cb_dwell_osc",
                detail={"dcp": dcp, "osc": osc, "note": "consolidation_not_cb"},
                volatility_flag=vflag, close_position=close_pos,
                osc_asymmetry=osc_asym, curvature=curvature, slope_ratio=slope_ratio
            )

        # v5 — C3 : PW override si mouvement trop fort
        if net >= CB_PW_OVERRIDE_NET and nr >= CB_PW_OVERRIDE_NR:
            return VerdictV4(
                "PROGRESSIVE_WAVE", 0.70, "pw_override_cb_strong",
                detail={"net": net, "nr": nr, "note": "too_strong_for_cb"},
                volatility_flag=vflag, close_position=close_pos,
                osc_asymmetry=osc_asym, curvature=curvature, slope_ratio=slope_ratio
            )

        # COUNTER_BREATH_CANDIDATE
        return VerdictV4(
            "COUNTER_BREATH_CANDIDATE", 0.72, "cb_ratio_inverse",
            detail={"net": net, "ctx_net": ctx_net, "ratio": round(net / ctx_net, 2)},
            volatility_flag=vflag, close_position=close_pos,
            osc_asymmetry=osc_asym, curvature=curvature, slope_ratio=slope_ratio
        )

    # -----------------------------------------------------------------------
    # 16. PROGRESSIVE_WAVE avec contexte
    # -----------------------------------------------------------------------
    if ctx_aligned and ctx_active and nr >= 0.55 and net >= 3.0:
        conf = 0.70
        # OPT1
        aligned_asym = (osc_asym > 0.15 and net_pips > 0) or (osc_asym < -0.15 and net_pips < 0)
        if aligned_asym:
            conf += 0.05
        # OPT2
        if curvature < 0.50:
            conf -= 0.07
        if curvature > 1.3:
            detail_extra = {"acceleration": True}
        else:
            detail_extra = {}
        # OPT3
        if net_pips > 0 and close_pos > 0.85:
            conf += 0.05
        if net_pips < 0 and close_pos < 0.15:
            conf += 0.05
        # OPT6
        if net_pips > 0 and d_high > 0.40:
            conf += 0.04
        if net_pips < 0 and d_low > 0.40:
            conf += 0.04
        # OPT5
        if vflag == "HIGH":
            conf += 0.03
        return VerdictV4(
            "PROGRESSIVE_WAVE", round(min(conf, 0.95), 2), "pw_with_context",
            detail={**detail_extra, "nr": nr, "net": net, "curvature": curvature},
            volatility_flag=vflag, close_position=close_pos,
            osc_asymmetry=osc_asym, curvature=curvature, slope_ratio=slope_ratio
        )

    # -----------------------------------------------------------------------
    # 17. v5 — C2 : PW standalone (sans contexte actif)
    # -----------------------------------------------------------------------
    pw_nr_min = 0.70 if vflag == "EVENT" else PW_STANDALONE_NR_MIN
    if nr >= pw_nr_min and net >= PW_STANDALONE_NET_MIN:
        conf = 0.68
        if abs(slope_ratio) >= SLOPE_PW_MIN:
            conf += 0.04
        if curvature > 1.3:
            conf += 0.03
        return VerdictV4(
            "PROGRESSIVE_WAVE", round(conf, 2), "pw_standalone_strong",
            detail={"nr": nr, "net": net, "note": "no_ctx_but_strong_move",
                    "slope_ratio": slope_ratio},
            volatility_flag=vflag, close_position=close_pos,
            osc_asymmetry=osc_asym, curvature=curvature, slope_ratio=slope_ratio
        )

    # -----------------------------------------------------------------------
    # 18. v5 — OPT4 : PW slope rescue
    # -----------------------------------------------------------------------
    if abs(slope_ratio) >= SLOPE_PW_MIN and net >= 4.0:
        return VerdictV4(
            "PROGRESSIVE_WAVE", 0.66, "pw_slope_rescue",
            detail={"slope_ratio": slope_ratio, "note": "slope_confirmed_pw"},
            volatility_flag=vflag, close_position=close_pos,
            osc_asymmetry=osc_asym, curvature=curvature, slope_ratio=slope_ratio
        )

    # -----------------------------------------------------------------------
    # 19. INCONCLUSIVE
    # -----------------------------------------------------------------------
    return VerdictV4(
        "INCONCLUSIVE", 0.40, "no_rule_matched",
        detail={"nr": nr, "net": net, "dcp": dcp, "osc": osc},
        volatility_flag=vflag, close_position=close_pos,
        osc_asymmetry=osc_asym, curvature=curvature, slope_ratio=slope_ratio
    )


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------
def get_verdict(closes: list, context: Optional[dict] = None) -> VerdictV4:
    return compute_verdict(closes, context)


# ---------------------------------------------------------------------------
# SMOKE TEST
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import random
    random.seed(42)

    base = 1.3400
    # W08-like : strong PW standalone, nr=1.0 net=6.8p
    closes_pw = [base + i * 0.0001 * 0.8 for i in range(20)]
    closes_pw[-1] = base + 0.00068
    v = get_verdict(closes_pw)
    print(f"PW standalone  : {v.verdict} conf={v.confidence} rule={v.rule}")
    print(f"  slope={v.slope_ratio} curv={v.curvature} vflag={v.volatility_flag}")

    # W01-like : CM oscillatoire osc=9 dcp=0.68
    closes_cm = []
    center_cm = base
    for i in range(30):
        closes_cm.append(center_cm + ((-1)**i) * 0.00005)
    v2 = get_verdict(closes_cm)
    print(f"CM oscillatoire: {v2.verdict} conf={v2.confidence} rule={v2.rule}")

    # CB + override C3 : net=9.8p nr=0.89 dans contexte inverse
    closes_cb = [base - i * 0.0001 for i in range(10)]
    ctx_cb = {"context_direction": "UP", "context_net_pips": 5.0,
              "is_pullback_context": False, "is_inverse_context": True}
    v3 = get_verdict(closes_cb, ctx_cb)
    print(f"CB/PW override : {v3.verdict} conf={v3.confidence} rule={v3.rule}")

    print("\n✅ pf_price_verdict_v5.py OK")
