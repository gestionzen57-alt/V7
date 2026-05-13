from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OUT = Path("output/dashboard_surface")
MEMORY = OUT / "eie_telegram_memory.json"

LEVEL_RANK = {
    "INFO": 0,
    "WATCH": 1,
    "ACTIVE": 2,
    "HOT": 3,
}

CRITICAL_SYNTHESES = {
    "TRAP_CONTEXT_ELASTIC_PRESSURE_ALIGNED",
    "ELASTIC_LOADING_WITH_B6_ALIGNMENT",
    "ELASTIC_PRESSURE_IN_REACTION_CONTEXT",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        obj = json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def safe_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


def load_memory() -> dict[str, Any]:
    mem = load_json(MEMORY)
    if not mem:
        mem = {
            "method": "EIE_TELEGRAM_MEMORY_V74",
            "families": {},
            "fingerprints": {},
            "events": [],
        }
    mem.setdefault("families", {})
    mem.setdefault("fingerprints", {})
    mem.setdefault("events", [])
    return mem


def packet_family(p: dict[str, Any]) -> str:
    return "|".join(
        [
            str(p.get("symbol") or ""),
            str(p.get("event_family") or ""),
            str(p.get("event_type") or ""),
            str(p.get("synthesis") or ""),
            str(p.get("bias") or ""),
            str(p.get("timeframe") or ""),
        ]
    )


def packet_fingerprint(p: dict[str, Any]) -> str:
    raw = "|".join(
        [
            packet_family(p),
            str(p.get("level") or ""),
            str(p.get("score") or ""),
            str(p.get("state") or ""),
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def should_send(packet: dict[str, Any], min_level: str = "ACTIVE") -> tuple[bool, str]:
    level = str(packet.get("level") or "INFO").upper()
    synthesis = str(packet.get("synthesis") or "").upper()
    score = safe_float(packet.get("score"))

    level_ok = LEVEL_RANK.get(level, 0) >= LEVEL_RANK.get(min_level.upper(), 2)
    synthesis_ok = synthesis in CRITICAL_SYNTHESES and LEVEL_RANK.get(level, 0) >= LEVEL_RANK["WATCH"]

    if not level_ok and not synthesis_ok:
        return False, "LEVEL_BELOW_EIE_TELEGRAM_THRESHOLD"

    mem = load_memory()
    fp = str(packet.get("fingerprint") or packet_fingerprint(packet))
    fam = str(packet.get("family") or packet_family(packet))

    if fp in mem.get("fingerprints", {}):
        return False, "DUPLICATE_EIE_FINGERPRINT_SUPPRESSED"

    previous = mem.get("families", {}).get(fam)
    if not previous:
        return True, "NEW_EIE_FAMILY"

    prev_level = str(previous.get("level") or "INFO").upper()
    prev_score = safe_float(previous.get("score"))

    if LEVEL_RANK.get(level, 0) > LEVEL_RANK.get(prev_level, 0):
        return True, "EIE_LEVEL_ESCALATION"

    if score >= prev_score + 0.8:
        return True, "EIE_SCORE_ACCELERATION"

    return False, "DUPLICATE_EIE_FAMILY_SUPPRESSED"


def mark_seen(packet: dict[str, Any], reason: str) -> None:
    mem = load_memory()

    fp = str(packet.get("fingerprint") or packet_fingerprint(packet))
    fam = str(packet.get("family") or packet_family(packet))

    packet["fingerprint"] = fp
    packet["family"] = fam

    rec = {
        "seen_at": now_utc(),
        "reason": reason,
        **packet,
    }

    mem["families"][fam] = rec
    mem["fingerprints"][fp] = rec
    mem["events"].append(rec)
    mem["events"] = mem["events"][-200:]

    write_json(MEMORY, mem)


def build_message(packet: dict[str, Any]) -> str:
    evidence = packet.get("evidence") or []
    contradictions = packet.get("contradictions") or []
    risks = packet.get("technical_risks") or []

    lines = [
        f"⚡ POWERFLOW EIE {packet.get('symbol')}",
        f"{packet.get('level')} | {packet.get('synthesis')}",
        f"Bias: {packet.get('bias')} | TF={packet.get('timeframe')} | score={packet.get('score')}",
        f"State: {packet.get('state')} | Event: {packet.get('event_type')}",
        "",
        "Evidence:",
        ", ".join(evidence) if evidence else "NONE",
    ]

    if contradictions:
        lines += ["", "Contradictions:", ", ".join(contradictions)]

    if risks:
        lines += ["", "Risks:", ", ".join(risks)]

    return "\n".join(lines)


def send_telegram(text: str) -> str:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    if not token or not chat_id:
        return "TELEGRAM_ENV_MISSING"

    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        with urllib.request.urlopen(url, data=data, timeout=12) as resp:
            body = resp.read().decode("utf-8", errors="replace")
        obj = json.loads(body)
        return "TELEGRAM_SEND_OK" if obj.get("ok") else "TELEGRAM_SEND_FAIL"
    except Exception as exc:
        return f"TELEGRAM_SEND_ERROR:{type(exc).__name__}"


def write_txt(path: Path, decision: dict[str, Any]) -> None:
    p = decision.get("packet", {})
    lines = [
        f"{p.get('symbol')} | EIE TELEGRAM V7.4 | send={decision.get('send')} | {decision.get('reason')}",
        f"telegram={decision.get('telegram_status')}",
        f"level={p.get('level')} synthesis={p.get('synthesis')}",
        f"state={p.get('state')} bias={p.get('bias')} tf={p.get('timeframe')} score={p.get('score')}",
        f"event={p.get('event_type')} family={p.get('event_family')}",
        f"fingerprint={p.get('fingerprint')}",
        f"memory={decision.get('memory_path')}",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="GBPUSD")
    ap.add_argument("--send", action="store_true")
    ap.add_argument("--mark-dry-run", action="store_true")
    ap.add_argument("--min-level", default="ACTIVE")
    args = ap.parse_args()

    symbol = args.symbol.upper()
    src = load_json(OUT / symbol / "eie_gravity.json")

    packet = {
        "symbol": symbol,
        "state": src.get("state"),
        "level": src.get("level"),
        "bias": src.get("bias"),
        "score": src.get("score"),
        "confidence": src.get("confidence"),
        "timeframe": src.get("timeframe"),
        "event_family": src.get("event_family"),
        "event_type": src.get("event_type"),
        "synthesis": src.get("synthesis"),
        "evidence": src.get("evidence", []),
        "contradictions": src.get("contradictions", []),
        "technical_risks": src.get("technical_risks", []),
    }

    packet["family"] = packet_family(packet)
    packet["fingerprint"] = packet_fingerprint(packet)

    send, reason = should_send(packet, min_level=args.min_level)

    telegram_status = "DRY_RUN"

    if send and args.send:
        telegram_status = send_telegram(build_message(packet))
        if telegram_status == "TELEGRAM_SEND_OK":
            mark_seen(packet, reason)

    elif send and args.mark_dry_run:
        telegram_status = "WOULD_SEND_DRY_RUN_MARKED"
        mark_seen(packet, reason)

    elif send:
        telegram_status = "WOULD_SEND_DRY_RUN"

    decision = {
        "timestamp_utc": now_utc(),
        "method": "EIE_TELEGRAM_GATE_V74",
        "send": send,
        "reason": reason,
        "telegram_status": telegram_status,
        "memory_path": str(MEMORY),
        "packet": packet,
        "message_preview": build_message(packet),
    }

    out = OUT / symbol
    write_json(out / "eie_telegram_decision.json", decision)
    write_txt(out / "eie_telegram_decision.txt", decision)

    print("EIE_TELEGRAM_GATE_DONE")
    print("send=", send)
    print("reason=", reason)
    print("telegram=", telegram_status)
    print("json=", out / "eie_telegram_decision.json")
    print("txt =", out / "eie_telegram_decision.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
