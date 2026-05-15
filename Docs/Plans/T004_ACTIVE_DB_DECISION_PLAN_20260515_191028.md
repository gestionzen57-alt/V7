# T004-C Active DB Decision Report

Date: 2026-05-15T17:10:28Z

## Decision

- Decision: ROOT_DB_EMPTY_BUT_POPULATED_DB_EXISTS
- Populated DB count: 4
- Empty DB count: 1

## Key interpretation

The inspected root `powerflow.db` is empty, but populated DB files exist elsewhere.
USDJPY THIN cannot be treated as a symbol-specific issue until the active DB path is resolved.

## Recommendations

- Do not debug USDJPY symbol yet. First align diagnostics/runtime to the populated DB or confirm why root powerflow.db is empty.
- Inspect Core/db.py and Core/capture_bridge.py DB path constants/imports before any engine change.
- Run a read-only symbol density diagnostic against the best populated DB candidate.
- Best populated candidate by heuristic: Core/powerflow.db

## Root DB

- powerflow.db | exists=True | rows=0 | size=73728
  - context_htf rows=0
  - force_snapshots rows=0
  - force_snapshots_v2 rows=0
  - signals rows=0
  - sqlite_sequence rows=0

## Ranked populated DB candidates

- Core/powerflow.db | rows=58134 | size=17027072 | score=78
  - context_htf rows=9876
  - flow_packets rows=819
  - force_snapshots rows=19797
  - force_snapshots_v2 rows=16357
  - nodes_v6 rows=34
  - signals rows=9876
  - sqlite_sequence rows=7
  - zone_diagnostics rows=1368
- DB/powerflow.db | rows=4430 | size=962560 | score=14
  - context_htf rows=1124
  - force_snapshots rows=2144
  - nodes_v6 rows=34
  - signals rows=1124
  - sqlite_sequence rows=4
- db/powerflow.db | rows=4430 | size=962560 | score=14
  - context_htf rows=1124
  - force_snapshots rows=2144
  - nodes_v6 rows=34
  - signals rows=1124
  - sqlite_sequence rows=4
- output/lab_engine_v72_selftest.db | rows=158 | size=24576 | score=5
  - force_snapshots rows=158

## DB path reference files

- Core/CHECKPOINT_P0_LIVE_20260511.md
- Core/CHECKPOINT_SESSION_FINAL_20260511.md
- Core/CHECKPOINT_V73.md
- Core/CHECK_DB_SCHEMA_POWERFLOW.py
- Core/CHECK_EXTENDED_DB_V2.py
- Core/CLAUDE_REBASE_POWERFLOW_V721_20260511.md
- Core/CLAUDE_md_V7.1.md
- Core/CLAUDE_md_V72_FINAL_UPDATE.md
- Core/analyze_powerflow_from_0600_today.py
- Core/audit_usdjpy_capture.py
- Core/audit_usdjpy_fast.py
- Core/capture_bridge.py
- Core/check_db.py
- Core/check_recent_signals.py
- Core/check_table_freshness.py
- Core/check_tf_by_table.py
- Core/check_tf_counts.py
- Core/cockpit_agentic_state_v01.py
- Core/cockpit_reader.py
- Core/cockpit_terminal.py

## Focused AST findings

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

## Stop rule

Do not patch USDJPY logic or engine logic while active DB path is ambiguous.

## Next action

T004-D should run a read-only symbol density check against the best populated DB candidate, if any.

