# HOTFIX V7.3.2b — DAILY_LEVEL_GRAMMAR

## Problème corrigé

V7.3.2 classait parfois `ACCEPTED_ABOVE/BELOW` alors qu'il n'y avait aucun vrai contact avec le niveau.

Exemple :
- `RECENT_H4_HIGH`
- `touch_count = 0`
- `pierce_down_count = 82`
- ancien état : `ACCEPTED_BELOW`

Ce n'est pas une acceptation : c'est un contexte sous niveau.

## Nouvelles règles

- Pas de `ACCEPTED_ABOVE/BELOW` sans `touch_count > 0`.
- Si prix sous un niveau non touché : `CONTEXT_BELOW_LEVEL`.
- Si prix au-dessus d'un niveau non touché : `CONTEXT_ABOVE_LEVEL`.
- Les états `CONTEXT_*` ne génèrent pas de sweep.
- Les niveaux quasi-identiques H1/H4/current sont fusionnés en cluster via `aliases`.

## Résultat attendu

Moins de faux sweeps.
Moins d'acceptations artificielles.
Lecture plus proche du trader : un niveau non travaillé reste un contexte, pas un événement.
