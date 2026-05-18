Claude,

T0176 - B9 Chain Degraded Dashboard Candidate V0 est pret.

Branche :
feat/t0176-b9-chain-degraded-dashboard-candidate-v0

Commit propose :
feat(t0176): add B9 chain degraded dashboard candidate v0

Objectif :
Transformer un lock T0175 bloque ou partiel en surface dashboard candidate utile, sans brancher le dashboard live.

Fichiers livres :
- tools/build_t0176_b9_chain_degraded_dashboard_candidate.py
- tests/test_t0176_b9_chain_degraded_dashboard_candidate.py
- scripts/RUN_T0176_B9_CHAIN_DEGRADED_DASHBOARD_CANDIDATE_FROM_DOWNLOADS.ps1
- samples/t0176_b9_chain_degraded_dashboard_candidate_v0/README.md
- Docs/Reports/T0176_B9_CHAIN_DEGRADED_DASHBOARD_CANDIDATE_REPORT.md
- Docs/Reports/T0176_B9_CHAIN_DEGRADED_DASHBOARD_CANDIDATE_MANIFEST.json
- Docs/Reports/COMMANDES_T0176_B9_CHAIN_DEGRADED_DASHBOARD_CANDIDATE.md
- Docs/Reports/MESSAGE_CLAUDE_T0176_B9_CHAIN_DEGRADED_DASHBOARD_CANDIDATE.md

Tests :
python -m py_compile tools\build_t0176_b9_chain_degraded_dashboard_candidate.py
python -m pytest tests\test_t0176_b9_chain_degraded_dashboard_candidate.py -q

Commande CLI :
python tools\build_t0176_b9_chain_degraded_dashboard_candidate.py --core-root . --output-dir outputs\t0176_b9_chain_degraded_dashboard_candidate_v0 --print-json

Sorties runtime :
- outputs/t0176_b9_chain_degraded_dashboard_candidate_v0/B9_CHAIN_DEGRADED_DASHBOARD_CANDIDATE_V0.json
- outputs/t0176_b9_chain_degraded_dashboard_candidate_v0/B9_CHAIN_DEGRADED_DASHBOARD_CANDIDATE_V0.md
- outputs/t0176_b9_chain_degraded_dashboard_candidate_v0/B9_CHAIN_DEGRADED_DASHBOARD_MISSING_BRICK_CARDS_V0.csv
- outputs/t0176_b9_chain_degraded_dashboard_candidate_v0/B9_CHAIN_DEGRADED_DASHBOARD_REGEN_COMMANDS_V0.csv
- outputs/t0176_b9_chain_degraded_dashboard_candidate_v0/B9_CHAIN_DEGRADED_DASHBOARD_CANDIDATE_MANIFEST_V0.json

Sections affichables :
- Etat de chaine B9
- Lecture operationnelle degradee
- Inputs manquants
- Cartes techniques par brique absente
- Commandes de regeneration
- Ce que B9 voit deja
- Ce que B9 ne peut pas encore completer
- Source quality

Contraintes :
- Aucune DB.
- Aucun cockpit live.
- Aucun Telegram.
- Aucun bouton decisionnel.
- Le dashboard affiche, il ne decide pas.

Prochain geste :
Lancer T0176 apres T0175. Si le lock reste bloque, afficher ce panel degrade candidat au lieu d'une scene complete artificielle.
