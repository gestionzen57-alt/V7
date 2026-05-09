#!/usr/bin/env python3
"""
Dashboard Server V3 - donnees live pour dashboard_live.html.

PowerFlow V6 : le serveur dashboard reste une couche de lecture/affichage.
Les calculs de terrain et de densite sont delegues aux modules pf_*.

Usage:
    python dashboard_server.py --once
    python dashboard_server.py --loop
    python dashboard_server.py --serve
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pf_cockpit_field import build_and_render_cockpit_field
from pf_temporal_density import scan_all_currencies

try:
    from dashboard_sync_agent_v01 import sync_dashboard_data
except Exception:
    sync_dashboard_data = None

FIELD_PREFIXES = {
    "FIELD:": "dominant",
    "DOMINANT:": "coalition",
    "OPPOSITE/CONTEXT:": "context",
    "CONTESTED_WINDOW:": "contested_window",
    "BIPOLAR_FOCUS:": "bipolar_focus",
    "BIPOLAR_LIST:": "bipolar_list",
}

DENSITY_CURRENCIES = ("GBP", "USD", "EUR", "JPY", "CAD", "CHF", "AUD")


class DashboardDataGenerator:
    def __init__(self, db_path: str = "powerflow.db"):
        self.db_path = db_path
        self.output_file = "dashboard_data.json"

    def _connect(self) -> sqlite3.Connection:
        db_uri = f"{Path(self.db_path).expanduser().resolve().as_uri()}?mode=ro"
        conn = sqlite3.connect(db_uri, uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def get_db_freshness(self) -> tuple[str, str, str]:
        """Retourne le statut DB sans jamais ecrire dans powerflow.db."""
        try:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT created_at FROM force_snapshots ORDER BY created_at DESC LIMIT 1"
                ).fetchone()
        except Exception as exc:
            return "ERROR", f"DB erreur ({exc})", "Erreur"

        if not row:
            return "UNKNOWN", "DB inconnue", "Inconnue"

        last_ts = str(row[0])
        minutes_ago = 0

        try:
            dt = datetime.fromisoformat(last_ts)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            minutes_ago = max(0, int((datetime.now(timezone.utc) - dt).total_seconds() / 60))
        except Exception:
            return "UNKNOWN", "DB timestamp illisible", last_ts

        if minutes_ago > 60:
            return "STALE", f"DB ancienne ({minutes_ago}min)", last_ts
        if minutes_ago > 10:
            return "DELAYED", f"DB ({minutes_ago}min)", last_ts
        return "LIVE", f"LIVE ({minutes_ago}min)", last_ts

    @staticmethod
    def _is_separator(line: str) -> bool:
        stripped = line.strip()
        if not stripped:
            return False
        if len(stripped) >= 3 and set(stripped) <= {"-", "=", "_", "*", " ", "|"}:
            return True
        upper = stripped.upper().rstrip(":")
        return upper in {"TEMPORAL_PATTERNS", "TEMPORAL PATTERNS", "PATTERNS"}

    @classmethod
    def parse_cockpit_field(cls, cockpit_text: str) -> dict[str, str]:
        field = {
            "dominant": "",
            "coalition": "",
            "context": "",
            "contested_window": "",
            "bipolar_focus": "",
            "bipolar_list": "",
            "temporal_patterns": "",
        }

        temporal_lines: list[str] = []
        collect_temporal = False

        for raw_line in cockpit_text.splitlines():
            line = raw_line.strip()
            if not line:
                if collect_temporal and temporal_lines:
                    temporal_lines.append("")
                continue

            if cls._is_separator(line):
                collect_temporal = True
                continue

            upper_line = line.upper()
            matched_prefix = False

            for prefix, target_key in FIELD_PREFIXES.items():
                if upper_line.startswith(prefix):
                    field[target_key] = line.split(":", 1)[1].strip()
                    matched_prefix = True
                    break

            if matched_prefix:
                continue

            if collect_temporal:
                temporal_lines.append(raw_line.rstrip())

        field["temporal_patterns"] = "\n".join(temporal_lines).strip()
        return field

    @staticmethod
    def build_density_dict(density_list: list[dict[str, Any]]) -> dict[str, dict[str, float | str]]:
        density: dict[str, dict[str, float | str]] = {
            currency: {"state": "DEAD", "score": 0.0} for currency in DENSITY_CURRENCIES
        }

        for item in density_list:
            currency = str(item.get("currency", "")).upper()
            if currency not in density:
                continue

            score_value = item.get("density_score", item.get("score", 0.0))
            try:
                score = round(float(score_value), 6)
            except (TypeError, ValueError):
                score = 0.0

            density[currency] = {
                "state": str(item.get("state", "DEAD")),
                "score": score,
            }

        return density

    def generate_data(self) -> dict[str, Any]:
        db_status, db_label, last_ts = self.get_db_freshness()

        try:
            cockpit_text = build_and_render_cockpit_field(
                db_path=self.db_path,
                symbol="GBPUSD",
                timeframes=[1, 5, 15, 30, 60],
                recent_minutes=180,
            )
        except Exception as exc:
            cockpit_text = f"COCKPIT_FIELD_ERROR: {exc}"

        if cockpit_text is None:
            cockpit_text = ""
        cockpit_raw = str(cockpit_text)
        field = self.parse_cockpit_field(cockpit_raw)

        try:
            density_list = scan_all_currencies(
                db_path=self.db_path,
                symbol="GBPUSD",
                timeframe=5,
                window=20,
            )
        except Exception as exc:
            density_list = [
                {
                    "currency": currency,
                    "state": "DEAD",
                    "density_score": 0.0,
                    "note": f"Density error: {exc}",
                }
                for currency in DENSITY_CURRENCIES
            ]

        density = self.build_density_dict(density_list)

        return {
            "timestamp": datetime.now().isoformat(),
            "db_status": db_status,
            "db_label": db_label,
            "db_last_update": last_ts,
            "cockpit_raw": cockpit_raw,
            "field": field,
            "density": density,
        }

    def apply_behavioral_sync(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Enrichit dashboard_data avec le cockpit agentic / behavioral_flow.
        Read-only. Si absent ou erreur, retourne data brut sans casser le serveur.
        """
        if sync_dashboard_data is None:
            return data

        cockpit_path = Path("output") / "cockpit_agentic_state_v01.json"
        if not cockpit_path.exists():
            return data

        try:
            cockpit = json.loads(cockpit_path.read_text(encoding="utf-8"))
            if not isinstance(cockpit, dict):
                return data
            return sync_dashboard_data(cockpit=cockpit, existing_dashboard=data)
        except Exception as exc:
            data["behavioral_sync_error"] = f"{type(exc).__name__}: {exc}"
            return data

    def save_json(self, data: dict[str, Any]) -> None:
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Dashboard mis a jour - {data.get('db_label', '')}")

    def run_once(self) -> None:
        data = self.generate_data()
        data = self.apply_behavioral_sync(data)
        self.save_json(data)

    def run_loop(self, interval: int = 10) -> None:
        print(f"Loop demarree (refresh {interval}s) - Ctrl+C pour arreter")
        try:
            while True:
                self.run_once()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nArret")


def serve_http(port: int = 8080, generator: DashboardDataGenerator | None = None) -> None:
    import http.server
    import socketserver
    import threading

    if generator is None:
        generator = DashboardDataGenerator()

    class CORSHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self) -> None:
            self.send_header("Access-Control-Allow-Origin", "*")
            super().end_headers()

        def log_message(self, format: str, *args: Any) -> None:
            pass

    def refresh_loop() -> None:
        while True:
            try:
                generator.run_once()
            except Exception as exc:
                print(f"Erreur refresh dashboard: {exc}")
            time.sleep(10)

    threading.Thread(target=refresh_loop, daemon=True).start()

    print(f"Serveur demarre sur http://localhost:{port}")
    print(f"Dashboard : http://localhost:{port}/dashboard_live.html")
    print("Ctrl+C pour arreter")

    with socketserver.TCPServer(("", port), CORSHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServeur arrete")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--db", type=str, default="powerflow.db")
    args = parser.parse_args()

    generator = DashboardDataGenerator(db_path=args.db)

    if args.serve:
        generator.run_once()
        serve_http(port=args.port, generator=generator)
    elif args.loop:
        generator.run_loop()
    elif args.once:
        generator.run_once()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
