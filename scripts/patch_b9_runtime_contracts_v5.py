# -*- coding: utf-8 -*-
"""B9 runtime contract compatibility patch V5.

Adds read-only compatibility facades for GPT-2 contract modules used by
pf_engine_b9. The patch is append-only and creates timestamped backups.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

ROOT = Path.cwd()
STAMP = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
MARK = "# B9_RUNTIME_CONTRACT_COMPAT_V5"


def backup(path: Path) -> Path:
    dest = path.with_name(f"{path.name}.b9contracts_v5_{STAMP}.bak")
    dest.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return dest


def append_once(path: Path, marker: str, block: str) -> None:
    if not path.exists():
        path.write_text("# -*- coding: utf-8 -*-\n", encoding="utf-8")
    text = path.read_text(encoding="utf-8")
    if marker in text:
        print(f"[B9 CONTRACT PATCH V5] Already present in {path.name}")
        return
    bak = backup(path)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text + "\n" + block.strip() + "\n", encoding="utf-8")
    print(f"[B9 CONTRACT PATCH V5] Patched {path.name}; backup {bak.name}")


TERRAIN_NODE_BLOCK = r'''
# B9_RUNTIME_CONTRACT_COMPAT_V5 terrain node facade
try:
    _B9_V5_ORIGINAL_CREATE_TERRAIN_NODE_SNAPSHOT = create_terrain_node_snapshot
except NameError:  # pragma: no cover
    _B9_V5_ORIGINAL_CREATE_TERRAIN_NODE_SNAPSHOT = None


def _b9_v5_public_packet(value):
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    if isinstance(value, dict):
        return dict(value)
    return value


def create_terrain_node_snapshot(*args, **kwargs):
    """Compatibility facade for pf_engine_b9 terrain node creation.

    Accepts window-style keyword payloads such as zone_low/zone_high and returns
    a read-only packet if the original implementation cannot accept them.
    """
    original = _B9_V5_ORIGINAL_CREATE_TERRAIN_NODE_SNAPSHOT
    if original is not None:
        try:
            return original(*args, **kwargs)
        except TypeError as exc:
            if "unexpected keyword" not in str(exc):
                raise
            try:
                import inspect
                sig = inspect.signature(original)
                allowed = {
                    name: value
                    for name, value in kwargs.items()
                    if name in sig.parameters
                }
                return original(*args, **allowed)
            except Exception:
                pass

    symbol = kwargs.get("symbol") or (args[0] if args else "GBPUSD")
    zone_low = kwargs.get("zone_low")
    zone_high = kwargs.get("zone_high")
    current_price = kwargs.get("current_price")
    visibility = kwargs.get("data_visibility") or kwargs.get("visibility") or "TACTICAL_OK"
    price_verdict = kwargs.get("price_verdict_candidate") or kwargs.get("price_verdict") or "PENDING"
    node_id = kwargs.get("node_id") or f"B9NODE_{symbol}_COMPAT"
    return {
        "node_id": node_id,
        "symbol": symbol,
        "zone_bounds": {"low": zone_low, "high": zone_high},
        "zone_low": zone_low,
        "zone_high": zone_high,
        "current_price": current_price,
        "price_verdict_candidate": price_verdict,
        "data_visibility": visibility,
        "source_profile": kwargs.get("source_profile") or {
            "source_mode": "B9_RUNTIME_COMPAT",
            "data_visibility": visibility,
            "confidence_cap": 0.35,
        },
        "limits": ["runtime contract compatibility facade"],
        "raw": {k: _b9_v5_public_packet(v) for k, v in kwargs.items()},
    }
'''

PACKET_REQUALIFIER_BLOCK = r'''
# B9_RUNTIME_CONTRACT_COMPAT_V5 packet requalification facade
try:
    _B9_V5_ORIGINAL_REQUALIFY_PACKET = requalify_packet
except NameError:  # pragma: no cover
    _B9_V5_ORIGINAL_REQUALIFY_PACKET = None


def requalify_packet(*args, **kwargs):
    """Read-only compatibility facade for B9 packet requalification."""
    original = _B9_V5_ORIGINAL_REQUALIFY_PACKET
    if original is not None:
        try:
            return original(*args, **kwargs)
        except TypeError:
            pass
    packet = kwargs.get("packet") or kwargs.get("terrain_node") or (args[0] if args else {})
    if hasattr(packet, "__dict__"):
        packet = dict(packet.__dict__)
    if not isinstance(packet, dict):
        packet = {"value": str(packet)}
    result = dict(packet)
    result.setdefault("qualified_bias", "PERCEPTION_PENDING")
    result.setdefault("packet_quality", "TACTICAL_OK")
    result.setdefault("data_visibility", result.get("data_visibility", "TACTICAL_OK"))
    result.setdefault("limits", ["runtime requalification compatibility facade"])
    return result


def requalify_terrain_packet(*args, **kwargs):
    return requalify_packet(*args, **kwargs)
'''

B6_MEMORY_BLOCK = r'''
# B9_RUNTIME_CONTRACT_COMPAT_V5 B6 memory facade
try:
    _B9_V5_ORIGINAL_READ_B6_FIELD_MEMORY = read_b6_field_memory
except NameError:  # pragma: no cover
    _B9_V5_ORIGINAL_READ_B6_FIELD_MEMORY = None


def read_b6_field_memory(*args, **kwargs):
    """Read-only compatibility facade for B6 memory context."""
    original = _B9_V5_ORIGINAL_READ_B6_FIELD_MEMORY
    if original is not None:
        try:
            return original(*args, **kwargs)
        except TypeError:
            pass
    return {
        "status": "MEMORY_COMPAT_CONTEXT",
        "film_pattern": "UNKNOWN",
        "similarity": None,
        "usual_next_scene": None,
        "false_positive_risk": ["memory facade fallback"],
        "limits": ["B6 memory reader compatibility facade"],
    }


def get_b6_field_memory(*args, **kwargs):
    return read_b6_field_memory(*args, **kwargs)
'''

TELEGRAM_BLOCK = r'''
# B9_RUNTIME_CONTRACT_COMPAT_V5 telegram facade
try:
    _B9_V5_ORIGINAL_SEND_B9_ALERT = send_b9_alert
except NameError:  # pragma: no cover
    _B9_V5_ORIGINAL_SEND_B9_ALERT = None


def send_b9_alert(*args, **kwargs):
    """Dry-run default compatibility facade for B9 alert transmission."""
    original = _B9_V5_ORIGINAL_SEND_B9_ALERT
    enable = bool(kwargs.get("enable") or kwargs.get("ENABLE_TELEGRAM") or kwargs.get("send", False))
    if original is not None and enable:
        return original(*args, **kwargs)
    return {
        "status": "DRY_RUN",
        "alert_sent": False,
        "channel": "telegram_disabled",
        "limits": ["telegram compatibility facade dry-run"],
    }


def send_telegram_alert_b9(*args, **kwargs):
    return send_b9_alert(*args, **kwargs)
'''


def main() -> int:
    append_once(ROOT / "pf_terrain_node_snapshot.py", "B9_RUNTIME_CONTRACT_COMPAT_V5 terrain node facade", TERRAIN_NODE_BLOCK)
    append_once(ROOT / "pf_packet_requalifier_v767.py", "B9_RUNTIME_CONTRACT_COMPAT_V5 packet requalification facade", PACKET_REQUALIFIER_BLOCK)
    append_once(ROOT / "pf_b6_field_memory_reader.py", "B9_RUNTIME_CONTRACT_COMPAT_V5 B6 memory facade", B6_MEMORY_BLOCK)
    append_once(ROOT / "telegram_alert_sender_b9.py", "B9_RUNTIME_CONTRACT_COMPAT_V5 telegram facade", TELEGRAM_BLOCK)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
