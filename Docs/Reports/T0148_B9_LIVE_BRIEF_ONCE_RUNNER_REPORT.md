# T0148 — B9 Live Brief Once Runner V0

## Résumé

T0148 assemble une exécution CLI unique pour produire un brief B9/B6 live read-only.

Chaîne cible :

```text
T0147 latest scene candidate
+ T0116 adapter payload
+ T0115 similarity query
+ T0117/T0145 false positive context
+ T0118 terrain synthesis
+ T0134 French trader report
→ B9_LIVE_BRIEF_ONCE_V0
```

## Doctrine

```text
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l'effort.
B6 compare les films.
Le brief transmet une mémoire comparable, pas une décision d'exécution.
```

## Comportement runtime

Si toutes les entrées requises sont présentes :

```text
B9_LIVE_BRIEF_READY
```

Si une entrée manque :

```text
BLOCKED_MISSING_INPUTS
```

Si les résultats mémoire contiennent raw unavailable :

```text
BLOCKED_RAW_UNAVAILABLE_IN_MEMORY_RESULTS
```

## Entrées requises

```text
B9_LATEST_SCENE_CANDIDATE_V0.json
B6_LIVE_SCENE_QUERY_PAYLOAD_V0.json
B6_SIMILARITY_QUERY_RESULT_V0.json
B6_FALSE_POSITIVE_CONTEXT_V0.json
B6_HUMAN_TERRAIN_SYNTHESIS_V0.json
B9_FRENCH_TRADER_SCENE_REPORT_V0.json
```

## Sorties

```text
B9_LIVE_BRIEF_ONCE_V0.md
B9_LIVE_BRIEF_ONCE_V0.json
B9_LIVE_BRIEF_ONCE_MATCHES_V0.csv
B9_LIVE_BRIEF_ONCE_MANIFEST.json
B9_LIVE_BRIEF_ONCE_V0.zip
```

## Limites

Read-only. Aucune écriture DB. Aucun dashboard. Aucun Telegram. Aucun ordre directionnel. Aucun taux de réussite.
