Claude,

T0175 - B9 Global Chain Contract Lock V0 est pret.

Branche :
feat/t0175-b9-global-chain-contract-lock-v0

Commit propose :
feat(t0175): add B9 global chain contract lock v0

Objectif :
Verrouiller le contrat global de chaine B9 avant tout branchement dashboard live.

Fichiers livres :
- tools/build_t0175_b9_global_chain_contract_lock.py
- tests/test_t0175_b9_global_chain_contract_lock.py
- scripts/RUN_T0175_B9_GLOBAL_CHAIN_CONTRACT_LOCK_FROM_DOWNLOADS.ps1
- samples/t0175_global_chain_contract_lock_v0/README.md
- Docs/Reports/T0175_B9_GLOBAL_CHAIN_CONTRACT_LOCK_REPORT.md
- Docs/Reports/T0175_B9_GLOBAL_CHAIN_CONTRACT_LOCK_MANIFEST.json
- Docs/Reports/COMMANDES_T0175_B9_GLOBAL_CHAIN_CONTRACT_LOCK.md
- Docs/Reports/MESSAGE_CLAUDE_T0175_B9_GLOBAL_CHAIN_CONTRACT_LOCK.md

Tests :
python -m py_compile tools\build_t0175_b9_global_chain_contract_lock.py
python -m pytest tests\test_t0175_b9_global_chain_contract_lock.py -q

Commande CLI :
python tools\build_t0175_b9_global_chain_contract_lock.py --core-root . --output-dir outputs\t0175_b9_global_chain_contract_lock_v0 --print-json

Etats possibles :
- LOCK_READY_FOR_DASHBOARD_REVIEW
- LOCK_PARTIAL_OPTIONAL_MISSING
- LOCK_BLOCKED_MISSING_REQUIRED
- LOCK_BLOCKED_SOURCE_ERROR
- LOCK_BLOCKED_FORBIDDEN_LANGUAGE

Doctrine :
B9 ne cherche pas le signal.
B9 cherche la trace laissee par l'effort.
Le dashboard affiche, il ne decide pas.

Limites :
- Aucune DB.
- Aucun cockpit live.
- Aucun Telegram.
- Aucun BUY/SELL.
- Aucune probabilite de succes.
- Les outputs T0175 sont runtime/local review et ne doivent pas etre commites sans validation architecte.

Prochain geste :
Lire le lock_state T0175. Si LOCK_READY_FOR_DASHBOARD_REVIEW, revue architecte du contrat de surface. Sinon corriger les inputs manquants/source errors avant tout branchement dashboard.
