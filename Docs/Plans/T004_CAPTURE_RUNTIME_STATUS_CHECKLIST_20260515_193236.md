# T004-H Capture Runtime Status Checklist

Date: 2026-05-15T17:32:36Z

## Verdict

- Status: NO_CAPTURE_PROCESS_DETECTED_BUT_DB_RECENT
- DB: Core/powerflow.db
- DB modified_at: 2026-05-15T17:30:16Z
- DB modified_age_seconds: 143.272762
- Capture processes detected: 0
- Scheduler processes detected: 0
- Python processes detected: 0

## Recommendations

- DB changed recently without capture process visible in snapshot. Check scheduler/other writer process or short-lived capture.
- Do not change engine/scoring logic. This is live capture health and process supervision.

## DB tables

- context_htf | rows=9914 | symbol_col=None | time_col=None | max_time=None
- flow_packets | rows=824 | symbol_col=symbol | time_col=created_at | max_time=2026-05-15T17:29:29.665103+00:00
- force_snapshots | rows=19872 | symbol_col=symbol | time_col=created_at | max_time=2026-05-15T20:32:00+00:00
- force_snapshots_v2 | rows=16432 | symbol_col=symbol | time_col=created_at | max_time=2026-05-15T20:32:00+00:00
- nodes_v6 | rows=34 | symbol_col=symbol | time_col=detected_at | max_time=2026-04-29T15:40:00
- signals | rows=9914 | symbol_col=symbol | time_col=created_at | max_time=2026-05-15T17:30:19.423018+00:00
- sqlite_sequence | rows=7 | symbol_col=None | time_col=None | max_time=None
- zone_diagnostics | rows=1368 | symbol_col=symbol | time_col=logged_at | max_time=2026-05-02T17:01:09+00:00

## Capture-like processes

- none

## Scheduler-like processes

- none

## Latest logs

- Core/logs/scheduler.log | modified=2026-05-15T17:32:36Z | size=15664618
- Core/logs/task_scheduler.log | modified=2026-05-15T17:29:37Z | size=30363540
- Core/logs/p0_run_2026-05-15.log | modified=2026-05-15T17:23:05Z | size=3845
- Core/logs/p0_run_2026-05-14.log | modified=2026-05-14T23:23:04Z | size=4293
- Core/logs/p0_run_2026-05-13.log | modified=2026-05-13T23:22:59Z | size=4291
- Core/logs/telegram_v7.log | modified=2026-05-13T06:27:25Z | size=3665460
- Core/logs/p0_run_2026-05-12.log | modified=2026-05-12T23:23:17Z | size=5123
- Core/logs/scheduler_powerflow_v731_20260512_132650.log | modified=2026-05-12T13:26:51Z | size=18765
- Core/logs/scheduler_powerflow_v731_latest.log | modified=2026-05-12T13:26:51Z | size=18765
- Core/logs/p0_run_2026-05-11.log | modified=2026-05-11T23:22:59Z | size=6759
- Core/logs/dashboard_hydration_20260511_105043.log | modified=2026-05-11T10:51:32Z | size=516569
- Core/logs/dashboard_hydration_20260511_101339.log | modified=2026-05-11T10:14:30Z | size=481064
- Core/logs/dashboard_hydration_20260511_101057.log | modified=2026-05-11T10:11:46Z | size=480888
- Core/logs/dashboard_hydration_20260511_100259.log | modified=2026-05-11T10:03:51Z | size=473489
- Core/logs/dashboard_hydrate_20260511_093327.log | modified=2026-05-11T09:34:15Z | size=448113
- Core/logs/dashboard_hydrate_20260511_092455.log | modified=2026-05-11T09:25:50Z | size=439179
- Core/logs/dashboard_hydrate_20260511_092150.log | modified=2026-05-11T09:22:39Z | size=438105
- Core/logs/dashboard_hydrate_20260511_091957.log | modified=2026-05-11T09:20:46Z | size=434777
- Core/logs/dashboard_hydrate_20260511_091410.log | modified=2026-05-11T09:15:04Z | size=428882
- Core/logs/dashboard_hydrate_20260511_091122.log | modified=2026-05-11T09:12:10Z | size=428279

## Entry files

### Core/analyze_powerflow_from_0600_today.py
- line 8 | DB      = powerflow.db
- line 15 | python analyze_powerflow_from_0600_today.py --db powerflow.db --symbol GBPUSD --start 2026-05-04T06:00:00+00:00
- line 16 | python analyze_powerflow_from_0600_today.py --db powerflow.db --symbol GBPUSD --start-hour 6 --out report_0600.md
- line 412 | ap.add_argument("--db", default="powerflow.db")

### Core/audit_usdjpy_capture.py
- line 42 | def audit_usdjpy_capture(db_path='powerflow.db', symbol='USDJPY', max_rows_preview=500) -> Dict[str,Any]:
- line 92 | ap.add_argument('--db', default='powerflow.db'); ap.add_argument('--symbol', default='USDJPY'); ap.add_argument('--out', default='output/audit_usdjpy_report.json'); ap.add_argument('--pretty', action='store_true'); ap.add_argument('--max-rows-preview', type=in

### Core/audit_usdjpy_fast.py
- line 8 | Does not write powerflow.db.
- line 206 | lines.append("Read-only audit. No DB write. No capture_bridge patch.")
- line 212 | ap.add_argument("--db", default="powerflow.db")

### Core/capture_bridge.py
- line 229 | async def handle_connection(reader, writer, brain, on_tick):
- line 274 | await on_tick(tick, prev, brain)
- line 284 | async def start_bridge(brain, on_tick):
- line 286 | lambda r, w: handle_connection(r, w, brain, on_tick),
- line 305 | async def on_tick(tick, prev, brain):
- line 311 | asyncio.run(start_bridge(brain, on_tick))

### Core/CHECKPOINT_P0_LIVE_20260511.md
- line 12 | 2026-05-11 01:15Z → Résultat : M5/M15 reviennent dans powerflow.db.

### Core/CHECKPOINT_POWERFLOW_V76_20260513.md
- line 17 | capture_bridge.py
- line 19 | scheduler_powerflow_turbo_wrapper.py       # patch tenté, attention ancienne erreur indentation puis fix partiel
- line 53 | capture_bridge.py

### Core/CHECKPOINT_SESSION_FINAL_20260511.md
- line 16 | 2026-05-11 01:15Z     : M5/M15 reviennent dans powerflow.db
- line 142 | ✅ Aucune modification capture_bridge.py
- line 143 | ✅ Aucune écriture manuelle powerflow.db
- line 183 | Il ne faut pas toucher capture_bridge.py ni powerflow.db.

### Core/CHECKPOINT_V73.md
- line 48 | python pf_price_schema_probe.py --db powerflow.db --symbols GBPUSD,EURUSD,USDJPY --pretty
- line 49 | python run_topdown_market_reader_all_once.py --db powerflow.db --symbols GBPUSD,EURUSD,USDJPY --pretty

### Core/CHECKPOINT_V731_DAILY_FLOW_PACKET.md
- line 34 | Intégrer V7.3.1 dans `scheduler_powerflow_turbo_wrapper.py` après validation manuelle.

### Core/CHECKPOINT_V736_TRADER_JOURNAL_J1.md
- line 43 | python -m py_compile scheduler_powerflow_turbo_wrapper.py

### Core/CHECKPOINT_V73_TURBO_WRAPPER.md
- line 9 | - `scheduler_powerflow_turbo_wrapper.py`
- line 19 | python -m py_compile scheduler_powerflow_turbo_wrapper.py
- line 20 | python scheduler_powerflow_turbo_wrapper.py --symbols GBPUSD,EURUSD,USDJPY
- line 40 | python scheduler_powerflow_turbo_wrapper.py --symbols GBPUSD,EURUSD,USDJPY

### Core/CHECKPOINT_V74_DASHBOARD_FINAL.md
- line 42 | python -m py_compile dashboard_v74_contract_check.py scheduler_powerflow_turbo_wrapper.py pf_powerflow_telegram_gate_dedup_once.py

### Core/CHECKPOINT_V75_FINAL_DASHBOARD.md
- line 25 | - scheduler_powerflow_turbo_wrapper.py = orchestration

### Core/check_db.py
- line 4 | db_path = "powerflow.db"
- line 7 | print(f"❌ powerflow.db introuvable dans : {os.getcwd()}")
- line 10 | print(f"✅ powerflow.db trouvé")

### Core/CHECK_DB_SCHEMA_POWERFLOW.py
- line 4 | paths = ["powerflow.db", "db/powerflow.db"]

### Core/CHECK_EXTENDED_DB_V2.py
- line 9 | db = Path("powerflow.db")
- line 13 | raise SystemExit("Missing powerflow.db")

### Core/check_recent_signals.py
- line 3 | conn = sqlite3.connect("powerflow.db")

### Core/check_table_freshness.py
- line 3 | conn = sqlite3.connect("powerflow.db")

### Core/check_tf_by_table.py
- line 3 | conn = sqlite3.connect("powerflow.db")

### Core/check_tf_counts.py
- line 3 | conn = sqlite3.connect("powerflow.db")

### Core/CLAUDE_md_V7.1.md
- line 35 | capture_bridge.py              ← bridge MT4 live
- line 36 | powerflow.db                   ← mémoire SQLite
- line 204 | python run_regime_engine_once.py --db powerflow.db --pretty
- line 210 | python run_temporal_density_once.py --db powerflow.db --tfs 1,5,15 --summary --pretty
- line 213 | python run_spearman_gravity_once.py --db powerflow.db --tfs 1,5,15 --summary --pretty
- line 216 | python run_temporal_node_state_once.py --db powerflow.db --symbol GBPUSD --recent-minutes 180 --timeframes 1,5,15,30,60 --pretty
- line 219 | python run_currency_energy_probe_once.py --db powerflow.db --symbol GBPUSD --timeframe 1 --bars 50 --pretty
- line 228 | python run_orchestral_loop.py --db powerflow.db --symbol GBPUSD --tfs "1,5,15,30" --once --pretty
- line 231 | python run_powerflow_dashboard_refresh_once.py --db powerflow.db --symbol GBPUSD --pretty
- line 242 | capture_bridge.py
- line 243 | powerflow.db
- line 257 | ❌ Ne pas modifier capture_bridge.py
- line 258 | ❌ Ne pas écrire dans powerflow.db
- line 290 | python .\run_data_quality_guard_once.py --db .\powerflow.db --since 2026-05-12 --pretty --output .\output\data_quality_guard.json
- line 291 | python .\run_market_open_validator_once.py --db .\powerflow.db --since 2026-05-12 --recent-minutes 180 --pretty --output .\output\market_open_validator.json
- line 292 | python .\run_entropy_engine_once.py --db .\powerflow.db --symbol GBPUSD --pretty
- line 311 | 9. run_powerflow_dashboard_refresh_once.py

### Core/CLAUDE_md_V72_FINAL_UPDATE.md
- line 68 | M5/M15 restaurés dans powerflow.db.
- line 201 | ❌ NE PAS modifier capture_bridge.py sans accord explicite
- line 202 | ❌ NE PAS écrire manuellement dans powerflow.db
- line 265 | Ne repatche pas capture_bridge.py.
- line 266 | Ne touche pas powerflow.db.

### Core/CLAUDE_REBASE_POWERFLOW_V721_20260511.md
- line 38 | Ne pas toucher capture_bridge.py.
- line 39 | Ne pas écrire powerflow.db.
- line 102 | scheduler_powerflow.py
- line 112 | python scheduler_powerflow.py --once --symbols GBPUSD,EURUSD,USDJPY
- line 124 | Remove-Item .\logs\scheduler_powerflow.lock -Force
- line 138 | Mode      : python scheduler_powerflow.py --once
- line 319 | python run_audit_usdjpy_once.py --db powerflow.db --pretty
- line 353 | ✅ capture_bridge.py intouchable
- line 354 | ✅ powerflow.db read-only dans pf_*
- line 383 | python scheduler_powerflow.py --once --symbols GBPUSD,EURUSD,USDJPY
- line 389 | python run_audit_usdjpy_once.py --db powerflow.db --pretty

### Core/cockpit_reader.py
- line 235 | db_path        = request.args.get('db', 'powerflow.db')
- line 274 | db_path = request.args.get('db', 'powerflow.db')

### Core/cockpit_terminal.py
- line 6 | - Lire la DB powerflow.db.
- line 12 | python cockpit_terminal.py --db powerflow.db --symbols GBPUSD --timeframes 1,5,15,30 --once
- line 13 | python cockpit_terminal.py --db powerflow.db --symbols GBPUSD --timeframes 1,5,15,30 --loop-seconds 60
- line 35 | DB_PATH = "powerflow.db"
- line 353 | parser.add_argument("--db", default=DB_PATH, help="Chemin powerflow.db")

### Core/COMMIT_PREP_DASHBOARD_V72_FINAL.md
- line 81 | powerflow.db
- line 82 | powerflow.db-shm
- line 83 | powerflow.db-wal

### Core/create_v74_eie_docs.py
- line 21 | python run_confluence_alert.py --db powerflow.db --symbol GBPUSD --zone-tf 15 --once --dry-run
- line 26 | python run_confluence_alert.py --db powerflow.db --symbol GBPUSD --zone-tf 15 --once --send
- line 59 | 5. Brancher dans run_powerflow_live_stack_once.py.

### Core/CURRENT_STATE_POWERFLOW_V721_CENTRALISE_20260511.md
- line 46 | Command: python scheduler_powerflow.py --once
- line 69 | python run_audit_usdjpy_once.py --db powerflow.db --pretty

### Core/CURRENT_STATE_V7_OFFICIAL_20260511.md
- line 159 | capture_bridge.py                  ✅ LIVE — intouchable
- line 160 | powerflow.db                       ✅ mémoire centrale — aucune écriture manuelle
- line 249 | 7. Ne jamais modifier capture_bridge.py / powerflow.db sans décision architecte

### Core/CURRENT_STATE_V7_POST_P0_UPDATE.md
- line 44 | Effet                       : M5/M15 reviennent dans powerflow.db
- line 76 | capture_bridge.py             PASS   Bridge MT4 → powerflow.db LIVE
- line 77 | powerflow.db                  PASS   Mémoire SQLite centrale respirante
- line 202 | --db .\powerflow.db `
- line 216 | capture_bridge.py
- line 217 | powerflow.db
- line 232 | Ne pas écrire dans powerflow.db manuellement.

### Core/dashboard_hydration_failure_doctor.py
- line 10 | Does not modify engine files or powerflow.db.

### Core/DASHBOARD_HYDRATION_RUNNER_GUIDE.md
- line 11 | Il ne modifie pas les `pf_*` et n’écrit jamais dans `powerflow.db`.
- line 38 | --db powerflow.db --symbol GBPUSD --start <utc> --end <utc> --timeframes 1,5,15 --out output\force_kinematics_state.json --json
- line 41 | --db powerflow.db --symbol GBPUSD
- line 44 | --db powerflow.db --symbol GBPUSD
- line 47 | --db powerflow.db --symbol GBPUSD

### Core/DASHBOARD_HYDRATION_RUNNER_README.md
- line 32 | Le script ne modifie pas `powerflow.db`, n’importe pas de `pf_*`, et ne touche pas aux fichiers moteur.

### Core/dashboard_output_coverage_doctor.py
- line 7 | pf_* and does not write to powerflow.db.
- line 20 | 'regime_legacy': 'python run_regime_engine_once.py --db powerflow.db --pretty',
- line 21 | 'regime_hmm': 'python run_hmm_regime_engine_once.py --db powerflow.db --pretty',
- line 22 | 'kinematics': 'python run_force_kinematics_once.py --db powerflow.db --symbol GBPUSD --pretty',
- line 23 | 'force_kinematics': 'python run_force_kinematics_once.py --db powerflow.db --symbol GBPUSD --pretty',
- line 24 | 'energy': 'python run_currency_energy_probe_once.py --db powerflow.db --symbol GBPUSD --pretty',
- line 25 | 'density': 'python run_temporal_density_once.py --db powerflow.db --tfs 1,5,15 --summary --pretty',
- line 26 | 'wavelet': 'python run_wavelet_density_once.py --db powerflow.db --tfs 1,5,15 --summary --pretty',
- line 27 | 'spearman': 'python run_spearman_gravity_once.py --db powerflow.db --tfs 1,5,15 --summary --pretty',
- line 28 | 'fractal': 'python run_fractal_resonance_once.py --db powerflow.db --summary --pretty',
- line 29 | 'texture': 'python run_volatility_texture_once.py --db powerflow.db --summary --pretty',
- line 33 | 'dq': 'python run_data_quality_guard_once.py --db powerflow.db --since 2026-05-11T01:15:00 --tfs 1,5,15 --pretty --output output/data_quality_report.json',
- line 34 | 'memory': 'python run_memory_engine_once.py --db powerflow.db --summary --pretty',
- line 36 | 'node': 'python run_temporal_node_state_once.py --db powerflow.db --symbol GBPUSD --recent-minutes 60 --timeframes 1,5,15,30,60 --pretty',
- line 84 | lines += ['', '## Interpretation', '', '- MISSING is acceptable when the runtime did not produce that brick output yet.', '- DEGRADED means payload exists but no source UTC timestamp was found.', '- This doctor does not modify the engine and does not write to 

### Core/dashboard_server.py
- line 45 | def __init__(self, db_path: str = "powerflow.db"):
- line 56 | """Retourne le statut DB sans jamais ecrire dans powerflow.db."""
- line 295 | parser.add_argument("--db", type=str, default="powerflow.db")

### Core/db.py
- line 467 | conn = init_db("powerflow.db")

### Core/diagnose_usdjpy_thin_bottleneck.py
- line 15 | - Opens powerflow.db with uri mode=ro when possible
- line 416 | "Inspect capture_bridge symbol normalization for USDJPY broker suffix.",
- line 559 | "Do not patch capture_bridge.py until this diagnostic is reviewed.",
- line 560 | "Do not write powerflow.db.",
- line 572 | ap.add_argument("--db", default="powerflow.db")
- line 604 | "next_fix": ["Start from correct Core directory or restore powerflow.db."],

### Core/engine.py
- line 51 | DB_CONN = init_db("powerflow.db")
- line 1184 | async def process_temporal_nodes_cycle(symbols=None, db_path="powerflow.db"):

### Core/engine_temporal_nodes.py
- line 294 | db_path="powerflow.db",
- line 353 | db_path="powerflow.db",
- line 363 | db_path="powerflow.db",

### Core/film.py
- line 4 | Testé sur powerflow.db 06/05/2026.
- line 23 | DB_DEFAULT = "powerflow.db"

### Core/git_deploy_multisymbol.ps1
- line 32 | "scheduler_powerflow.py"
- line 53 | Copy-Item "scheduler_powerflow.py" (Join-Path $Core "scheduler_powerflow.py") -Force
- line 69 | & $PythonPath run_temporal_node_state_once.py --db powerflow.db --symbol GBPUSD --pretty
- line 73 | & $PythonPath run_cross_symbol_validation_once.py --db powerflow.db --symbols GBPUSD --pretty
- line 77 | & $PythonPath scheduler_powerflow.py --once --symbols GBPUSD
- line 92 | git add pf_cross_symbol_validation.py run_cross_symbol_validation_once.py scheduler_powerflow.py scheduler_config.json setup_windows_task_scheduler.ps1 `

### Core/inspect_db.py
- line 3 | conn = sqlite3.connect("powerflow.db")

### Core/INSPECT_FORCE_SNAPSHOTS_V2.py
- line 3 | con = sqlite3.connect("powerflow.db")

### Core/install_powerflow_pack.ps1
- line 14 | - Never touches powerflow.db or capture_bridge.py

### Core/lab.py
- line 4 | Testé sur powerflow.db 06/05/2026.
- line 21 | DB_DEFAULT = "powerflow.db"

### Core/lab_elastic.py
- line 19 | DB_DEFAULT = Path("powerflow.db")

### Core/lab_powerflow.py
- line 297 | parser.add_argument("--db", default="powerflow.db", help="Chemin powerflow.db")

### Core/LAB_POWERFLOW_README.md
- line 52 | python lab_powerflow.py --list-tfs --symbol GBPUSD --db powerflow.db
- line 53 | python lab_powerflow.py --probe-db --symbol GBPUSD --db powerflow.db
- line 59 | --db powerflow.db --symbol GBPUSD `
- line 66 | --db powerflow.db --symbol GBPUSD `
- line 79 | --db powerflow.db --symbol GBPUSD `
- line 91 | --db powerflow.db --symbol GBPUSD `
- line 104 | --db powerflow.db --symbol GBPUSD `
- line 109 | --db powerflow.db --symbol GBPUSD `
- line 122 | --db powerflow.db --symbol GBPUSD `
- line 133 | --db powerflow.db --symbol GBPUSD `
- line 145 | --db powerflow.db --symbol GBPUSD `
- line 158 | --db powerflow.db --symbol GBPUSD `
- line 169 | --db powerflow.db --symbol GBPUSD `
- line 180 | --db powerflow.db --symbol GBPUSD `
- line 209 | --db powerflow.db --symbol GBPUSD `
- line 245 | --db powerflow.db --symbol GBPUSD `
- line 252 | --db powerflow.db --symbol GBPUSD `
- line 261 | --db powerflow.db --symbol GBPUSD `
- line 329 | powerflow.db                ← données
- line 339 | --db powerflow.db --symbol GBPUSD `

### Core/lab_replay.py
- line 18 | default="powerflow.db",
- line 19 | help="Path to SQLite DB. Default: powerflow.db",

### Core/launcher.py
- line 186 | help='Mode démo (sans powerflow.db)'

### Core/LEXIQUE_GRAMMAIRE_V7_FINAL_20260511.md
- line 1242 | Ne touche pas capture_bridge.py.
- line 1243 | N’écrit pas powerflow.db.

### Core/note.py
- line 26 | DB_PATH = Path("powerflow.db")

### Core/P0_AUTOMATION_INTEGRATION_REPORT.md
- line 35 | capture_bridge visible : process python contenant capture_bridge.py
- line 113 | → Vérifier capture_bridge.py / EA / connexion MT4.
- line 143 | Les scripts sont livrés prêts à copier dans `Core/`. Ils doivent être validés localement avec le vrai `powerflow.db`, le vrai `run_p0_final_auto.ps1` et les vrais outputs. Aucun accès runtime local n'était disponible dans cet espace de génération.

### Core/P0_FINAL_ARCHITECT_DECISION.md
- line 107 | NE PAS modifier capture_bridge.py.
- line 108 | NE PAS écrire dans powerflow.db manuellement.

### Core/p0_final_validator.py
- line 335 | ap.add_argument("--db", default="powerflow.db")

### Core/P0_PASS_STRICT_PROMOTION_20260511.md
- line 57 | This gate does not patch `capture_bridge.py`, does not write `powerflow.db`, and does not modify `pf_*`.

### Core/p0_strict_promotion_gate.py
- line 18 | This script does not touch powerflow.db and does not patch pf_*.
- line 263 | "This gate does not patch `capture_bridge.py`, does not write `powerflow.db`, and does not modify `pf_*`.",

### Core/patch_cross_symbol_future_import_fix_v737d.py
- line 24 | # Backward compatibility: scheduler_powerflow.py still passes --symbols.

### Core/patch_cross_symbol_symbols_compat_v737d.py
- line 15 | # Backward compatibility: scheduler_powerflow.py still passes --symbols.

### Core/patch_scheduler_perception_spine_v76_fix.py
- line 3 | """Fix/patch scheduler_powerflow_turbo_wrapper.py for Perception Spine V7.6 Turbo.
- line 99 | parser.add_argument("--scheduler", default="scheduler_powerflow_turbo_wrapper.py")

## Stop rule

Do not patch engine/scoring modules until live capture activity is confirmed.

## Next action

If capture is inactive/stale, start the intended capture stack and rerun T004-G. If capture is active but DB stale, audit insertion target/path.

