from pathlib import Path
from datetime import datetime, timezone

TARGET = Path("pf_powerflow_telegram_gate_dedup_once.py")

if not TARGET.exists():
    raise SystemExit("PATCH_FAIL | pf_powerflow_telegram_gate_dedup_once.py missing")

text = TARGET.read_text(encoding="utf-8", errors="replace")

backup = TARGET.with_suffix(".py.bak_dedup_mark_sent_reason_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"))
backup.write_text(text, encoding="utf-8")

text2 = text.replace(
    "        mark_sent(d)\n",
    "        mark_sent(d, d.get(\"reason\") or \"DRY_RUN_MARK_SEEN\")\n"
)

if text2 == text:
    raise SystemExit("PATCH_FAIL | mark_sent(d) not found")

TARGET.write_text(text2, encoding="utf-8")

print("PATCH_OK | mark_sent now receives reason")
print("backup=", backup.name)
