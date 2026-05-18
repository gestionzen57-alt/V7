Claude,

T0115 — B6 Similarity Query CLI/API V0 est prêt.

Branche :
feat/t0115-b6-similarity-query-v0

Commit proposé :
feat(t0115): add B6 similarity query cli v0

Fichiers livrés :

tools/build_t0115_b6_similarity_query_v0.py
scripts/RUN_T0115_B6_SIMILARITY_QUERY_V0_FROM_DOWNLOADS.ps1
tests/test_t0115_b6_similarity_query_v0_contract.py
docs/Reports/T0115_B6_SIMILARITY_QUERY_V0_REPORT.md
docs/Reports/T0115_B6_SIMILARITY_QUERY_V0_MANIFEST.json
docs/Reports/COMMANDES_T0115_B6_SIMILARITY_QUERY_V0.md
docs/Reports/MESSAGE_CLAUDE_T0115_B6_SIMILARITY_QUERY_V0.md
outputs/b6_similarity_index_v0/B6_SIMILARITY_INDEX_V0.json
outputs/b6_similarity_query_v0/B6_SIMILARITY_QUERY_RESULT_V0.json
outputs/b6_similarity_query_v0/B6_SIMILARITY_QUERY_RESULT_V0.md
outputs/b6_similarity_query_v0/B6_SIMILARITY_QUERY_RESULT_V0.csv
outputs/b6_similarity_query_v0/B6_SIMILARITY_QUERY_RESULT_V0_MANIFEST.json
outputs/b6_similarity_query_v0/B6_SIMILARITY_QUERY_RESULT_V0.zip

Tests passés :

python -m py_compile tools\build_t0115_b6_similarity_query_v0.py
python -m pytest tests\test_t0115_b6_similarity_query_v0_contract.py

Commande CLI :

python tools\build_t0115_b6_similarity_query_v0.py --similarity-index outputs\b6_similarity_index_v0\B6_SIMILARITY_INDEX_V0.json --query-film-id B6FC_20260505_1413_BDE6E508 --output-dir outputs\b6_similarity_query_v0 --top-k 5

Résultat validé :

matches: 5
query_memory_family: DIRECTIONAL_PROGRESS_MEMORY
cross_family_match_count: 0
low_trust_in_results: false
raw_unavailable_in_results: false

Top match sample :

B6FC_20260514_1903_E8F0918A
similarity_score: 0.778821

Limites / blockers :

Read-only.
Aucune écriture powerflow.db.
Aucune écriture tick_archive.db.
Aucun dashboard.
Aucun Telegram.
Aucun BUY/SELL.
Aucune probabilité de succès.
T0115 interroge l'index T0114 sans le reconstruire.
Une scène actuelle sans memory_family explicite reçoit une inférence visible dans memory_family_origin.
Les retests restent limités aux champs présents dans les film cards/index.

Prochain geste attendu côté architecte :

Valider T0115 comme couche CLI/API query, puis lancer T0116 — B6 Live Scene Adapter V0 pour convertir les scènes B9 actuelles en payload compatible T0115.
