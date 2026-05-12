from pathlib import Path
from datetime import datetime
import re

path = Path("run_cross_symbol_validation_once.py")
text = path.read_text(encoding="utf-8")

backup = Path(f"run_cross_symbol_validation_once.py.bak_future_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
backup.write_text(text, encoding="utf-8")

# Remove every misplaced future import.
text = re.sub(r'^\s*from __future__ import annotations\s*\n+', '', text, flags=re.MULTILINE)

# Remove previous compat block if present.
text = re.sub(
    r'\n?# PF_SYMBOLS_COMPAT_V737D.*?# END_PF_SYMBOLS_COMPAT_V737D\s*\n+',
    '\n',
    text,
    flags=re.DOTALL,
)

compat = '''
# PF_SYMBOLS_COMPAT_V737D
# Backward compatibility: scheduler_powerflow.py still passes --symbols.
# B8 runner currently works without this argument, so we strip it before argparse.
import sys as _pf_sys

def _pf_strip_legacy_symbols_arg(argv):
    out = []
    skip_next = False
    for item in argv:
        if skip_next:
            skip_next = False
            continue
        if item == "--symbols":
            skip_next = True
            continue
        if item.startswith("--symbols="):
            continue
        out.append(item)
    return out

_pf_sys.argv = _pf_strip_legacy_symbols_arg(_pf_sys.argv)
# END_PF_SYMBOLS_COMPAT_V737D

'''

# Keep future import first.
text = "from __future__ import annotations\n\n" + compat + text.lstrip()

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | future import restored to top | backup={backup}")
