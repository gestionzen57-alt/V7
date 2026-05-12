from pathlib import Path
from datetime import datetime
import re

p = Path("pf_time_profile_window.py")
text = p.read_text(encoding="utf-8-sig")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = Path(f"pf_time_profile_window.py.bak_write_json_scope_v737e_{stamp}")
backup.write_text(text, encoding="utf-8")

# 1) Durcir la signature write_json
text, n1 = re.subn(
    r"def write_json\(([^)]*?)pretty\s*=\s*False\):",
    r"def write_json(\1pretty=False, broker_offset_hours=1.0):",
    text,
    count=1
)

# Variante si espaces/type hints différents
if n1 == 0:
    text, n1 = re.subn(
        r"def write_json\(([^)]*)\):",
        lambda m: (
            m.group(0)[:-2] + ", broker_offset_hours=1.0):"
            if "broker_offset_hours" not in m.group(1)
            else m.group(0)
        ),
        text,
        count=1
    )

# 2) S'assurer que l'appel dans main transmet la valeur
text, n2 = re.subn(
    r"write_json\(out,\s*profile,\s*pretty=args\.pretty\)",
    r"write_json(out, profile, pretty=args.pretty, broker_offset_hours=broker_offset_hours)",
    text,
    count=1
)

# 3) Filet de sécurité : si write_json utilise encore une variable non locale,
# elle sera maintenant fournie par paramètre.
p.write_text(text.replace("\ufeff", ""), encoding="utf-8")

print(f"PATCH_OK | write_json_scope fixed signature={n1} call={n2} | backup={backup}")
