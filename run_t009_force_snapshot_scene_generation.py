from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

from pf_t009_force_snapshot_scene_generator import DATE_TARGETS_DEFAULT, GeneratorConfig, generate


def parse_dates(text: str | None) -> tuple[str, ...]:
    if not text:
        return DATE_TARGETS_DEFAULT
    return tuple(x.strip() for x in text.split(",") if x.strip())


def parse_tfs(text: str | None) -> tuple[int, ...]:
    if not text:
        return (1, 5, 15, 30, 60)
    return tuple(int(x.strip()) for x in text.split(",") if x.strip())


def zip_summaries(output_dir: Path) -> Path:
    root = output_dir / "force_snapshot_derived_summaries"
    zip_path = output_dir / "B9_FORCE_SNAPSHOT_DERIVED_SUMMARIES_20260504_20260514.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        if root.exists():
            for file in sorted(root.rglob("t009_sequence_summary.json")):
                zf.write(file, file.relative_to(root.parent))
    return zip_path


def main() -> int:
    p = argparse.ArgumentParser(description="T009/B9 force_snapshots_v2 historical scene generator")
    p.add_argument("--db", required=True, help="Path to powerflow.db, opened read-only")
    p.add_argument("--output", required=True, help="Output directory")
    p.add_argument("--symbol", default="GBPUSD")
    p.add_argument("--dates", default=",".join(DATE_TARGETS_DEFAULT), help="Comma-separated YYYY-MM-DD dates")
    p.add_argument("--preferred-timeframes", default="1,5,15,30,60")
    p.add_argument("--max-window-min", type=int, default=60)
    p.add_argument("--pip-size", type=float, default=0.0001)
    p.add_argument("--strict-full-days", action="store_true", help="Skip sparse/partial days")
    args = p.parse_args()

    cfg = GeneratorConfig(
        db_path=Path(args.db).resolve(),
        output_dir=Path(args.output).resolve(),
        symbol=args.symbol,
        dates=parse_dates(args.dates),
        preferred_timeframes=parse_tfs(args.preferred_timeframes),
        max_window_minutes=args.max_window_min,
        pip_size=args.pip_size,
        allow_partial_days=not args.strict_full_days,
    )
    result = generate(cfg)
    zip_path = zip_summaries(cfg.output_dir)
    print("B9 force snapshot scene generation done")
    print("Output dir:", cfg.output_dir)
    print("Generated summaries:", result["generated_count"])
    for item in result["generated"]:
        print(f" - {item['date']} moments={item['moment_count']} path={item['path']}")
    print("ZIP:", zip_path)
    print(json.dumps({"generated_count": result["generated_count"], "zip": str(zip_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
