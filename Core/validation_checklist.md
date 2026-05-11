# validation_checklist - Dashboard UI + USDJPY Audit

## Dashboard
- [ ] Tabs GBPUSD/EURUSD/USDJPY/XAUUSD visibles.
- [ ] GBPUSD actif par defaut.
- [ ] Click EURUSD charge output/dashboard_surface/EURUSD/.
- [ ] Click USDJPY charge output/dashboard_surface/USDJPY/.
- [ ] Cross-validation card visible.
- [ ] Freshness badges visibles.
- [ ] data-brick et data-symbol presents.
- [ ] Pas de fusion des donnees par symbole.

## Audit USDJPY
- [ ] python run_audit_usdjpy_once.py --pretty fonctionne.
- [ ] output/audit_usdjpy_report.json cree.
- [ ] rows_total, timestamps, timeframes, diagnosis presents.
- [ ] DB read-only.

## General
- [ ] py_compile PASS.
- [ ] Aucun BUY/SELL.
- [ ] LEXIQUE_PATCH_UI.md committe.
- [ ] REGISTRE_PATCH_UI.md committe.
