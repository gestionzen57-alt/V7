# COMMANDES — T0117 B6 False Positive Context V0

## Install one-shot

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0117_b6_false_positive_context_v0.ps1"
```

## Git one-shot

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0117_b6_false_positive_context_v0.ps1"
```

## CLI direct

```powershell
python tools\build_t0117_b6_false_positive_context_v0.py `
  --query-result-json outputs\b6_similarity_query_v0\B6_SIMILARITY_QUERY_RESULT_V0.json `
  --output-dir outputs\b6_false_positive_context_v0 `
  --top-k 5
```

## Tests

```powershell
python -m py_compile tools\build_t0117_b6_false_positive_context_v0.py
python -m pytest tests\test_t0117_b6_false_positive_context_v0_contract.py
```
