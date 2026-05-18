# Commandes T0176

## Tests

```powershell
python -m py_compile tools\build_t0176_b9_chain_degraded_dashboard_candidate.py
python -m pytest tests\test_t0176_b9_chain_degraded_dashboard_candidate.py -q
```

## CLI

```powershell
python tools\build_t0176_b9_chain_degraded_dashboard_candidate.py --core-root . --output-dir outputs\t0176_b9_chain_degraded_dashboard_candidate_v0 --print-json
```

## Ouverture des sorties

```powershell
notepad .\outputs\t0176_b9_chain_degraded_dashboard_candidate_v0\B9_CHAIN_DEGRADED_DASHBOARD_CANDIDATE_V0.md
notepad .\outputs\t0176_b9_chain_degraded_dashboard_candidate_v0\B9_CHAIN_DEGRADED_DASHBOARD_MISSING_BRICK_CARDS_V0.csv
notepad .\outputs\t0176_b9_chain_degraded_dashboard_candidate_v0\B9_CHAIN_DEGRADED_DASHBOARD_REGEN_COMMANDS_V0.csv
```
