from pathlib import Path

path = Path("dashboard_v74_contract_check.py")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_cockpit_utf8_v74e")
backup.write_text(text, encoding="utf-8")

old = '''    required_tokens = [
        "evidence_reading.json",
        "evidence_bus.json",
        "time_profiles_dashboard.json",
        "trader_cockpit.json",
        "dashboard_bias",
        "structural_bias",
        "counterflow_bias",
        "semantic_warning",
    ]
'''

new = '''    required_tokens = [
        "evidence_reading.json",
        "evidence_bus.json",
        "time_profiles_dashboard.json",
        "trader_cockpit.json",
        "dashboard_bias",
        "structural_bias",
        "counterflow_bias",
        "semantic_warning",
        "recursiveFind",
        "repairMojibake",
        "MISSING_FIELD",
    ]
'''

if old not in text:
    raise SystemExit("PATCH_FAIL | required_tokens block not found")

text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | V7.4e contract requires cockpit/utf8 helpers | backup={backup.name}")
