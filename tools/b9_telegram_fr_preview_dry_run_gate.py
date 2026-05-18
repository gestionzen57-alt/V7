#!/usr/bin/env python
from __future__ import annotations
import argparse, json, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

VERSION_PREVIEW = "B9_TELEGRAM_FR_PREVIEW_V0"
VERSION_GATE = "B9_TELEGRAM_DRY_RUN_GATE_V0"

FORBIDDEN_PATTERNS = [
    r"\bBUY\b", r"\bSELL\b", r"\bachat\b", r"\bvente\b",
    r"\bentre\s+maintenant\b", r"\bprobabilit[ée]\s+de\s+r[ée]ussite\b",
    r"\bsignal\s+gagnant\b", r"\bconseil\s+financier\b",
]
REQUIRED_SECTIONS = ["B9 voit", "Zone", "État", "Mémoire proche", "Piège technique", "À surveiller", "Limite"]

def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"_missing": True, "_path": str(path)}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {"_invalid_json": True, "_path": str(path), "_error": str(exc)}

def first_non_empty(*values: Any, default: str = "non visible") -> str:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, list) and value:
            return "; ".join(str(x) for x in value)
        if not isinstance(value, (dict, tuple)) and value != "":
            return str(value)
    return default

def get_nested(obj: Mapping[str, Any], *keys: str) -> Any:
    cur: Any = obj
    for key in keys:
        if not isinstance(cur, Mapping):
            return None
        cur = cur.get(key)
    return cur

def flatten_candidates(obj: Any) -> list[Mapping[str, Any]]:
    if isinstance(obj, list):
        out = []
        for item in obj:
            out.extend(flatten_candidates(item))
        return out
    if not isinstance(obj, Mapping):
        return []
    for key in ("telegram_candidates","candidates","attention_packets","packets","moments","events","rows","items","cards"):
        value = obj.get(key)
        if isinstance(value, list):
            out = []
            for item in value:
                out.extend(flatten_candidates(item))
            return out
    keys = {"b9_see_fr","reading_fr","telegram_fr","what_happens_fr","zone","zone_label","state","memory_near","trap","watch","limit","moment_type","label_fr"}
    return [obj] if any(k in obj for k in keys) else []

def score_candidate(c: Mapping[str, Any]) -> float:
    score = 0.0
    for key in ("b6_memory_candidate_score","source_quality_score","proxy_raw_agreement_score"):
        try: score += float(c.get(key) or 0) * 2.0
        except Exception: pass
    verdict = str(c.get("proxy_vs_raw_verdict") or "")
    if verdict == "CONFIRMED_BY_RAW": score += 3
    elif verdict == "NUANCED_BY_RAW": score += 2
    elif verdict == "RAW_UNAVAILABLE": score -= 3
    state = str(c.get("b6_memory_candidate_state") or "")
    if state == "B6_KEEP_CANDIDATE": score += 3
    elif state == "B6_REVIEW_CANDIDATE": score += 2
    elif "REJECT" in state: score -= 3
    return score

def choose_candidate(*payloads: Mapping[str, Any]) -> Mapping[str, Any]:
    candidates = []
    for p in payloads:
        candidates.extend(flatten_candidates(p))
    if candidates:
        return sorted(candidates, key=score_candidate, reverse=True)[0]
    merged = {}
    for p in payloads:
        if isinstance(p, Mapping):
            merged.update({k:v for k,v in p.items() if not str(k).startswith("_")})
    return merged

def safe_line(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip() or "non visible"

def derive_preview(candidate: Mapping[str, Any], gate_payload: Mapping[str, Any], board_payload: Mapping[str, Any], attention_payload: Mapping[str, Any], display_contract: Mapping[str, Any]) -> dict[str, Any]:
    zone_obj = candidate.get("zone_memory") if isinstance(candidate.get("zone_memory"), Mapping) else {}
    parent_scene = candidate.get("parent_scene") if isinstance(candidate.get("parent_scene"), Mapping) else {}
    values = {
        "B9 voit": first_non_empty(candidate.get("telegram_fr"), candidate.get("b9_see_fr"), candidate.get("reading_fr"), candidate.get("what_happens_fr"), candidate.get("label_fr"), candidate.get("moment_type"), get_nested(attention_payload,"packet","film"), default="une scène B9 demande attention, sans décision automatique"),
        "Zone": first_non_empty(candidate.get("zone"), candidate.get("zone_label"), candidate.get("active_zone"), zone_obj.get("zone_id"), zone_obj.get("description_fr"), default="zone non visible dans le candidat"),
        "État": first_non_empty(candidate.get("state"), candidate.get("b6_memory_candidate_state"), candidate.get("source_quality_state"), candidate.get("proxy_raw_agreement_state"), get_nested(gate_payload,"state"), default="lecture à confirmer"),
        "Mémoire proche": first_non_empty(candidate.get("memory_near"), candidate.get("near_memory_fr"), candidate.get("film_pattern"), parent_scene.get("fractal_reading_fr"), default="mémoire proche non établie"),
        "Piège technique": first_non_empty(candidate.get("trap"), candidate.get("technical_trap"), candidate.get("false_positive_risk"), candidate.get("t0112_reason_flags"), default="risque de surinterprétation si source proxy ou raw incomplet"),
        "À surveiller": first_non_empty(candidate.get("watch"), candidate.get("watch_fr"), candidate.get("next_expected_behavior"), candidate.get("retest_outcome_hint"), default="réaction prix, retest, acceptation ou rejet de zone"),
        "Limite": first_non_empty(candidate.get("limit"), candidate.get("limits"), candidate.get("technical_limits"), candidate.get("data_visibility"), get_nested(display_contract,"limits"), default="lecture informative, source et raw à garder visibles"),
    }
    lines = [f"{section} : {safe_line(values[section])}" for section in REQUIRED_SECTIONS]
    return {
        "version": VERSION_PREVIEW,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "telegram_send_enabled": False,
        "message_candidate": "\n".join(lines),
        "sections": values,
        "source_candidate_score": score_candidate(candidate),
        "source_candidate_keys": sorted([str(k) for k in candidate.keys()])[:80],
        "doctrine": "Le message Telegram réveille l’attention, il ne décide pas.",
    }

def forbidden_hits(text: str) -> list[str]:
    return [p for p in FORBIDDEN_PATTERNS if re.search(p, text, flags=re.IGNORECASE)]

def build_gate(preview: Mapping[str, Any], input_status: Mapping[str, Any]) -> dict[str, Any]:
    message = str(preview.get("message_candidate") or "")
    hits = forbidden_hits(message)
    missing = [s for s in REQUIRED_SECTIONS if f"{s} :" not in message]
    ok = bool(message.strip()) and not hits and not missing
    return {
        "version": VERSION_GATE,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "telegram_send_enabled": False,
        "send_attempted": False,
        "gate_status": "DRY_RUN_PASS" if ok else "DRY_RUN_BLOCKED",
        "dry_run_only": True,
        "forbidden_language_hits": hits,
        "missing_sections": missing,
        "input_status": input_status,
        "constraints": ["NO_TELEGRAM_SEND","NO_TELEGRAM_MODULE_CREATION","NO_CREDENTIAL_TOUCH","NO_TELEGRAM_EXISTING_MODULE_MODIFICATION","READ_ONLY","NO_DB","NO_DASHBOARD_LIVE","NO_DECISION_LANGUAGE"],
        "message_candidate": message,
        "doctrine": "Le message Telegram réveille l’attention, il ne décide pas.",
    }

def md_preview(preview: Mapping[str, Any]) -> str:
    return f"""# B9 Telegram FR Preview V0

```text
version = {preview.get('version')}
telegram_send_enabled = false
```

## Message candidat

```text
{preview.get('message_candidate','')}
```

## Doctrine

Le message Telegram réveille l’attention, il ne décide pas.

## Contraintes

- Aucun envoi Telegram.
- Aucun module d’envoi.
- Aucun credential touché.
- Aucun module `telegram_*` modifié.
- Read-only.
- Aucune DB.
- Aucun dashboard live.
"""

def md_gate(gate: Mapping[str, Any]) -> str:
    return f"""# B9 Telegram Dry Run Gate V0

```text
version = {gate.get('version')}
gate_status = {gate.get('gate_status')}
telegram_send_enabled = false
send_attempted = false
dry_run_only = true
```

## Langage interdit

```text
forbidden_language_hits = {gate.get('forbidden_language_hits')}
missing_sections = {gate.get('missing_sections')}
```

## Message contrôlé

```text
{gate.get('message_candidate','')}
```

## Contraintes

{chr(10).join('- ' + str(x) for x in gate.get('constraints', []))}

## Doctrine

Le message Telegram réveille l’attention, il ne décide pas.
"""

def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate-candidate", default="outputs/b9_telegram_fr_gate_candidate_v0/B9_TELEGRAM_FR_GATE_CANDIDATE_V0.json")
    parser.add_argument("--reality-board", default="outputs/b9_reality_board_integration_candidate_v0/B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.json")
    parser.add_argument("--attention-packet", default="outputs/b9_trader_attention_packet_v0/B9_TRADER_ATTENTION_PACKET_V0.json")
    parser.add_argument("--display-contract", default="outputs/b9_french_event_display_contract_v0/B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.json")
    parser.add_argument("--output-dir", default="outputs/b9_telegram_fr_preview_v0")
    args = parser.parse_args(argv)
    paths = {"gate_candidate":Path(args.gate_candidate), "reality_board":Path(args.reality_board), "attention_packet":Path(args.attention_packet), "display_contract":Path(args.display_contract)}
    payloads = {k: load_json(v) for k,v in paths.items()}
    status = {k: {"path":str(v), "exists":v.exists(), "missing":bool(payloads[k].get("_missing")), "invalid_json":bool(payloads[k].get("_invalid_json"))} for k,v in paths.items()}
    candidate = choose_candidate(payloads["gate_candidate"], payloads["reality_board"], payloads["attention_packet"], payloads["display_contract"])
    preview = derive_preview(candidate, payloads["gate_candidate"], payloads["reality_board"], payloads["attention_packet"], payloads["display_contract"])
    gate = build_gate(preview, status)
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    (out/"B9_TELEGRAM_FR_PREVIEW_V0.json").write_text(json.dumps(preview, ensure_ascii=False, indent=2), encoding="utf-8")
    (out/"B9_TELEGRAM_FR_PREVIEW_V0.md").write_text(md_preview(preview), encoding="utf-8")
    (out/"B9_TELEGRAM_DRY_RUN_GATE_V0.json").write_text(json.dumps(gate, ensure_ascii=False, indent=2), encoding="utf-8")
    (out/"B9_TELEGRAM_DRY_RUN_GATE_V0.md").write_text(md_gate(gate), encoding="utf-8")
    print(f"Wrote: {out}")
    print(f"Gate: {gate['gate_status']}")
    return 0 if gate["gate_status"] == "DRY_RUN_PASS" else 2

if __name__ == "__main__":
    raise SystemExit(main())
