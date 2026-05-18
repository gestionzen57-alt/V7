# T0126 — B9 Runtime Replay Pack Collector V0

## Résumé exécutif

B9 ne cherche pas le signal.
B9 cherche la trace laissée par l'effort.
Le collector ne prédit rien : il prépare un lot replay propre pour les guards T0124/T0125.

## Counts

- scanned_root: `C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core`
- files_discovered: 1
- candidates_keep: 1
- candidates_review: 0
- candidates_rejected: 0

## KEEP candidates

- `output/b9_raw_calibrated_v32_v35/0800_0900/t009_sequence_summary_raw_calibrated.json` — B9_REPLAY_PACK_KEEP_V4_READY — moments=3 — date=2026-05-16 — session=LONDON

## REVIEW candidates

Aucun candidat REVIEW détecté.

## Rejected

Aucun fichier rejeté.

## Usage T0125

Copier ou pointer les fichiers KEEP vers un batch réel, puis lancer T0125 sur ce lot.

## Limites techniques

- Read-only : aucune DB touchée.
- Le collector classe les fichiers par structure JSON et metadata visible.
- Un fichier REVIEW peut devenir exploitable après inspection humaine.
- Les samples, validations, regenerated et _extract sont exclus pour éviter les faux lots.
- La présence V4 est détectée, mais la vérité runtime reste validée par T0122/T0123/T0125.
