# T0173 — B9 Live Chain Runtime Missing Input Resolver V0

## Objectif

Produire un plan de régénération quand T0172 signale des inputs manquants dans la chaîne B9 live candidate.

Le resolver ne relance rien automatiquement. Il indique l'ordre exact des briques à régénérer et les commandes recommandées.

## Doctrine

B9 lit la scène.  
B6 compare les films.  
Le resolver prépare la remise en cohérence ; il ne déclenche aucune action.

## Contraintes

- Read-only.
- Aucune écriture `powerflow.db`.
- Aucune écriture `tick_archive.db`.
- Aucun cockpit live modifié.
- Aucun envoi Telegram.
- Aucun ordre directionnel.
- Aucune promesse de performance.

## Sorties

- `B9_LIVE_CHAIN_MISSING_INPUT_RESOLVER_V0.json`
- `B9_LIVE_CHAIN_MISSING_INPUT_RESOLVER_V0.md`
- `B9_LIVE_CHAIN_MISSING_INPUTS_V0.csv`
- `B9_LIVE_CHAIN_REGENERATION_PLAN_V0.csv`
- `B9_LIVE_CHAIN_REGENERATION_PLAN_V0.ps1`
- `B9_LIVE_CHAIN_RESOLVER_STEPS_V0.csv`
