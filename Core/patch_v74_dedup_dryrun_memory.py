from pathlib import Path
from datetime import datetime, timezone

TARGET = Path("pf_powerflow_telegram_gate_dedup_once.py")

old = '''    if d.get("send") and not args.send:
        telegram_status = "WOULD_SEND_DRY_RUN"
'''

new = '''    if d.get("send") and not args.send:
        telegram_status = "WOULD_SEND_DRY_RUN"
        # V7.4 dry-run must also mark memory so dedup can be tested without real Telegram spam.
        mark_sent(d)
'''

if not TARGET.exists():
    raise SystemExit("PATCH_FAIL | pf_powerflow_telegram_gate_dedup_once.py missing")

text = TARGET.read_text(encoding="utf-8", errors="replace")

if new in text:
    print("PATCH_OK | already patched")
    raise SystemExit(0)

if old not in text:
    raise SystemExit("PATCH_FAIL | dry-run block not found")

backup = TARGET.with_suffix(".py.bak_dedup_dryrun_memory_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"))
backup.write_text(text, encoding="utf-8")

text = text.replace(old, new, 1)
TARGET.write_text(text, encoding="utf-8")

print("PATCH_OK | dry-run now writes dedup memory")
print("backup=", backup)
