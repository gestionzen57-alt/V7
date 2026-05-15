# T004-B Capture DB Path Audit

Date: 2026-05-15T17:05:38Z

## Executive finding

- Populated DB files found: Core/powerflow.db, DB/powerflow.db, db/powerflow.db, output/lab_engine_v72_selftest.db

## Recommendations

- At least one populated DB exists. Compare capture configured path against populated DB path before diagnosing USDJPY.
- DB path references found. Next step: inspect capture_bridge.py/db.py references in the audit report and align active DB path.
- capture_bridge.py contains relevant DB/capture references; audit insertion function before changing engine logic.

## Candidate DB paths

- powerflow.db | exists=True | size=73728 | total_rows=0
  - context_htf rows=0
  - force_snapshots rows=0
  - force_snapshots_v2 rows=0
  - signals rows=0
  - sqlite_sequence rows=0
- Core/powerflow.db | exists=True | size=17027072 | total_rows=58134
  - context_htf rows=9876
  - flow_packets rows=819
  - force_snapshots rows=19797
  - force_snapshots_v2 rows=16357
  - nodes_v6 rows=34
  - signals rows=9876
  - sqlite_sequence rows=7
  - zone_diagnostics rows=1368
- data/powerflow.db | exists=False | size=None | total_rows=None
- DB/powerflow.db | exists=True | size=962560 | total_rows=4430
  - context_htf rows=1124
  - force_snapshots rows=2144
  - nodes_v6 rows=34
  - signals rows=1124
  - sqlite_sequence rows=4
- db/powerflow.db | exists=True | size=962560 | total_rows=4430
  - context_htf rows=1124
  - force_snapshots rows=2144
  - nodes_v6 rows=34
  - signals rows=1124
  - sqlite_sequence rows=4

## Discovered DB files

- output/lab_engine_v72_selftest.db | exists=True | size=24576 | total_rows=158

## DB path references

- Core/analyze_powerflow_from_0600_today.py:8 | powerflow.db | DB      = powerflow.db
- Core/analyze_powerflow_from_0600_today.py:15 | powerflow.db | python analyze_powerflow_from_0600_today.py --db powerflow.db --symbol GBPUSD --start 2026-05-04T06:00:00+00:00
- Core/analyze_powerflow_from_0600_today.py:16 | powerflow.db | python analyze_powerflow_from_0600_today.py --db powerflow.db --symbol GBPUSD --start-hour 6 --out report_0600.md
- Core/analyze_powerflow_from_0600_today.py:85 | DB_PATH | def load_rows(db_path: str, symbol: str, start: datetime, end: datetime) -> List[Row]:
- Core/analyze_powerflow_from_0600_today.py:86 | sqlite3.connect | con = sqlite3.connect(db_path)
- Core/analyze_powerflow_from_0600_today.py:86 | DB_PATH | con = sqlite3.connect(db_path)
- Core/analyze_powerflow_from_0600_today.py:124 | DB_PATH | def get_db_range(db_path: str, symbol: str) -> Tuple[str, str, int]:
- Core/analyze_powerflow_from_0600_today.py:125 | sqlite3.connect | con = sqlite3.connect(db_path)
- Core/analyze_powerflow_from_0600_today.py:125 | DB_PATH | con = sqlite3.connect(db_path)
- Core/analyze_powerflow_from_0600_today.py:136 | DB_PATH | def latest_date_start(db_path: str, symbol: str, start_hour: int) -> Tuple[datetime, datetime]:
- Core/analyze_powerflow_from_0600_today.py:137 | DB_PATH | mn, mx, _ = get_db_range(db_path, symbol)
- Core/analyze_powerflow_from_0600_today.py:412 | powerflow.db | ap.add_argument("--db", default="powerflow.db")
- Core/audit_usdjpy_capture.py:8 | sqlite3.connect | def connect_ro(db_path: str) -> sqlite3.Connection:
- Core/audit_usdjpy_capture.py:8 | DB_PATH | def connect_ro(db_path: str) -> sqlite3.Connection:
- Core/audit_usdjpy_capture.py:9 | sqlite3.connect | return sqlite3.connect(f"file:{Path(db_path).as_posix()}?mode=ro", uri=True)
- Core/audit_usdjpy_capture.py:9 | DB_PATH | return sqlite3.connect(f"file:{Path(db_path).as_posix()}?mode=ro", uri=True)
- Core/audit_usdjpy_capture.py:42 | powerflow.db | def audit_usdjpy_capture(db_path='powerflow.db', symbol='USDJPY', max_rows_preview=500) -> Dict[str,Any]:
- Core/audit_usdjpy_capture.py:42 | DB_PATH | def audit_usdjpy_capture(db_path='powerflow.db', symbol='USDJPY', max_rows_preview=500) -> Dict[str,Any]:
- Core/audit_usdjpy_capture.py:44 | DB_PATH | rep={"symbol":symbol,"audit_type":"AUDIT_USDJPY_CAPTURE","timestamp_utc":datetime.now(timezone.utc).isoformat(),"db_path":db_path,"db_mode":"READ_ONLY","table":"force_snapshots","technical_risks":[]}
- Core/audit_usdjpy_capture.py:45 | DB_PATH | try: conn=connect_ro(db_path)
- Core/audit_usdjpy_capture.py:92 | powerflow.db | ap.add_argument('--db', default='powerflow.db'); ap.add_argument('--symbol', default='USDJPY'); ap.add_argument('--out', default='output/audit_usdjpy_report.json'); ap.add_argument('--pretty', action='store_true'); ap.ad
- Core/audit_usdjpy_fast.py:8 | powerflow.db | Does not write powerflow.db.
- Core/audit_usdjpy_fast.py:44 | sqlite3.connect | def table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
- Core/audit_usdjpy_fast.py:51 | sqlite3.connect | def find_symbol_tables(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
- Core/audit_usdjpy_fast.py:74 | sqlite3.connect | def count_symbol(conn: sqlite3.Connection, table_info: Dict[str, Any], symbol: str) -> Dict[str, Any]:
- Core/audit_usdjpy_fast.py:212 | powerflow.db | ap.add_argument("--db", default="powerflow.db")
- Core/audit_usdjpy_fast.py:221 | DB_PATH | db_path = core / args.db
- Core/audit_usdjpy_fast.py:227 | DB_PATH | "db": str(db_path),
- Core/audit_usdjpy_fast.py:234 | DB_PATH | if not db_path.exists():
- Core/audit_usdjpy_fast.py:238 | sqlite3.connect | conn = sqlite3.connect(str(db_path))
- Core/audit_usdjpy_fast.py:238 | DB_PATH | conn = sqlite3.connect(str(db_path))
- Core/capture_bridge.py:20 | DB_PATH | DB_PATH, FORCE_SNAPSHOTS_ENABLED,
- Core/capture_bridge.py:76 | DB_PATH | SNAPSHOT_DB_CONN = init_db(DB_PATH) if FORCE_SNAPSHOTS_ENABLED else None
- Core/CHECKPOINT_P0_LIVE_20260511.md:12 | powerflow.db | 2026-05-11 01:15Z → Résultat : M5/M15 reviennent dans powerflow.db.
- Core/CHECKPOINT_SESSION_FINAL_20260511.md:16 | powerflow.db | 2026-05-11 01:15Z     : M5/M15 reviennent dans powerflow.db
- Core/CHECKPOINT_SESSION_FINAL_20260511.md:143 | powerflow.db | ✅ Aucune écriture manuelle powerflow.db
- Core/CHECKPOINT_SESSION_FINAL_20260511.md:183 | powerflow.db | Il ne faut pas toucher capture_bridge.py ni powerflow.db.
- Core/CHECKPOINT_V73.md:48 | powerflow.db | python pf_price_schema_probe.py --db powerflow.db --symbols GBPUSD,EURUSD,USDJPY --pretty
- Core/CHECKPOINT_V73.md:49 | powerflow.db | python run_topdown_market_reader_all_once.py --db powerflow.db --symbols GBPUSD,EURUSD,USDJPY --pretty
- Core/check_db.py:4 | powerflow.db | db_path = "powerflow.db"
- Core/check_db.py:4 | DB_PATH | db_path = "powerflow.db"
- Core/check_db.py:6 | DB_PATH | if not os.path.exists(db_path):
- Core/check_db.py:7 | powerflow.db | print(f"❌ powerflow.db introuvable dans : {os.getcwd()}")
- Core/check_db.py:10 | powerflow.db | print(f"✅ powerflow.db trouvé")
- Core/check_db.py:11 | DB_PATH | print(f"   Taille : {os.path.getsize(db_path) / 1024:.1f} Ko")
- Core/check_db.py:14 | sqlite3.connect | conn = sqlite3.connect(db_path)
- Core/check_db.py:14 | DB_PATH | conn = sqlite3.connect(db_path)
- Core/CHECK_DB_SCHEMA_POWERFLOW.py:4 | powerflow.db | paths = ["powerflow.db", "db/powerflow.db"]
- Core/CHECK_DB_SCHEMA_POWERFLOW.py:15 | sqlite3.connect | con = sqlite3.connect(path)
- Core/CHECK_EXTENDED_DB_V2.py:9 | powerflow.db | db = Path("powerflow.db")
- Core/CHECK_EXTENDED_DB_V2.py:13 | powerflow.db | raise SystemExit("Missing powerflow.db")
- Core/CHECK_EXTENDED_DB_V2.py:15 | sqlite3.connect | con = sqlite3.connect(str(db))
- Core/check_recent_signals.py:3 | powerflow.db | conn = sqlite3.connect("powerflow.db")
- Core/check_recent_signals.py:3 | sqlite3.connect | conn = sqlite3.connect("powerflow.db")
- Core/check_table_freshness.py:3 | powerflow.db | conn = sqlite3.connect("powerflow.db")
- Core/check_table_freshness.py:3 | sqlite3.connect | conn = sqlite3.connect("powerflow.db")
- Core/check_tf_by_table.py:3 | powerflow.db | conn = sqlite3.connect("powerflow.db")
- Core/check_tf_by_table.py:3 | sqlite3.connect | conn = sqlite3.connect("powerflow.db")
- Core/check_tf_counts.py:3 | powerflow.db | conn = sqlite3.connect("powerflow.db")
- Core/check_tf_counts.py:3 | sqlite3.connect | conn = sqlite3.connect("powerflow.db")
- Core/CLAUDE_md_V7.1.md:36 | powerflow.db | powerflow.db                   ← mémoire SQLite
- Core/CLAUDE_md_V7.1.md:204 | powerflow.db | python run_regime_engine_once.py --db powerflow.db --pretty
- Core/CLAUDE_md_V7.1.md:210 | powerflow.db | python run_temporal_density_once.py --db powerflow.db --tfs 1,5,15 --summary --pretty
- Core/CLAUDE_md_V7.1.md:213 | powerflow.db | python run_spearman_gravity_once.py --db powerflow.db --tfs 1,5,15 --summary --pretty
- Core/CLAUDE_md_V7.1.md:216 | powerflow.db | python run_temporal_node_state_once.py --db powerflow.db --symbol GBPUSD --recent-minutes 180 --timeframes 1,5,15,30,60 --pretty
- Core/CLAUDE_md_V7.1.md:219 | powerflow.db | python run_currency_energy_probe_once.py --db powerflow.db --symbol GBPUSD --timeframe 1 --bars 50 --pretty
- Core/CLAUDE_md_V7.1.md:228 | powerflow.db | python run_orchestral_loop.py --db powerflow.db --symbol GBPUSD --tfs "1,5,15,30" --once --pretty
- Core/CLAUDE_md_V7.1.md:231 | powerflow.db | python run_powerflow_dashboard_refresh_once.py --db powerflow.db --symbol GBPUSD --pretty
- Core/CLAUDE_md_V7.1.md:243 | powerflow.db | powerflow.db
- Core/CLAUDE_md_V7.1.md:258 | powerflow.db | ❌ Ne pas écrire dans powerflow.db
- Core/CLAUDE_md_V7.1.md:290 | powerflow.db | python .\run_data_quality_guard_once.py --db .\powerflow.db --since 2026-05-12 --pretty --output .\output\data_quality_guard.json
- Core/CLAUDE_md_V7.1.md:291 | powerflow.db | python .\run_market_open_validator_once.py --db .\powerflow.db --since 2026-05-12 --recent-minutes 180 --pretty --output .\output\market_open_validator.json
- Core/CLAUDE_md_V7.1.md:292 | powerflow.db | python .\run_entropy_engine_once.py --db .\powerflow.db --symbol GBPUSD --pretty
- Core/CLAUDE_md_V72_FINAL_UPDATE.md:68 | powerflow.db | M5/M15 restaurés dans powerflow.db.
- Core/CLAUDE_md_V72_FINAL_UPDATE.md:202 | powerflow.db | ❌ NE PAS écrire manuellement dans powerflow.db
- Core/CLAUDE_md_V72_FINAL_UPDATE.md:266 | powerflow.db | Ne touche pas powerflow.db.
- Core/CLAUDE_REBASE_POWERFLOW_V721_20260511.md:39 | powerflow.db | Ne pas écrire powerflow.db.
- Core/CLAUDE_REBASE_POWERFLOW_V721_20260511.md:319 | powerflow.db | python run_audit_usdjpy_once.py --db powerflow.db --pretty
- Core/CLAUDE_REBASE_POWERFLOW_V721_20260511.md:354 | powerflow.db | ✅ powerflow.db read-only dans pf_*
- Core/CLAUDE_REBASE_POWERFLOW_V721_20260511.md:389 | powerflow.db | python run_audit_usdjpy_once.py --db powerflow.db --pretty

## Key file AST findings

### Core/capture_bridge.py

- line 76 | assign | SNAPSHOT_DB_CONN = init_db(DB_PATH) if FORCE_SNAPSHOTS_ENABLED else None
- line 197 | assign | inserted = insert_force_snapshot(SNAPSHOT_DB_CONN, snapshot)
- line 197 | call | insert_force_snapshot(SNAPSHOT_DB_CONN, snapshot)

### Core/db.py

- line 467 | assign | conn = init_db('powerflow.db')
- line 196 | assign | parent = os.path.dirname(os.path.abspath(db_path))
- line 200 | assign | conn = sqlite3.connect(db_path, check_same_thread=False)
- line 201 | assign | conn.row_factory = sqlite3.Row
- line 200 | call | sqlite3.connect(db_path, check_same_thread=False)
- line 203 | call | conn.execute('PRAGMA foreign_keys = ON;')
- line 205 | call | conn.execute('PRAGMA journal_mode = WAL;')
- line 208 | call | conn.executescript(_SCHEMA_SQL)
- line 209 | call | conn.commit()
- line 269 | call | cur.execute('\n            INSERT INTO signals (\n                created_at, symbol, timeframe, signal_type,\n                dev_strong, dev_weak, score, level, spread_ok,\n                volume_badge, note, price,\n                is_po
- line 304 | call | cur.execute('\n            INSERT INTO context_htf (\n                signal_id, bias, bias_state, scenario,\n                aligned_count, fractal_rank, leader_tf,\n                htf_bonus, details_json\n            ) VALUES (?, ?, ?, ?
- line 315 | call | conn.commit()
- line 360 | call | cur.execute('\n            INSERT INTO force_snapshots (\n                created_at, symbol, timeframe, bid, spread,\n                force_gbp, force_usd, force_eur, force_jpy,\n                force_cad, force_chf, force_aud\n           
- line 370 | call | conn.commit()
- line 421 | call | cur.execute(sql, params)
- line 508 | call | cur.execute('\n            INSERT INTO force_snapshots (\n                created_at, symbol, timeframe, bid, spread,\n                force_gbp, force_usd, force_eur, force_jpy,\n                force_cad, force_chf, force_aud\n           
- line 519 | call | conn.commit()
- line 571 | call | cur.execute('\n            INSERT OR IGNORE INTO force_snapshots_v2 (\n                created_at, symbol, timeframe,\n                bar_time, bar_close_time, server_time, capture_time, is_closed_bar,\n                bid, ask, mid,\n    
- line 586 | call | conn.commit()
- line 374 | call | _log(f'ERREUR insert_force_snapshot : {e}')
- line 522 | call | _log(f'ERREUR insert_force_snapshot legacy: {e}')
- line 589 | call | _log(f'WARN insert_force_snapshot_v2: {e}')

### Core/system_config.py

- line 188 | assign | DB_PATH = 'powerflow.db'
- line 212 | assign | DB_CONTEXT_ENABLED = False

### Core/pf_multi_symbol_db.py

- line 32 | assign | path = Path(db_path)
- line 112 | assign | conn = connect_readonly(db_path)
- line 35 | call | sqlite3.connect(f'file:{path}?mode=ro', uri=True)
- line 61 | call | conn.execute(sql, params).fetchall()
- line 61 | call | conn.execute(sql, params)

### Core/capture_bridge.py

- line 76 | assign | SNAPSHOT_DB_CONN = init_db(DB_PATH) if FORCE_SNAPSHOTS_ENABLED else None
- line 197 | assign | inserted = insert_force_snapshot(SNAPSHOT_DB_CONN, snapshot)
- line 197 | call | insert_force_snapshot(SNAPSHOT_DB_CONN, snapshot)

## Runtime behavior

- DB inspection is read-only.
- No runtime wiring.
- No dashboard files touched.

## Next action

If no populated DB is found, stop USDJPY-specific debugging and fix active capture/DB path first.
If a populated DB is found elsewhere, point diagnostics at that DB or fix the runtime DB target.

