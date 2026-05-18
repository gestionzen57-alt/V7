# T0123 — B9 V4 Replay Runtime Comparison

## Résumé exécutif

T0123 compare un summary B9 avant/après enrichissement V4 pour vérifier que B9 gagne en lecture de scène sans perdre les moments, la provenance, la source quality ni les limites.

Doctrine :

```text
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l'effort.
Ne lis pas l'absorption comme une direction.
Lis où elle déplace la mémoire.
```

## Verdict

- État : `PASS`
- Moments avant : `8`
- Moments après : `8`
- Champs requis manquants : `0`
- Langage interdit détecté : `0`
- Cellules de provenance/limites changées : `0`
- Mode after : `generated_by_installed_contract_or_fallback`

## Ce que T0123 vérifie

```text
1. Le nombre de moments ne change pas.
2. Les champs V4 existent sur chaque moment.
3. Les champs source/provenance/limites ne sont pas effacés.
4. Les timestamps shifted/replay sont signalés par policy.
5. Aucun BUY/SELL, aucune probabilité de succès.
```

## Fichiers CSV

```text
B9_V4_REPLAY_FIELD_DIFF_V0.csv
B9_V4_REPLAY_MOMENT_PRESERVATION_V0.csv
B9_V4_REPLAY_REQUIRED_FIELD_COVERAGE_V0.csv
B9_V4_REPLAY_TIMESTAMP_POLICY_V0.csv
```

## Limites

Read-only. Aucune écriture powerflow.db. Aucune écriture tick_archive.db. Aucun dashboard. Aucun Telegram. Aucun BUY/SELL. Aucune probabilité de succès.
