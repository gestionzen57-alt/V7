# T0127 — B9 Timestamp Remap Guard V0

## Résumé exécutif

B9 ne cherche pas le signal.
B9 cherche la trace laissée par l'effort.
T0127 protège l'heure du film : une scène bien lue mais mal horodatée reste techniquement fragile.

## Counts

- Moments analysés : 3
- State : PASS_WITH_SHIFT_DETECTED
- Shifted/replay détectés : 3
- Real unknown : 0
- Remap required : 0

## Politique timestamp

| index | label | raw start | real start | policy | shift min | source |
|---:|---|---|---|---|---:|---|
| 1 | Centre de gravité qui descend | 22:00 | 08:00 | TIMESTAMP_SHIFT_DETECTED | -600 | REPLAY_REPORT_REMAP |
| 2 | Retest échoué / reprise refusée | 23:10 | 09:10 | TIMESTAMP_SHIFT_DETECTED | -600 | REPLAY_REPORT_REMAP |
| 3 | Vague progressive | 00:11 | 10:11 | TIMESTAMP_SHIFT_DETECTED | -600 | REPLAY_REPORT_REMAP |

## Limites techniques

- `TIMESTAMP_SHIFT_DETECTED` : lire le film avec `time_*_real`, pas avec l'heure replay brute.
- `TIMESTAMP_REMAP_REQUIRED` : le fichier peut être utile analytiquement mais pas comme preuve horaire terrain.
- `TIMESTAMP_REAL_UNKNOWN` : ne pas ancrer le moment dans une session sans source horaire externe.

## Ce que T0127 ne conclut pas

T0127 ne juge pas la direction, ne produit pas de BUY/SELL et ne calcule aucune probabilité de succès.
