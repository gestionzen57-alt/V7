# T002-B Engine Internal Map

Date: 2026-05-15T15:27:40Z

## Executive finding

- Target: Core/engine.py
- Runtime callable: process_tick
- process_tick lines: 896-1178
- process_tick line count: 283
- process_tick args: tick, prev, brain, send_alert

## Statement categories inside process_tick

- TICK_PRICE: 14
- OTHER: 14
- ALERT_TRANSMISSION: 11
- FLOW_COMPUTE: 4
- BRAIN_MEMORY: 1
- SCENE_CONTEXT: 1

## Top calls inside process_tick

- mark_alerted: 9
- score_signal: 9
- Signal: 9
- persist_signal: 9
- _write_legacy_behavioral_signal: 9
- can_alert: 9
- send_alert: 9
- get_level_high: 7
- print: 7
- get_level_low: 6
- TF_LABELS.get: 6
- strong.upper: 4
- dev_c.upper: 4
- weak.upper: 2
- last.get: 2
- dev.upper: 2
- check_volume: 1
- build_htf_context: 1
- detect_approach: 1
- detect_zone_battle: 1
- detect_cross: 1
- register_cross: 1
- detect_convergence: 1
- build_note: 1
- detect_time_compression: 1
- detect_slingshot: 1
- detect_compression: 1
- detect_compression_squeeze: 1
- get_kiss_frolement: 1
- get_kiss_force_rejet: 1

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

## Side-effect hints

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

## process_tick statement map

- line 897-898 | TICK_PRICE | If | if tick.timeframe not in TIMEFRAMES: return
- line 900-900 | TICK_PRICE | Assign | uid = f"{tick.symbol}M{tick.timeframe}"
- line 901-901 | TICK_PRICE | Assign | pair = tick.symbol
- line 902-902 | TICK_PRICE | Assign | tf = tick.timeframe
- line 903-903 | TICK_PRICE | Assign | dev_a, dev_b = tick.dev_a, tick.dev_b
- line 906-906 | OTHER | Assign | lvl_surcht_max = get_level_high(tf)
- line 907-907 | OTHER | Assign | lvl_surcht_debut = get_level_high(tf)
- line 908-908 | OTHER | Assign | lvl_survente_max = get_level_low(tf)
- line 909-909 | OTHER | Assign | lvl_survente_debut = get_level_low(tf)
- line 911-911 | FLOW_COMPUTE | Assign | spread_ok = tick.spread <= MAX_SPREAD
- line 912-912 | TICK_PRICE | Assign | volume_badge = check_volume(tick, uid)
- line 913-913 | BRAIN_MEMORY | Assign | htf = build_htf_context(pair, tf, dev_a, dev_b, brain)
- line 915-917 | TICK_PRICE | If | if DEBUG_CROSS: print(f"⚙️ V5 process_tick {pair} M{tf} | " f"A={tick.val_a:.1f} {dev_a.upper()} | B={tick.val_b:.1f} {dev_b.upper()}")
- line 920-935 | TICK_PRICE | Try | try: tc_ev = detect_time_compression(tick, uid) if tc_ev: tf_lbl = TF_LABELS.get(tf, f"M{tf}") tc_record = _write_legacy_timecomp_event_v7bus(pair, tf, tf_lbl, tick, tc_ev) stamp =
- line 938-938 | TICK_PRICE | Assign | approach = detect_approach(tick, prev, uid)
- line 939-956 | ALERT_TRANSMISSION | If | if approach: spam_key = f"APPROACH_{uid}_{approach['challenger']}" if can_alert(spam_key): mark_alerted(spam_key) tf_lbl = TF_LABELS.get(tf, f"M{tf}") ch, dom = approach["challenge
- line 959-959 | SCENE_CONTEXT | Assign | zone = detect_zone_battle(tick, prev, uid)
- line 960-976 | ALERT_TRANSMISSION | If | if zone: spam_key = f"ZONE_{uid}_{zone['actor']}" if can_alert(spam_key): mark_alerted(spam_key) tf_lbl = TF_LABELS.get(tf, f"M{tf}") stype = "EXTREME_HIGH" if zone["zone"]=="HAUTE
- line 979-1012 | ALERT_TRANSMISSION | If | if ALERT_EXTREME_LEVELS: for dev, val in [(dev_a, tick.val_a), (dev_b, tick.val_b)]: key_ex = f"{uid}_{dev}_extreme" prev_state = cross_states.get(key_ex, "NEUTRE") lvl_h = get_lev
- line 1015-1037 | ALERT_TRANSMISSION | If | if ALERT_SLINGSHOT: sling = detect_slingshot(tick, prev, uid) if sling: exploding = dev_a if sling=="SLINGSHOT_A" else dev_b weak = dev_b if exploding==dev_a else dev_a spam_key = 
- line 1040-1073 | ALERT_TRANSMISSION | If | if ALERT_COMPRESSION: comp_events = detect_compression(tick, uid) if comp_events: ev = max(comp_events, key=lambda e: abs(e["val"]-50.0)) dev_c = ev["dev"] opp_c = dev_b if dev_c==
- line 1076-1094 | ALERT_TRANSMISSION | If | if ALERT_COMPRESSION_SQUEEZE: sq = detect_compression_squeeze(tick, prev, uid) if sq: spam_key = f"SQUEEZE_{uid}_{sq['compressed_dev']}_{sq['pressure_dev']}" if can_alert(spam_key)
- line 1097-1097 | TICK_PRICE | Assign | signal_type = detect_cross(tick, prev, uid)
- line 1098-1099 | OTHER | If | if signal_type is None: return
- line 1101-1101 | TICK_PRICE | Assign | strong = dev_a if tick.val_a >= tick.val_b else dev_b
- line 1102-1102 | OTHER | Assign | weak = dev_b if strong==dev_a else dev_a
- line 1104-1130 | ALERT_TRANSMISSION | If | if signal_type == "KISS_REJECT": if not ALERT_KISS_REJECT: return spam_key = f"KISS_REJECT_{uid}_{strong}" if not can_alert(spam_key): return mark_alerted(spam_key) tf_lbl = TF_LAB
- line 1133-1133 | OTHER | Expr | register_cross(pair, tf, strong, weak)
- line 1134-1134 | OTHER | Assign | conv = detect_convergence(pair, tf, strong, weak, htf)
- line 1136-1140 | ALERT_TRANSMISSION | If | if signal_type=="FAKEOUT" and ALERT_FAKEOUT: final_type="FAKEOUT" elif signal_type=="SUPER_SWITCH" and ALERT_SUPER_SWITCH: final_type="SUPER_SWITCH" elif conv and ALERT_CONVERGENCE
- line 1142-1142 | OTHER | Assign | spam_key = f"{final_type}_{uid}_{strong}"
- line 1143-1143 | ALERT_TRANSMISSION | If | if not can_alert(spam_key): return
- line 1144-1144 | ALERT_TRANSMISSION | Expr | mark_alerted(spam_key)
- line 1146-1146 | FLOW_COMPUTE | Assign | sc, lv = score_signal(final_type, tf, volume_badge, htf.htf_bonus, spread_ok)
- line 1149-1149 | OTHER | Assign | extreme_tag = ""
- line 1150-1163 | TICK_PRICE | If | if tf in (5,15) and final_type in ("CROSS","SUPER_SWITCH","FAKEOUT"): lvl_l = get_level_low(tf) lvl_h = get_level_high(tf) bonus_extreme = 0 if (strong==dev_a and prev.val_a<=lvl_l
- line 1164-1164 | OTHER | If | if conv: sc += conv["bonus"]
- line 1165-1165 | OTHER | Assign | lv = "PREMIUM" if sc>=8 else ("CONFIRM" if sc>=5 else "STANDARD")
- line 1167-1167 | TICK_PRICE | Assign | note = build_note(signal_type, tick, htf, conv)
- line 1168-1168 | OTHER | If | if extreme_tag: note += extreme_tag
- line 1170-1173 | FLOW_COMPUTE | Assign | sig = Signal(symbol=pair, timeframe=tf, signal_type=final_type, timestamp=tick.timestamp, dev_strong=strong, dev_weak=weak, score=sc, level=lv, htf=htf, volume_badge=volume_badge, 
- line 1175-1176 | FLOW_COMPUTE | Expr | print(f"🔥 V5 signal : {sig.signal_type} {pair} M{tf} " f"{strong.upper()}>{weak.upper()} score={sc} {lv}")
- line 1177-1177 | ALERT_TRANSMISSION | Expr | await send_alert(sig, htf, brain)
- line 1178-1178 | OTHER | Expr | persist_signal(sig, htf)
- line 1178-1178 | TICK_PRICE | Expr | _write_legacy_behavioral_signal(sig, htf, tick=tick)

## Recommended extraction order

1. Do not move process_tick yet. Keep pf_engine_v6_adapter as the stable boundary.
2. Extract pure helper computations first: force, score, price/tick transforms.
3. Extract alert formatting after helper computations are stable.
4. Extract DB or persistence last because it carries side effects.
5. Add a targeted test before each extraction.

## Technical risks

- Import side effects from engine.py remain active.
- process_tick may mix compute, memory, alerting and persistence.
- Moving DB writes before tests risks silent runtime drift.
- Moving send_alert before tests risks alert payload drift.

## Files

- JSON map: Docs\Audits\T002_ENGINE_INTERNAL_MAP_20260515_172740.json
- Markdown report: Docs\Audits\T002_ENGINE_INTERNAL_MAP_20260515_172740.md

