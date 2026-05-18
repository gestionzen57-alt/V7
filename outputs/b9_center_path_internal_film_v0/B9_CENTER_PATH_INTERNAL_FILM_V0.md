# T0130 — B9 Center Path Internal Film V0

## Résumé exécutif

B9 ne juge plus seulement deux photos du centre (`center_start -> center_end`).
T0130 ajoute une lecture du film interne du centre : chemin, range, excursions, inflexions, forme et limites.

B9 ne cherche pas le signal.
B9 cherche la trace laissée par l’effort.
Ne lis pas l’absorption comme une direction.
Lis où elle déplace la mémoire.

## Counts

- Moments lus : 5
- Champs requis manquants : 0
- Hits langage interdit : 0
- Changements champs préservés : 0

## Visibility

- CENTER_PATH_PROXY_EXTREMES: 1
- CENTER_PATH_VISIBLE: 4

## Shapes

- ROUND_TRIP_NO_PROGRESS: 1
- STAIR_STEP_PROGRESS_DOWN: 2
- STRAIGHT_PROGRESS_DOWN: 1
- STRAIGHT_PROGRESS_UP: 1

## Internal progress states

- INTERNAL_PROGRESS_VISIBLE: 2
- INTERNAL_ROUND_TRIP_CAUTION: 1
- INTERNAL_STAIR_STEP_PROGRESS: 2

## Limites techniques

- Si le chemin natif n’est pas visible, T0130 expose `CENTER_PATH_START_END_ONLY` ou `CENTER_PATH_PROXY_EXTREMES`.
- Les extrêmes dérivés ne sont pas durcis comme chronologie raw.
- Le score de chemin interne n’est pas une décision de trade.
- Aucun BUY/SELL, aucune probabilité de succès.

## Prochaine brique

T0131 — B9 Memory Brief Injector V0, à exécuter en GPT Pro étendue.
