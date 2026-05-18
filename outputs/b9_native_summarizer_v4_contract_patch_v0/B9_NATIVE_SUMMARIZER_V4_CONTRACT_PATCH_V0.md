# T0120 — B9 Native Summarizer V4 Contract Patch

## Résumé exécutif

T0120 ajoute un contrat V4 natif testable pour les summaries T009/B9.

Il ne remplace pas le moteur et ne modifie aucune base. Il fournit une couche pure Python que `pf_t009_sequence_summarizer.py` peut appeler avant l'écriture JSON/Markdown.

Phrase de cap :

```text
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l'effort.
Ne lis pas l'absorption comme une direction.
Lis où elle déplace la mémoire.
```

## Résultat CLI

```text
version = T0120_B9_NATIVE_SUMMARIZER_V4_CONTRACT_PATCH_V0
input_moments = 52
forbidden_language_hits = []
output_dir = outputs/b9_native_summarizer_v4_contract_patch_v0
```

## Champs natifs ajoutés

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

## Counts effort / résultat / progrès

```json
{
  "EFFORT_WITHOUT_RESULT": 6,
  "MOVEMENT_WITH_LIMITED_PROGRESS": 30,
  "EFFORT_RESULT_PROGRESS": 5,
  "LOCAL_FRICTION_OR_DECISION": 11
}
```

## Counts retest natif

```json
{
  "RETEST_JUDGMENT_NOT_VISIBLE_NATIVE_FIELD_REQUIRED": 52
}
```

## Intégration recommandée dans le summarizer

```python
from pf_t009_sequence_summarizer_v4_contract import enrich_sequence_summary_v4

summary = build_existing_t009_summary(...)
summary = enrich_sequence_summary_v4(summary)
write_summary(summary)
```

## Limites techniques

```text
Read-only.
Aucune écriture powerflow.db.
Aucune écriture tick_archive.db.
Aucun dashboard.
Aucun Telegram.
Aucun BUY/SELL.
Aucune probabilité de succès.
Les champs proxy restent proxy.
Un retest non visible reste non visible.
La politique timestamp ne réécrit pas silencieusement les heures shifted/replay.
```

## Prochaine brique

```text
T0121 — B9 Native Summarizer V4 Integration Patch
```

Objectif : brancher ce contrat dans `pf_t009_sequence_summarizer.py` si la revue architecte valide l'interface.
