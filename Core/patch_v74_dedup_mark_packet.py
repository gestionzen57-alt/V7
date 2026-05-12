from pathlib import Path
from datetime import datetime, timezone

TARGET = Path("pf_powerflow_telegram_gate_dedup_once.py")

if not TARGET.exists():
    raise SystemExit("PATCH_FAIL | pf_powerflow_telegram_gate_dedup_once.py missing")

text = TARGET.read_text(encoding="utf-8", errors="replace")

backup = TARGET.with_suffix(".py.bak_dedup_mark_packet_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"))
backup.write_text(text, encoding="utf-8")

old = '        mark_sent(d, d.get("reason") or "DRY_RUN_MARK_SEEN")\n'
new = '        mark_sent(d.get("packet") or {}, d.get("reason") or "DRY_RUN_MARK_SEEN")\n'

if old not in text:
    raise SystemExit("PATCH_FAIL | expected mark_sent decision call not found")

text = text.replace(old, new, 1)
TARGET.write_text(text, encoding="utf-8")

print("PATCH_OK | dry-run marks real packet, not decision wrapper")
print("backup=", backup.name)
