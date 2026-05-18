# Commandes T0141 — B9 Zone Memory Object Builder V0

## Installation one-shot

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0141_b9_zone_memory_object_builder.ps1"
```

## Git one-shot

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0141_b9_zone_memory_object_builder.ps1"
```

## Test manuel

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core
python -m py_compile pf_t009_zone_memory_object_builder.py tools\build_t0141_b9_zone_memory_object_builder.py
python -m pytest tests\test_t0141_b9_zone_memory_object_builder.py
```

## CLI manuel

```powershell
python tools\build_t0141_b9_zone_memory_object_builder.py `
  --sequence-summary-json samples\b9_zone_memory_object_builder_v0\sample_t009_sequence_summary_zone_memory.json `
  --output-dir outputs\b9_zone_memory_object_builder_v0
```
