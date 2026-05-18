"""Import MT5 tick CSV exports into PowerFlow tick_archive.db."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, Iterable, Optional, Sequence

from tick_archive_writer import TickArchiveWriter


def iter_csv_ticks(
    csv_path: str | Path,
    *,
    symbol_override: Optional[str] = None,
    source_mode_override: Optional[str] = None,
    broker_override: Optional[str] = None,
) -> Iterable[Dict[str, str]]:
    with Path(csv_path).open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            tick = {str(k).strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items() if k is not None}
            if symbol_override:
                tick["symbol"] = symbol_override.upper().strip()
            if source_mode_override:
                tick["source_mode"] = source_mode_override.upper().strip()
            if broker_override:
                tick["broker"] = broker_override
            yield tick


def import_csv(
    csv_path: str | Path,
    db_path: str | Path,
    *,
    symbol: Optional[str] = None,
    source_mode: Optional[str] = None,
    broker: Optional[str] = None,
) -> Dict[str, int | str]:
    writer = TickArchiveWriter(db_path)
    result = writer.insert_ticks(
        iter_csv_ticks(csv_path, symbol_override=symbol, source_mode_override=source_mode, broker_override=broker)
    )
    return {
        "csv": str(Path(csv_path).resolve()),
        "db": str(Path(db_path).resolve()),
        "inserted": result.inserted,
        "ignored": result.ignored,
        "total_rows": writer.count_ticks(symbol),
        "journal_mode": writer.journal_mode(),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Import MT5 raw tick CSV into tick_archive.db")
    parser.add_argument("--csv", required=True, help="MT5 CSV file to import")
    parser.add_argument("--db", default="tick_archive.db", help="Target tick_archive.db path")
    parser.add_argument("--symbol", default=None, help="Override symbol for all rows")
    parser.add_argument("--source-mode", default=None, help="Override source_mode for all rows")
    parser.add_argument("--broker", default=None, help="Override broker for all rows")
    args = parser.parse_args(argv)

    summary = import_csv(args.csv, args.db, symbol=args.symbol, source_mode=args.source_mode, broker=args.broker)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
