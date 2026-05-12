from pathlib import Path
from datetime import datetime, timezone

TARGET = Path("pf_powerflow_telegram_gate_dedup_once.py")

if not TARGET.exists():
    raise SystemExit("PATCH_FAIL | pf_powerflow_telegram_gate_dedup_once.py missing")

text = TARGET.read_text(encoding="utf-8", errors="replace")

backup = TARGET.with_suffix(".py.bak_conflict_cleanup_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"))
backup.write_text(text, encoding="utf-8")

# Remove raw git conflict marker lines.
clean_lines = []
for line in text.splitlines():
    s = line.strip()
    if s.startswith("<<<<<<<") or s.startswith("=======") or s.startswith(">>>>>>>"):
        continue
    clean_lines.append(line)

text = "\n".join(clean_lines) + "\n"

# Ensure mark_sent writes the real packet, not the decision wrapper.
text = text.replace(
    'mark_sent(d, d.get("reason") or "DRY_RUN_MARK_SEEN")',
    'mark_sent(d.get("packet") or {}, d.get("reason") or "DRY_RUN_MARK_SEEN")'
)

text = text.replace(
    'mark_sent(d)',
    'mark_sent(d.get("packet") or {}, d.get("reason") or "MARK_SEEN")'
)

TARGET.write_text(text, encoding="utf-8")

print("PATCH_OK | conflict markers removed and mark_sent normalized")
print("backup=", backup.name)
