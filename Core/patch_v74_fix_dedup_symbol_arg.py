from pathlib import Path
from datetime import datetime, timezone

TARGET = Path("run_powerflow_live_stack_once.py")

bad = '("powerflow_telegram_gate_dedup", [py, "pf_powerflow_telegram_gate_dedup_once.py", "--symbol", args.symbol], 120),'
good = '("powerflow_telegram_gate_dedup", [py, "pf_powerflow_telegram_gate_dedup_once.py", "--symbol", str(args.symbols).split(",")[0].strip()], 120),'

if not TARGET.exists():
    raise SystemExit("PATCH_FAIL | run_powerflow_live_stack_once.py missing")

text = TARGET.read_text(encoding="utf-8", errors="replace")

if good in text:
    print("PATCH_OK | already fixed")
    raise SystemExit(0)

if bad not in text:
    raise SystemExit("PATCH_FAIL | bad args.symbol line not found")

backup = TARGET.with_suffix(".py.bak_v74_dedup_symbol_arg_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"))
backup.write_text(text, encoding="utf-8")

text = text.replace(bad, good, 1)
TARGET.write_text(text, encoding="utf-8")

print("PATCH_OK | args.symbol fixed -> first symbol from args.symbols")
print("backup=", backup)
