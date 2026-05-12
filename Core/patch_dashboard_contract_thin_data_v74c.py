from pathlib import Path

path = Path("dashboard_v74_contract_check.py")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_thin_data_v74c")
backup.write_text(text, encoding="utf-8")

old = '''            add_if_bad(issues, f"time_profiles.{name}.{tf}.phase", row.get("phase"))
            add_if_bad(issues, f"time_profiles.{name}.{tf}.bias", row.get("bias"))
            add_if_bad(issues, f"time_profiles.{name}.{tf}.important_event", row.get("important_event"))

            # D1 can be thin; it must say so explicitly.
            if upper(tf) == "D1" and upper(row.get("phase")) == "THIN_DATA":
                risks = row.get("technical_risks") or []
                if "D1_THIN_ROWS" not in risks:
                    issues.append("D1_THIN_DATA_WITHOUT_RISK:D1_THIN_ROWS")
'''

new = '''            phase = upper(row.get("phase"))
            bias = upper(row.get("bias"))
            risks = row.get("technical_risks") or []

            add_if_bad(issues, f"time_profiles.{name}.{tf}.phase", row.get("phase"))
            add_if_bad(issues, f"time_profiles.{name}.{tf}.important_event", row.get("important_event"))

            # Thin higher-timeframe data is an explicit data-health state, not a silent dashboard failure.
            # D1 can legitimately have UNKNOWN bias when phase=THIN_DATA and D1_THIN_ROWS is present.
            if upper(tf) == "D1" and phase == "THIN_DATA":
                if "D1_THIN_ROWS" not in risks:
                    issues.append("D1_THIN_DATA_WITHOUT_RISK:D1_THIN_ROWS")
            else:
                add_if_bad(issues, f"time_profiles.{name}.{tf}.bias", row.get("bias"))
'''

if old not in text:
    raise SystemExit("PATCH_FAIL | target block not found")

text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | V7.4c thin-data allowance | backup={backup.name}")
