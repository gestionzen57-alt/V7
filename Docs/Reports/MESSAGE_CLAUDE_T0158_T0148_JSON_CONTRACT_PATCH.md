Claude,

T0158 — T0148 JSON Contract Patch Formalization V0 est prêt.

Branche :
feat/t0158-t0148-json-contract-patch

Commit proposé :
fix(t0158): formalize T0148 JSON contract keys

Objectif :
Formaliser le patch local validé sur `pf_t009_live_brief_once_runner.py` afin que T0148 lise correctement les sorties réelles de T0115/T0117.

Cause corrigée :
T0115 produit `similar_films`.
T0117 produit `false_positive_contexts`.
T0148 ne lisait pas ces clés dans `_as_list()`.

Patch :
Ajouter `similar_films` et `false_positive_contexts` aux clés lues par `_as_list()`.

Fichiers livrés :

```text
pf_t009_live_brief_once_runner.py
tools/apply_t0158_t0148_json_contract_patch.py
tests/test_t0158_t0148_json_contract_patch.py
samples/t0148_json_contract_patch_v0/sample_old_as_list.py
Docs/Reports/T0158_T0148_JSON_CONTRACT_PATCH_REPORT.md
Docs/Reports/T0158_T0148_JSON_CONTRACT_PATCH_MANIFEST.json
Docs/Reports/COMMANDES_T0158_T0148_JSON_CONTRACT_PATCH.md
Docs/Reports/MESSAGE_CLAUDE_T0158_T0148_JSON_CONTRACT_PATCH.md
```

Tests :

```text
python -m py_compile tools\apply_t0158_t0148_json_contract_patch.py
python -m pytest tests\test_t0158_t0148_json_contract_patch.py
python -m py_compile pf_t009_live_brief_once_runner.py
```

Validation attendue :

```text
brief_state = B9_LIVE_BRIEF_READY
match_count = 3
top_match_film_id = B6FC_20260511_1641_010496DB
false_positive_context_available = true
forbidden_language_hits = []
```

Doctrine :
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l'effort.
B6 compare les films.
Un contexte faux positif HIGH est une mémoire comparable avec piège technique fort, pas une absence de mémoire.

Limites :
Aucune écriture powerflow.db.
Aucune écriture tick_archive.db.
Aucun dashboard.
Aucun Telegram.
Aucun BUY/SELL.
Aucune probabilité de succès.

Prochain geste :
Review du patch minimal, puis continuer B9 MAX V3 sur T0159 / T0160.


## Correction V2

Le patcher ne bloque plus sur les termes BUY/SELL présents dans les garde-fous internes du code source. Le scan anti-langage interdit reste porté par les tests et sorties utilisateur T0148/T0155/T0157.
