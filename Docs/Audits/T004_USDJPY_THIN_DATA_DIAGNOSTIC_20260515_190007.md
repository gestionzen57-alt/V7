# T004 USDJPY Thin Data Diagnostic

Date: 2026-05-15T17:00:07Z

## Result

- Status: DB_FOUND
- DB path: powerflow.db
- Symbols: USDJPY, GBPUSD, EURUSD
- Tables inspected: 5

## Recommendations

- DB found but all inspected tables have zero rows. Diagnose capture path or DB path mismatch first.

## Per-symbol table matrix

### USDJPY

- force_snapshots | count=0 | min=None | max=None
- force_snapshots_v2 | count=0 | min=None | max=None
- signals | count=0 | min=None | max=None

### GBPUSD

- force_snapshots | count=0 | min=None | max=None
- force_snapshots_v2 | count=0 | min=None | max=None
- signals | count=0 | min=None | max=None

### EURUSD

- force_snapshots | count=0 | min=None | max=None
- force_snapshots_v2 | count=0 | min=None | max=None
- signals | count=0 | min=None | max=None

## Table overview

- context_htf | rows=0 | symbol_col=None | time_col=None
- force_snapshots | rows=0 | symbol_col=symbol | time_col=created_at
- force_snapshots_v2 | rows=0 | symbol_col=symbol | time_col=created_at
- signals | rows=0 | symbol_col=symbol | time_col=created_at
- sqlite_sequence | rows=0 | symbol_col=None | time_col=None

## Code/log references

- Core\analyze_powerflow_from_0600_today.py | hits=force_snapshots, symbol
- Core\audit_usdjpy_capture.py | hits=USDJPY, force_snapshots, stale, symbol, symbols
- Core\audit_usdjpy_fast.py | hits=USDJPY, capture_bridge, force_snapshots, stale, symbol, thin
- Core\capture_bridge.py | hits=force_snapshots, symbol
- Core\CHECKPOINT_P0_LIVE_20260511.md | hits=symbol
- Core\CHECKPOINT_POWERFLOW_V76_20260513.md | hits=USDJPY, capture_bridge, symbol, symbols
- Core\CHECKPOINT_SESSION_FINAL_20260511.md | hits=capture_bridge, stale, symbol
- Core\CHECKPOINT_V73.md | hits=USDJPY, symbol, symbols
- Core\CHECKPOINT_V731_DAILY_FLOW_PACKET.md | hits=symbol
- Core\CHECKPOINT_V734B_B6_PARSER_HOTFIX.md | hits=USDJPY, symbol, symbols
- Core\CHECKPOINT_V734_B6_MULTIREAD_SYNTHESIS.md | hits=USDJPY, symbol, symbols
- Core\CHECKPOINT_V735B_TRADER_COCKPIT_CLARITY.md | hits=USDJPY, symbol, symbols
- Core\CHECKPOINT_V735_TRADER_COCKPIT.md | hits=USDJPY, symbol, symbols
- Core\CHECKPOINT_V736_TRADER_JOURNAL_J1.md | hits=USDJPY, symbol, symbols
- Core\CHECKPOINT_V73_TURBO_WRAPPER.md | hits=USDJPY, symbol, symbols
- Core\CHECKPOINT_V74_DASHBOARD_FINAL.md | hits=thin
- Core\CHECKPOINT_V75_FINAL_DASHBOARD.md | hits=stale
- Core\check_db.py | hits=force_snapshots, symbol
- Core\CHECK_DB_SCHEMA_POWERFLOW.py | hits=force_snapshots
- Core\CHECK_EXTENDED_DB_V2.py | hits=force_snapshots, symbol
- Core\check_recent_signals.py | hits=symbol
- Core\check_table_freshness.py | hits=force_snapshots
- Core\check_tf_by_table.py | hits=force_snapshots, symbol
- Core\check_tf_counts.py | hits=force_snapshots, symbol
- Core\CLAUDE_md_V7.1.md | hits=capture_bridge, force_snapshots, stale, symbol
- Core\CLAUDE_md_V72_FINAL_UPDATE.md | hits=capture_bridge, stale, symbol
- Core\CLAUDE_REBASE_POWERFLOW_V721_20260511.md | hits=USDJPY, capture_bridge, force_snapshots, stale, symbol, symbols, thin
- Core\cleanup_powerflow_dashboard_artifacts.ps1 | hits=thin
- Core\cockpit_agentic_state_v01.py | hits=force_snapshots, symbol
- Core\cockpit_alerts.py | hits=symbol
- Core\cockpit_reader.py | hits=force_snapshots, stale, symbol
- Core\cockpit_terminal.py | hits=force_snapshots, symbol, symbols
- Core\COMMIT_PREP_DASHBOARD_V72_FINAL.md | hits=stale, symbol
- Core\create_v74_eie_docs.py | hits=force_snapshots, symbol
- Core\CURRENT_STATE_POWERFLOW_V721_CENTRALISE_20260511.md | hits=USDJPY, stale, symbol, thin
- Core\CURRENT_STATE_V7_OFFICIAL_20260511.md | hits=capture_bridge, stale, symbol
- Core\CURRENT_STATE_V7_POST_P0_UPDATE.md | hits=capture_bridge, symbol
- Core\dashboard_consensus_divergence_builder.py | hits=symbol
- Core\dashboard_contract_v2.json | hits=stale, symbol
- Core\dashboard_contract_validator.py | hits=stale
- Core\dashboard_data.json | hits=force_snapshots, symbol, thin
- Core\dashboard_data_normalizer.py | hits=stale
- Core\DASHBOARD_HYDRATION_RUNNER_GUIDE.md | hits=symbol
- Core\DASHBOARD_HYDRATION_RUNNER_README.md | hits=stale, symbol
- Core\DASHBOARD_LIVE_USER_GUIDE.md | hits=stale, symbol
- Core\dashboard_normalize_b6_live_fusion.py | hits=stale, symbol, symbols
- Core\dashboard_normalize_daily_flow_packet.py | hits=symbol, symbols
- Core\dashboard_normalize_daily_journal.py | hits=symbol, symbols
- Core\dashboard_normalize_data_health.py | hits=USDJPY, stale, symbol, symbols
- Core\dashboard_normalize_live_brief.py | hits=symbol, symbols
- Core\dashboard_normalize_m1_context.py | hits=symbol
- Core\dashboard_normalize_multiread_synthesis.py | hits=symbol, symbols
- Core\dashboard_normalize_signal_adaptive.py | hits=stale, symbol, symbols
- Core\dashboard_normalize_time_profiles.py | hits=symbol
- Core\dashboard_normalize_topdown_reader.py | hits=symbol, symbols
- Core\dashboard_output_coverage_doctor.py | hits=stale, symbol
- Core\dashboard_server.py | hits=force_snapshots, stale, symbol
- Core\dashboard_sync_agent_v01.py | hits=symbol
- Core\DASHBOARD_V72_FINAL_VALIDATION_REPORT.md | hits=stale, symbol
- Core\dashboard_v74_contract_check.py | hits=symbol, thin
- Core\db.py | hits=force_snapshots, symbol
- Core\diagnose_usdjpy_thin_bottleneck.py | hits=USDJPY, capture_bridge, force_snapshots, stale, symbol, symbols, thin
- Core\DOCS_UPDATE_PASS_STRICT_REPORT.md | hits=stale
- Core\engine.py | hits=stale, symbol, symbols
- Core\engine_temporal_nodes.py | hits=symbol, symbols
- Core\film.py | hits=force_snapshots, symbol, thin
- Core\flow_extended_v2_live.txt | hits=force_snapshots, symbol
- Core\flow_extended_v2_strict.txt | hits=force_snapshots, symbol
- Core\fractal_window_lab004.txt | hits=symbol
- Core\git_deploy_multisymbol.ps1 | hits=symbol, symbols
- Core\INSPECT_FORCE_SNAPSHOTS_V2.py | hits=force_snapshots
- Core\install_powerflow_pack.ps1 | hits=capture_bridge
- Core\lab.py | hits=force_snapshots, symbol
- Core\lab_powerflow.py | hits=force_snapshots, symbol
- Core\LAB_POWERFLOW_README.md | hits=symbol
- Core\lab_replay.py | hits=symbol
- Core\LEXIQUE_GRAMMAIRE_V7_FINAL_20260511.md | hits=capture_bridge, stale, thin
- Core\LEXIQUE_GRAMMAIRE_V7_PATCH_POST_P0.md | hits=stale
- Core\LEXIQUE_PATCH_B1HMM_B4WAVELET.md | hits=stale
- Core\LEXIQUE_PATCH_M1_NOISE_USDJPY_DASHBOARD.md | hits=USDJPY, force_snapshots, thin

## Runtime behavior

- DB opened read-only.
- No runtime wiring.
- No dashboard file touched.

## Next action candidate

If DB is empty, diagnose the active DB path and capture insertion path before changing any engine logic.
If reference symbols have rows but USDJPY does not, inspect symbol filters / MT4 Market Watch / bridge symbol allowlist.

