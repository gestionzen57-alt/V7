from pathlib import Path
from datetime import datetime, timezone

TARGET = Path("run_powerflow_live_stack_once.py")

old = '("powerflow_telegram_gate", [py, "pf_powerflow_telegram_gate_once.py"], 120),'
new = '("powerflow_telegram_gate_dedup", [py, "pf_powerflow_telegram_gate_dedup_once.py", "--symbol", args.symbol], 120),'

if not TARGET.exists():
    raise SystemExit("PATCH_FAIL | run_powerflow_live_stack_once.py missing")

text = TARGET.read_text(encoding="utf-8", errors="replace")

if new in text:
    print("PATCH_OK | already uses dedup gate")
    raise SystemExit(0)

if old not in text:
    raise SystemExit("PATCH_FAIL | old telegram gate line not found")

backup = TARGET.with_suffix(".py.bak_v74_dedup_scheduler_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"))
backup.write_text(text, encoding="utf-8")

text = text.replace(old, new, 1)
TARGET.write_text(text, encoding="utf-8")

print("PATCH_OK | scheduler now uses telegram dedup gate")
print("backup=", backup)
