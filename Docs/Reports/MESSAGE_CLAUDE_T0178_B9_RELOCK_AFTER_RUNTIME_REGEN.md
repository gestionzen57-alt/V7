Claude,

T0178 - B9 Relock After Runtime Regen V0 est pret.

Branche :
feat/t0178-b9-relock-after-runtime-regen-v0

Commit propose :
feat(t0178): add B9 relock after runtime regen v0

Objectif :
Relancer T0175 Global Chain Contract Lock puis T0176 Dashboard Operational Degraded Gate apres regeneration des artefacts runtime.

But :
Passer de LOCK_BLOCKED_MISSING_REQUIRED vers LOCK_READY_FOR_DASHBOARD_REVIEW, LOCK_PARTIAL_OPTIONAL_MISSING ou au minimum DEGRADED_READY / OPERATIONAL_DEGRADED.

Fichiers livres :
- tools/build_t0178_b9_relock_after_runtime_regen.py
- tests/test_t0178_b9_relock_after_runtime_regen.py
- scripts/RUN_T0178_B9_RELOCK_AFTER_RUNTIME_REGEN_FROM_DOWNLOADS.ps1
- samples/t0178_b9_relock_after_runtime_regen_v0/README.md
- Docs/Reports/T0178_B9_RELOCK_AFTER_RUNTIME_REGEN_REPORT.md
- Docs/Reports/T0178_B9_RELOCK_AFTER_RUNTIME_REGEN_MANIFEST.json
- Docs/Reports/COMMANDES_T0178_B9_RELOCK_AFTER_RUNTIME_REGEN.md
- Docs/Reports/MESSAGE_CLAUDE_T0178_B9_RELOCK_AFTER_RUNTIME_REGEN.md

Tests :
python -m py_compile tools\build_t0178_b9_relock_after_runtime_regen.py
python -m pytest tests\test_t0178_b9_relock_after_runtime_regen.py -q

Commande CLI :
python tools\build_t0178_b9_relock_after_runtime_regen.py --core-root . --output-dir outputs\t0178_b9_relock_after_runtime_regen_v0 --execute --print-json

Contraintes :
- aucun cockpit live modifie
- aucune DB touchee
- aucun Telegram
- aucun BUY/SELL
- aucune probabilite de succes
- aucun bouton decisionnel
- le dashboard affiche, il ne decide pas

Doctrine :
B9 ne cherche pas le signal. B9 cherche la trace laissee par l'effort.

Prochain geste :
Installer T0178, lire final_state et display_mode, puis valider si le dashboard peut afficher B9 en mode complet, partiel ou degrade.
