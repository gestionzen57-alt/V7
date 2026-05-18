# Commandes T0128 — B9 Native Retest Source Fields / T0111B

## Installation

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0128_b9_native_retest_source_fields.ps1"
```

## Git

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0128_b9_native_retest_source_fields.ps1"
```

## Test manuel

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core
python -m py_compile pf_t009_native_retest_source_fields.py tools\build_t0128_b9_native_retest_source_fields.py
python -m pytest tests\test_t0128_b9_native_retest_source_fields.py
python tools\build_t0128_b9_native_retest_source_fields.py --sequence-summary-json samples\b9_native_retest_source_fields_v0\sample_t009_sequence_summary_retest_candidate.json --output-dir outputs\b9_native_retest_source_fields_v0
```
