from pathlib import Path

path = Path("pf_evidence_bus_once.py")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_semantic_bias_split_v739g")
backup.write_text(text, encoding="utf-8")

old = '''    return {
        "global_attention": max_attention,
        "dominant_phase": dominant_phase,
        "dominant_bias": dominant_bias,
        "confidence": round(confidence, 4),
        "bias_weights": {k: round(v, 4) for k, v in sorted(bias_weights.items())},
        "bias_votes": layer_votes,
        "technical_risks": sorted(set(risks)),
    }
'''

new = '''    structural_bias = dominant_bias
    counterflow_bias = "UNKNOWN"
    dashboard_bias = dominant_bias
    semantic_warning = "NONE"

    if dominant_phase == "STRUCTURAL_BEARISH_WITH_LTF_MTF_COUNTERFLOW":
        structural_bias = "PAIR_DOWN"
        counterflow_bias = "PAIR_UP"
        dashboard_bias = "PAIR_DOWN"
        semantic_warning = "LTF_MTF_COUNTERFLOW_ACTIVE"
        if "EVIDENCE_BUS_LTF_MTF_COUNTERFLOW_ACTIVE" not in risks:
            risks.append("EVIDENCE_BUS_LTF_MTF_COUNTERFLOW_ACTIVE")

    elif dominant_phase == "STRUCTURAL_BULLISH_WITH_LTF_MTF_COUNTERFLOW":
        structural_bias = "PAIR_UP"
        counterflow_bias = "PAIR_DOWN"
        dashboard_bias = "PAIR_UP"
        semantic_warning = "LTF_MTF_COUNTERFLOW_ACTIVE"
        if "EVIDENCE_BUS_LTF_MTF_COUNTERFLOW_ACTIVE" not in risks:
            risks.append("EVIDENCE_BUS_LTF_MTF_COUNTERFLOW_ACTIVE")

    elif dominant_bias == "CONFLICT":
        dashboard_bias = "CONFLICT"
        semantic_warning = "DIRECTIONAL_CONFLICT_ACTIVE"

    return {
        "global_attention": max_attention,
        "dominant_phase": dominant_phase,
        "dominant_bias": dominant_bias,
        "structural_bias": structural_bias,
        "counterflow_bias": counterflow_bias,
        "dashboard_bias": dashboard_bias,
        "semantic_warning": semantic_warning,
        "confidence": round(confidence, 4),
        "bias_weights": {k: round(v, 4) for k, v in sorted(bias_weights.items())},
        "bias_votes": layer_votes,
        "technical_risks": sorted(set(risks)),
    }
'''

if old not in text:
    raise SystemExit("PATCH_FAIL | return block not found")

text = text.replace(old, new, 1)

old_txt = '''        f"bias={data.get('dominant_bias')}",
        f"confidence={data.get('confidence')}",
'''

new_txt = '''        f"bias={data.get('dominant_bias')}",
        f"structural_bias={data.get('structural_bias')}",
        f"counterflow_bias={data.get('counterflow_bias')}",
        f"dashboard_bias={data.get('dashboard_bias')}",
        f"semantic_warning={data.get('semantic_warning')}",
        f"confidence={data.get('confidence')}",
'''

if old_txt not in text:
    raise SystemExit("PATCH_FAIL | txt header block not found")

text = text.replace(old_txt, new_txt, 1)

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | semantic bias split installed | backup={backup.name}")
