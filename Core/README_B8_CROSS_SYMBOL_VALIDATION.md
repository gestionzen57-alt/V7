# B8 — Cross-Symbol Validation

Livrable prêt à intégrer dans PowerFlow V7.x.

## Fichiers

- `pf_cross_symbol_validation.py` — moteur B8 core, read-only DB.
- `run_cross_symbol_validation_once.py` — runner CLI.
- `test_cross_symbol_validation.py` — tests unitaires.
- `pf_confluence_gravity_b8_patch.py` — fonction d'enrichissement à intégrer dans `pf_confluence_gravity.py`.
- `dashboard_b8_cross_validation_card.html` — carte dashboard prête à coller.

## Commandes

```powershell
python -m pytest test_cross_symbol_validation.py -v
python run_cross_symbol_validation_once.py --db .\powerflow.db --symbol GBP --timeframe 1 --pretty --verbose
```

## Doctrine

B8 nomme un driver et qualifie la cohérence cross-symbol. Il ne décide pas, ne conseille pas, ne génère aucun BUY/SELL, et n'écrit jamais dans `powerflow.db`.
