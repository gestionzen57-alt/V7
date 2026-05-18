# T0117 — B6 False Positive Context V0

## Phrase de cap

La ressemblance n’est pas une répétition. B6 montre les similarités, T0117 montre les pièges de comparaison.

## Résumé exécutif

- Query: `B6Q_PRECOMPUTED_B6FC_20260505_1413_BDE6E508`
- Scene: `B6FC_20260505_1413_BDE6E508`
- Famille mémoire: `DIRECTIONAL_PROGRESS_MEMORY`
- Matches revus: `5`
- États: `{'B6_FALSE_POSITIVE_CONTEXT_MEDIUM': 5}`

## Ce que T0117 fait

T0117 prend le résultat T0115 et explique les pièges techniques de comparaison : source différente, session différente, raw nuancé, retest absent, famille inférée, dimensions faibles, échelles de ticks ou de range différentes.

## Ce que T0117 ne fait pas

- Pas de prédiction.
- Pas de probabilité de succès.
- Pas de BUY/SELL.
- Pas d’écriture DB.
- Pas de dashboard.
- Pas de Telegram.

## Matches et pièges

### Rank 1 — B6FC_20260514_1903_E8F0918A

- Similarité T0115: `0.778821`
- État T0117: `B6_FALSE_POSITIVE_CONTEXT_MEDIUM`
- Score contexte faux positif: `0.37`
- Flags: `SESSION_DIFFERENCE, DIMENSION_WEAK_BASE_MOTION, MODERATE_SIMILARITY_SCORE`
- Lecture: Ressemblance utile mais partielle: B6 reconnait une famille, T0117 signale les ecarts a regarder avant toute lecture forte.
- Différences: Pieges techniques: session difference; dimension de similarite faible: base_motion; moderate similarity score.

### Rank 2 — B6FC_20260513_0200_5821F72C

- Similarité T0115: `0.764655`
- État T0117: `B6_FALSE_POSITIVE_CONTEXT_MEDIUM`
- Score contexte faux positif: `0.37`
- Flags: `SESSION_DIFFERENCE, DIMENSION_WEAK_BASE_MOTION, MODERATE_SIMILARITY_SCORE`
- Lecture: Ressemblance utile mais partielle: B6 reconnait une famille, T0117 signale les ecarts a regarder avant toute lecture forte.
- Différences: Pieges techniques: session difference; dimension de similarite faible: base_motion; moderate similarity score.

### Rank 3 — B6FC_20260513_0700_C66F0CA0

- Similarité T0115: `0.755217`
- État T0117: `B6_FALSE_POSITIVE_CONTEXT_MEDIUM`
- Score contexte faux positif: `0.37`
- Flags: `SESSION_DIFFERENCE, DIMENSION_WEAK_BASE_MOTION, MODERATE_SIMILARITY_SCORE`
- Lecture: Ressemblance utile mais partielle: B6 reconnait une famille, T0117 signale les ecarts a regarder avant toute lecture forte.
- Différences: Pieges techniques: session difference; dimension de similarite faible: base_motion; moderate similarity score.

### Rank 4 — B6FC_20260513_1700_10F2213C

- Similarité T0115: `0.741605`
- État T0117: `B6_FALSE_POSITIVE_CONTEXT_MEDIUM`
- Score contexte faux positif: `0.42`
- Flags: `SESSION_DIFFERENCE, DIMENSION_WEAK_BASE_MOTION, DIMENSION_WEAK_REACTION_PROFILE, MODERATE_SIMILARITY_SCORE`
- Lecture: Ressemblance utile mais partielle: B6 reconnait une famille, T0117 signale les ecarts a regarder avant toute lecture forte.
- Différences: Pieges techniques: session difference; dimension de similarite faible: base_motion; dimension de similarite faible: reaction_profile; moderate similarity score.

### Rank 5 — B6FC_20260512_1037_3A1AF089

- Similarité T0115: `0.740596`
- État T0117: `B6_FALSE_POSITIVE_CONTEXT_MEDIUM`
- Score contexte faux positif: `0.42`
- Flags: `SESSION_DIFFERENCE, DIMENSION_WEAK_BASE_MOTION, DIMENSION_WEAK_REACTION_PROFILE, MODERATE_SIMILARITY_SCORE`
- Lecture: Ressemblance utile mais partielle: B6 reconnait une famille, T0117 signale les ecarts a regarder avant toute lecture forte.
- Différences: Pieges techniques: session difference; dimension de similarite faible: base_motion; dimension de similarite faible: reaction_profile; moderate similarity score.

## Limites techniques

- Read-only: no powerflow.db write and no tick_archive.db write.
- Uses T0115 similarity query result as input; does not rebuild T0114 index.
- False-positive context score is a technical caution score, not an outcome probability.
- Retest visibility is limited to fields present in query result / film cards.
- No dashboard, no Telegram, no BUY/SELL, no probability of success.
