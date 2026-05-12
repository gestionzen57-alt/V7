from pathlib import Path

path = Path("pf_phase_synthesizer_once.py")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_use_cockpit_helper_v738f")
backup.write_text(text, encoding="utf-8")

old = '    evidence.append(f"Cockpit={cockpit_action} {cockpit_state}")'
new = '    evidence.append(f"Cockpit={_cockpit_evidence(cockpit)}")'

if old not in text:
    raise SystemExit("PATCH_FAIL | target cockpit evidence line not found")

text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | cockpit evidence now uses helper | backup={backup.name}")
