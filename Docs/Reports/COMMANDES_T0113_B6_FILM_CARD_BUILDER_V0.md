# Commandes T0113 — B6 Film Card Builder V0

## Installation one-shot

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\install_t0113_b6_film_card_builder_v0.ps1"
```

## Git one-shot

```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\User\Downloads\git_t0113_b6_film_card_builder_v0.ps1"
```

## CLI manuelle

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\core
python tools\build_t0113_b6_film_card_builder_v0.py `
  --input-csv "outputs\b6_memory_candidate_board_v0\B6_MEMORY_CANDIDATE_BOARD_V0.csv" `
  --output-dir "outputs\b6_film_library_v0_regenerated"
```

## Tests

```powershell
python -m py_compile tools\build_t0113_b6_film_card_builder_v0.py
python -m pytest tests\test_t0113_b6_film_card_builder_v0_contract.py
```
