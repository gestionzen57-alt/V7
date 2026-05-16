# T009_PHASE0_GPT1_REPORT

## Resume
- [x] Schema tick_archive.db OK
- [x] 8 feature flags OK
- [x] Formules scores multi-composants OK
- [x] 5 tests schema OK
- [x] Audit EA source OK

## Audit source
EA envoie : TIMER_1S_SAMPLE

### Evidence audit
- EA_PowerFlow_V6_Sonde_M1_PATCHED.mq4 utilise EventSetTimer(RefreshSeconds) avec RefreshSeconds=1, puis OnTimer(), puis SendToPython(json).
- EA_PowerFlow_V6_Sonde_NoM1_PATCHED.mq4 utilise EventSetTimer(RefreshSeconds) avec RefreshSeconds=5, puis OnTimer(), puis SendToPython(json).
- Aucune route OnTick() detectee comme emetteur direct vers PowerFlow dans les deux EA fournis.

### Implications
- Le mode source Phase 0 par defaut doit etre TIMER_1S_SAMPLE.
- Le flux M1 actuel est un micro-snapshot timer 1 seconde, pas un tick brut ONTICK_RAW.
- ONTICK_RAW reste reserve a un futur EA qui enverrait directement depuis OnTick().
- M1_BAR_PROXY reste un fallback de reconstruction depuis les barres M1, pas la source EA active.

## Livrables
- Core/tick_archive_schema.sql -> 74 lines, commit 090a69d
- Core/config_t009_flags.py -> 60 lines, commit 090a69d
- Core/core_score_formulas.py -> 222 lines, commit 090a69d
- tests/test_t009_phase0_schema.py -> 157 lines, 5 tests, commit 090a69d

## Tests
Commande executee :

```bash
python3 -m py_compile Core/config_t009_flags.py Core/core_score_formulas.py
python3 -m pytest tests/test_t009_phase0_schema.py -q
```

Resultat :

```text
.....                                                                    [100%]
5 passed in 0.41s
```

- test_schema_creation OK
- test_schema_constraints OK
- test_unique_index OK
- test_source_mode_constraint OK
- test_query_performance_120min OK

## Schema contract
- PRAGMA journal_mode=WAL
- PRAGMA synchronous=NORMAL
- PRAGMA busy_timeout=250
- tick_stream avec ts_epoch_ms, source_mode, capture_seq, gap_ms, quality_flags
- Constraints bid>0, ask>0, ask>=bid, mid>0, spread>=0
- source_mode IN ('ONTICK_RAW', 'TIMER_1S_SAMPLE', 'M1_BAR_PROXY')
- Index performance (symbol, ts_epoch_ms) et created_at_utc
- Unique index (symbol, ts_epoch_ms, capture_seq, source)
- Tables tick_archive_metadata et tick_rotation_log

## Feature flags contract
- POWERFLOW_T009_TICK_ARCHIVE_WRITE=0 par defaut
- POWERFLOW_T009_USE_BATTLEFIELD_FLUX=0 par defaut
- POWERFLOW_T009_SOURCE_MODE=auto par defaut
- POWERFLOW_T009_ALLOW_M1_FALLBACK=1 par defaut
- POWERFLOW_T009_ENABLE_TELEGRAM=0 par defaut
- POWERFLOW_T009_ENABLE_ENGINE_INTEGRATION=0 par defaut
- POWERFLOW_T009_MAX_LOOKBACK_MIN=120 par defaut
- POWERFLOW_T009_DRY_RUN=1 par defaut

## Score formulas contract
- battle_score = 0.30*activity + 0.25*compression + 0.20*dwell + 0.15*retest + 0.10*pressure_or_contention
- absorption_score = 0.35*pressure + 0.25*compression + 0.15*failed_displacement + 0.10*dwell + 0.10*activity + 0.05*spread_stability
- BATTLE_LEVEL_BORN thresholds implementees
- ABSORPTION_CLUSTER thresholds implementees
- data_visibility BLIND / STALE bloque BATTLE_LEVEL_BORN

## Blockers
Aucun blocker technique sur Phase 0.

Note operationnelle : git push vers GitHub a ete tente mais refuse par l'environnement reseau : Could not resolve host github.com (status 128). Le commit local et le patch restent disponibles pour application manuelle.

## ETA Phase 1A
GPT-2 peut demarrer immediatement apres recuperation de ce commit Phase 0.

Estimated: 6-7 h pour Phase 1A selon checkpoint T009.

## Git commits
- 090a69d [feat(t009): add tick_archive schema with source_mode + feature flags + score formulas]
- a7d7bff [docs(t009): add phase0 GPT1 report]

## Push status
- Branch locale : feat/t009-phase0-schema
- Push origin : FAILED dans cet environnement, DNS github.com indisponible.
