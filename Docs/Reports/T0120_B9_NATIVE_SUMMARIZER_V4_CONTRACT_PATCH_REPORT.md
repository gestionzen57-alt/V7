# T0120 — B9 Native Summarizer V4 Contract Patch

## Résumé

T0120 fournit le contrat natif V4 pour le summarizer T009/B9.

Il ajoute une couche pure Python :

```text
pf_t009_sequence_summarizer_v4_contract.py
```

Cette couche peut être appelée par `pf_t009_sequence_summarizer.py` avant l'écriture JSON/Markdown.

## Doctrine

```text
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l'effort.
Ne lis pas l'absorption comme une direction.
Lis où elle déplace la mémoire.
```

## Champs V4 natifs

### V1 — Why / How

```text
what_happens_fr
why_it_matters_fr
how_it_happened_fr
mechanism_fr
proof_summary_fr
```

### V2 — Scene Causality

```text
previous_context_fr
cause_fr
reaction_fr
consequence_fr
memory_shift_fr
retest_role_fr
```

### V3 — Fractal Scene

```text
scene_id
scene_role
parent_scene
child_moments
session_chapter
fractal_reading_fr
```

### V4 — B9 native contract

```text
b9_center_path_state
b9_effort_result_progress_state
b9_progress_type
b9_native_retest_judgment
b9_source_quality_native_state
b9_v4_timestamp_policy
```

## Résultat de validation

```text
input_moments = 52
missing_required_field_counts = {}
forbidden_language_hits = []
tests = 2 passed
```

## Intégration recommandée

```python
from pf_t009_sequence_summarizer_v4_contract import enrich_sequence_summary_v4

summary = build_existing_t009_summary(...)
summary = enrich_sequence_summary_v4(summary)
write_summary(summary)
```

## Limites

```text
Read-only.
Aucune écriture powerflow.db.
Aucune écriture tick_archive.db.
Aucun dashboard.
Aucun Telegram.
Aucun BUY/SELL.
Aucune probabilité de succès.
Le retest non visible reste non visible.
Les champs proxy restent proxy.
```

## Prochaine étape

```text
T0121 — B9 Native Summarizer V4 Integration Patch
```
