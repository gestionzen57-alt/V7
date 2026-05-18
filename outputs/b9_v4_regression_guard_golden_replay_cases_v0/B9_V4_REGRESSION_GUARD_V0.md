# T0124 — B9 V4 Regression Guard + Golden Replay Cases

## Résumé exécutif

T0124 V2 fige les cas replay critiques pour empêcher B9 V4 de régresser sur effort/résultat/progrès, chemin interne du centre, retest, source quality et timestamp policy.

```text
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l'effort.
Ne lis pas l'absorption comme une direction.
Lis où elle déplace la mémoire.
```

## Verdict

- État : `PASS`
- Cas golden : `6`
- Cas passés : `6`
- Cas échoués : `0`
- Champs requis manquants : `0`
- Hits langage interdit : `0`
- Source contrat : `LOCAL_REGRESSION_GUARD_FALLBACK_DETERMINISTIC_V2`

## Cas golden protégés

- `B9V4_GOLDEN_EFFORT_WITHOUT_RESULT` — `PASS` — Effort sans résultat
- `B9V4_GOLDEN_PROGRESSIVE_WAVE_UP` — `PASS` — Vague progressive haussière
- `B9V4_GOLDEN_CENTER_MIGRATION_DOWN` — `PASS` — Centre de gravité qui descend
- `B9V4_GOLDEN_RETEST_FAILED` — `PASS` — Retest échoué / reprise refusée
- `B9V4_GOLDEN_CORRECTIVE_BREATH` — `PASS` — Respiration corrective
- `B9V4_GOLDEN_SOURCE_QUALITY_TIMESTAMP` — `PASS` — Source limitée / retest non visible

## Échecs

Aucun échec golden case.

## Limites techniques

- Read-only.
- Aucune écriture `powerflow.db`.
- Aucune écriture `tick_archive.db`.
- Aucun dashboard.
- Aucun Telegram.
- Aucun BUY/SELL.
- Aucune probabilité de succès.
- V2 utilise un fallback local déterministe pour aligner pytest et CLI. La validation native reste couverte par T0122/T0123.

## Prochain geste

T0125 — B9 V4 Golden Replay Batch Runner : appliquer le guard sur plusieurs summaries replay réels.
