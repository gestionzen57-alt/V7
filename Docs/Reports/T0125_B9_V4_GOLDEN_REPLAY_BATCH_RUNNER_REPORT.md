# T0125 — B9 V4 Golden Replay Batch Runner V0

## Résumé

T0125 applique le guard T0124 sur un lot de summaries replay JSON.

Objectif : vérifier que B9 V4 tient sur plusieurs films, pas seulement sur un sample isolé.

## Doctrine

B9 ne cherche pas le signal.  
B9 cherche la trace laissée par l'effort.  
Ne lis pas l'absorption comme une direction.  
Lis où elle déplace la mémoire.

## Entrées

- `samples/b9_v4_golden_replay_batch_runner_v0/*.json` par défaut ;
- ou n'importe quel dossier passé via `--input-dir`.

## Sorties

- `B9_V4_GOLDEN_REPLAY_BATCH_RUNNER_V0.json`
- `B9_V4_GOLDEN_REPLAY_BATCH_RUNNER_V0.md`
- `B9_V4_GOLDEN_REPLAY_BATCH_RESULTS_V0.csv`
- `B9_V4_GOLDEN_REPLAY_BATCH_FAILURES_V0.csv`
- `B9_V4_GOLDEN_REPLAY_BATCH_COVERAGE_V0.csv`
- `B9_V4_GOLDEN_REPLAY_BATCH_RUNNER_MANIFEST.json`
- `B9_V4_GOLDEN_REPLAY_BATCH_RUNNER_V0.zip`

## Limites

T0125 est read-only. Il ne remplace pas T0122/T0123 pour vérifier le hook natif local dans `pf_t009_sequence_summarizer.py`.
