# Commandes T0172

## Install

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0172_b9_live_chain_contract_validator.ps1"
```

## Git

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0172_b9_live_chain_contract_validator.ps1"
```

## Tests

```powershell
python -m py_compile pf_t009_live_chain_contract_validator.py tools\build_t0172_b9_live_chain_contract_validator.py
python -m pytest tests\test_t0172_b9_live_chain_contract_validator.py
```

## CLI runtime

```powershell
python tools\build_t0172_b9_live_chain_contract_validator.py --core-root . --output-dir outputs\b9_live_chain_contract_validator_v0 --print-json
```
