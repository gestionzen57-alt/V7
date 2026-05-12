from pathlib import Path

path = Path("scheduler_powerflow_turbo_wrapper.py")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_evidence_reading_v739f")
backup.write_text(text, encoding="utf-8")

if "pf_evidence_reading_once.py" in text:
    print("SKIP | evidence reading already integrated")
    raise SystemExit(0)

anchor = '''    run_step("evidence_bus", [
        sys.executable, "pf_evidence_bus_once.py",
        "--symbol", "GBPUSD",
        "--output", "output/dashboard_surface/evidence_bus.json",
        "--txt", "output/dashboard_surface/evidence_bus.txt",
    ], core)

'''

insert = '''    run_step("evidence_reading", [
        sys.executable, "pf_evidence_reading_once.py",
        "--evidence-bus", "output/dashboard_surface/evidence_bus.json",
        "--output", "output/dashboard_surface/evidence_reading.json",
        "--txt", "output/dashboard_surface/evidence_reading.txt",
    ], core)

    run_step("trader_cockpit_evidence_enrich", [
        sys.executable, "pf_trader_cockpit_evidence_enrich.py",
        "--cockpit-json", "output/dashboard_surface/trader_cockpit.json",
        "--cockpit-txt", "output/dashboard_surface/trader_cockpit.txt",
        "--evidence-reading", "output/dashboard_surface/evidence_reading.json",
        "--evidence-bus", "output/dashboard_surface/evidence_bus.json",
    ], core)

'''

if anchor not in text:
    raise SystemExit("PATCH_FAIL | evidence_bus anchor not found")

text = text.replace(anchor, anchor + insert, 1)
text = text.replace(
    "phase_synthesis,evidence_bus,daily_journal",
    "phase_synthesis,evidence_bus,evidence_reading,daily_journal",
)

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | evidence reading integrated | backup={backup.name}")
