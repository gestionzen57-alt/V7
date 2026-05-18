# Commandes T0122 — B9 V4 Native Runtime Validation

## Installation

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0122_b9_v4_native_runtime_validation.ps1"
```

## Git

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0122_b9_v4_native_runtime_validation.ps1"
```

## CLI directe

```powershell
python tools\build_t0122_b9_v4_native_runtime_validation.py `
  --sequence-summary-json samples\b9_v4_native_runtime_validation_v0\sample_t009_sequence_summary_v4_candidate.json `
  --summarizer-py pf_t009_sequence_summarizer.py `
  --output-dir outputs\b9_v4_native_runtime_validation_v0
```
