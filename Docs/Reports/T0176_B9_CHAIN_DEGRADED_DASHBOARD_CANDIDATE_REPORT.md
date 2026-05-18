# T0176 - B9 Chain Degraded Dashboard Candidate V0

## Objectif

T0176 transforme le resultat T0175 en surface dashboard candidate degradee.

Quand T0175 retourne un lock bloque ou partiel, le dashboard ne doit pas rester muet et ne doit pas afficher une scene complete artificielle.
Il doit afficher un diagnostic utile : etat de chaine, lecture degradee, inputs manquants, cartes techniques, commandes de regeneration, ce que B9 voit deja, et ce que B9 ne peut pas encore completer.

## Entree principale

```text
outputs/t0175_b9_global_chain_contract_lock_v0/B9_GLOBAL_CHAIN_CONTRACT_LOCK_V0.json
outputs/t0175_b9_global_chain_contract_lock_v0/B9_GLOBAL_CHAIN_CONTRACT_LOCK_MISSING_INPUTS_V0.csv
outputs/t0175_b9_global_chain_contract_lock_v0/B9_GLOBAL_CHAIN_CONTRACT_LOCK_SOURCE_MATRIX_V0.csv
```

## Sorties runtime

```text
outputs/t0176_b9_chain_degraded_dashboard_candidate_v0/B9_CHAIN_DEGRADED_DASHBOARD_CANDIDATE_V0.json
outputs/t0176_b9_chain_degraded_dashboard_candidate_v0/B9_CHAIN_DEGRADED_DASHBOARD_CANDIDATE_V0.md
outputs/t0176_b9_chain_degraded_dashboard_candidate_v0/B9_CHAIN_DEGRADED_DASHBOARD_MISSING_BRICK_CARDS_V0.csv
outputs/t0176_b9_chain_degraded_dashboard_candidate_v0/B9_CHAIN_DEGRADED_DASHBOARD_REGEN_COMMANDS_V0.csv
outputs/t0176_b9_chain_degraded_dashboard_candidate_v0/B9_CHAIN_DEGRADED_DASHBOARD_CANDIDATE_MANIFEST_V0.json
```

## Etats

```text
READY_FULL_CHAIN_VIEW
DEGRADED_OPTIONAL_INPUTS_MISSING
DEGRADED_REQUIRED_INPUTS_MISSING
BLOCKED_T0175_LOCK_UNREADABLE
BLOCKED_FORBIDDEN_LANGUAGE
DEGRADED_CHAIN_STATE_UNKNOWN
```

## Sections dashboard candidate

```text
Etat de chaine B9
Lecture operationnelle degradee
Inputs manquants
Cartes techniques par brique absente
Commandes de regeneration
Ce que B9 voit deja
Ce que B9 ne peut pas encore completer
Source quality
```

## Contraintes

- Read-only hors outputs T0176.
- Aucune DB.
- Aucun cockpit live.
- Aucun Telegram.
- Aucun bouton decisionnel.
- Le dashboard affiche, il ne decide pas.
