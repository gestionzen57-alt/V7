# Commandes T0115 — B6 Similarity Query CLI/API V0

## Install one-shot

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0115_b6_similarity_query_v0.ps1"
```

## Git one-shot

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0115_b6_similarity_query_v0.ps1"
```

## CLI query depuis un film existant

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core
python tools\build_t0115_b6_similarity_query_v0.py `
  --similarity-index outputs\b6_similarity_index_v0\B6_SIMILARITY_INDEX_V0.json `
  --query-film-id B6FC_20260505_1413_BDE6E508 `
  --output-dir outputs\b6_similarity_query_v0 `
  --top-k 5
```

## CLI query depuis une scène actuelle JSON

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core
python tools\build_t0115_b6_similarity_query_v0.py `
  --similarity-index outputs\b6_similarity_index_v0\B6_SIMILARITY_INDEX_V0.json `
  --query-json C:\Users\User\Downloads\current_b9_scene.json `
  --output-dir outputs\b6_similarity_query_v0_live `
  --top-k 5
```

## Tests

```powershell
python -m py_compile tools\build_t0115_b6_similarity_query_v0.py
python -m pytest tests\test_t0115_b6_similarity_query_v0_contract.py
```
