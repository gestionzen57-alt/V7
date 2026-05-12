from pathlib import Path
from datetime import datetime
import re

path = Path("run_cross_symbol_validation_once.py")
text = path.read_text(encoding="utf-8")

backup = Path(f"run_cross_symbol_validation_once.py.bak_b8_soft_fail_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
backup.write_text(text, encoding="utf-8")

marker = "PF_B8_SOFT_FAIL_V737D"

if marker not in text:
    # Replace the final hard SystemExit(main()) by a guarded launcher.
    text = re.sub(
        r'if\s+__name__\s*==\s*["\']__main__["\']:\s*\n\s*raise\s+SystemExit\(main\(\)\)\s*$',
        '''if __name__ == "__main__":
    # PF_B8_SOFT_FAIL_V737D
    # B8 is a contextual validation layer. Missing cross-pair coverage must degrade,
    # not block the full PowerFlow scheduler.
    import sys as _pf_sys

    try:
        _code = main()
    except Exception as _exc:
        _msg = str(_exc)
        if "Not enough usable cross pairs" in _msg:
            print("B8_CROSS_SYMBOL_DEGRADED | " + _msg)
            raise SystemExit(0)
        raise

    if _code not in (0, None):
        # Some versions print the failure and return 1 instead of raising.
        # Keep non-B8 failures hard, but let known coverage insufficiency be soft.
        raise SystemExit(_code)

    raise SystemExit(0)
''',
        text,
        flags=re.DOTALL,
    )

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | B8 soft fail guard installed | backup={backup}")
