from pathlib import Path

path = Path("pf_phase_synthesizer_once.py")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_force_cockpit_line_v738e")
backup.write_text(text, encoding="utf-8")

helper = r'''
def _pf_force_cockpit_evidence_line_v738e(txt: str, cockpit: dict) -> str:
    if not isinstance(cockpit, dict):
        cockpit = {}

    action = (
        cockpit.get("action")
        or cockpit.get("attention")
        or cockpit.get("status")
        or cockpit.get("global_status")
        or "UNKNOWN"
    )

    state = (
        cockpit.get("state")
        or cockpit.get("etat")
        or cockpit.get("main_state")
        or cockpit.get("market_state")
        or cockpit.get("phase")
        or "UNKNOWN"
    )

    synthesis = (
        cockpit.get("synthesis")
        or cockpit.get("live_synthesis")
        or cockpit.get("multiread_synthesis")
        or cockpit.get("reading_type")
        or cockpit.get("reading")
        or "UNKNOWN"
    )

    line = f"- Cockpit={action} | {state} | synthesis={synthesis}"

    out = []
    replaced = False
    for raw in str(txt).splitlines():
        if raw.strip().startswith("- Cockpit="):
            out.append(line)
            replaced = True
        else:
            out.append(raw)

    if not replaced:
        out.append(line)

    return "\n".join(out) + "\n"
'''

if "def _pf_force_cockpit_evidence_line_v738e(" not in text:
    marker = "\ndef main("
    if marker in text:
        text = text.replace(marker, helper + marker, 1)
    else:
        marker = '\nif __name__ == "__main__":'
        text = text.replace(marker, helper + marker, 1)

# Force after common txt/render variable names before write_text.
candidates = [
    "txt_path.write_text(txt, encoding=\"utf-8\")",
    "txt_path.write_text(text, encoding=\"utf-8\")",
    "args.txt.write_text(txt, encoding=\"utf-8\")",
    "Path(args.txt).write_text(txt, encoding=\"utf-8\")",
    "Path(args.txt).write_text(text, encoding=\"utf-8\")",
]

patched = 0
for c in candidates:
    if c in text:
        if "write_text(txt" in c:
            text = text.replace(c, "txt = _pf_force_cockpit_evidence_line_v738e(txt, cockpit)\n    " + c, 1)
            patched += 1
            break
        if "write_text(text" in c:
            text = text.replace(c, "text = _pf_force_cockpit_evidence_line_v738e(text, cockpit)\n    " + c, 1)
            patched += 1
            break

if patched == 0:
    raise SystemExit("PATCH_FAIL | txt write pattern not found. Need inspect write_text lines.")

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | forced cockpit evidence line | patched={patched} | backup={backup.name}")
