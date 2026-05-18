# T0117 — B6 False Positive Context V0

## Résumé exécutif

T0117 ajoute la couche de prudence technique après T0115.

```text
T0115 trouve les films proches.
T0117 explique pourquoi cette proximité peut tromper.
```

Phrase de cap :

```text
La ressemblance n’est pas une répétition.
B6 montre les similarités, T0117 montre les pièges de comparaison.
```

## Entrée

```text
B6_SIMILARITY_QUERY_RESULT_V0.json
```

Produit par T0115, depuis l’index T0114.

## Sorties

```text
outputs/b6_false_positive_context_v0/B6_FALSE_POSITIVE_CONTEXT_V0.json
outputs/b6_false_positive_context_v0/B6_FALSE_POSITIVE_CONTEXT_V0.md
outputs/b6_false_positive_context_v0/B6_FALSE_POSITIVE_CONTEXT_V0.csv
outputs/b6_false_positive_context_v0/B6_FALSE_POSITIVE_CONTEXT_V0_MANIFEST.json
outputs/b6_false_positive_context_v0/B6_FALSE_POSITIVE_CONTEXT_V0.zip
```

## Logique

Pour chaque film proche, T0117 détecte les pièges techniques :

- famille mémoire inférée ;
- session différente ;
- source_family différente ;
- source_mode différent ;
- data_visibility différente ;
- raw agreement différent ;
- NUANCED_BY_RAW côté query ou match ;
- source_quality différente ;
- raw_texture_role différent ;
- delta raw opposé ;
- range raw très différent ;
- densité de ticks très différente ;
- retest absent ou faible ;
- dimension 4D faible.

## États T0117

```text
B6_FALSE_POSITIVE_CONTEXT_MINIMAL
B6_FALSE_POSITIVE_CONTEXT_LOW
B6_FALSE_POSITIVE_CONTEXT_MEDIUM
B6_FALSE_POSITIVE_CONTEXT_HIGH
```

Ces états sont des niveaux de prudence technique sur la comparaison. Ce ne sont pas des probabilités de succès.

## Validation sample

```text
matches_reviewed: 5
state_counts: B6_FALSE_POSITIVE_CONTEXT_MEDIUM = 5
cross_family_match_count: 0
low_trust_in_results: false
raw_unavailable_in_results: false
```

## Contraintes

```text
read-only
no powerflow.db write
no tick_archive.db write
no dashboard
no Telegram
no BUY/SELL
no probability of success
```

## Prochain bloc logique

T0118 — B6 Human Terrain Synthesis V0 : lire les familles B6 et produire une synthèse humaine des films qui reviennent.
