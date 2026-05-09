"""
Runner — Telegram Agentic Nodes V0.1

Dry-run:
    python run_telegram_agentic_nodes_once.py --json output/cockpit_agentic_state_v01.json --dry-run

Send:
    python run_telegram_agentic_nodes_once.py --json output/cockpit_agentic_state_v01.json

Force send:
    python run_telegram_agentic_nodes_once.py --json output/cockpit_agentic_state_v01.json --force
"""

from __future__ import annotations

from telegram_agentic_nodes_v01 import main

if __name__ == "__main__":
    raise SystemExit(main())
