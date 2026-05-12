from pathlib import Path
from datetime import datetime
import re

p = Path("pf_time_profile_window.py")
text = p.read_text(encoding="utf-8-sig")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = Path(f"pf_time_profile_window.py.bak_write_json_signature_force_v737e_{stamp}")
backup.write_text(text, encoding="utf-8")

# Remplace uniquement la ligne de signature write_json, quelle que soit sa forme actuelle.
pattern = r"^def write_json\(.*?\)\s*(?:->\s*[^:]+)?\s*:"
replacement = "def write_json(path: Path, data: dict, pretty: bool = False, broker_offset_hours: float = 1.0) -> None:"

text2, n = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)

if n != 1:
    raise SystemExit(f"PATCH_FAIL | write_json signature not found | replacements={n}")

# Sécurité : aucune BOM
text2 = text2.replace("\ufeff", "")

p.write_text(text2, encoding="utf-8")

print(f"PATCH_OK | write_json signature forced | replacements={n} | backup={backup}")
