from __future__ import annotations

import re
from pathlib import Path
from datetime import datetime

path = Path("scheduler_powerflow_turbo_wrapper.py")
text = path.read_text(encoding="utf-8")

backup = Path(f"scheduler_powerflow_turbo_wrapper.py.bak_time_profiles_v737d_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
backup.write_text(text, encoding="utf-8")

if "time_profile_ltf" not in text:
    marker = '    run_step("trader_cockpit", ['
    insert = '''    run_step("time_profile_ltf", [
        sys.executable, "run_ltf_profile_once.py",
        "--symbol", "GBPUSD",
    ], core)
    run_step("time_profile_mtf", [
        sys.executable, "run_mtf_profile_once.py",
        "--symbol", "GBPUSD",
    ], core)
    run_step("time_profile_htf", [
        sys.executable, "run_htf_profile_once.py",
        "--symbol", "GBPUSD",
    ], core)
    run_step("time_profiles_normalize", [
        sys.executable, "dashboard_normalize_time_profiles.py",
        "--symbol", "GBPUSD",
        "--output", "output/dashboard_surface/time_profiles_dashboard.json",
    ], core)

'''
    if marker not in text:
        raise SystemExit("PATCH_FAIL trader_cockpit marker not found")
    text = text.replace(marker, insert + marker, 1)

if "trader_cockpit_time_profiles_enrich" not in text:
    pattern = re.compile(
        r'(    run_step\("trader_cockpit", \[\n'
        r'        sys\.executable, "pf_trader_cockpit_once\.py",\n'
        r'        "--symbols", symbols,\n'
        r'        "--trade-symbol", "GBPUSD",\n'
        r'        "--output", "output/dashboard_surface/trader_cockpit\.json",\n'
        r'        "--txt", "output/dashboard_surface/trader_cockpit\.txt",\n'
        r'    \], core\)\n)',
        re.MULTILINE,
    )
    repl = r'''\1    run_step("trader_cockpit_time_profiles_enrich", [
        sys.executable, "pf_trader_cockpit_time_profiles_enrich.py",
        "--cockpit-json", "output/dashboard_surface/trader_cockpit.json",
        "--cockpit-txt", "output/dashboard_surface/trader_cockpit.txt",
        "--time-profiles", "output/dashboard_surface/time_profiles_dashboard.json",
    ], core)
'''
    text, count = pattern.subn(repl, text, count=1)
    if count != 1:
        raise SystemExit("PATCH_FAIL trader_cockpit block not patched")

text = text.replace(
    "topdown_reader,live_brief,b6,multiread,trader_cockpit,daily_journal",
    "topdown_reader,time_profiles,live_brief,b6,multiread,trader_cockpit,daily_journal",
)

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | scheduler time profiles integrated | backup={backup}")
