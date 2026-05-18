# T0130 — B9 Center Path Internal Film V0

## Résumé exécutif

T0130 ajoute à B9 une lecture du chemin interne du centre. La brique évite que B9 juge un moment uniquement par deux points, `center_start` et `center_end`.

Doctrine :

```text
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l’effort.
Ne lis pas l’absorption comme une direction.
Lis où elle déplace la mémoire.
```

## Champs ajoutés

```text
b9_center_path_version
b9_center_path_visibility
b9_center_path_points
b9_center_start
b9_center_end
b9_center_min
b9_center_max
b9_center_range_pips
b9_center_net_delta_pips
b9_center_max_favorable_excursion_pips
b9_center_max_adverse_excursion_pips
b9_center_inflexion_count
b9_center_path_shape
b9_internal_progress_state
b9_center_path_reading_fr
b9_center_path_limits
```

## États de forme

```text
STRAIGHT_PROGRESS_UP / DOWN
STAIR_STEP_PROGRESS_UP / DOWN
ROUND_TRIP_NO_PROGRESS
SPIKE_AND_RETRACE
CENTER_DRIFT_UP / DOWN
CENTER_LOCKED
TWO_POINT_DRIFT_UP / DOWN
CENTER_PATH_NOT_VISIBLE
```

## États de visibilité

```text
CENTER_PATH_VISIBLE
CENTER_PATH_PROXY_EXTREMES
CENTER_PATH_START_END_ONLY
CENTER_PATH_NOT_VISIBLE
```

## Validation sample

```text
moments = 5
total_missing_required_fields = 0
forbidden_language_hit_count = 0
preserved_field_changes = 0
pytest = 2 passed
```

## Limites techniques

- Si le chemin natif n’est pas visible, T0130 expose explicitement une visibilité limitée.
- Les extrêmes dérivés ne deviennent pas une chronologie raw.
- Le chemin interne est une aide de lecture de scène, pas un ordre.
- Aucun ordre d’exécution, aucune probabilité de succès.

## Prochaine brique

T0131 — B9 Memory Brief Injector V0.

Mode recommandé : GPT Pro étendue.
