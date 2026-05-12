from pathlib import Path
from datetime import datetime

TARGET = Path("pf_gbpusd_live_decision_once.py")

if not TARGET.exists():
    raise SystemExit("PATCH_FAIL | pf_gbpusd_live_decision_once.py missing")

text = TARGET.read_text(encoding="utf-8", errors="replace")

backup = TARGET.with_suffix(".py.bak_unicode_console_" + datetime.utcnow().strftime("%Y%m%d_%H%M%S"))
backup.write_text(text, encoding="utf-8")

if "def safe_console_text(" not in text:
    insert = '''
def safe_console_text(value):
    """
    Console-safe text for Windows cp1252 terminals.
    Keeps engine/output JSON untouched. Only protects print().
    """
    try:
        return str(value).encode("cp1252", errors="replace").decode("cp1252")
    except Exception:
        return str(value).encode("ascii", errors="replace").decode("ascii")

'''
    # Insère après les imports
    lines = text.splitlines(True)
    pos = 0
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            pos = i + 1
    lines.insert(pos, insert)
    text = "".join(lines)

# Patch print("-", str(n).replace(...))
text = text.replace(
    'print("-", str(n).replace("\\n", " | "))',
    'print("-", safe_console_text(str(n).replace("\\n", " | ")))'
)

# Patch défensif pour autres prints directs de notes/messages si présents
text = text.replace(
    'print("-", n)',
    'print("-", safe_console_text(n))'
)

TARGET.write_text(text, encoding="utf-8")

print(f"PATCH_OK | unicode console guarded | backup={backup}")
