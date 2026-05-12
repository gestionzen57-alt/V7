#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

LEVEL_FILE = Path("pf_daily_level_interaction.py")
SWEEP_FILE = Path("pf_daily_sweep_classifier.py")

CLASSIFY_NEW = """def classify_level_interaction(symbol: str, current_rows: Sequence[Dict[str, Any]], level: Dict[str, Any]) -> Dict[str, Any]:
    price = float(level["price"])
    tol = tolerance(symbol, price)
    touches, pierce_up, pierce_down = [], [], []
    last_close = current_rows[-1]["close"] if current_rows else None

    for idx, c in enumerate(current_rows):
        if c.get("high") is None or c.get("low") is None or c.get("close") is None:
            continue
        if candle_crosses_level(c, price, tol):
            touches.append(idx)
        if c["high"] > price + tol:
            pierce_up.append(idx)
        if c["low"] < price - tol:
            pierce_down.append(idx)

    real_test = bool(touches)

    if not real_test:
        if last_close is not None and last_close > price + tol:
            state = "CONTEXT_ABOVE_LEVEL"
        elif last_close is not None and last_close < price - tol:
            state = "CONTEXT_BELOW_LEVEL"
        else:
            state = "UNTESTED"
    else:
        recent = current_rows[-10:] if len(current_rows) >= 10 else current_rows
        recent_above = sum(1 for c in recent if c.get("close") is not None and c["close"] > price + tol)
        recent_below = sum(1 for c in recent if c.get("close") is not None and c["close"] < price - tol)

        if last_close is not None and pierce_up and last_close < price - tol:
            state = "REJECTED_FROM_ABOVE"
        elif last_close is not None and pierce_down and last_close > price + tol:
            state = "REJECTED_FROM_BELOW"
        elif recent_above >= max(3, int(len(recent) * 0.6)):
            state = "ACCEPTED_ABOVE"
        elif recent_below >= max(3, int(len(recent) * 0.6)):
            state = "ACCEPTED_BELOW"
        elif pierce_up or pierce_down:
            state = "PIERCED"
        else:
            state = "TOUCHED"

    first_idx = touches[0] if touches else None
    first_ts = current_rows[first_idx]["timestamp_utc"] if first_idx is not None and first_idx < len(current_rows) else None

    robustness = 0.0
    if state in ("TOUCHED", "PIERCED"):
        robustness += 0.25
    if state.startswith("REJECTED") or state.startswith("ACCEPTED"):
        robustness += 0.35
    if len(touches) >= 2:
        robustness += 0.15
    if len(current_rows) >= 60:
        robustness += 0.15
    if str(level.get("source", "")).startswith(("H1", "H4", "M1_DERIVED_PREVIOUS")):
        robustness += 0.10
    if state.startswith("CONTEXT_"):
        robustness = min(robustness, 0.20)

    return {
        "level": level.get("name"),
        "price": price,
        "source": level.get("source"),
        "interaction_state": state,
        "first_touch_utc": first_ts,
        "touch_count": len(touches),
        "pierce_up_count": len(pierce_up),
        "pierce_down_count": len(pierce_down),
        "last_close": round(last_close, 6) if isinstance(last_close, (int, float)) else None,
        "tolerance": round(tol, 6),
        "robustness": round(min(1.0, robustness), 3),
    }
"""

DEDUP_NEW = """def dedupe_levels_by_price(symbol: str, levels: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    clusters: List[Dict[str, Any]] = []

    def priority(level: Dict[str, Any]) -> int:
        name = str(level.get("name", ""))
        source = str(level.get("source", ""))
        if "PREVIOUS_DAY" in name:
            return 5
        if source.startswith("H4"):
            return 4
        if source.startswith("H1"):
            return 3
        if "CURRENT_DAY" in name:
            return 2
        return 1

    for lvl in levels:
        price = lvl.get("price")
        if not isinstance(price, (int, float)):
            continue
        tol = tolerance(symbol, float(price))
        matched = None
        for cluster in clusters:
            if abs(float(cluster["price"]) - float(price)) <= tol:
                matched = cluster
                break
        if matched is None:
            new_lvl = dict(lvl)
            new_lvl["aliases"] = [dict(lvl)]
            clusters.append(new_lvl)
        else:
            matched.setdefault("aliases", []).append(dict(lvl))
            if priority(lvl) > priority(matched):
                aliases = matched["aliases"]
                matched.clear()
                matched.update(dict(lvl))
                matched["aliases"] = aliases

    return clusters
"""


def find_bounds(text: str, name: str):
    needle = f"def {name}("
    start = text.find(needle)
    if start < 0:
        return None
    line_start = text.rfind("\n", 0, start) + 1
    scan = text.find("\n", start)
    while scan != -1:
        nxt = scan + 1
        if text.startswith("def ", nxt) or text.startswith("class ", nxt):
            return line_start, nxt
        scan = text.find("\n", nxt)
    return line_start, len(text)


def replace_function(text: str, name: str, new_func: str) -> str:
    bounds = find_bounds(text, name)
    if not bounds:
        raise RuntimeError(f"function not found: {name}")
    start, end = bounds
    return text[:start] + new_func + "\n" + text[end:]


def patch_level_file() -> bool:
    if not LEVEL_FILE.exists():
        print("PATCH_FAIL | pf_daily_level_interaction.py missing")
        return False

    text = LEVEL_FILE.read_text(encoding="utf-8", errors="replace")
    if "CONTEXT_ABOVE_LEVEL" in text and "dedupe_levels_by_price" in text:
        print("LEVEL_PATCH_OK | already patched")
        return True

    backup = LEVEL_FILE.with_suffix(".py.bak_v732b_level_grammar")
    backup.write_text(text, encoding="utf-8")

    try:
        text = replace_function(text, "classify_level_interaction", CLASSIFY_NEW)
    except Exception as exc:
        print(f"PATCH_FAIL | classify replace failed | {exc}")
        return False

    if "dedupe_levels_by_price" not in text:
        anchor = "def build_level_interactions("
        pos = text.find(anchor)
        if pos < 0:
            print("PATCH_FAIL | build_level_interactions anchor not found")
            return False
        text = text[:pos] + DEDUP_NEW + "\n" + text[pos:]

    old = "levels = build_key_levels(symbol, current_rows, previous_rows, h1, h4)\n    interactions = [classify_level_interaction(symbol, current_rows, lvl) for lvl in levels]"
    new = "levels = dedupe_levels_by_price(symbol, build_key_levels(symbol, current_rows, previous_rows, h1, h4))\n    interactions = [classify_level_interaction(symbol, current_rows, lvl) for lvl in levels]"
    if old in text:
        text = text.replace(old, new)
    elif "dedupe_levels_by_price(symbol, build_key_levels" not in text:
        print("PATCH_WARN | level dedupe call not patched automatically")

    LEVEL_FILE.write_text(text, encoding="utf-8")
    print(f"LEVEL_PATCH_OK | patched | backup={backup}")
    return True


def patch_sweep_file() -> bool:
    if not SWEEP_FILE.exists():
        print("PATCH_FAIL | pf_daily_sweep_classifier.py missing")
        return False

    text = SWEEP_FILE.read_text(encoding="utf-8", errors="replace")
    if 'state.startswith("CONTEXT_")' in text:
        print("SWEEP_PATCH_OK | already patched")
        return True

    backup = SWEEP_FILE.with_suffix(".py.bak_v732b_sweep_context_guard")
    backup.write_text(text, encoding="utf-8")

    needle = '    state = str(item.get("interaction_state") or "")\n'
    insert = '    state = str(item.get("interaction_state") or "")\n    if state.startswith("CONTEXT_") or state == "UNTESTED":\n        return None\n'
    if needle not in text:
        print("PATCH_FAIL | sweep state anchor not found")
        return False

    text = text.replace(needle, insert, 1)
    SWEEP_FILE.write_text(text, encoding="utf-8")
    print(f"SWEEP_PATCH_OK | patched | backup={backup}")
    return True


def main() -> int:
    ok1 = patch_level_file()
    ok2 = patch_sweep_file()
    if not (ok1 and ok2):
        return 1
    print("PATCH_OK | V7.3.2b daily level grammar hotfix applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
