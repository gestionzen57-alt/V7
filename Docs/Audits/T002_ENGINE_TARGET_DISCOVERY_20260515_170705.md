# T002 Engine Target Discovery

Date: 2026-05-15 17:07:05
Repo: C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT

## Executive finding

- Active pf_engine.py: NOT FOUND outside archives/backups.
- Active engine.py candidates:
  - Core\engine.py
- Candidate T002 target: Core\engine.py

## Engine-like active files

- Core\engine.py
- Core\engine_temporal_nodes.py
- Core\patch_engine_legacy_behavioral_bus_v7.py
- Core\patch_engine_timecomp_v7_fix.py
- Core\patch_scheduler_perception_spine_v76_fix.py
- Core\patch_scheduler_turbo_b8_surface_v738b.py
- Core\patch_scheduler_turbo_daily_journal.py
- Core\patch_scheduler_turbo_dashboard_contract_v74b.py
- Core\patch_scheduler_turbo_evidence_bus_v739.py
- Core\patch_scheduler_turbo_evidence_reading_v739f.py
- Core\patch_scheduler_turbo_live_brief_v733.py
- Core\patch_scheduler_turbo_live_brief_v733_hotfix.py
- Core\patch_scheduler_turbo_multiread_v734.py
- Core\patch_scheduler_turbo_phase_synthesis_v738c.py
- Core\patch_scheduler_turbo_time_profiles_v737d.py
- Core\patch_scheduler_turbo_trader_cockpit_v735.py
- Core\patch_v74_eie_orchestrator.py
- Core\patch_v74_scheduler_use_dedup_gate.py
- Core\pf_cascade_engine.py
- Core\pf_cycle_orchestrator.py
- Core\pf_engine_orchestrator.py
- Core\pf_engine_scenes.py
- Core\pf_film_engine.py
- Core\pf_fractal_window_engine.py
- Core\pf_hmm_regime_engine.py
- Core\pf_lab_engine.py
- Core\pf_lab_engine_v72.py
- Core\pf_memory_engine.py
- Core\pf_regime_engine.py
- Core\pf_replay_engine.py
- Core\run_cascade_engine_once.py
- Core\run_cycle_orchestrator.py
- Core\run_entropy_engine_once.py
- Core\run_flow_ontology_cycle_once.py
- Core\run_force_kinematics_orchestrator_once.py
- Core\run_lab_engine_v72_once.py
- Core\run_powerflow_cycle_once.py
- Core\run_powerflow_cycle_once_CURRENT_BACKUP_20260511.py
- Core\run_powerflow_live_cycle.py
- Core\run_regime_engine_once.py
- Core\scheduler_powerflow.py
- Core\scheduler_powerflow_ontology_wrapper.py
- Core\scheduler_powerflow_turbo_wrapper.py
- Core\test_cascade_engine.py
- patch\pf_v76_telegram_cycle_once.py
- tests\test_v76_telegram_cycle_once.py
- tests\test_v767_reality_board_cycle_binding.py

## Reference scan

- Core\capture_bridge.py:90 | pattern engine.py | # (le filtre métier est dans engine.py)
- Core\capture_bridge.py:299 | pattern from engine import | from engine import process_tick
- Core\cockpit_terminal.py:33 | pattern pf_engine | import pf_engine_scenes as scene_engine
- Core\create_v74_eie_docs.py:59 | pattern run_powerflow_live_stack_once | 5. Brancher dans run_powerflow_live_stack_once.py.
- Core\engine.py:2 | pattern engine.py | # PowerFlow V5 — engine.py
- Core\engine_temporal_nodes.py:229 | pattern engine.py | # ENGINE ORCHESTRATION — Intégration au cycle engine.py
- Core\engine_temporal_nodes.py:233 | pattern engine.py | """Orchestrateur pour intégration dans engine.py."""
- Core\engine_temporal_nodes.py:276 | pattern engine.py | # HELPER FUNCTIONS — Pour appels depuis engine.py
- Core\engine_temporal_nodes.py:286 | pattern engine.py | Fonction wrapper pour appeler depuis engine.py.
- Core\engine_temporal_nodes.py:331 | pattern engine.py | # INTÉGRATION SIMPLE DANS engine.py — Code à copier
- Core\engine_temporal_nodes.py:335 | pattern engine.py | EXEMPLE D'UTILISATION DANS engine.py:
- Core\engine_temporal_nodes.py:388 | pattern engine.py | print("Import this in your engine.py to use.")
- Core\patch_cross_symbol_future_import_fix_v737d.py:24 | pattern scheduler_powerflow | # Backward compatibility: scheduler_powerflow.py still passes --symbols.
- Core\patch_cross_symbol_symbols_compat_v737d.py:15 | pattern scheduler_powerflow | # Backward compatibility: scheduler_powerflow.py still passes --symbols.
- Core\patch_engine_legacy_behavioral_bus_v7.py:4 | pattern engine.py | Patch PowerFlow legacy engine.py so fast V5 alerts are mirrored into a V7-readable JSONL bus.
- Core\patch_engine_legacy_behavioral_bus_v7.py:324 | pattern engine.py | parser.add_argument("--engine", default="engine.py")
- Core\patch_engine_timecomp_v7_fix.py:135 | pattern engine.py | print("[OK] engine.py already patched")
- Core\patch_engine_timecomp_v7_fix.py:161 | pattern engine.py | parser.add_argument("--engine", default="engine.py")
- Core\patch_scheduler_perception_spine_v76_fix.py:3 | pattern scheduler_powerflow | """Fix/patch scheduler_powerflow_turbo_wrapper.py for Perception Spine V7.6 Turbo.
- Core\patch_scheduler_perception_spine_v76_fix.py:3 | pattern scheduler_powerflow_turbo_wrapper | """Fix/patch scheduler_powerflow_turbo_wrapper.py for Perception Spine V7.6 Turbo.
- Core\patch_scheduler_perception_spine_v76_fix.py:99 | pattern scheduler_powerflow | parser.add_argument("--scheduler", default="scheduler_powerflow_turbo_wrapper.py")
- Core\patch_scheduler_perception_spine_v76_fix.py:99 | pattern scheduler_powerflow_turbo_wrapper | parser.add_argument("--scheduler", default="scheduler_powerflow_turbo_wrapper.py")
- Core\patch_scheduler_turbo_b8_surface_v738b.py:3 | pattern scheduler_powerflow | path = Path("scheduler_powerflow_turbo_wrapper.py")
- Core\patch_scheduler_turbo_b8_surface_v738b.py:3 | pattern scheduler_powerflow_turbo_wrapper | path = Path("scheduler_powerflow_turbo_wrapper.py")
- Core\patch_scheduler_turbo_daily_journal.py:7 | pattern scheduler_powerflow | TARGET = Path("scheduler_powerflow_turbo_wrapper.py")
- Core\patch_scheduler_turbo_daily_journal.py:7 | pattern scheduler_powerflow_turbo_wrapper | TARGET = Path("scheduler_powerflow_turbo_wrapper.py")
- Core\patch_scheduler_turbo_daily_journal.py:13 | pattern scheduler_powerflow | print("PATCH_FAIL | scheduler_powerflow_turbo_wrapper.py missing"); return 1
- Core\patch_scheduler_turbo_daily_journal.py:13 | pattern scheduler_powerflow_turbo_wrapper | print("PATCH_FAIL | scheduler_powerflow_turbo_wrapper.py missing"); return 1
- Core\patch_scheduler_turbo_daily_journal.py:45 | pattern scheduler_powerflow | print(f"PATCH_OK | scheduler_powerflow_turbo_wrapper.py patched | backup={backup}")
- Core\patch_scheduler_turbo_daily_journal.py:45 | pattern scheduler_powerflow_turbo_wrapper | print(f"PATCH_OK | scheduler_powerflow_turbo_wrapper.py patched | backup={backup}")
- Core\patch_scheduler_turbo_dashboard_contract_v74b.py:3 | pattern scheduler_powerflow | path = Path("scheduler_powerflow_turbo_wrapper.py")
- Core\patch_scheduler_turbo_dashboard_contract_v74b.py:3 | pattern scheduler_powerflow_turbo_wrapper | path = Path("scheduler_powerflow_turbo_wrapper.py")
- Core\patch_scheduler_turbo_evidence_bus_v739.py:3 | pattern scheduler_powerflow | path = Path("scheduler_powerflow_turbo_wrapper.py")
- Core\patch_scheduler_turbo_evidence_bus_v739.py:3 | pattern scheduler_powerflow_turbo_wrapper | path = Path("scheduler_powerflow_turbo_wrapper.py")
- Core\patch_scheduler_turbo_evidence_reading_v739f.py:3 | pattern scheduler_powerflow | path = Path("scheduler_powerflow_turbo_wrapper.py")
- Core\patch_scheduler_turbo_evidence_reading_v739f.py:3 | pattern scheduler_powerflow_turbo_wrapper | path = Path("scheduler_powerflow_turbo_wrapper.py")
- Core\patch_scheduler_turbo_live_brief_v733.py:7 | pattern scheduler_powerflow | TARGET = Path("scheduler_powerflow_turbo_wrapper.py")
- Core\patch_scheduler_turbo_live_brief_v733.py:7 | pattern scheduler_powerflow_turbo_wrapper | TARGET = Path("scheduler_powerflow_turbo_wrapper.py")
- Core\patch_scheduler_turbo_live_brief_v733.py:13 | pattern scheduler_powerflow | print("PATCH_FAIL | scheduler_powerflow_turbo_wrapper.py missing")
- Core\patch_scheduler_turbo_live_brief_v733.py:13 | pattern scheduler_powerflow_turbo_wrapper | print("PATCH_FAIL | scheduler_powerflow_turbo_wrapper.py missing")
- Core\patch_scheduler_turbo_live_brief_v733.py:49 | pattern scheduler_powerflow | print(f"PATCH_OK | scheduler_powerflow_turbo_wrapper.py patched | backup={backup}")
- Core\patch_scheduler_turbo_live_brief_v733.py:49 | pattern scheduler_powerflow_turbo_wrapper | print(f"PATCH_OK | scheduler_powerflow_turbo_wrapper.py patched | backup={backup}")
- Core\patch_scheduler_turbo_live_brief_v733_hotfix.py:8 | pattern scheduler_powerflow | TARGET = Path("scheduler_powerflow_turbo_wrapper.py")
- Core\patch_scheduler_turbo_live_brief_v733_hotfix.py:8 | pattern scheduler_powerflow_turbo_wrapper | TARGET = Path("scheduler_powerflow_turbo_wrapper.py")
- Core\patch_scheduler_turbo_live_brief_v733_hotfix.py:9 | pattern scheduler_powerflow | BACKUP = Path("scheduler_powerflow_turbo_wrapper.py.bak_live_brief_v733")
- Core\patch_scheduler_turbo_live_brief_v733_hotfix.py:9 | pattern scheduler_powerflow_turbo_wrapper | BACKUP = Path("scheduler_powerflow_turbo_wrapper.py.bak_live_brief_v733")
- Core\patch_scheduler_turbo_live_brief_v733_hotfix.py:62 | pattern scheduler_powerflow | print("PATCH_FAIL | scheduler_powerflow_turbo_wrapper.py missing")
- Core\patch_scheduler_turbo_live_brief_v733_hotfix.py:62 | pattern scheduler_powerflow_turbo_wrapper | print("PATCH_FAIL | scheduler_powerflow_turbo_wrapper.py missing")
- Core\patch_scheduler_turbo_multiread_v734.py:7 | pattern scheduler_powerflow | TARGET = Path("scheduler_powerflow_turbo_wrapper.py")
- Core\patch_scheduler_turbo_multiread_v734.py:7 | pattern scheduler_powerflow_turbo_wrapper | TARGET = Path("scheduler_powerflow_turbo_wrapper.py")
- Core\patch_scheduler_turbo_multiread_v734.py:47 | pattern scheduler_powerflow | print("PATCH_FAIL | scheduler_powerflow_turbo_wrapper.py missing")
- Core\patch_scheduler_turbo_multiread_v734.py:47 | pattern scheduler_powerflow_turbo_wrapper | print("PATCH_FAIL | scheduler_powerflow_turbo_wrapper.py missing")
- Core\patch_scheduler_turbo_phase_synthesis_v738c.py:3 | pattern scheduler_powerflow | path = Path("scheduler_powerflow_turbo_wrapper.py")
- Core\patch_scheduler_turbo_phase_synthesis_v738c.py:3 | pattern scheduler_powerflow_turbo_wrapper | path = Path("scheduler_powerflow_turbo_wrapper.py")
- Core\patch_scheduler_turbo_time_profiles_v737d.py:7 | pattern scheduler_powerflow | path = Path("scheduler_powerflow_turbo_wrapper.py")
- Core\patch_scheduler_turbo_time_profiles_v737d.py:7 | pattern scheduler_powerflow_turbo_wrapper | path = Path("scheduler_powerflow_turbo_wrapper.py")
- Core\patch_scheduler_turbo_time_profiles_v737d.py:10 | pattern scheduler_powerflow | backup = Path(f"scheduler_powerflow_turbo_wrapper.py.bak_time_profiles_v737d_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
- Core\patch_scheduler_turbo_time_profiles_v737d.py:10 | pattern scheduler_powerflow_turbo_wrapper | backup = Path(f"scheduler_powerflow_turbo_wrapper.py.bak_time_profiles_v737d_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
- Core\patch_scheduler_turbo_trader_cockpit_v735.py:8 | pattern scheduler_powerflow | TARGET = Path("scheduler_powerflow_turbo_wrapper.py")
- Core\patch_scheduler_turbo_trader_cockpit_v735.py:8 | pattern scheduler_powerflow_turbo_wrapper | TARGET = Path("scheduler_powerflow_turbo_wrapper.py")
- Core\patch_v74_fix_dedup_symbol_arg.py:4 | pattern run_powerflow_live_stack_once | TARGET = Path("run_powerflow_live_stack_once.py")
- Core\patch_v74_fix_dedup_symbol_arg.py:10 | pattern run_powerflow_live_stack_once | raise SystemExit("PATCH_FAIL | run_powerflow_live_stack_once.py missing")
- Core\patch_v74_scheduler_use_dedup_gate.py:4 | pattern run_powerflow_live_stack_once | TARGET = Path("run_powerflow_live_stack_once.py")
- Core\patch_v74_scheduler_use_dedup_gate.py:10 | pattern run_powerflow_live_stack_once | raise SystemExit("PATCH_FAIL | run_powerflow_live_stack_once.py missing")
- Core\pf_cycle_orchestrator.py:4 | pattern pf_cycle_orchestrator | pf_cycle_orchestrator.py
- Core\pf_engine_orchestrator.py:47 | pattern pf_engine | OUTPUT_STATE_FILE = "output/pf_engine_orchestrator_state.json"
- Core\pf_engine_orchestrator.py:47 | pattern pf_engine_orchestrator | OUTPUT_STATE_FILE = "output/pf_engine_orchestrator_state.json"
- Core\pf_engine_orchestrator.py:66 | pattern pf_engine | "Place pf_engine_orchestrator.py dans le même dossier."
- Core\pf_engine_orchestrator.py:66 | pattern pf_engine_orchestrator | "Place pf_engine_orchestrator.py dans le même dossier."
- Core\pf_engine_scenes.py:4 | pattern pf_engine | PowerFlow V5+ - pf_engine_scenes.py
- Core\pf_film_engine.py:5 | pattern engine.py | pf_film_engine.py
- Core\pf_lab_engine.py:3 | pattern engine.py | PowerFlow V6 — pf_lab_engine.py
- Core\pf_legacy_behavioral_bridge_once.py:6 | pattern engine.py | Reads fast legacy observations emitted by engine.py:
- Core\pf_normalizer.py:26 | pattern pf_engine | import pf_engine_scenes as scene_engine
- Core\pf_normalizer.py:374 | pattern pf_engine | """Appelle pf_engine_scenes et retourne la derniere scene produite pour ce TF."""
- Core\pf_regime_engine.py:2 | pattern engine.py | pf_regime_engine.py — PowerFlow V6
- Core\pf_replay_engine.py:1 | pattern engine.py | # pf_replay_engine.py
- Core\run_cross_symbol_validation_once.py:5 | pattern scheduler_powerflow | # Backward compatibility: scheduler_powerflow.py still passes --symbols.
- Core\run_cycle_orchestrator.py:5 | pattern pf_cycle_orchestrator | PowerFlow V7.2 - Runner / Daemon for pf_cycle_orchestrator.py
- Core\run_cycle_orchestrator.py:20 | pattern pf_cycle_orchestrator | from pf_cycle_orchestrator import ORCHESTRATOR_VERSION, parse_tfs, normalize_symbols, run_cycle
- Core\run_force_kinematics_orchestrator_once.py:9 | pattern pf_cycle_orchestrator | - pf_cycle_orchestrator.py expects a runner that can be called with --db/--symbol/--output.
- Core\run_powerflow_cycle_once.py:2 | pattern run_powerflow_cycle_once | run_powerflow_cycle_once.py
- Core\run_powerflow_cycle_once_CURRENT_BACKUP_20260511.py:2 | pattern run_powerflow_cycle_once | run_powerflow_cycle_once.py
- Core\run_powerflow_live_stack_once.py:267 | pattern scheduler_powerflow | lines.append("1. Si `TURBO_STACK_OK`, lancer ce runner via tâche Windows 5 min ou l'intégrer dans `scheduler_powerflow_turbo_wrapper.py`.")
- Core\run_powerflow_live_stack_once.py:267 | pattern scheduler_powerflow_turbo_wrapper | lines.append("1. Si `TURBO_STACK_OK`, lancer ce runner via tâche Windows 5 min ou l'intégrer dans `scheduler_powerflow_turbo_wrapper.py`.")
- Core\run_powerflow_live_stack_once.py:291 | pattern run_powerflow_live_stack_once | ck.append("- `run_powerflow_live_stack_once.py`")
- Core\run_volatility_texture_once.py:15 | pattern import engine | from pf_volatility_texture import ENGINE_VERSION, VolatilityTextureEngine
- Core\scheduler_powerflow.py:174 | pattern scheduler_powerflow | return Path("logs") / "scheduler_powerflow.lock"
- Core\scheduler_powerflow_ontology_wrapper.py:6 | pattern scheduler_powerflow | - Run existing scheduler_powerflow.py in --once mode.
- Core\scheduler_powerflow_ontology_wrapper.py:10 | pattern scheduler_powerflow | This avoids brittle direct patching of scheduler_powerflow.py.
- Core\scheduler_powerflow_ontology_wrapper.py:53 | pattern scheduler_powerflow | code = run([sys.executable, "scheduler_powerflow.py", "--once", "--symbols", symbols])
- Core\scheduler_powerflow_turbo_wrapper.py:109 | pattern scheduler_powerflow | [py, "scheduler_powerflow.py", "--once", "--symbols", symbols],
- Core\system_config.py:30 | pattern engine.py | # Anciennement dans l'EA — maintenant gérés ici par engine.py
- semantic_audit_gravity_zones_v72.py:37 | pattern engine.py | "Core/pf_memory_engine.py",
- test_batch_all_bricks.py:424 | pattern run_powerflow_cycle_once | "run_powerflow_cycle_once.py",
- test_batch_all_bricks_v2.py:384 | pattern run_powerflow_cycle_once | "run_powerflow_cycle_once.py",

## Syntax checks

- PASS py_compile Core\engine.py
- PASS py_compile Core\pf_engine_orchestrator.py
- PASS py_compile Core\pf_cycle_orchestrator.py
- PASS py_compile Core\scheduler_powerflow.py
- PASS py_compile Core\scheduler_powerflow_turbo_wrapper.py
- PASS py_compile Core\run_powerflow_live_stack_once.py
- PASS py_compile Core\run_powerflow_cycle_once.py

## Recommendation

- T002 is probably misnamed: dispatch says pf_engine.py, but active target appears to be Core\engine.py.
- Do not refactor blindly. First convert T002 from 'pf_engine.py refactor' to 'engine target audit / extraction plan'.
- Next action: inspect callable surfaces and runtime entrypoints before changing behavior.

## PowerFlow rule

No runtime refactor before confirming the actual entrypoint and active call graph.
