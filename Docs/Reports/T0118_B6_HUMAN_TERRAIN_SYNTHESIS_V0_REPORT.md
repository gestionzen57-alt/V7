# T0118 — B6 Human Terrain Synthesis V0

## Objet

Transformer la bibliothèque B6 en synthèse humaine lisible : quelles familles reviennent, quelles scènes valent mémoire, où raw nuance, où le proxy reste partiel, où le retest n’est pas explicite.

## Position dans la chaîne

```text
B9 lit la scène
T0112 qualifie la fiabilité
T0113 crée les cartes film
T0114 indexe les similarités
T0115 interroge les films proches
T0116 adapte une scène live
T0117 explique les pièges de similarité
T0118 synthétise le terrain humain
```

## Doctrine

B6 ne prédit pas. B6 compare des films. T0118 ne transforme jamais une récurrence en probabilité de succès.

## Entrées

```text
outputs/b6_film_library_v0/B6_FILM_CARDS_V0.json
outputs/b6_false_positive_context_v0/B6_FALSE_POSITIVE_CONTEXT_V0.json
```

## Sorties

```text
outputs/b6_human_terrain_synthesis_v0/B6_HUMAN_TERRAIN_SYNTHESIS_V0.md
outputs/b6_human_terrain_synthesis_v0/B6_HUMAN_TERRAIN_SYNTHESIS_V0.json
outputs/b6_human_terrain_synthesis_v0/B6_HUMAN_TERRAIN_FAMILY_COUNTS_V0.csv
outputs/b6_human_terrain_synthesis_v0/B6_HUMAN_TERRAIN_DATE_COUNTS_V0.csv
outputs/b6_human_terrain_synthesis_v0/B6_HUMAN_TERRAIN_PRIORITY_SCENES_V0.csv
outputs/b6_human_terrain_synthesis_v0/B6_HUMAN_TERRAIN_TECHNICAL_LIMITS_V0.csv
outputs/b6_human_terrain_synthesis_v0/B6_HUMAN_TERRAIN_FALSE_POSITIVE_FLAGS_V0.csv
outputs/b6_human_terrain_synthesis_v0/B6_HUMAN_TERRAIN_SYNTHESIS_V0.zip
```

## Contraintes

Read-only. Aucun DB write. Aucun dashboard. Aucun Telegram. Aucun BUY/SELL. Aucune probabilité de succès.
