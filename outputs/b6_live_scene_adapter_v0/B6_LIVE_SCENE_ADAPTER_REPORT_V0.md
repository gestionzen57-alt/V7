# T0116 — B6 Live Scene Adapter V0

## Résumé exécutif

T0116 convertit une scène B9 actuelle en payload JSON compatible T0115.
Il ne compare pas lui-même les films. Il prépare la scène pour la couche de query B6.

```text
B9 lit la scène.
T0116 adapte la scène.
T0115 interroge l'index.
B6 compare les films.
```

## Doctrine

```text
B6 ne prédit pas.
B6 compare des films.
Une query live est une reconnaissance de contexte, pas un signal.
Aucun BUY/SELL. Aucune probabilité de succès. Aucune écriture DB.
```

## Payload adapté

- film_id: `LIVE_SCENE_F4930E9A5C`
- date: `2026-05-18`
- time_start: `2026-05-18T10:15:00+00:00`
- time_end: `2026-05-18T10:23:00+00:00`
- session: `LONDON_SESSION`
- memory_family: `DIRECTIONAL_PROGRESS_MEMORY`
- memory_family_origin: `heuristic_text_directional_progress`
- source_family: `B9_LIVE_SCENE_ADAPTED`
- source_mode: `B9_LIVE_SCENE`
- data_visibility: `LIVE_SCENE_ADAPTED_FROM_PAYLOAD`
- proxy_vs_raw_verdict: `NUANCED_BY_RAW`
- source_quality_state: `SOURCE_QUALITY_LIVE_UNQUALIFIED`

## Lecture 4D pour T0115

- base: Base scene: Vague progressive live (T009_MOMENT_PROGRESSIVE_WAVE).
- reaction: Reaction live: raw role RAW_PROGRESS_CONFIRMED, delta 8.4, range 10.1, ticks 420.
- projection: Projection de lecture: progression/migration à comparer aux films directionnels, sans prédiction.
- judgment: Judgment technique: B6_LIVE_QUERY_ONLY_NOT_CANDIDATE, NUANCED_BY_RAW, SOURCE_QUALITY_LIVE_UNQUALIFIED.

## Qualité adaptateur

- adapter_state: `ADAPTER_READY_HEURISTIC_FAMILY`
- t0115_compatible: `True`
- raw_texture_visible: `True`
- missing_query_fields: `[]`

## Limites techniques

- Normalisation de payload uniquement.
- Pas de lecture DB.
- Pas d'écriture DB.
- Pas de dashboard.
- Pas de Telegram.
- Pas de BUY/SELL.
- Pas de probabilité de succès.
- Si `memory_family` n'est pas explicite, elle est inférée et tracée dans `memory_family_origin`.
