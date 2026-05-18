Claude,

T0173 — B9 Live Chain Runtime Missing Input Resolver V0 est prêt.

Branche :
feat/t0173-b9-live-chain-missing-input-resolver

Commit proposé :
feat(t0173): add B9 live chain missing input resolver v0

Objectif :
Quand T0172 signale des inputs manquants dans la chaîne B9 live candidate, T0173 produit un plan de régénération ordonné, sans rien exécuter automatiquement.

Tests :
python -m py_compile pf_t009_live_chain_runtime_missing_input_resolver.py tools\build_t0173_b9_live_chain_missing_input_resolver.py
python -m pytest tests\test_t0173_b9_live_chain_missing_input_resolver.py

Commande CLI :
python tools\build_t0173_b9_live_chain_missing_input_resolver.py --core-root . --output-dir outputs\b9_live_chain_missing_input_resolver_v0 --print-json

Doctrine :
B9 lit la scène.
B6 compare les films.
Le resolver indique quoi relancer ; il ne déclenche aucune action.

Contraintes :
Read-only.
Aucune DB.
Aucun cockpit live.
Aucun Telegram.
Aucun ordre directionnel.
Aucune promesse de performance.

Prochain geste :
T0174 — B9 Surface Adapter Import Path Hotfix V0.
