from pathlib import Path

path = Path("scheduler_powerflow_turbo_wrapper.py")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_evidence_bus_v739")
backup.write_text(text, encoding="utf-8")

if "pf_evidence_bus_once.py" in text:
    print("SKIP | evidence bus already integrated")
    raise SystemExit(0)

anchor = '''    run_step("trader_journal_j1", [
        sys.executable, "pf_trader_journal_j1.py",
        "--symbols", symbols,
        "--output", "output/dashboard_surface/trader_journal_j1.json",
        "--md", "output/dashboard_surface/trader_journal_j1.md",
    ], core)
'''

insert = '''    run_step("evidence_bus", [
        sys.executable, "pf_evidence_bus_once.py",
        "--symbol", "GBPUSD",
        "--output", "output/dashboard_surface/evidence_bus.json",
        "--txt", "output/dashboard_surface/evidence_bus.txt",
    ], core)

'''

if anchor not in text:
    raise SystemExit("PATCH_FAIL | trader_journal_j1 anchor not found")

text = text.replace(anchor, insert + anchor, 1)
text = text.replace(
    "layers=data_health,ontology,signal_adaptive,price_schema,topdown_reader,time_profiles,live_brief,b6,multiread,trader_cockpit,b8,phase_synthesis,daily_journal",
    "layers=data_health,ontology,signal_adaptive,price_schema,topdown_reader,time_profiles,live_brief,b6,multiread,trader_cockpit,b8,phase_synthesis,evidence_bus,daily_journal",
)

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | evidence bus integrated | backup={backup.name}")
