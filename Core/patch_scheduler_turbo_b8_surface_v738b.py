from pathlib import Path

path = Path("scheduler_powerflow_turbo_wrapper.py")
text = path.read_text(encoding="utf-8")

backup = path.with_suffix(path.suffix + ".bak_b8_surface_v738b")
backup.write_text(text, encoding="utf-8")

needle = '''    run_step("trader_cockpit_time_profiles_enrich", [
        sys.executable, "pf_trader_cockpit_time_profiles_enrich.py",
        "--cockpit-json", "output/dashboard_surface/trader_cockpit.json",
        "--cockpit-txt", "output/dashboard_surface/trader_cockpit.txt",
        "--time-profiles", "output/dashboard_surface/time_profiles_dashboard.json",
    ], core)
'''

insert = needle + '''
    run_step("b8_cross_surface", [
        sys.executable, "pf_b8_cross_surface_once.py",
        "--symbols", symbols,
        "--output", "output/dashboard_surface/b8_cross_surface.json",
        "--txt", "output/dashboard_surface/b8_cross_surface.txt",
    ], core)

    run_step("trader_cockpit_b8_enrich", [
        sys.executable, "pf_trader_cockpit_b8_enrich.py",
        "--cockpit-json", "output/dashboard_surface/trader_cockpit.json",
        "--cockpit-txt", "output/dashboard_surface/trader_cockpit.txt",
        "--b8", "output/dashboard_surface/b8_cross_surface.json",
    ], core)
'''

if needle not in text:
    raise SystemExit("PATCH_FAIL | trader_cockpit_time_profiles_enrich block not found")

text = text.replace(needle, insert, 1)

old_layers = "time_profiles,live_brief,b6,multiread,trader_cockpit,daily_journal"
new_layers = "time_profiles,live_brief,b6,multiread,trader_cockpit,b8,daily_journal"
text = text.replace(old_layers, new_layers)

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | B8 surface integrated into turbo | backup={backup.name}")
