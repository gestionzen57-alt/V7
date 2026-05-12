from pathlib import Path

path = Path("pf_trader_cockpit_evidence_enrich.py")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_semantic_bias_split_v739g")
backup.write_text(text, encoding="utf-8")

old_bus = '''        "dominant_bias": bus.get("dominant_bias"),
        "confidence": bus.get("confidence"),
        "bias_weights": bus.get("bias_weights"),
'''

new_bus = '''        "dominant_bias": bus.get("dominant_bias"),
        "structural_bias": bus.get("structural_bias"),
        "counterflow_bias": bus.get("counterflow_bias"),
        "dashboard_bias": bus.get("dashboard_bias"),
        "semantic_warning": bus.get("semantic_warning"),
        "confidence": bus.get("confidence"),
        "bias_weights": bus.get("bias_weights"),
'''

if old_bus not in text:
    raise SystemExit("PATCH_FAIL | cockpit evidence_bus block not found")

text = text.replace(old_bus, new_bus, 1)

old_reading = '''        "bias": reading.get("bias"),
        "confidence": reading.get("confidence"),
        "phrase": reading.get("phrase"),
'''

new_reading = '''        "bias": reading.get("bias"),
        "structural_bias": reading.get("structural_bias"),
        "counterflow_bias": reading.get("counterflow_bias"),
        "semantic_warning": reading.get("semantic_warning"),
        "confidence": reading.get("confidence"),
        "phrase": reading.get("phrase"),
'''

if old_reading not in text:
    raise SystemExit("PATCH_FAIL | cockpit evidence_reading block not found")

text = text.replace(old_reading, new_reading, 1)

old_txt = '''        f"bias={reading.get('bias')}",
        f"confidence={reading.get('confidence')}",
        f"phrase={reading.get('phrase')}",
'''

new_txt = '''        f"bias={reading.get('bias')}",
        f"structural_bias={reading.get('structural_bias')}",
        f"counterflow_bias={reading.get('counterflow_bias')}",
        f"semantic_warning={reading.get('semantic_warning')}",
        f"confidence={reading.get('confidence')}",
        f"phrase={reading.get('phrase')}",
'''

if old_txt not in text:
    raise SystemExit("PATCH_FAIL | cockpit txt block not found")

text = text.replace(old_txt, new_txt, 1)

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | cockpit semantic bias split | backup={backup.name}")
