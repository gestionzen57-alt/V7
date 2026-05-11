# REGISTRE_PATCH_UI - PowerFlow V7.2.1 Dashboard MultiSymbol + USDJPY Audit

## DASHBOARD_MULTISYMBOL_UI
Fichier: dashboard_multisymbol_ui_patch.html  
Couche: dashboard_*  
Role: afficher outputs par symbole via tabs.  
Lit: output/dashboard_surface/{symbol}/regime_legacy.json, regime_hmm.json, energy.json, node.json, cascade.json.  
Ecrit: aucun.

## CROSS_SYMBOL_VALIDATION_CARD
Fichier: dashboard_cross_validation_card.html  
Role: afficher driver global et force nette par devise.  
Source: output/dashboard_surface/cross_validation.json.  
Regle: global, pas per-symbol.

## AUDIT_USDJPY_CAPTURE
Fichier: audit_usdjpy_capture.py  
Runner: run_audit_usdjpy_once.py  
Role: diagnostiquer capture USDJPY.  
DB: read-only sqlite mode=ro.  
Output: output/audit_usdjpy_report.json.

## DASHBOARD_TABS_TEST
Fichier: test_dashboard_tabs.py  
Role: validation statique tabs/card/freshness + optional runtime outputs.

## GIT_DEPLOY_DASHBOARD_UI_USDJPY
Fichier: git_deploy_dashboard_ui_usdjpy.ps1  
Role: copier, compiler, auditer, patcher dashboard, tester, commit/push.

## Interdits
Pas de BUY/SELL. Pas d'ecriture DB. Pas de fusion par symbole. Pas de morale financiere.
