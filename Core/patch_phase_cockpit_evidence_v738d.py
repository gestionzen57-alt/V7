from pathlib import Path
import re

path = Path("pf_phase_synthesizer_once.py")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_cockpit_evidence_v738d")
backup.write_text(text, encoding="utf-8")

# Add robust cockpit evidence helper if missing
helper = r'''
def _cockpit_evidence(cockpit: dict) -> str:
    if not isinstance(cockpit, dict):
        return "UNKNOWN"

    action = (
        cockpit.get("action")
        or cockpit.get("attention")
        or cockpit.get("status")
        or cockpit.get("decision")
        or "UNKNOWN"
    )

    state = (
        cockpit.get("state")
        or cockpit.get("etat")
        or cockpit.get("main_state")
        or cockpit.get("market_state")
        or "UNKNOWN"
    )

    synthesis = (
        cockpit.get("synthesis")
        or cockpit.get("live_synthesis")
        or cockpit.get("multiread_synthesis")
        or cockpit.get("reading_type")
        or "UNKNOWN"
    )

    return f"{action} | {state} | synthesis={synthesis}"
'''

if "def _cockpit_evidence(" not in text:
    # Insert before main if possible, otherwise before if __name__
    marker = "\ndef main("
    if marker in text:
        text = text.replace(marker, helper + marker, 1)
    else:
        marker = '\nif __name__ == "__main__":'
        text = text.replace(marker, helper + marker, 1)

# Replace weak cockpit evidence patterns
text = re.sub(
    r'(["\']- Cockpit=)\{?[^\\n"\']*\}?(["\'])',
    r'\1" + _cockpit_evidence(cockpit) + r"\2',
    text
)

# If the file builds evidence list differently, patch common append form
text = text.replace(
    'f"- Cockpit={cockpit_status}"',
    'f"- Cockpit={_cockpit_evidence(cockpit)}"'
)
text = text.replace(
    'f"- Cockpit={cockpit_state}"',
    'f"- Cockpit={_cockpit_evidence(cockpit)}"'
)
text = text.replace(
    '"- Cockpit="',
    'f"- Cockpit={_cockpit_evidence(cockpit)}"'
)

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | phase cockpit evidence hardened | backup={backup.name}")
