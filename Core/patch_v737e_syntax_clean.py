from pathlib import Path
from datetime import datetime
import re

FILES = [
    "pf_time_profile_window.py",
    "run_ltf_profile_once.py",
    "run_mtf_profile_once.py",
    "run_htf_profile_once.py",
    "dashboard_normalize_time_profiles.py",
]

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

for name in FILES:
    p = Path(name)
    if not p.exists():
        print(f"SKIP missing {name}")
        continue

    raw = p.read_text(encoding="utf-8-sig")

    backup = Path(f"{name}.bak_syntax_clean_v737e_{stamp}")
    backup.write_text(raw, encoding="utf-8")

    # Remove invisible BOM anywhere, not only first char.
    raw = raw.replace("\ufeff", "")

    # Fix broker arg accidentally glued to next parser.add_argument.
    raw = raw.replace(
        "help='Broker clock offset vs local reference. Broker H+1 => 1.')parser.add_argument",
        "help='Broker clock offset vs local reference. Broker H+1 => 1.')\n    parser.add_argument",
    )

    raw = raw.replace(
        'default=1.0)parser.add_argument',
        'default=1.0)\n    parser.add_argument',
    )

    # General safety: if two parser.add_argument are glued.
    raw = raw.replace(
        ')parser.add_argument(',
        ')\n    parser.add_argument(',
    )

    p.write_text(raw, encoding="utf-8")
    print(f"CLEAN_OK | {name} | backup={backup}")

print("PATCH_DONE | syntax clean V7.3.7e")
