from pathlib import Path

path = Path("dashboard_v74_contract_check.py")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_visual_leaks_v74g")
backup.write_text(text, encoding="utf-8")

needle = '''def check_dashboard_html(path: Path, issues: list[str]) -> None:
    if not path.exists():
        issues.append(f"MISSING_DASHBOARD_HTML:{path.as_posix()}")
        return

    text = path.read_text(encoding="utf-8-sig", errors="replace")
'''

insert = '''def scan_visual_leaks(label: str, data: Any, issues: list[str]) -> None:
    """Detect values that would leak badly into the dashboard."""
    bad_fragments = [
        "[object Object]",
        "undefined",
        "NaN",
        "Aucune phrase Evidence Reading disponible",
    ]

    def walk(prefix: str, v: Any) -> None:
        if isinstance(v, dict):
            for k, val in v.items():
                walk(f"{prefix}.{k}" if prefix else str(k), val)
        elif isinstance(v, list):
            for i, val in enumerate(v):
                walk(f"{prefix}[{i}]", val)
        else:
            s = str(v)
            for frag in bad_fragments:
                if frag in s:
                    issues.append(f"VISUAL_LEAK:{label}:{prefix}:{frag}")

    walk("", data)


'''

if needle not in text:
    raise SystemExit("PATCH_FAIL | check_dashboard_html block not found")

text = text.replace(needle, insert + needle, 1)

old = '''    if data.get("phase_synthesis"):
        check_phase(data["phase_synthesis"], issues)

    result = {
'''

new = '''    if data.get("phase_synthesis"):
        check_phase(data["phase_synthesis"], issues)

    for name, obj in data.items():
        if obj:
            scan_visual_leaks(name, obj, issues)

    result = {
'''

if old not in text:
    raise SystemExit("PATCH_FAIL | scan insertion point not found")

text = text.replace(old, new, 1)

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | V7.4g visual leak scan added | backup={backup.name}")
