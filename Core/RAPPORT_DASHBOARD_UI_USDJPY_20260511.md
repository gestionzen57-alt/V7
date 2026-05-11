# RAPPORT_DASHBOARD_UI_USDJPY_20260511

## Mission
Dashboard MultiSymbol UI + USDJPY Capture Audit.

## Livrable
powerflow_v721_dashboard_ui_usdjpy_fix.zip

## Contenu
- dashboard_multisymbol_ui_patch.html
- dashboard_cross_validation_card.html
- audit_usdjpy_capture.py
- run_audit_usdjpy_once.py
- test_dashboard_tabs.py
- git_deploy_dashboard_ui_usdjpy.ps1
- LEXIQUE_PATCH_UI.md
- REGISTRE_PATCH_UI.md
- validation_checklist.md

## Resultat attendu apres deploiement
- Tabs GBPUSD/EURUSD/USDJPY/XAUUSD visibles.
- Card CROSS-SYMBOL VALIDATION visible.
- Audit USDJPY produit output/audit_usdjpy_report.json.
- Dashboard expose LIVE OK / HTF INCOMPLETE / DATA STALE.

## Risques techniques connus
- USDJPY_STALE_DATA.
- USDJPY_INSUFFICIENT_ROWS.
- EURUSD_HTF_CONTEXT_INCOMPLETE.
- Dashboard legacy encore GBPUSD-centric si dashboard_live.html non remplace.

## Verdict
Pack pret a deploiement Git. Le fix capture USDJPY lui-meme reste mission MT4/bridge apres audit.
