# T0156 — B9 Reality Board Integration Candidate V0

## Objectif

Transformer le `B9 Trader Attention Packet` T0155 en payload candidat pour Reality Board, sans brancher le dashboard live.

T0156 produit un contrat lisible par une future surface, mais reste strictement read-only.

## Doctrine

```text
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l'effort.
Le payload Reality Board expose une scène candidate, il ne décide pas.
```

## Entrée

```text
T0155 B9 Trader Attention Packet JSON
```

## Sorties

```text
B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.json
B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.md
B9_REALITY_BOARD_INTEGRATION_CANDIDATE_ROW_V0.csv
B9_REALITY_BOARD_INTEGRATION_CANDIDATE_MANIFEST.json
B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.zip
```

## Etats possibles

```text
B9_REALITY_BOARD_INTEGRATION_CANDIDATE_READY
B9_REALITY_BOARD_INTEGRATION_CANDIDATE_REVIEW_TECHNICAL_RISK
BLOCKED_MISSING_ATTENTION_PACKET_INPUT
BLOCKED_ATTENTION_PACKET_NOT_READY
BLOCKED_RAW_UNAVAILABLE_IN_ATTENTION_PACKET
BLOCKED_FORBIDDEN_LANGUAGE
BLOCKED_MISSING_NO_DECISION_GUARD
```

## Validation sample

```text
payload_state = B9_REALITY_BOARD_INTEGRATION_CANDIDATE_REVIEW_TECHNICAL_RISK
candidate_id = B9LSC_E49A7AEC65CE
scene_state = SCENE_ACCEPTED
price_verdict = ACCEPTED
memory_confidence_ladder = MEMORY_PARTIAL_COMPARABLE
match_count = 3
top_match_film_id = B6FC_20260511_1641_010496DB
false_positive_context_available = true
forbidden_language_hits = []
```

## Garde-fous

- Read-only.
- Aucune écriture `powerflow.db`.
- Aucune écriture `tick_archive.db`.
- Aucun dashboard live.
- Aucun Telegram.
- Aucun ordre directionnel.
- Aucun taux de réussite.
- Une scène proxy reste proxy.
- Une mémoire comparable n'est pas une répétition certaine.
