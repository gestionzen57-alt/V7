# T004-F Capture Symbol Routing Operator Checklist

Date: 2026-05-15T17:23:13Z

## Context

- Thin symbol: USDJPY
- Reference symbols: GBPUSD, EURUSD
- T004-E likely cause: relative_sparsity
- This is not an engine/scoring issue yet. It is capture/routing/data-density.

## Risk flags

- LOGS_CONTAIN_USDJPY
- POSSIBLE_SYMBOL_ALLOWLIST_EXCLUDES_USDJPY
- USDJPY_REFERENCED_IN_CODE_SCAN

## Operator checklist

- [ ] Confirm USDJPY is visible/enabled in MT4 Market Watch or the source feed.
- [ ] Confirm the broker symbol name matches exactly: USDJPY vs USDJPY.suffix / USDJPYm / USDJPY.pro.
- [ ] Confirm the bridge/EA emits USDJPY ticks at the same cadence as GBPUSD/EURUSD.
- [ ] Confirm capture_bridge receives USDJPY before DB insertion.
- [ ] Confirm any symbol allowlist includes USDJPY exactly.
- [ ] Confirm no timeframe-specific filter excludes USDJPY.
- [ ] Confirm Core/powerflow.db is the DB used by the live capture path.
- [ ] Run a short live capture window and compare per-symbol tick counters.

## Code findings to inspect first

- Core/analyze_powerflow_from_0600_today.py:9 | symbol  = GBPUSD
- Core/analyze_powerflow_from_0600_today.py:15 | python analyze_powerflow_from_0600_today.py --db powerflow.db --symbol GBPUSD --start 2026-05-04T06:00:00+00:00
- Core/analyze_powerflow_from_0600_today.py:16 | python analyze_powerflow_from_0600_today.py --db powerflow.db --symbol GBPUSD --start-hour 6 --out report_0600.md
- Core/analyze_powerflow_from_0600_today.py:413 | ap.add_argument("--symbol", default="GBPUSD")
- Core/audit_usdjpy_capture.py:42 | def audit_usdjpy_capture(db_path='powerflow.db', symbol='USDJPY', max_rows_preview=500) -> Dict[str,Any]:
- Core/audit_usdjpy_capture.py:44 | rep={"symbol":symbol,"audit_type":"AUDIT_USDJPY_CAPTURE","timestamp_utc":datetime.now(timezone.utc).isoformat(),"db_path":db_path,"db_mode":"READ_ONLY","table":"force_snapshots","technical_risks":[]}
- Core/audit_usdjpy_capture.py:71 | rep['usdjpy_rows_preview_limit']=max_rows_preview
- Core/audit_usdjpy_capture.py:72 | rep['usdjpy_rows']=dict_rows(conn, f"SELECT * FROM force_snapshots WHERE UPPER({sym_col})=? LIMIT ?", (symbol, max_rows_preview))
- Core/audit_usdjpy_capture.py:75 | diag='NO_USDJPY_ROWS - CAPTURE INACTIVE OR SYMBOL NOT INSERTED'; rec='Check MT4 EA symbols list, bridge symbol routing, and force_snapshots insertion path'; action='URGENT'; rep['technical_risks']+=['USDJPY_NO_ROWS','CAPTURE_INACTIVE']
- Core/audit_usdjpy_capture.py:77 | diag='STALE DATA - CAPTURE INACTIVE OR INCOMPLETE'; rec='Check MT4 EA symbols list / Check bridge insertion logic / Verify USDJPY enabled in capture'; action='URGENT'; rep['technical_risks']+=['USDJPY_INSUFFICIENT_ROWS','CAPTURE_INCOMPLETE']
- Core/audit_usdjpy_capture.py:79 | diag='STALE TIMESTAMP - USDJPY NOT LIVE'; rec='Check MT4 EA live feed and bridge insertion for USDJPY'; action='URGENT'; rep['technical_risks']+=['USDJPY_STALE_TIMESTAMP','CAPTURE_NOT_LIVE']
- Core/audit_usdjpy_capture.py:81 | diag='USDJPY CAPTURE APPEARS ACTIVE'; rec='Continue monitoring row growth and timeframe completeness'; action='MONITOR'
- Core/audit_usdjpy_capture.py:91 | ap=argparse.ArgumentParser(description='Audit USDJPY capture in PowerFlow DB')
- Core/audit_usdjpy_capture.py:92 | ap.add_argument('--db', default='powerflow.db'); ap.add_argument('--symbol', default='USDJPY'); ap.add_argument('--out', default='output/audit_usdjpy_report.json'); ap.add_argument('--pretty', action='store_true'); ap.add_argument('--max-rows-preview', type=in
- Core/audit_usdjpy_capture.py:93 | a=ap.parse_args(); rep=audit_usdjpy_capture(a.db, a.symbol, a.max_rows_preview); write_report(rep,a.out)
- Core/audit_usdjpy_capture.py:95 | else: print(f"AUDIT_USDJPY_CAPTURE_OK | symbol={rep.get('symbol')} | rows={rep.get('rows_total')} | diagnosis={rep.get('diagnosis')} | out={a.out}")
- Core/audit_usdjpy_fast.py:4 | PowerFlow V7.2.1 — USDJPY Fast Audit
- Core/audit_usdjpy_fast.py:7 | Goal: classify USDJPY as LIVE / THIN / STALE / MISSING and produce a clear report.
- Core/audit_usdjpy_fast.py:140 | lines.append("# RAPPORT USDJPY CAPTURE AUDIT FAST — PowerFlow V7.2.1")
- Core/audit_usdjpy_fast.py:174 | lines.append("| Table | Rows USDJPY | Max timestamp | Age sec |")
- Core/audit_usdjpy_fast.py:213 | ap.add_argument("--symbol", default="USDJPY")
- Core/audit_usdjpy_fast.py:267 | report["interpretation"] = "USDJPY capture appears live in force_snapshots. If dashboard still shows stale, inspect dashboard surface generation."
- Core/audit_usdjpy_fast.py:268 | report["next_action"] = "Run scheduler once, hydrate dashboard, then verify USDJPY card freshness."
- Core/audit_usdjpy_fast.py:270 | report["interpretation"] = "USDJPY exists but has too few rows. Engine path may work, but capture depth is insufficient."
- Core/audit_usdjpy_fast.py:273 | report["interpretation"] = "USDJPY exists but is stale. This is a capture/data freshness problem, not a scheduler or dashboard decision problem."
- Core/audit_usdjpy_fast.py:274 | report["next_action"] = "Check MT4 EA symbol list, bridge incoming messages for USDJPY, and insertion into force_snapshots."
- Core/audit_usdjpy_fast.py:276 | report["interpretation"] = "No USDJPY rows found. Capture is not feeding USDJPY into force_snapshots."
- Core/audit_usdjpy_fast.py:277 | report["next_action"] = "Enable USDJPY in MT4 EA / bridge config, then rerun audit."
- Core/audit_usdjpy_fast.py:279 | report["interpretation"] = "Audit could not classify USDJPY cleanly. Inspect table discovery and runner output."
- Core/audit_usdjpy_fast.py:282 | json_out = Path(args.json_out) if args.json_out else core / "output" / f"usdjpy_audit_fast_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
- Core/audit_usdjpy_fast.py:283 | md_out = Path(args.md_out) if args.md_out else core / f"RAPPORT_USDJPY_CAPTURE_AUDIT_FAST_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md"
- Core/audit_usdjpy_fast.py:289 | print(f"USDJPY_AUDIT_FAST verdict={report['global_verdict']}")
- Core/CHECKPOINT_P0_LIVE_20260511.md:144 | .\run_p0_final_auto.ps1 -Symbol GBPUSD
- Core/CHECKPOINT_P0_LIVE_20260511.md:150 | .\run_p0_full_workflow.ps1 -Symbol GBPUSD -Once
- Core/CHECKPOINT_P0_LIVE_20260511.md:169 | -Symbol GBPUSD
- Core/CHECKPOINT_POWERFLOW_V76_20260513.md:77 | python run_trader_perception_stack_once.py --symbol GBPUSD
- Core/CHECKPOINT_POWERFLOW_V76_20260513.md:83 | python run_trader_perception_stack_once.py --symbols GBPUSD,EURUSD,USDJPY
- Core/CHECKPOINT_POWERFLOW_V76_20260513.md:89 | python run_trader_perception_stack_once.py --symbols GBPUSD,EURUSD,USDJPY --table
- Core/CHECKPOINT_POWERFLOW_V76_20260513.md:95 | python run_trader_perception_stack_once.py --symbols GBPUSD,EURUSD,USDJPY --table --watch-loop --interval 20
- Core/CHECKPOINT_POWERFLOW_V76_20260513.md:101 | python pf_trader_attention_alert_gate_once.py --symbols GBPUSD,EURUSD,USDJPY --pretty
- Core/CHECKPOINT_POWERFLOW_V76_20260513.md:107 | python run_trader_alert_loop.py --symbols GBPUSD,EURUSD,USDJPY --interval 20
- Core/CHECKPOINT_POWERFLOW_V76_20260513.md:118 | python run_trader_alert_loop.py --symbols GBPUSD,EURUSD,USDJPY --interval 15 --release-threshold 65 --loading-threshold 74 --send-telegram
- Core/CHECKPOINT_POWERFLOW_V76_20260513.md:170 | GBPUSD | WAKE | ELASTIC_RELEASE_LEGACY | MIXED | next=LOCK_ACCEPTANCE_AFTER_RELEASE
- Core/CHECKPOINT_POWERFLOW_V76_20260513.md:171 | EURUSD | WAKE | MULTI_TF_ELASTIC_LOADING | MIXED | next=TIME_COMP_BREAK
- Core/CHECKPOINT_POWERFLOW_V76_20260513.md:172 | USDJPY | WAKE | ELASTIC_RELEASE_LEGACY | PAIR_DOWN | next=LOCK_ACCEPTANCE_AFTER_RELEASE
- Core/CHECKPOINT_SESSION_FINAL_20260511.md:191 | .\run_p0_final_auto.ps1 -Symbol GBPUSD
- Core/CHECKPOINT_SESSION_FINAL_20260511.md:193 | .\run_dashboard_hydrate_outputs.ps1 -CorePath . -Symbol GBPUSD
- Core/CHECKPOINT_V73.md:13 | - Multi-symbol GBPUSD / EURUSD / USDJPY.
- Core/CHECKPOINT_V73.md:48 | python pf_price_schema_probe.py --db powerflow.db --symbols GBPUSD,EURUSD,USDJPY --pretty
- Core/CHECKPOINT_V73.md:49 | python run_topdown_market_reader_all_once.py --db powerflow.db --symbols GBPUSD,EURUSD,USDJPY --pretty
- Core/CHECKPOINT_V734B_B6_PARSER_HOTFIX.md:5 | Après hotfix, GBPUSD doit sortir proche de :
- Core/CHECKPOINT_V734B_B6_PARSER_HOTFIX.md:23 | python dashboard_normalize_b6_live_fusion.py --symbols GBPUSD,EURUSD,USDJPY --trade-symbol GBPUSD --output output/dashboard_surface/b6_live_fusion_dashboard.json --pretty
- Core/CHECKPOINT_V734B_B6_PARSER_HOTFIX.md:24 | python pf_powerflow_multiread_synthesis_once.py --symbols GBPUSD,EURUSD,USDJPY --output output/dashboard_surface/powerflow_multiread_synthesis.json --pretty
- Core/CHECKPOINT_V734_B6_MULTIREAD_SYNTHESIS.md:15 | python dashboard_normalize_b6_live_fusion.py --symbols GBPUSD,EURUSD,USDJPY --output output/dashboard_surface/b6_live_fusion_dashboard.json --pretty
- Core/CHECKPOINT_V734_B6_MULTIREAD_SYNTHESIS.md:16 | python pf_powerflow_multiread_synthesis_once.py --symbols GBPUSD,EURUSD,USDJPY --output output/dashboard_surface/powerflow_multiread_synthesis.json --pretty
- Core/CHECKPOINT_V735B_TRADER_COCKPIT_CLARITY.md:9 | EURUSD / USDJPY ne doivent plus apparaître en `WAKE_TRADER` quand ils sont seulement contexte.
- Core/CHECKPOINT_V735B_TRADER_COCKPIT_CLARITY.md:31 | python pf_trader_cockpit_once.py --symbols GBPUSD,EURUSD,USDJPY --trade-symbol GBPUSD --output output/dashboard_surface/trader_cockpit.json --txt output/dashboard_surface/trader_cockpit.txt --pretty
- Core/CHECKPOINT_V735_TRADER_COCKPIT.md:21 | python pf_trader_cockpit_once.py --symbols GBPUSD,EURUSD,USDJPY --trade-symbol GBPUSD --pretty
- Core/CHECKPOINT_V736_TRADER_JOURNAL_J1.md:14 | python pf_trader_journal_j1.py --symbols GBPUSD,EURUSD,USDJPY --pretty
- Core/CHECKPOINT_V73_TURBO_WRAPPER.md:20 | python scheduler_powerflow_turbo_wrapper.py --symbols GBPUSD,EURUSD,USDJPY
- Core/CHECKPOINT_V73_TURBO_WRAPPER.md:40 | python scheduler_powerflow_turbo_wrapper.py --symbols GBPUSD,EURUSD,USDJPY
- Core/CHECKPOINT_V73_TURBO_WRAPPER.md:48 | - `_pending_usdjpy_diag/`
- Core/check_tf_by_table.py:11 | WHERE symbol='GBPUSD'
- Core/check_tf_counts.py:11 | for row in conn.execute(q, ("GBPUSD",)).fetchall():
- Core/CLAUDE_md_V7.1.md:216 | python run_temporal_node_state_once.py --db powerflow.db --symbol GBPUSD --recent-minutes 180 --timeframes 1,5,15,30,60 --pretty
- Core/CLAUDE_md_V7.1.md:219 | python run_currency_energy_probe_once.py --db powerflow.db --symbol GBPUSD --timeframe 1 --bars 50 --pretty
- Core/CLAUDE_md_V7.1.md:228 | python run_orchestral_loop.py --db powerflow.db --symbol GBPUSD --tfs "1,5,15,30" --once --pretty
- Core/CLAUDE_md_V7.1.md:231 | python run_powerflow_dashboard_refresh_once.py --db powerflow.db --symbol GBPUSD --pretty
- Core/CLAUDE_md_V7.1.md:292 | python .\run_entropy_engine_once.py --db .\powerflow.db --symbol GBPUSD --pretty
- Core/CLAUDE_md_V72_FINAL_UPDATE.md:138 | .\run_p0_final_auto.ps1 -Symbol GBPUSD
- Core/CLAUDE_md_V72_FINAL_UPDATE.md:156 | .\run_dashboard_hydrate_outputs.ps1 -CorePath . -Symbol GBPUSD -Serve
- Core/CLAUDE_md_V72_FINAL_UPDATE.md:248 | .\run_p0_final_auto.ps1 -Symbol GBPUSD
- Core/CLAUDE_md_V72_FINAL_UPDATE.md:249 | .\run_dashboard_hydrate_outputs.ps1 -CorePath . -Symbol GBPUSD
- Core/CLAUDE_REBASE_POWERFLOW_V721_20260511.md:27 | - USDJPY audit disponible
- Core/CLAUDE_REBASE_POWERFLOW_V721_20260511.md:34 | - c97fb1c : Dashboard multiSymbol UI tabs + cross-validation card + USDJPY audit
- Core/CLAUDE_REBASE_POWERFLOW_V721_20260511.md:90 | c97fb1c — Dashboard: add multiSymbol UI tabs + cross-validation card + USDJPY audit
- Core/CLAUDE_REBASE_POWERFLOW_V721_20260511.md:112 | python scheduler_powerflow.py --once --symbols GBPUSD,EURUSD,USDJPY
- Core/CLAUDE_REBASE_POWERFLOW_V721_20260511.md:151 | ## 5. Dashboard UI + USDJPY audit — état consolidé
- Core/CLAUDE_REBASE_POWERFLOW_V721_20260511.md:156 | c97fb1c — Dashboard: add multiSymbol UI tabs + cross-validation card + USDJPY audit
- Core/CLAUDE_REBASE_POWERFLOW_V721_20260511.md:164 | Core/RAPPORT_DASHBOARD_UI_USDJPY_20260511.md

## Focused AST findings

### Core/capture_bridge.py

- line 143 | assign | dedup_key = f'{tick.symbol}_{tick.timeframe}_{bar_time}'
- line 157 | assign | snapshot = {'created_at': created_at, 'symbol': tick.symbol, 'timeframe': tick.timeframe, 'bid': _sf(raw.get('bid')), 'spread': _sf(raw.get('spread')), 'force_gbp': safe_f(raw.get('gbp')), 'force_usd': safe_f(raw.get('usd')), 'force_eur': safe_f(raw.get('eur')), 'force_jpy': safe_f(raw.get('jpy')), 'force_cad': safe_f(raw.get('ca
- line 84 | assign | symbol = raw.get('symbol', '').upper()
- line 85 | assign | tf = int(raw.get('tf', raw.get('timeframe', 0)))
- line 106 | assign | dev_a = raw.get('dev_A', raw.get('devA', symbol[:3])).lower()
- line 107 | assign | dev_b = raw.get('dev_B', raw.get('devB', symbol[3:6])).lower()
- line 197 | call | insert_force_snapshot(SNAPSHOT_DB_CONN, snapshot)
- line 289 | call | server.sockets[0].getsockname()
- line 303 | call | print(f'🔔 ALERT {sig.signal_type} {sig.symbol} M{sig.timeframe} event_at={ts}')
- line 84 | call | raw.get('symbol', '').upper()
- line 106 | call | raw.get('dev_A', raw.get('devA', symbol[:3])).lower()
- line 107 | call | raw.get('dev_B', raw.get('devB', symbol[3:6])).lower()
- line 124 | call | Tick(symbol=symbol, timeframe=tf, timestamp=event_dt, dev_a=dev_a, dev_b=dev_b, val_a=val_a, val_b=val_b, bid=bid, spread=spread, volume=volume, atr=atr)
- line 267 | assign | key = f'{tick.symbol}M{tick.timeframe}'
- line 306 | call | process_tick(tick, prev, brain, dummy_send_alert)
- line 201 | call | print(f'✅ Snapshot: {tick.symbol} M{tick.timeframe} bar={created_at[:16]}')
- line 84 | call | raw.get('symbol', '')
- line 106 | call | raw.get('dev_A', raw.get('devA', symbol[:3]))
- line 107 | call | raw.get('dev_B', raw.get('devB', symbol[3:6]))
- line 241 | call | json.loads(line)
- line 246 | call | print('[RAW]', 'symbol=', raw.get('symbol'), 'tf=', raw.get('tf'), 'timeframe=', raw.get('timeframe'), 'bar_time=', raw.get('bar_time'), 'server_time=', raw.get('server_time'), 'capture_time=', raw.get('capture_time'), 'event_time=', _format_event_time_debug(_parse_event_datetime(raw)), 'close=', raw.get('close'), 'bid
- line 106 | call | raw.get('devA', symbol[:3])
- line 107 | call | raw.get('devB', symbol[3:6])
- line 248 | call | raw.get('symbol')

### Core/db.py

- line 29 | assign | _SCHEMA_SQL = '\nCREATE TABLE IF NOT EXISTS signals (\n    id                      INTEGER PRIMARY KEY AUTOINCREMENT,\n    created_at              TEXT    NOT NULL,\n    symbol                  TEXT    NOT NULL,\n    timeframe               INTEGER NOT NULL,\n    signal_type             TEXT    NOT NULL,\n    dev_strong             
- line 388 | assign | _SELECT_JOIN = '\nSELECT\n    s.*,\n    c.bias          AS htf_bias,\n    c.bias_state    AS htf_bias_state,\n    c.scenario      AS htf_scenario,\n    c.aligned_count AS htf_aligned_count,\n    c.fractal_rank  AS htf_fractal_rank,\n    c.leader_tf     AS htf_leader_tf,\n    c.htf_bonus     AS htf_bonus,\n    c.details_json  AS htf_d
- line 407 | assign | raw = d.pop('htf_details_json', None)
- line 440 | assign | sql = _SELECT_JOIN + ' WHERE s.symbol = ? ORDER BY s.id DESC LIMIT ?'
- line 468 | assign | sig = {'symbol': 'GBPUSD', 'timeframe': 15, 'signal_type': 'CROSS', 'timestamp': time.time(), 'dev_strong': 'gbp', 'dev_weak': 'usd', 'score': 7, 'level': 'PREMIUM', 'spread_ok': True, 'volume_badge': 'HIGH', 'note': 'Croisement propre M15', 'price': 1.2734, 'convergence': {'tf1': 15, 'tf2': 60, 'label1': 'M15', 'label2': 'H
- line 476 | assign | htf = {'bias': 'GBP', 'bias_state': 'VALIDE', 'scenario': 'TENDANCE', 'aligned_count': 4, 'fractal_rank': 4, 'leader': 'M15', 'details': ['M15 ✅', 'M30 ✅', 'H1 ✅', 'H4 ❌'], 'htf_bonus': 2}
- line 244 | assign | signal_row = (created_at, sig.get('symbol', ''), int(sig.get('timeframe', 0)), sig.get('signal_type', ''), sig.get('dev_strong', ''), sig.get('dev_weak', ''), int(sig.get('score', 0)), sig.get('level', 'STANDARD'), _bool_to_int(sig.get('spread_ok', False)), sig.get('volume_badge'), sig.get('note', ''), sig.get('price'), is_post_ext
- line 286 | assign | details = htf.get('details', []) if htf else []
- line 292 | assign | htf_row = (signal_id, (htf or {}).get('bias'), (htf or {}).get('bias_state'), (htf or {}).get('scenario'), (htf or {}).get('aligned_count'), (htf or {}).get('fractal_rank'), (htf or {}).get('leader'), (htf or {}).get('htf_bonus'), details_json)
- line 344 | assign | row = (created_at, str(snapshot.get('symbol', '')).upper(), int(snapshot.get('timeframe', 0)), snapshot.get('bid'), snapshot.get('spread'), snapshot.get('force_gbp'), snapshot.get('force_usd'), snapshot.get('force_eur'), snapshot.get('force_jpy'), snapshot.get('force_cad'), snapshot.get('force_chf'), snapshot.get('force_aud'
- line 407 | call | d.pop('htf_details_json', None)
- line 409 | assign | d['htf_details'] = json.loads(raw) if raw else []
- line 441 | call | _safe_fetch(conn, sql, (symbol, int(limit)))
- line 492 | assign | legacy_row = (str(snapshot.get('created_at') or datetime.now(timezone.utc).isoformat()), str(snapshot.get('symbol', '')).upper(), int(snapshot.get('timeframe', 0)), snapshot.get('bid'), snapshot.get('spread'), snapshot.get('force_gbp'), snapshot.get('force_usd'), snapshot.get('force_eur'), snapshot.get('force_jpy'), snapshot.get('f
- line 530 | assign | v2_row = (str(snapshot.get('created_at') or datetime.now(timezone.utc).isoformat()), str(snapshot.get('symbol', '')).upper(), int(snapshot.get('timeframe', 0)), snapshot.get('bar_time'), snapshot.get('bar_close_time'), snapshot.get('server_time'), snapshot.get('capture_time'), _bool_to_int(snapshot.get('is_closed_bar')), snapsh
- line 203 | call | conn.execute('PRAGMA foreign_keys = ON;')
- line 205 | call | conn.execute('PRAGMA journal_mode = WAL;')
- line 208 | call | conn.executescript(_SCHEMA_SQL)
- line 269 | call | cur.execute('\n            INSERT INTO signals (\n                created_at, symbol, timeframe, signal_type,\n                dev_strong, dev_weak, score, level, spread_ok,\n                volume_badge, note, price,\n                is_post_extreme, post_extreme_side,\n                has_convergence, conv_tf1, conv_
- line 304 | call | cur.execute('\n            INSERT INTO context_htf (\n                signal_id, bias, bias_state, scenario,\n                aligned_count, fractal_rank, leader_tf,\n                htf_bonus, details_json\n            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)\n            ', htf_row)
- line 360 | call | cur.execute('\n            INSERT INTO force_snapshots (\n                created_at, symbol, timeframe, bid, spread,\n                force_gbp, force_usd, force_eur, force_jpy,\n                force_cad, force_chf, force_aud\n            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n            ', row)
- line 411 | assign | d['htf_details'] = []
- line 421 | call | cur.execute(sql, params)
- line 508 | call | cur.execute('\n            INSERT INTO force_snapshots (\n                created_at, symbol, timeframe, bid, spread,\n                force_gbp, force_usd, force_eur, force_jpy,\n                force_cad, force_chf, force_aud\n            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n            ', legacy_row)
- line 571 | call | cur.execute('\n            INSERT OR IGNORE INTO force_snapshots_v2 (\n                created_at, symbol, timeframe,\n                bar_time, bar_close_time, server_time, capture_time, is_closed_bar,\n                bid, ask, mid,\n                spread, spread_points, spread_price, spread_pips,\n                o
- line 246 | call | sig.get('symbol', '')
- line 288 | call | json.dumps(details, ensure_ascii=False)
- line 346 | call | str(snapshot.get('symbol', '')).upper()
- line 374 | call | _log(f'ERREUR insert_force_snapshot : {e}')
- line 409 | call | json.loads(raw)
- line 494 | call | str(snapshot.get('symbol', '')).upper()
- line 522 | call | _log(f'ERREUR insert_force_snapshot legacy: {e}')
- line 532 | call | str(snapshot.get('symbol', '')).upper()
- line 589 | call | _log(f'WARN insert_force_snapshot_v2: {e}')
- line 346 | call | str(snapshot.get('symbol', ''))
- line 494 | call | str(snapshot.get('symbol', ''))
- line 532 | call | str(snapshot.get('symbol', ''))
- line 346 | call | snapshot.get('symbol', '')
- line 494 | call | snapshot.get('symbol', '')
- line 532 | call | snapshot.get('symbol', '')

### Core/system_config.py

- line 16 | assign | PAIRS = ['GBPUSD', 'GBPJPY', 'EURUSD', 'USDJPY', 'EURGBP', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD']
- line 26 | assign | TIMEFRAMES = [1, 5, 15, 30, 60, 240]
- line 155 | assign | LOCK_DOMINANT_MIN = {tf: get_level_high(tf) for tf in [1, 5, 15, 30, 60, 240]}
- line 198 | assign | HTF_RADAR_ENABLED = True
- line 199 | assign | VOLUME_FILTER_ENABLED = True

## Log symbol evidence

- Core/logs/dashboard_hydrate_20260511_085215.log | {"USDJPY": 0, "GBPUSD": 9, "EURUSD": 0}
- Core/logs/dashboard_hydrate_20260511_085320.log | {"USDJPY": 0, "GBPUSD": 9, "EURUSD": 0}
- Core/logs/dashboard_hydrate_20260511_085941.log | {"USDJPY": 0, "GBPUSD": 14, "EURUSD": 0}
- Core/logs/dashboard_hydrate_20260511_090452.log | {"USDJPY": 0, "GBPUSD": 7, "EURUSD": 0}
- Core/logs/dashboard_hydrate_20260511_090720.log | {"USDJPY": 0, "GBPUSD": 16, "EURUSD": 0}
- Core/logs/dashboard_hydrate_20260511_091122.log | {"USDJPY": 0, "GBPUSD": 17, "EURUSD": 0}
- Core/logs/dashboard_hydrate_20260511_091410.log | {"USDJPY": 0, "GBPUSD": 17, "EURUSD": 0}
- Core/logs/dashboard_hydrate_20260511_091957.log | {"USDJPY": 0, "GBPUSD": 17, "EURUSD": 0}
- Core/logs/dashboard_hydrate_20260511_092150.log | {"USDJPY": 0, "GBPUSD": 17, "EURUSD": 0}
- Core/logs/dashboard_hydrate_20260511_092455.log | {"USDJPY": 0, "GBPUSD": 17, "EURUSD": 0}
- Core/logs/dashboard_hydrate_20260511_093327.log | {"USDJPY": 0, "GBPUSD": 17, "EURUSD": 0}
- Core/logs/dashboard_hydration_20260511_100259.log | {"USDJPY": 0, "GBPUSD": 17, "EURUSD": 0}
- Core/logs/dashboard_hydration_20260511_101057.log | {"USDJPY": 0, "GBPUSD": 17, "EURUSD": 0}
- Core/logs/dashboard_hydration_20260511_101339.log | {"USDJPY": 0, "GBPUSD": 17, "EURUSD": 0}
- Core/logs/dashboard_hydration_20260511_105043.log | {"USDJPY": 0, "GBPUSD": 17, "EURUSD": 0}
- Core/logs/scheduler.log | {"USDJPY": 54313, "GBPUSD": 57112, "EURUSD": 54620}
- Core/logs/scheduler_powerflow_v731_20260512_132650.log | {"USDJPY": 9, "GBPUSD": 37, "EURUSD": 9}
- Core/logs/scheduler_powerflow_v731_latest.log | {"USDJPY": 9, "GBPUSD": 37, "EURUSD": 9}
- Core/logs/task_scheduler.log | {"USDJPY": 67437, "GBPUSD": 107752, "EURUSD": 67437}

## Stop rule

Do not patch Core/engine.py, pf_engine_v6_core.py, or scoring modules for this issue.
Only capture/routing instrumentation or operator-side feed correction is justified at this stage.

## Next action

T004-G should add a lightweight read-only/operator capture health script or manual command that counts incoming ticks per symbol over a short window, without changing engine behavior.

