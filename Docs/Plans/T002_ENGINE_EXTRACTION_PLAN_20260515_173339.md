# T002-C Engine Extraction Plan

Date: 2026-05-15T15:33:39Z
Source map: Docs\Audits\T002_ENGINE_INTERNAL_MAP_20260515_172740.json

## Current technical state

- Runtime boundary is now: capture_bridge.py -> pf_engine_v6_adapter.process_tick -> engine.process_tick.
- Core/engine.py remains untouched.
- Frozen process_tick contract remains active.
- Existing T002 tests protect signature, adapter delegation and capture bridge boundary.

## Internal map summary

- process_tick line count: 283
- statement count: 45
- local helpers called: 18
- side-effect hints: 17

### Statement category counts

- OTHER: 14
- TICK_PRICE: 14
- ALERT_TRANSMISSION: 11
- FLOW_COMPUTE: 4
- BRAIN_MEMORY: 1
- SCENE_CONTEXT: 1

## Interpretation

process_tick is not a pure computation function. It mixes tick/price reading, alert transmission, helper calls and side-effect hints.
Therefore T002 must continue as progressive extraction behind the adapter, not as a direct rewrite.

## Extraction order

### Phase 0 - Keep boundary locked

- Keep Core/pf_engine_v6_adapter.py as the only bridge used by capture_bridge.py.
- Keep Docs/Contracts/T002_ENGINE_PROCESS_TICK_CONTRACT.json unchanged unless an intentional migration is documented.
- Keep tests/test_t002_engine_process_tick_contract.py and tests/test_t002_engine_v6_adapter.py green.

### Phase 1 - Extract pure read/compute helpers only

Candidate categories:
- TICK_PRICE
- FLOW_COMPUTE

Candidate target module:
- Core/pf_engine_v6_core.py

Allowed in Phase 1:
- stateless calculations
- tick/prev derived values
- score/force/angle helper wrappers

Forbidden in Phase 1:
- DB writes
- send_alert calls
- brain mutation unless wrapped and tested
- dashboard/cockpit/telegram imports

### Phase 2 - Extract alert payload construction, not sending

Candidate target module:
- Core/pf_engine_v6_alert_payloads.py

Allowed:
- build payload dictionaries
- format alert labels
- classify maturity / event type

Forbidden:
- direct send_alert
- telegram import
- DB writes

### Phase 3 - Wrap brain mutation

Candidate target module:
- Core/pf_engine_v6_state.py

Goal:
- isolate brain read/write semantics with golden tests.

### Phase 4 - Persistence and side effects last

Persistence, DB writes, file writes and alert transmission must stay inside legacy engine.py until all pure phases are tested.

## Local helpers called by process_tick

- mark_alerted | lines 550-551 | calls 9
- score_signal | lines 534-542 | calls 9
- persist_signal | lines 448-460 | calls 9
- _write_legacy_behavioral_signal | lines 214-247 | calls 9
- can_alert | lines 547-548 | calls 9
- check_volume | lines 468-485 | calls 1
- build_htf_context | lines 490-529 | calls 1
- detect_approach | lines 771-790 | calls 1
- detect_zone_battle | lines 795-815 | calls 1
- detect_cross | lines 681-743 | calls 1
- register_cross | lines 561-565 | calls 1
- detect_convergence | lines 567-593 | calls 1
- build_note | lines 875-891 | calls 1
- detect_time_compression | lines 833-870 | calls 1
- detect_slingshot | lines 748-762 | calls 1
- detect_compression | lines 601-639 | calls 1
- detect_compression_squeeze | lines 641-674 | calls 1
- _write_legacy_timecomp_event_v7bus | lines 274-321 | calls 1

## Statement map by category

### FLOW_COMPUTE

- line 911-911 | Assign | spread_ok = tick.spread <= MAX_SPREAD
- line 1146-1146 | Assign | sc, lv = score_signal(final_type, tf, volume_badge, htf.htf_bonus, spread_ok)
- line 1170-1173 | Assign | sig = Signal(symbol=pair, timeframe=tf, signal_type=final_type, timestamp=tick.timestamp, dev_strong=strong, dev_weak=weak, score=sc, level=lv, htf=htf, volume_badge=volume_badge, 
- line 1175-1176 | Expr | print(f"🔥 V5 signal : {sig.signal_type} {pair} M{tf} " f"{strong.upper()}>{weak.upper()} score={sc} {lv}")

### TICK_PRICE

- line 897-898 | If | if tick.timeframe not in TIMEFRAMES: return
- line 900-900 | Assign | uid = f"{tick.symbol}M{tick.timeframe}"
- line 901-901 | Assign | pair = tick.symbol
- line 902-902 | Assign | tf = tick.timeframe
- line 903-903 | Assign | dev_a, dev_b = tick.dev_a, tick.dev_b
- line 912-912 | Assign | volume_badge = check_volume(tick, uid)
- line 915-917 | If | if DEBUG_CROSS: print(f"⚙️ V5 process_tick {pair} M{tf} | " f"A={tick.val_a:.1f} {dev_a.upper()} | B={tick.val_b:.1f} {dev_b.upper()}")
- line 920-935 | Try | try: tc_ev = detect_time_compression(tick, uid) if tc_ev: tf_lbl = TF_LABELS.get(tf, f"M{tf}") tc_record = _write_legacy_timecomp_event_v7bus(pair, tf, tf_lbl, tick, tc_ev) stamp =
- line 938-938 | Assign | approach = detect_approach(tick, prev, uid)
- line 1097-1097 | Assign | signal_type = detect_cross(tick, prev, uid)
- line 1101-1101 | Assign | strong = dev_a if tick.val_a >= tick.val_b else dev_b
- line 1150-1163 | If | if tf in (5,15) and final_type in ("CROSS","SUPER_SWITCH","FAKEOUT"): lvl_l = get_level_low(tf) lvl_h = get_level_high(tf) bonus_extreme = 0 if (strong==dev_a and prev.val_a<=lvl_l
- line 1167-1167 | Assign | note = build_note(signal_type, tick, htf, conv)
- line 1178-1178 | Expr | _write_legacy_behavioral_signal(sig, htf, tick=tick)

### BRAIN_MEMORY

- line 913-913 | Assign | htf = build_htf_context(pair, tf, dev_a, dev_b, brain)

### SCENE_CONTEXT

- line 959-959 | Assign | zone = detect_zone_battle(tick, prev, uid)

### ALERT_TRANSMISSION

- line 939-956 | If | if approach: spam_key = f"APPROACH_{uid}_{approach['challenger']}" if can_alert(spam_key): mark_alerted(spam_key) tf_lbl = TF_LABELS.get(tf, f"M{tf}") ch, dom = approach["challenge
- line 960-976 | If | if zone: spam_key = f"ZONE_{uid}_{zone['actor']}" if can_alert(spam_key): mark_alerted(spam_key) tf_lbl = TF_LABELS.get(tf, f"M{tf}") stype = "EXTREME_HIGH" if zone["zone"]=="HAUTE
- line 979-1012 | If | if ALERT_EXTREME_LEVELS: for dev, val in [(dev_a, tick.val_a), (dev_b, tick.val_b)]: key_ex = f"{uid}_{dev}_extreme" prev_state = cross_states.get(key_ex, "NEUTRE") lvl_h = get_lev
- line 1015-1037 | If | if ALERT_SLINGSHOT: sling = detect_slingshot(tick, prev, uid) if sling: exploding = dev_a if sling=="SLINGSHOT_A" else dev_b weak = dev_b if exploding==dev_a else dev_a spam_key = 
- line 1040-1073 | If | if ALERT_COMPRESSION: comp_events = detect_compression(tick, uid) if comp_events: ev = max(comp_events, key=lambda e: abs(e["val"]-50.0)) dev_c = ev["dev"] opp_c = dev_b if dev_c==
- line 1076-1094 | If | if ALERT_COMPRESSION_SQUEEZE: sq = detect_compression_squeeze(tick, prev, uid) if sq: spam_key = f"SQUEEZE_{uid}_{sq['compressed_dev']}_{sq['pressure_dev']}" if can_alert(spam_key)
- line 1104-1130 | If | if signal_type == "KISS_REJECT": if not ALERT_KISS_REJECT: return spam_key = f"KISS_REJECT_{uid}_{strong}" if not can_alert(spam_key): return mark_alerted(spam_key) tf_lbl = TF_LAB
- line 1136-1140 | If | if signal_type=="FAKEOUT" and ALERT_FAKEOUT: final_type="FAKEOUT" elif signal_type=="SUPER_SWITCH" and ALERT_SUPER_SWITCH: final_type="SUPER_SWITCH" elif conv and ALERT_CONVERGENCE
- line 1143-1143 | If | if not can_alert(spam_key): return
- line 1144-1144 | Expr | mark_alerted(spam_key)
- line 1177-1177 | Expr | await send_alert(sig, htf, brain)

### OTHER

- line 906-906 | Assign | lvl_surcht_max = get_level_high(tf)
- line 907-907 | Assign | lvl_surcht_debut = get_level_high(tf)
- line 908-908 | Assign | lvl_survente_max = get_level_low(tf)
- line 909-909 | Assign | lvl_survente_debut = get_level_low(tf)
- line 1098-1099 | If | if signal_type is None: return
- line 1102-1102 | Assign | weak = dev_b if strong==dev_a else dev_a
- line 1133-1133 | Expr | register_cross(pair, tf, strong, weak)
- line 1134-1134 | Assign | conv = detect_convergence(pair, tf, strong, weak, htf)
- line 1142-1142 | Assign | spam_key = f"{final_type}_{uid}_{strong}"
- line 1149-1149 | Assign | extreme_tag = ""
- line 1164-1164 | If | if conv: sc += conv["bonus"]
- line 1165-1165 | Assign | lv = "PREMIUM" if sc>=8 else ("CONFIRM" if sc>=5 else "STANDARD")
- line 1168-1168 | If | if extreme_tag: note += extreme_tag
- line 1178-1178 | Expr | persist_signal(sig, htf)

## Side-effect hints to avoid in early extraction

- line 896 | Alert call | async def process_tick(tick: Tick, prev: Tick, brain: Brain, send_alert):
- line 916 | Print | print(f"⚙️ V5 process_tick {pair} M{tf} | "
- line 927 | Print | print(stamp)
- line 928 | Print | print(f"🔒 TIME-COMP LOCK | {pair} {tf_lbl} | "
- line 931 | Print | print(stamp)
- line 932 | Print | print(f"💨 TIME-COMP BREAK | {pair} {tf_lbl} | "
- line 935 | Print | print(f"[engine] detect_time_compression ignoré : {e}")
- line 955 | Alert call | await send_alert(sig, htf, brain)
- line 975 | Alert call | await send_alert(sig, htf, brain)
- line 997 | Alert call | await send_alert(sig, htf, brain); persist_signal(sig, htf); _write_legacy_behavioral_signal(sig, htf, tick=tick)
- line 1010 | Alert call | await send_alert(sig, htf, brain); persist_signal(sig, htf); _write_legacy_behavioral_signal(sig, htf, tick=tick)
- line 1037 | Alert call | await send_alert(sig, htf, brain); persist_signal(sig, htf); _write_legacy_behavioral_signal(sig, htf, tick=tick)
- line 1073 | Alert call | await send_alert(sig, htf, brain); persist_signal(sig, htf); _write_legacy_behavioral_signal(sig, htf, tick=tick)
- line 1094 | Alert call | await send_alert(sig, htf, brain); persist_signal(sig, htf); _write_legacy_behavioral_signal(sig, htf, tick=tick)
- line 1130 | Alert call | await send_alert(sig, htf, brain); persist_signal(sig, htf); _write_legacy_behavioral_signal(sig, htf, tick=tick); return
- line 1175 | Print | print(f"🔥 V5 signal : {sig.signal_type} {pair} M{tf} "
- line 1177 | Alert call | await send_alert(sig, htf, brain)

## Proposed next coding step

Create a no-behavior-change module skeleton:

- Core/pf_engine_v6_core.py
- tests/test_t002_engine_v6_core_contract.py

Initial content should be minimal:

1. A dataclass or plain dict helper for derived tick context.
2. Tests using synthetic tick-like objects.
3. No connection to capture_bridge yet.
4. No call from process_tick yet.

This creates a safe destination for future extraction without changing runtime.

## Stop criteria

- Any test failure in existing T002 tests.
- Any new import from pf_* to cockpit_*, dashboard_* or telegram_*.
- Any DB write moved into a new pf_* module.
- Any change to process_tick signature without updating contract intentionally.

## Verdict

T002 is now ready for a minimal Phase 1 code patch, but only as a detached pure-helper module first.
Do not move process_tick logic yet.

