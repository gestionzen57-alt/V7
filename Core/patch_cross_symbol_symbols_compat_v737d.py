from pathlib import Path
from datetime import datetime
import re

path = Path("run_cross_symbol_validation_once.py")
text = path.read_text(encoding="utf-8")

backup = Path(f"run_cross_symbol_validation_once.py.bak_symbols_compat_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
backup.write_text(text, encoding="utf-8")

marker = "PF_SYMBOLS_COMPAT_V737D"

block = f'''
# {marker}
# Backward compatibility: scheduler_powerflow.py still passes --symbols.
# B8 runner currently works without this argument, so we strip it before argparse.
import sys as _pf_sys

def _pf_strip_legacy_symbols_arg(argv):
    out = []
    skip_next = False
    for i, item in enumerate(argv):
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
# END_{marker}

'''

if marker not in text:
    m = re.match(r'((?:from __future__ import .+\n)+)', text)
    if m:
        pos = m.end()
        text = text[:pos] + block + text[pos:]
    else:
        text = block + text

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | --symbols compatibility added | backup={backup}")
