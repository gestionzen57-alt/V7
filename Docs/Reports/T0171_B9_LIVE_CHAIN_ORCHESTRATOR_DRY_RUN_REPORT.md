# T0171 — B9 Live Chain Orchestrator Dry Run V0

## Objet

Orchestrer en dry-run la chaîne B9 live candidate sans déclencher dashboard, Telegram, DB write ni décision.

## Chaîne contrôlée

- T0166 freshness guard
- T0147 latest scene candidate / queue
- T0167 B9/B6 realignment
- T0148 live brief once
- T0155 trader attention packet
- T0156 Reality Board integration candidate
- T0169 surface adapter candidate
- T0157 Telegram FR gate candidate
- T0170 manual approval candidate
- T0159 French display contract

## États

- B9_LIVE_CHAIN_DRY_RUN_READY
- B9_LIVE_CHAIN_DRY_RUN_REVIEW_TECHNICAL_RISK
- B9_LIVE_CHAIN_DRY_RUN_BLOCKED_MISSING_INPUTS
- B9_LIVE_CHAIN_DRY_RUN_BLOCKED_INVALID_INPUT
- B9_LIVE_CHAIN_DRY_RUN_BLOCKED_UPSTREAM_STATE

## Doctrine

B9 lit la scène. B6 compare les films. L'orchestrateur dry-run vérifie la chaîne ; il ne déclenche aucune action.

## Limites

Read-only. Aucune DB. Aucun cockpit live modifié. Aucun Telegram. Aucun ordre directionnel. Aucun taux de réussite.
