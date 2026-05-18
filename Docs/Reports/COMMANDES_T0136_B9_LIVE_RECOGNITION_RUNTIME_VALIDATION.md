# Commandes T0136

## Install

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0136_b9_live_recognition_runtime_validation.ps1"
```

## Git

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0136_b9_live_recognition_runtime_validation.ps1"
```

## CLI sample

```powershell
python tools\build_t0136_b9_live_recognition_runtime_validation.py --mode sample --sample-dir samples\b9_live_recognition_runtime_validation_v0 --output-dir outputs\b9_live_recognition_runtime_validation_v0_sample
```

## CLI runtime réel

```powershell
python tools\build_t0136_b9_live_recognition_runtime_validation.py --mode runtime --core-root . --output-dir outputs\b9_live_recognition_runtime_validation_v0 --execute-t0135
```
