#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
lab_film.py

PowerFlow V7.1 — Film Lab CLI.

Role:
    Execute the Film Engine from replay JSON and optional behavioral alert queue,
    then write a Markdown report.

Doctrine:
    - No DB connection.
    - No cockpit import.
    - JSON replay/queue input only.
    - Markdown film output.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pf_film_engine import FilmEngineConfig, generate_film_markdown_from_files


DEFAULT_OUTPUT_DIR = Path("reports")
DEFAULT_FORMAT = "markdown"


@dataclass(frozen=True)
class LabFilmConfig:
    replay_file: Path
    queue_file: Optional[Path]
    output: Path
    output_format: str
    title: str
    include_raw_evidence: bool
    m1_m5_angle_gap_threshold: float
    strong_angle_threshold: float
    compression_ratio_threshold: float
    elastic_score_threshold: float


def default_output_path(replay_file: Path) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    stem = replay_file.stem or "replay"
    return DEFAULT_OUTPUT_DIR / f"film_{stem}_{timestamp}.md"


def validate_file_exists(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")

    if not path.is_file():
        raise ValueError(f"{label} is not a file: {path}")


def write_text_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_engine_config(config: LabFilmConfig) -> FilmEngineConfig:
    return FilmEngineConfig(
        title=config.title,
        include_raw_evidence=config.include_raw_evidence,
        m1_m5_angle_gap_threshold=config.m1_m5_angle_gap_threshold,
        strong_angle_threshold=config.strong_angle_threshold,
        compression_ratio_threshold=config.compression_ratio_threshold,
        elastic_score_threshold=config.elastic_score_threshold,
    )


def run(config: LabFilmConfig) -> dict:
    validate_file_exists(config.replay_file, "Replay file")

    if config.queue_file is not None:
        validate_file_exists(config.queue_file, "Queue file")

    if config.output_format != "markdown":
        raise ValueError("Only markdown format is supported for V7.1 Phase 3.")

    engine_config = build_engine_config(config)

    markdown = generate_film_markdown_from_files(
        replay_file=config.replay_file,
        queue_file=config.queue_file,
        config=engine_config,
    )

    write_text_file(config.output, markdown)

    return {
        "runner": "lab_film.py",
        "status": "OK",
        "format": config.output_format,
        "replay_file": str(config.replay_file),
        "queue_file": str(config.queue_file) if config.queue_file else None,
        "output": str(config.output),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def parse_args() -> LabFilmConfig:
    parser = argparse.ArgumentParser(
        description="Generate a PowerFlow Film markdown report from replay JSON and optional alert queue."
    )

    parser.add_argument(
        "--replay-file",
        required=True,
        help="Path to Replay Engine JSON file.",
    )

    parser.add_argument(
        "--queue-file",
        default=None,
        help="Optional path to behavioral_alert_queue.json.",
    )

    parser.add_argument(
        "--output",
        default=None,
        help="Output Markdown report path. Default: reports/film_<replay>_<timestamp>.md",
    )

    parser.add_argument(
        "--format",
        dest="output_format",
        default=DEFAULT_FORMAT,
        choices=("markdown",),
        help="Output format. Default: markdown.",
    )

    parser.add_argument(
        "--title",
        default="PowerFlow Film",
        help="Markdown report title.",
    )

    parser.add_argument(
        "--no-evidence",
        action="store_true",
        help="Hide compact evidence fields in the Markdown report.",
    )

    parser.add_argument(
        "--m1-m5-angle-gap-threshold",
        type=float,
        default=12.0,
        help="Angle gap threshold for M1/M5 desync scene detection. Default: 12.0",
    )

    parser.add_argument(
        "--strong-angle-threshold",
        type=float,
        default=35.0,
        help="Angle delta threshold for marked kinematic shift detection. Default: 35.0",
    )

    parser.add_argument(
        "--compression-ratio-threshold",
        type=float,
        default=0.70,
        help="Compression ratio threshold. Default: 0.70",
    )

    parser.add_argument(
        "--elastic-score-threshold",
        type=float,
        default=0.65,
        help="Elastic score threshold. Default: 0.65",
    )

    args = parser.parse_args()

    replay_file = Path(args.replay_file)
    output = Path(args.output) if args.output else default_output_path(replay_file)

    return LabFilmConfig(
        replay_file=replay_file,
        queue_file=Path(args.queue_file) if args.queue_file else None,
        output=output,
        output_format=args.output_format,
        title=args.title,
        include_raw_evidence=not args.no_evidence,
        m1_m5_angle_gap_threshold=args.m1_m5_angle_gap_threshold,
        strong_angle_threshold=args.strong_angle_threshold,
        compression_ratio_threshold=args.compression_ratio_threshold,
        elastic_score_threshold=args.elastic_score_threshold,
    )


def main() -> int:
    try:
        config = parse_args()
        report = run(config)
    except Exception as exc:
        error_payload = {
            "runner": "lab_film.py",
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