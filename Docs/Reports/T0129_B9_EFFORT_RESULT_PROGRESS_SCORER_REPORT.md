# T0129 — B9 Effort / Résultat / Progrès Scorer V0

## Résumé exécutif

B9 ne cherche pas le signal.  
B9 cherche la trace laissée par l’effort.  
Ne lis pas l’absorption comme une direction.  
Lis où elle déplace la mémoire.

T0129 ajoute une couche de lecture physique native pour chaque moment B9/T009 : **effort**, **résultat**, **progrès**, rôle du mouvement et état de déplacement de mémoire.

## Pourquoi cette brique est P0

Une absorption peut bloquer le mouvement ou accompagner une progression par paliers. Le scorer empêche la confusion classique :

```text
Absorption + centre bloqué = frein / friction.
Absorption + centre qui avance = pression qui progresse.
```

## Champs ajoutés

```text
b9_effort_score
b9_result_score
b9_progress_score
b9_effort_result_ratio
b9_progress_type
b9_movement_role
b9_memory_shift_state
b9_effort_result_progress_state
b9_effort_result_progress_reading_fr
b9_effort_result_progress_limits
```

## États protégés

```text
EFFORT_WITHOUT_RESULT
PROGRESSIVE_WAVE
CORRECTIVE_BREATH
CENTER_MIGRATION
FAILED_DISPLACEMENT
ABSORPTION_WITH_PROGRESS
ABSORPTION_WITHOUT_PROGRESS
```

## Validation sample

```text
moments = 5
state_counts:
  ABSORPTION_WITHOUT_PROGRESS = 1
  PROGRESSIVE_WAVE = 1
  CENTER_MIGRATION = 1
  CORRECTIVE_BREATH = 1
  ABSORPTION_WITH_PROGRESS = 1
missing_required_fields = 0
forbidden_language_hits = 0
preserved_field_changes = 0
tests = 2 passed
```

## Limites techniques

- Scores relatifs à la source et au microfilm disponible.
- Une scène proxy ne devient jamais une vérité raw.
- T0129 ne remplace pas le retest natif T0128.
- T0129 ne produit aucune direction de trade, aucune probabilité et aucun ordre.
- Read-only : aucune écriture `powerflow.db`, aucune écriture `tick_archive.db`.
