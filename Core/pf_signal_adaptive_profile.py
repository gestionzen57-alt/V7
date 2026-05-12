#!/usr/bin/env python3
"""
PowerFlow V7.2.1 — SIGNAL_ADAPTIVE_PROFILE

Parametric signal-readiness profile driven by DATA_HEALTH_MONITOR.

Doctrine:
- M1 is never censored, only qualified.
- HTF thinness reduces structural confidence but does not block M1 perception.
- No DB write.
- No BUY/SELL.
- Symbol is a parameter.

Inputs:
- output/data_health_monitor.json

Outputs by runner:
- output/dashboard_surface/{symbol}/signal_adaptive_profile.json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence


DEFAULT_SYMBOLS = ["GBPUSD", "EURUSD", "USDJPY"]

TF_MAP = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
}

# Minimal data required for each layer to be considered present.
# These are deliberately tactical and adaptive, not structural validation thresholds.
DEFAULT_RULES = {
    "m1_required_rows": 20,
    "m1_max_age_min": 30.0,
    "m5_thin_required_rows": 5,
    "m5_max_age_min": 30.0,
    "m15_seed_required_rows": 3,
    "m30_seed_required_rows": 2,
    "h1_seed_required_rows": 2,
    "h4_seed_required_rows": 1,
    "d1_seed_required_rows": 1,
    "full_stack_m15_rows": 10,
    "full_stack_m30_rows": 5,
    "full_stack_h1_rows": 5,
    "full_stack_h4_rows": 5,
    "full_stack_d1_rows": 3,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_symbols(value: str) -> List[str]:
    return [s.strip().upper() for s in str(value).split(",") if s.strip()]


def read_json(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def write_json(data: Mapping[str, Any], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def tf_payload(symbol_payload: Mapping[str, Any], tf: int) -> Mapping[str, Any]:
    tfs = symbol_payload.get("timeframes")
    if not isinstance(tfs, Mapping):
        return {}
    payload = tfs.get(str(tf))
    return payload if isinstance(payload, Mapping) else {}


def tf_rows(symbol_payload: Mapping[str, Any], tf: int) -> int:
    try:
        return int(tf_payload(symbol_payload, tf).get("row_count") or 0)
    except Exception:
        return 0


def tf_age(symbol_payload: Mapping[str, Any], tf: int) -> Optional[float]:
    raw = tf_payload(symbol_payload, tf).get("age_minutes")
    if raw is None:
        return None
    try:
        return float(raw)
    except Exception:
        return None


def tf_gap_count(symbol_payload: Mapping[str, Any], tf: int) -> int:
    payload = tf_payload(symbol_payload, tf)
    if "gap_count" in payload:
        try:
            return int(payload.get("gap_count") or 0)
        except Exception:
            pass
    gaps = payload.get("gaps")
    if isinstance(gaps, list):
        return len(gaps)
    return 0


def is_age_live(age: Optional[float], max_age: float) -> bool:
    return age is not None and age <= max_age


def layer_health(symbol_payload: Mapping[str, Any], rules: Mapping[str, Any]) -> Dict[str, bool]:
    rows = {label: tf_rows(symbol_payload, tf) for label, tf in TF_MAP.items()}
    ages = {label: tf_age(symbol_payload, tf) for label, tf in TF_MAP.items()}

    return {
        "M1_microfilm": rows["M1"] >= int(rules["m1_required_rows"]) and is_age_live(ages["M1"], float(rules["m1_max_age_min"])),
        "M5_relay_thin": rows["M5"] >= int(rules["m5_thin_required_rows"]) and is_age_live(ages["M5"], float(rules["m5_max_age_min"])),
        "M15_seed_context": rows["M15"] >= int(rules["m15_seed_required_rows"]),
        "M30_seed_context": rows["M30"] >= int(rules["m30_seed_required_rows"]),
        "H1_seed_context": rows["H1"] >= int(rules["h1_seed_required_rows"]),
        "H4_seed_context": rows["H4"] >= int(rules["h4_seed_required_rows"]),
        "D1_context": rows["D1"] >= int(rules["d1_seed_required_rows"]),
    }


def full_stack_ready(symbol_payload: Mapping[str, Any], rules: Mapping[str, Any]) -> bool:
    rows = {label: tf_rows(symbol_payload, tf) for label, tf in TF_MAP.items()}
    ages = {label: tf_age(symbol_payload, tf) for label, tf in TF_MAP.items()}

    return (
        rows["M1"] >= int(rules["m1_required_rows"])
        and is_age_live(ages["M1"], float(rules["m1_max_age_min"]))
        and rows["M5"] >= int(rules["m5_thin_required_rows"])
        and is_age_live(ages["M5"], float(rules["m5_max_age_min"]))
        and rows["M15"] >= int(rules["full_stack_m15_rows"])
        and rows["M30"] >= int(rules["full_stack_m30_rows"])
        and rows["H1"] >= int(rules["full_stack_h1_rows"])
        and rows["H4"] >= int(rules["full_stack_h4_rows"])
        and rows["D1"] >= int(rules["full_stack_d1_rows"])
    )


def classify_mode(symbol_payload: Mapping[str, Any], rules: Mapping[str, Any]) -> tuple[str, str]:
    layers = layer_health(symbol_payload, rules)
    if full_stack_ready(symbol_payload, rules):
        return "FULL_STACK_SIGNAL_READY", "ALLOW_FULL_STACK_QUALIFIED"

    if layers["M1_microfilm"] and layers["M5_relay_thin"]:
        return "M1_TACTICAL_THIN_HTF", "ALLOW_M1_QUALIFIED"

    if layers["M1_microfilm"]:
        return "M1_ONLY_NO_RELAY", "ALLOW_M1_DEGRADED"

    return "DATA_NOT_READY", "HOLD_PERCEPTION_ONLY"


def compute_context_confidence(symbol_payload: Mapping[str, Any], rules: Mapping[str, Any]) -> float:
    layers = layer_health(symbol_payload, rules)

    weights = {
        "M1_microfilm": 0.35,
        "M5_relay_thin": 0.20,
        "M15_seed_context": 0.12,
        "M30_seed_context": 0.08,
        "H1_seed_context": 0.10,
        "H4_seed_context": 0.10,
        "D1_context": 0.05,
    }

    score = sum(weight for layer, weight in weights.items() if layers.get(layer))
    return round(min(1.0, max(0.0, score)), 3)


def compute_profile(
    symbol: str,
    data_health: Mapping[str, Any],
    rules: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    symbol = symbol.upper()
    rules = dict(DEFAULT_RULES if rules is None else rules)

    symbols_obj = data_health.get("symbols")
    if not isinstance(symbols_obj, Mapping):
        symbols_obj = {}

    symbol_payload = symbols_obj.get(symbol)
    if not isinstance(symbol_payload, Mapping):
        symbol_payload = {}

    rows = {label: tf_rows(symbol_payload, tf) for label, tf in TF_MAP.items()}
    ages = {label: tf_age(symbol_payload, tf) for label, tf in TF_MAP.items()}
    gaps = {label: tf_gap_count(symbol_payload, tf) for label, tf in TF_MAP.items()}

    layers = layer_health(symbol_payload, rules)
    mode, permission = classify_mode(symbol_payload, rules)
    confidence = compute_context_confidence(symbol_payload, rules)

    disabled = [layer for layer, ok in layers.items() if not ok]
    technical_risks: List[str] = []

    if not layers["M1_microfilm"]:
        technical_risks.append(f"{symbol}_M1_NOT_LIVE_ENOUGH")
    if not layers["M5_relay_thin"]:
        technical_risks.append(f"{symbol}_M5_RELAY_MISSING_OR_TOO_THIN")

    if rows["H4"] < int(rules["full_stack_h4_rows"]):
        technical_risks.append(f"{symbol}_HTF_THIN_H4")
    if rows["D1"] < int(rules["full_stack_d1_rows"]):
        technical_risks.append(f"{symbol}_D1_NOT_READY")
    if any(v > 0 for v in gaps.values()):
        technical_risks.append(f"{symbol}_TEMPORAL_GAPS_PRESENT")

    if mode == "M1_TACTICAL_THIN_HTF":
        technical_risks.append("HTF_STRUCTURE_WEAK_DO_NOT_BLOCK_M1")
    if mode == "M1_ONLY_NO_RELAY":
        technical_risks.append("M5_RELAY_ABSENT_DO_NOT_CENSOR_M1")
    if mode == "DATA_NOT_READY":
        technical_risks.append("DATA_NOT_READY_FOR_SIGNAL_PROFILE")

    source_status = str(symbol_payload.get("status", "UNKNOWN"))
    if source_status in {"DATA_STALE", "PARTIAL_STALE", "HTF_INCOMPLETE"}:
        technical_risks.append(f"DATA_HEALTH_STATUS_{source_status}")

    # Deduplicate while preserving order.
    deduped: List[str] = []
    for risk in technical_risks:
        if risk not in deduped:
            deduped.append(risk)

    return {
        "timestamp_utc": utc_now_iso(),
        "symbol": symbol,
        "method": "SIGNAL_ADAPTIVE_PROFILE",
        "mode": mode,
        "signal_permission": permission,
        "context_confidence": confidence,
        "source_data_health_status": source_status,
        "rows": rows,
        "ages_minutes": ages,
        "gap_counts": gaps,
        "adaptive_rules": rules,
        "enabled_layers": layers,
        "disabled_or_degraded_layers": disabled,
        "technical_risks": deduped,
        "note": "M1 is qualified, never censored. HTF thinness reduces structural confidence but does not block M1 perception.",
    }


def compute_profiles(
    data_health_path: str = "output/data_health_monitor.json",
    symbols: Sequence[str] = DEFAULT_SYMBOLS,
    rules: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    health = read_json(data_health_path)
    profiles = {symbol.upper(): compute_profile(symbol, health, rules) for symbol in symbols}
    global_mode = classify_global_mode(profiles)
    return {
        "timestamp_utc": utc_now_iso(),
        "method": "SIGNAL_ADAPTIVE_PROFILE_MULTI",
        "source": data_health_path,
        "global_mode": global_mode,
        "symbols": profiles,
        "technical_risks": collect_global_risks(profiles),
    }


def classify_global_mode(profiles: Mapping[str, Mapping[str, Any]]) -> str:
    if not profiles:
        return "DATA_NOT_READY"
    modes = [str(p.get("mode")) for p in profiles.values()]
    if all(m == "FULL_STACK_SIGNAL_READY" for m in modes):
        return "FULL_STACK_SIGNAL_READY"
    if any(m in {"FULL_STACK_SIGNAL_READY", "M1_TACTICAL_THIN_HTF", "M1_ONLY_NO_RELAY"} for m in modes):
        return "PARTIAL_SIGNAL_AVAILABLE"
    return "DATA_NOT_READY"


def collect_global_risks(profiles: Mapping[str, Mapping[str, Any]]) -> List[str]:
    risks: List[str] = []
    for symbol, profile in profiles.items():
        for risk in profile.get("technical_risks", []):
            item = f"{symbol}:{risk}"
            if item not in risks:
                risks.append(item)
    return risks


def main() -> int:
    parser = argparse.ArgumentParser(description="PowerFlow SIGNAL_ADAPTIVE_PROFILE")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--data-health", default="output/data_health_monitor.json")
    parser.add_argument("--output", "--out", dest="output", default=None)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    health = read_json(args.data_health)
    profile = compute_profile(args.symbol, health)

    output = args.output or f"output/dashboard_surface/{args.symbol.upper()}/signal_adaptive_profile.json"
    write_json(profile, output)

    if args.pretty:
        print(json.dumps(profile, indent=2, ensure_ascii=False))
    else:
        print(
            "SIGNAL_ADAPTIVE_PROFILE_OK | "
            f"symbol={profile['symbol']} | "
            f"mode={profile['mode']} | "
            f"permission={profile['signal_permission']} | "
            f"confidence={profile['context_confidence']} | "
            f"out={output}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
