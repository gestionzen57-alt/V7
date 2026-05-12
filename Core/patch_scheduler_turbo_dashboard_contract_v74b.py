from pathlib import Path

path = Path("scheduler_powerflow_turbo_wrapper.py")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_dashboard_contract_v74b")
backup.write_text(text, encoding="utf-8")

needle = '''    run_step("trader_journal_j1", [
        sys.executable, "pf_trader_journal_j1.py",
'''

insert = '''    run_step("dashboard_v74_contract_check", [
        sys.executable, "dashboard_v74_contract_check.py",
        "--html", "dashboard_powerflow_v74.html",
    ], core, required=False)

'''

if needle not in text:
    raise SystemExit("PATCH_FAIL | trader_journal insertion point not found")

text = text.replace(needle, insert + needle, 1)

old = '''layers=data_health,ontology,signal_adaptive,price_schema,topdown_reader,time_profiles,live_brief,b6,multiread,trader_cockpit,b8,phase_synthesis,evidence_bus,daily_journal'''
new = '''layers=data_health,ontology,signal_adaptive,price_schema,topdown_reader,time_profiles,live_brief,b6,multiread,trader_cockpit,b8,phase_synthesis,evidence_bus,evidence_reading,dashboard_contract,daily_journal'''

if old in text:
    text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | dashboard contract check integrated soft | backup={backup.name}")
