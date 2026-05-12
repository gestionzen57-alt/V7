from pathlib import Path
from datetime import datetime

p = Path("pf_time_profile_window.py")
text = p.read_text(encoding="utf-8-sig")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = Path(f"pf_time_profile_window.py.bak_glued_lines_v737e_{stamp}")
backup.write_text(text, encoding="utf-8")

replacements = {
    "broker_offset_hours = getattr(args, 'broker_offset_hours', 1.0)db = Path(args.db)":
        "broker_offset_hours = getattr(args, 'broker_offset_hours', 1.0)\n    db = Path(args.db)",

    'broker_offset_hours = getattr(args, "broker_offset_hours", 1.0)db = Path(args.db)':
        'broker_offset_hours = getattr(args, "broker_offset_hours", 1.0)\n    db = Path(args.db)',

    ")db = Path(args.db)":
        ")\n    db = Path(args.db)",

    ")symbol = args.symbol":
        ")\n    symbol = args.symbol",

    ")profile = args.profile":
        ")\n    profile = args.profile",

    ")output = Path(args.output)":
        ")\n    output = Path(args.output)",
}

changed = 0
for old, new in replacements.items():
    if old in text:
        text = text.replace(old, new)
        changed += 1

text = text.replace("\ufeff", "")

p.write_text(text, encoding="utf-8")
print(f"PATCH_OK | glued lines fixed={changed} | backup={backup}")
