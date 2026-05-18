Claude,

T0117 — B6 False Positive Context V0 est prêt.

Branche :
feat/t0117-b6-false-positive-context-v0

Commit proposé :
feat(t0117): add B6 false positive context v0

Fichiers livrés :

tools/build_t0117_b6_false_positive_context_v0.py
scripts/RUN_T0117_B6_FALSE_POSITIVE_CONTEXT_V0_FROM_DOWNLOADS.ps1
tests/test_t0117_b6_false_positive_context_v0_contract.py
samples/b6_false_positive_context_v0/sample_t0115_similarity_query_result_v0.json
docs/Reports/T0117_B6_FALSE_POSITIVE_CONTEXT_V0_REPORT.md
docs/Reports/T0117_B6_FALSE_POSITIVE_CONTEXT_V0_MANIFEST.json
docs/Reports/COMMANDES_T0117_B6_FALSE_POSITIVE_CONTEXT_V0.md
docs/Reports/MESSAGE_CLAUDE_T0117_B6_FALSE_POSITIVE_CONTEXT_V0.md
outputs/b6_false_positive_context_v0/B6_FALSE_POSITIVE_CONTEXT_V0.json
outputs/b6_false_positive_context_v0/B6_FALSE_POSITIVE_CONTEXT_V0.md
outputs/b6_false_positive_context_v0/B6_FALSE_POSITIVE_CONTEXT_V0.csv
outputs/b6_false_positive_context_v0/B6_FALSE_POSITIVE_CONTEXT_V0_MANIFEST.json
outputs/b6_false_positive_context_v0/B6_FALSE_POSITIVE_CONTEXT_V0.zip

Tests :
python -m py_compile tools\build_t0117_b6_false_positive_context_v0.py
python -m pytest tests\test_t0117_b6_false_positive_context_v0_contract.py

Résultat attendu :
2 passed

Commande CLI :
python tools\build_t0117_b6_false_positive_context_v0.py --query-result-json outputs\b6_similarity_query_v0\B6_SIMILARITY_QUERY_RESULT_V0.json --output-dir outputs\b6_false_positive_context_v0 --top-k 5

Résultat sample :
matches_reviewed = 5
state_counts = B6_FALSE_POSITIVE_CONTEXT_MEDIUM: 5
cross_family_match_count = 0
low_trust_in_results = false
raw_unavailable_in_results = false

Phrase de cap :
La ressemblance n’est pas une répétition.
B6 montre les similarités, T0117 montre les pièges de comparaison.

Limites :
Read-only.
Aucune écriture powerflow.db.
Aucune écriture tick_archive.db.
Aucun dashboard.
Aucun Telegram.
Aucun BUY/SELL.
Aucune probabilité de succès.
Le score T0117 est un score de prudence technique, pas une probabilité de résultat.

Prochain geste attendu :
Review PR T0117, puis lancer T0118 — B6 Human Terrain Synthesis V0.
