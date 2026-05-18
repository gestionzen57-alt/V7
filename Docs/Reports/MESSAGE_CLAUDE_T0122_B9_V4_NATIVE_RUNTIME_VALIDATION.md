Claude,

T0122 — B9 V4 Native Runtime Validation est prêt.

Branche :
feat/t0122-b9-v4-native-runtime-validation

Commit proposé :
feat(t0122): add B9 V4 native runtime validation

Objectif :
Vérifier que T0121 enrichit réellement les summaries B9 en champs V4 natifs, sans modifier DB, dashboard ou Telegram.

Fichiers livrés :

tools/build_t0122_b9_v4_native_runtime_validation.py
scripts/RUN_T0122_B9_V4_NATIVE_RUNTIME_VALIDATION_FROM_DOWNLOADS.ps1
tests/test_t0122_b9_v4_native_runtime_validation.py
samples/b9_v4_native_runtime_validation_v0/sample_t009_sequence_summary_v4_candidate.json
Docs/Reports/T0122_B9_V4_NATIVE_RUNTIME_VALIDATION_REPORT.md
Docs/Reports/T0122_B9_V4_NATIVE_RUNTIME_VALIDATION_MANIFEST.json
Docs/Reports/COMMANDES_T0122_B9_V4_NATIVE_RUNTIME_VALIDATION.md
Docs/Reports/MESSAGE_CLAUDE_T0122_B9_V4_NATIVE_RUNTIME_VALIDATION.md
outputs/b9_v4_native_runtime_validation_v0/*

Tests :

python -m py_compile tools\build_t0122_b9_v4_native_runtime_validation.py
python -m pytest tests\test_t0122_b9_v4_native_runtime_validation.py

Commande CLI :

python tools\build_t0122_b9_v4_native_runtime_validation.py --sequence-summary-json samples\b9_v4_native_runtime_validation_v0\sample_t009_sequence_summary_v4_candidate.json --summarizer-py pf_t009_sequence_summarizer.py --output-dir outputs\b9_v4_native_runtime_validation_v0

Champs vérifiés :

V1 why/how
V2 causalité
V3 fractal scene
V4 center path / effort-result-progress / retest / source quality / timestamp policy

Doctrine :
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l’effort.
Ne lis pas l’absorption comme une direction.
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
Si T0122 passe, lancer T0123 — B9 V4 Replay Runtime Comparison.
