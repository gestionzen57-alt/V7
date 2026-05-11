# Validation checklist — PowerFlow V7.2 MultiSymbol

## 1. Compile

```powershell
python -m py_compile pf_cross_symbol_validation.py
python -m py_compile run_cross_symbol_validation_once.py
python -m py_compile scheduler_powerflow.py
python -m py_compile PATCHED_RUNNERS\run_temporal_node_state_once.py
python -m py_compile PATCHED_RUNNERS\run_currency_energy_probe_once.py
python -m py_compile PATCHED_RUNNERS\run_regime_engine_once.py
python -m py_compile PATCHED_RUNNERS\run_temporal_density_once.py
python -m py_compile PATCHED_RUNNERS\run_spearman_gravity_once.py
python -m py_compile PATCHED_RUNNERS\run_behavioral_alert_mapper_once.py
python -m py_compile PATCHED_MODULES\pf_temporal_density.py
python -m py_compile PATCHED_MODULES\pf_spearman_gravity.py
```

## 2. Déploiement fichiers

- [ ] `pf_cross_symbol_validation.py` copié dans `Core/`
- [ ] `run_cross_symbol_validation_once.py` copié dans `Core/`
- [ ] `scheduler_powerflow.py` copié dans `Core/`
- [ ] `scheduler_config.json` copié dans `Core/`
- [ ] `PATCHED_RUNNERS/*.py` copiés dans `Core/`
- [ ] `PATCHED_MODULES/*.py` copiés dans `Core/`

## 3. Tests GBPUSD legacy

- [ ] `python run_temporal_node_state_once.py --db powerflow.db --symbol GBPUSD --pretty`
- [ ] `output/dashboard_surface/GBPUSD/node.json` existe
- [ ] `output/temporal_node_state.json` existe encore en alias legacy
- [ ] `python run_currency_energy_probe_once.py --db powerflow.db --symbol GBPUSD --pretty`
- [ ] `output/dashboard_surface/GBPUSD/energy.json` existe
- [ ] alias legacy `output/currency_energy_state.json` existe

## 4. Tests autres symboles

- [ ] `python run_temporal_density_once.py --db powerflow.db --symbol EURUSD --pretty --summary`
- [ ] `output/temporal_density_state_EURUSD.json` existe
- [ ] `python run_spearman_gravity_once.py --db powerflow.db --symbol USDJPY --pretty --summary`
- [ ] `output/spearman_gravity_state_USDJPY.json` existe
- [ ] `python run_currency_energy_probe_once.py --db powerflow.db --symbol XAUUSD --pretty`
- [ ] si `force_xau` absent, risque technique explicite, pas crash silencieux

## 5. Cross-validation

- [ ] `python run_cross_symbol_validation_once.py --db powerflow.db --symbols GBPUSD,EURUSD,USDJPY --pretty`
- [ ] `output/dashboard_surface/cross_validation.json` existe
- [ ] `driver` présent
- [ ] `symbols_used` présent
- [ ] `technical_risks` présent

## 6. Scheduler once

- [ ] `python scheduler_powerflow.py --once --symbols GBPUSD`
- [ ] `logs/scheduler.log` existe
- [ ] `output/scheduler_last_cycle_report.json` existe
- [ ] pas de chevauchement si lock actif

## 7. Dashboard patch

- [ ] `dashboard_multisymbol_patch.html` injecté ou ouvert à côté du dashboard
- [ ] tabs GBPUSD/EURUSD/USDJPY/XAUUSD visibles
- [ ] chaque card expose `data-brick` et `data-symbol`
- [ ] timestamp visible
- [ ] age_seconds visible
- [ ] freshness FRESH/AGING/STALE/MISSING visible

## 8. Git

- [ ] `git status` propre avant patch
- [ ] `git add` fichiers patch
- [ ] commit `MultiSymbol: parametric symbol extension + cross-validation + scheduler`
- [ ] `git push`
