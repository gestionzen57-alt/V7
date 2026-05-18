# Commandes T0145 — B9 False Positive Memory Explainer V0

## Install one-shot

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0145_b9_false_positive_memory_explainer.ps1"
```

## Git one-shot

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0145_b9_false_positive_memory_explainer.ps1"
```

## Tests

```powershell
python -m py_compile pf_t009_false_positive_memory_explainer.py tools\build_t0145_b9_false_positive_memory_explainer.py
python -m pytest tests\test_t0145_b9_false_positive_memory_explainer.py
```

## CLI

```powershell
python tools\build_t0145_b9_false_positive_memory_explainer.py --sequence-summary-json samples\b9_false_positive_memory_explainer_v0\sample_t009_sequence_summary_false_positive_memory.json --output-dir outputs\b9_false_positive_memory_explainer_v0
```
