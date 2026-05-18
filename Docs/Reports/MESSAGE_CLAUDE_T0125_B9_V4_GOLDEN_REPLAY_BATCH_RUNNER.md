Claude,

T0125 — B9 V4 Golden Replay Batch Runner V0 est prêt.

Branche :
feat/t0125-b9-v4-golden-replay-batch-runner

Commit proposé :
feat(t0125): add B9 V4 golden replay batch runner

Objectif :
Appliquer le guard T0124 sur plusieurs summaries replay JSON pour vérifier que B9 V4 tient sur un lot complet, pas seulement sur un sample isolé.

Fichiers livrés :

tools/build_t0125_b9_v4_golden_replay_batch_runner.py
scripts/RUN_T0125_B9_V4_GOLDEN_REPLAY_BATCH_RUNNER_FROM_DOWNLOADS.ps1
tests/test_t0125_b9_v4_golden_replay_batch_runner.py
samples/b9_v4_golden_replay_batch_runner_v0/sample_replay_summary_1.json
samples/b9_v4_golden_replay_batch_runner_v0/sample_replay_summary_2.json
samples/b9_v4_golden_replay_batch_runner_v0/sample_replay_summary_3.json
Docs/Reports/T0125_B9_V4_GOLDEN_REPLAY_BATCH_RUNNER_REPORT.md
Docs/Reports/T0125_B9_V4_GOLDEN_REPLAY_BATCH_RUNNER_MANIFEST.json
Docs/Reports/COMMANDES_T0125_B9_V4_GOLDEN_REPLAY_BATCH_RUNNER.md
Docs/Reports/MESSAGE_CLAUDE_T0125_B9_V4_GOLDEN_REPLAY_BATCH_RUNNER.md
outputs/b9_v4_golden_replay_batch_runner_v0/*

Tests :
python -m py_compile toolsuild_t0125_b9_v4_golden_replay_batch_runner.py
python -m pytest tests	est_t0125_b9_v4_golden_replay_batch_runner.py

Résultat attendu :
2 passed
batch_state = PASS
files_processed >= 3
files_failed = 0

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
T0126 — B9 V4 Runtime Replay Pack Collector, pour trouver automatiquement les summaries B9 locaux et préparer des lots réels pour T0125.
