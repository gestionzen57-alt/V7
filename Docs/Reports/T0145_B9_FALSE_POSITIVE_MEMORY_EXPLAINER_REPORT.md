# T0145 — B9 False Positive Memory Explainer V0

## Résumé

T0145 explique pourquoi une similarité mémoire B9/B6 peut tromper.

Il prend une scène B9 enrichie par les briques précédentes :

```text
source quality
session
retest
center path
B9/B6 scene family
memory family
films proches
```

Puis il produit :

```text
b9_memory_false_positive_state
b9_memory_false_positive_score
b9_memory_false_positive_flags
b9_memory_comparison_state
b9_memory_similarity_caution_fr
b9_memory_difference_explanation_fr
b9_memory_technical_limits
```

## Doctrine

B9 lit la scène.
B6 compare les films.
T0145 explique les pièges de comparaison.

La ressemblance n'est pas une répétition.
Une mémoire proche reste une comparaison technique, pas une décision d'exécution.

## États

```text
MEMORY_FP_LOW
MEMORY_FP_MEDIUM
MEMORY_FP_HIGH
MEMORY_FP_REJECT_RAW_UNAVAILABLE
```

## Flags techniques

```text
FORCE_SNAPSHOT_DERIVED_NOT_RECOVERED_SUMMARY
PROXY_SOURCE_MODE
RECONSTRUCTED_VISIBILITY
RAW_NUANCED_NOT_CONFIRMED
LOW_CONFIDENCE_CAP
LOW_TRUST_SOURCE
RETEST_NOT_VISIBLE
RETEST_PENDING
RETEST_FAILURE_CONTEXT
SESSION_MISMATCH
SESSION_CONTEXT_WEAK
MEMORY_FAMILY_MISMATCH
SCENE_FAMILY_VARIANT
SCENE_FAMILY_INFERRED_OR_WEAK
CENTER_PATH_SHAPE_MISMATCH
CENTER_PATH_START_END_ONLY
CENTER_PATH_PROXY_EXTREMES
CENTER_PATH_NOT_VISIBLE
RAW_UNAVAILABLE
```

## Sorties

```text
B9_FALSE_POSITIVE_MEMORY_EXPLAINER_V0.md
B9_FALSE_POSITIVE_MEMORY_EXPLAINER_V0.json
B9_FALSE_POSITIVE_MEMORY_ROWS_V0.csv
B9_FALSE_POSITIVE_MEMORY_COUNTS_V0.csv
B9_FALSE_POSITIVE_MEMORY_FLAGS_V0.csv
B9_FALSE_POSITIVE_MEMORY_ENRICHED_SUMMARY_V0.json
B9_FALSE_POSITIVE_MEMORY_EXPLAINER_MANIFEST.json
B9_FALSE_POSITIVE_MEMORY_EXPLAINER_V0.zip
```

## Limites

Read-only.
Aucune écriture powerflow.db.
Aucune écriture tick_archive.db.
Aucun dashboard.
Aucun Telegram.
Aucun ordre directionnel.
Aucun taux de réussite.
Une scène proxy reste proxy.
RAW_UNAVAILABLE est rejeté de la mémoire active.
