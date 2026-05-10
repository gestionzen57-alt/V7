#!/usr/bin/env python3
"""
PowerFlow V7.2 — B6 Scene Memory Enrichment

Add scene_id / scene_context to behavioral alerts before or around B6 memory.

This module is additive:
- does not overwrite B6 logic
- does not break existing 6D pattern tuple
- does not write DB
- does not filter alerts
- does not decide

Outputs:
- output/behavioral_alert_queue_scene_enriched.json
- output/scene_memory_enrichment_report.json
- output/scene_memory_enrichment_report.md
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pf_scene_registry import enrich_alert_with_scene, VERSION as SCENE_REGISTRY_VERSION


VERSION = "SceneMemoryEnrichmentV0.1"
METHOD = "scene_memory_enrichment_non_blocking"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_alert_queue(path: Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    risks: List[str] = []
    if not path.exists():
        return [], ["QUEUE_NOT_FOUND"]

    raw = path.read_text(encoding="utf-8", errors="replace").strip()
    if not raw:
        return [], ["QUEUE_EMPTY_FILE"]

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        alerts = []
        malformed = 0
        for line in raw.splitlines():
            line = line.strip().rstrip(",")
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                malformed += 1
                continue
            if isinstance(obj, dict):
                alerts.append(obj)
        if malformed:
            risks.append("MALFORMED_JSONL_ENTRIES")
        return alerts, risks

    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)], risks

    if isinstance(data, dict):
        for key in ("alerts", "events", "queue", "items", "results", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)], risks
        if any(k in data for k in ("alert_type", "type", "scene_id", "event_type")):
            return [data], risks
        return [], ["NO_ALERT_LIST_FOUND_IN_JSON"]

    return [], ["UNSUPPORTED_QUEUE_FORMAT"]


def enrich_queue(alerts: List[Dict[str, Any]], threshold: float = 0.35) -> List[Dict[str, Any]]:
    return [enrich_alert_with_scene(alert, threshold=threshold) for alert in alerts]


def build_report(
    queue_path: Path,
    enriched_alerts: List[Dict[str, Any]],
    load_risks: List[str],
    threshold: float,
) -> Dict[str, Any]:
    scene_counter = Counter(a.get("scene_id", "UNKNOWN_SCENE") for a in enriched_alerts)
    family_counter = Counter(a.get("scene_family", "UNKNOWN") for a in enriched_alerts)
    compression_counter = Counter(
        (((a.get("scene_context") or {}).get("compression_qualification") or {}).get("compression_label", "UNKNOWN"))
        for a in enriched_alerts
    )

    risks = list(load_risks)
    for alert in enriched_alerts:
        for risk in alert.get("technical_risks", []):
            risks.append(str(risk))

    risk_counter = Counter(risks)

    return {
        "valid": True,
        "method": METHOD,
        "version": VERSION,
        "scene_registry_version": SCENE_REGISTRY_VERSION,
        "generated_at": utc_now_iso(),
        "queue_path": str(queue_path),
        "threshold": threshold,
        "total_alerts": len(enriched_alerts),
        "metrics_only": True,
        "no_filtering": True,
        "no_trade_decision": True,
        "summary": {
            "by_scene_id": dict(scene_counter),
            "by_scene_family": dict(family_counter),
            "by_compression_qualification": dict(compression_counter),
            "technical_risks": dict(risk_counter),
        },
        "top_scenes": [
            {"scene_id": scene, "count": count}
            for scene, count in scene_counter.most_common(10)
        ],
        "technical_risks": list(dict.fromkeys(risks)),
    }


def write_markdown_report(report: Dict[str, Any], path: Path) -> None:
    lines = [
        "# PowerFlow V7.2 — Scene Memory Enrichment Report",
        "",
        f"**Generated at:** {report.get('generated_at')}",
        f"**Queue:** `{report.get('queue_path')}`",
        f"**Total alerts:** **{report.get('total_alerts')}**",
        f"**Method:** `{report.get('method')}`",
        "",
        "## Doctrine",
        "",
        "- This enrichment is non-blocking.",
        "- It does not filter alerts.",
        "- It does not decide.",
        "- It only gives scene names to alerts so B6 can remember behavior.",
        "",
        "## By scene",
        "",
    ]

    by_scene = report.get("summary", {}).get("by_scene_id", {})
    if by_scene:
        for k, v in sorted(by_scene.items()):
            lines.append(f"- `{k}`: {v}")
    else:
        lines.append("- No scene observed.")

    lines += ["", "## By family", ""]
    by_family = report.get("summary", {}).get("by_scene_family", {})
    if by_family:
        for k, v in sorted(by_family.items()):
            lines.append(f"- `{k}`: {v}")
    else:
        lines.append("- No family observed.")

    lines += ["", "## Compression qualification", ""]
    comp = report.get("summary", {}).get("by_compression_qualification", {})
    if comp:
        for k, v in sorted(comp.items()):
            lines.append(f"- `{k}`: {v}")
    else:
        lines.append("- No compression qualification.")

    lines += ["", "## Technical risks", ""]
    risks = report.get("summary", {}).get("technical_risks", {})
    if risks:
        for k, v in sorted(risks.items()):
            lines.append(f"- `{k}`: {v}")
    else:
        lines.append("- No technical risk.")

    lines += [
        "",
        "## B6 integration",
        "",
        "Each enriched alert contains:",
        "",
        "```text",
        "scene_id",
        "scene_family",
        "scene_confidence_non_blocking",
        "scene_context",
        "memory_tuple_6d",
        "B3_noise_ratio if available",
        "B7_state if available",
        "outcome if available",
        "bars_to_move if available",
        "```",
        "",
        "The existing B6 6D tuple remains compatible.",
        "",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")


def run_enrichment(
    queue_path: Path,
    out_queue: Path,
    out_report_json: Path,
    out_report_md: Path,
    threshold: float = 0.35,
) -> Dict[str, Any]:
    alerts, load_risks = load_alert_queue(queue_path)
    enriched = enrich_queue(alerts, threshold=threshold)
    report = build_report(queue_path, enriched, load_risks, threshold=threshold)

    out_queue.parent.mkdir(parents=True, exist_ok=True)
    out_report_json.parent.mkdir(parents=True, exist_ok=True)
    out_report_md.parent.mkdir(parents=True, exist_ok=True)

    out_queue.write_text(json.dumps(enriched, indent=2, ensure_ascii=False), encoding="utf-8")
    out_report_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown_report(report, out_report_md)

    return report
