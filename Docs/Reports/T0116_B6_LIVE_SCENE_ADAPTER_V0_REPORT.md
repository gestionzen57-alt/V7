# T0116 — B6 Live Scene Adapter V0

## Résumé exécutif

T0116 ajoute le pont propre entre une scène B9 actuelle et la query B6/T0115.

```text
B9 lit la scène.
T0116 adapte la scène.
T0115 interroge l'index T0114.
B6 compare les films.
```

T0116 ne reconstruit pas l'index, ne lit pas la DB, ne modifie pas le board, ne modifie pas la film library et ne produit aucune décision.

## Doctrine

```text
B6 ne prédit pas.
B6 compare des films.
Une query live est une reconnaissance de contexte, pas un signal.
Aucun BUY/SELL.
Aucune probabilité de succès.
Aucune écriture DB.
```

## Entrée

Un JSON scène/moment B9, par exemple :

```text
samples/b6_live_scene_adapter_v0/sample_b9_live_scene_v0.json
```

Le script accepte plusieurs formes :

```text
scene
current_scene
moment
query_scene
payload
film_card
moments[]
scenes[]
items[]
cards[]
```

## Sorties

```text
outputs/b6_live_scene_adapter_v0/B6_LIVE_SCENE_QUERY_PAYLOAD_V0.json
outputs/b6_live_scene_adapter_v0/B6_LIVE_SCENE_ADAPTER_REPORT_V0.md
outputs/b6_live_scene_adapter_v0/B6_LIVE_SCENE_ADAPTER_MANIFEST_V0.json
outputs/b6_live_scene_adapter_v0/B6_LIVE_SCENE_ADAPTER_V0.zip
```

## Champs adaptés pour T0115

```text
film_id
date
time_start
time_end
session
memory_family
memory_family_origin
source_family
summary_recovery_type
source_mode
data_visibility
confidence_cap
moment_type
label_fr
raw_agreement
proxy_vs_raw_verdict
proxy_raw_agreement_state
source_quality_state
b6_memory_candidate_state
raw_texture_role
raw_delta_pips
raw_range_pips
raw_tick_count
base
reaction
projection
judgment
limits
```

## Inférence memory_family

Si `memory_family` est déjà explicite, T0116 le garde et marque :

```text
memory_family_origin = explicit_payload
```

Sinon, T0116 infère une famille par heuristique visible :

```text
DIRECTIONAL_PROGRESS_MEMORY
FRICTION_ABSORPTION_MEMORY
ROTATION_BREATH_MEMORY
```

Le champ `memory_family_origin` garde toujours la trace de l'origine.

## Validation locale

```powershell
python -m py_compile tools\build_t0116_b6_live_scene_adapter_v0.py
python -m pytest tests\test_t0116_b6_live_scene_adapter_v0_contract.py
python tools\build_t0116_b6_live_scene_adapter_v0.py --input-json samples\b6_live_scene_adapter_v0\sample_b9_live_scene_v0.json --output-dir outputs\b6_live_scene_adapter_v0
```

Option compatible T0115 :

```powershell
python tools\build_t0115_b6_similarity_query_v0.py --similarity-index outputs\b6_similarity_index_v0\B6_SIMILARITY_INDEX_V0.json --query-json outputs\b6_live_scene_adapter_v0\B6_LIVE_SCENE_QUERY_PAYLOAD_V0.json --output-dir outputs\b6_live_scene_adapter_v0_t0115_query_validation --top-k 5
```

## Tests passés côté pack

```text
python3 -m py_compile tools/build_t0116_b6_live_scene_adapter_v0.py
python3 -m pytest -q tests/test_t0116_b6_live_scene_adapter_v0_contract.py

2 passed
```

## Limites techniques

```text
Read-only.
Aucune écriture powerflow.db.
Aucune écriture tick_archive.db.
Aucun dashboard.
Aucun Telegram.
Aucun BUY/SELL.
Aucune probabilité de succès.
T0116 ne compare pas lui-même les films.
T0116 ne reconstruit pas l'index T0114.
Si memory_family est heuristique, elle doit être auditée via memory_family_origin.
```

## Prochaine brique recommandée

```text
T0117 — B6 False Positive Context V0
```

But : expliquer pourquoi une similarité peut être trompeuse : source plus faible, raw moins visible, retest absent, famille inférée, contexte de session différent, source_family différente.
