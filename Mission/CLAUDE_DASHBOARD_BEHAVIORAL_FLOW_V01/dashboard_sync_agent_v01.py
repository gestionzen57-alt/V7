from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_COCKPIT = Path("output") / "cockpit_agentic_state_v01.json"
DEFAULT_DASHBOARD = Path("dashboard_data.json")


LEVEL_PRIORITY = {
    "HOT": 4,
    "DEGRADED": 3,
    "WATCH": 2,
    "INFO": 1,
}


def load_json(path: Path, required: bool = False) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"Missing required JSON: {path}")
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        if required:
            raise RuntimeError(f"Cannot read JSON {path}: {exc}") from exc
        return {}

    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: dict[str, Any], pretty: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2 if pretty else None),
        encoding="utf-8",
    )


def pick_top_alert(alerts: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not alerts:
        return None

    return max(
        alerts,
        key=lambda a: LEVEL_PRIORITY.get(str(a.get("level", "")), 0),
    )


def build_behavioral_flow_card(cockpit: dict[str, Any]) -> dict[str, Any]:
    behavioral = cockpit.get("behavioral_alerts", []) or []
    degraded = cockpit.get("degraded_alerts", []) or []
    summary = cockpit.get("behavioral_summary", {}) or {}
    film_steps = cockpit.get("film_steps", []) or []

    all_alerts = behavioral + degraded
    top = pick_top_alert(all_alerts)

    top_name = top.get("name") if top else "NO_BEHAVIORAL_ALERT"
    top_level = top.get("level") if top else "INFO"

    release_line = next((s for s in film_steps if s.startswith("[RELEASE]")), "")
    energy_line = next((s for s in film_steps if s.startswith("[ENERGY_CONTEXT]")), "")
    detach_line = next((s for s in film_steps if s.startswith("[DETACH]")), "")

    status = top_level
    if top_name == "FIRST_DETACHMENT_WITH_CLEAN_RELAY":
        status = "HOT_DETACHMENT"
    if any(a.get("name") == "COUNTER_RELEASE_ATTEMPT_ALERT" for a in behavioral):
        status = "HOT_DETACHMENT_COUNTER_RELEASE"
    if any(a.get("name") == "NODE_HEAT_ENERGY_DIVERGENCE" for a in behavioral):
        status = "HOT_DETACHMENT_COUNTER_RELEASE_ENERGY_DIVERGENT"

    line_parts = []
    if detach_line:
        line_parts.append(detach_line.replace("[DETACH] ", ""))
    if release_line:
        line_parts.append(release_line.replace("[RELEASE] ", ""))
    if energy_line:
        line_parts.append(energy_line.replace("[ENERGY_CONTEXT] ", ""))

    return {
        "title": "BEHAVIORAL FLOW",
        "status": status,
        "level": top_level,
        "top_alert": top_name,
        "line": " | ".join(line_parts) if line_parts else "No behavioral film available",
        "summary": summary,
        "alerts": [
            {
                "name": a.get("name"),
                "level": a.get("level"),
                "badge": a.get("dashboard_badge"),
                "reason": a.get("reason"),
            }
            for a in all_alerts
        ],
    }


def replace_card(cards: list[dict[str, Any]], new_card: dict[str, Any]) -> list[dict[str, Any]]:
    title = new_card.get("title")
    out = []
    replaced = False

    for card in cards:
        if isinstance(card, dict) and card.get("title") == title:
            out.append(new_card)
            replaced = True
        else:
            out.append(card)

    if not replaced:
        out.append(new_card)

    return out


def sync_dashboard_data(
    cockpit: dict[str, Any],
    existing_dashboard: dict[str, Any],
) -> dict[str, Any]:
    dashboard = dict(existing_dashboard)

    behavioral = cockpit.get("behavioral_alerts", []) or []
    degraded = cockpit.get("degraded_alerts", []) or []
    film_steps = cockpit.get("film_steps", []) or []
    next_watch = cockpit.get("next_watch_enriched", []) or []
    summary = cockpit.get("behavioral_summary", {}) or {}

    behavioral_card = build_behavioral_flow_card(cockpit)

    dashboard["source"] = "dashboard_sync_agent_v01"
    dashboard["symbol"] = cockpit.get("symbol", dashboard.get("symbol"))
    dashboard["generated_at_utc"] = cockpit.get("generated_at_utc", dashboard.get("generated_at_utc"))
    dashboard["cockpit_status"] = cockpit.get("cockpit_status")
    dashboard["headline"] = cockpit.get("headline")

    dashboard["behavioral_summary"] = summary
    dashboard["behavioral_alerts"] = behavioral
    dashboard["degraded_alerts"] = degraded
    dashboard["film_steps"] = film_steps
    dashboard["next_watch_enriched"] = next_watch
    dashboard["behavioral_flow"] = behavioral_card

    existing_cards = dashboard.get("dashboard_cards", [])
    if not isinstance(existing_cards, list):
        existing_cards = []

    cockpit_cards = cockpit.get("dashboard_cards", [])
    if isinstance(cockpit_cards, list) and cockpit_cards:
        existing_cards = cockpit_cards

    dashboard["dashboard_cards"] = replace_card(existing_cards, behavioral_card)

    return dashboard


def main() -> int:
    parser = argparse.ArgumentParser(description="PowerFlow V6 — Dashboard Sync Agent V0.1")
    parser.add_argument("--cockpit", default=str(DEFAULT_COCKPIT))
    parser.add_argument("--dashboard", default=str(DEFAULT_DASHBOARD))
    parser.add_argument("--out", default=str(DEFAULT_DASHBOARD))
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--summary", action="store_true")

    args = parser.parse_args()

    cockpit_path = Path(args.cockpit)
    dashboard_path = Path(args.dashboard)
    out_path = Path(args.out)

    cockpit = load_json(cockpit_path, required=True)
    existing = load_json(dashboard_path, required=False)

    synced = sync_dashboard_data(cockpit, existing)
    write_json(out_path, synced, pretty=args.pretty)

    if args.summary:
        bs = synced.get("behavioral_summary", {}) or {}
        bf = synced.get("behavioral_flow", {}) or {}

        print("DASHBOARD_SYNC_OK")
        print(f"cockpit={cockpit_path}")
        print(f"out={out_path}")
        print(f"cockpit_status={synced.get('cockpit_status')}")
        print(f"behavioral_count={bs.get('behavioral_count')}")
        print(f"degraded_count={bs.get('degraded_count')}")
        print(f"top_alert={bs.get('top_alert')}")
        print(f"top_level={bs.get('top_level')}")
        print(f"behavioral_flow_status={bf.get('status')}")
        print(f"film_steps_count={len(synced.get('film_steps', []))}")
        print(f"next_watch_enriched_count={len(synced.get('next_watch_enriched', []))}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())