# T0175 - B9 Global Chain Contract Lock V0

## Mission

Verrouiller le contrat global de chaine B9 avant tout branchement dashboard live.

## Role

T0175 ne branche rien. Il valide que les artefacts candidats B9 existent, que le builder T0169 et sa sortie candidate sont visibles, et que le vocabulaire decisionnel interdit ne fuit pas dans les surfaces candidates.

## Contrat

- Read-only hors outputs T0175 generes.
- Aucune DB.
- Aucun cockpit live.
- Aucun Telegram.
- Aucun BUY/SELL.
- Aucune probabilite de succes.
- Aucun bouton decision.

## Sorties runtime

- outputs/t0175_b9_global_chain_contract_lock_v0/B9_GLOBAL_CHAIN_CONTRACT_LOCK_V0.json
- outputs/t0175_b9_global_chain_contract_lock_v0/B9_GLOBAL_CHAIN_CONTRACT_LOCK_V0.md
- outputs/t0175_b9_global_chain_contract_lock_v0/B9_GLOBAL_CHAIN_CONTRACT_LOCK_MISSING_INPUTS_V0.csv
- outputs/t0175_b9_global_chain_contract_lock_v0/B9_GLOBAL_CHAIN_CONTRACT_LOCK_FORBIDDEN_HITS_V0.csv
- outputs/t0175_b9_global_chain_contract_lock_v0/B9_GLOBAL_CHAIN_CONTRACT_LOCK_SOURCE_MATRIX_V0.csv
- outputs/t0175_b9_global_chain_contract_lock_v0/B9_GLOBAL_CHAIN_CONTRACT_LOCK_MANIFEST_V0.json

## Etats possibles

- LOCK_READY_FOR_DASHBOARD_REVIEW
- LOCK_PARTIAL_OPTIONAL_MISSING
- LOCK_BLOCKED_MISSING_REQUIRED
- LOCK_BLOCKED_SOURCE_ERROR
- LOCK_BLOCKED_FORBIDDEN_LANGUAGE

## Commande CLI

```powershell
python tools\build_t0175_b9_global_chain_contract_lock.py --core-root . --output-dir outputs\t0175_b9_global_chain_contract_lock_v0 --print-json
```
