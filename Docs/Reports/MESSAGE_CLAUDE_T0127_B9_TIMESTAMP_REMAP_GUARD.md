Claude,

T0127 — B9 Timestamp Remap Guard V0 est prêt.

Branche :
feat/t0127-b9-timestamp-remap-guard

Commit proposé :
feat(t0127): add B9 timestamp remap guard

Objectif :
Détecter et qualifier les timestamps shifted/replay dans les summaries B9/T009 pour empêcher qu'une scène correctement lue soit mal ancrée dans le temps terrain.

Fichiers livrés :

tools/build_t0127_b9_timestamp_remap_guard_v0.py
scripts/RUN_T0127_B9_TIMESTAMP_REMAP_GUARD_FROM_DOWNLOADS.ps1
tests/test_t0127_b9_timestamp_remap_guard_v0.py
samples/b9_timestamp_remap_guard_v0/sample_t009_sequence_summary_shifted.json
samples/b9_timestamp_remap_guard_v0/sample_t009_replay_sequence_report.json
Docs/Reports/T0127_B9_TIMESTAMP_REMAP_GUARD_REPORT.md
Docs/Reports/T0127_B9_TIMESTAMP_REMAP_GUARD_MANIFEST.json
Docs/Reports/COMMANDES_T0127_B9_TIMESTAMP_REMAP_GUARD.md
Docs/Reports/MESSAGE_CLAUDE_T0127_B9_TIMESTAMP_REMAP_GUARD.md
outputs/b9_timestamp_remap_guard_v0/B9_TIMESTAMP_REMAP_GUARD_V0.md
outputs/b9_timestamp_remap_guard_v0/B9_TIMESTAMP_REMAP_GUARD_V0.json
outputs/b9_timestamp_remap_guard_v0/B9_TIMESTAMP_REMAP_GUARD_ROWS_V0.csv
outputs/b9_timestamp_remap_guard_v0/B9_TIMESTAMP_REMAP_GUARD_POLICY_COUNTS_V0.csv
outputs/b9_timestamp_remap_guard_v0/B9_TIMESTAMP_REMAP_GUARD_MANIFEST.json
outputs/b9_timestamp_remap_guard_v0/B9_TIMESTAMP_REMAP_GUARD_V0.zip

Tests :
python -m py_compile tools\build_t0127_b9_timestamp_remap_guard_v0.py
python -m pytest tests\test_t0127_b9_timestamp_remap_guard_v0.py

Résultat attendu :
2 passed

CLI :
python tools\build_t0127_b9_timestamp_remap_guard_v0.py --sequence-summary-json samples\b9_timestamp_remap_guard_v0\sample_t009_sequence_summary_shifted.json --replay-report-json samples\b9_timestamp_remap_guard_v0\sample_t009_replay_sequence_report.json --output-dir outputs\b9_timestamp_remap_guard_v0

Résultat sample :
timestamp_guard_state = PASS_WITH_SHIFT_DETECTED
moments_checked = 3
TIMESTAMP_SHIFT_DETECTED = 3
missing_required_field_counts = {}
forbidden_language_hits = []

États protégés :
TIMESTAMP_POLICY_OK
TIMESTAMP_SHIFT_DETECTED
TIMESTAMP_REMAP_REQUIRED
TIMESTAMP_REAL_UNKNOWN

Doctrine :
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l'effort.
Une scène bien lue mais mal horodatée reste techniquement fragile.

Limites :
Read-only.
Aucune écriture powerflow.db.
Aucune écriture tick_archive.db.
Aucun dashboard.
Aucun Telegram.
Aucun BUY/SELL.
Aucune probabilité de succès.

Prochain geste :
T0128 — Native Retest Source Fields / T0111B.
