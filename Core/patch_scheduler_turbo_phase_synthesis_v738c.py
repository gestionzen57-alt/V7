from pathlib import Path

path = Path("scheduler_powerflow_turbo_wrapper.py")
text = path.read_text(encoding="utf-8")

backup = path.with_suffix(path.suffix + ".bak_phase_synthesis_v738c")
backup.write_text(text, encoding="utf-8")

needle = '''    run_step("trader_cockpit_b8_enrich", [
        sys.executable, "pf_trader_cockpit_b8_enrich.py",
        "--cockpit-json", "output/dashboard_surface/trader_cockpit.json",
        "--cockpit-txt", "output/dashboard_surface/trader_cockpit.txt",
        "--b8", "output/dashboard_surface/b8_cross_surface.json",
    ], core)
'''

insert = needle + '''
    run_step("phase_synthesis", [
        sys.executable, "pf_phase_synthesizer_once.py",
        "--symbol", "GBPUSD",
        "--time-profiles", "output/dashboard_surface/time_profiles_dashboard.json",
        "--cockpit", "output/dashboard_surface/trader_cockpit.json",
        "--b8", "output/dashboard_surface/b8_cross_surface.json",
        "--output", "output/dashboard_surface/phase_synthesis.json",
        "--txt", "output/dashboard_surface/phase_synthesis.txt",
    ], core)

    run_step("trader_cockpit_phase_enrich", [
        sys.executable, "pf_trader_cockpit_phase_enrich.py",
        "--cockpit-json", "output/dashboard_surface/trader_cockpit.json",
        "--cockpit-txt", "output/dashboard_surface/trader_cockpit.txt",
        "--phase", "output/dashboard_surface/phase_synthesis.json",
    ], core)
'''

if needle not in text:
    raise SystemExit("PATCH_FAIL | trader_cockpit_b8_enrich block not found")

text = text.replace(needle, insert, 1)

old_layers = "time_profiles,live_brief,b6,multiread,trader_cockpit,b8,daily_journal"
new_layers = "time_profiles,live_brief,b6,multiread,trader_cockpit,b8,phase_synthesis,daily_journal"
text = text.replace(old_layers, new_layers)

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | phase synthesis integrated into turbo | backup={backup.name}")
