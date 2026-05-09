#!/usr/bin/env python3
"""
load_runtime_fixture.py

Charge les 5 fichiers runtime réels de PowerFlow et les analyse.

INPUTS:
- output/runtime_status.json
- output/pipeline_trace.json
- output/behavioral_alert_queue.json
- output/cockpit_agentic_state_v01.json
- dashboard_data.json

OBJECTIF:
Transformer le film runtime en 1 scène trader lisible, datée, fraîche, < 3 lignes.

PHRASE NOYAU:
PowerFlow sait rafraîchir le film.
Il faut le traduire en message trader.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone


def load_json_safe(path: Path) -> Optional[Dict[str, Any]]:
    """Charge un JSON de manière sécurisée."""
    if not path.exists():
        print(f"⚠️  Missing: {path}")
        return None
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading {path}: {e}")
        return None


def analyze_runtime_fixture(base_dir: Path = Path("output")):
    """Analyse les 5 fichiers runtime réels."""
    
    print("="*60)
    print("📦 LOADING RUNTIME FIXTURE")
    print("="*60)
    
    # Load all runtime files
    runtime_status = load_json_safe(base_dir / "runtime_status.json")
    pipeline_trace = load_json_safe(base_dir / "pipeline_trace.json")
    behavioral_queue = load_json_safe(base_dir / "behavioral_alert_queue.json")
    cockpit_state = load_json_safe(base_dir / "cockpit_agentic_state_v01.json")
    dashboard_data = load_json_safe(Path("dashboard_data.json"))
    
    print("\n📊 RUNTIME FILES STATUS:")
    print(f"  runtime_status.json: {'✅' if runtime_status else '❌'}")
    print(f"  pipeline_trace.json: {'✅' if pipeline_trace else '❌'}")
    print(f"  behavioral_alert_queue.json: {'✅' if behavioral_queue else '❌'}")
    print(f"  cockpit_agentic_state_v01.json: {'✅' if cockpit_state else '❌'}")
    print(f"  dashboard_data.json: {'✅' if dashboard_data else '❌'}")
    
    # Extract key info from each
    print("\n" + "="*60)
    print("🎬 RUNTIME FILM ANALYSIS")
    print("="*60)
    
    # 1. Runtime Status
    if runtime_status:
        print("\n🔧 RUNTIME STATUS:")
        print(f"  Generated: {runtime_status.get('meta', {}).get('generated_at', 'N/A')}")
        print(f"  Status: {runtime_status.get('status', 'N/A')}")
        if 'errors' in runtime_status:
            print(f"  Errors: {len(runtime_status['errors'])}")
    
    # 2. Pipeline Trace
    if pipeline_trace:
        print("\n📈 PIPELINE TRACE:")
        print(f"  Generated: {pipeline_trace.get('meta', {}).get('generated_at', 'N/A')}")
        steps = pipeline_trace.get('steps', [])
        print(f"  Steps: {len(steps)}")
        if steps:
            last_step = steps[-1]
            print(f"  Last Step: {last_step.get('name', 'N/A')} ({last_step.get('status', 'N/A')})")
    
    # 3. Behavioral Alert Queue
    if behavioral_queue:
        print("\n🚨 BEHAVIORAL ALERTS:")
        print(f"  Generated: {behavioral_queue.get('meta', {}).get('generated_at', 'N/A')}")
        alerts = behavioral_queue.get('alerts', [])
        print(f"  Total Alerts: {len(alerts)}")
        
        if alerts:
            # Group by level
            hot = [a for a in alerts if a.get('level') == 'HOT']
            watch = [a for a in alerts if a.get('level') == 'WATCH']
            info = [a for a in alerts if a.get('level') == 'INFO']
            
            print(f"  HOT: {len(hot)}")
            print(f"  WATCH: {len(watch)}")
            print(f"  INFO: {len(info)}")
            
            # Show most recent HOT alert
            if hot:
                latest_hot = max(hot, key=lambda x: x.get('timestamp', ''))
                print(f"\n  🔥 Latest HOT Alert:")
                print(f"     Type: {latest_hot.get('alert_type', 'N/A')}")
                print(f"     Time: {latest_hot.get('timestamp', 'N/A')}")
    
    # 4. Cockpit State
    if cockpit_state:
        print("\n🎛️  COCKPIT STATE:")
        print(f"  Generated: {cockpit_state.get('meta', {}).get('generated_at', 'N/A')}")
        
        if 'scene' in cockpit_state:
            scene = cockpit_state['scene']
            print(f"  Scene Dominant: {scene.get('dominant', 'N/A')}")
            print(f"  Gravity: {scene.get('gravity', 'N/A')}")
        
        if 'temporal_nodes' in cockpit_state:
            nodes = cockpit_state['temporal_nodes']
            print(f"  Active Nodes: {nodes.get('active_count', 0)}")
            print(f"  Highest Level: {nodes.get('highest_level', 'N/A')}")
    
    # 5. Dashboard Data
    if dashboard_data:
        print("\n📊 DASHBOARD DATA:")
        print(f"  Generated: {dashboard_data.get('meta', {}).get('generated_at', 'N/A')}")
        
        if 'main_scene' in dashboard_data:
            main_scene = dashboard_data['main_scene']
            print(f"  Main Scene: {main_scene.get('title', 'N/A')}")
    
    print("\n" + "="*60)
    
    return {
        'runtime_status': runtime_status,
        'pipeline_trace': pipeline_trace,
        'behavioral_queue': behavioral_queue,
        'cockpit_state': cockpit_state,
        'dashboard_data': dashboard_data
    }


def extract_trader_scene(fixture: Dict[str, Any]) -> str:
    """
    Extraire LA scène trader principale depuis le runtime fixture.
    
    OBJECTIF: 1 scène < 3 lignes, datée, fraîche.
    """
    
    behavioral = fixture.get('behavioral_queue')
    cockpit = fixture.get('cockpit_state')
    dashboard = fixture.get('dashboard_data')
    
    # Priority: behavioral alerts > cockpit state > dashboard
    
    # 1. Check behavioral alerts
    if behavioral and behavioral.get('alerts'):
        alerts = behavioral['alerts']
        
        # Filter FRESH (< 2 min)
        now = datetime.now(timezone.utc)
        fresh_alerts = []
        
        for alert in alerts:
            timestamp = alert.get('timestamp', '')
            try:
                alert_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                age = (now - alert_time).total_seconds()
                if age < 120:  # < 2 min
                    fresh_alerts.append(alert)
            except:
                pass
        
        # Get HOT alerts
        hot_alerts = [a for a in fresh_alerts if a.get('level') == 'HOT']
        
        if hot_alerts:
            # Take most recent HOT
            latest = max(hot_alerts, key=lambda x: x.get('timestamp', ''))
            alert_type = latest.get('alert_type', '')
            timestamp = latest.get('timestamp', '')
            
            # Build short scene
            if 'DETACHMENT' in alert_type and 'COUNTER_RELEASE' in alert_type:
                scene = f"Détachement M1 + contre-release. Non confirmé. {timestamp}"
            elif 'FIRST_DETACHMENT' in alert_type:
                scene = f"Premier détachement M1. Relay propre. {timestamp}"
            elif 'NODE_HEAT' in alert_type:
                scene = f"Node chaud. Énergie divergente. {timestamp}"
            else:
                scene = f"{alert_type}. {timestamp}"
            
            return scene
    
    # 2. Fallback to cockpit state
    if cockpit and 'scene' in cockpit:
        scene = cockpit['scene']
        dominant = scene.get('dominant', 'N/A')
        timestamp = cockpit.get('meta', {}).get('generated_at', '')
        return f"Scène: {dominant}. {timestamp}"
    
    # 3. Fallback to dashboard
    if dashboard and 'main_scene' in dashboard:
        main_scene = dashboard['main_scene']
        title = main_scene.get('title', 'Aucune scène active')
        timestamp = dashboard.get('meta', {}).get('generated_at', '')
        return f"{title}. {timestamp}"
    
    return "Aucune scène active."


def main():
    """Main."""
    
    # Load fixture
    fixture = analyze_runtime_fixture()
    
    # Extract trader scene
    print("\n" + "="*60)
    print("🎯 TRADER SCENE (< 3 lignes)")
    print("="*60)
    
    scene = extract_trader_scene(fixture)
    
    print(f"\n📌 {scene}\n")
    print("="*60)


if __name__ == "__main__":
    main()
