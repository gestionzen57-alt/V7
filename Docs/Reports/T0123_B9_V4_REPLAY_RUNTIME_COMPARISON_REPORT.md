# T0123 — B9 V4 Replay Runtime Comparison

## Objectif

Comparer un summary B9 avant/après enrichissement V4 afin de vérifier que le patch natif enrichit la lecture sans casser les moments, les labels FR, la source quality, les limites ni la politique timestamp.

## Doctrine

```text
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l'effort.
Ne lis pas l'absorption comme une direction.
Lis où elle déplace la mémoire.
```

## Contrat vérifié

- nombre de moments inchangé ;
- champs V1/V2/V3/V4 présents ;
- source/provenance/limites préservées ;
- timestamp policy explicite si replay shifted ;
- aucun BUY/SELL ;
- aucune probabilité de succès ;
- aucun accès DB.

## Commande CLI

```powershell
python tools\build_t0123_b9_v4_replay_runtime_comparison.py `
  --before-summary-json samples\b9_v4_replay_runtime_comparison_v0\sample_t009_sequence_summary_before_v4.json `
  --output-dir outputs\b9_v4_replay_runtime_comparison_v0
```

## Sorties

```text
B9_V4_REPLAY_RUNTIME_COMPARISON_V0.md
B9_V4_REPLAY_RUNTIME_COMPARISON_V0.json
B9_V4_REPLAY_FIELD_DIFF_V0.csv
B9_V4_REPLAY_MOMENT_PRESERVATION_V0.csv
B9_V4_REPLAY_REQUIRED_FIELD_COVERAGE_V0.csv
B9_V4_REPLAY_TIMESTAMP_POLICY_V0.csv
B9_V4_REPLAY_ENRICHED_SUMMARY_SAMPLE_V0.json
B9_V4_REPLAY_RUNTIME_COMPARISON_V0.zip
```

## Limites

Read-only. Aucune écriture `powerflow.db`. Aucune écriture `tick_archive.db`. Aucun dashboard. Aucun Telegram. Aucun BUY/SELL. Aucune probabilité de succès.
