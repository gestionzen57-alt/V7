# T0149 — B9 Reality Board Payload Candidate V0

## Objectif

Construire un payload candidat pour Reality Board à partir du brief live T0148, sans brancher le dashboard, sans Telegram et sans écriture DB.

## Contrat

- Read-only.
- Aucune écriture `powerflow.db`.
- Aucune écriture `tick_archive.db`.
- Aucun dashboard live.
- Aucun Telegram.
- Aucun ordre directionnel.
- Aucun taux de réussite.

## États

```text
B9_REALITY_BOARD_PAYLOAD_CANDIDATE_READY
B9_REALITY_BOARD_PAYLOAD_CANDIDATE_REVIEW_LIMITED_SOURCE
BLOCKED_MISSING_LIVE_BRIEF_INPUT
BLOCKED_LIVE_BRIEF_NOT_READY
BLOCKED_RAW_UNAVAILABLE_IN_MEMORY_RESULTS
BLOCKED_FORBIDDEN_LANGUAGE
```

## Doctrine

B9 ne cherche pas le signal.  
B9 cherche la trace laissée par l’effort.  
Le payload Reality Board expose une scène, il ne décide pas.
