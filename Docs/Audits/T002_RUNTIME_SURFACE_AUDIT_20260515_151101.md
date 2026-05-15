# T002 Runtime Surface Audit

Date UTC: 2026-05-15T15:11:01Z
Repo: C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT

## Executive finding

- Core/engine.py exposes process_tick: YES
- process_tick signature: async def process_tick(tick: Tick, prev: Tick, brain: Brain, send_alert):
- Hard runtime caller count: 7
- Main hard caller: .t002_runtime_surface_audit.py:17
- Recommendation: T002 must start as an adapter/extraction plan, not a blind refactor.

## Hard runtime callers

- .t002_runtime_surface_audit.py:17 | "from engine import process_tick",
- .t002_runtime_surface_audit.py:18 | "from engine import",
- .t002_runtime_surface_audit.py:19 | "import engine",
- .t002_runtime_surface_audit.py:20 | "engine.process_tick",
- .t002_runtime_surface_audit.py:253 | add("2. Add a small contract test that imports engine.process_tick and records its signature.")
- .t002_runtime_surface_audit.py:284 | hard_pats = {"from engine import process_tick", "from engine import", "import engine", "engine.process_tick"}
- Core/capture_bridge.py:299 | from engine import process_tick

## Engine metrics

- Lines: 1227
- Imports: 11
- Functions: 43
- Classes: 0
- Main blocks: 0

## Functions

- line 93-104 | def _pfv7_utc_iso(dt) -> str:
- line 107-110 | def _pfv7_symbol_dir(symbol: str) -> str:
- line 113-114 | def _pfv7_behavioral_jsonl_path(symbol: str) -> str:
- line 117-118 | def _pfv7_timecomp_jsonl_path(symbol: str) -> str:
- line 121-137 | def _pfv7_event_time_risks(event_at: str, detected_at: str) -> list[str]:
- line 140-150 | def _pfv7_signal_layer(signal_type: str) -> str:
- line 153-170 | def _pfv7_event_role(signal_type: str) -> str:
- line 173-187 | def _pfv7_pair_bias_from_signal(sig) -> str:
- line 190-192 | def _pfv7_write_jsonl(path: str, record: dict) -> None:
- line 195-211 | def _write_legacy_behavioral_event(record: dict) -> dict:
- line 214-247 | def _write_legacy_behavioral_signal(sig, htf=None, tick=None) -> dict:
- line 250-256 | def _pfv7_timecomp_event_type(tc_ev: dict) -> str:
- line 259-271 | def _pfv7_timecomp_direction(tc_ev: dict) -> str:
- line 274-321 | def _write_legacy_timecomp_event_v7bus(symbol: str, tf: int, tf_label: str, tick: Tick, tc_ev: dict) -> dict:
- line 327-341 | def _utc_iso(dt) -> str:
- line 343-349 | def _legacy_timecomp_event_type(tc_ev: dict) -> str:
- line 351-363 | def _legacy_timecomp_direction(tc_ev: dict) -> str:
- line 365-368 | def _legacy_timecomp_jsonl_path(symbol: str) -> str:
- line 370-408 | def _write_legacy_timecomp_event(symbol: str, tf: int, tf_label: str, tick: Tick, tc_ev: dict) -> dict:
- line 414-432 | def signal_to_db_dict(sig) -> dict:
- line 434-446 | def htf_to_db_dict(htf) -> dict:
- line 448-460 | def persist_signal(sig, htf) -> None:
- line 462-463 | def log_flow_regime(htf, sig) -> None:
- line 468-485 | def check_volume(tick: Tick, uid: str) -> str:
- line 490-529 | def build_htf_context(pair, tf, dev_a, dev_b, brain) -> HTFContext:
- line 534-542 | def score_signal(signal_type, tf, volume_badge, htf_bonus, spread_ok) -> tuple:
- line 547-548 | def can_alert(key):
- line 550-551 | def mark_alerted(key):
- line 561-565 | def register_cross(pair, tf, strong, weak):
- line 567-593 | def detect_convergence(pair, tf, strong, weak, htf):
- line 598-599 | def get_compression_band(tick: Tick) -> float:
- line 601-639 | def detect_compression(tick: Tick, uid: str):
- line 641-674 | def detect_compression_squeeze(tick: Tick, prev: Tick, uid: str):
- line 681-743 | def detect_cross(tick: Tick, prev: Tick, uid: str):
- line 748-762 | def detect_slingshot(tick: Tick, prev: Tick, uid: str):
- line 771-790 | def detect_approach(tick: Tick, prev: Tick, uid: str):
- line 795-815 | def detect_zone_battle(tick: Tick, prev: Tick, uid: str):
- line 825-826 | def _pip_size(symbol: str) -> float:
- line 828-831 | def _time_comp_band(tick: Tick) -> float:
- line 833-870 | def detect_time_compression(tick: Tick, uid: str):
- line 875-891 | def build_note(signal_type, tick, htf, conv) -> str:
- line 896-1178 | async def process_tick(tick: Tick, prev: Tick, brain: Brain, send_alert):
- line 1184-1227 | async def process_temporal_nodes_cycle(symbols=None, db_path="powerflow.db"):

## Classes

- None

## Imports

- line 13 | import time
- line 14 | import os
- line 15 | import json
- line 16 | from datetime import datetime, timezone
- line 17 | from collections import deque, defaultdict
- line 18 | from models import Tick, HTFContext, Signal, Brain
- line 19 | from system_config import HTF_RADAR_ENABLED, VOLUME_FILTER_ENABLED, VOLUME_SPIKE_RATIO, VOLUME_SPIKE_MIN_TICKS, MAX_SPREAD, ANTISPAM_SECONDS, ALERT_CROSS_BASIC, ALERT_SUPER_SWITCH, ALERT_FAKEOUT, ALERT_SNIPER_REVERSAL, ALERT_CONVERGENCE, ALERT_SLINGSHOT, ALERT_EXTREME_LEVELS, ALERT_KISS_REJECT, ALERT_COMPRESSION, ALERT_COMPRESSION_SQUEEZE, DEBUG_CROSS, DEBUG_CONVERGENCE, TIMEFRAMES, get_level_high, get_level_low, get_kiss_frolement, get_kiss_force_rejet, get_fakeout_delay, get_fakeout_gap, get_marge_croisement, COMPRESSION_THRESHOLD, COMPRESSION_MIN_BARS, LIBERATION_THRESHOLD, LIBERATION_MAX_BARS, PENTE_THRESHOLD, CROSS_MIN_DELTA, LOCK_DOMINANT_MIN, LOCK_OTHERS_MAX, LOCK_MIN_BARS
- line 40 | from db import init_db, log_signal
- line 44 | from pf_temporal_nodes import get_temporal_nodes_for_engine
- line 45 | from engine_temporal_nodes import process_temporal_nodes_for_engine
- line 46 | from telegram_v6 import send_temporal_node_alert

## Main block

- None

## Signal lines in Core/engine.py

- line 7 | force | #  - get_level_high/low(tf), get_kiss_frolement(tf), get_kiss_force_rejet(tf)
- line 18 | tick | from models import Tick, HTFContext, Signal, Brain
- line 21 | tick | VOLUME_FILTER_ENABLED, VOLUME_SPIKE_RATIO, VOLUME_SPIKE_MIN_TICKS,
- line 23 | alert | ALERT_CROSS_BASIC, ALERT_SUPER_SWITCH,
- line 24 | alert | ALERT_FAKEOUT, ALERT_SNIPER_REVERSAL,
- line 25 | alert | ALERT_CONVERGENCE, ALERT_SLINGSHOT,
- line 26 | alert | ALERT_EXTREME_LEVELS, ALERT_KISS_REJECT,
- line 27 | alert | ALERT_COMPRESSION, ALERT_COMPRESSION_SQUEEZE,
- line 31 | force | get_kiss_frolement, get_kiss_force_rejet,
- line 46 | alert | from telegram_v6 import send_temporal_node_alert
- line 91 | behavioral | # LEGACY BEHAVIORAL BUS V7
- line 113 | Path( | def _pfv7_behavioral_jsonl_path(symbol: str) -> str:
- line 114 | behavioral | return os.path.join(_pfv7_symbol_dir(symbol), "legacy_behavioral_events.jsonl")
- line 117 | Path( | def _pfv7_timecomp_jsonl_path(symbol: str) -> str:
- line 167 | force | "SUPER_SWITCH": "FORCE_SWITCH",
- line 191 | open( | with open(path, "a", encoding="utf-8") as f:
- line 192 | json.dump | f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
- line 195 | behavioral | def _write_legacy_behavioral_event(record: dict) -> dict:
- line 196 | behavioral | """Append one V7 legacy behavioral proof record."""
- line 207 | behavioral | record.setdefault("method", "LEGACY_BEHAVIORAL_BUS_V7A")
- line 208 | Path( | _pfv7_write_jsonl(_pfv7_behavioral_jsonl_path(symbol), record)
- line 210 | behavioral | print(f"[engine] legacy behavioral bus ignored: {exc}")
- line 214 | behavioral | def _write_legacy_behavioral_signal(sig, htf=None, tick=None) -> dict:
- line 215 | alert | """Mirror an existing legacy Signal into V7 JSONL. Does not affect alert flow."""
- line 217 | tick | event_at = _pfv7_utc_iso(getattr(sig, "timestamp", None) or getattr(tick, "timestamp", None))
- line 219 | tick | symbol = str(getattr(sig, "symbol", getattr(tick, "symbol", "UNKNOWN"))).upper()
- line 220 | tick | tf = int(getattr(sig, "timeframe", getattr(tick, "timeframe", 0)) or 0)
- line 224 | behavioral | "method": "LEGACY_BEHAVIORAL_BUS_V7A",
- line 236 | tick | "price": getattr(sig, "price", None) or getattr(tick, "bid", None),
- line 247 | behavioral | return _write_legacy_behavioral_event(record)
- line 274 | bus | def _write_legacy_timecomp_event_v7bus(symbol: str, tf: int, tf_label: str, tick: Tick, tc_ev: dict) -> dict:
- line 275 | behavioral | """Write TIME-COMP into both dedicated temporal JSONL and common behavioral bus."""
- line 276 | tick | event_at = _pfv7_utc_iso(getattr(tick, "timestamp", None))
- line 301 | tick | "ticks": tc_ev.get("ticks"),
- line 307 | Path( | _pfv7_write_jsonl(_pfv7_timecomp_jsonl_path(symbol), temporal)
- line 311 | behavioral | behavioral = dict(temporal)
- line 312 | behavioral | behavioral.update({
- line 313 | behavioral | "method": "LEGACY_BEHAVIORAL_BUS_V7A",
- line 318 | tick | "note": f"TIME-COMP {phase} {tf_label} ticks={tc_ev.get('ticks')}",
- line 320 | behavioral | _write_legacy_behavioral_event(behavioral)
- line 365 | Path( | def _legacy_timecomp_jsonl_path(symbol: str) -> str:
- line 370 | tick | def _write_legacy_timecomp_event(symbol: str, tf: int, tf_label: str, tick: Tick, tc_ev: dict) -> dict:
- line 376 | tick | event_at = _utc_iso(getattr(tick, "timestamp", None))
- line 399 | tick | "ticks": tc_ev.get("ticks"),
- line 405 | Path( | path = _legacy_timecomp_jsonl_path(symbol)
- line 406 | open( | with open(path, "a", encoding="utf-8") as f:
- line 407 | json.dump | f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
- line 468 | tick | def check_volume(tick: Tick, uid: str) -> str:
- line 471 | tick | vol_now = getattr(tick, "volume", 0)
- line 478 | tick | if vol_now > avg * VOLUME_SPIKE_RATIO and vol_now > VOLUME_SPIKE_MIN_TICKS:
- line 547 | alert | def can_alert(key):
- line 550 | alert | def mark_alerted(key):
- line 598 | tick | def get_compression_band(tick: Tick) -> float:
- line 599 | tick | return COMPRESSION_THRESHOLD.get(tick.timeframe, 13.0)
- line 601 | tick | def detect_compression(tick: Tick, uid: str):
- line 603 | tick | band     = get_compression_band(tick)
- line 604 | tick | min_bars = COMPRESSION_MIN_BARS.get(tick.timeframe, 3)
- line 607 | tick | for dev, val in [(tick.dev_a, tick.val_a), (tick.dev_b, tick.val_b)]:
- line 610 | tick | k_ticks  = f"{uid}_{dev}_comp_ticks"
- line 614 | tick | ticks    = compression_states.get(k_ticks, 0)
- line 617 | tick | compression_states.update({k_state:"WATCHING",k_center:val,k_ticks:1})
- line 621 | tick | ticks += 1
- line 622 | tick | compression_states[k_ticks] = ticks
- line 625 | tick | if ticks >= min_bars and state == "WATCHING":
- line 631 | tick | "center":round(center,1),"band":round(band,2),"ticks":ticks})
- line 637 | tick | compression_states.update({k_state:"WATCHING",k_center:val,k_ticks:1})
- line 641 | tick | def detect_compression_squeeze(tick: Tick, prev: Tick, uid: str):
- line 643 | tick | squeeze_min_ticks    = 2
- line 648 | tick | (tick.dev_a, tick.val_a, prev.val_a, tick.dev_b, tick.val_b, prev.val_b),
- line 649 | tick | (tick.dev_b, tick.val_b, prev.val_b, tick.dev_a, tick.val_a, prev.val_a),
- line 654 | tick | squeeze_states[f"{uid}_{comp_dev}_sq_ticks"] = 0
- line 657 | tick | gap_shrinks  = tick.gap < prev.gap
- line 659 | tick | sq_key = f"{uid}_{comp_dev}_sq_ticks"
- line 661 | tick | sq_ticks = squeeze_states.get(sq_key, 0) + 1
- line 662 | tick | squeeze_states[sq_key] = sq_ticks
- line 663 | tick | if sq_ticks >= squeeze_min_ticks:
- line 670 | tick | "gap_prev":round(prev.gap,1),"gap_now":round(tick.gap,1),
- line 671 | tick | "ticks":squeeze_min_ticks}
- line 673 | tick | squeeze_states[f"{uid}_{comp_dev}_sq_ticks"] = 0
- line 681 | tick | def detect_cross(tick: Tick, prev: Tick, uid: str):
- line 682 | tick | tf   = tick.timeframe
- line 683 | tick | state_now  = "A_DOM" if tick.val_a >= tick.val_b else "B_DOM"
- line 688 | force | kiss_force_rejet  = get_kiss_force_rejet(tf)
- line 694 | tick | cur_gap  = tick.gap
- line 701 | tick | f"now={state_now}({tick.val_a:.1f}/{tick.val_b:.1f})")
- line 706 | force | if cur_gap > kiss_frolement + kiss_force_rejet + KISS_RESET_BUFFER:
- line 710 | force | cond_explosion = gap_delta >= kiss_force_rejet
- line 717 | force | f"(+{gap_delta:.1f}) | frolement≤{kiss_frolement:.1f} force≥{kiss_force_rejet:.1f}")
- line 731 | tick | tick_strong = max(tick.val_a, tick.val_b)
- line 738 | tick | if prev_strong < lvl_survente_debut and tick_strong > 55:
- line 740 | tick | if prev_strong > lvl_surcht_debut   and tick_strong < 45:
- line 748 | tick | def detect_slingshot(tick: Tick, prev: Tick, uid: str):
- line 750 | tick | v_a  = tick.val_a - prev.val_a
- line 751 | tick | v_b  = tick.val_b - prev.val_b
- line 771 | tick | def detect_approach(tick: Tick, prev: Tick, uid: str):
- line 772 | tick | if tick.gap > APPROACH_GAP_CANCEL:
- line 774 | tick | if tick.val_a >= tick.val_b:
- line 775 | tick | challenger, ch_now, ch_prv = tick.dev_b, tick.val_b, prev.val_b
- line 776 | tick | dominant,   dom_val       = tick.dev_a, tick.val_a
- line 778 | tick | challenger, ch_now, ch_prv = tick.dev_a, tick.val_a, prev.val_a
- line 779 | tick | dominant,   dom_val       = tick.dev_b, tick.val_b
- line 781 | tick | if momentum < APPROACH_MIN_MOMENTUM or tick.gap > APPROACH_GAP_TRIGGER: return None
- line 784 | tick | lvl_low = get_level_low(tick.timeframe)
- line 787 | tick | "ts_start":time.time(),"ticks":1}
- line 788 | tick | return {"challenger":challenger,"dominant":dominant,"gap":round(tick.gap,1),
- line 795 | tick | def detect_zone_battle(tick: Tick, prev: Tick, uid: str):
- line 796 | tick | if tick.timeframe not in (15, 30, 60, 240): return None
- line 798 | tick | lvl_high = get_level_high(tick.timeframe)
- line 799 | tick | lvl_low  = get_level_low(tick.timeframe)
- line 801 | tick | if   tick.val_b >= lvl_high and prev.val_b < lvl_high:
- line 802 | tick | result = {"actor":tick.dev_b,"opponent":tick.dev_a,"zone":"HAUTE",
- line 803 | tick | "val_actor":round(tick.val_b,1),"val_opp":round(tick.val_a,1),"direction":"surchauffe"}
- line 804 | tick | elif tick.val_a >= lvl_high and prev.val_a < lvl_high:
- line 805 | tick | result = {"actor":tick.dev_a,"opponent":tick.dev_b,"zone":"HAUTE",
- line 806 | tick | "val_actor":round(tick.val_a,1),"val_opp":round(tick.val_b,1),"direction":"surchauffe"}
- line 807 | tick | elif tick.val_b <= lvl_low and prev.val_b > lvl_low:
- line 808 | tick | result = {"actor":tick.dev_b,"opponent":tick.dev_a,"zone":"BASSE",
- line 809 | tick | "val_actor":round(tick.val_b,1),"val_opp":round(tick.val_a,1),"direction":"survente"}
- line 810 | tick | elif tick.val_a <= lvl_low and prev.val_a > lvl_low:
- line 811 | tick | result = {"actor":tick.dev_a,"opponent":tick.dev_b,"zone":"BASSE",
- Truncated: 109 more signal lines

## Reference scan

- .t002_runtime_surface_audit.py:17 | from engine import process_tick | "from engine import process_tick",
- .t002_runtime_surface_audit.py:18 | from engine import | "from engine import",
- .t002_runtime_surface_audit.py:19 | import engine | "import engine",
- .t002_runtime_surface_audit.py:20 | engine.process_tick | "engine.process_tick",
- .t002_runtime_surface_audit.py:21 | process_tick( | "process_tick(",
- .t002_runtime_surface_audit.py:22 | engine.py | "engine.py",
- .t002_runtime_surface_audit.py:23 | scheduler_powerflow.py | "scheduler_powerflow.py",
- .t002_runtime_surface_audit.py:24 | scheduler_powerflow_turbo_wrapper.py | "scheduler_powerflow_turbo_wrapper.py",
- .t002_runtime_surface_audit.py:163 | engine.py | add("- Core/engine.py exposes process_tick: YES")
- .t002_runtime_surface_audit.py:166 | engine.py | add("- Core/engine.py exposes process_tick: NO")
- .t002_runtime_surface_audit.py:221 | engine.py | add("## Signal lines in Core/engine.py")
- .t002_runtime_surface_audit.py:240 | engine.py | add("- PASS py_compile Core/engine.py")
- .t002_runtime_surface_audit.py:242 | engine.py | add("- FAIL py_compile Core/engine.py")
- .t002_runtime_surface_audit.py:248 | engine.py | add("T002 should be renamed from pf_engine.py refactor to Core/engine.py legacy boundary audit and extraction plan.")
- .t002_runtime_surface_audit.py:253 | engine.process_tick | add("2. Add a small contract test that imports engine.process_tick and records its signature.")
- .t002_runtime_surface_audit.py:256 | engine.py | add("5. Keep engine.py as compatibility shell until capture_bridge.py is intentionally migrated.")
- .t002_runtime_surface_audit.py:261 | engine.py | add("- Risk of hidden side effects if engine.py writes DB/output/bus during tick processing.")
- .t002_runtime_surface_audit.py:278 | engine.py | engine_path = repo / "Core" / "engine.py"
- .t002_runtime_surface_audit.py:284 | from engine import process_tick | hard_pats = {"from engine import process_tick", "from engine import", "import engine", "engine.process_tick"}
- .t002_runtime_surface_audit.py:285 | engine.py | hard_callers = [r for r in refs if r["pattern"] in hard_pats and r["file"] != "Core/engine.py"]
- semantic_audit_gravity_zones_v72.py:37 | engine.py | "Core/pf_memory_engine.py",
- Core/capture_bridge.py:90 | engine.py | # (le filtre métier est dans engine.py)
- Core/capture_bridge.py:299 | from engine import process_tick | from engine import process_tick
- Core/capture_bridge.py:306 | process_tick( | await process_tick(tick, prev, brain, dummy_send_alert)
- Core/engine.py:2 | engine.py | # PowerFlow V5 — engine.py
- Core/engine.py:896 | process_tick( | async def process_tick(tick: Tick, prev: Tick, brain: Brain, send_alert):
- Core/engine_temporal_nodes.py:229 | engine.py | # ENGINE ORCHESTRATION — Intégration au cycle engine.py
- Core/engine_temporal_nodes.py:233 | engine.py | """Orchestrateur pour intégration dans engine.py."""
- Core/engine_temporal_nodes.py:276 | engine.py | # HELPER FUNCTIONS — Pour appels depuis engine.py
- Core/engine_temporal_nodes.py:286 | engine.py | Fonction wrapper pour appeler depuis engine.py.
- Core/engine_temporal_nodes.py:331 | engine.py | # INTÉGRATION SIMPLE DANS engine.py — Code à copier
- Core/engine_temporal_nodes.py:335 | engine.py | EXEMPLE D'UTILISATION DANS engine.py:
- Core/engine_temporal_nodes.py:388 | engine.py | print("Import this in your engine.py to use.")
- Core/patch_cross_symbol_future_import_fix_v737d.py:24 | scheduler_powerflow.py | # Backward compatibility: scheduler_powerflow.py still passes --symbols.
- Core/patch_cross_symbol_symbols_compat_v737d.py:15 | scheduler_powerflow.py | # Backward compatibility: scheduler_powerflow.py still passes --symbols.
- Core/patch_engine_legacy_behavioral_bus_v7.py:4 | engine.py | Patch PowerFlow legacy engine.py so fast V5 alerts are mirrored into a V7-readable JSONL bus.
- Core/patch_engine_legacy_behavioral_bus_v7.py:324 | engine.py | parser.add_argument("--engine", default="engine.py")
- Core/patch_engine_timecomp_v7_fix.py:135 | engine.py | print("[OK] engine.py already patched")
- Core/patch_engine_timecomp_v7_fix.py:161 | engine.py | parser.add_argument("--engine", default="engine.py")
- Core/patch_scheduler_perception_spine_v76_fix.py:3 | scheduler_powerflow_turbo_wrapper.py | """Fix/patch scheduler_powerflow_turbo_wrapper.py for Perception Spine V7.6 Turbo.
- Core/patch_scheduler_perception_spine_v76_fix.py:99 | scheduler_powerflow_turbo_wrapper.py | parser.add_argument("--scheduler", default="scheduler_powerflow_turbo_wrapper.py")
- Core/patch_scheduler_turbo_b8_surface_v738b.py:3 | scheduler_powerflow_turbo_wrapper.py | path = Path("scheduler_powerflow_turbo_wrapper.py")
- Core/patch_scheduler_turbo_daily_journal.py:7 | scheduler_powerflow_turbo_wrapper.py | TARGET = Path("scheduler_powerflow_turbo_wrapper.py")
- Core/patch_scheduler_turbo_daily_journal.py:13 | scheduler_powerflow_turbo_wrapper.py | print("PATCH_FAIL | scheduler_powerflow_turbo_wrapper.py missing"); return 1
- Core/patch_scheduler_turbo_daily_journal.py:45 | scheduler_powerflow_turbo_wrapper.py | print(f"PATCH_OK | scheduler_powerflow_turbo_wrapper.py patched | backup={backup}")
- Core/patch_scheduler_turbo_dashboard_contract_v74b.py:3 | scheduler_powerflow_turbo_wrapper.py | path = Path("scheduler_powerflow_turbo_wrapper.py")
- Core/patch_scheduler_turbo_evidence_bus_v739.py:3 | scheduler_powerflow_turbo_wrapper.py | path = Path("scheduler_powerflow_turbo_wrapper.py")
- Core/patch_scheduler_turbo_evidence_reading_v739f.py:3 | scheduler_powerflow_turbo_wrapper.py | path = Path("scheduler_powerflow_turbo_wrapper.py")
- Core/patch_scheduler_turbo_live_brief_v733.py:7 | scheduler_powerflow_turbo_wrapper.py | TARGET = Path("scheduler_powerflow_turbo_wrapper.py")
- Core/patch_scheduler_turbo_live_brief_v733.py:13 | scheduler_powerflow_turbo_wrapper.py | print("PATCH_FAIL | scheduler_powerflow_turbo_wrapper.py missing")
- Core/patch_scheduler_turbo_live_brief_v733.py:49 | scheduler_powerflow_turbo_wrapper.py | print(f"PATCH_OK | scheduler_powerflow_turbo_wrapper.py patched | backup={backup}")
- Core/patch_scheduler_turbo_live_brief_v733_hotfix.py:8 | scheduler_powerflow_turbo_wrapper.py | TARGET = Path("scheduler_powerflow_turbo_wrapper.py")
- Core/patch_scheduler_turbo_live_brief_v733_hotfix.py:9 | scheduler_powerflow_turbo_wrapper.py | BACKUP = Path("scheduler_powerflow_turbo_wrapper.py.bak_live_brief_v733")
- Core/patch_scheduler_turbo_live_brief_v733_hotfix.py:62 | scheduler_powerflow_turbo_wrapper.py | print("PATCH_FAIL | scheduler_powerflow_turbo_wrapper.py missing")
- Core/patch_scheduler_turbo_multiread_v734.py:7 | scheduler_powerflow_turbo_wrapper.py | TARGET = Path("scheduler_powerflow_turbo_wrapper.py")
- Core/patch_scheduler_turbo_multiread_v734.py:47 | scheduler_powerflow_turbo_wrapper.py | print("PATCH_FAIL | scheduler_powerflow_turbo_wrapper.py missing")
- Core/patch_scheduler_turbo_phase_synthesis_v738c.py:3 | scheduler_powerflow_turbo_wrapper.py | path = Path("scheduler_powerflow_turbo_wrapper.py")
- Core/patch_scheduler_turbo_time_profiles_v737d.py:7 | scheduler_powerflow_turbo_wrapper.py | path = Path("scheduler_powerflow_turbo_wrapper.py")
- Core/patch_scheduler_turbo_time_profiles_v737d.py:10 | scheduler_powerflow_turbo_wrapper.py | backup = Path(f"scheduler_powerflow_turbo_wrapper.py.bak_time_profiles_v737d_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
- Core/patch_scheduler_turbo_trader_cockpit_v735.py:8 | scheduler_powerflow_turbo_wrapper.py | TARGET = Path("scheduler_powerflow_turbo_wrapper.py")
- Core/pf_film_engine.py:5 | engine.py | pf_film_engine.py
- Core/pf_lab_engine.py:3 | engine.py | PowerFlow V6 — pf_lab_engine.py
- Core/pf_legacy_behavioral_bridge_once.py:6 | engine.py | Reads fast legacy observations emitted by engine.py:
- Core/pf_regime_engine.py:2 | engine.py | pf_regime_engine.py — PowerFlow V6
- Core/pf_replay_engine.py:1 | engine.py | # pf_replay_engine.py
- Core/run_cross_symbol_validation_once.py:5 | scheduler_powerflow.py | # Backward compatibility: scheduler_powerflow.py still passes --symbols.
- Core/run_powerflow_live_stack_once.py:267 | scheduler_powerflow_turbo_wrapper.py | lines.append("1. Si `TURBO_STACK_OK`, lancer ce runner via tâche Windows 5 min ou l'intégrer dans `scheduler_powerflow_turbo_wrapper.py`.")
- Core/scheduler_powerflow_ontology_wrapper.py:6 | scheduler_powerflow.py | - Run existing scheduler_powerflow.py in --once mode.
- Core/scheduler_powerflow_ontology_wrapper.py:10 | scheduler_powerflow.py | This avoids brittle direct patching of scheduler_powerflow.py.
- Core/scheduler_powerflow_ontology_wrapper.py:53 | scheduler_powerflow.py | code = run([sys.executable, "scheduler_powerflow.py", "--once", "--symbols", symbols])
- Core/scheduler_powerflow_turbo_wrapper.py:109 | scheduler_powerflow.py | [py, "scheduler_powerflow.py", "--once", "--symbols", symbols],
- Core/system_config.py:30 | engine.py | # Anciennement dans l'EA — maintenant gérés ici par engine.py
- Core/_backup_multisymbol_20260511_153542/run_regime_engine_once.py:3 | engine.py | Runner ponctuel pour pf_regime_engine.py.

## Syntax check

- PASS py_compile Core/engine.py

## T002 decision

T002 should be renamed from pf_engine.py refactor to Core/engine.py legacy boundary audit and extraction plan.

Minimal safe sequence:

1. Freeze the process_tick contract used by capture_bridge.py.
2. Add a small contract test that imports engine.process_tick and records its signature.
3. Identify side effects inside process_tick: DB writes, output files, alert bus writes.
4. Extract pure helpers only if they are not called directly by capture_bridge.py.
5. Keep engine.py as compatibility shell until capture_bridge.py is intentionally migrated.

## Technical risks

- Risk of breaking capture_bridge.py if process_tick signature changes.
- Risk of hidden side effects if engine.py writes DB/output/bus during tick processing.
- Risk of circular dependency if new pf_* module imports capture_* or cockpit_*.
- Risk of over-refactor while scheduler currently relies on wrappers/orchestrators.

## PowerFlow rule

No engine behavior change before the process_tick contract is frozen and tested.
