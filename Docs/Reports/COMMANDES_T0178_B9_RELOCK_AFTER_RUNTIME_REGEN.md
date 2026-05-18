# Commandes T0178

## Tests

```powershell
python -m py_compile tools\build_t0178_b9_relock_after_runtime_regen.py
python -m pytest tests\test_t0178_b9_relock_after_runtime_regen.py -q
```

## CLI

```powershell
python tools\build_t0178_b9_relock_after_runtime_regen.py --core-root . --output-dir outputs\t0178_b9_relock_after_runtime_regen_v0 --execute --print-json
```
