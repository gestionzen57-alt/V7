#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
run_session_overlay_once.py

PowerFlow V7.1 — Session Overlay Runner.

Role:
    Read behavioral_alert_queue.json, inject session_context into each alert,
    and write a preview JSON output.

Doctrine:
    - No DB write.
    - No cockpit dependency.
    - Queue-in / JSON-out.
    - Preview output by default.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

from pf_session_overlay import enrich_payload_with_session_context


DEFAULT_INPUT = Path("output") / "behavioral_alert_queue.json"
DEFAULT_OUTPUT = Path("output") / "behavioral_alert_queue.session_preview.json"


@dataclass(frozen=True)
class RunnerConfig:
    input_path: Path
    output_path: Path
    pretty: bool
    dry_run: bool


def load_json_file(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json_file(path: Path, payload: Any, pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as handle:
        if pretty:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
        else:
            json.dump(payload, handle, separators=(",", ":"), ensure_ascii=False)


def normalize_alerts(payload: Any) -> List[Dict[str, Any]]:
    """
    Accept common queue shapes:
        - list[dict]
        - {"alerts": list[dict]}
        - {"items": list[dict]}
        - {"queue": list[dict]}
        - {"behavioral_alert_queue": list[dict]}
    """
    if isinstance(payload, list):
        raw_alerts = payload
    elif isinstance(payload, dict):
        for key in ("alerts", "items", "queue", "behavioral_alert_queue"):
            value = payload.get(key)
            if isinstance(value, list):
                raw_alerts = value
                break
        else:
            raise ValueError(
                "Unsupported JSON object shape. Expected key: alerts/items/queue/behavioral_alert_queue."
            )
    else:
        raise ValueError("Unsupported JSON payload. Expected list or object.")

    alerts: List[Dict[str, Any]] = []

    for index, item in enumerate(raw_alerts):
        if isinstance(item, dict):
            alerts.append(item)
        else:
            alerts.append(
                {
                    "raw_value": item,
                    "source_index": index,
                    "alert_type": "INVALID_ALERT_PAYLOAD",
                    "technical_risks": ["NON_DICT_ALERT_PAYLOAD"],
                }
            )

    return alerts


def rebuild_payload(original_payload: Any, enriched_alerts: List[Dict[str, Any]]) -> Any:
    """
    Preserve the original top-level queue shape when possible.
    """
    if isinstance(original_payload, list):
        return enriched_alerts

    if isinstance(original_payload, dict):
        rebuilt = dict(original_payload)

        for key in ("alerts", "items", "queue", "behavioral_alert_queue"):
            if isinstance(rebuilt.get(key), list):
                rebuilt[key] = enriched_alerts
                return rebuilt

        rebuilt["alerts"] = enriched_alerts
        return rebuilt

    return enriched_alerts


def inject_session_context(alerts: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [enrich_payload_with_session_context(alert) for alert in alerts]


def build_run_report(
    input_path: Path,
    output_path: Path,
    alerts_count: int,
    dry_run: bool,
) -> Dict[str, Any]:
    return {
        "runner": "run_session_overlay_once.py",
        "status": "OK",
        "dry_run": dry_run,
        "input": str(input_path),
        "output": str(output_path),
        "alerts_processed": alerts_count,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def run(config: RunnerConfig) -> Dict[str, Any]:
    original_payload = load_json_file(config.input_path)
    alerts = normalize_alerts(original_payload)
    enriched_alerts = inject_session_context(alerts)
    enriched_payload = rebuild_payload(original_payload, enriched_alerts)

    output_document = {
        "metadata": build_run_report(
            input_path=config.input_path,
            output_path=config.output_path,
            alerts_count=len(enriched_alerts),
            dry_run=config.dry_run,
        ),
        "payload": enriched_payload,
    }

    save_json_file(config.output_path, output_document, pretty=config.pretty)
    return output_document["metadata"]


def parse_args() -> RunnerConfig:
    parser = argparse.ArgumentParser(
        description="Inject PowerFlow session_context into behavioral_alert_queue.json preview."
    )

    parser.add_argument(
        "--input",
        dest="input_path",
        default=str(DEFAULT_INPUT),
        help=f"Input behavioral queue JSON path. Default: {DEFAULT_INPUT}",
    )

    parser.add_argument(
        "--output",
        dest="output_path",
        default=str(DEFAULT_OUTPUT),
        help=f"Output preview JSON path. Default: {DEFAULT_OUTPUT}",
    )

    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Write indented JSON output.",
    )

    parser.add_argument(
        "--compact",
        action="store_true",
        help="Write compact JSON output. Overrides --pretty.",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Compatibility flag. This runner still writes only to the output preview path.",
    )

    args = parser.parse_args()
    pretty = bool(args.pretty and not args.compact)

    return RunnerConfig(
        input_path=Path(args.input_path),
        output_path=Path(args.output_path),
        pretty=pretty,
        dry_run=not bool(args.apply),
    )


def main() -> int:
    config = parse_args()

    try:
        report = run(config)
    except Exception as exc:
        error_payload = {
            "runner": "run_session_overlay_once.py",
            "status": "ERROR",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        print(json.dumps(error_payload, indent=2, ensure_ascii=False))
        return 1

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
