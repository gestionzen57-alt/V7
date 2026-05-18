# T0172 — B9 Live Chain Contract Validator V0

## Objectif

Valider en read-only le contrat de chaîne B9 live candidate avant tout branchement dashboard ou Telegram réel.

T0172 vérifie que les artefacts suivants sont présents, lisibles et alignés :

- T0166 freshness guard
- T0147 latest scene candidate
- T0167 B9/B6 realignment
- T0148 live brief once
- T0155 trader attention packet
- T0156 Reality Board candidate
- T0169 surface adapter candidate
- T0157 Telegram FR gate
- T0170 manual approval candidate
- T0159 French display contract

## Rôle PowerFlow

B9 lit la scène.
B6 compare les films.
Le validator vérifie le contrat live ; il ne déclenche aucune action.

## États possibles

- `B9_LIVE_CHAIN_CONTRACT_PASS`
- `B9_LIVE_CHAIN_CONTRACT_REVIEW_TECHNICAL_RISK`
- `B9_LIVE_CHAIN_CONTRACT_BLOCKED_MISSING_INPUTS`
- `B9_LIVE_CHAIN_CONTRACT_BLOCKED_FORBIDDEN_LANGUAGE`
- `B9_LIVE_CHAIN_CONTRACT_BLOCKED_RAW_UNAVAILABLE`
- `B9_LIVE_CHAIN_CONTRACT_BLOCKED_CANDIDATE_MISMATCH`

## Sorties

- `B9_LIVE_CHAIN_CONTRACT_VALIDATOR_V0.json`
- `B9_LIVE_CHAIN_CONTRACT_VALIDATOR_V0.md`
- `B9_LIVE_CHAIN_CONTRACT_STEPS_V0.csv`
- `B9_LIVE_CHAIN_CONTRACT_RISKS_V0.csv`
- `B9_LIVE_CHAIN_CONTRACT_VALIDATOR_MANIFEST.json`
- `B9_LIVE_CHAIN_CONTRACT_VALIDATOR_V0.zip`

## Validation sample

```text
contract_state = B9_LIVE_CHAIN_CONTRACT_PASS
candidate_id = B9LSC_E49A7AEC65CE
steps_found = 10/10
match_count = 3
top_match_film_id = B6FC_20260511_1641_010496DB
false_positive_context_available = true
forbidden_language_hits = []
tests = 3 passed
```

## Limites

Read-only.
Aucune écriture `powerflow.db`.
Aucune écriture `tick_archive.db`.
Aucun cockpit live modifié.
Aucun Telegram.
Aucun ordre directionnel.
Aucun taux de réussite.
Une mémoire comparable n'est pas une répétition certaine.
