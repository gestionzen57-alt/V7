from __future__ import annotations

import importlib.util
from pathlib import Path

root = Path(__file__).resolve().parents[1]
mod_path = root / "patch" / "pf_telegram_short_live_v766.py"
spec = importlib.util.spec_from_file_location("pf_telegram_short_live_v766", mod_path)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

packet = {
    "symbol": "GBPUSD",
    "film_state": "HIGH_ZONE_REJECTION",
    "qualified_bias": "HIGH_ZONE_EXHAUSTION_RISK",
    "data_visibility": "READING_PARTIAL",
}
memory = {"memory_match": "LATE_HIGH_REJECTION_WITH_DEEP_UNWIND", "day": "2026-05-07"}
playbook = {"playbook_label_fr": "Risque d\u2019\u00e9puisement en zone haute"}
msg = mod.build_short_message(packet, memory, playbook)
assert "GBPUSD" in msg
assert "Risque d\u2019\u00e9puisement" in msg
assert "07 mai" in msg
assert "pas ordre automatique" in msg
assert "BUY" not in msg and "SELL" not in msg and "ENTRY" not in msg
print("OK test_v766_polish_static")
