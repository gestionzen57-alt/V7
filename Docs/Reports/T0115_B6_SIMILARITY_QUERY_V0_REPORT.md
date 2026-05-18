# T0115 — B6 Similarity Query CLI/API V0

## Résumé exécutif

T0115 ajoute la couche d'interrogation read-only au-dessus de l'index T0114.

```text
B9 voit une scène actuelle.
T0112 qualifie sa fiabilité.
T0113 transforme les scènes historiques en cartes film.
T0114 construit l'index de similarité.
T0115 interroge l'index sans le reconstruire.
```

Phrase de cap :

```text
B6 ne prédit pas.
B6 compare des films.
Une similarité est un contexte de reconnaissance, jamais une probabilité de succès.
```

## Entrées

- `outputs/b6_similarity_index_v0/B6_SIMILARITY_INDEX_V0.json`
- soit `--query-film-id` pour interroger un film existant déjà indexé ;
- soit `--query-json` pour interroger une scène actuelle au format film-like ;
- soit les champs CLI `--base`, `--reaction`, `--projection`, `--judgment`, etc.

## Sorties

```text
outputs/b6_similarity_query_v0/B6_SIMILARITY_QUERY_RESULT_V0.json
outputs/b6_similarity_query_v0/B6_SIMILARITY_QUERY_RESULT_V0.md
outputs/b6_similarity_query_v0/B6_SIMILARITY_QUERY_RESULT_V0.csv
outputs/b6_similarity_query_v0/B6_SIMILARITY_QUERY_RESULT_V0_MANIFEST.json
outputs/b6_similarity_query_v0/B6_SIMILARITY_QUERY_RESULT_V0.zip
```

## Politique de similarité

T0115 conserve la politique T0114 V0 :

```text
QUERY_INDEX_ONLY_INTRA_MEMORY_FAMILY_V0
```

Conséquences :

- pas de mélange entre familles mémoire ;
- LOW_TRUST exclu des résultats actifs ;
- RAW_UNAVAILABLE exclu des résultats actifs ;
- chaque score conserve ses dimensions et son audit.

## Dimensions 4D

| Dimension | Poids | Sens |
|---|---:|---|
| base_motion | 0.25 | similarité de base / scène initiale |
| reaction_profile | 0.25 | similarité de réaction raw / texture |
| projection_shape | 0.25 | similarité de projection / forme du mouvement |
| judgment_clarity | 0.25 | similarité de jugement technique / qualité source |

## Exemple validé

Query :

```text
B6FC_20260505_1413_BDE6E508
```

Résultat :

```text
matches: 5
query_memory_family: DIRECTIONAL_PROGRESS_MEMORY
cross_family_match_count: 0
low_trust_in_results: false
raw_unavailable_in_results: false
```

Top match observé :

```text
B6FC_20260514_1903_E8F0918A
similarity_score: 0.778821
```

## Tests

```powershell
python -m py_compile tools\build_t0115_b6_similarity_query_v0.py
python -m pytest tests\test_t0115_b6_similarity_query_v0_contract.py
```

Résultat conteneur :

```text
2 passed
```

## Limites techniques

- T0115 ne reconstruit pas l'index T0114.
- T0115 lit seulement `B6_SIMILARITY_INDEX_V0.json`.
- Une scène sans `memory_family` explicite reçoit une inférence heuristique visible dans `memory_family_origin`.
- Les retests ne sont lus que si les film cards/index les exposent.
- Les scores sont des scores de reconnaissance comparative, pas des probabilités.

## Ce que T0115 peut dire

```text
Cette scène ressemble à ces films historiques de la même famille.
Voici les similarités.
Voici les différences.
Voici les limites techniques.
```

## Ce que T0115 ne doit pas conclure

```text
Cette scène va refaire pareil.
Probabilité de succès.
BUY/SELL.
Conseil d'exécution.
```

## Prochaine brique recommandée

```text
T0116 — B6 Live Scene Adapter V0
```

Objectif : convertir une scène B9 actuelle en payload query compatible T0115.
