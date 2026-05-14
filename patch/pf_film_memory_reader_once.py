#!/usr/bin/env python3
"""PowerFlow V7.6 minimal B6 film memory reader.

B6 is informative only. It can reinforce, limit, expose false_positive_risk,
and suggest expected_next_behavior, but it never decides qualified_bias alone.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def _upper(value: Any) -> str:
    if value is None:
        return "UNKNOWN"
    text = str(value).strip()
    return text.upper() if text else "UNKNOWN"


def load_film_memory(path: str | Path | None) -> List[Dict[str, Any]]:
    """Load memory cards from JSON list, JSON object, or JSONL.

    Missing or unreadable files return [] so the patch can run in fallback mode.
    """
    if not path:
        return []
    path = Path(path)
    if not path.exists():
        return []
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError:
        return []
    if not text:
        return []
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [card for card in parsed if isinstance(card, dict)]
        if isinstance(parsed, dict):
            if isinstance(parsed.get("films"), list):
                return [card for card in parsed["films"] if isinstance(card, dict)]
            return [parsed]
    except json.JSONDecodeError:
        cards: List[Dict[str, Any]] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                cards.append(item)
        return cards
    return []


def _tokens(card: Dict[str, Any]) -> set[str]:
    values: List[str] = []
    for key in ["film_state", "last_structural_event", "current_zone_status", "current_move_role", "raw_bias", "qualified_bias", "pattern", "sequence", "name"]:
        value = card.get(key)
        if isinstance(value, list):
            values.extend(str(v) for v in value)
        elif value is not None:
            values.append(str(value))
    return {_upper(value) for value in values if value}


def _context_tokens(context: Dict[str, Any]) -> set[str]:
    return {_upper(context.get(key)) for key in ["film_state", "last_structural_event", "current_zone_status", "current_move_role", "raw_bias", "qualified_bias"]}


def match_film_context(context: Dict[str, Any], memory_cards: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Return the closest film memory match without deciding the packet."""
    context = context or {}
    ctx = _context_tokens(context)
    best_card: Dict[str, Any] | None = None
    best_score = 0.0
    best_overlap: List[str] = []

    for card in memory_cards or []:
        card_tokens = _tokens(card)
        if not card_tokens:
            continue
        overlap = sorted(ctx.intersection(card_tokens))
        score = len(overlap) / max(len(ctx), 1)
        if score > best_score:
            best_score = score
            best_card = card
            best_overlap = overlap

    if not best_card:
        return {
            "memory_match": "UNKNOWN",
            "memory_confidence": 0.0,
            "expected_next_behavior": "UNKNOWN",
            "false_positive_risk": "UNKNOWN",
            "memory_effect": "NO_DECISION",
            "matched_fields": [],
        }

    expected = best_card.get("expected_next_behavior") or best_card.get("next_expected_behavior") or best_card.get("outcome") or "UNKNOWN"
    false_positive_risk = best_card.get("false_positive_risk") or best_card.get("risk") or "UNKNOWN"
    memory_effect = "REINFORCE_OR_LIMIT_ONLY"
    if false_positive_risk != "UNKNOWN":
        memory_effect = "LIMIT_WITH_FALSE_POSITIVE_RISK"

    return {
        "memory_match": str(best_card.get("name") or best_card.get("film") or best_card.get("pattern") or "UNKNOWN"),
        "memory_confidence": round(float(best_score), 4),
        "expected_next_behavior": str(expected),
        "false_positive_risk": str(false_positive_risk),
        "memory_effect": memory_effect,
        "matched_fields": best_overlap,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read B6 film memory and match a terrain context.")
    parser.add_argument("--context", required=True, help="Context JSON")
    parser.add_argument("--memory", required=True, help="Memory JSON/JSONL")
    parser.add_argument("--output", required=True, help="Output match JSON")
    args = parser.parse_args()

    with open(args.context, "r", encoding="utf-8") as handle:
        context = json.load(handle)
    result = match_film_context(context, load_film_memory(args.memory))
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
