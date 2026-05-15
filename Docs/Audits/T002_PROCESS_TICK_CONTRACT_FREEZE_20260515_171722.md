# T002 Process Tick Contract Freeze

Date: 2026-05-15T15:17:22Z

## Verdict

- engine.process_tick exists: YES
- signature: (tick: models.Tick, prev: models.Tick, brain: dict, send_alert)
- source sha256: 632b49c80c23aa68635fc5989cedd0963ff6467c15cd451f615c33eee7ff6db9
- source lines: 896-1178

## Runtime boundary callers

- Core/capture_bridge.py:299 | from engine import process_tick | from engine import process_tick
- Core/capture_bridge.py:299 | from engine import | from engine import process_tick

## Side-effect hints inside process_tick

- line 21 | print( | print(f"⚙️ V5 process_tick {pair} M{tf} | "
- line 32 | print( | print(stamp)
- line 33 | print( | print(f"🔒 TIME-COMP LOCK | {pair} {tf_lbl} | "
- line 36 | print( | print(stamp)
- line 37 | print( | print(f"💨 TIME-COMP BREAK | {pair} {tf_lbl} | "
- line 40 | print( | print(f"[engine] detect_time_compression ignoré : {e}")
- line 280 | print( | print(f"🔥 V5 signal : {sig.signal_type} {pair} M{tf} "

## Active engine.py top-level surface

### Functions
- _pfv7_utc_iso | lines 93-104
- _pfv7_symbol_dir | lines 107-110
- _pfv7_behavioral_jsonl_path | lines 113-114
- _pfv7_timecomp_jsonl_path | lines 117-118
- _pfv7_event_time_risks | lines 121-137
- _pfv7_signal_layer | lines 140-150
- _pfv7_event_role | lines 153-170
- _pfv7_pair_bias_from_signal | lines 173-187
- _pfv7_write_jsonl | lines 190-192
- _write_legacy_behavioral_event | lines 195-211
- _write_legacy_behavioral_signal | lines 214-247
- _pfv7_timecomp_event_type | lines 250-256
- _pfv7_timecomp_direction | lines 259-271
- _write_legacy_timecomp_event_v7bus | lines 274-321
- _utc_iso | lines 327-341
- _legacy_timecomp_event_type | lines 343-349
- _legacy_timecomp_direction | lines 351-363
- _legacy_timecomp_jsonl_path | lines 365-368
- _write_legacy_timecomp_event | lines 370-408
- signal_to_db_dict | lines 414-432
- htf_to_db_dict | lines 434-446
- persist_signal | lines 448-460
- log_flow_regime | lines 462-463
- check_volume | lines 468-485
- build_htf_context | lines 490-529
- score_signal | lines 534-542
- can_alert | lines 547-548
- mark_alerted | lines 550-551
- register_cross | lines 561-565
- detect_convergence | lines 567-593
- get_compression_band | lines 598-599
- detect_compression | lines 601-639
- detect_compression_squeeze | lines 641-674
- detect_cross | lines 681-743
- detect_slingshot | lines 748-762
- detect_approach | lines 771-790
- detect_zone_battle | lines 795-815
- _pip_size | lines 825-826
- _time_comp_band | lines 828-831
- detect_time_compression | lines 833-870
- build_note | lines 875-891
- process_tick | lines 896-1178
- process_temporal_nodes_cycle | lines 1184-1227

### Classes
- none

## Files created

- Docs/Contracts/T002_ENGINE_PROCESS_TICK_CONTRACT.json
- tests/test_t002_engine_process_tick_contract.py

## Recommendation

1. Treat T002 as a runtime-boundary stabilization task, not a blind refactor.
2. Keep capture_bridge.py compatible with engine.process_tick until the contract test has a replacement boundary.
3. Next step: build a V6 adapter around process_tick or extract internals behind the same signature.

