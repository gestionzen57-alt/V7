# T0139 — B9 London / NY / Asian Replay Scorecard V0

## Résumé exécutif

- État : `REVIEW_REQUIRED`
- Fichiers traités : `1`
- KEEP : `0`
- REVIEW : `0`
- REJECT : `1`
- Moments : `3`

B9 ne cherche pas le signal. B9 cherche la trace laissée par l’effort. La session contextualise la scène ; elle ne décide pas.

## Counts par session

| Session | Fichiers | KEEP | REVIEW | REJECT | Moments | Score moyen |
|---|---:|---:|---:|---:|---:|---:|
| ASIAN | 1 | 0 | 0 | 1 | 3 | 0.3333 |

## Failure patterns

| Pattern | Count |
|---|---:|
| CENTER_PATH_MISSING | 1 |
| EFFORT_RESULT_PROGRESS_MISSING | 1 |
| RAW_UNAVAILABLE_ONLY | 1 |
| RETEST_FIELDS_MISSING | 1 |
| TIMESTAMP_POLICY_MISSING | 1 |

## Fichiers

| Decision | Session | Moments | Score | Fichier | Limites |
|---|---|---:|---:|---|---|
| REJECT | ASIAN | 3 | 0.3333 | `t009_sequence_summary_raw_calibrated.json` | RETEST_FIELDS_MISSING|EFFORT_RESULT_PROGRESS_MISSING|CENTER_PATH_MISSING|TIMESTAMP_POLICY_MISSING|RAW_UNAVAILABLE_ONLY |

## Ce que B9 ne doit pas conclure

- Aucun ordre d’exécution.
- Aucun taux de réussite.
- Une session ne transforme pas une scène proxy en vérité raw.
- Une similarité de comportement ne signifie pas répétition certaine.
