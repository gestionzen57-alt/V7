#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PowerFlow V7.3.6b - Trader Journal J1 schema-flex hotfix.

Purpose:
- Build a J+1 review object from machine perceptions.
- Read Daily Journal / Daily Flow Packet / Multiread with tolerant schemas.
- Never decide a trade.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


ROOT_DAILY_JOURNAL = Path("output/dashboard_surface/daily_journal.json")
ROOT_DAILY_FLOW_PACKET = Path("output/dashboard_surface/daily_flow_packet.json")
ROOT_DAILY_FLOW_PACKETS = Path("output/dashboard_surface/daily_flow_packets.json")
ROOT_COCKPIT = Path("output/dashboard_surface/trader_cockpit.json")
ROOT_MULTIREAD = Path("output/dashboard_surface/powerflow_multiread_synthesis.json")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_json(path: Path, data: Any, pretty: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    txt = json.dumps(data, indent=2 if pretty else None, ensure_ascii=False)
    path.write_text(txt + "\n", encoding="utf-8")


def as_list(v: Any) -> List[Any]:
    return v if isinstance(v, list) else []


def as_dict(v: Any) -> Dict[str, Any]:
    return v if isinstance(v, dict) else {}


def find_symbol_obj(container: Any, symbol: str) -> Dict[str, Any]:
    sym = symbol.upper()
    if isinstance(container, dict):
        for k, v in container.items():
            if str(k).upper() == sym and isinstance(v, dict):
                return v
        for v in container.values():
            if isinstance(v, dict) and str(v.get("symbol", "")).upper() == sym:
                return v
            if isinstance(v, list):
                found = find_symbol_obj(v, sym)
                if found:
                    return found
    if isinstance(container, list):
        for item in container:
            if isinstance(item, dict) and str(item.get("symbol", "")).upper() == sym:
                return item
    return {}


def first_non_empty(*vals: Any, default: Any = None) -> Any:
    for v in vals:
        if v is not None and v != "" and v != [] and v != {}:
            return v
    return default


def count_or_len(v: Any) -> int:
    if isinstance(v, list):
        return len(v)
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return int(v)
    return 0


def extract_daily_from_flow_packet(symbol: str, daily_flow_packet: Dict[str, Any]) -> Dict[str, Any]:
    obj = find_symbol_obj(daily_flow_packet.get("symbols"), symbol)
    if not obj:
        return {}
    return {
        "date_utc": obj.get("date_utc") or obj.get("reference_date_utc"),
        "high_of_day": obj.get("high_of_day"),
        "low_of_day": obj.get("low_of_day"),
        "close": obj.get("close"),
        "close_position": obj.get("close_position"),
        "tested_levels": obj.get("tested_count"),
        "rejected_levels": obj.get("rejected_count"),
        "accepted_levels": obj.get("accepted_count"),
        "sweeps": obj.get("sweep_count"),
        "intent": obj.get("intent_detected") or obj.get("intent"),
        "prediction_next_session": obj.get("prediction_next_session"),
        "technical_risks": as_list(obj.get("technical_risks")),
    }


def extract_daily_from_flow_packets(symbol: str, daily_flow_packets: Dict[str, Any]) -> Dict[str, Any]:
    packets = as_dict(daily_flow_packets.get("packets"))
    pkt = packets.get(symbol) or packets.get(symbol.upper()) or packets.get(symbol.lower()) or {}
    if not isinstance(pkt, dict):
        return {}
    dp = as_dict(pkt.get("daily_packet"))
    levels = as_dict(dp.get("journal_levels"))
    return {
        "date_utc": dp.get("reference_date_utc") or pkt.get("reference_date_utc"),
        "high_of_day": levels.get("high_of_day"),
        "low_of_day": levels.get("low_of_day"),
        "open": levels.get("open"),
        "close": levels.get("close"),
        "close_position": levels.get("close_position"),
        "tested_levels": count_or_len(dp.get("tested_levels")),
        "rejected_levels": count_or_len(dp.get("rejected_levels")),
        "accepted_levels": count_or_len(dp.get("accepted_levels")),
        "sweeps": count_or_len(dp.get("sweep_candidates") or dp.get("sweeps")),
        "intent": dp.get("intent_detected") or dp.get("intent"),
        "prediction_next_session": dp.get("prediction_next_session"),
        "technical_risks": as_list(pkt.get("technical_risks")) + as_list(dp.get("technical_risks")),
    }


def extract_daily_from_journal(symbol: str, daily_journal: Dict[str, Any]) -> Dict[str, Any]:
    source: Dict[str, Any] = {}
    journals = daily_journal.get("journals")
    if isinstance(journals, dict):
        cand = journals.get(symbol) or journals.get(symbol.upper()) or find_symbol_obj(journals, symbol)
        if isinstance(cand, dict):
            source = cand
    elif isinstance(journals, list):
        source = find_symbol_obj(journals, symbol)

    if not source:
        source = find_symbol_obj(daily_journal.get("symbols"), symbol)

    journal = as_dict(source.get("journal")) or as_dict(source.get("daily_journal")) or source
    levels = as_dict(journal.get("journal_levels")) or as_dict(journal.get("levels")) or journal

    return {
        "date_utc": first_non_empty(journal.get("date_utc"), journal.get("reference_date_utc"), source.get("date_utc")),
        "high_of_day": first_non_empty(journal.get("high_of_day"), levels.get("high_of_day")),
        "low_of_day": first_non_empty(journal.get("low_of_day"), levels.get("low_of_day")),
        "open": first_non_empty(journal.get("open"), levels.get("open")),
        "close": first_non_empty(journal.get("close"), levels.get("close")),
        "close_position": first_non_empty(journal.get("close_position"), levels.get("close_position")),
        "tested_levels": first_non_empty(
            journal.get("tested"),
            journal.get("tested_count"),
            count_or_len(journal.get("levels_tested")),
            count_or_len(journal.get("tested_levels")),
        ),
        "rejected_levels": first_non_empty(
            journal.get("rejected"),
            journal.get("rejected_count"),
            count_or_len(journal.get("levels_rejected")),
            count_or_len(journal.get("rejected_levels")),
        ),
        "accepted_levels": first_non_empty(
            journal.get("accepted"),
            journal.get("accepted_count"),
            count_or_len(journal.get("levels_accepted")),
            count_or_len(journal.get("accepted_levels")),
        ),
        "sweeps": first_non_empty(
            journal.get("sweeps"),
            journal.get("sweep_count"),
            count_or_len(journal.get("sweep_candidates")),
        ),
        "intent": first_non_empty(journal.get("intent_detected"), journal.get("intent")),
        "prediction_next_session": journal.get("prediction_next_session"),
        "technical_risks": as_list(source.get("technical_risks")) + as_list(journal.get("technical_risks")),
    }


def merge_daily(*parts: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    keys = [
        "date_utc", "high_of_day", "low_of_day", "open", "close", "close_position",
        "tested_levels", "rejected_levels", "accepted_levels", "sweeps",
        "intent", "prediction_next_session"
    ]
    for key in keys:
        out[key] = first_non_empty(*(p.get(key) for p in parts if p), default=None)

    risks: List[str] = []
    for p in parts:
        for r in as_list(p.get("technical_risks")):
            if r not in risks:
                risks.append(r)
    out["technical_risks"] = risks
    return out


def extract_multiread(symbol: str, multiread: Dict[str, Any]) -> Dict[str, Any]:
    obj = find_symbol_obj(multiread.get("symbols"), symbol)
    if not obj:
        return {}
    dirs = as_dict(obj.get("directions"))
    return {
        "machine_direction": first_non_empty(dirs.get("daily"), obj.get("machine_direction"), default="NEUTRAL_OR_WAIT"),
        "multiread_attention": obj.get("attention") or obj.get("status") or "WATCH",
        "multiread_synthesis": obj.get("synthesis") or "UNKNOWN",
        "alignment": obj.get("alignment") or "UNKNOWN",
        "reading": obj.get("reading") or "",
        "technical_risks": as_list(obj.get("technical_risks")),
        "informational_risks": as_list(obj.get("informational_risks")),
    }


def extract_cockpit(symbol: str, cockpit: Dict[str, Any]) -> Dict[str, Any]:
    obj = find_symbol_obj(cockpit.get("symbols"), symbol)
    if not obj and str(cockpit.get("symbol", "")).upper() == symbol.upper():
        obj = cockpit
    if not obj:
        return {}
    return {
        "cockpit_attention": obj.get("attention") or obj.get("status"),
        "cockpit_state": obj.get("state") or obj.get("synthesis"),
        "cockpit_reading": obj.get("reading") or obj.get("summary"),
    }


def status_for(entry: Dict[str, Any]) -> str:
    fields = entry.get("trader_fields", {})
    required = ["actual_result_next_session", "machine_vs_real", "lesson"]
    if all(fields.get(k) for k in required):
        return "J1_REVIEW_FILLED"
    return "PENDING_REVIEW"


def build_entry(symbol: str, daily_journal: Dict[str, Any], daily_flow_packet: Dict[str, Any], daily_flow_packets: Dict[str, Any], multiread: Dict[str, Any], cockpit: Dict[str, Any]) -> Dict[str, Any]:
    dj = extract_daily_from_journal(symbol, daily_journal)
    dfp = extract_daily_from_flow_packet(symbol, daily_flow_packet)
    dfps = extract_daily_from_flow_packets(symbol, daily_flow_packets)

    daily = merge_daily(dfps, dfp, dj)
    mr = extract_multiread(symbol, multiread)
    cp = extract_cockpit(symbol, cockpit)

    technical_risks: List[str] = []
    for src in [daily, mr]:
        for r in as_list(src.get("technical_risks")):
            if r not in technical_risks:
                technical_risks.append(r)

    informational_risks: List[str] = []
    for r in as_list(mr.get("informational_risks")):
        if r not in informational_risks:
            informational_risks.append(r)

    entry = {
        "symbol": symbol,
        "date_utc": daily.get("date_utc"),
        "machine_snapshot": {
            "high_of_day": daily.get("high_of_day"),
            "low_of_day": daily.get("low_of_day"),
            "open": daily.get("open"),
            "close": daily.get("close"),
            "close_position": first_non_empty(daily.get("close_position"), default="UNKNOWN"),
            "tested_levels": count_or_len(daily.get("tested_levels")),
            "rejected_levels": count_or_len(daily.get("rejected_levels")),
            "accepted_levels": count_or_len(daily.get("accepted_levels")),
            "sweeps": count_or_len(daily.get("sweeps")),
            "intent": first_non_empty(daily.get("intent"), default="UNKNOWN"),
            "prediction_next_session": first_non_empty(daily.get("prediction_next_session"), default="UNKNOWN"),
            "machine_direction": first_non_empty(mr.get("machine_direction"), default="NEUTRAL_OR_WAIT"),
            "multiread_attention": first_non_empty(mr.get("multiread_attention"), default="WATCH"),
            "multiread_synthesis": first_non_empty(mr.get("multiread_synthesis"), default="UNKNOWN"),
            "alignment": first_non_empty(mr.get("alignment"), default="UNKNOWN"),
            "reading": first_non_empty(mr.get("reading"), cp.get("cockpit_reading"), default=""),
        },
        "trader_fields": {
            "htf_manual_read": None,
            "zones_seen": None,
            "rotation_seen": None,
            "correlation_coalition_seen": None,
            "trader_prediction_next_session": None,
            "actual_result_next_session": None,
            "machine_vs_real": None,
            "trader_vs_real": None,
            "lesson": None,
        },
        "technical_risks": technical_risks,
        "informational_risks": informational_risks,
    }
    entry["j1_review_status"] = status_for(entry)
    return entry


def md_val(v: Any) -> str:
    if v is None:
        return ""
    return str(v)


def write_markdown(path: Path, payload: Dict[str, Any]) -> None:
    lines: List[str] = []
    lines.append("# PowerFlow V7.3.6b - Journal trader J+1")
    lines.append("")
    lines.append(f"Generated UTC: {payload.get('timestamp_utc')}")
    lines.append(f"Method: {payload.get('method')}")
    lines.append("")
    lines.append("## Objectif")
    lines.append("")
    lines.append("Creer la boucle quotidienne : lecture -> prediction -> resultat -> apprentissage.")
    lines.append("")

    for e in payload.get("symbols", []):
        m = e.get("machine_snapshot", {})
        tf = e.get("trader_fields", {})
        lines.append(f"## {e.get('symbol')}")
        lines.append("")
        lines.append("### Lecture machine")
        lines.append("")
        lines.append(f"- Date UTC : {md_val(e.get('date_utc'))}")
        lines.append(f"- High : {md_val(m.get('high_of_day'))}")
        lines.append(f"- Low : {md_val(m.get('low_of_day'))}")
        lines.append(f"- Open : {md_val(m.get('open'))}")
        lines.append(f"- Close : {md_val(m.get('close'))}")
        lines.append(f"- Position close : {md_val(m.get('close_position'))}")
        lines.append(f"- Niveaux testes : {md_val(m.get('tested_levels'))}")
        lines.append(f"- Niveaux rejetes : {md_val(m.get('rejected_levels'))}")
        lines.append(f"- Niveaux acceptes : {md_val(m.get('accepted_levels'))}")
        lines.append(f"- Sweeps : {md_val(m.get('sweeps'))}")
        lines.append(f"- Intention machine : {md_val(m.get('intent'))}")
        lines.append(f"- Prediction machine : {md_val(m.get('prediction_next_session'))}")
        lines.append(f"- Direction machine : {md_val(m.get('machine_direction'))}")
        lines.append(f"- Synthese multiread : {md_val(m.get('multiread_synthesis'))}")
        lines.append(f"- Alignement : {md_val(m.get('alignment'))}")
        lines.append(f"- Lecture : {md_val(m.get('reading'))}")
        lines.append("")
        lines.append("### Lecture trader a remplir")
        lines.append("")
        lines.append(f"- HTF manuel : {md_val(tf.get('htf_manual_read'))}")
        lines.append(f"- Zones vues : {md_val(tf.get('zones_seen'))}")
        lines.append(f"- Rotation vue : {md_val(tf.get('rotation_seen'))}")
        lines.append(f"- Correlation / coalition vue : {md_val(tf.get('correlation_coalition_seen'))}")
        lines.append(f"- Prediction trader J+1 : {md_val(tf.get('trader_prediction_next_session'))}")
        lines.append("")
        lines.append("### Revue J+1 a remplir")
        lines.append("")
        lines.append(f"- Resultat reel J+1 : {md_val(tf.get('actual_result_next_session'))}")
        lines.append(f"- Ecart machine vs reel : {md_val(tf.get('machine_vs_real'))}")
        lines.append(f"- Ecart trader vs reel : {md_val(tf.get('trader_vs_real'))}")
        lines.append(f"- Apprentissage : {md_val(tf.get('lesson'))}")
        lines.append("")
        if e.get("technical_risks"):
            lines.append("### Risques techniques")
            lines.append("")
            for r in e.get("technical_risks", []):
                lines.append(f"- {r}")
            lines.append("")
        if e.get("informational_risks"):
            lines.append("### Notes informationnelles")
            lines.append("")
            for r in e.get("informational_risks", []):
                lines.append(f"- {r}")
            lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[Iterable[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default="GBPUSD,EURUSD,USDJPY")
    ap.add_argument("--daily-journal", default=str(ROOT_DAILY_JOURNAL))
    ap.add_argument("--daily-flow-packet", default=str(ROOT_DAILY_FLOW_PACKET))
    ap.add_argument("--daily-flow-packets", default=str(ROOT_DAILY_FLOW_PACKETS))
    ap.add_argument("--cockpit", default=str(ROOT_COCKPIT))
    ap.add_argument("--multiread", default=str(ROOT_MULTIREAD))
    ap.add_argument("--output", default="output/dashboard_surface/trader_journal_j1.json")
    ap.add_argument("--md", default="output/dashboard_surface/trader_journal_j1.md")
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args(list(argv) if argv is not None else None)

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]

    daily_journal = read_json(Path(args.daily_journal))
    daily_flow_packet = read_json(Path(args.daily_flow_packet))
    daily_flow_packets = read_json(Path(args.daily_flow_packets))
    cockpit = read_json(Path(args.cockpit))
    multiread = read_json(Path(args.multiread))

    entries = [
        build_entry(s, daily_journal, daily_flow_packet, daily_flow_packets, multiread, cockpit)
        for s in symbols
    ]

    pending = [f"{e['symbol']}_J1_REVIEW_PENDING" for e in entries if e.get("j1_review_status") == "PENDING_REVIEW"]
    missing_daily = [
        f"{e['symbol']}_DAILY_FIELDS_MISSING"
        for e in entries
        if e["machine_snapshot"].get("intent") == "UNKNOWN" or e["machine_snapshot"].get("high_of_day") is None
    ]

    payload = {
        "timestamp_utc": utc_now(),
        "method": "TRADER_JOURNAL_J1_V736B_SCHEMA_FLEX",
        "symbols": entries,
        "global_status": "J1_REVIEW_PENDING" if pending else "J1_REVIEW_FILLED",
        "critical_issues": pending + missing_daily,
        "inputs": {
            "daily_journal": args.daily_journal,
            "daily_flow_packet": args.daily_flow_packet,
            "daily_flow_packets": args.daily_flow_packets,
            "cockpit": args.cockpit,
            "multiread": args.multiread,
        },
        "note": "Journal J+1 records machine perception and leaves trader/result/lesson fields editable. It does not decide trades.",
    }

    write_json(Path(args.output), payload, pretty=args.pretty)
    write_markdown(Path(args.md), payload)

    if args.pretty:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    print(
        "TRADER_JOURNAL_J1_OK | "
        f"global_status={payload['global_status']} | symbols={len(entries)} | "
        f"out={args.output} | md={args.md}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
