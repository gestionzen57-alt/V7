# Commandes T0120 — B9 Native Summarizer V4 Contract Patch

## Installation

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0120_b9_native_summarizer_v4_contract_patch.ps1"
```

## Git

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0120_b9_native_summarizer_v4_contract_patch.ps1"
```

## CLI directe

```powershell
python tools\build_t0120_b9_native_summarizer_v4_contract_patch.py `
  --sequence-summary-json samples\b9_native_summarizer_v4_contract_patch_v0\sample_t009_sequence_summary_raw_calibrated.json `
  --output-dir outputs\b9_native_summarizer_v4_contract_patch_v0
```

## Tests

```powershell
python -m py_compile pf_t009_sequence_summarizer_v4_contract.py tools\build_t0120_b9_native_summarizer_v4_contract_patch.py
python -m pytest tests\test_t0120_b9_native_summarizer_v4_contract_patch.py
```
