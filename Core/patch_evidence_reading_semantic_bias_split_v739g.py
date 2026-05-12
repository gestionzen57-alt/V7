from pathlib import Path

path = Path("pf_evidence_reading_once.py")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_semantic_bias_split_v739g")
backup.write_text(text, encoding="utf-8")

old = '''    bias = str(bus.get("dominant_bias") or "UNKNOWN").upper()
    attention = str(bus.get("global_attention") or "INFO").upper()
    confidence = bus.get("confidence")
'''

new = '''    bias = str(bus.get("dashboard_bias") or bus.get("dominant_bias") or "UNKNOWN").upper()
    dominant_bias = str(bus.get("dominant_bias") or "UNKNOWN").upper()
    structural_bias = str(bus.get("structural_bias") or bias or "UNKNOWN").upper()
    counterflow_bias = str(bus.get("counterflow_bias") or "UNKNOWN").upper()
    semantic_warning = str(bus.get("semantic_warning") or "NONE").upper()
    attention = str(bus.get("global_attention") or "INFO").upper()
    confidence = bus.get("confidence")
'''

if old not in text:
    raise SystemExit("PATCH_FAIL | bias block not found")

text = text.replace(old, new, 1)

old_return = '''        "bias": bias,
        "confidence": confidence,
        "phrase": phrase,
        "watch": watch,
'''

new_return = '''        "bias": bias,
        "dominant_bias": dominant_bias,
        "structural_bias": structural_bias,
        "counterflow_bias": counterflow_bias,
        "semantic_warning": semantic_warning,
        "confidence": confidence,
        "phrase": phrase,
        "watch": watch,
'''

if old_return not in text:
    raise SystemExit("PATCH_FAIL | return bias block not found")

text = text.replace(old_return, new_return, 1)

old_txt = '''        f"bias={data.get('bias')}",
        f"confidence={data.get('confidence')}",
'''

new_txt = '''        f"bias={data.get('bias')}",
        f"structural_bias={data.get('structural_bias')}",
        f"counterflow_bias={data.get('counterflow_bias')}",
        f"semantic_warning={data.get('semantic_warning')}",
        f"confidence={data.get('confidence')}",
'''

if old_txt not in text:
    raise SystemExit("PATCH_FAIL | txt bias block not found")

text = text.replace(old_txt, new_txt, 1)

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | evidence reading semantic bias split | backup={backup.name}")
