#!/usr/bin/env python3
"""
pf_trader_alert_state.py

MISSION: Trader Alert State V0.1
Synthétiser behavioral_alert_queue + cockpit_agentic_state en UNE alerte trader principale claire.

RÈGLES:
- Français court
- Pas BUY/SELL
- HOT behavioral ≠ release confirmed
- Grouper alertes liées en une scène
- Afficher fraîcheur / âge
- Ne pas spammer

OUTPUT: output/trader_alert_state.json

CRITÈRE: Une scène principale lisible en moins de 3 lignes.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


# ============================================================================
# CONSTANTES
# ============================================================================

# Niveaux d'alerte (priority order)
ALERT_LEVELS = ["HOT", "WATCH", "INFO"]

# Freshness thresholds (seconds)
FRESHNESS_FRESH = 120      # < 2 min
FRESHNESS_RECENT = 300     # < 5 min
FRESHNESS_STALE = 900      # < 15 min
# > 15 min = OLD

# Grouping patterns (pour identifier les alertes liées)
GROUPING_PATTERNS = {
    "detachment_release": [
        "FIRST_DETACHMENT",
        "COUNTER_RELEASE",
        "RELEASE_ATTEMPT",
        "HOT_DETACHMENT"
    ],
    "energy_divergence": [
        "ENERGY_DIVERGENCE",
        "ENERGY_THIN",
        "NODE_HEAT_ENERGY_DIVERGENCE"
    ],
    "relay_quality": [
        "CLEAN_RELAY",
        "M5_RELAY",
        "RELAY_MISSING"
    ],
    "gravity_cluster": [
        "TIGHT_GRAVITY_CLUSTER",
        "SAME_ANGLE_CLUSTER"
    ]
}

# Terms pour construire messages courts
TERMS_SHORT = {
    "FIRST_DETACHMENT": "détachement M1",
    "COUNTER_RELEASE": "contre-release",
    "RELEASE_ATTEMPT": "tentative release",
    "CLEAN_RELAY": "relay propre M5",
    "ENERGY_DIVERGENCE": "énergie divergente",
    "ENERGY_THIN": "énergie faible",
    "NODE_HEAT_ENERGY_DIVERGENCE": "node chaud sans énergie",
    "TIGHT_GRAVITY_CLUSTER": "cluster gravité serré",
    "SAME_ANGLE_CLUSTER": "cluster angle synchrone",
    "HOT_DETACHMENT_COUNTER_RELEASE": "détachement chaud + contre-release"
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class MainAlert:
    """Alerte trader principale."""
    level: str
    title: str
    message: str
    symbol: str
    event_time: str
    age_seconds: int
    freshness: str
    why_watch: str
    not_confirmed_reason: Optional[str]
    contradictions: List[str]
    source_alerts: List[str]


@dataclass
class SecondaryAlert:
    """Alerte secondaire."""
    level: str
    title: str
    age_seconds: int
    freshness: str


@dataclass
class TraderAlertState:
    """État complet de l'alerte trader."""
    meta: Dict[str, Any]
    main_alert: Optional[MainAlert]
    secondary_alerts: List[SecondaryAlert]
    summary: str


# ============================================================================
# HELPERS
# ============================================================================

def compute_freshness(age_seconds: int) -> str:
    """Calculer freshness status."""
    if age_seconds < FRESHNESS_FRESH:
        return "FRESH"
    elif age_seconds < FRESHNESS_RECENT:
        return "RECENT"
    elif age_seconds < FRESHNESS_STALE:
        return "STALE"
    else:
        return "OLD"


def compute_age_seconds(event_time_str: str) -> int:
    """Calculer âge en secondes depuis event_time."""
    try:
        event_dt = datetime.fromisoformat(event_time_str.replace("Z", "+00:00"))
        now_dt = datetime.now(timezone.utc)
        delta = now_dt - event_dt
        return int(delta.total_seconds())
    except Exception:
        return 9999  # default old


def extract_alert_type(alert_name: str) -> str:
    """Extraire le type d'alerte depuis le nom complet."""
    # Example: "HOT_DETACHMENT_COUNTER_RELEASE_ENERGY_DIVERGENT" → "HOT_DETACHMENT_COUNTER_RELEASE"
    for pattern in GROUPING_PATTERNS.values():
        for term in pattern:
            if term in alert_name:
                return term
    return alert_name


def group_related_alerts(alerts: List[Dict]) -> Dict[str, List[Dict]]:
    """Grouper les alertes par famille."""
    groups = {key: [] for key in GROUPING_PATTERNS.keys()}
    groups["other"] = []
    
    for alert in alerts:
        alert_name = alert.get("alert_type", "")
        grouped = False
        
        for group_name, patterns in GROUPING_PATTERNS.items():
            if any(pattern in alert_name for pattern in patterns):
                groups[group_name].append(alert)
                grouped = True
                break
        
        if not grouped:
            groups["other"].append(alert)
    
    return groups


def build_short_message(alerts: List[Dict], group_name: str) -> str:
    """Construire message court depuis un groupe d'alertes."""
    parts = []
    
    for alert in alerts[:3]:  # max 3 éléments
        alert_type = extract_alert_type(alert.get("alert_type", ""))
        short = TERMS_SHORT.get(alert_type, alert_type.lower().replace("_", " "))
        parts.append(short)
    
    # Join unique parts
    unique_parts = []
    for part in parts:
        if part not in unique_parts:
            unique_parts.append(part)
    
    return " + ".join(unique_parts)


def identify_contradictions(alerts: List[Dict]) -> List[str]:
    """Identifier contradictions dans les alertes."""
    contradictions = []
    
    alert_types = [alert.get("alert_type", "") for alert in alerts]
    
    # Node heat vs energy weak
    if any("NODE_HEAT" in t for t in alert_types) and any("ENERGY" in t and "THIN" in t or "DIVERGENT" in t for t in alert_types):
        contradictions.append("node_heat vs energy_faible")
    
    # Release attempt vs energy divergent
    if any("RELEASE" in t for t in alert_types) and any("ENERGY_DIVERGENT" in t for t in alert_types):
        contradictions.append("release vs énergie_opposée")
    
    # Detachment sans relay
    if any("DETACHMENT" in t for t in alert_types) and any("RELAY_MISSING" in t for t in alert_types):
        contradictions.append("détachement sans relay")
    
    return contradictions


def extract_why_watch(alerts: List[Dict]) -> str:
    """Extraire raisons de surveillance."""
    reasons = []
    
    for alert in alerts:
        alert_type = alert.get("alert_type", "")
        
        if "FIRST_DETACHMENT" in alert_type:
            reasons.append("first_detachment")
        if "CLEAN_RELAY" in alert_type:
            reasons.append("clean_relay")
        if "ENERGY_DIVERGENT" in alert_type:
            reasons.append("energy_divergent")
        if "COUNTER_RELEASE" in alert_type:
            reasons.append("counter_release")
        if "NODE_HEAT" in alert_type:
            reasons.append("node_heat")
    
    return " + ".join(list(set(reasons))) if reasons else "scène_active"


def extract_not_confirmed_reason(alerts: List[Dict]) -> Optional[str]:
    """Identifier pourquoi la scène n'est pas confirmée."""
    for alert in alerts:
        alert_type = alert.get("alert_type", "")
        
        if "COUNTER_RELEASE_ATTEMPT" in alert_type:
            return "counter_release sans confirmation"
        if "ENERGY_THIN" in alert_type or "ENERGY_DIVERGENT" in alert_type:
            return "énergie paire insuffisante"
        if "NODE_HEAT_ENERGY_DIVERGENCE" in alert_type:
            return "node chaud mais énergie faible"
        if "RELAY_MISSING" in alert_type:
            return "relay M5 manquant"
    
    return None


def build_main_alert(
    grouped_alerts: Dict[str, List[Dict]],
    symbol: str
) -> Optional[MainAlert]:
    """Construire l'alerte principale depuis les groupes."""
    
    # Priority: detachment_release > energy_divergence > relay_quality > gravity_cluster > other
    priority_groups = [
        "detachment_release",
        "energy_divergence",
        "relay_quality",
        "gravity_cluster",
        "other"
    ]
    
    main_group = None
    main_alerts = []
    
    for group_name in priority_groups:
        if grouped_alerts[group_name]:
            main_group = group_name
            main_alerts = grouped_alerts[group_name]
            break
    
    if not main_alerts:
        return None
    
    # Prendre l'alerte la plus récente
    main_alerts_sorted = sorted(
        main_alerts,
        key=lambda x: compute_age_seconds(x.get("timestamp", "")),
        reverse=False  # plus récent d'abord
    )
    
    primary_alert = main_alerts_sorted[0]
    
    # Extract data
    event_time = primary_alert.get("timestamp", datetime.now(timezone.utc).isoformat())
    age_seconds = compute_age_seconds(event_time)
    freshness = compute_freshness(age_seconds)
    level = primary_alert.get("level", "INFO")
    
    # Build title
    title = build_short_message(main_alerts_sorted[:2], main_group)
    
    # Build message (max 3 lignes)
    message_parts = []
    
    # Line 1: what's happening
    if "detachment_release" in main_group:
        message_parts.append(build_short_message(main_alerts_sorted[:2], main_group))
    elif "energy_divergence" in main_group:
        message_parts.append("Énergie divergente ou faible détectée")
    else:
        message_parts.append(title)
    
    # Line 2: context
    relay_alerts = grouped_alerts.get("relay_quality", [])
    if relay_alerts:
        relay_msg = build_short_message(relay_alerts[:1], "relay_quality")
        message_parts.append(f"Relay: {relay_msg}")
    
    # Line 3: watchpoint
    why_watch = extract_why_watch(main_alerts_sorted)
    not_confirmed = extract_not_confirmed_reason(main_alerts_sorted)
    
    if not_confirmed:
        message_parts.append(f"Non confirmé: {not_confirmed}")
    
    # Join (max 3 lines)
    message = ". ".join(message_parts[:3]) + "."
    
    # Contradictions
    contradictions = identify_contradictions(main_alerts_sorted)
    
    # Source alerts
    source_alerts = [alert.get("alert_type", "") for alert in main_alerts_sorted[:3]]
    
    return MainAlert(
        level=level,
        title=title,
        message=message,
        symbol=symbol,
        event_time=event_time,
        age_seconds=age_seconds,
        freshness=freshness,
        why_watch=why_watch,
        not_confirmed_reason=not_confirmed,
        contradictions=contradictions,
        source_alerts=source_alerts
    )


def build_secondary_alerts(
    grouped_alerts: Dict[str, List[Dict]],
    main_group: Optional[str]
) -> List[SecondaryAlert]:
    """Construire alertes secondaires (autres groupes)."""
    secondary = []
    
    for group_name, alerts in grouped_alerts.items():
        if group_name == main_group or not alerts:
            continue
        
        # Prendre la plus récente du groupe
        alert = sorted(
            alerts,
            key=lambda x: compute_age_seconds(x.get("timestamp", "")),
            reverse=False
        )[0]
        
        age_seconds = compute_age_seconds(alert.get("timestamp", ""))
        freshness = compute_freshness(age_seconds)
        level = alert.get("level", "INFO")
        title = build_short_message([alert], group_name)
        
        secondary.append(SecondaryAlert(
            level=level,
            title=title,
            age_seconds=age_seconds,
            freshness=freshness
        ))
    
    return secondary


def build_summary(main_alert: Optional[MainAlert], secondary_count: int) -> str:
    """Construire résumé final ultra-court."""
    if not main_alert:
        return "Aucune alerte active."
    
    parts = [main_alert.title]
    
    if main_alert.not_confirmed_reason:
        parts.append(f"non confirmé ({main_alert.not_confirmed_reason})")
    
    if secondary_count > 0:
        parts.append(f"{secondary_count} alerte(s) secondaire(s)")
    
    return ". ".join(parts) + "."


# ============================================================================
# MAIN LOGIC
# ============================================================================

def load_behavioral_queue(path: Path) -> List[Dict]:
    """Charger behavioral_alert_queue.json."""
    if not path.exists():
        return []
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data.get("alerts", [])


def load_cockpit_state(path: Path) -> Dict:
    """Charger cockpit_agentic_state_v01.json."""
    if not path.exists():
        return {}
    
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_runtime_status(path: Path) -> Dict:
    """Charger runtime_status.json."""
    if not path.exists():
        return {}
    
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_pipeline_trace(path: Path) -> Dict:
    """Charger pipeline_trace.json."""
    if not path.exists():
        return {}
    
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_dashboard_data(path: Path) -> Dict:
    """Charger dashboard_data.json."""
    if not path.exists():
        return {}
    
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_trader_alert_state(
    behavioral_queue_path: Path,
    cockpit_state_path: Path,
    runtime_status_path: Optional[Path] = None,
    pipeline_trace_path: Optional[Path] = None,
    dashboard_data_path: Optional[Path] = None,
    symbol: str = "GBPUSD"
) -> TraderAlertState:
    """Générer trader alert state depuis tous les runtime files."""
    
    # Load inputs
    behavioral_alerts = load_behavioral_queue(behavioral_queue_path)
    cockpit_state = load_cockpit_state(cockpit_state_path)
    
    # Load optional runtime files
    runtime_status = {}
    pipeline_trace = {}
    dashboard_data = {}
    
    if runtime_status_path:
        runtime_status = load_runtime_status(runtime_status_path)
    if pipeline_trace_path:
        pipeline_trace = load_pipeline_trace(pipeline_trace_path)
    if dashboard_data_path:
        dashboard_data = load_dashboard_data(dashboard_data_path)
    
    # Filter only FRESH/RECENT alerts (< 5 min)
    now = datetime.now(timezone.utc)
    filtered_alerts = []
    
    for alert in behavioral_alerts:
        age = compute_age_seconds(alert.get("timestamp", ""))
        if age < FRESHNESS_RECENT:  # < 5 min
            filtered_alerts.append(alert)
    
    # Group alerts
    grouped = group_related_alerts(filtered_alerts)
    
    # Build main alert
    main_alert = build_main_alert(grouped, symbol)
    
    # Identify main group
    main_group = None
    if main_alert:
        for group_name, alerts in grouped.items():
            if alerts and any(a.get("alert_type", "") in main_alert.source_alerts for a in alerts):
                main_group = group_name
                break
    
    # Build secondary alerts
    secondary_alerts = build_secondary_alerts(grouped, main_group)
    
    # Build summary
    summary = build_summary(main_alert, len(secondary_alerts))
    
    # Meta
    meta = {
        "generated_at": now.isoformat(),
        "symbol": symbol,
        "source": "pf_trader_alert_state",
        "total_behavioral_alerts": len(behavioral_alerts),
        "filtered_alerts": len(filtered_alerts),
        "main_group": main_group,
        "runtime_files_loaded": {
            "runtime_status": runtime_status_path is not None and runtime_status_path.exists(),
            "pipeline_trace": pipeline_trace_path is not None and pipeline_trace_path.exists(),
            "dashboard_data": dashboard_data_path is not None and dashboard_data_path.exists()
        }
    }
    
    # Add runtime context if available
    if runtime_status:
        meta["runtime_status"] = runtime_status.get("status", "UNKNOWN")
    
    if dashboard_data and "main_scene" in dashboard_data:
        meta["dashboard_scene"] = dashboard_data["main_scene"].get("title", "N/A")
    
    return TraderAlertState(
        meta=meta,
        main_alert=main_alert,
        secondary_alerts=secondary_alerts,
        summary=summary
    )


def save_trader_alert_state(state: TraderAlertState, output_path: Path):
    """Sauvegarder trader_alert_state.json."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to dict
    data = {
        "meta": state.meta,
        "main_alert": asdict(state.main_alert) if state.main_alert else None,
        "secondary_alerts": [asdict(a) for a in state.secondary_alerts],
        "summary": state.summary
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Trader Alert State saved: {output_path}")


# ============================================================================
# CLI
# ============================================================================

def main():
    """Main CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Trader Alert State V0.1")
    parser.add_argument("--behavioral", type=str, default="output/behavioral_alert_queue.json",
                        help="Path to behavioral_alert_queue.json")
    parser.add_argument("--cockpit", type=str, default="output/cockpit_agentic_state_v01.json",
                        help="Path to cockpit_agentic_state_v01.json")
    parser.add_argument("--runtime-status", type=str, default="output/runtime_status.json",
                        help="Path to runtime_status.json (optional)")
    parser.add_argument("--pipeline-trace", type=str, default="output/pipeline_trace.json",
                        help="Path to pipeline_trace.json (optional)")
    parser.add_argument("--dashboard-data", type=str, default="dashboard_data.json",
                        help="Path to dashboard_data.json (optional)")
    parser.add_argument("--symbol", type=str, default="GBPUSD",
                        help="Symbol")
    parser.add_argument("--out", type=str, default="output/trader_alert_state.json",
                        help="Output path")
    parser.add_argument("--pretty", action="store_true",
                        help="Pretty print summary")
    
    args = parser.parse_args()
    
    behavioral_path = Path(args.behavioral)
    cockpit_path = Path(args.cockpit)
    runtime_status_path = Path(args.runtime_status) if args.runtime_status else None
    pipeline_trace_path = Path(args.pipeline_trace) if args.pipeline_trace else None
    dashboard_data_path = Path(args.dashboard_data) if args.dashboard_data else None
    output_path = Path(args.out)
    
    # Generate
    state = generate_trader_alert_state(
        behavioral_queue_path=behavioral_path,
        cockpit_state_path=cockpit_path,
        runtime_status_path=runtime_status_path,
        pipeline_trace_path=pipeline_trace_path,
        dashboard_data_path=dashboard_data_path,
        symbol=args.symbol
    )
    
    # Save
    save_trader_alert_state(state, output_path)
    
    # Pretty print
    if args.pretty:
        print("\n" + "="*60)
        print("TRADER ALERT STATE V0.1")
        print("="*60)
        print(f"\nSummary: {state.summary}")
        
        if state.main_alert:
            print(f"\n🔥 MAIN ALERT [{state.main_alert.level}]")
            print(f"   {state.main_alert.title}")
            print(f"   {state.main_alert.message}")
            print(f"   Âge: {state.main_alert.age_seconds}s ({state.main_alert.freshness})")
            
            if state.main_alert.contradictions:
                print(f"   ⚠️ Contradictions: {', '.join(state.main_alert.contradictions)}")
        
        if state.secondary_alerts:
            print(f"\n📋 SECONDARY ALERTS ({len(state.secondary_alerts)})")
            for sec in state.secondary_alerts:
                print(f"   [{sec.level}] {sec.title} ({sec.freshness})")
        
        # Runtime context
        meta = state.meta
        if "runtime_status" in meta:
            print(f"\n🔧 Runtime: {meta['runtime_status']}")
        if "dashboard_scene" in meta:
            print(f"📊 Dashboard: {meta['dashboard_scene']}")
        
        print("\n" + "="*60)


if __name__ == "__main__":
    main()
