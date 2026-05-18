# T0138 — B9 Real Replay Day Pack Runner V0

## Résumé exécutif

T0138 applique les contrôles B9 V4 sur des summaries replay réels issus du collector T0126 ou d'un scan local.

B9 ne cherche pas le signal. B9 cherche la trace laissée par l'effort.

## Rôle

- lire un index T0126 KEEP/REVIEW quand il existe ;
- exclure samples/validation/regenerated/_extract ;
- classer chaque replay en KEEP / REVIEW / REJECT ;
- produire résultats, coverage, failures et rapport Markdown.

## Limites

Read-only. Aucune DB. Aucun dashboard. Aucun Telegram. Aucun ordre d'exécution. Aucun taux de réussite.

## Prochain geste

T0139 — B9 London / NY / Asian Replay Scorecard V0.


## Correction V2

Le test sample accepte maintenant les candidats KEEP ou REVIEW selon la couverture réelle des champs locaux. RAW_UNAVAILABLE-only reste rejeté. Pytest et CLI restent bloquants.
