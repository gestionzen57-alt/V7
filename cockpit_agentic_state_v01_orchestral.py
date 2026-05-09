"""
PowerFlow V6 — Cockpit Agentic State V0.1.4 — ORCHESTRAL INTEGRATED

Mission:
    Build a stable JSON state for the dashboard from the 5 runtime agents:

        DBVisionGuard
        FlowEventExtractor
        SceneNamer
        FractalWindowEngine
        OrchestraGravity (NEW)

Architecture:
    - cockpit_* reads.
    - no DB write.
    - no Telegram.
    - no BUY/SELL.
    - output JSON only.

Output:
    output/cockpit_agentic_state_v01.json
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence
import argparse
import json

from pf_db_vision_guard import analyze_db_vision
from pf_flow_event_extractor import extract_flow_events
from pf_scene_namer import name_scene
from pf_fractal_window_engine import analyze_fractal_window
from pf_flow_event_extractor_v02_extended import extract_flow_events_extended

# ---------------------------------------------------------------------------
# Relational Gravity Bridge — lecture read-only JSON, pas de DB, pas de Telegram
# ---------------------------------------------------------------------------
from pf_relational_gravity_bridge import (
    build_relational_gravity_block,
    relational_gravity_block_to_dict,
)

# ---------------------------------------------------------------------------
# Orchestral Gravity Bridge — NEW V0.1.4
# ---------------------------------------------------------------------------
from pf_orchestral_gravity_v02 import compute_orchestra_state

# ---------------------------------------------------------------------------
# Behavioral Queue Bridge — lecture read-only, pas de DB, pas de Telegram
# ---------------------------------------------------------------------------

DEFAULT_BEHAVIORAL_QUEUE = Path("output") / "behavioral_alert_queue.json"

LEVEL_PRIORITY = {"HOT": 4, "DEGRADED": 3, "WATCH": 2, "INFO": 1}


def _load_behavioral_queue(queue_path: Path) -> Dict[str, Any]:
    """Charge behavioral_alert_queue.json en read-only. Retourne dict vide si absent."""
    if not queue_path.exists():
        return {}
    try:
        with queue_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _build_behavioral_summary(queue: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produit behavioral_summary depuis le contenu de la queue.
    Règle de priorité : HOT > DEGRADED > WATCH > INFO
    """
    behavioral = queue.get("behavioral_alerts", [])
    degraded = queue.get("degraded_alerts", [])
    all_alerts = behavioral + degraded

    if not all_alerts:
        return {
            "behavioral_count": 0,
            "degraded_count": 0,
            "top_alert": None,
            "top_level": None,
            "has_degraded": False,
            "has_hot_behavioral": False,
        }

    # Top alert = priorité la plus haute, puis premier dans la liste
    top = max(
        all_alerts,
        key=lambda a: LEVEL_PRIORITY.get(a.get("level", ""), 0),
    )

    has_hot = any(a.get("level") == "HOT" for a in all_alerts)
    has_degraded = bool(degraded)

    return {
        "behavioral_count": len(behavioral),
        "degraded_count": len(degraded),
        "top_alert": top.get("name"),
        "top_level": top.get("level"),
        "has_degraded": has_degraded,
        "has_hot_behavioral": has_hot,
    }


COCKPIT_AGENTIC_STATE_VERSION = "0.1.4"  # orchestral gravity integrated


def _build_relational_gravity(base_dir: str = ".") -> Dict[str, Any]:
    """
    Lit les JSON Relational Gravity V0.1.1 (fallback V0.1).
    Retourne le bloc prêt pour cockpit_state["relational_gravity"].
    Read-only. Jamais de DB. Jamais de Telegram. Zéro crash.
    """
    try:
        rg_block = build_relational_gravity_block(base_dir=base_dir)
        return relational_gravity_block_to_dict(rg_block)
    except Exception as e:
        return {
            "cross_tf_state": "RELATIONAL_GRAVITY_MISSING",
            "dominant_direction": "UNKNOWN",
            "dominant_leader": "UNKNOWN",
            "dominant_antagonist": "NONE",
            "aligned_tfs": [],
            "counter_tf": None,
            "max_score": 0.0,
            "notes": [f"bridge_error: {e}"],
            "tf_details": {},
        }


def _build_orchestral_gravity(
    db_path: str,
    symbol: str,
    start: str,
    end: str,
    timeframes: List[int],
    avg_bars: int = 3,
) -> Dict[str, Any]:
    """
    Lit orchestral gravity pour TFs données.
    Read-only. No DB write. No Telegram. Zero crash.
    
    Args:
        db_path: chemin powerflow.db
        symbol: GBPUSD
        start: ISO timestamp
        end: ISO timestamp
        timeframes: liste TFs (ex: [1,5,15,30,60])
        avg_bars: moyenne angle sur N dernières barres (default 3)
    
    Returns:
        {
            "timeframes": {
                "1": OrchestraState.to_dict(),
                "5": {...},
                ...
            },
            "latest_tf": 15,
            "latest_state": {...},
            "compression_detected": bool,
            "leader_currency": str,
            "patterns": [str],
            "notes": [str]
        }
    """
    if not timeframes:
        return {
            "state": "ORCHESTRAL_NO_TIMEFRAMES",
            "timeframes": {},
            "latest_state": None,
            "compression_detected": False,
            "notes": ["No timeframes provided for orchestral analysis"],
        }
    
    try:
        # Compute orchestral state par TF
        tf_states = {}
        for tf in sorted(timeframes):
            try:
                state = compute_orchestra_state(
                    db_path=db_path,
                    symbol=symbol,
                    timeframe=tf,
                    start=start,
                    end=end,
                    avg_bars=avg_bars,
                    use_zone_dynamics=True,  # toujours utiliser zone_dynamics si dispo
                )
                if state:
                    tf_states[str(tf)] = state.to_dict()
            except Exception as e:
                tf_states[str(tf)] = {
                    "state": "ORCHESTRAL_TF_ERROR",
                    "error": str(e),
                }
        
        if not tf_states:
            return {
                "state": "ORCHESTRAL_ALL_TF_FAILED",
                "timeframes": {},
                "latest_state": None,
                "compression_detected": False,
                "notes": ["All timeframes failed to compute orchestral state"],
            }
        
        # Latest state = TF le plus élevé disponible (ex: si 1,5,15,60 → prendre 60)
        latest_tf = max(int(k) for k in tf_states.keys() if tf_states[k].get("state") != "ORCHESTRAL_TF_ERROR")
        latest_state = tf_states.get(str(latest_tf), {})
        
        # Extraction quick summary
        compression_detected = any(
            "ORCHESTRAL_COMPRESSION" in state.get("patterns", [])
            for state in tf_states.values()
            if isinstance(state, dict) and "patterns" in state
        )
        
        leader_currency = latest_state.get("leader", {}).get("currency") if latest_state else None
        patterns = latest_state.get("patterns", []) if latest_state else []
        
        return {
            "state": "ORCHESTRAL_ACTIVE",
            "timeframes": tf_states,
            "latest_tf": latest_tf,
            "latest_state": latest_state,
            "compression_detected": compression_detected,
            "leader_currency": leader_currency,
            "patterns": patterns,
            "notes": [],
        }
    
    except Exception as e:
        return {
            "state": "ORCHESTRAL_BRIDGE_ERROR",
            "timeframes": {},
            "latest_state": None,
            "compression_detected": False,
            "notes": [f"orchestral_bridge_error: {type(e).__name__}: {e}"],
        }


def _phase_times(events) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for ev in events:
        out[ev.phase] = {
            "start": ev.start,
            "end": ev.end,
            "timeframe": ev.timeframe,
            "up_block": ev.up_block,
            "down_block": ev.down_block,
            "force_energy": ev.force_energy,
            "price_response": ev.price_response,
            "confidence": ev.confidence,
        }
    return out


def _compact_agent_summary(vision, extraction, scene, fractal) -> Dict[str, Any]:
    return {
        "vision_state": vision.vision_state,
        "live_state": vision.live_state,
        "schema_state": vision.schema_state,
        "source_table": vision.source_table,
        "scene": scene.scene_name,
        "window_state": scene.window_state,
        "dominant_phase": scene.dominant_phase,
        "next_watch": scene.next_watch,
        "fractal_state": fractal.fractal_state,
        "temporal_state": fractal.temporal_state,
        "htf_relation": fractal.htf_relation,
        "higher_story": fractal.higher_story_state,
        "contradiction": fractal.contradiction_state,
        "flags": fractal.flags,
    }


def build_cockpit_agentic_state(
    db_path: str,
    symbol: str,
    start: str,
    end: str,
    ltf_timeframes: Iterable[int] = (1, 5, 15),
    htf_timeframes: Iterable[int] = (30, 60, 240),
    orchestral_timeframes: Optional[Iterable[int]] = None,
    orchestral_avg_bars: int = 3,
    visual_htf_story: str = "none",
    behavioral_queue_path: Path = DEFAULT_BEHAVIORAL_QUEUE,
) -> Dict[str, Any]:
    ltf_tfs = [int(tf) for tf in ltf_timeframes]
    htf_tfs = [int(tf) for tf in htf_timeframes]
    all_tfs = sorted(set(ltf_tfs + htf_tfs))
    
    # Orchestral TFs : si None, utilise LTF + 30 par défaut (comme demandé)
    if orchestral_timeframes is None:
        orch_tfs = ltf_tfs + [30]
    else:
        orch_tfs = [int(tf) for tf in orchestral_timeframes]

    generated_at = datetime.now(timezone.utc).isoformat()

    vision = analyze_db_vision(
        db_path=db_path,
        symbol=symbol,
        timeframes=all_tfs,
        recent_minutes=60,
        gap_threshold_minutes=180,
    )

    extraction = extract_flow_events(
        db_path=db_path,
        symbol=symbol,
        start=start,
        end=end,
        timeframes=ltf_tfs,
    )

    scene = name_scene(extraction)

    fractal = analyze_fractal_window(
        db_path=db_path,
        symbol=symbol,
        start=start,
        end=end,
        ltf_timeframes=ltf_tfs,
        htf_timeframes=htf_tfs,
        visual_htf_story=visual_htf_story,
    )

    try:
        extended = extract_flow_events_extended(
            db_path=db_path,
            symbol=symbol,
            start=start,
            end=end,
            timeframes=ltf_tfs,
            source_table="force_snapshots_v2",
            fallback_to_legacy=False,
        )
        extended_state = extended.to_dict()
    except Exception as exc:
        extended_state = {
            "mode": "EXTENDED_V02_ERROR",
            "extended_schema_state": "ERROR",
            "extended_rows_loaded": {},
            "extended_flags": [],
            "extended_summary": f"EXTENDED ERROR: {type(exc).__name__}: {exc}",
            "extended_event_metrics": [],
            "warnings": [str(exc)],
        }

    agent_summary = _compact_agent_summary(vision, extraction, scene, fractal)
    agent_summary["extended_summary"] = extended_state.get("extended_summary")
    agent_summary["extended_flags"] = extended_state.get("extended_flags", [])
    agent_summary["extended_schema_state"] = extended_state.get("extended_schema_state")

    # Minimal dashboard status logic.
    if vision.vision_state == "DATA_BLIND":
        cockpit_status = "DATA_BLIND"
    elif "LTF_BIRTH" in fractal.fractal_state or scene.scene_name != "DATA_PARTIAL_REVIEW_REQUIRED":
        cockpit_status = "AGENTIC_WINDOW_ACTIVE"
    elif vision.vision_state == "DATA_PARTIAL":
        cockpit_status = "DATA_PARTIAL_AGENTIC_READY"
    else:
        cockpit_status = "AGENTIC_READY"

    if fractal.temporal_state == "TEMPORAL_ELASTICITY_FIELD":
        headline = "FENÊTRE FRACTALE — temps compressé puis étiré"
    elif scene.scene_name != "DATA_PARTIAL_REVIEW_REQUIRED":
        headline = f"SCÈNE ACTIVE — {scene.scene_name}"
    else:
        headline = "AGENTS PRÊTS — aucune scène majeure"

    # ------------------------------------------------------------------
    # Behavioral Queue Bridge — read-only, no DB, no Telegram
    # ------------------------------------------------------------------
    behavioral_queue = _load_behavioral_queue(behavioral_queue_path)
    behavioral_summary = _build_behavioral_summary(behavioral_queue)

    # next_watch_enriched : fusion next_watch fractal/scene + enrichissement behavioral
    # L'ancien next_watch (fractal + scene) est préservé en premier.
    _original_next_watch: List[str] = []
    if fractal.next_watch:
        _original_next_watch.append(fractal.next_watch)
    if scene.next_watch and scene.next_watch != fractal.next_watch:
        _original_next_watch.append(scene.next_watch)
    _behavioral_next_watch: List[str] = behavioral_queue.get("next_watch_enriched", [])
    # Dédupliquer en conservant l'ordre : original d'abord, enrichissement ensuite
    _seen_nw: set = set()
    next_watch_enriched: List[str] = []
    for _nw in _original_next_watch + _behavioral_next_watch:
        if _nw not in _seen_nw:
            _seen_nw.add(_nw)
            next_watch_enriched.append(_nw)

    # ------------------------------------------------------------------
    # Orchestral Gravity Bridge — NEW V0.1.4
    # ------------------------------------------------------------------
    orchestral_gravity = _build_orchestral_gravity(
        db_path=db_path,
        symbol=symbol,
        start=start,
        end=end,
        timeframes=orch_tfs,
        avg_bars=orchestral_avg_bars,
    )

    return {
        "version": COCKPIT_AGENTIC_STATE_VERSION,
        "generated_at_utc": generated_at,
        "symbol": symbol,
        "window": {
            "start": start,
            "end": end,
            "ltf_timeframes": ltf_tfs,
            "htf_timeframes": htf_tfs,
            "orchestral_timeframes": orch_tfs,
            "visual_htf_story": visual_htf_story,
        },
        "cockpit_status": cockpit_status,
        "headline": headline,
        "agent_summary": agent_summary,
        "db_vision": {
            "schema_state": vision.schema_state,
            "live_state": vision.live_state,
            "vision_state": vision.vision_state,
            "source_table": vision.source_table,
            "can_detect_ltf_birth": vision.can_detect_ltf_birth,
            "can_validate_htf_gravity": vision.can_validate_htf_gravity,
            "timeframes": [asdict(tf) for tf in vision.timeframes],
            "gaps": [asdict(gap) for gap in vision.gaps],
            "notes": vision.notes,
        },
        "flow_events": {
            "mode": extraction.mode,
            "source_table": extraction.source_table,
            "rows_loaded": extraction.rows_loaded,
            "phases": _phase_times(extraction.events),
            "events": [asdict(ev) for ev in extraction.events],
            "warnings": extraction.warnings,
        },
        "scene": scene.to_dict(),
        "fractal": fractal.to_dict(),
        "extended": extended_state,
        # ------------------------------------------------------------------
        # Behavioral Queue Bridge — champs injectés depuis behavioral_alert_queue.json
        # ------------------------------------------------------------------
        "behavioral_alerts": behavioral_queue.get("behavioral_alerts", []),
        "degraded_alerts": behavioral_queue.get("degraded_alerts", []),
        "film_steps": behavioral_queue.get("film_steps", []),
        "next_watch_enriched": next_watch_enriched,
        "behavioral_summary": behavioral_summary,
        # ------------------------------------------------------------------
        # Relational Gravity Bridge — read-only JSON, no DB, no Telegram
        # ------------------------------------------------------------------
        "relational_gravity": _build_relational_gravity(base_dir="."),
        # ------------------------------------------------------------------
        # Orchestral Gravity Bridge — NEW V0.1.4
        # ------------------------------------------------------------------
        "orchestral_gravity": orchestral_gravity,
        # ------------------------------------------------------------------
        "dashboard_cards": [
            {
                "title": "VISION DB",
                "status": vision.vision_state,
                "line": f"{vision.live_state} | {vision.schema_state} | source={vision.source_table}",
            },
            {
                "title": "SCÈNE",
                "status": scene.scene_name,
                "line": scene.one_liner,
            },
            {
                "title": "FRACTALITÉ",
                "status": fractal.fractal_state,
                "line": fractal.summary,
            },
            {
                "title": "EXTENDED V0.2",
                "status": extended_state.get("extended_summary", "EXTENDED_UNKNOWN"),
                "line": " | ".join(extended_state.get("extended_flags", [])[:6]) if extended_state.get("extended_flags") else "no extended flags",
            },
            {
                "title": "ORCHESTRAL GRAVITY",
                "status": orchestral_gravity.get("state", "UNKNOWN"),
                "line": f"Leader: {orchestral_gravity.get('leader_currency') or 'NONE'} | Compression: {orchestral_gravity.get('compression_detected')} | Patterns: {len(orchestral_gravity.get('patterns', []))}",
            },
            {
                "title": "NEXT WATCH",
                "status": fractal.next_watch,
                "line": f"scene={scene.next_watch} | fractal={fractal.next_watch}",
            },
        ],
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PowerFlow V6 Cockpit Agentic State V0.1.4 — Orchestral Integrated")
    parser.add_argument("--db", required=True)
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--ltf-timeframes", default="1,5,15")
    parser.add_argument("--htf-timeframes", default="30,60,240")
    parser.add_argument(
        "--orchestral-tfs",
        default=None,
        help="Orchestral timeframes (default: LTF + 30). Ex: 1,5,15,30,60 or 60,240,1440,10080 for HTF strategy",
    )
    parser.add_argument(
        "--orchestral-avg-bars",
        type=int,
        default=3,
        help="Moyenne angle orchestral sur N barres (default: 3)",
    )
    parser.add_argument("--visual-htf-story", default="none", choices=["none", "pending", "review", "confirmed", "yes", "true", "1"])
    parser.add_argument(
        "--behavioral-queue",
        default=str(DEFAULT_BEHAVIORAL_QUEUE),
        help="Path to behavioral_alert_queue.json (default: output/behavioral_alert_queue.json)",
    )
    parser.add_argument("--out", default="output/cockpit_agentic_state_v01.json")
    parser.add_argument("--pretty", action="store_true")

    args = parser.parse_args(argv)

    ltf_tfs = [int(x.strip()) for x in args.ltf_timeframes.split(",") if x.strip()]
    htf_tfs = [int(x.strip()) for x in args.htf_timeframes.split(",") if x.strip()]
    
    orch_tfs = None
    if args.orchestral_tfs:
        orch_tfs = [int(x.strip()) for x in args.orchestral_tfs.split(",") if x.strip()]

    state = build_cockpit_agentic_state(
        db_path=args.db,
        symbol=args.symbol,
        start=args.start,
        end=args.end,
        ltf_timeframes=ltf_tfs,
        htf_timeframes=htf_tfs,
        orchestral_timeframes=orch_tfs,
        orchestral_avg_bars=args.orchestral_avg_bars,
        visual_htf_story=args.visual_htf_story,
        behavioral_queue_path=Path(args.behavioral_queue),
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    indent = 2 if args.pretty else None
    out_path.write_text(json.dumps(state, ensure_ascii=False, indent=indent), encoding="utf-8")

    print(f"✅ COCKPIT_AGENTIC_STATE_WRITTEN: {out_path}")
    print(f"VERSION: {state['version']}")
    print(f"STATUS: {state['cockpit_status']}")
    print(f"HEADLINE: {state['headline']}")
    print(f"SCENE: {state['agent_summary']['scene']}")
    print(f"FRACTAL: {state['agent_summary']['fractal_state']}")
    print(f"EXTENDED: {state['agent_summary'].get('extended_summary')}")
    print(f"ORCHESTRAL: {state['orchestral_gravity']['state']} | Leader: {state['orchestral_gravity'].get('leader_currency')}")
    print(f"NEXT: {state['agent_summary']['next_watch']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
