#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Replace pf_trader_attention_packet_once.py with V7.6 Turbo B.

Usage:
  python patch_trader_attention_packet_v76_b.py --file pf_trader_attention_packet_once.py
"""
from __future__ import annotations
import argparse
import shutil
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default="pf_trader_attention_packet_once.py")
    parser.add_argument("--source", default="pf_trader_attention_packet_once_v76_b.py")
    args = parser.parse_args()

    target = Path(args.file)
    source = Path(args.source)
    if not source.exists():
        alt = Path.home() / "Downloads" / source.name
        if alt.exists():
            source = alt
    if not source.exists():
        raise SystemExit(f"[KO] source missing: {args.source}")
    if target.exists():
        backup = target.with_suffix(target.suffix + ".bak_v76_turbo_b")
        shutil.copy2(target, backup)
        print(f"[OK] backup  {backup}")
    shutil.copy2(source, target)
    print(f"[OK] patched {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
