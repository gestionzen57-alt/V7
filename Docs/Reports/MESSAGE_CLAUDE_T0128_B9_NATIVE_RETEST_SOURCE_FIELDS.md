Claude,

T0128 — B9 Native Retest Source Fields / T0111B est prêt.

Branche :
feat/t0128-b9-native-retest-source-fields

Commit proposé :
feat(t0128): add B9 native retest source fields

Objectif :
Porter nativement les champs retest dans les moments B9/T009, au lieu de dépendre uniquement d’une reconstruction tardive.

Fichiers livrés :

pf_t009_native_retest_source_fields.py
tools/build_t0128_b9_native_retest_source_fields.py
scripts/RUN_T0128_B9_NATIVE_RETEST_SOURCE_FIELDS_FROM_DOWNLOADS.ps1
tests/test_t0128_b9_native_retest_source_fields.py
samples/b9_native_retest_source_fields_v0/sample_t009_sequence_summary_retest_candidate.json
Docs/Reports/T0128_B9_NATIVE_RETEST_SOURCE_FIELDS_REPORT.md
Docs/Reports/T0128_B9_NATIVE_RETEST_SOURCE_FIELDS_MANIFEST.json
Docs/Reports/COMMANDES_T0128_B9_NATIVE_RETEST_SOURCE_FIELDS.md
Docs/Reports/MESSAGE_CLAUDE_T0128_B9_NATIVE_RETEST_SOURCE_FIELDS.md
outputs/b9_native_retest_source_fields_v0/B9_NATIVE_RETEST_SOURCE_FIELDS_V0.md
outputs/b9_native_retest_source_fields_v0/B9_NATIVE_RETEST_SOURCE_FIELDS_V0.json
outputs/b9_native_retest_source_fields_v0/B9_NATIVE_RETEST_SOURCE_FIELDS_ROWS_V0.csv
outputs/b9_native_retest_source_fields_v0/B9_NATIVE_RETEST_SOURCE_FIELDS_COUNTS_V0.csv
outputs/b9_native_retest_source_fields_v0/B9_NATIVE_RETEST_SOURCE_FIELDS_ENRICHED_SUMMARY_V0.json
outputs/b9_native_retest_source_fields_v0/B9_NATIVE_RETEST_SOURCE_FIELDS_MANIFEST.json
outputs/b9_native_retest_source_fields_v0/B9_NATIVE_RETEST_SOURCE_FIELDS_V0.zip

Tests :
python -m py_compile pf_t009_native_retest_source_fields.py tools\build_t0128_b9_native_retest_source_fields.py
python -m pytest tests\test_t0128_b9_native_retest_source_fields.py

Résultat attendu :
2 passed

Commande CLI :
python tools\build_t0128_b9_native_retest_source_fields.py --sequence-summary-json samples\b9_native_retest_source_fields_v0\sample_t009_sequence_summary_retest_candidate.json --output-dir outputs\b9_native_retest_source_fields_v0

Champs natifs :
retest_visible
retest_source
retest_zone
retest_start
retest_end
retest_result
retest_judgment_fr
retest_limits

États :
RETEST_NOT_VISIBLE
RETEST_PENDING
RETEST_ACCEPTED
RETEST_FAILED
FAILED_REINTEGRATION

Doctrine :
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l’effort.
Le retest juge une scène, il ne produit pas un ordre.

Limites :
Read-only.
Aucune écriture powerflow.db.
Aucune écriture tick_archive.db.
Aucun dashboard.
Aucun Telegram.
Aucun BUY/SELL.
Aucune probabilité de succès.
Un retest non visible reste explicitement non visible.
Une scène proxy ne devient jamais une vérité raw.

Prochain geste :
T0129 — B9 Effort / Résultat / Progrès Scorer V0.
