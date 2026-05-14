from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SYMBOL = "GBPUSD"


def read_json(path: str | Path) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"JSON object expected at {path}")
    return data


def write_json(path: str | Path, data: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def load_memory_cards(path: Path) -> Any:
    if not path.exists():
        return {"version": "missing", "symbol": "GBPUSD", "cards": []}
    with path.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        return {"version": "legacy_list_wrapped", "symbol": "GBPUSD", "cards": data}
    return {"version": "invalid", "symbol": "GBPUSD", "cards": []}


def build_packet_from_evidence(evidence: Dict[str, Any], symbol: str = DEFAULT_SYMBOL, memory_cards: Optional[List[Dict[str, Any]]] = None) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    sys.path.insert(0, str(ROOT / "patch"))

    from pf_terrain_context_once import build_terrain_context
    from pf_packet_requalification_once import requalify_packet
    from pf_film_memory_reader_once import match_film_context

    context = build_terrain_context(evidence)
    context["symbol"] = context.get("symbol") or symbol
    if context.get("symbol") == "UNKNOWN":
        context["symbol"] = symbol

    packet = requalify_packet(context)

    memory_cards = memory_cards or []
    memory = match_film_context(packet, memory_cards)
    packet["memory_match"] = memory.get("memory_match", "UNKNOWN")
    packet["memory_confidence"] = memory.get("memory_confidence", 0.0)
    packet["expected_next_behavior"] = memory.get("expected_next_behavior", "UNKNOWN")
    packet["false_positive_risk"] = memory.get("false_positive_risk", "UNKNOWN")

    return context, packet, memory


def write_dashboard_surface(symbol: str, context: Dict[str, Any], packet: Dict[str, Any], memory: Dict[str, Any]) -> Dict[str, str]:
    out_dir = ROOT / "output" / "dashboard_surface" / symbol
    out_dir.mkdir(parents=True, exist_ok=True)

    context_path = out_dir / "terrain_context.json"
    packet_path = out_dir / "terrain_packet.json"
    memory_path = out_dir / "film_memory_match.json"
    fr_path = out_dir / "terrain_packet_fr.txt"

    write_json(context_path, context)
    write_json(packet_path, packet)
    write_json(memory_path, memory)

    # PowerFlow V7.6 trader playbook enrichment
    playbook_path = out_dir / "trader_playbook.json"
    playbook_cmd = [
        sys.executable,
        str(ROOT / "patch" / "pf_trader_playbook_once.py"),
        "--symbol",
        symbol,
        "--input",
        str(packet_path),
        "--labels",
        str(ROOT / "schema" / "playbook_labels_fr_v76.json"),
        "--output",
        str(playbook_path),
        "--packet-output",
        str(packet_path),
    ]
    subprocess.run(playbook_cmd, cwd=str(ROOT), check=True)

    # Reload enriched packet so the result summary and downstream formatter share the same payload.
    try:
        enriched_packet = read_json(packet_path)
        packet.clear()
        packet.update(enriched_packet)
    except Exception:
        pass

    cmd = [
        sys.executable,
        str(ROOT / "patch" / "pf_trader_labels_fr_once.py"),
        "--input",
        str(packet_path),
        "--output",
        str(fr_path),
    ]
    subprocess.run(cmd, cwd=str(ROOT), check=True)

    return {
        "context": str(context_path.relative_to(ROOT)),
        "packet": str(packet_path.relative_to(ROOT)),
        "memory": str(memory_path.relative_to(ROOT)),
        "playbook": str(playbook_path.relative_to(ROOT)),
        "text_fr": str(fr_path.relative_to(ROOT)),
    }


def run_telegram(packet_path: str, text_fr_path: str, mode: str, force: bool = False) -> Dict[str, Any]:
    if mode == "off":
        return {"telegram_mode": "off", "status": "skipped"}

    cmd = [
        sys.executable,
        str(ROOT / "patch" / "pf_telegram_qualified_alert_once.py"),
        "--packet",
        packet_path,
        "--text-fr",
        text_fr_path,
    ]

    if mode == "dry-run":
        cmd.append("--dry-run")
    elif mode == "send":
        cmd.append("--send")
    else:
        raise ValueError(f"unknown telegram mode: {mode}")

    if force:
        cmd.append("--force")

    proc = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True)
    return {
        "telegram_mode": mode,
        "force": force,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "command": " ".join(cmd),
    }


def run_cycle(symbol: str, legacy_source: Path, telegram_mode: str, force_alert: bool) -> Dict[str, Any]:
    evidence = read_json(legacy_source)
    memory_cards = load_memory_cards(ROOT / "data" / "film_memory" / "gbpusd_v76_film_memory_cards.json")
    context, packet, memory = build_packet_from_evidence(evidence, symbol=symbol, memory_cards=memory_cards)
    paths = write_dashboard_surface(symbol, context, packet, memory)

    telegram = run_telegram(paths["packet"], paths["text_fr"], telegram_mode, force=force_alert)

    result = {
        "symbol": symbol,
        "legacy_source": str(legacy_source.relative_to(ROOT)) if legacy_source.is_relative_to(ROOT) else str(legacy_source),
        "film_state": packet.get("film_state", "UNKNOWN"),
        "last_structural_event": packet.get("last_structural_event", "UNKNOWN"),
        "raw_bias": packet.get("raw_bias", "UNKNOWN"),
        "qualified_bias": packet.get("qualified_bias", "UNKNOWN"),
        "packet_quality": packet.get("packet_quality", "UNKNOWN"),
        "price_confirmation": packet.get("price_confirmation", "UNKNOWN"),
        "data_visibility": packet.get("data_visibility", "UNKNOWN"),
        "technical_risks": packet.get("technical_risks", []),
        "paths": paths,
        "telegram": telegram,
    }

    result_path = ROOT / "output" / "dashboard_surface" / symbol / "v76_telegram_cycle_result.json"
    write_json(result_path, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="PowerFlow V7.6.5 cycle tail: legacy evidence -> terrain packet FR -> qualified Telegram alert.")
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL)
    parser.add_argument("--legacy-source", help="Path to legacy_behavioral_state.json")
    parser.add_argument("--telegram-mode", choices=["off", "dry-run", "send"], default="dry-run")
    parser.add_argument("--force-alert", action="store_true")
    args = parser.parse_args()

    symbol = args.symbol.upper()
    legacy_source = Path(args.legacy_source) if args.legacy_source else ROOT / "Core" / "output" / "dashboard_surface" / symbol / "legacy_behavioral_state.json"

    if not legacy_source.exists():
        raise SystemExit(f"Missing legacy source: {legacy_source}")

    result = run_cycle(symbol, legacy_source, args.telegram_mode, args.force_alert)

    print("=== V7.6 TELEGRAM CYCLE RESULT ===")
    print(f"symbol={result['symbol']}")
    print(f"film_state={result['film_state']}")
    print(f"last_structural_event={result['last_structural_event']}")
    print(f"raw_bias={result['raw_bias']}")
    print(f"qualified_bias={result['qualified_bias']}")
    print(f"packet_quality={result['packet_quality']}")
    print(f"price_confirmation={result['price_confirmation']}")
    print(f"data_visibility={result['data_visibility']}")
    print(f"technical_risks={','.join(result['technical_risks']) if result['technical_risks'] else 'NONE'}")
    print(f"terrain_packet={result['paths']['packet']}")
    print(f"terrain_packet_fr={result['paths']['text_fr']}")
    print(f"telegram_mode={result['telegram']['telegram_mode']}")
    print(f"telegram_returncode={result['telegram'].get('returncode', 'NA')}")

    stdout = result["telegram"].get("stdout") or ""
    stderr = result["telegram"].get("stderr") or ""
    if stdout.strip():
        print("")
        print(stdout.strip())
    if stderr.strip():
        print("")
        print("STDERR:")
        print(stderr.strip())

    return 0 if result["telegram"].get("returncode", 0) in (0, None) else int(result["telegram"].get("returncode", 1))


if __name__ == "__main__":
    raise SystemExit(main())

