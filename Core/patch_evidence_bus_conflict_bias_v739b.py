from pathlib import Path

path = Path("pf_evidence_bus_once.py")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_conflict_bias_v739b")
backup.write_text(text, encoding="utf-8")

start = text.find("def derive_global(evidence: list[dict[str, Any]]) -> dict[str, Any]:")
if start == -1:
    raise SystemExit("PATCH_FAIL | derive_global not found")

next_def = text.find("\ndef ", start + 1)
if next_def == -1:
    raise SystemExit("PATCH_FAIL | cannot find end of derive_global")

new_func = r'''def derive_global(evidence: list[dict[str, Any]]) -> dict[str, Any]:
    attention_rank = {
        "NO_ALERT": 0,
        "INFO": 1,
        "WATCH_CONTEXT": 2,
        "WATCH": 3,
        "WATCH_ATTENTION": 4,
        "ALERT_READY": 5,
        "WAKE_TRADER": 6,
        "HOT": 7,
        "ACTIVE": 8,
        "LIVE_ATTENTION_PRESENT": 5,
        "MULTIREAD_WAKE_TRADER": 6,
        "DEGRADED": 2,
    }

    max_attention = "INFO"
    for e in evidence:
        att = str(e.get("attention") or "INFO").upper()
        if attention_rank.get(att, 1) > attention_rank.get(max_attention, 1):
            max_attention = att

    phase_item = next((e for e in evidence if e.get("layer") == "PHASE_SYNTHESIS"), {})
    dominant_phase = first_non_empty(phase_item.get("state"), default="UNKNOWN")
    phase_bias = first_non_empty(phase_item.get("bias"), default="UNKNOWN")
    confidence = as_float(phase_item.get("confidence"), 0.0)

    bias_weights: dict[str, float] = {}
    layer_votes: dict[str, list[str]] = {"PAIR_UP": [], "PAIR_DOWN": []}

    # PHASE_SYNTHESIS is a result layer, not a raw vote when phase is unclear.
    for e in evidence:
        layer = str(e.get("layer") or "").upper()
        b = str(e.get("bias") or "").upper()
        if b not in {"PAIR_UP", "PAIR_DOWN"}:
            continue

        w = as_float(e.get("weight"), 0.0)

        if layer == "PHASE_SYNTHESIS" and dominant_phase in {"NO_CLEAR_PHASE", "MIXED_PHASE", "CONFLICT"}:
            w = 0.0

        bias_weights[b] = bias_weights.get(b, 0.0) + w
        if w > 0:
            layer_votes[b].append(layer)

    up_w = bias_weights.get("PAIR_UP", 0.0)
    down_w = bias_weights.get("PAIR_DOWN", 0.0)

    total_directional = up_w + down_w
    conflict_gap = abs(up_w - down_w)

    if up_w > 0.0 and down_w > 0.0 and conflict_gap <= 0.18:
        dominant_bias = "CONFLICT"
        if dominant_phase in {"UNKNOWN", "NO_CLEAR_PHASE"}:
            dominant_phase = "DIRECTIONAL_CONFLICT"
        confidence = min(confidence, 0.45)
    elif total_directional > 0:
        dominant_bias = "PAIR_UP" if up_w > down_w else "PAIR_DOWN"
    else:
        dominant_bias = phase_bias

    risks = []
    for e in evidence:
        risks.extend(e.get("technical_risks") or [])
    risks = sorted(set(str(r) for r in risks if r))

    if dominant_bias == "CONFLICT":
        risks.append("EVIDENCE_BUS_DIRECTIONAL_CONFLICT")

    return {
        "global_attention": max_attention,
        "dominant_phase": dominant_phase,
        "dominant_bias": dominant_bias,
        "confidence": round(confidence, 4),
        "bias_weights": {k: round(v, 4) for k, v in sorted(bias_weights.items())},
        "bias_votes": layer_votes,
        "technical_risks": sorted(set(risks)),
    }
'''

text = text[:start] + new_func + text[next_def:]
path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | evidence bus conflict-aware bias | backup={backup.name}")
