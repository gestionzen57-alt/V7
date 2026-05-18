Claude,

T0124 — B9 V4 Regression Guard + Golden Replay Cases V2 est prêt.

Branche :
feat/t0124-b9-v4-regression-guard-golden-replay-cases

Commit proposé :
feat(t0124): add B9 V4 regression guard golden replay cases

Objectif :
Figer les cas replay golden B9 V4 pour empêcher les régressions sur effort sans résultat, vague progressive, centre qui descend, retest échoué, respiration corrective, source quality et timestamp policy.

Fichiers livrés :

tools/build_t0124_b9_v4_regression_guard_golden_replay_cases.py
scripts/RUN_T0124_B9_V4_REGRESSION_GUARD_GOLDEN_REPLAY_CASES_FROM_DOWNLOADS.ps1
tests/test_t0124_b9_v4_regression_guard_golden_replay_cases.py
samples/b9_v4_regression_guard_golden_replay_cases_v0/sample_b9_v4_golden_replay_cases_input.json
Docs/Reports/T0124_B9_V4_REGRESSION_GUARD_GOLDEN_REPLAY_CASES_REPORT.md
Docs/Reports/T0124_B9_V4_REGRESSION_GUARD_GOLDEN_REPLAY_CASES_MANIFEST.json
Docs/Reports/COMMANDES_T0124_B9_V4_REGRESSION_GUARD_GOLDEN_REPLAY_CASES.md
Docs/Reports/MESSAGE_CLAUDE_T0124_B9_V4_REGRESSION_GUARD_GOLDEN_REPLAY_CASES.md
outputs/b9_v4_regression_guard_golden_replay_cases_v0/*

Tests :

python -m py_compile tools\build_t0124_b9_v4_regression_guard_golden_replay_cases.py
python -m pytest tests\test_t0124_b9_v4_regression_guard_golden_replay_cases.py

Résultat attendu :
2 passed

Commande CLI :

python tools\build_t0124_b9_v4_regression_guard_golden_replay_cases.py --input-summary-json samples\b9_v4_regression_guard_golden_replay_cases_v0\sample_b9_v4_golden_replay_cases_input.json --output-dir outputs\b9_v4_regression_guard_golden_replay_cases_v0

Résultat sample :

regression_guard_state = PASS
golden_case_count = 6
golden_cases_passed = 6
golden_cases_failed = 0
total_missing_required_fields = 0
forbidden_language_hit_count = 0

Cas golden protégés :

B9V4_GOLDEN_EFFORT_WITHOUT_RESULT
B9V4_GOLDEN_PROGRESSIVE_WAVE_UP
B9V4_GOLDEN_CENTER_MIGRATION_DOWN
B9V4_GOLDEN_RETEST_FAILED
B9V4_GOLDEN_CORRECTIVE_BREATH
B9V4_GOLDEN_SOURCE_QUALITY_TIMESTAMP

Doctrine :

B9 ne cherche pas le signal.
B9 cherche la trace laissée par l'effort.
Ne lis pas l'absorption comme une direction.
Lis où elle déplace la mémoire.

Limites :

Read-only.
Aucune écriture powerflow.db.
Aucune écriture tick_archive.db.
Aucun dashboard.
Aucun Telegram.
Aucun BUY/SELL.
Aucune probabilité de succès.

Prochain geste :
T0125 — B9 V4 Golden Replay Batch Runner.


## Correctif V2

V2 aligne pytest et CLI sur le fallback local déterministe afin d’éviter le drift observé quand pytest importe un contrat natif disponible dans le repo alors que la CLI exécutée depuis tools/ utilise le fallback. T0122/T0123 restent les validations natives du hook/summarizer.
