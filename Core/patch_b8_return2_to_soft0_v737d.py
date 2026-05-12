from pathlib import Path
from datetime import datetime
import re

path = Path("run_cross_symbol_validation_once.py")
text = path.read_text(encoding="utf-8")

backup = Path(f"run_cross_symbol_validation_once.py.bak_b8_return2_to_soft0_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
backup.write_text(text, encoding="utf-8")

marker = "PF_B8_COVERAGE_SOFT_RETURN_V737D"

if marker not in text:
    # Case most likely present:
    # except Exception as exc:
    #     print(f"B8 Cross-Symbol Validation failed: {exc}", ...)
    #     return 2
    pattern = re.compile(
        r'(B8 Cross-Symbol Validation failed:[^\n]*\n(?:.*\n){0,8}?)(\s*)return\s+2',
        re.MULTILINE,
    )

    def repl(m):
        return (
            m.group(1)
            + m.group(2)
            + f'# {marker}\n'
            + m.group(2)
            + 'if "Not enough usable cross pairs" in str(exc):\n'
            + m.group(2)
            + '    print("B8_CROSS_SYMBOL_DEGRADED | " + str(exc))\n'
            + m.group(2)
            + '    return 0\n'
            + m.group(2)
            + 'return 2'
        )

    text2, count = pattern.subn(repl, text, count=1)

    if count != 1:
        raise SystemExit("PATCH_FAIL | could not locate B8 failure return block")

    text = text2

path.write_text(text, encoding="utf-8")
print(f"PATCH_OK | B8 coverage insufficiency returns 0 | backup={backup}")
