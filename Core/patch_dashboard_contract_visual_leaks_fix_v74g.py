from pathlib import Path

path = Path("dashboard_v74_contract_check.py")
text = path.read_text(encoding="utf-8")
backup = path.with_suffix(path.suffix + ".bak_visual_leaks_fix_v74g")
backup.write_text(text, encoding="utf-8")

if "def scan_visual_leaks(" not in text:
    marker = "def check_dashboard_html(path: Path, issues: list[str]) -> None:"
    if marker not in text:
        raise SystemExit("PATCH_FAIL | check_dashboard_html marker not found")

    fn = '''
def scan_visual_leaks(label: str, data: Any, issues: list[str]) -> None:
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
    text = text.replace(marker, fn + marker, 1)

call = '''    for name, obj in data.items():
        if obj:
            scan_visual_leaks(name, obj, issues)

'''

if "scan_visual_leaks(name, obj, issues)" not in text:
    marker = "    result = {"
    if marker not in text:
        raise SystemExit("PATCH_FAIL | result marker not found")
    text = text.replace(marker, call + marker, 1)

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | visual leak scan active | backup={backup.name}")
