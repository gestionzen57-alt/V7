# Commandes T0158 — T0148 JSON Contract Patch

## Installation

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0158_t0148_json_contract_patch.ps1"
```

## Git

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0158_t0148_json_contract_patch.ps1"
```

## Validation manuelle

```powershell
cd "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core"
python -m py_compile tools\apply_t0158_t0148_json_contract_patch.py
python -m pytest tests\test_t0158_t0148_json_contract_patch.py
python tools\apply_t0158_t0148_json_contract_patch.py --target pf_t009_live_brief_once_runner.py --output-report outputs\t0148_json_contract_patch_v0\T0158_T0148_JSON_CONTRACT_PATCH_REPORT.json
python -m py_compile pf_t009_live_brief_once_runner.py
```


## Correction V2

Le patcher ne bloque plus sur les termes BUY/SELL présents dans les garde-fous internes du code source. Le scan anti-langage interdit reste porté par les tests et sorties utilisateur T0148/T0155/T0157.
