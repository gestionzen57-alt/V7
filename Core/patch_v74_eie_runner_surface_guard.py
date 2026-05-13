from pathlib import Path
from datetime import datetime, timezone

TARGET = Path("run_confluence_alert.py")

text = TARGET.read_text(encoding="utf-8", errors="replace")
backup = TARGET.with_suffix(".py.bak_eie_surface_guard_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"))
backup.write_text(text, encoding="utf-8")

old = '''    primary = load_json(OUT / symbol / "eie_confluence.json")

    report = {
'''

new = '''    out_json = OUT / symbol / "eie_confluence.json"
    out_txt = OUT / symbol / "eie_confluence.txt"
    primary = load_json(out_json)

    missing_outputs = []
    if not out_json.exists():
        missing_outputs.append(str(out_json))
    if not out_txt.exists():
        missing_outputs.append(str(out_txt))

    if missing_outputs:
        rc = 2

    report = {
'''

if old not in text:
    raise SystemExit("PATCH_FAIL | insertion point A not found")

text = text.replace(old, new, 1)

old2 = '''        "returncode": rc,
        "outputs": {
'''

new2 = '''        "returncode": rc,
        "missing_outputs": missing_outputs,
        "outputs": {
'''

if old2 not in text:
    raise SystemExit("PATCH_FAIL | insertion point B not found")

text = text.replace(old2, new2, 1)

old3 = '''    print("EIE_ALERT_QUEUE_OK")
    print("json=", OUT / "eie_alert_queue.json")
    return rc
'''

new3 = '''    if missing_outputs:
        print("EIE_ALERT_QUEUE_FAIL | missing_outputs=" + ",".join(missing_outputs))
    else:
        print("EIE_ALERT_QUEUE_OK")
    print("json=", OUT / "eie_alert_queue.json")
    return rc
'''

if old3 not in text:
    raise SystemExit("PATCH_FAIL | insertion point C not found")

text = text.replace(old3, new3, 1)

TARGET.write_text(text, encoding="utf-8")
print("PATCH_OK | EIE runner now fails if surface missing")
print("backup=", backup.name)
