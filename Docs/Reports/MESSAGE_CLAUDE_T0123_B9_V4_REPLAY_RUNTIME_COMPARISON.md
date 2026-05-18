Claude,

T0123 — B9 V4 Replay Runtime Comparison est prêt.

Branche :
feat/t0123-b9-v4-replay-runtime-comparison

Commit proposé :
feat(t0123): add B9 V4 replay runtime comparison

Objectif :
Comparer un summary B9 avant/après V4 pour vérifier que l’intégration T0121 enrichit les moments sans casser les labels FR, la source quality, les limites, la provenance ni les timestamps.

Fichiers livrés :

tools/build_t0123_b9_v4_replay_runtime_comparison.py
scripts/RUN_T0123_B9_V4_REPLAY_RUNTIME_COMPARISON_FROM_DOWNLOADS.ps1
tests/test_t0123_b9_v4_replay_runtime_comparison.py
samples/b9_v4_replay_runtime_comparison_v0/sample_t009_sequence_summary_before_v4.json
Docs/Reports/T0123_B9_V4_REPLAY_RUNTIME_COMPARISON_REPORT.md
Docs/Reports/T0123_B9_V4_REPLAY_RUNTIME_COMPARISON_MANIFEST.json
Docs/Reports/COMMANDES_T0123_B9_V4_REPLAY_RUNTIME_COMPARISON.md
Docs/Reports/MESSAGE_CLAUDE_T0123_B9_V4_REPLAY_RUNTIME_COMPARISON.md
outputs/b9_v4_replay_runtime_comparison_v0/*

Tests :
python -m py_compile tools\build_t0123_b9_v4_replay_runtime_comparison.py
python -m pytest tests\test_t0123_b9_v4_replay_runtime_comparison.py

Résultat attendu :
2 passed

Commande CLI :
python tools\build_t0123_b9_v4_replay_runtime_comparison.py --before-summary-json samples\b9_v4_replay_runtime_comparison_v0\sample_t009_sequence_summary_before_v4.json --output-dir outputs\b9_v4_replay_runtime_comparison_v0

T0123 vérifie :
- nombre de moments inchangé ;
- champs V4 présents ;
- labels/source/provenance/limites préservés ;
- timestamp policy explicite ;
- aucun BUY/SELL ;
- aucune probabilité de succès.

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
Si T0123 passe sur replay local, lancer T0124 — B9 V4 Regression Guard + Golden Replay Cases.
