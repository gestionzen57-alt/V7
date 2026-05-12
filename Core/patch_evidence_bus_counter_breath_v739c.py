from pathlib import Path

path = Path("pf_evidence_bus_once.py")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_counter_breath_v739c")
backup.write_text(text, encoding="utf-8")

old = '''    if up_w > 0.0 and down_w > 0.0 and conflict_gap <= 0.18:
        dominant_bias = "CONFLICT"
        if dominant_phase in {"UNKNOWN", "NO_CLEAR_PHASE"}:
            dominant_phase = "DIRECTIONAL_CONFLICT"
        confidence = min(confidence, 0.45)
    elif total_directional > 0:
        dominant_bias = "PAIR_UP" if up_w > down_w else "PAIR_DOWN"
    else:
        dominant_bias = phase_bias
'''

new = '''    if up_w > 0.0 and down_w > 0.0 and conflict_gap <= 0.18:
        dominant_bias = "CONFLICT"
        dominant_phase = "DIRECTIONAL_CONFLICT"
        confidence = min(confidence, 0.45)

    elif up_w >= 0.25 and down_w >= 0.25:
        dominant_bias = "PAIR_UP" if up_w > down_w else "PAIR_DOWN"

        up_layers = set(layer_votes.get("PAIR_UP") or [])
        down_layers = set(layer_votes.get("PAIR_DOWN") or [])

        if {"LTF", "MTF"}.issubset(up_layers) and {"HTF", "COCKPIT"}.intersection(down_layers):
            dominant_phase = "STRUCTURAL_BEARISH_WITH_LTF_MTF_COUNTERFLOW"
            confidence = min(confidence, 0.55)
        elif {"LTF", "MTF"}.issubset(down_layers) and {"HTF", "COCKPIT"}.intersection(up_layers):
            dominant_phase = "STRUCTURAL_BULLISH_WITH_LTF_MTF_COUNTERFLOW"
            confidence = min(confidence, 0.55)
        else:
            dominant_phase = "DIRECTIONAL_CONFLICT"
            confidence = min(confidence, 0.55)

    elif total_directional > 0:
        dominant_bias = "PAIR_UP" if up_w > down_w else "PAIR_DOWN"
    else:
        dominant_bias = phase_bias
'''

if old not in text:
    raise SystemExit("PATCH_FAIL | target bias block not found")

text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | counter-breath phase naming added | backup={backup.name}")
