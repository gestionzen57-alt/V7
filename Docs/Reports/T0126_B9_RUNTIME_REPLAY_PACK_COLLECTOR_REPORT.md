# T0126 — B9 V4 Runtime Replay Pack Collector V0

## Résumé exécutif

T0126 scanne le Core PowerFlow local pour repérer les vrais summaries replay B9/T009 exploitables par T0125.

Il exclut les artefacts de validation, samples artificiels, outputs regenerated et dossiers `_extract` afin de préparer un lot réel propre.

Phrase de cap :

```text
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l'effort.
Le collector ne prédit rien : il prépare le terrain replay.
```

## Entrée

```text
--scan-root .
```

## Sorties

```text
B9_RUNTIME_REPLAY_PACK_INDEX_V0.csv
B9_RUNTIME_REPLAY_PACK_INDEX_V0.json
B9_RUNTIME_REPLAY_PACK_CANDIDATES_V0.md
B9_RUNTIME_REPLAY_PACK_KEEP_V0.csv
B9_RUNTIME_REPLAY_PACK_REVIEW_V0.csv
B9_RUNTIME_REPLAY_PACK_REJECTED_V0.csv
B9_RUNTIME_REPLAY_PACK_COLLECTOR_MANIFEST.json
B9_RUNTIME_REPLAY_PACK_COLLECTOR_V0.zip
```

## Exclusions

```text
samples/
*_validation/
*_install_validation/
*_git_validation/
*_regenerated/
_extract/
.git/
```

## Doctrine

Read-only. Aucune écriture `powerflow.db`. Aucune écriture `tick_archive.db`. Aucun dashboard. Aucun Telegram. Aucun BUY/SELL. Aucune probabilité de succès.

## Prochain geste

Lancer T0125 sur le lot réel issu des fichiers KEEP.
