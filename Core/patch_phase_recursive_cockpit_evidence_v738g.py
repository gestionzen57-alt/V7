from pathlib import Path

path = Path("pf_phase_synthesizer_once.py")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_recursive_cockpit_evidence_v738g")
backup.write_text(text, encoding="utf-8")

start = text.find("def _cockpit_evidence(cockpit: dict) -> str:")
if start == -1:
    raise SystemExit("PATCH_FAIL | _cockpit_evidence not found")

next_def = text.find("\ndef ", start + 1)
if next_def == -1:
    next_def = text.find("\nif __name__", start + 1)
if next_def == -1:
    raise SystemExit("PATCH_FAIL | cannot find end of _cockpit_evidence")

new_func = r'''def _cockpit_evidence(cockpit: dict) -> str:
    def walk(obj):
        if isinstance(obj, dict):
            yield obj
            for v in obj.values():
                yield from walk(v)
        elif isinstance(obj, list):
            for v in obj:
                yield from walk(v)

    def first(keys, default="UNKNOWN"):
        for d in walk(cockpit):
            for k in keys:
                v = d.get(k)
                if v is not None and str(v).strip() not in {"", "None", "null"}:
                    return str(v).strip()
        return default

    action = first([
        "action",
        "attention",
        "status",
        "global_status",
        "decision",
        "wake_state",
        "trade_action",
    ])

    state = first([
        "state",
        "etat",
        "main_state",
        "market_state",
        "phase",
        "context",
        "label",
    ])

    synthesis = first([
        "synthesis",
        "live_synthesis",
        "multiread_synthesis",
        "reading_type",
        "reading",
        "alignment",
        "summary",
    ])

    return f"{action} | {state} | synthesis={synthesis}"
'''

text = text[:start] + new_func + text[next_def:]
path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | recursive cockpit evidence helper installed | backup={backup.name}")
