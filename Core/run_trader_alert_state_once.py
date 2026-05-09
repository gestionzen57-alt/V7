#!/usr/bin/env python3
"""
run_trader_alert_state_once.py

Runner simple pour exécuter pf_trader_alert_state.py une fois.

Usage:
    python run_trader_alert_state_once.py --symbol GBPUSD --pretty
"""

import sys
from pathlib import Path

# Ajouter le répertoire courant au path si besoin
sys.path.insert(0, str(Path(__file__).parent))

from pf_trader_alert_state import (
    generate_trader_alert_state,
    save_trader_alert_state,
    TraderAlertState
)


def main():
    """Main runner."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run Trader Alert State V0.1 once"
    )
    parser.add_argument(
        "--behavioral",
        type=str,
        default="output/behavioral_alert_queue.json",
        help="Path to behavioral_alert_queue.json"
    )
    parser.add_argument(
        "--cockpit",
        type=str,
        default="output/cockpit_agentic_state_v01.json",
        help="Path to cockpit_agentic_state_v01.json"
    )
    parser.add_argument(
        "--symbol",
        type=str,
        default="GBPUSD",
        help="Trading symbol"
    )
    parser.add_argument(
        "--out",
        type=str,
        default="output/trader_alert_state.json",
        help="Output JSON path"
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty print summary to console"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print only summary line"
    )
    
    args = parser.parse_args()
    
    behavioral_path = Path(args.behavioral)
    cockpit_path = Path(args.cockpit)
    output_path = Path(args.out)
    
    print("🚀 Generating Trader Alert State V0.1...")
    print(f"   Behavioral: {behavioral_path}")
    print(f"   Cockpit: {cockpit_path}")
    print(f"   Symbol: {args.symbol}")
    
    # Generate
    state = generate_trader_alert_state(
        behavioral_queue_path=behavioral_path,
        cockpit_state_path=cockpit_path,
        symbol=args.symbol
    )
    
    # Save
    save_trader_alert_state(state, output_path)
    
    # Print
    if args.summary:
        print(f"\n📌 SUMMARY: {state.summary}\n")
    
    if args.pretty:
        print("\n" + "=" * 60)
        print("TRADER ALERT STATE V0.1")
        print("=" * 60)
        print(f"\nSymbol: {args.symbol}")
        print(f"Summary: {state.summary}")
        
        if state.main_alert:
            print(f"\n🔥 MAIN ALERT [{state.main_alert.level}]")
            print(f"   Title: {state.main_alert.title}")
            print(f"   Message: {state.main_alert.message}")
            print(f"   Event Time: {state.main_alert.event_time}")
            print(f"   Age: {state.main_alert.age_seconds}s ({state.main_alert.freshness})")
            print(f"   Why Watch: {state.main_alert.why_watch}")
            
            if state.main_alert.not_confirmed_reason:
                print(f"   ⚠️ Not Confirmed: {state.main_alert.not_confirmed_reason}")
            
            if state.main_alert.contradictions:
                print(f"   ⚠️ Contradictions: {', '.join(state.main_alert.contradictions)}")
            
            print(f"   Source Alerts: {', '.join(state.main_alert.source_alerts[:3])}")
        else:
            print("\n📭 No main alert (all alerts too old or none present)")
        
        if state.secondary_alerts:
            print(f"\n📋 SECONDARY ALERTS ({len(state.secondary_alerts)})")
            for i, sec in enumerate(state.secondary_alerts, 1):
                print(f"   {i}. [{sec.level}] {sec.title} — {sec.age_seconds}s ({sec.freshness})")
        
        print("\n" + "=" * 60)
        print(f"✅ Output saved: {output_path}")
        print("=" * 60 + "\n")
    
    print("✅ Trader Alert State V0.1 complete.")


if __name__ == "__main__":
    main()
