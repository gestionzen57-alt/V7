#!/usr/bin/env python3
"""
START.py - Lanceur PowerFlow V6
Lance uniquement le dashboard (le bridge tourne deja separement)
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path

CORE_DIR = Path(__file__).parent

def print_banner():
    print()
    print("=" * 55)
    print("   POWERFLOW V6 — DASHBOARD LIVE")
    print("=" * 55)
    print()

def check_bridge():
    """Verifie si le bridge alimente la DB"""
    try:
        import sqlite3
        from datetime import datetime, timezone
        conn = sqlite3.connect(str(CORE_DIR / "powerflow.db"))
        c = conn.cursor()
        c.execute("SELECT created_at FROM force_snapshots ORDER BY created_at DESC LIMIT 1")
        row = c.fetchone()
        conn.close()
        if row:
            dt = datetime.fromisoformat(row[0])
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            minutes = abs((datetime.now(timezone.utc) - dt).total_seconds() / 60)
            if minutes < 5:
                print(f"  Bridge : OK  (donnee il y a {int(minutes)}min)")
                return True
            else:
                print(f"  Bridge : ATTENTION — derniere donnee il y a {int(minutes)}min")
                print(f"           Lance 'python capture_bridge.py' dans un autre terminal")
                return False
    except Exception as e:
        print(f"  Bridge : ERREUR — {e}")
        return False

def launch_dashboard():
    """Lance dashboard_server en arriere-plan"""
    try:
        proc = subprocess.Popen(
            [sys.executable, "dashboard_server.py", "--serve"],
            cwd=str(CORE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(2)
        if proc.poll() is None:
            print(f"  Dashboard : OK (PID {proc.pid})")
            return proc
        else:
            print(f"  Dashboard : ERREUR au demarrage")
            return None
    except Exception as e:
        print(f"  Dashboard : ERREUR — {e}")
        return None

def main():
    print_banner()

    print("Verification bridge...")
    bridge_ok = check_bridge()
    print()

    print("Lancement dashboard...")
    dash_proc = launch_dashboard()
    print()

    if not dash_proc:
        print("ERREUR : Dashboard ne demarre pas.")
        print("Lance manuellement : python dashboard_server.py --serve")
        return

    print("=" * 55)
    print("  DASHBOARD EN MARCHE")
    print("=" * 55)
    print()
    if not bridge_ok:
        print("  ⚠️  BRIDGE NON DETECTE")
        print("  Lance : python capture_bridge.py")
        print()
    print("  URL : http://localhost:8080/dashboard_live.html")
    print()
    print("  Ctrl+C pour arreter le dashboard")
    print()

    try:
        webbrowser.open("http://localhost:8080/dashboard_live.html")
    except:
        pass

    try:
        while True:
            time.sleep(30)
            if dash_proc.poll() is not None:
                print("  Dashboard arrete — relance...")
                dash_proc = launch_dashboard()
    except KeyboardInterrupt:
        print()
        print("Dashboard arrete.")
        print("Le bridge continue de tourner.")
        if dash_proc:
            dash_proc.terminate()

if __name__ == "__main__":
    main()
