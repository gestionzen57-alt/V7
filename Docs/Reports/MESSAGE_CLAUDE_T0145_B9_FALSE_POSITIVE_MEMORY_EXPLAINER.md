Claude,

T0145 — B9 False Positive Memory Explainer V0 est prêt.

Branche :
feat/t0145-b9-false-positive-memory-explainer

Commit proposé :
feat(t0145): add B9 false positive memory explainer v0

Objectif :
Expliquer pourquoi une similarité mémoire B9/B6 peut tromper : source plus faible, retest absent, session différente, center path différent, raw seulement nuancé, famille mémoire variante ou RAW_UNAVAILABLE.

Fichiers livrés :

pf_t009_false_positive_memory_explainer.py
tools/build_t0145_b9_false_positive_memory_explainer.py
scripts/RUN_T0145_B9_FALSE_POSITIVE_MEMORY_EXPLAINER_FROM_DOWNLOADS.ps1
tests/test_t0145_b9_false_positive_memory_explainer.py
samples/b9_false_positive_memory_explainer_v0/sample_t009_sequence_summary_false_positive_memory.json
Docs/Reports/T0145_B9_FALSE_POSITIVE_MEMORY_EXPLAINER_REPORT.md
Docs/Reports/T0145_B9_FALSE_POSITIVE_MEMORY_EXPLAINER_MANIFEST.json
Docs/Reports/COMMANDES_T0145_B9_FALSE_POSITIVE_MEMORY_EXPLAINER.md
Docs/Reports/MESSAGE_CLAUDE_T0145_B9_FALSE_POSITIVE_MEMORY_EXPLAINER.md
outputs/b9_false_positive_memory_explainer_v0/*

Tests :

python -m py_compile pf_t009_false_positive_memory_explainer.py tools\build_t0145_b9_false_positive_memory_explainer.py
python -m pytest tests\test_t0145_b9_false_positive_memory_explainer.py

Résultat attendu :
2 passed

Commande CLI :

python tools\build_t0145_b9_false_positive_memory_explainer.py --sequence-summary-json samples\b9_false_positive_memory_explainer_v0\sample_t009_sequence_summary_false_positive_memory.json --output-dir outputs\b9_false_positive_memory_explainer_v0

Résultat sample :

moments = 4
MEMORY_FP_LOW = 1
MEMORY_FP_HIGH >= 1
MEMORY_FP_REJECT_RAW_UNAVAILABLE = 1
raw_unavailable_allowed_count = 0
forbidden_language_hits = []

Doctrine :

B9 lit la scène.
B6 compare les films.
T0145 explique les pièges de comparaison.
La ressemblance n'est pas une répétition.

Limites :

Read-only.
Aucune écriture powerflow.db.
Aucune écriture tick_archive.db.
Aucun dashboard.
Aucun Telegram.
Aucun ordre directionnel.
Aucun taux de réussite.
Une scène proxy reste proxy.
RAW_UNAVAILABLE est rejeté de la mémoire active.

Prochain geste :
T0146 — B9 Memory Confidence Ladder V0.

Mode recommandé :
GPT Thinking étendue.
